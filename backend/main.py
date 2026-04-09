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

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = "gpt-4o"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# ------------------ FUNÇÕES ------------------

def salvar_imagem(file: UploadFile, path: str):
    if not file:
        return None
    content = file.file.read()
    if not content:
        return None
    with open(path, "wb") as f:
        f.write(content)
    return path

def to_base64(path):
    if not path or not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

# ------------------ PROMPT ------------------

def gerar_prompt():
    return """
Você é um perito automotivo.

⚠️ REGRAS:
- NÃO gerar texto livre
- NÃO criar relatório
- NÃO criar layout
- NÃO escrever nada fora do JSON

Sua única função é analisar imagens e retornar JSON:

{
  "exterior": {"observacoes": "", "subtotal": 0},
  "interior": {"observacoes": "", "subtotal": 0},
  "mecanica": {"observacoes": "", "subtotal": 0},
  "conservacao": {"observacoes": "", "subtotal": 0},
  "total": 0,
  "veredito": "",
  "mercado": {
    "venda_rapida": "",
    "particular": "",
    "pos_placa_preta": ""
  },
  "recomendacoes": []
}
"""

# ------------------ IA ------------------

def gerar_relatorio(fotos):
    imgs = []
    for _, path in fotos.items():
        if not path:
            continue
        b64 = to_base64(path)
        if b64:
            imgs.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
            })

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{
            "role": "user",
            "content": [{"type": "text", "text": gerar_prompt()}, *imgs]
        }],
        temperature=0.1
    )

    content = response.choices[0].message.content

    try:
        return json.loads(content)
    except:
        return {"erro": content}

# ------------------ POST ------------------

@app.post("/avaliacao")
async def avaliacao(
    nome: Optional[str] = Form(None),
    marca: Optional[str] = Form(None),
    modelo: Optional[str] = Form(None),
    ano: Optional[str] = Form(None),
    foto_frente: Optional[UploadFile] = File(None),
    foto_traseira: Optional[UploadFile] = File(None),
):

    cliente_id = f"{nome}_{uuid.uuid4().hex[:6]}".replace(" ", "_")
    pasta = os.path.join(UPLOAD_DIR, cliente_id)
    os.makedirs(pasta, exist_ok=True)

    fotos = {
        "frente": salvar_imagem(foto_frente, f"{pasta}/frente.jpg"),
        "traseira": salvar_imagem(foto_traseira, f"{pasta}/traseira.jpg"),
    }

    relatorio = gerar_relatorio(fotos)

    dados = {
        "nome": nome,
        "veiculo": {"marca": marca, "modelo": modelo, "ano": ano},
        "data": datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M"),
        "id": cliente_id,
        "relatorio_ai": relatorio
    }

    with open(f"{pasta}/dados.json", "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)

    return {"ok": True, "id": cliente_id}

# ------------------ DASHBOARD ------------------

@app.get("/avaliacoes", response_class=HTMLResponse)
def dashboard():
    clientes = []

    for pasta in os.listdir(UPLOAD_DIR):
        path = os.path.join(UPLOAD_DIR, pasta, "dados.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                clientes.append(json.load(f))

    clientes.reverse()

    html = """
    <html>
    <body style="font-family:Arial;padding:20px;background:#f2f2f2">
    <h1>📊 Dashboard</h1>
    """

    for d in clientes:
        r = d.get("relatorio_ai", {})

        html += f"""
        <div style="background:#fff;padding:15px;margin-bottom:10px;border-radius:10px">
            <b>{d.get('nome')}</b><br>
            🚗 {d.get('veiculo')['marca']} {d.get('veiculo')['modelo']}<br>
            📅 {d.get('data')}<br><br>

            ⭐ Score: {r.get('total')}<br>
            🏁 Veredito: {r.get('veredito')}<br><br>

            <a href="/cliente/{d.get('id')}">Abrir Laudo</a>
        </div>
        """

    html += "</body></html>"
    return HTMLResponse(html)

# ------------------ LAUDO ------------------

@app.get("/cliente/{id}", response_class=HTMLResponse)
def cliente(id: str):
    path = os.path.join(UPLOAD_DIR, id, "dados.json")
    if not os.path.exists(path):
        return HTMLResponse("Não encontrado")

    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)

    r = d.get("relatorio_ai", {})

    return f"""
    <html><body style="font-family:Arial;padding:40px">

    <h1>LAUDO COMPLETO</h1>

    <h2>Exterior</h2>
    <p>{r.get('exterior', {}).get('observacoes')}</p>

    <h2>Interior</h2>
    <p>{r.get('interior', {}).get('observacoes')}</p>

    <h2>Mecânica</h2>
    <p>{r.get('mecanica', {}).get('observacoes')}</p>

    <h2>Conservação</h2>
    <p>{r.get('conservacao', {}).get('observacoes')}</p>

    <h1>Score: {r.get('total')}</h1>
    <h1>{r.get('veredito')}</h1>

    </body></html>
    """