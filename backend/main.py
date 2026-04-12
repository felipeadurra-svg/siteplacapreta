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
- Carros só podem conseguir placa preta com 30 anos de fabricação ou mais.
- Carros rebaixados ou com motor não original devem ser AUTOMATICAMENTE REPROVADOS.
- Use exatamente os tópicos solicitados abaixo.
- Linguagem técnica estilo clube de antigomobilismo.

⚖️ CRITÉRIOS DE PONTUAÇÃO (RIGOR MATEMÁTICO ABSOLUTO):
- Exterior: Inicia com 30 pontos.
- Interior: Inicia com 30 pontos.
- Mecânica: Inicia com 30 pontos.
- Conservação: Inicia com 10 pontos. 
- REGRA DO 10/10: Se NÃO houver defeitos na seção de CONSERVAÇÃO (borrachas, estrutura, desgaste), a nota DEVE ser 10/10, mesmo que o carro tenha sido reprovado em outras seções.
- REGRA DO ESTADO IMPECÁVEL: Se não houver reduções, a nota deve ser a máxima da seção.
- Redução de 1 ponto: Itens desgastados ou peças de época não originais.
- Redução de 2 ou mais pontos: Faltas graves (ex: motor de outra marca, rebaixamento).
- O cálculo do Subtotal deve ser exato (Total da seção - reduções).

FORMATO DE RESPOSTA OBRIGATÓRIO:

📌 IDENTIFICAÇÃO DO VEÍCULO
- Marca: 
- Modelo: 
- Ano estimado: 
- Geração: 
- Confiança da análise: 

1- EXTERIOR
[itens aqui]
Subtotal: XX/30
OBS: [descrição do desconto ou "Nenhuma"]

2- INTERIOR
[itens aqui]
Subtotal: XX/30
OBS: [descrição do desconto ou "Nenhuma"]

3- MECÂNICA
[itens aqui]
Subtotal: XX/30
OBS: [descrição do desconto ou "Nenhuma"]

4- CONSERVAÇÃO
[itens aqui]
Subtotal: XX/10
OBS: [descrição do desconto ou "Nenhuma"]

TOTAL: XX / 100
VEREDITO: [APROVADO ou REPROVADO] para placa preta

