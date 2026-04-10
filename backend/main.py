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
- Use exatamente os tópicos solicitados abaixo.
- Em cada tópico, descreva o que vê tecnicamente.
- Se houver desconto de pontos, adicione uma linha "OBS: [justificativa]".
- Mantenha o Subtotal no formato "Subtotal: XX/XX".

FORMATO DE RESPOSTA OBRIGATÓRIO:

📌 IDENTIFICAÇÃO DO VEÍCULO
Marca: [Texto]
Modelo: [Texto]
Ano: [Texto]

1- EXTERIOR E CARROCERIA (0-30pts)
-alinhamento de porta: [comentário]
-pintura: [comentário]
-cromados e lanternas: [comentário]
-rodas e pneus: [comentário]
-sinais de restauração: [comentário]
OBS: [Se houver desconto, descreva aqui, senão ignore]
Subtotal: XX/30

2- INTERIOR E TAPEÇARIA (0-30pts)
-painel: [comentário]
-volante: [comentário]
-bancos e tecidos: [comentário]
-forração: [comentário]
-conservação geral: [comentário]
OBS: [Se houver desconto, descreva aqui, senão ignore]
Subtotal: XX/30

3- MECÂNICA / VISUAL (0-30pts)
-organização do cofre: [comentário]
-fiação aparente: [comentário]
-componentes originais visíveis: [comentário]
-suspensão e rodas: [comentário]
OBS: [Se houver desconto, descreva aqui, senão ignore]
Subtotal: XX/30

4- CONSERVAÇÃO (0-10pts)
-estrutura aparente: [comentário]
-borrachas: [comentário]
-desgaste natural: [comentário]
OBS: [Se houver desconto, descreva aqui, senão ignore]
Subtotal: XX/10

📊 RESULTADO FINAL
TOTAL: XX / 100
🏁 VEREDITO: [APROVADO ou REPROVADO] para placa preta

