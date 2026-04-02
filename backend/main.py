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


# 🚀 RELATÓRIO NÍVEL VISTORIA REAL
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
Você é um PERITO AUTOMOTIVO ESPECIALIZADO EM VEÍCULOS ANTIGOS, atuando com padrão técnico de vistoria para certificação de originalidade e conservação (placa preta).

DADOS DO VEÍCULO:
- Marca: {dados_veiculo.get("marca")}
- Modelo: {dados_veiculo.get("modelo")}
- Ano: {dados_veiculo.get("ano")}

REGRAS OBRIGATÓRIAS:
- Analise SOMENTE o que estiver visível nas imagens
- NÃO invente informações
- NÃO use linguagem genérica
- NÃO use termos vagos como "parece bom"
- Seja técnico, objetivo e direto
- Quando algo não for visível: escreva "não visível nas imagens"
- Aponte inconsistências entre fotos se existirem

---

CRITÉRIOS (NOTA 0 A 100):

1. ORIGINALIDADE
2. LATARIA E PINTURA
3. INTERIOR
4. MOTOR E COMPONENTES VISÍVEIS
5. ESTRUTURA
6. CONSERVAÇÃO GERAL

---

PARA CADA ITEM:
- Descrever tecnicamente o que está visível
- Dar nota de 0 a 100

---

ANÁLISE POR IMAGEM:
- Descrever objetivamente cada imagem
- Identificar defeitos visuais reais (riscos, desalinhamento, desgaste, etc)

---

CÁLCULO FINAL:
- Calcular média das notas
- Gerar NOTA FINAL (0 a 100)

---

PLACA PRETA:
- Mínimo aceitável: 80 pontos
- Informar: APTO ou NÃO APTO
- Justificar tecnicamente

---

AVALIAÇÃO DE MERCADO:
- Estimar valor em reais (R$)
- Baseado no estado visual
- Considerar mercado brasileiro de clássicos

---

FORMATO FINAL:

1. Resumo técnico geral  
2. Análise por imagem  
3. Avaliação por critérios (com notas)  
4. Nota final  
5. Status placa preta (APTO / NÃO APTO)  
6. Avaliação de mercado  

Gere um relatório técnico de vistoria, objetivo, detalhado e profissional.
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


# 📥 ENDPOINT
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

    nome_limpo = (nome or "cliente").strip().replace(" ", "_")
    telefone_limpo = (telefone or "sem_numero").strip().replace(" ", "")

    cliente_id = f"{nome_limpo}_{telefone_limpo}_{uuid.uuid4().hex[:6]}"

    pasta = os.path.join(UPLOAD_DIR, cliente_id)
    os.makedirs(pasta, exist_ok=True)

    dados = {
        "nome": nome,
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
        "lateral_direita": salvar_imagem(foto_lateral_direita, f"{pasta}/lateral1.jpg"),
        "lateral_esquerda": salvar_imagem(foto_lateral_esquerda, f"{pasta}/lateral2.jpg"),
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


# 📊 DASHBOARD
@app.get("/avaliacoes", response_class=HTMLResponse)
def avaliacoes():
    html = "<h1>📊 Avaliações</h1>"

    for pasta in os.listdir(UPLOAD_DIR):
        html += f'<div><a href="/cliente/{pasta}">{pasta}</a></div>'

    return HTMLResponse(html)


# 👤 CLIENTE
@app.get("/cliente/{cliente_id}", response_class=HTMLResponse)
def cliente(cliente_id: str):

    path = f"{UPLOAD_DIR}/{cliente_id}/dados.json"

    if not os.path.exists(path):
        return HTMLResponse("Não encontrado")

    with open(path, "r", encoding="utf-8") as f:
        dados = json.load(f)

    html = f"""
    <h2>{dados.get("nome")}</h2>
    <pre>{dados.get("relatorio_ai")}</pre>
    """

    return HTMLResponse(html)