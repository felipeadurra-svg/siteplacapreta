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
- Carros só podem conseguir placa preta com 30 anos de fabricação ou mais
- Carros rebaixados , motor nao original , automaticamente reprovados
- Use exatamente os tópicos solicitados abaixo.
- Em cada tópico, descreva o que vê tecnicamente.
- Linguagem técnica estilo clube de antigomobilismo
⚖️ CRITÉRIOS DE PONTUAÇÃO (RIGOR MODERADO):
- Redução de 1 ponto: Para itens desgastados, substituições por peças de época não originais ou detalhes estéticos menores. (Padrão para a maioria dos desvios).
- Redução de 2 ou mais pontos: APENAS para faltas graves de originalidade, modificações irreversíveis ou itens que descaracterizam o modelo (ex: motor de outra marca, teto solar adaptado, cor não existente no catálogo do ano).
Formato obrigatório para descontos (NÃO USE EMOJIS OU SÍMBOLOS ESPECIAIS):
“Redução de X ponto(s) devido a [descrição objetiva]”
- Base exclusivamente em evidência visual
- Todo desconto deve vir acompanhado de justificativa técnica objetiva
- Se houver desconto de pontos, adicione uma linha "OBS: [justificativa]".
-Só desconte pontos 1 vez pelo mesmo motivo, mesmo que apareça em mais de um item (ex: motor não original pode aparecer em mecânica e conservação, mas só deve ser descontado uma vez).
- Mantenha o Subtotal no formato "Subtotal: XX/XX".

FORMATO DE RESPOSTA OBRIGATÓRIO:

📌 IDENTIFICAÇÃO DO VEÍCULO
- Marca
- Modelo
- Ano estimado
- Geração
- Confiança da análise (baixa / média / alta)


1- EXTERIOR
-Alinhamento de porta: [comentário]
-Pintura: [comentário]
-Cromados e lanternas: [comentário]
-Rodas e pneus: [comentário]
-Sinais de restauração: [comentário]
Subtotal: XX/30
OBS: [Se houver desconto, descreva aqui, senão ignore]

2- INTERIOR
-Painel: [comentário]
-Volante: [comentário]
-Bancos e tecidos: [comentário]
-Forração: [comentário]
-Conservação geral: [comentário]
Subtotal: XX/30
OBS: [Se houver desconto, descreva aqui, senão ignore]

3- MECÂNICA
-Organização do cofre: [comentário]
-Fiação aparente: [comentário]
-Componentes originais visíveis: [comentário]
-Suspensão e rodas: [comentário]
Subtotal: XX/30
OBS: [Se houver desconto, descreva aqui, senão ignore]

4- CONSERVAÇÃO
-Estrutura aparente: [comentário]
-Borrachas: [comentário]
-Desgaste natural: [comentário]
Subtotal: XX/10
OBS: [Se houver desconto, descreva aqui, senão ignore]

📊 RESULTADO FINAL
TOTAL: XX / 100
🏁 VEREDITO: [APROVADO ou REPROVADO] para placa preta

