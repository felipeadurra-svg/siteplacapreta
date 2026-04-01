from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from typing import Optional
from datetime import datetime
from zoneinfo import ZoneInfo
import os
import uuid
import json

app = FastAPI()

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

    try:
        content = file.file.read()
        if not content:
            return None

        with open(caminho, "wb") as f:
            f.write(content)

        return caminho
    except Exception as e:
        print("Erro imagem:", e)
        return None


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

    # 🇧🇷 horário Brasília
    data_brasil = datetime.now(
        ZoneInfo("America/Sao_Paulo")
    ).strftime("%d/%m/%Y %H:%M:%S")

    # 💾 dados do cliente
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

    # 📸 fotos
    fotos = {
        "frente": salvar_imagem(foto_frente, f"{pasta}/frente.jpg"),
        "traseira": salvar_imagem(foto_traseira, f"{pasta}/traseira.jpg"),
        "lateral_direita": salvar_imagem(foto_lateral_direita, f"{pasta}/lateral_direita.jpg"),
        "lateral_esquerda": salvar_imagem(foto_lateral_esquerda, f"{pasta}/lateral_esquerda.jpg"),
        "interior": salvar_imagem(foto_interior, f"{pasta}/interior.jpg"),
        "painel": salvar_imagem(foto_painel, f"{pasta}/painel.jpg"),
        "motor": salvar_imagem(foto_motor, f"{pasta}/motor.jpg"),
        "porta_malas": salvar_imagem(foto_porta_malas, f"{pasta}/porta_malas.jpg"),
        "chassi": salvar_imagem(foto_chassi, f"{pasta}/chassi.jpg"),
        "adicional": salvar_imagem(foto_adicional, f"{pasta}/adicional.jpg"),
    }

    dados["fotos"] = fotos

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

        clientes.append({
            "id": pasta_cliente,
            "dados": dados
        })

    # 🔥 mais recente primeiro
    clientes.sort(
        key=lambda c: c["dados"].get("data", ""),
        reverse=True
    )

    html = """
    <html>
    <head>
        <title>Avaliações</title>
        <style>
            body { font-family: Arial; background:#f4f4f4; padding:20px; }
            .card { background:white; padding:15px; margin-bottom:15px; border-radius:10px; }
            .btn { padding:8px 12px; background:black; color:white; text-decoration:none; border-radius:6px; }
            .linha { display:flex; justify-content:space-between; align-items:center; }
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
                    <b>👤 {d.get('nome','Sem nome')}</b><br>
                    📞 {d.get('telefone','')}<br>
                    ✉️ {d.get('email','Não informado')}<br>
                    📅 {d.get('data','')}
                </div>

                <a class="btn" href="/cliente/{c['id']}">Ver</a>
            </div>
        </div>
        """

    html += "</body></html>"

    return HTMLResponse(content=html)


# 👤 CLIENTE INDIVIDUAL
@app.get("/cliente/{cliente_id}", response_class=HTMLResponse)
def cliente(cliente_id: str):

    pasta = os.path.join(UPLOAD_DIR, cliente_id)
    json_path = os.path.join(pasta, "dados.json")

    if not os.path.exists(json_path):
        return HTMLResponse("<h1>Cliente não encontrado</h1>")

    with open(json_path, "r", encoding="utf-8") as f:
        dados = json.load(f)

    fotos = []
    for file in os.listdir(pasta):
        if file.endswith(".jpg"):
            fotos.append(f"/uploads/{cliente_id}/{file}")

    html = f"""
    <html>
    <head>
        <title>Cliente</title>
        <style>
            body {{ font-family: Arial; background:#f4f4f4; padding:20px; }}
            .card {{ background:white; padding:15px; border-radius:10px; }}
            img {{ width:200px; border-radius:8px; margin:5px; }}
        </style>
    </head>
    <body>

    <a href="/avaliacoes">⬅ Voltar</a>

    <div class="card">
        <h2>👤 {dados.get('nome','')}</h2>
        <p>📞 {dados.get('telefone','')}</p>
        <p>✉️ {dados.get('email','')}</p>
        <p>📅 {dados.get('data','')}</p>

        <h3>📸 Fotos</h3>
    """

    for f in fotos:
        html += f'<img src="{f}"/>'

    html += "</div></body></html>"

    return HTMLResponse(content=html)