from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from typing import Optional
from datetime import datetime
from zoneinfo import ZoneInfo
from openai import OpenAI
import os
import uuid
import json
import base64

app = FastAPI()

# 🔑 OPENAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MODEL = "gpt-4o"  # 🔥 VISÃO REAL FORTE (NÃO MINI)

# 🌍 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 📁 UPLOADS
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


# 💾 SALVAR IMAGEM
def salvar_imagem(file: UploadFile, caminho: str):
    if not file:
        return None
    content = file.file.read()
    if not content:
        return None

    with open(caminho, "wb") as f:
        f.write(content)

    return caminho


# 🧠 BASE64
def img_to_base64(path):
    if not path or not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


# 🚨 PROMPT ULTRA RÍGIDO (ANTI-GENERICIDADE)
VISION_PROMPT = """
Você é um PERITO AUTOMOTIVO ESPECIALISTA EM VISTORIA REAL.

Você está analisando UMA FOTO DO VEÍCULO.

REGRAS OBRIGATÓRIAS:
- descreva SOMENTE o que está visível na imagem
- NÃO invente nada
- NÃO seja genérico
- NÃO use frases como "parece estar em bom estado"
- seja específico e técnico
- cite detalhes visuais concretos

Você deve identificar:

✔ pintura (brilho, desgaste, riscos)
✔ lataria (amassados, ondulações)
✔ ferrugem (se visível)
✔ alinhamento de peças
✔ estado de conservação real
✔ danos visuais explícitos

Se algo NÃO for visível:
→ escreva "não visível nesta imagem"

Agora faça uma análise técnica REAL desta imagem.
"""


