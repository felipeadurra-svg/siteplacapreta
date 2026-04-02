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

MODEL = "gpt-4o"

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


# 🚀 IA VISÃO REAL (COM PROMPT PROFISSIONAL)
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
Você é um AVALIADOR AUTOMOTIVO PROFISSIONAL especializado em veículos antigos, atuando com critérios técnicos semelhantes aos utilizados pela :contentReference[oaicite:0]{index=0}.

DADOS DO VEÍCULO:
- Marca: {dados_veiculo.get("marca")}
- Modelo: {dados_veiculo.get("modelo")}
- Ano: {dados_veiculo.get("ano")}

REGRAS OBRIGATÓRIAS:
- Analise SOMENTE o que estiver visível nas imagens
- NÃO invente informações
- NÃO use linguagem genérica
- NÃO use achismos
- Utilize linguagem técnica, objetiva e profissional
- Quando algo não for visível, declare: "não visível nas imagens"
- Se houver inconsistência entre imagens, aponte tecnicamente

---

CRITÉRIOS DE AVALIAÇÃO (NOTA 0 A 100):

1. ORIGINALIDADE
- presença de peças originais vs modificações visíveis

2. LATARIA E PINTURA
- riscos, amassados, ondulações, qualidade da pintura, oxidação

3. INTERIOR
- estado de bancos, painel, acabamento e desgaste

4. MOTOR E COMPONENTES VISÍVEIS
- aparência, originalidade, sinais de intervenção

5. ESTRUTURA
- alinhamento, integridade aparente, indícios de reparo

6. ESTADO GERAL DE CONSERVAÇÃO

---

PARA CADA ITEM:
- descreva tecnicamente o que está visível
- atribua uma nota de 0 a 100

---

ANÁLISE POR IMAGEM:
- descreva o que cada imagem mostra tecnicamente
- destaque inconsistências ou danos específicos

---

AVALIAÇÃO FINAL:

- calcule a média das notas
- informe NOTA FINAL (0 a 100)

CRITÉRIO DE PLACA PRETA:
- mínimo de 80% de originalidade e conservação

Informe:

✔ APTO ou NÃO APTO para placa preta  
✔ justificativa técnica detalhada  

---

AVALIAÇÃO DE MERCADO:

- estime faixa de valor em reais (R$)
- baseie-se no estado visual observado
- utilize coerência com mercado brasileiro de clássicos

---

FORMATO FINAL:

1. Resumo técnico geral  
2. Análise por imagem  
3. Avaliação por critérios com notas  
4. Nota final  
5. Status placa preta (APTO / NÃO APTO)  
6. Avaliação de mercado  

Gere um relatório técnico completo, detalhado e profissional.
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
    <body style="font-family:Arial;padding:20px">
    <h1>📊 Vistorias IA (Padrão FBVA)</h1>
    """

    for c in clientes:
        d = c["dados"]

        html += f"""
        <div style="background:white;padding:15px;margin-bottom:10px;border-radius:8px">
            <b>{d.get('nome','')}</b><br>
            📞 {d.get('telefone','')}<br>
            <a href="/cliente/{c['id']}">Ver relatório</a>
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

    html += "<h3>🤖 Relatório IA</h3>"
    html += f"<pre>{dados.get('relatorio_ai','')}</pre>"

    html += "</body></html>"

    return HTMLResponse(html)