💰 ANÁLISE DE MERCADO
- Venda rápida: R$ [Valor]
- Mercado particular: R$ [Valor]
- Pós placa preta: R$ [Valor]
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
        .card { background: #fff; border-radius: 12px; padding: 16px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); border-top: 4px solid #0b3b2e; }
        .btn { display: inline-block; margin-top: 10px; padding: 10px; background: #0b3b2e; color: #fff; border-radius: 6px; text-decoration: none; font-weight: bold; }
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

    def extrair_secao(prefixo, proximo, original):
        try:
            padrao = rf"{prefixo}(.*?)(?={proximo}|$)"
            match = re.search(padrao, original, re.DOTALL | re.IGNORECASE)
            if match:
                res = match.group(1).strip()
                # Extrair subtotal antes de limpar para o card
                sub = re.search(r"Subtotal:\s*(\d+/\d+)", res, re.IGNORECASE)
                sub_val = sub.group(1) if sub else "-- / --"
                # Limpar o subtotal do texto principal para não repetir
                res = re.sub(r"Subtotal:.*", "", res, flags=re.IGNORECASE).strip()
                return res, sub_val
            return "Dados não localizados.", "-- / --"
        except: return "Erro", "-- / --"

    sec_ext, sub_ext = extrair_secao("1- EXTERIOR", "2- INTERIOR", texto)
    sec_int, sub_int = extrair_secao("2- INTERIOR", "3- MECÂNICA", texto)
    sec_mec, sub_mec = extrair_secao("3- MECÂNICA", "4- CONSERVAÇÃO", texto)
    sec_cons, sub_cons = extrair_secao("4- CONSERVAÇÃO", "RESULTADO FINAL", texto)
    
    score = (re.findall(r"TOTAL:\s*(\d+)", texto) or ["00"])[-1]
    veredito = "APROVADO" if "APROVADO" in texto.upper() else "REPROVADO"
    
    def get_val(regex, txt):
        m = re.search(regex, txt, re.IGNORECASE)
        return m.group(1).strip() if m else "R$ --"

    v_rapida = get_val(r"Venda rápida:?\s*(.*)", texto)
    v_part = get_val(r"Mercado particular:?\s*(.*)", texto)
    v_pos = get_val(r"Pós placa preta:?\s*(.*)", texto)

    fotos_dir = os.path.join(UPLOAD_DIR, id)
    arquivos = sorted([f for f in os.listdir(fotos_dir) if f.endswith(".jpg")])
    fotos_html = "".join([f'<div class="photo" style="background-image:url(\'/uploads/{id}/{f}\'); background-size:cover; background-position:center;" data="{i+1}"></div>' for i, f in enumerate(arquivos)])

    return f"""
<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="UTF-8">
<title>Laudo Técnico Pericial - {id}</title>
<link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=Montserrat:wght@300;400;600&display=swap" rel="stylesheet">
<style>
:root {{ --verde1:#0b3b2e; --verde2:#1f6b4a; --dourado:#c8a96a; --fundo:#e8e4db; }}
body {{ margin:0; background:var(--fundo); font-family:'Montserrat',sans-serif; }}
.container {{ width:1180px; margin:20px auto; position:relative; }}
.header {{ background:linear-gradient(135deg,var(--verde1),var(--verde2)); color:white; border-radius:12px; padding:25px; display:flex; align-items:center; justify-content:center; flex-direction:column; box-shadow:inset 0 0 30px rgba(0,0,0,.4); }}
.header h1 {{ font-family:'Cinzel',serif; letter-spacing:3px; margin:0; }}
.header span {{ font-size:13px; opacity:.9; }}
.main {{ display:grid; grid-template-columns: 2fr 1fr; gap:15px; margin-top:15px; }}
.card {{ background:#f6f2ea; border-radius:10px; border:1px solid #d6d1c7; box-shadow:0 3px 10px rgba(0,0,0,.15); margin-bottom:15px; }}
.title {{ background:linear-gradient(90deg,var(--verde1),var(--verde2)); color:#fff; padding:8px 12px; border-radius:10px 10px 0 0; font-weight:600; font-size:13px; display:flex; align-items:center; gap:6px; }}
.content {{ padding:12px; font-size:13px; line-height:1.5; white-space: pre-wrap; }}
.info-box {{ display:grid; grid-template-columns:1fr; gap:4px; }}
.field {{ border-bottom:1px solid #bbb; padding:4px 0; }}
.subtotal {{ margin-top:8px; background:var(--verde1); color:#fff; text-align:center; padding:6px; border-radius:6px; font-weight:bold; }}
.result-box {{ text-align:center; padding:15px; }}
.score {{ font-size:35px; font-weight:bold; color: var(--verde1); }}
.veredito {{ margin-top:10px; background:linear-gradient(135deg,var(--verde1),var(--verde2)); color:white; padding:12px; border-radius:8px; font-weight:bold; }}
.market p {{ margin:6px 0; font-size:13px; border-bottom: 1px dashed #ccc; padding-bottom:4px; }}
.photos {{ display:grid; grid-template-columns:repeat(5,1fr); gap:6px; }}
.photo {{ height:70px; background:#cfcfcf; border-radius:6px; position:relative; border: 1px solid #ccc; }}
.photo::before {{ content:attr(data); position:absolute; top:2px; left:4px; font-size:9px; background:rgba(255,255,255,0.7); padding:1px 4px; border-radius:3px; }}
.footer {{ display:flex; justify-content:space-between; margin-top:30px; align-items: flex-end; }}
.assinatura {{ width:60%; }}
.linha {{ border-top:2px solid #333; width:280px; margin-bottom:10px; }}
.assinatura-nome {{ font-family:'Cinzel',serif; font-size:20px; color:var(--verde1); }}
.final {{ width:30%; background:linear-gradient(135deg,var(--verde1),var(--verde2)); color:white; border-radius:10px; padding:20px; text-align:center; font-weight:bold; font-size:18px; }}
.watermark {{ position:fixed; bottom:20px; right:20px; opacity:0.05; font-size:150px; z-index:-1; }}
.icon {{ font-size: 16px; }}
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>LAUDO TÉCNICO PERICIAL</h1>
        <span>SISTEMA PREMIUM DE AVALIAÇÃO - ORIGINALIDADE E ANTIGOMOBILISMO</span>
    </div>

    <div class="main">
        <div>
            <div class="card">
                <div class="title">DADOS DO PROPRIETÁRIO E VEÍCULO</div>
                <div class="content info-box">
                    <div class="field"><b>Proprietário:</b> {d['nome']}</div>
                    <div class="field"><b>Veículo:</b> {d['veiculo']['marca']} {d['veiculo']['modelo']} - {d['veiculo']['ano']}</div>
                    <div class="field"><b>Data do Laudo:</b> {d['data']} | <b>ID:</b> {id}</div>
                </div>
            </div>

            <div class="card">
                <div class="title">1. EXTERIOR E CARROCERIA (0-30 pts)</div>
                <div class="content">
                    {sec_ext}
                    <div class="subtotal">Subtotal: {sub_ext}</div>
                </div>
            </div>

            <div class="card">
                <div class="title">2. INTERIOR E TAPEÇARIA (0-30 pts)</div>
                <div class="content">
                    {sec_int}
                    <div class="subtotal">Subtotal: {sub_int}</div>
                </div>
            </div>

            <div class="card">
                <div class="title">3. MECÂNICA VISUAL (0-30 pts)</div>
                <div class="content">
                    {sec_mec}
                    <div class="subtotal">Subtotal: {sub_mec}</div>
                </div>
            </div>

            <div class="card">
                <div class="title">4. CONSERVAÇÃO (0-10 pts)</div>
                <div class="content">
                    {sec_cons}
                    <div class="subtotal">Subtotal: {sub_cons}</div>
                </div>
            </div>
        </div>

        <div>
            <div class="card">
                <div class="title">🏆 RESULTADO FINAL</div>
                <div class="result-box">
                    <span>Pontuação Total</span>
                    <div class="score">{score} / 100</div>
                    <div class="veredito">{veredito}</div>
                </div>
            </div>

            <div class="card">
                <div class="title">💰 ANÁLISE DE MERCADO (ESTIMADA)</div>
                <div class="content market">
                    <p><b>Venda rápida:</b> {v_rapida}</p>
                    <p><b>Particular:</b> {v_part}</p>
                    <p><b>Pós placa preta:</b> {v_pos}</p>
                </div>
            </div>

            <div class="card">
                <div class="title">📷 REGISTRO FOTOGRÁFICO</div>
                <div class="content photos">
                    {fotos_html}
                </div>
            </div>
        </div>
    </div>

    <div class="footer">
        <div class="assinatura">
            <div class="linha"></div>
            <div class="assinatura-nome">Perito Automotivo Responsável</div>
            <div style="font-size:10px; margin-top:5px;">Certificado de Originalidade e Antigomobilismo</div>
        </div>
        <div class="final">
            STATUS FINAL:<br>
            {veredito}
        </div>
    </div>

    <div class="watermark">🚗</div>
</div>
</body>
</html>
    """