# 🚀 IA VISÃO REAL (ROBUSTA)
def gerar_relatorio_real(fotos, dados_veiculo):

    imagens = []

    for nome, path in fotos.items():
        if not path:
            continue

        b64 = img_to_base64(path)
        if not b64:
            continue

        imagens.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{b64}"
            }
        })

    prompt = f"""
VEÍCULO EM ANÁLISE:
- Marca: {dados_veiculo.get("marca")}
- Modelo: {dados_veiculo.get("modelo")}
- Ano: {dados_veiculo.get("ano")}

Agora você receberá várias imagens do veículo.

IMPORTANTE:
- Analise TODAS as imagens
- Cada imagem representa uma visão diferente do veículo
- Seja extremamente técnico
- NÃO resuma sem analisar
- NÃO gere texto genérico

FORMATO FINAL:

1. Resumo técnico geral
2. Análise detalhada por imagem (IMPORTANTE)
3. Exterior (pintura e lataria)
4. Interior
5. Estrutura e integridade
6. Conclusão final

CLASSIFICAÇÃO FINAL:
RUIM / REGULAR / BOM / ÓTIMO
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    *imagens
                ]
            }
        ],
        temperature=0.2
    )

    return response.choices[0].message.content


# 📥 ENDPOINT PRINCIPAL
@app.post("/avaliacao")
async def avaliacao(
    nome: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    telefone: Optional[str] = Form(None),
    marca: Optional[str] = Form(None),
    modelo: Optional[str] = Form(None),
    ano: Optional[str] = Form(None),

    foto_frente: Optional[UploadFile] = File(None),
    foto_traseira: Optional[UploadFile] = File(None),
    foto_lateral_direita: Optional[UploadFile] = File(None),
    foto_lateral_esquerda: Optional[UploadFile] = File(None),
    foto_interior: Optional[UploadFile] = File(None),
    foto_painel: Optional[UploadFile] = File(None),
    foto_motor: Optional[UploadFile] = File(None),
    foto_porta_malas: Optional[UploadFile] = File(None),
    foto_chassi: Optional[UploadFile] = File(None),
    foto_adicional: Optional[UploadFile] = File(None),
):

    nome_limpo = (nome or "cliente").strip().replace(" ", "_")
    telefone_limpo = (telefone or "sem_numero").strip().replace(" ", "")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    uid = uuid.uuid4().hex[:6]

    cliente_id = f"{nome_limpo}_{telefone_limpo}_{timestamp}_{uid}"

    pasta = os.path.join(UPLOAD_DIR, cliente_id)
    os.makedirs(pasta, exist_ok=True)

    data_brasil = datetime.now(
        ZoneInfo("America/Sao_Paulo")
    ).strftime("%d/%m/%Y %H:%M:%S")

    dados = {
        "id": cliente_id,
        "nome": nome,
        "email": email,
        "telefone": telefone,
        "veiculo": {
            "marca": marca,
            "modelo": modelo,
            "ano": ano
        },
        "data": data_brasil
    }

    json_path = os.path.join(pasta, "dados.json")

    # 📸 FOTOS
    fotos = {
        "frente": salvar_imagem(foto_frente, f"{pasta}/frente.jpg"),
        "traseira": salvar_imagem(foto_traseira, f"{pasta}/traseira.jpg"),
        "lateral_direita": salvar_imagem(foto_lateral_direita, f"{pasta}/lateral.jpg"),
        "lateral_esquerda": salvar_imagem(foto_lateral_esquerda, f"{pasta}/lateral2.jpg"),
        "interior": salvar_imagem(foto_interior, f"{pasta}/interior.jpg"),
        "motor": salvar_imagem(foto_motor, f"{pasta}/motor.jpg"),
        "painel": salvar_imagem(foto_painel, f"{pasta}/painel.jpg"),
    }

    dados["fotos"] = fotos

    # 🔥 IA VISÃO REAL
    try:
        relatorio = gerar_relatorio_real(fotos, dados["veiculo"])
        dados["relatorio_ai"] = relatorio
    except Exception as e:
        dados["relatorio_ai"] = f"Erro IA: {str(e)}"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)

    return {"status": "ok", "cliente_id": cliente_id}


# 🏠 ROOT
@app.get("/")
def root():
    return {"status": "backend funcionando 🚀"}


# 📊 DASHBOARD
@app.get("/avaliacoes", response_class=HTMLResponse)
def avaliacoes():

    clientes = []

    for pasta_cliente in os.listdir(UPLOAD_DIR):
        pasta_path = os.path.join(UPLOAD_DIR, pasta_cliente)

        if not os.path.isdir(pasta_path):
            continue

        json_path = os.path.join(pasta_path, "dados.json")

        dados = {}
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                dados = json.load(f)

        clientes.append({"id": pasta_cliente, "dados": dados})

    clientes.sort(key=lambda c: c["dados"].get("data", ""), reverse=True)

    html = """
    <html>
    <head>
        <title>Avaliações IA Vision</title>
        <style>
            body { font-family: Arial; background:#f4f4f4; padding:20px; }
            .card { background:white; padding:15px; margin-bottom:15px; border-radius:10px; }
            .btn { padding:8px 12px; background:black; color:white; text-decoration:none; border-radius:6px; }
            pre { white-space: pre-wrap; }
        </style>
    </head>
    <body>
        <h1>📊 Vistorias com IA Vision REAL</h1>
    """

    for c in clientes:
        d = c["dados"]

        html += f"""
        <div class="card">
            <b>{d.get('nome','')}</b><br>
            📞 {d.get('telefone','')}<br>
            📅 {d.get('data','')}<br>
            <a class="btn" href="/cliente/{c['id']}">Ver relatório</a>
        </div>
        """

    html += "</body></html>"
    return HTMLResponse(html)


# 👤 CLIENTE
@app.get("/cliente/{cliente_id}", response_class=HTMLResponse)
def cliente(cliente_id: str):

    pasta = os.path.join(UPLOAD_DIR, cliente_id)
    json_path = os.path.join(pasta, "dados.json")

    if not os.path.exists(json_path):
        return HTMLResponse("Cliente não encontrado")

    with open(json_path, "r", encoding="utf-8") as f:
        dados = json.load(f)

    fotos = []
    for file in os.listdir(pasta):
        if file.endswith(".jpg"):
            fotos.append(f"/uploads/{cliente_id}/{file}")

    html = f"""
    <html>
    <body style="font-family:Arial;padding:20px">

    <h2>{dados.get("nome","")}</h2>

    <h3>📸 Fotos</h3>
    """

    for f in fotos:
        html += f'<img src="{f}" width="200" style="margin:5px"/>'

    html += "<h3>🤖 Relatório IA Vision REAL</h3>"
    html += f"<pre>{dados.get('relatorio_ai','')}</pre>"

    html += "</body></html>"

    return HTMLResponse(html)