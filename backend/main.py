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
import re

app = FastAPI()

# 🔑 Configuração da OpenAI
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

# 📁 Configuração de Diretórios
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


def salvar_imagem(file: UploadFile, path: str):
    if not file: return None
    try:
        content = file.file.read()
        if not content: return None
        with open(path, "wb") as f:
            f.write(content)
        return path
    except: return None


def to_base64(path):
    if not path or not os.path.exists(path): return None
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def gerar_prompt():
    return """
Você é um PERITO AUTOMOTIVO ESPECIALISTA EM ANTIGOMOBILISMO E ORIGINALIDADE.
Você está produzindo um LAUDO TÉCNICO PROFISSIONAL PARA CLIENTE FINAL.

⚠️ REGRAS CRÍTICAS:
- NÃO inventar peças não visíveis
- NÃO usar fórmulas ou cálculos no texto
- Linguagem técnica estilo clube de antigomobilismo
- Base exclusivamente em evidência visual
- Todo desconto deve vir acompanhado de justificativa técnica objetiva

Formato obrigatório para descontos:
“Redução de X ponto(s) devido a [descrição objetiva]”

────────────────────────────────────────

📌 IDENTIFICAÇÃO DO VEÍCULO
- Marca
- Modelo
- Ano estimado
- Geração
- Confiança da análise (baixa / média / alta)

────────────────────────────────────────

I. 🚗 EXTERIOR E CARROCERIA (0–30 pts)
Avaliar: alinhamento, pintura, cromados, rodas e restauração.
📌 Apresentar observações técnicas e descontos.
📌 Subtotal: XX / 30

────────────────────────────────────────

II. 🪑 INTERIOR E TAPEÇARIA (0–30 pts)
Avaliar: painel, volante, bancos, forrações e conservação.
📌 Apresentar observações técnicas e descontos.
📌 Subtotal: XX / 30

────────────────────────────────────────

III. 🧰 MECÂNICA VISUAL / COFRE (0–30 pts)
Avaliar: cofre, fiação, componentes originais e suspensão visual.
📌 Apresentar observações técnicas e descontos.
📌 Subtotal: XX / 30

────────────────────────────────────────

IV. 🧼 CONSERVAÇÃO GERAL (0–10 pts)
Avaliar: estrutura, borrachas, cuidado e desgaste natural.
📌 Apresentar observações técnicas e descontos.
📌 Subtotal: XX / 10

────────────────────────────────────────

📊 RESULTADO FINAL
TOTAL: XX / 100

────────────────────────────────────────

🏁 VEREDITO FINAL
APROVADO ou REPROVADO para placa preta

────────────────────────────────────────

💰 ANÁLISE DE MERCADO (BRASIL – VALORES REAIS EM R$)
💸 Venda rápida: R$ XXXXX a R$ XXXXX
💰 Mercado particular: R$ XXXXX a R$ XXXXX
🏆 Pós placa preta: R$ XXXXX a R$ XXXXX

────────────────────────────────────────

🧠 RECOMENDAÇÕES
Baseadas exclusivamente nas imagens: correções de originalidade, estética e valorização.

────────────────────────────────────────

✍️ ASSINATURA
Perito Automotivo em Antigomobilismo
"""

def gerar_relatorio(fotos):
    imgs = []
    for _, path in fotos.items():
        if not path or not os.path.exists(path): continue
        b64 = to_base64(path)
        if b64: imgs.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})
    
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": [{"type": "text", "text": gerar_prompt()}, *imgs]}],
            temperature=0.1
        )
        return response.choices.message.content
    except Exception as e:
        return f"Erro na IA: {str(e)}"

