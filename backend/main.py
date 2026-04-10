from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
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

PROTOCOLO DE AVALIAÇÃO TÉCNICA - PLACA PRETA
[CRITÉRIOS DE ELEGIBILIDADE E REPROVAÇÃO]
REQUISITO OBRIGATÓRIO: O veículo deve possuir 30 anos ou mais de fabricação.
REPROVAÇÃO AUTOMÁTICA: Veículos com suspensão rebaixada ou motorização não original.
ESTILO DE LINGUAGEM: Técnica, formal, padrão clube de antigomobilismo.
[DIRETRIZES DE PONTUAÇÃO E JUSTIFICATIVA]
RIGOR: Moderado.
REDUÇÃO DE 1 PONTO: Itens desgastados, peças de época não originais ou detalhes estéticos menores.
REDUÇÃO DE 2 OU MAIS PONTOS: Faltas graves, modificações irreversíveis, itens fora de catálogo ou descaracterização.
REGRA DE OURO: Não penalizar o mesmo erro em mais de um tópico.
FORMATO DE DESCONTO: "Redução de X ponto(s) devido a [descrição objetiva]"
OBSERVAÇÃO: Todo desconto exige uma linha "OBS: [justificativa técnica]".
[ESTRUTURA DE TÓPICOS E CÁLCULO]
EXTERIOR (LATARIA, PINTURA, CROMADOS E VIDROS): Valor Máximo 30 pontos.
INTERIOR (ESTOFAMENTO, PAINEL E GUARNIÇÕES): Valor Máximo 30 pontos.
MECÂNICA (MOTOR E TRANSMISSÃO): Valor Máximo 30 pontos.
CONSERVAÇÃO E COMPLEMENTARES (RODAS, PNEUS E LUZES): Valor Máximo 10 pontos.
[LÓGICA DE EXECUÇÃO]
Descreva tecnicamente o que é visto em cada tópico antes de aplicar a pontuação.
Realize o cálculo de subtração para cada subtotal (Máximo - Descontos).
Formato do Subtotal: "Subtotal: XX/XX".
CONFERÊNCIA: O Total Final deve ser a soma exata dos 4 subtotais.
RESULTADO FINAL: Exibir Total XX/100 e Status (Aprovado se >= 80).
FORMATO DE RESPOSTA OBRIGATÓRIO (MANTENHA OS NÚMEROS):

1- EXTERIOR
[Texto técnico aqui]
Subtotal: XX/30
OBS: [Justificativa]

2- INTERIOR
[Texto técnico aqui]
Subtotal: XX/30
OBS: [Justificativa]

3- MECÂNICA
[Texto técnico aqui]
Subtotal: XX/30
OBS: [Justificativa]

4- CONSERVAÇÃO
[Texto técnico aqui]
Subtotal: XX/10
OBS: [Justificativa]

📊 RESULTADO FINAL
TOTAL: XX / 100
🏁 VEREDITO: [APROVADO ou REPROVADO] para placa preta

