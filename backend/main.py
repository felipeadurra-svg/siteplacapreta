from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from typing import Optional, List
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


def gerar_hash(nome, data, nota):
    raw = f"{nome}-{data}-{nota}".encode()
    return hashlib.md5(raw).hexdigest()


def gerar_prompt():
    return """
Você é um PERITO AUTOMOTIVO ESPECIALISTA EM ANTIGOMOBILISMO E ORIGINALIDADE.

Você está produzindo um LAUDO TÉCNICO PROFISSIONAL PARA CLIENTE FINAL.

⚠️ REGRAS CRÍTICAS:
- NÃO inventar peças não visíveis
- NÃO usar fórmulas, pesos ou cálculos
- NÃO mostrar lógica de pontuação
- Linguagem técnica estilo clube de antigomobilismo
- Base apenas em evidência visual

────────────────────────────────────────

📑 RELATÓRIO DE VISTORIA TÉCNICA DE ORIGINALIDADE

📌 IDENTIFICAÇÃO DO VEÍCULO
- Marca
- Modelo
- Ano estimado
- Geração
- Confiança da análise

────────────────────────────────────────

I. 🚗 EXTERIOR E CARROCERIA (0–30 pts)
Avaliar:
- alinhamento de portas, capô e tampa
- pintura (original / repintura / verniz moderno)
- cromados e lanternas
- rodas e pneus
- sinais de restauração

📌 Subtotal: XX / 30

────────────────────────────────────────

II. 🪑 INTERIOR E TAPEÇARIA (0–30 pts)
Avaliar:
- painel e instrumentação
- volante
- bancos e tecidos
- forrações
- conservação geral

📌 Subtotal: XX / 30

────────────────────────────────────────

III. 🧰 MECÂNICA VISUAL / COFRE (0–30 pts)
Avaliar:
- organização do cofre
- fiação aparente
- componentes originais visíveis
- suspensão e rodas (aspecto visual)

📌 Subtotal: XX / 30

────────────────────────────────────────

IV. 🧼 CONSERVAÇÃO GERAL (0–10 pts)
Avaliar:
- estrutura
- borrachas
- desgaste natural

📌 Subtotal: XX / 10

────────────────────────────────────────

📊 RESULTADO FINAL
TOTAL: XX / 100

────────────────────────────────────────

🏁 VEREDITO FINAL
APROVADO ou REPROVADO para placa preta

────────────────────────────────────────

💰 ANÁLISE DE MERCADO
- venda rápida
- mercado particular
- pós certificação

────────────────────────────────────────

🧠 RECOMENDAÇÕES
- melhorias técnicas
- peças originais
- ajustes para aprovação futura

────────────────────────────────────────

✍️ ASSINATURA
"Perito Automotivo em Antigomobilismo - Sistema de Avaliação de Originalidade"
"""


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

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": gerar_prompt()},
                    *imgs
                ]
            }
        ],
        temperature=0.1
    )

    return response.choices[0].message.content


# 📥 AVALIAÇÃO (AGORA CORRETO - 10 FOTOS DINÂMICAS)
@app.post("/avaliacao")
async def avaliacao(
    nome: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    telefone: Optional[str] = Form(None),
    marca: Optional[str] = Form(None),
    modelo: Optional[str] = Form(None),
    ano: Optional[str] = Form(None),

    fotos_upload: List[UploadFile] = File(...)
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

    nomes = [
        "frente",
        "traseira",
        "lat1",
        "lat2",
        "interior",
        "painel",
        "motor",
        "extra1",
        "extra2",
        "extra3",
    ]

    fotos = {}

    for i, file in enumerate(fotos_upload):
        if i >= len(nomes):
            break

        nome = nomes[i]
        path = f"{pasta}/{nome}.jpg"

        fotos[nome] = salvar_imagem(file, path)

    try:
        relatorio = gerar_relatorio(fotos, dados["veiculo"])
        dados["relatorio_ai"] = relatorio
    except Exception as e:
        dados["relatorio_ai"] = str(e)

    with open(f"{pasta}/dados.json", "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)

    return {"ok": True, "id": cliente_id, "url": url_publica}


# 📊 DASHBOARD (INALTERADO)
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
            body { font-family: Arial; background:#f4f4f4; padding:20px; }
            .card { background:#fff; padding:15px; margin-bottom:15px; border-radius:10px; }
            .btn { background:#000; color:#fff; padding:8px 12px; text-decoration:none; border-radius:6px; }
        </style>
    </head>
    <body>
    <h1>📊 Dashboard Vistoria Placa Preta</h1>
    """

    for id_, d in clientes:
        html += f"""
        <div class="card">
            👤 <b>{d.get('nome')}</b><br>
            📞 {d.get('telefone')}<br>
            📅 {d.get('data')}<br>
            📧 {d.get('email')}<br>
            🆔 {id_}<br>
            🌐 <a class="btn" href="/cliente/{id_}" target="_blank">Abrir relatório</a>
        </div>
        """

    html += "</body></html>"
    return HTMLResponse(html)


# 👤 CLIENTE (5x2 GRID CORRIGIDO)
@app.get("/cliente/{id}", response_class=HTMLResponse)
def cliente(id: str):

    path = os.path.join(UPLOAD_DIR, id, "dados.json")

    if not os.path.exists(path):
        return HTMLResponse("não encontrado")

    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)

    fotos_dir = os.path.join(UPLOAD_DIR, id)

    fotos = [
        f"/uploads/{id}/frente.jpg",
        f"/uploads/{id}/traseira.jpg",
        f"/uploads/{id}/lat1.jpg",
        f"/uploads/{id}/lat2.jpg",
        f"/uploads/{id}/interior.jpg",
        f"/uploads/{id}/painel.jpg",
        f"/uploads/{id}/motor.jpg",
        f"/uploads/{id}/extra1.jpg",
        f"/uploads/{id}/extra2.jpg",
        f"/uploads/{id}/extra3.jpg",
    ]

    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial; background:#f4f4f4; padding:20px; }}
            .card {{ background:#fff; padding:15px; margin-bottom:15px; border-radius:10px; }}

            .grid {{
                display:grid;
                grid-template-columns: repeat(5, 1fr);
                gap:10px;
            }}

            .grid img {{
                width:100%;
                height:140px;
                object-fit:cover;
                border-radius:8px;
            }}

            pre {{ white-space:pre-wrap; }}
        </style>
    </head>
    <body>

    <div class="card">
        👤 <b>{d.get("nome")}</b><br>
        📞 {d.get("telefone")}<br>
        📅 {d.get("data")}<br>
        📧 {d.get("email")}<br>
        🆔 {d.get("id")}<br>
    </div>

    <div class="card">
        <h3>📸 Fotos</h3>
        <div class="grid">
    """

    for f in fotos:
        html += f'<img src="{f}"/>'

    html += f"""
        </div>
    </div>

    <div class="card">
        <h3>🤖 Relatório Técnico</h3>
        <pre>{d.get("relatorio_ai","")}</pre>
    </div>

    <div class="card">
        <h3>🏁 Validação</h3>
        <p>Assinatura digital: <b>{gerar_hash(d.get("nome"), d.get("data"), "LAUDO")}</b></p>
    </div>

    </body>
    </html>
    """

    return HTMLResponse(html)