@app.post("/avaliacao")
async def avaliacao(
    nome: Optional[str] = Form(None), marca: Optional[str] = Form(None), 
    modelo: Optional[str] = Form(None), ano: Optional[str] = Form(None),
    foto_frente: Optional[UploadFile] = File(None), foto_traseira: Optional[UploadFile] = File(None),
    foto_lateral_direita: Optional[UploadFile] = File(None), foto_lateral_esquerda: Optional[UploadFile] = File(None),
    foto_interior: Optional[UploadFile] = File(None), foto_painel: Optional[UploadFile] = File(None),
    foto_motor: Optional[UploadFile] = File(None), foto_chassi: Optional[UploadFile] = File(None),
):
    cliente_id = f"{nome}_{uuid.uuid4().hex[:6]}".replace(" ", "_")
    pasta = os.path.join(UPLOAD_DIR, cliente_id)
    os.makedirs(pasta, exist_ok=True)

    fotos_map = {
        "frente": salvar_imagem(foto_frente, f"{pasta}/frente.jpg"),
        "traseira": salvar_imagem(foto_traseira, f"{pasta}/traseira.jpg"),
        "lat1": salvar_imagem(foto_lateral_direita, f"{pasta}/lat1.jpg"),
        "lat2": salvar_imagem(foto_lateral_esquerda, f"{pasta}/lat2.jpg"),
        "interior": salvar_imagem(foto_interior, f"{pasta}/interior.jpg"),
        "motor": salvar_imagem(foto_motor, f"{pasta}/motor.jpg"),
        "painel": salvar_imagem(foto_painel, f"{pasta}/painel.jpg"),
        "chassi": salvar_imagem(foto_chassi, f"{pasta}/chassi.jpg"),
    }

    relatorio = gerar_relatorio(fotos_map)
    
    dados = {
        "nome": nome, "veiculo": {"marca": marca, "modelo": modelo, "ano": ano},
        "data": datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M"),
        "relatorio_ai": relatorio
    }

    with open(f"{pasta}/dados.json", "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)

    return {"ok": True, "id": cliente_id}

@app.get("/avaliacoes", response_class=HTMLResponse)
def avaliacoes():
    clientes = []
    if os.path.exists(UPLOAD_DIR):
        for pasta in os.listdir(UPLOAD_DIR):
            path = os.path.join(UPLOAD_DIR, pasta, "dados.json")
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    clientes.append((pasta, json.load(f)))
    
    clientes.reverse()

    html = """<html><head><meta charset="UTF-8"><style>
        body { font-family: 'Montserrat', sans-serif; background: #f2f2f2; padding: 20px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 16px; }
        .card { background: #fff; border-radius: 12px; padding: 16px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); border-top: 4px solid #052e22; }
        .btn { display: inline-block; margin-top: 10px; padding: 10px; background: #052e22; color: #fff; border-radius: 6px; text-decoration: none; font-weight: bold; }
    </style></head><body><h1>🚗 Dashboard de Avaliações</h1><div class="grid">"""

    for id_, d in clientes:
        v = d.get("veiculo", {})
        html += f"""<div class="card"><b>{d.get('nome')}</b><br>
        🚗 {v.get('marca')} {v.get('modelo')} ({v.get('ano')})<br>📅 {d.get('data')}<br>
        <a class="btn" href="/cliente/{id_}">Abrir Laudo Técnico</a></div>"""
    
    html += "</div></body></html>"
    return HTMLResponse(html)

@app.get("/cliente/{id}", response_class=HTMLResponse)
def cliente(id: str):
    path = os.path.join(UPLOAD_DIR, id, "dados.json")
    if not os.path.exists(path): return HTMLResponse("Erro: Laudo não encontrado.")

    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)

    texto = d.get("relatorio_ai", "")

    # 🛠️ FUNÇÃO DE EXTRAÇÃO CORRIGIDA (EVITA REPETIÇÃO)
    def extrair_secao(secao_alvo, prox_secao, original):
        try:
            # Regex que para no próximo marcador romano ou na linha de separação
            padrao = rf"{secao_alvo}.*?\n(.*?)(?=\n───|\n[IVX]+\.|\nRESULTADO FINAL|\nASSINATURA|$)"
            match = re.search(padrao, original, re.DOTALL | re.IGNORECASE)
            if match:
                conteudo = match.group(1).strip()
                # Remove a linha de Subtotal de dentro do card
                conteudo = re.sub(r"Subtotal:.*", "", conteudo, flags=re.IGNORECASE)
                return conteudo
            return "Dados não localizados."
        except: return "Erro ao processar seção."

    sec_ident = extrair_secao("IDENTIFICAÇÃO DO VEÍCULO", "I.", texto)
    sec_ext = extrair_secao("I. 🚗 EXTERIOR", "II.", texto)
    sec_int = extrair_secao("II. 🪑 INTERIOR", "III.", texto)
    sec_mec = extrair_secao("III. 🧰 MECÂNICA", "IV.", texto)
    sec_cons = extrair_secao("IV. 🧼 CONSERVAÇÃO", "RESULTADO FINAL", texto)
    sec_recom = extrair_secao("🧠 RECOMENDAÇÕES", "ASSINATURA", texto)

    # Capturas de Score, Veredito e Mercado
    score = (re.findall(r"TOTAL:\s*(\d+)", texto) or ["00"])[-1]
    veredito = "APROVADO" if "APROVADO" in texto.upper() else "EM ANÁLISE"
    
    def get_val(regex, txt):
        m = re.search(regex, txt, re.IGNORECASE)
        return m.group(1).strip() if m else "Consulte"

    v_rapida = get_val(r"Venda rápida:?\s*(.*)", texto)
    v_part = get_val(r"Mercado particular:?\s*(.*)", texto)
    v_pos = get_val(r"Pós placa preta:?\s*(.*)", texto)

    fotos_dir = os.path.join(UPLOAD_DIR, id)
    arquivos = sorted([f for f in os.listdir(fotos_dir) if f.endswith(".jpg")])
    foto_capa = f"/uploads/{id}/frente.jpg" if "frente.jpg" in arquivos else f"/uploads/{id}/{arquivos}" if arquivos else ""
    fotos_html = "".join([f'<div class="img-mini" style="background-image:url(\'/uploads/{id}/{f}\')"></div>' for f in arquivos])

    return f"""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <title>Laudo Premium - {id}</title>
        <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@700&family=Montserrat:wght@300;400;700&display=swap" rel="stylesheet">
        <style>
            :root {{ --dark: #052e22; --gold: #b59a5d; --bg: #e6e2d8; --white: #ffffff; }}
            body {{ font-family: 'Montserrat', sans-serif; background: var(--bg); margin: 0; padding: 20px; }}
            .container {{ width: 1000px; margin: auto; display: grid; grid-template-columns: 1.8fr 1fr; gap: 20px; }}
            .header {{ grid-column: 1/-1; background: var(--dark); color: white; padding: 25px; border-radius: 8px; border-bottom: 5px solid var(--gold); display: flex; justify-content: space-between; }}
            .header h1 {{ font-family: 'Cinzel', serif; margin: 0; font-size: 28px; }}
            .card {{ background: var(--white); border-radius: 8px; margin-bottom: 15px; border: 1px solid #ddd; overflow: hidden; }}
            .card-header {{ background: var(--dark); color: white; padding: 10px 15px; font-weight: bold; font-size: 12px; }}
            .card-body {{ padding: 15px; font-size: 13px; line-height: 1.6; white-space: pre-wrap; }}
            .score-box {{ background: var(--white); border: 3px solid var(--gold); border-radius: 8px; padding: 20px; text-align: center; }}
            .score-num {{ font-size: 55px; font-weight: 800; color: var(--dark); }}
            .veredito {{ background: var(--dark); color: white; padding: 10px; border-radius: 4px; font-weight: bold; margin-top: 10px; }}
            .mercado-item {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px dashed #ccc; }}
            .img-mini {{ height: 90px; background-size: cover; background-position: center; border: 1px solid #ddd; border-radius: 4px; }}
            .photo-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 5px; }}
            .main-img {{ height: 250px; background: url('{foto_capa}') center/cover; border-radius: 8px; margin-bottom: 20px; border: 2px solid var(--white); }}
        </style>
    </head>
    <body>
        <div class="container">
            <header class="header">
                <div><h1>LAUDO TÉCNICO PERICIAL</h1><span>SISTEMA DE AVALIAÇÃO DE ORIGINALIDADE</span></div>
                <div style="text-align: right;">ID: {id}<br>EMISSÃO: {d['data']}</div>
            </header>
            <div class="left-col">
                <div class="card"><div class="card-header">● DADOS DO PROPRIETÁRIO</div><div class="card-body"><b>NOME:</b> {d['nome']}<br>{sec_ident}</div></div>
                <div class="card"><div class="card-header">I. EXTERIOR E CARROCERIA</div><div class="card-body">{sec_ext}</div></div>
                <div class="card"><div class="card-header">II. INTERIOR E TAPEÇARIA</div><div class="card-body">{sec_int}</div></div>
                <div class="card"><div class="card-header">III. MECÂNICA VISUAL</div><div class="card-body">{sec_mec}</div></div>
                <div class="card"><div class="card-header">IV. CONSERVAÇÃO GERAL</div><div class="card-body">{sec_cons}</div></div>
                <div class="card" style="border-left: 5px solid var(--gold);"><div class="card-header">🧠 RECOMENDAÇÕES TÉCNICAS</div><div class="card-body">{sec_recom}</div></div>
            </div>
            <div class="right-col">
                <div class="main-img"></div>
                <div class="score-box">
                    <div style="font-family: Cinzel;">PONTUAÇÃO FINAL</div>
                    <div class="score-num">{score}</div>
                    <div class="veredito">{veredito} PARA PLACA PRETA</div>
                </div>
                <div class="card" style="margin-top:20px;">
                    <div class="card-header">💰 ANÁLISE DE MERCADO (R$)</div>
                    <div class="card-body">
                        <div class="mercado-item"><span>Venda Rápida:</span> <b>{v_rapida}</b></div>
                        <div class="mercado-item"><span>Particular:</span> <b>{v_part}</b></div>
                        <div class="mercado-item"><span>Pós Placa:</span> <b>{v_pos}</b></div>
                    </div>
                </div>
                <div class="card"><div class="card-header">📷 REGISTRO FOTOGRÁFICO</div><div class="card-body"><div class="photo-grid">{fotos_html}</div></div></div>
            </div>
        </div>
    </body>
    </html>
    """