💰 ANÁLISE DE MERCADO (BRASIL)
💸 Venda rápida: R$ XXXXX a R$ XXXXX
💰 Mercado particular: R$ XXXXX a R$ XXXXX
🏆 Pós placa preta: R$ XXXXX a R$ XXXXX
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

    # NOVA LÓGICA DE EXTRAÇÃO POR DIVISÃO DE BLOCOS (MUITO MAIS ROBUSTA)
    def organizar_bloco(conteudo_bloco):
        # Captura a última nota no formato XX/XX
        notas = re.findall(r"(\d+\s*/\s*\d+)", conteudo_bloco)
        sub_val = notas[-1].replace(" ", "") if notas else "0/0"
        
        # Captura a OBS
        obs_match = re.search(r"OBS:\s*(.*?)(?=\nSubtotal:|\nSub:|$)", conteudo_bloco, re.DOTALL | re.IGNORECASE)
        obs_val = obs_match.group(1).strip() if obs_match and obs_match.group(1).strip() else "Sem observações específicas."
        
        # Limpa o texto descritivo
        limpo = re.sub(r"(?:OBS:|Subtotal:|Sub:|TOTAL:).*", "", conteudo_bloco, flags=re.DOTALL | re.IGNORECASE)
        limpo = re.sub(r"\d+\s*/\s*\d+", "", limpo).strip()
        return limpo, sub_val, obs_val

    # Divide o texto usando os títulos numerados como marcadores
    partes = re.split(r"(\d-\s*(?:EXTERIOR|INTERIOR|MECÂNICA|CONSERVAÇÃO))", texto, flags=re.IGNORECASE)
    
    secoes = {}
    for i in range(1, len(partes), 2):
        titulo = partes[i].upper()
        conteudo = partes[i+1] if (i+1) < len(partes) else ""
        if "EXTERIOR" in titulo: secoes['ext'] = organizar_bloco(conteudo)
        elif "INTERIOR" in titulo: secoes['int'] = organizar_bloco(conteudo)
        elif "MECÂNICA" in titulo: secoes['mec'] = organizar_bloco(conteudo)
        elif "CONSERVAÇÃO" in titulo: secoes['cons'] = organizar_bloco(conteudo)

    sec_ext, sub_ext, obs_ext = secoes.get('ext', ("Dados não localizados", "0/30", "N/A"))
    sec_int, sub_int, obs_int = secoes.get('int', ("Dados não localizados", "0/30", "N/A"))
    sec_mec, sub_mec, obs_mec = secoes.get('mec', ("Dados não localizados", "0/30", "N/A"))
    sec_cons, sub_cons, obs_cons = secoes.get('cons', ("Dados não localizados", "0/10", "N/A"))
    
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
    foto_capa = f"/uploads/{id}/frente.jpg" if "frente.jpg" in arquivos else (f"/uploads/{id}/{arquivos}" if arquivos else "https://via.placeholder.com/800x400")
    fotos_grid_html = "".join([f'<div class="mini-foto" style="background-image:url(\'/uploads/{id}/{f}\');"></div>' for f in arquivos])

    return f"""
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>Laudo Técnico Pericial - {id}</title>
    <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&family=Montserrat:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{ --verde-escuro: #062b21; --verde-medio: #0b3b2e; --verde-claro: #1f6b4a; --bege-fundo: #e3e8e1; --bege-card: #f1f4ef; --dourado: #c8a96a; }}
        body {{ background-color: #222; font-family: 'Montserrat', sans-serif; margin: 0; padding: 20px; display: flex; justify-content: center; }}
        .laudo-folha {{ width: 1000px; background-color: var(--bege-fundo); padding: 30px; border-radius: 5px; box-shadow: 0 0 30px rgba(0,0,0,0.5); }}
        .header {{ background: linear-gradient(135deg, var(--verde-escuro), var(--verde-claro)); color: white; padding: 20px; border-radius: 10px; text-align: center; border-bottom: 4px solid var(--dourado); margin-bottom: 20px; }}
        .header h1 {{ font-family: 'Cinzel', serif; margin: 0; font-size: 42px; letter-spacing: 2px; }}
        .topo-container {{ display: grid; grid-template-columns: 400px 1fr; gap: 20px; margin-bottom: 20px; }}
        .dados-proprietario {{ background: var(--bege-card); border: 1px solid #c0c5bd; border-radius: 12px; padding: 15px; }}
        .info-row {{ display: flex; align-items: center; gap: 15px; padding: 10px 0; border-bottom: 1px solid #d0d5cd; }}
        .info-text label {{ display: block; font-size: 11px; font-weight: 800; color: var(--verde-escuro); }}
        .foto-principal {{ border: 5px solid #fff; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.2); overflow: hidden; height: 250px; }}
        .foto-principal img {{ width: 100%; height: 100%; object-fit: cover; }}
        .barra-titulo {{ background: var(--verde-escuro); color: white; padding: 10px 20px; border-radius: 8px; margin-bottom: 15px; }}
        .conteudo-grid {{ display: grid; grid-template-columns: 1fr 350px; gap: 20px; }}
        .card-avaliacao {{ background: var(--bege-card); border: 1px solid #c0c5bd; border-radius: 10px; margin-bottom: 15px; overflow: hidden; }}
        .card-header {{ background: linear-gradient(90deg, var(--verde-escuro), var(--verde-claro)); color: white; padding: 8px 15px; font-weight: 600; display: flex; justify-content: space-between; }}
        .card-body {{ display: grid; grid-template-columns: 1fr 180px; padding: 12px; gap: 15px; }}
        .itens-lista {{ font-size: 11px; line-height: 1.5; color: #444; white-space: pre-wrap; }}
        .obs-tecnica {{ font-size: 10px; background: #fff; padding: 8px; border-radius: 5px; border-left: 3px solid var(--verde-claro); }}
        .subtotal-box {{ grid-column: span 2; background: var(--verde-escuro); color: white; text-align: right; padding: 5px 15px; font-weight: bold; font-size: 18px; border-radius: 5px; }}
        .sidebar-card {{ background: var(--bege-card); border: 1px solid #c0c5bd; border-radius: 10px; margin-bottom: 15px; padding: 15px; }}
        .score-grande {{ font-size: 48px; font-weight: 800; color: var(--verde-escuro); text-align: center; }}
        .veredito-tag {{ background: var(--verde-escuro); color: white; padding: 10px; border-radius: 8px; font-weight: 700; text-align: center; margin-top: 10px; }}
        .foto-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 5px; }}
        .mini-foto {{ aspect-ratio: 1; background-color: #ddd; border-radius: 4px; background-position: center; background-size: cover; }}
    </style>
</head>
<body>
<div class="laudo-folha">
    <div class="header">
        <h1>LAUDO TÉCNICO PERICIAL</h1>
        <p>ORIGINALIDADE E ANTIGOMOBILISMO</p>
    </div>
    <div class="topo-container">
        <div class="dados-proprietario">
            <div class="info-row"><div class="info-text"><label>Proprietário:</label><span>{d['nome']}</span></div></div>
            <div class="info-row"><div class="info-text"><label>Veículo:</label><span>{d['veiculo']['marca']} {d['veiculo']['modelo']} - {d['veiculo']['ano']}</span></div></div>
            <div class="info-row"><div class="info-text"><label>Data:</label><span>{d['data']}</span></div></div>
        </div>
        <div class="foto-principal"><img src="{foto_capa}"></div>
    </div>
    <div class="barra-titulo"><strong>RELATÓRIO DE VISTORIA TÉCNICA</strong></div>
    <div class="conteudo-grid">
        <div class="col-esquerda">
            <div class="card-avaliacao">
                <div class="card-header">I. EXTERIOR E CARROCERIA (0-30 pts)</div>
                <div class="card-body">
                    <div class="itens-lista">{sec_ext}</div>
                    <div class="obs-tecnica"><strong>Observações:</strong><br>{obs_ext}</div>
                    <div class="subtotal-box">Subtotal: {sub_ext}</div>
                </div>
            </div>
            <div class="card-avaliacao">
                <div class="card-header">II. INTERIOR E TAPEÇARIA (0-30 pts)</div>
                <div class="card-body">
                    <div class="itens-lista">{sec_int}</div>
                    <div class="obs-tecnica"><strong>Observações:</strong><br>{obs_int}</div>
                    <div class="subtotal-box">Subtotal: {sub_int}</div>
                </div>
            </div>
            <div class="card-avaliacao">
                <div class="card-header">III. MECÂNICA / COFRE (0-30 pts)</div>
                <div class="card-body">
                    <div class="itens-lista">{sec_mec}</div>
                    <div class="obs-tecnica"><strong>Observações:</strong><br>{obs_mec}</div>
                    <div class="subtotal-box">Subtotal: {sub_mec}</div>
                </div>
            </div>
            <div class="card-avaliacao">
                <div class="card-header">IV. CONSERVAÇÃO GERAL (0-10 pts)</div>
                <div class="card-body">
                    <div class="itens-lista">{sec_cons}</div>
                    <div class="obs-tecnica"><strong>Observações:</strong><br>{obs_cons}</div>
                    <div class="subtotal-box">Subtotal: {sub_cons}</div>
                </div>
            </div>
        </div>
        <div class="col-direita">
            <div class="sidebar-card">
                <div class="score-grande">{score}/100</div>
                <div class="veredito-tag">{veredito}</div>
            </div>
            <div class="sidebar-card">
                <strong>VALORES DE MERCADO</strong>
                <p style="font-size:12px">Venda rápida: {v_rapida}<br>Particular: {v_part}<br>Placa Preta: {v_pos}</p>
            </div>
            <div class="sidebar-card">
                <div class="foto-grid">{fotos_grid_html}</div>
            </div>
        </div>
    </div>
</div>
</body>
</html>
"""