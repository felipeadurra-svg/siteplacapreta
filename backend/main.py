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

Você está produzindo um LAUDO TÉCNICO PROFISSIONAL PARA CLIENTE FINAL.

⚠️ REGRAS CRÍTICAS:
- NÃO inventar peças não visíveis
- NÃO inferir itens fora do campo visual
- NÃO usar fórmulas, pesos ou cálculos
- NÃO mostrar lógica interna de pontuação
- Linguagem técnica estilo clube de antigomobilismo
- Base exclusivamente em evidência visual
- PROIBIDO desconto sem justificativa técnica clara
- PROIBIDO análise de mercado sem valores em R$

────────────────────────────────────────

⚖️ REGRA DE PONTUAÇÃO (OBRIGATÓRIA)

A avaliação deve ser CONSERVADORA e JUSTA.

- A pontuação deve priorizar notas altas quando não houver evidência clara de problema
- Descontos devem ser MÍNIMOS e proporcionais

📌 Diretrizes de desconto:
- Pequenas inconsistências visuais → desconto de 1 ponto
- Problemas moderados visíveis → até 2 pontos
- Problemas evidentes e claros → até 3 pontos (máximo por item)

❗ REGRA PRINCIPAL:
Se não houver evidência visual clara → NÃO DESCONTAR

📌 OBRIGATÓRIO:
Todo desconto deve vir acompanhado de justificativa técnica objetiva

Formato obrigatório:
“Redução de X ponto(s) devido a [descrição objetiva do que é visível]”

Exemplo:
“Redução de 1 ponto devido a leve desalinhamento visual entre capô e paralama”
“Redução de 2 pontos devido a diferença de tonalidade indicando possível repintura”

⚠️ PROIBIDO:
- Descontar por suposição
- Descontar por desgaste presumido
- Descontos genéricos sem explicação

────────────────────────────────────────

📑 RELATÓRIO DE VISTORIA TÉCNICA DE ORIGINALIDADE

📌 IDENTIFICAÇÃO DO VEÍCULO
- Marca
- Modelo
- Ano estimado
- Geração
- Confiança da análise (baixa / média / alta)

────────────────────────────────────────

I. 🚗 EXTERIOR E CARROCERIA (0–30 pts)

Avaliar:
- alinhamento de portas, capô e tampa
- pintura (original / repintura / verniz moderno)
- cromados e lanternas
- rodas e pneus
- sinais de restauração

📌 Apresentar observações técnicas
📌 Listar descontos (quando houver)
📌 Subtotal: XX / 30

────────────────────────────────────────

II. 🪑 INTERIOR E TAPEÇARIA (0–30 pts)

Avaliar:
- painel e instrumentação
- volante
- bancos e tecidos
- forrações
- conservação geral

📌 Apresentar observações técnicas
📌 Listar descontos (quando houver)
📌 Subtotal: XX / 30

────────────────────────────────────────

III. 🧰 MECÂNICA VISUAL / COFRE (0–30 pts)

Avaliar:
- organização do cofre
- fiação aparente
- componentes originais visíveis
- suspensão e rodas (aspecto visual)

📌 Apresentar observações técnicas
📌 Listar descontos (quando houver)
📌 Subtotal: XX / 30

────────────────────────────────────────

IV. 🧼 CONSERVAÇÃO GERAL (0–10 pts)

Avaliar:
- estrutura aparente
- borrachas
- desgaste natural compatível

📌 Apresentar observações técnicas
📌 Listar descontos (quando houver)
📌 Subtotal: XX / 10

────────────────────────────────────────

📊 RESULTADO FINAL
TOTAL: XX / 100

────────────────────────────────────────

🏁 VEREDITO FINAL
APROVADO ou REPROVADO para placa preta

────────────────────────────────────────

💰 ANÁLISE DE MERCADO (BRASIL – VALORES REAIS EM R$)

A avaliação deve apresentar valores reais baseados no mercado brasileiro de veículos clássicos.

Considerar:
- estado visual observado
- originalidade
- conservação
- demanda do modelo

📌 Apresentar obrigatoriamente:

💸 Venda rápida:
R$ XXXXX a R$ XXXXX

💰 Mercado particular:
R$ XXXXX a R$ XXXXX

🏆 Pós placa preta:
R$ XXXXX a R$ XXXXX

⚠️ PROIBIDO:
- Não usar termos genéricos
- Não omitir valores
- Não usar outra moeda

────────────────────────────────────────

🧠 RECOMENDAÇÕES

Baseadas exclusivamente nas imagens:

- correções de originalidade
- ajustes estéticos visíveis
- melhorias para valorização
- pontos necessários para aprovação em placa preta

────────────────────────────────────────

✍️ ASSINATURA

Perito Automotivo em Antigomobilismo  
Sistema de Avaliação de Originalidade
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


# 📊 DASHBOARD (ÚNICA ALTERAÇÃO: VISUAL EM CARDS)
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
                margin: 0;
                font-family: Arial;
                background: #ececec;
                display: flex;
                justify-content: center;
                padding: 40px;
            }

            .container {
                width: 100%;
                max-width: 1100px;
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                gap: 20px;
            }

            .card {
                background: #fff;
                border-radius: 16px;
                padding: 20px;
                box-shadow: 0 10px 25px rgba(0,0,0,0.08);
                text-align: center;
            }

            .name {
                font-size: 18px;
                font-weight: bold;
                margin-bottom: 10px;
            }

            .info {
                font-size: 14px;
                color: #444;
                line-height: 1.6;
                margin-bottom: 15px;
            }

            .btn {
                display: inline-block;
                padding: 10px 15px;
                background: #111;
                color: #fff;
                text-decoration: none;
                border-radius: 10px;
                font-weight: bold;
            }

            h1 {
                text-align: center;
                width: 100%;
                margin-bottom: 30px;
            }
        </style>
    </head>

    <body>
    <div style="width:100%">
        <h1>Dashboard</h1>

        <div class="container">
    """

    for id_, d in clientes:
        html += f"""
        <div class="card">
            <div class="name">{d.get('nome')}</div>
            <div class="info">
                📱 {d.get('telefone')}<br>
                📧 {d.get('email')}<br>
                🆔 {d.get('id')}
            </div>
            <a class="btn" href="/cliente/{id_}">Abrir relatório</a>
        </div>
        """

    html += """
        </div>
    </div>
    </body>
    </html>
    """

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
    <body>
        <h2>{d.get("nome")}</h2>
        <p>{d.get("telefone")} - {d.get("email")}</p>
        <p>ID: {d.get("id")}</p>
    </body>
    </html>
    """

    return HTMLResponse(html)