💰 ANÁLISE DE MERCADO (BRASIL – VALORES REAIS EM R$)
💸 Venda rápida: R$ XXXXX a R$ XXXXX
💰 Mercado particular: R$ XXXXX a R$ XXXXX
🏆 Pós placa preta: R$ XXXXX a R$ XXXXX
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
        return "Informação técnica indisponível no momento."

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
    
    # Lógica de Fotos com Caminho Absoluto
    fotos_dir = os.path.join(UPLOAD_DIR, id_laudo)
    fotos_urls = []
    foto_capa = "https://via.placeholder.com/1200x600?text=Foto+Principal"
    
    if os.path.exists(fotos_dir):
        arquivos = sorted([f for f in os.listdir(fotos_dir) if f.lower().endswith(".jpg")])
        fotos_urls = [f"/uploads/{id_laudo}/{f}" for f in arquivos]
        if "frente.jpg" in arquivos:
            foto_capa = f"/uploads/{id_laudo}/frente.jpg"
        elif fotos_urls:
            foto_capa = fotos_urls

    fotos_html = "".join([f'<div class="mini-foto"><img src="{url}"></div>' for url in fotos_urls])

    return f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@700&family=Montserrat:wght@300;400;700&display=swap');
        :root {{
            --verde-primario: #062b21; --verde-detalhe: #1f6b4a;
            --dourado: #c8a96a; --bege-fundo: #e3e8e1;
        }}
        body, html {{ margin: 0; padding: 0; width: 100%; height: 100%; background: #1a1a1a; }}
        .laudo-container {{
            width: 100%; min-height: 100vh; background-color: var(--bege-fundo);
            box-sizing: border-box; padding: 40px; font-family: 'Montserrat', sans-serif;
        }}
        .header-full {{
            background: linear-gradient(135deg, var(--verde-primario), var(--verde-detalhe));
            color: white; padding: 40px; border-radius: 15px; text-align: center;
            border-bottom: 6px solid var(--dourado); margin-bottom: 40px;
        }}
        .header-full h1 {{ font-family: 'Cinzel', serif; font-size: 56px; margin: 0; letter-spacing: 4px; }}
        .header-full p {{ font-size: 20px; letter-spacing: 8px; text-transform: uppercase; margin-top: 10px; opacity: 0.9; }}
        .layout-grid {{ display: grid; grid-template-columns: 1fr 1.5fr; gap: 40px; margin-bottom: 40px; }}
        .card-dados {{ background: #f1f4ef; padding: 30px; border-radius: 15px; border: 1px solid #c0c5bd; display: flex; flex-direction: column; justify-content: center; }}
        .info-item {{ border-bottom: 1px solid #d0d5cd; padding: 15px 0; }}
        .info-item:last-child {{ border: none; }}
        .info-item label {{ display: block; font-size: 13px; font-weight: 800; color: var(--verde-primario); text-transform: uppercase; }}
        .info-item span {{ font-size: 22px; font-weight: 600; color: #333; }}
        .foto-destaque {{ border: 10px solid #fff; border-radius: 20px; height: 450px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }}
        .foto-destaque img {{ width: 100%; height: 100%; object-fit: cover; }}
        .corpo-relatorio {{ display: grid; grid-template-columns: 2fr 1fr; gap: 40px; }}
        .secao-box {{ background: #f1f4ef; border-radius: 15px; margin-bottom: 25px; border: 1px solid #c0c5bd; overflow: hidden; }}
        .secao-titulo {{ background: var(--verde-primario); color: white; padding: 15px 25px; font-size: 18px; font-weight: bold; }}
        .secao-texto {{ padding: 25px; font-size: 16px; line-height: 1.8; color: #444; white-space: pre-wrap; }}
        .subtotal-tag {{ background: var(--verde-detalhe); color: white; padding: 12px 30px; text-align: right; font-weight: bold; font-size: 22px; }}
        .sidebar-full {{ display: flex; flex-direction: column; gap: 30px; }}
        .placar-final {{ background: #f1f4ef; padding: 40px; border-radius: 15px; text-align: center; border: 2px solid var(--verde-primario); }}
        .score-num {{ font-size: 90px; font-weight: 900; color: var(--verde-primario); line-height: 1; margin: 15px 0; }}
        .veredito-box {{ background: var(--verde-primario); color: white; padding: 15px; border-radius: 10px; font-size: 24px; font-weight: bold; text-transform: uppercase; }}
        .galeria-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; }}
        .mini-foto {{ aspect-ratio: 1; border: 3px solid #fff; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }}
        .mini-foto img {{ width: 100%; height: 100%; object-fit: cover; }}
        .footer-full {{ margin-top: 60px; padding-top: 30px; border-top: 2px solid #c0c5bd; display: flex; justify-content: space-between; align-items: flex-end; }}
        .assinatura {{ text-align: center; width: 400px; }}
        .linha-assinatura {{ border-top: 2px solid #333; margin-bottom: 10px; }}
    </style>
    <div class="laudo-container">
        <div class="header-full">
            <h1>LAUDO DE ORIGINALIDADE</h1>
            <p>Perícia Técnica Especializada</p>
        </div>
        <div class="layout-grid">
            <div class="card-dados">
                <div class="info-item"><label>Proprietário</label><span>{dados_json['nome']}</span></div>
                <div class="info-item"><label>Veículo</label><span>{dados_json['veiculo']['marca']} {dados_json['veiculo']['modelo']}</span></div>
                <div class="info-item"><label>Ano / Versão</label><span>{dados_json['veiculo']['ano']}</span></div>
                <div class="info-item"><label>Data da Análise</label><span>{dados_json['data']}</span></div>
            </div>
            <div class="foto-destaque"><img src="{foto_capa}"></div>
        </div>
        <div class="corpo-relatorio">
            <div class="main-content">
                <div class="secao-box">
                    <div class="secao-titulo">I. ANÁLISE EXTERIOR</div>
                    <div class="secao-texto">{corpo_ext}</div>
                    <div class="subtotal-tag">PONTOS: {sub_ext}</div>
                </div>
                <div class="secao-box">
                    <div class="secao-titulo">II. ANÁLISE INTERIOR</div>
                    <div class="secao-texto">{corpo_int}</div>
                    <div class="subtotal-tag">PONTOS: {sub_int}</div>
                </div>
                <div class="secao-box">
                    <div class="secao-titulo">III. COFRE E MECÂNICA</div>
                    <div class="secao-texto">{corpo_mec}</div>
                    <div class="subtotal-tag">PONTOS: {sub_mec}</div>
                </div>
            </div>
            <div class="sidebar-full">
                <div class="placar-final">
                    <label>PONTUAÇÃO TOTAL</label>
                    <div class="score-num">{score}</div>
                    <div class="veredito-box">{veredito}</div>
                </div>
                <div class="galeria-grid">{fotos_html}</div>
            </div>
        </div>
        <div class="footer-full">
            <div class="assinatura">
                <div class="linha-assinatura"></div>
                <strong>RESPONSÁVEL TÉCNICO</strong><br>
                <span>meucarroantigo.com</span>
            </div>
            <div style="text-align: right; opacity: 0.6;">ID: {id_laudo}</div>
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
    return HTMLResponse(renderizar_laudo_html(id, d))