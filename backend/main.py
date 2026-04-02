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


# 🤖 IA VISTORIA NÍVEL PERITO
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

    prompt = f"""
Você é um PERITO AUTOMOTIVO ESPECIALISTA EM VISTORIA DE VEÍCULOS CLÁSSICOS E ANTIGOS.

---

## DADOS DO FORMULÁRIO
Marca informada: {dados.get("marca")}
Modelo informado: {dados.get("modelo")}
Ano informado: {dados.get("ano")}

---

## ETAPA 1 — IDENTIFICAÇÃO DO VEÍCULO

Analise as imagens e determine:

- Marca provável
- Modelo provável
- Ano aproximado ou geração
- País de origem
- Nível de confiança (%)

Se não tiver certeza:
- declare IDENTIFICAÇÃO INCONCLUSIVA
- explique o motivo

---

## ETAPA 2 — REFERÊNCIA ORIGINAL DE FÁBRICA

Descreva como o veículo ORIGINAL deveria ser:

- motor original esperado
- interior original
- painel original
- rodas originais
- lanternas/faróis originais
- acabamento de fábrica

Se não identificar o modelo:
→ use referência genérica de veículo clássico similar

---

## ETAPA 3 — ANÁLISE DAS IMAGENS

Analise cada imagem:

📸 Imagem 1:
📸 Imagem 2:
📸 Imagem 3:
...

Para cada:
- descrição técnica
- estado de conservação
- alterações visíveis
- observações relevantes

---

## ETAPA 4 — ORIGINALIDADE REAL (%)

Compare com padrão original e avalie:

- % originalidade geral
- peças não originais
- sinais de restauração
- sinais de modificação

---

## ETAPA 5 — AVALIAÇÃO TÉCNICA (0–100)

- Originalidade
- Lataria/Pintura
- Interior
- Motor
- Estrutura
- Conservação geral

---

## ETAPA 6 — NOTA FINAL

Explique tecnicamente a nota final.

---

## ETAPA 7 — STATUS PLACA PRETA

- APROVADO / REPROVADO / EM ANÁLISE
- justificativa técnica

---

## ETAPA 8 — VALOR DE MERCADO

Estimativa baseada em:
- modelo identificado
- originalidade
- conservação
- raridade
"""

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


# 📥 upload
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

    cliente_id = f"{nome}_{telefone}_{uuid.uuid4().hex[:6]}".replace(" ", "_")

    pasta = os.path.join(UPLOAD_DIR, cliente_id)
    os.makedirs(pasta, exist_ok=True)

    dados = {
        "nome": nome,
        "email": email,
        "telefone": telefone,
        "veiculo": {
            "marca": marca,
            "modelo": modelo,
            "ano": ano
        },
        "data": datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M")
    }

    fotos = {
        "frente": salvar_imagem(foto_frente, f"{pasta}/frente.jpg"),
        "traseira": salvar_imagem(foto_traseira, f"{pasta}/traseira.jpg"),
        "lat1": salvar_imagem(foto_lateral_direita, f"{pasta}/lat1.jpg"),
        "lat2": salvar_imagem(foto_lateral_esquerda, f"{pasta}/lat2.jpg"),
        "interior": salvar_imagem(foto_interior, f"{pasta}/interior.jpg"),
        "motor": salvar_imagem(foto_motor, f"{pasta}/motor.jpg"),
        "painel": salvar_imagem(foto_painel, f"{pasta}/painel.jpg"),
    }

    try:
        dados["relatorio_ai"] = gerar_relatorio(fotos, dados["veiculo"])
    except Exception as e:
        dados["relatorio_ai"] = str(e)

    with open(f"{pasta}/dados.json", "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)

    return {"ok": True, "id": cliente_id}


# 📊 DASHBOARD
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
    <h1>📊 Dashboard</h1>
    """

    for id_, d in clientes:
        html += f"""
        <div class="card">
            <b>{d.get('nome')}</b><br>
            📞 {d.get('telefone')}<br>
            📅 {d.get('data')}<br><br>

            <a class="btn" href="/cliente/{id_}">Ver relatório</a>
        </div>
        """

    html += "</body></html>"
    return HTMLResponse(html)


# 👤 CLIENTE
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
            body {{ font-family: Arial; background:#f4f4f4; padding:20px; }}

            .card {{
                background:#fff;
                padding:15px;
                margin-bottom:15px;
                border-radius:10px;
            }}

            .grid {{
                display:grid;
                grid-template-columns: repeat(4, 1fr);
                gap:10px;
            }}

            .grid img {{
                width:100%;
                height:140px;
                object-fit:cover;
                border-radius:8px;
            }}

            pre {{
                white-space:pre-wrap;
            }}

            .btn {{
                background:#000;
                color:#fff;
                padding:8px 12px;
                text-decoration:none;
                border-radius:6px;
                display:inline-block;
                margin-bottom:10px;
            }}
        </style>
    </head>
    <body>

    <a class="btn" href="/avaliacoes">⬅ Voltar</a>

    <div class="card">
        <b>{d.get("nome")}</b><br>
        📞 {d.get("telefone")}<br>
        📅 {d.get("data")}
    </div>

    <div class="card">
        <h3>📸 Fotos</h3>
        <div class="grid">
    """

    for f in fotos:
        html += f'<img src="{f}"/>'

    html += """
        </div>
    </div>

    <div class="card">
        <h3>🤖 Relatório Técnico</h3>
        <pre>{}</pre>
    </div>

    </body>
    </html>
    """.format(d.get("relatorio_ai", ""))

    return HTMLResponse(html)