💰 ANÁLISE DE MERCADO
💸 Venda rápida: R$ XXXXX
💰 Mercado particular: R$ XXXXX
🏆 Pós placa preta: R$ XXXXX
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
        return response.choices[0].message.content
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
    foto_adicional: Optional[UploadFile] = File(None),
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
        "adicional": salvar_imagem(foto_adicional, f"{pasta}/adicional.jpg"),
    }
    
    relatorio = gerar_relatorio(fotos_map)
    
    dados = {
        "nome": nome, "veiculo": {"marca": marca, "modelo": modelo, "ano": ano},
        "data": datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M"),
        "relatorio_ai": relatorio
    }
    
    with open(f"{pasta}/dados.json", "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)
    
    return RedirectResponse(url=f"/cliente/{cliente_id}", status_code=303)

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
        <a class="btn" href="/cliente/{id_}">Ver Relatório</a></div>"""
    html += "</div></body></html>"
    return HTMLResponse(html)

@app.get("/cliente/{id}", response_class=HTMLResponse)
def cliente(id: str):
    path = os.path.join(UPLOAD_DIR, id, "dados.json")
    if not os.path.exists(path): return HTMLResponse("Erro: Laudo não encontrado.")
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)
    
    texto = d.get("relatorio_ai", "")

    # --- NOVA FUNÇÃO DE EXTRAÇÃO ROBUSTA ---
    def extrair_secao_v3(num, proximo, original):
        try:
            # Captura tudo entre o número da seção e o próximo marco (número ou resultado final)
            padrao = rf"{num}[-\s\*\:]+(.*?)(?={proximo}|📊 RESULTADO FINAL|$)"
            match = re.search(padrao, original, re.DOTALL | re.IGNORECASE)
            if match:
                bloco = match.group(1).strip()
                
                # Extrai Subtotal
                sub_match = re.search(r"Subtotal:\s*(\d+/\d+)", bloco, re.IGNORECASE)
                sub_val = sub_match.group(1) if sub_match else "-- / --"
                
                # Extrai OBS
                obs_match = re.search(r"OBS:\s*(.*)", bloco, re.IGNORECASE | re.DOTALL)
                obs_val = obs_match.group(1).strip() if obs_match else "Nenhum desvio crítico observado."
                
                # Limpa o corpo (remove as linhas de subtotal e obs do texto principal)
                corpo = re.sub(r"Subtotal:.*", "", bloco, flags=re.IGNORECASE | re.DOTALL)
                corpo = re.sub(r"OBS:.*", "", corpo, flags=re.IGNORECASE | re.DOTALL).strip()
                
                return corpo, sub_val, obs_val
            return "Análise técnica em processamento...", "-- / --", "N/A"
        except:
            return "Erro na formatação.", "-- / --", "Erro"

    # Extração das seções
    sec_ext, sub_ext, obs_ext = extrair_secao_v3("1", "2", texto)
    sec_int, sub_int, obs_int = extrair_secao_v3("2", "3", texto)
    sec_mec, sub_mec, obs_mec = extrair_secao_v3("3", "4", texto)
    sec_cons, sub_cons, obs_cons = extrair_secao_v3("4", "📊", texto)
    
    # Score e Veredito
    score_list = re.findall(r"TOTAL:\s*(\d+)", texto, re.IGNORECASE)
    score = score_list[-1] if score_list else "00"
    veredito = "APROVADO" if "APROVADO" in texto.upper() else "REPROVADO"
    
    def get_val(regex, txt):
        m = re.search(regex, txt, re.IGNORECASE)
        return m.group(1).strip() if m else "R$ --"

    v_rapida = get_val(r"Venda rápida:?\s*(.*)", texto)
    v_part = get_val(r"Mercado particular:?\s*(.*)", texto)
    v_pos = get_val(r"Pós placa preta:?\s*(.*)", texto)

    # Fotos
    fotos_dir = os.path.join(UPLOAD_DIR, id)
    arquivos = sorted([f for f in os.listdir(fotos_dir) if f.endswith(".jpg")])
    
    foto_capa = f"/uploads/{id}/frente.jpg" if "frente.jpg" in arquivos else (f"/uploads/{id}/{arquivos}" if arquivos else "https://via.placeholder.com/800x400")
    fotos_grid_html = "".join([f'<div class="mini-foto" style="background-image:url(\'/uploads/{id}/{f}\');"></div>' for f in arquivos])

    return f"""
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>Laudo Técnico - {id}</title>
    <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&family=Montserrat:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{ --verde-escuro: #062b21; --verde-medio: #0b3b2e; --verde-claro: #1f6b4a; --bege-fundo: #e3e8e1; --bege-card: #f1f4ef; --dourado: #c8a96a; }}
        * {{ box-sizing: border-box; }}
        body {{ background-color: #222; font-family: 'Montserrat', sans-serif; margin: 0; padding: 20px; display: flex; justify-content: center; }}
        .laudo-folha {{ width: 1000px; background-color: var(--bege-fundo); padding: 30px; border-radius: 5px; box-shadow: 0 0 30px rgba(0,0,0,0.5); }}
        .header {{ background: linear-gradient(135deg, var(--verde-escuro), var(--verde-claro)); color: white; padding: 20px; border-radius: 10px; text-align: center; border-bottom: 4px solid var(--dourado); margin-bottom: 20px; }}
        .header h1 {{ font-family: 'Cinzel', serif; margin: 0; font-size: 42px; letter-spacing: 2px; }}
        .header p {{ margin: 5px 0 0; font-size: 16px; letter-spacing: 4px; font-weight: 300; }}
        .topo-container {{ display: grid; grid-template-columns: 400px 1fr; gap: 20px; margin-bottom: 20px; }}
        .dados-proprietario {{ background: var(--bege-card); border: 1px solid #c0c5bd; border-radius: 12px; padding: 15px; }}
        .info-row {{ display: flex; align-items: center; gap: 15px; padding: 10px 0; border-bottom: 1px solid #d0d5cd; }}
        .info-row:last-child {{ border: none; }}
        .icon {{ font-size: 24px; width: 30px; text-align: center; }}
        .info-text label {{ display: block; font-size: 11px; font-weight: 800; color: var(--verde-escuro); text-transform: uppercase; }}
        .info-text span {{ font-size: 15px; font-weight: 600; color: #333; }}
        .foto-principal {{ border: 5px solid #fff; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.2); overflow: hidden; height: 250px; }}
        .foto-principal img {{ width: 100%; height: 100%; object-fit: cover; }}
        .barra-titulo {{ background: var(--verde-escuro); color: white; padding: 10px 20px; border-radius: 8px; display: flex; align-items: center; gap: 15px; margin-bottom: 15px; }}
        .conteudo-grid {{ display: grid; grid-template-columns: 1fr 350px; gap: 20px; }}
        .card-avaliacao {{ background: var(--bege-card); border: 1px solid #c0c5bd; border-radius: 10px; margin-bottom: 15px; overflow: hidden; }}
        .card-header {{ background: linear-gradient(90deg, var(--verde-escuro), var(--verde-claro)); color: white; padding: 8px 15px; font-size: 13px; font-weight: 600; display: flex; justify-content: space-between; }}
        .card-body {{ display: grid; grid-template-columns: 1fr 180px; padding: 12px; gap: 15px; }}
        .itens-lista {{ font-size: 11px; line-height: 1.5; color: #444; white-space: pre-wrap; }}
        .obs-tecnica {{ font-size: 10px; background: #fff; padding: 8px; border-radius: 5px; border-left: 3px solid var(--verde-claro); }}
        .subtotal-box {{ grid-column: span 2; background: var(--verde-escuro); color: white; text-align: right; padding: 5px 15px; font-weight: bold; font-size: 18px; border-radius: 5px; }}
        .sidebar-card {{ background: var(--bege-card); border: 1px solid #c0c5bd; border-radius: 10px; margin-bottom: 15px; padding: 15px; }}
        .sidebar-titulo {{ border-bottom: 2px solid var(--verde-claro); color: var(--verde-escuro); font-weight: 700; font-size: 12px; margin-bottom: 10px; display: flex; align-items: center; gap: 8px; }}
        .resultado-final-box {{ text-align: center; padding: 10px; }}
        .score-grande {{ font-size: 48px; font-weight: 800; color: var(--verde-escuro); }}
        .veredito-tag {{ background: var(--verde-escuro); color: white; padding: 10px; border-radius: 8px; font-weight: 700; margin-top: 10px; }}
        .analise-mercado p {{ font-size: 12px; margin: 8px 0; display: flex; justify-content: space-between; border-bottom: 1px dashed #ccc; }}
        .foto-grid {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 5px; }}
        .mini-foto {{ aspect-ratio: 1; background: #ddd; border-radius: 4px; border: 1px solid #bbb; background-position: center; background-size: cover; }}
        .footer {{ margin-top: 20px; display: flex; justify-content: space-between; align-items: flex-end; }}
        .assinatura-box {{ text-align: center; width: 300px; }}
        .assinatura-linha {{ border-top: 2px solid #333; margin-bottom: 5px; }}
        .veredito-final-stamp {{ background: var(--verde-escuro); color: white; padding: 15px 30px; border-radius: 10px; text-align: center; }}
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
            <div class="info-row"><div class="icon">👤</div><div class="info-text"><label>Proprietário:</label><span>{d['nome']}</span></div></div>
            <div class="info-row"><div class="icon">🚗</div><div class="info-text"><label>Veículo:</label><span>{d['veiculo']['marca']} {d['veiculo']['modelo']} - {d['veiculo']['ano']}</span></div></div>
            <div class="info-row"><div class="icon">📅</div><div class="info-text"><label>Data:</label><span>{d['data']}</span></div></div>
            <div class="info-row"><div class="icon">🆔</div><div class="info-text"><label>Código:</label><span>{id}</span></div></div>
        </div>
        <div class="foto-principal"><img src="{foto_capa}" alt="Veículo"></div>
    </div>

    <div class="barra-titulo">
        <span style="font-size: 24px;">📄</span>
        <div><strong>RELATÓRIO DE VISTORIA</strong><br><span style="font-size: 10px; opacity: 0.8;">TÉCNICA DE ORIGINALIDADE AUTOMOTIVA</span></div>
    </div>

    <div class="conteudo-grid">
        <div class="col-esquerda">
            <div class="card-avaliacao">
                <div class="card-header"><span>I. 🚗 EXTERIOR E CARROCERIA (0-30 pts)</span></div>
                <div class="card-body">
                    <div class="itens-lista">{sec_ext}</div>
                    <div class="obs-tecnica"><strong>Observações:</strong><br>{obs_ext}</div>
                    <div class="subtotal-box">Subtotal: {sub_ext}</div>
                </div>
            </div>
            <div class="card-avaliacao">
                <div class="card-header"><span>II. 💺 INTERIOR E TAPEÇARIA (0-30 pts)</span></div>
                <div class="card-body">
                    <div class="itens-lista">{sec_int}</div>
                    <div class="obs-tecnica"><strong>Observações:</strong><br>{obs_int}</div>
                    <div class="subtotal-box">Subtotal: {sub_int}</div>
                </div>
            </div>
            <div class="card-avaliacao">
                <div class="card-header"><span>III. 🔧 MECÂNICA VISUAL / COFRE (0-30 pts)</span></div>
                <div class="card-body">
                    <div class="itens-lista">{sec_mec}</div>
                    <div class="obs-tecnica"><strong>Observações:</strong><br>{obs_mec}</div>
                    <div class="subtotal-box">Subtotal: {sub_mec}</div>
                </div>
            </div>
            <div class="card-avaliacao">
                <div class="card-header"><span>IV. ✨ CONSERVAÇÃO GERAL (0-10 pts)</span></div>
                <div class="card-body">
                    <div class="itens-lista">{sec_cons}</div>
                    <div class="obs-tecnica"><strong>Observações:</strong><br>{obs_cons}</div>
                    <div class="subtotal-box">Subtotal: {sub_cons}</div>
                </div>
            </div>
        </div>

        <div class="col-direita">
            <div class="sidebar-card">
                <div class="sidebar-titulo">📊 RESULTADO FINAL</div>
                <div class="resultado-final-box">
                    <label style="font-size: 12px;">TOTAL:</label>
                    <div class="score-grande">{score} / 100</div>
                    <div class="veredito-tag">{veredito}<br><span style="font-size: 11px; font-weight: 300;">para placa preta</span></div>
                </div>
            </div>

            <div class="sidebar-card">
                <div class="sidebar-titulo">💰 ANÁLISE DE MERCADO (R$)</div>
                <div class="analise-mercado">
                    <p>Venda rápida: <span>{v_rapida}</span></p>
                    <p>Particular: <span>{v_part}</span></p>
                    <p>Pós placa preta: <span>{v_pos}</span></p>
                </div>
            </div>

            <div class="sidebar-card">
                <div class="sidebar-titulo">📸 FOTOS DO VEÍCULO ({len(arquivos)})</div>
                <div class="foto-grid">{fotos_grid_html}</div>
            </div>
        </div>
    </div>

    <div class="footer">
        <div class="assinatura-box">
            <div class="assinatura-linha"></div>
            <strong style="font-size: 14px;">Perito Automotivo</strong><br>
            <span style="font-size: 10px;">Sistema de Avaliação de Originalidade</span>
        </div>
        <div class="veredito-final-stamp">
            <div style="font-size: 10px; opacity: 0.8;">PONTUAÇÃO FINAL</div>
            <div style="font-size: 24px; font-weight: 800;">{score}</div>
            <div style="font-size: 9px;">DE 100 PONTOS</div>
        </div>
    </div>
</div>
</body>
</html>
    """