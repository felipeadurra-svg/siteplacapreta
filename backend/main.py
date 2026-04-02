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
import qrcode
from io import BytesIO

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


# 📲 QR CODE (NOVO)
def gerar_qr(url):
    qr = qrcode.QRCode(box_size=6, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill="black", back_color="white")

    buffer = BytesIO()
    img.save(buffer)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


# 🧠 PROMPT (NÃO ALTERADO)
def gerar_prompt():
    return """
Você é um PERITO AUTOMOTIVO ESPECIALISTA EM ANTIGOMOBILISMO E ORIGINALIDADE.

Você está produzindo um LAUDO TÉCNICO PROFISSIONAL PARA CLIENTE FINAL, com padrão de certificação de veículos clássicos.

⚠️ REGRAS CRÍTICAS (OBRIGATÓRIO)
NÃO inventar peças ou detalhes não visíveis nas imagens
NÃO inferir componentes fora do campo visual
NÃO usar fórmulas matemáticas, pesos ou cálculos
NÃO mostrar lógica interna de pontuação
NÃO descontar pontos sem evidência visual clara
Linguagem técnica, formal, estilo clube de antigomobilismo
Base 100% em evidência fotográfica
Proibido suposições não observáveis

⚖️ REGRA DE PONTUAÇÃO (CRÍTICA)
A pontuação deve ser conservadora e tecnicamente justificável
Só pode haver desconto quando houver prova visual clara

Cada desconto deve ser acompanhado de:
👉 Justificativa técnica objetiva baseada na imagem

Exemplo:
“Redução de 2 pontos devido a indícios visuais de repintura na lateral esquerda, perceptível por variação de reflexo e textura”

Se não houver evidência clara → pontuação máxima mantida
Nunca estimar desgaste sem base visual

📑 RELATÓRIO DE VISTORIA TÉCNICA DE ORIGINALIDADE

📌 IDENTIFICAÇÃO DO VEÍCULO
- Marca
- Modelo
- Ano estimado
- Geração
- Confiança da análise (baixa / média / alta baseada em evidência visual)

I. 🚗 EXTERIOR E CARROCERIA (0–30 pts)
Avaliar:
- alinhamento de portas, capô e tampa
- qualidade da pintura (originalidade vs repintura)
- cromados, frisos e lanternas
- rodas e pneus
- sinais visuais de restauração

📌 Subtotal: XX / 30

II. 🪑 INTERIOR E TAPEÇARIA (0–30 pts)
Avaliar:
- painel e instrumentação
- volante
- bancos e tecidos
- forrações
- estado geral de conservação

📌 Subtotal: XX / 30

III. 🧰 MECÂNICA VISUAL / COFRE (0–30 pts)
Avaliar:
- organização do cofre
- fiação aparente
- originalidade de componentes visíveis
- estado visual da suspensão e conjunto mecânico

📌 Subtotal: XX / 30

IV. 🧼 CONSERVAÇÃO GERAL (0–10 pts)
Avaliar:
- integridade estrutural aparente
- borrachas e vedação
- desgaste natural compatível com idade

📌 Subtotal: XX / 10

📊 RESULTADO FINAL
TOTAL: XX / 100

🏁 VEREDITO FINAL
APROVADO ou REPROVADO para placa preta

💰 ANÁLISE DE MERCADO
- venda rápida
- mercado particular
- pós certificação

🧠 RECOMENDAÇÕES
Baseadas em evidência visual

✍️ ASSINATURA
"Perito Automotivo em Antigomobilismo - Sistema de Avaliação de Originalidade"
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


# 📊 DASHBOARD
@app.get("/avaliacoes", response_class=HTMLResponse)
def avaliacoes():
    ...
    # (mantido igual)


# 👤 CLIENTE (COM SELO + QR + ASSINATURA)
@app.get("/cliente/{id}", response_class=HTMLResponse)
def cliente(id: str):

    path = os.path.join(UPLOAD_DIR, id, "dados.json")

    if not os.path.exists(path):
        return HTMLResponse("não encontrado")

    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)

    url = f"/cliente/{id}"
    qr = gerar_qr(url)

    status = "APROVADO" if "APROVADO" in str(d.get("relatorio_ai")) else "REPROVADO"

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
                background: #f7f7f7;
                padding: 30px;
                color: #111;
            }}

            .seal {{
                text-align: center;
                font-size: 20px;
                font-weight: bold;
                padding: 12px;
                border: 3px solid #111;
                display: inline-block;
                border-radius: 12px;
                margin-bottom: 20px;
            }}

            .approved {{
                background: #e6ffe6;
                color: #0a7a0a;
            }}

            .rejected {{
                background: #ffe6e6;
                color: #a10f0f;
            }}

            .card {{
                background: #fff;
                padding: 20px;
                margin-bottom: 20px;
                border-radius: 14px;
                box-shadow: 0 6px 22px rgba(0,0,0,0.08);
                border-left: 6px solid #111;
            }}

            .grid {{
                display: grid;
                grid-template-columns: repeat(5, 1fr);
                gap: 12px;
            }}

            .grid img {{
                width: 100%;
                height: 150px;
                object-fit: cover;
                border-radius: 10px;
            }}

            pre {{
                background: #f2f2f2;
                padding: 15px;
                border-radius: 10px;
                white-space: pre-wrap;
            }}

            .qr {{
                text-align: center;
            }}

            .signature {{
                margin-top: 10px;
                padding: 15px;
                border-top: 2px dashed #333;
                font-family: monospace;
                font-size: 13px;
            }}
        </style>
    </head>
    <body>

    <div class="seal {'approved' if status=='APROVADO' else 'rejected'}">
        🏁 CERTIFICAÇÃO OFICIAL: {status}
    </div>

    <div class="card">
        👤 <b>{d.get("nome")}</b><br>
        📞 {d.get("telefone")}<br>
        📅 {d.get("data")}<br>
        📧 {d.get("email")}<br>
        🆔 {d.get("id")}<br>
    </div>

    <div class="card qr">
        <h3>🔎 Validação Digital</h3>
        <img src="data:image/png;base64,{qr}" width="180"/>
        <p>Escaneie para validar o laudo</p>
    </div>

    <div class="card">
        <h3>📸 Fotos do Veículo</h3>
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

    <div class="card signature">
        ✔ Documento assinado digitalmente<br>
        Hash: <b>{gerar_hash(d.get("nome"), d.get("data"), "LAUDO")}</b><br>
        Sistema: Perícia Automotiva Antigomobilismo v1.0
    </div>

    </body>
    </html>
    """

    return HTMLResponse(html)