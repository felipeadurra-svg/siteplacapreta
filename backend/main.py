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


# 🚀 RELATÓRIO IA NÍVEL VISTORIA
def gerar_relatorio_real(fotos, dados_veiculo):

    imagens = []

    for _, path in fotos.items():
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
Você é um PERITO AUTOMOTIVO ESPECIALIZADO EM VEÍCULOS ANTIGOS, com padrão técnico de vistoria para certificação de originalidade (placa preta).

DADOS DO VEÍCULO:
- Marca: {dados_veiculo.get("marca")}
- Modelo: {dados_veiculo.get("modelo")}
- Ano: {dados_veiculo.get("ano")}

REGRAS:
- Analise SOMENTE o que estiver visível
- NÃO invente
- NÃO use linguagem genérica
- Seja técnico e direto
- Se não for visível: "não visível nas imagens"

CRITÉRIOS (0 a 100):
1. Originalidade
2. Lataria e pintura
3. Interior
4. Motor
5. Estrutura
6. Conservação geral

Para cada item:
- descrição técnica
- nota (0 a 100)

Faça também:
- análise por imagem
- média final
- dizer se é APTO ou NÃO APTO para placa preta (mínimo 80)
- estimar valor de mercado em reais

FORMATO:
1. Resumo técnico
2. Análise por imagem
3. Critérios com notas
4. Nota final
5. Status placa preta
6. Valor de mercado
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
        temperature=0.1
    )

    return response.choices[0].message.content


# 📥 RECEBER AVALIAÇÃO
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
):

    nome_limpo = (nome or "cliente").replace(" ", "_")
    telefone_limpo = (telefone or "sem_numero").replace(" ", "")

    cliente_id = f"{nome_limpo}_{telefone_limpo}_{uuid.uuid4().hex[:6]}"

    pasta = os.path.join(UPLOAD_DIR, cliente_id)
    os.makedirs(pasta, exist_ok=True)

    data_brasil = datetime.now(
        ZoneInfo("America/Sao_Paulo")
    ).strftime("%d/%m/%Y %H:%M")

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

    fotos = {
        "frente": salvar_imagem(foto_frente, f"{pasta}/frente.jpg"),
        "traseira": salvar_imagem(foto_traseira, f"{pasta}/traseira.jpg"),
        "lateral1": salvar_imagem(foto_lateral_direita, f"{pasta}/lateral1.jpg"),
        "lateral2": salvar_imagem(foto_lateral_esquerda, f"{pasta}/lateral2.jpg"),
        "interior": salvar_imagem(foto_interior, f"{pasta}/interior.jpg"),
        "motor": salvar_imagem(foto_motor, f"{pasta}/motor.jpg"),
        "painel": salvar_imagem(foto_painel, f"{pasta}/painel.jpg"),
    }

    try:
        dados["relatorio_ai"] = gerar_relatorio_real(fotos, dados["veiculo"])
    except Exception as e:
        dados["relatorio_ai"] = f"Erro IA: {str(e)}"

    with open(f"{pasta}/dados.json", "w", encoding="utf-8") as f:
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

        if not os.path.exists(json_path):
            continue

        with open(json_path, "r", encoding="utf-8") as f:
            dados = json.load(f)

        clientes.append({
            "id": pasta_cliente,
            "dados": dados
        })

    clientes.sort(key=lambda c: c["dados"].get("data", ""), reverse=True)

    html = """
    <html>
    <head>
        <title>Avaliações</title>
        <style>
            body { font-family: Arial; background:#f4f4f4; padding:20px; }
            .card { background:white; padding:15px; margin-bottom:15px; border-radius:10px; box-shadow:0 2px 8px rgba(0,0,0,0.1);}
            .linha { display:flex; justify-content:space-between; align-items:center; }
            .btn { padding:8px 12px; background:black; color:white; text-decoration:none; border-radius:6px; }
        </style>
    </head>
    <body>
        <h1>📊 Avaliações Recebidas</h1>
    """

    for c in clientes:
        d = c["dados"]

        html += f"""
        <div class="card">
            <div class="linha">
                <div>
                    <b>👤 {d.get('nome','')}</b><br>
                    📞 {d.get('telefone','')}<br>
                    ✉️ {d.get('email','')}<br>
                    📅 {d.get('data','')}
                </div>

                <a class="btn" href="/cliente/{c['id']}">
                    Ver relatório
                </a>
            </div>
        </div>
        """

    html += "</body></html>"

    return HTMLResponse(content=html)


# 👤 CLIENTE
@app.get("/cliente/{cliente_id}", response_class=HTMLResponse)
def cliente(cliente_id: str):

    pasta = os.path.join(UPLOAD_DIR, cliente_id)
    json_path = os.path.join(pasta, "dados.json")

    if not os.path.exists(json_path):
        return HTMLResponse("<h1>Cliente não encontrado</h1>")

    with open(json_path, "r", encoding="utf-8") as f:
        dados = json.load(f)

    fotos = [
        f"/uploads/{cliente_id}/{f}"
        for f in os.listdir(pasta)
        if f.endswith(".jpg")
    ]

    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial; background:#f4f4f4; padding:20px; }}
            .card {{ background:white; padding:20px; border-radius:10px; margin-bottom:20px; }}
            img {{ width:180px; margin:5px; border-radius:8px; }}
            pre {{ white-space: pre-wrap; }}
            .btn {{ padding:8px 12px; background:black; color:white; text-decoration:none; border-radius:6px; }}
        </style>
    </head>
    <body>

    <a class="btn" href="/avaliacoes">⬅ Voltar</a>

    <div class="card">
        <h2>{dados.get("nome")}</h2>
        <p>📞 {dados.get("telefone")}</p>
        <p>✉️ {dados.get("email")}</p>
        <p>📅 {dados.get("data")}</p>
    </div>

    <div class="card">
        <h3>📸 Fotos</h3>
    """

    for f in fotos:
        html += f'<img src="{f}"/>'

    html += f"""
    </div>

    <div class="card">
        <h3>🤖 Relatório</h3>
        <pre>{dados.get("relatorio_ai","")}</pre>
    </div>

    </body>
    </html>
    """

    return HTMLResponse(content=html)