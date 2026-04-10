from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
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
    
    # Extração via Regex
    def extrair_pontos(secao, texto):
        padrao = rf"{secao}.*?Subtotal:\s*(\d+/\d+)"
        match = re.search(padrao, texto, re.S | re.IGNORECASE)
        return match.group(1) if match else "0/30"

    def extrair_corpo(secao_atual, proxima_secao, texto):
        padrao = rf"{secao_atual}(.*?)(?={proxima_secao}|$)"
        match = re.search(padrao, texto, re.S | re.IGNORECASE)
        if match:
            content = match.group(1).strip()
            content = re.sub(r"Subtotal:.*", "", content, flags=re.IGNORECASE)
            return content
        return "Análise técnica não disponível."

    sub_ext = extrair_pontos("1- EXTERIOR", analise_ia)
    sub_int = extrair_pontos("2- INTERIOR", analise_ia)
    sub_mec = extrair_pontos("3- MECÂNICA", analise_ia)
    
    corpo_ext = extrair_corpo("1- EXTERIOR", "2- INTERIOR", analise_ia)
    corpo_int = extrair_corpo("2- INTERIOR", "3- MECÂNICA", analise_ia)
    corpo_mec = extrair_corpo("3- MECÂNICA", "4- CONSERVAÇÃO", analise_ia)

    score = (re.findall(r"TOTAL:\s*(\d+)", analise_ia) or ["0"])[-1]
    veredito = "APROVADO" if "APROVADO" in analise_ia.upper() else "REPROVADO"
    
    # Busca de fotos no diretório - Lógica Reforçada
    fotos_dir = os.path.join(UPLOAD_DIR, id_laudo)
    fotos_urls = []
    foto_capa = "https://via.placeholder.com/1200x600?text=Foto+nao+encontrada"
    
    if os.path.exists(fotos_dir):
        arquivos = sorted([f for f in os.listdir(fotos_dir) if f.endswith(".jpg")])
        fotos_urls = [f"/uploads/{id_laudo}/{f}" for f in arquivos]
        # Prioridade para a foto frontal
        if "frente.jpg" in arquivos:
            foto_capa = f"/uploads/{id_laudo}/frente.jpg"
        elif fotos_urls:
            foto_capa = fotos_urls

    fotos_html = "".join([f'<div class="mini-foto"><img src="{url}" style="width:100%;height:100%;object-fit:cover;border-radius:4px;"></div>' for url in fotos_urls[:15]])

    return f"""
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>Laudo Técnico Pericial - {id_laudo}</title>
    <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&family=Montserrat:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --verde-escuro: #062b21; --verde-medio: #0b3b2e; --verde-claro: #1f6b4a;
            --bege-fundo: #e3e8e1; --bege-card: #f1f4ef; --dourado: #c8a96a;
        }}
        * {{ box-sizing: border-box; }}
        body {{ 
            background-color: #1a1a1a; 
            font-family: 'Montserrat', sans-serif; 
            margin: 0; 
            padding: 20px; 
            display: flex; 
            justify-content: center; 
        }}
        /* LARGURA AMPLIADA E RESPONSIVA */
        .laudo-folha {{ 
            width: 95%; 
            max-width: 1200px; 
            background-color: var(--bege-fundo); 
            padding: 40px; 
            border-radius: 8px; 
            box-shadow: 0 10px 50px rgba(0,0,0,0.6); 
        }}
        .header {{ 
            background: linear-gradient(135deg, var(--verde-escuro), var(--verde-claro)); 
            color: white; 
            padding: 30px; 
            border-radius: 12px; 
            text-align: center; 
            border-bottom: 5px solid var(--dourado); 
            margin-bottom: 30px; 
        }}
        .header h1 {{ font-family: 'Cinzel', serif; margin: 0; font-size: 48px; letter-spacing: 3px; }}
        .header p {{ margin: 10px 0 0; font-size: 18px; letter-spacing: 5px; font-weight: 300; }}
        
        .topo-container {{ 
            display: grid; 
            grid-template-columns: 1fr 1.5fr; 
            gap: 30px; 
            margin-bottom: 30px; 
        }}
        .dados-proprietario {{ background: var(--bege-card); border: 1px solid #c0c5bd; border-radius: 15px; padding: 25px; }}
        .info-row {{ display: flex; align-items: center; gap: 15px; padding: 12px 0; border-bottom: 1px solid #d0d5cd; }}
        .info-row:last-child {{ border: none; }}
        .info-text label {{ display: block; font-size: 12px; font-weight: 800; color: var(--verde-escuro); text-transform: uppercase; }}
        .info-text span {{ font-size: 18px; font-weight: 600; color: #333; }}
        
        .foto-principal {{ 
            border: 8px solid #fff; 
            border-radius: 20px; 
            box-shadow: 0 8px 25px rgba(0,0,0,0.3); 
            overflow: hidden; 
            height: 400px; 
        }}
        .foto-principal img {{ width: 100%; height: 100%; object-fit: cover; }}
        
        .barra-titulo {{ background: var(--verde-escuro); color: white; padding: 15px 25px; border-radius: 10px; margin-bottom: 25px; }}
        
        .conteudo-grid {{ display: grid; grid-template-columns: 1.6fr 1fr; gap: 30px; }}
        
        .card-avaliacao {{ background: var(--bege-card); border: 1px solid #c0c5bd; border-radius: 12px; margin-bottom: 20px; overflow: hidden; }}
        .card-header {{ background: linear-gradient(90deg, var(--verde-escuro), var(--verde-claro)); color: white; padding: 12px 20px; font-size: 16px; font-weight: 600; }}
        .card-body {{ padding: 20px; }}
        .itens-lista {{ font-size: 14px; line-height: 1.6; color: #444; white-space: pre-wrap; margin-bottom: 15px; }}
        .subtotal-box {{ background: var(--verde-escuro); color: white; text-align: right; padding: 10px 20px; font-weight: bold; font-size: 20px; border-radius: 6px; }}
        
        .sidebar-card {{ background: var(--bege-card); border: 1px solid #c0c5bd; border-radius: 12px; margin-bottom: 20px; padding: 25px; }}
        .sidebar-titulo {{ border-bottom: 3px solid var(--verde-claro); color: var(--verde-escuro); font-weight: 700; font-size: 14px; padding-bottom: 10px; margin-bottom: 15px; }}
        .score-grande {{ font-size: 64px; font-weight: 800; color: var(--verde-escuro); text-align: center; margin: 10px 0; }}
        .veredito-tag {{ background: var(--verde-escuro); color: white; padding: 15px; border-radius: 10px; font-weight: 700; font-size: 20px; text-align: center; }}
        
        .foto-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }}
        .mini-foto {{ aspect-ratio: 1; background: #ddd; border-radius: 8px; overflow: hidden; border: 2px solid #fff; }}
        
        .footer {{ margin-top: 40px; display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #ccc; padding-top: 30px; }}
        .assinatura-box {{ text-align: center; width: 350px; }}
        .assinatura-linha {{ border-top: 2px solid #333; margin-bottom: 8px; }}
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
            <div class="info-row"><div class="info-text"><label>Proprietário:</label><span>{dados_json['nome']}</span></div></div>
            <div class="info-row"><div class="info-text"><label>Veículo:</label><span>{dados_json['veiculo']['marca']} {dados_json['veiculo']['modelo']} ({dados_json['veiculo']['ano']})</span></div></div>
            <div class="info-row"><div class="info-text"><label>Data da Vistoria:</label><span>{dados_json['data']}</span></div></div>
            <div class="info-row"><div class="info-text"><label>Código de Autenticidade:</label><span>{id_laudo}</span></div></div>
        </div>
        <div class="foto-principal"><img src="{foto_capa}" alt="Foto Principal do Veículo"></div>
    </div>

    <div class="barra-titulo">
        <div style="font-size: 22px;">📄 <strong>RELATÓRIO TÉCNICO DE ORIGINALIDADE</strong></div>
    </div>

    <div class="conteudo-grid">
        <div class="col-esquerda">
            <div class="card-avaliacao">
                <div class="card-header">I. EXTERIOR E CARROCERIA</div>
                <div class="card-body">
                    <div class="itens-lista">{corpo_ext}</div>
                    <div class="subtotal-box">Subtotal: {sub_ext}</div>
                </div>
            </div>
            <div class="card-avaliacao">
                <div class="card-header">II. INTERIOR E TAPEÇARIA</div>
                <div class="card-body">
                    <div class="itens-lista">{corpo_int}</div>
                    <div class="subtotal-box">Subtotal: {sub_int}</div>
                </div>
            </div>
            <div class="card-avaliacao">
                <div class="card-header">III. MECÂNICA E COFRE</div>
                <div class="card-body">
                    <div class="itens-lista">{corpo_mec}</div>
                    <div class="subtotal-box">Subtotal: {sub_mec}</div>
                </div>
            </div>
        </div>

        <div class="col-direita">
            <div class="sidebar-card">
                <div class="sidebar-titulo">📊 PONTUAÇÃO FINAL</div>
                <div class="score-grande">{score} / 100</div>
                <div class="veredito-tag">{veredito}</div>
            </div>
            <div class="sidebar-card">
                <div class="sidebar-titulo">📸 EVIDÊNCIAS FOTOGRÁFICAS</div>
                <div class="foto-grid">{fotos_html}</div>
            </div>
        </div>
    </div>

    <div class="footer">
        <div class="assinatura-box">
            <div class="assinatura-linha"></div>
            <strong style="font-size: 16px;">Perito Responsável</strong><br>
            <span style="font-size: 12px; color: #666;">Sistema meucarroantigo.com</span>
        </div>
        <div style="text-align: right; color: var(--verde-escuro); font-weight: bold;">
            {datetime.now().year} © Laudo de Originalidade
        </div>
    </div>
</div>
</body>
</html>
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
    
    laudo_html = renderizar_laudo_html(cliente_id, dados)
    return {"ok": True, "id": cliente_id, "html_laudo": laudo_html}

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
    return HTMLResponse(f"<html><body style='background:#1a1a1a; padding:20px;'>{renderizar_laudo_html(id, d)}</body></html>")