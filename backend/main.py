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
import hashlib

app = FastAPI()

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

# 📁 uploads
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


# 💾 salvar imagem
def salvar_imagem(file: UploadFile, path: str):
    if not file:
        return None
    content = file.file.read()
    if not content:
        return None

    with open(path, "wb") as f:
        f.write(content)

    return path


# 🧠 base64
def to_base64(path):
    if not path or not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


# 🔐 hash simples
def gerar_hash(nome, data, nota):
    raw = f"{nome}-{data}-{nota}".encode()
    return hashlib.md5(raw).hexdigest()


# 🧠 PROMPT (NÃO ALTERADO)
def gerar_prompt():
    return """
Você é um PERITO AUTOMOTIVO ESPECIALISTA EM ANTIGOMOBILISMO E ORIGINALIDADE.
... (mantido exatamente igual ao seu original) ...
"""


# 🤖 IA
def gerar_relatorio(fotos, dados):

    imgs = []

    for _, path in fotos.items():
        if not path:
            continue

        b64 = to_base64(path)
        if not b64:
            continue

        imgs.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{b64}"
            }
        })

    prompt = gerar_prompt()

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    *imgs
                ]
            }
        ],
        temperature=0.1
    )

    return response.choices[0].message.content


# 📥 AVALIAÇÃO
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

    cliente_id = f"{nome}_{telefone}_{uuid.uuid4().hex[:6]}".replace(" ", "_")

    pasta = os.path.join(UPLOAD_DIR, cliente_id)
    os.makedirs(pasta, exist_ok=True)

    url_publica = f"/cliente/{cliente_id}"

    dados = {
        "nome": nome,
        "email": email,
        "telefone": telefone,
        "veiculo": {
            "marca": marca,
            "modelo": modelo,
            "ano": ano
        },
        "data": datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M"),
        "id": cliente_id,
        "url": url_publica
    }

    fotos = {
        "frente": salvar_imagem(foto_frente, f"{pasta}/frente.jpg"),
        "traseira": salvar_imagem(foto_traseira, f"{pasta}/traseira.jpg"),
        "lat1": salvar_imagem(foto_lateral_direita, f"{pasta}/lat1.jpg"),
        "lat2": salvar_imagem(foto_lateral_esquerda, f"{pasta}/lat2.jpg"),
        "interior": salvar_imagem(foto_interior, f"{pasta}/interior.jpg"),
        "motor": salvar_imagem(foto_motor, f"{pasta}/motor.jpg"),
        "painel": salvar_imagem(foto_painel, f"{pasta}/painel.jpg"),
        "porta_malas": salvar_imagem(foto_porta_malas, f"{pasta}/porta_malas.jpg"),
        "chassi": salvar_imagem(foto_chassi, f"{pasta}/chassi.jpg"),
        "adicional": salvar_imagem(foto_adicional, f"{pasta}/adicional.jpg"),
    }

    try:
        relatorio = gerar_relatorio(fotos, dados["veiculo"])
        dados["relatorio_ai"] = relatorio
    except Exception as e:
        dados["relatorio_ai"] = str(e)

    with open(f"{pasta}/dados.json", "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)

    return {"ok": True, "id": cliente_id, "url": url_publica}


# 📊 DASHBOARD (🔥 ÚNICA PARTE ALTERADA)
@app.get("/avaliacoes", response_class=HTMLResponse)
def avaliacoes():
    clientes = []

    for pasta in os.listdir(UPLOAD_DIR):
        path = os.path.join(UPLOAD_DIR, pasta, "dados.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                clientes.append((pasta, json.load(f)))

    clientes.reverse()

    html = """
    <html>
    <head>
        <style>
            body {
                font-family: Arial;
                background: linear-gradient(135deg, #eef2f3, #dfe9f3);
                padding: 40px;
            }

            h1 {
                text-align: center;
                margin-bottom: 30px;
                font-size: 28px;
            }

            .grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
                gap: 18px;
                max-width: 1200px;
                margin: auto;
            }

            .card {
                background: #fff;
                padding: 18px;
                border-radius: 14px;
                box-shadow: 0 8px 22px rgba(0,0,0,0.08);
                border-left: 5px solid #111;
                transition: 0.25s ease;
            }

            .card:hover {
                transform: translateY(-4px);
                box-shadow: 0 14px 30px rgba(0,0,0,0.12);
            }

            .btn {
                display: inline-block;
                margin-top: 10px;
                padding: 9px 12px;
                background: #111;
                color: #fff;
                border-radius: 8px;
                text-decoration: none;
                font-size: 13px;
            }

            .muted {
                font-size: 12px;
                opacity: 0.7;
            }
        </style>
    </head>

    <body>
        <h1>🏁 Dashboard de Laudos</h1>

        <div class="grid">
    """

    for id_, d in clientes:
        veiculo = d.get("veiculo", {})

        html += f"""
        <div class="card">
            <b>{d.get('nome')}</b><br>
            {veiculo.get('marca','')} {veiculo.get('modelo','')}<br>
            <span class="muted">{d.get('data')}</span><br>
            <a class="btn" href="/cliente/{id_}">Abrir Laudo</a>
        </div>
        """

    html += """
        </div>
    </body>
    </html>
    """

    return HTMLResponse(html)


# 👤 CLIENTE (INALTERADO)
@app.get("/cliente/{id}", response_class=HTMLResponse)
def cliente(id: str):

    path = os.path.join(UPLOAD_DIR, id, "dados.json")

    if not os.path.exists(path):
        return HTMLResponse("não encontrado")

    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)

    fotos_dir = os.path.join(UPLOAD_DIR, id)
    fotos = [
        f"/uploads/{id}/{f}"
        for f in os.listdir(fotos_dir)
        if f.endswith(".jpg")
    ]

    html = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial;
                background: #ececec;
                padding: 30px;
                color: #111;
            }}

            .container {{
                max-width: 1100px;
                margin: auto;
            }}

            .card {{
                background: #fff;
                padding: 25px;
                margin-bottom: 20px;
                border-radius: 16px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.08);
                border-left: 6px solid #111;
            }}

            h2, h3 {{
                text-align: center;
                font-weight: bold;
            }}

            .info {{
                text-align: center;
                line-height: 1.6;
            }}

            .grid {{
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 12px;
            }}

            .grid img {{
                width: 100%;
                height: 160px;
                object-fit: cover;
                border-radius: 10px;
            }}

            pre {{
                background: #f4f4f4;
                padding: 18px;
                border-radius: 12px;
                white-space: pre-wrap;
                font-size: 14px;
                line-height: 1.6;
            }}
        </style>
    </head>

    <body>
    <div class="container">

        <div class="card">
            <h2>🏁 LAUDO TÉCNICO DE ORIGINALIDADE VEICULAR</h2>
            <div class="info">
                <b>{d.get("nome")}</b><br>
                {d.get("telefone")}<br>
                {d.get("email")}<br>
                {d.get("data")}<br>
                ID: <b>{d.get("id")}</b>
            </div>
        </div>

        <div class="card">
            <h3>📸 FOTOS DO VEÍCULO</h3>
            <div class="grid">
    """

    for f in fotos:
        html += f'<img src="{f}"/>'

    html += f"""
            </div>
        </div>

        <div class="card">
            <h3>🤖 RELATÓRIO TÉCNICO</h3>
            <pre>{d.get("relatorio_ai","")}</pre>
        </div>

        <div class="card">
            <h3>🔐 VALIDAÇÃO DIGITAL</h3>
            <div class="info">
                <b>{gerar_hash(d.get("nome"), d.get("data"), "LAUDO")}</b>
            </div>
        </div>

    </div>
    </body>
    </html>
    """

    return HTMLResponse(html)