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
# O StaticFiles permite que o navegador acesse a pasta /uploads
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
Você é um PERITO AUTOMOTIVO ESPECIALISTA EM ANTIGOMOBILISMO.
Regras de Negócio:
- Carros com 30 anos ou mais = Placa Preta.
- Rebaixados ou motor não original = Reprovados.
Use linguagem técnica de antigomobilismo.
Siga rigorosamente as seções 1- EXTERIOR, 2- INTERIOR, 3- MECÂNICA, 4- CONSERVAÇÃO.
Finalize com TOTAL: XX/100 e VEREDITO.
"""

def gerar_relatorio_ai(fotos):
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
        return response.choices[0].message.content
    except Exception as e:
        return f"Erro na IA: {str(e)}"

def renderizar_laudo_html(id_laudo, dados_json):
    analise_ia = dados_json.get("relatorio_ai", "")
    
    # Extração de dados via regex
    def extrair_secao(secao_inicio, proxima_secao, texto):
        padrao = rf"{secao_inicio}(.*?)(?={proxima_secao}|$)"
        match = re.search(padrao, texto, re.S | re.IGNORECASE)
        if match:
            clean = re.sub(r"Subtotal:.*", "", match.group(1), flags=re.IGNORECASE).strip()
            return clean
        return "Informação não disponível."

    def extrair_pontos(secao, texto):
        match = re.search(rf"{secao}.*?Subtotal:\s*(\d+/\d+)", texto, re.S | re.IGNORECASE)
        return match.group(1) if match else "0/30"

    sub_ext = extrair_pontos("1- EXTERIOR", analise_ia)
    sub_int = extrair_pontos("2- INTERIOR", analise_ia)
    sub_mec = extrair_pontos("3- MECÂNICA", analise_ia)
    
    corpo_ext = extrair_secao("1- EXTERIOR", "2- INTERIOR", analise_ia)
    corpo_int = extrair_secao("2- INTERIOR", "3- MECÂNICA", analise_ia)
    corpo_mec = extrair_secao("3- MECÂNICA", "4- CONSERVAÇÃO", analise_ia)

    score = (re.findall(r"TOTAL:\s*(\d+)", analise_ia) or ["0"])[-1]
    veredito = "APROVADO" if "APROVADO" in analise_ia.upper() else "REPROVADO"
    
    # 📸 LÓGICA DE FOTOS CORRIGIDA (Caminhos Absolutos)
    fotos_dir = os.path.join(UPLOAD_DIR, id_laudo)
    fotos_urls = []
    foto_capa = "https://via.placeholder.com/800x400?text=Sem+Foto"
    
    if os.path.exists(fotos_dir):
        # Lista arquivos e limpa para pegar apenas o nome
        arquivos = sorted([f for f in os.listdir(fotos_dir) if f.lower().endswith(".jpg")])
        # IMPORTANTE: O caminho deve começar com / para ser absoluto no navegador
        fotos_urls = [f"/uploads/{id_laudo}/{f}" for f in arquivos]
        
        if "frente.jpg" in arquivos:
            foto_capa = f"/uploads/{id_laudo}/frente.jpg"
        elif fotos_urls:
            foto_capa = fotos_urls

    fotos_html = "".join([f'<div class="mini-foto"><img src="{url}"></div>' for url in fotos_urls])

    return f"""
    <div class="laudo-folha">
        <style>
            .laudo-folha {{ width: 95%; max-width: 1200px; background: #e3e8e1; margin: auto; padding: 40px; border-radius: 10px; font-family: 'Montserrat', sans-serif; box-shadow: 0 10px 40px rgba(0,0,0,0.5); }}
            .header {{ background: linear-gradient(135deg, #062b21, #1f6b4a); color: white; padding: 30px; border-radius: 10px; text-align: center; border-bottom: 5px solid #c8a96a; margin-bottom: 30px; }}
            .header h1 {{ font-family: 'Cinzel', serif; font-size: 42px; margin: 0; }}
            .topo-container {{ display: grid; grid-template-columns: 1fr 1.5fr; gap: 30px; margin-bottom: 30px; }}
            .dados-box {{ background: #f1f4ef; padding: 20px; border-radius: 10px; border: 1px solid #c0c5bd; }}
            .info-item {{ border-bottom: 1px solid #ddd; padding: 10px 0; }}
            .info-item label {{ display: block; font-size: 11px; font-weight: bold; color: #062b21; }}
            .info-item span {{ font-size: 18px; color: #333; }}
            .foto-principal-frame {{ border: 8px solid #fff; border-radius: 15px; height: 350px; overflow: hidden; box-shadow: 0 5px 15px rgba(0,0,0,0.2); }}
            .foto-principal-frame img {{ width: 100%; height: 100%; object-fit: cover; }}
            .conteudo {{ display: grid; grid-template-columns: 1.6fr 1fr; gap: 30px; }}
            .secao-card {{ background: #f1f4ef; border-radius: 10px; margin-bottom: 20px; border: 1px solid #c0c5bd; overflow: hidden; }}
            .secao-header {{ background: #062b21; color: white; padding: 10px 20px; font-weight: bold; }}
            .secao-body {{ padding: 20px; font-size: 14px; line-height: 1.6; white-space: pre-wrap; }}
            .subtotal {{ background: #062b21; color: white; text-align: right; padding: 10px; font-weight: bold; font-size: 18px; }}
            .score-card {{ background: #f1f4ef; padding: 20px; border-radius: 10px; text-align: center; border: 1px solid #c0c5bd; }}
            .score-val {{ font-size: 60px; font-weight: 800; color: #062b21; }}
            .veredito {{ background: #062b21; color: white; padding: 10px; border-radius: 5px; font-size: 20px; font-weight: bold; margin-top: 10px; }}
            .grid-fotos {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-top: 20px; }}
            .mini-foto {{ aspect-ratio: 1; border: 2px solid #fff; border-radius: 5px; overflow: hidden; }}
            .mini-foto img {{ width: 100%; height: 100%; object-fit: cover; }}
        </style>

        <div class="header">
            <h1>LAUDO TÉCNICO</h1>
            <p>CERTIFICAÇÃO DE ORIGINALIDADE</p>
        </div>

        <div class="topo-container">
            <div class="dados-box">
                <div class="info-item"><label>PROPRIETÁRIO</label><span>{dados_json['nome']}</span></div>
                <div class="info-item"><label>VEÍCULO</label><span>{dados_json['veiculo']['marca']} {dados_json['veiculo']['modelo']} ({dados_json['veiculo']['ano']})</span></div>
                <div class="info-item"><label>DATA</label><span>{dados_json['data']}</span></div>
                <div class="info-item"><label>ID LAUDO</label><span>{id_laudo}</span></div>
            </div>
            <div class="foto-principal-frame">
                <img src="{foto_capa}">
            </div>
        </div>

        <div class="conteudo">
            <div class="col-main">
                <div class="secao-card">
                    <div class="secao-header">EXTERIOR</div>
                    <div class="secao-body">{corpo_ext}</div>
                    <div class="subtotal">Subtotal: {sub_ext}</div>
                </div>
                <div class="secao-card">
                    <div class="secao-header">INTERIOR</div>
                    <div class="secao-body">{corpo_int}</div>
                    <div class="subtotal">Subtotal: {sub_int}</div>
                </div>
                <div class="secao-card">
                    <div class="secao-header">MECÂNICA</div>
                    <div class="secao-body">{corpo_mec}</div>
                    <div class="subtotal">Subtotal: {sub_mec}</div>
                </div>
            </div>

            <div class="col-side">
                <div class="score-card">
                    <label style="font-weight: bold; color: #666;">PONTUAÇÃO FINAL</label>
                    <div class="score-val">{score}</div>
                    <div class="veredito">{veredito}</div>
                </div>
                <div class="grid-fotos">
                    {fotos_html}
                </div>
            </div>
        </div>
    </div>
    """

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
    
    relatorio_texto = gerar_relatorio_ai(fotos_map)
    dados = {
        "nome": nome, "veiculo": {"marca": marca, "modelo": modelo, "ano": ano},
        "data": datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M"),
        "relatorio_ai": relatorio_texto
    }
    
    with open(f"{pasta}/dados.json", "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)
    
    return {"ok": True, "id": cliente_id}

@app.get("/avaliacoes", response_class=HTMLResponse)
def avaliacoes():
    # ... (mesmo código do dashboard anterior)
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
    </style></head><body><h1>🚗 Dashboard</h1><div class="grid">"""
    for id_, d in clientes:
        v = d.get("veiculo", {})
        html += f"""<div class="card"><b>{d.get('nome')}</b><br>
        🚗 {v.get('marca')} {v.get('modelo')}<br>
        <a class="btn" href="/cliente/{id_}">Abrir Laudo</a></div>"""
    html += "</div></body></html>"
    return HTMLResponse(html)

@app.get("/cliente/{id}", response_class=HTMLResponse)
def cliente(id: str):
    path = os.path.join(UPLOAD_DIR, id, "dados.json")
    if not os.path.exists(path): return HTMLResponse("Erro: Laudo não encontrado.")
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)
    # Aqui o HTML é gerado com os caminhos de imagem corrigidos
    return HTMLResponse(f"<html><body style='background:#1a1a1a; padding:40px;'>{renderizar_laudo_html(id, d)}</body></html>")