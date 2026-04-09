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


# 🧠 PROMPT ABSOLUTAMENTE INTACTO CONFORME SOLICITADO
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
- profissionalismo e cuidado
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


# 📥 ROTA DE ENVIO
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


# 📊 DASHBOARD (RESTAURADO)
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
        body { font-family: sans-serif; background: #f2f2f2; padding: 20px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 16px; }
        .card { background: #fff; border-radius: 12px; padding: 16px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
        .btn { display: inline-block; margin-top: 10px; padding: 10px; background: #052e22; color: #fff; border-radius: 6px; text-decoration: none; }
    </style></head><body><h1>Dashboard de Avaliações</h1><div class="grid">"""

    for id_, d in clientes:
        v = d.get("veiculo", {})
        html += f"""<div class="card"><b>{d.get('nome')}</b><br>
        🚗 {v.get('marca')} {v.get('modelo')} ({v.get('ano')})<br>📅 {d.get('data')}<br>
        <a class="btn" href="/cliente/{id_}">Ver Laudo Técnico →</a></div>"""
    
    html += "</div></body></html>"
    return HTMLResponse(html)


# 👤 CLIENTE (LAUDO DESIGN PREMIUM)
@app.get("/cliente/{id}", response_class=HTMLResponse)
def cliente(id: str):
    path = os.path.join(UPLOAD_DIR, id, "dados.json")
    if not os.path.exists(path): return HTMLResponse("Erro: Laudo não encontrado.")

    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)

    texto = d.get("relatorio_ai", "")

    def extrair(inicio, fim, original):
        try:
            pattern = f"{re.escape(inicio)}(.*?){re.escape(fim)}"
            match = re.search(pattern, original, re.DOTALL | re.IGNORECASE)
            return match.group(1).strip() if match else "Dados não identificados."
        except: return "Erro na extração"

    # Fatiamento por Regex baseado no seu Prompt
    sec_ident = extrair("📌 IDENTIFICAÇÃO DO VEÍCULO", "I. 🚗 EXTERIOR", texto)
    sec_ext = extrair("I. 🚗 EXTERIOR E CARROCERIA (0–30 pts)", "II. 🪑 INTERIOR", texto)
    sec_int = extrair("II. 🪑 INTERIOR E TAPEÇARIA (0–30 pts)", "III. 🧰 MECÂNICA", texto)
    sec_mec = extrair("III. 🧰 MECÂNICA VISUAL / COFRE (0–30 pts)", "IV. 🧼 CONSERVAÇÃO", texto)
    sec_cons = extrair("IV. 🧼 CONSERVAÇÃO GERAL (0–10 pts)", "📊 RESULTADO FINAL", texto)
    sec_recom = extrair("🧠 RECOMENDAÇÕES", "✍️ ASSINATURA", texto)

    score = re.search(r"TOTAL:\s*(\d+)", texto)
    score = score.group(1) if score else "00"
    veredito = "APROVADO" if "APROVADO" in texto.upper() else "EM ANÁLISE"
    
    v_rapida = re.search(r"💸 Venda rápida:\s*(.*)", texto)
    v_part = re.search(r"💰 Mercado particular:\s*(.*)", texto)
    v_pos = re.search(r"🏆 Pós placa preta:\s*(.*)", texto)

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
            body {{ font-family: 'Montserrat', sans-serif; background: var(--bg); margin: 0; padding: 20px; color: #333; }}
            .container {{ width: 1000px; margin: auto; display: grid; grid-template-columns: 1.8fr 1fr; gap: 20px; }}
            .header {{ grid-column: 1/-1; background: var(--dark); color: white; padding: 25px; border-radius: 8px; border-bottom: 5px solid var(--gold); display: flex; justify-content: space-between; align-items: center; }}
            .header h1 {{ font-family: 'Cinzel', serif; margin: 0; font-size: 30px; letter-spacing: 2px; }}
            .card {{ background: var(--white); border-radius: 8px; margin-bottom: 15px; overflow: hidden; border: 1px solid #ddd; }}
            .card-header {{ background: var(--dark); color: white; padding: 10px 15px; font-weight: bold; font-size: 13px; text-transform: uppercase; }}
            .card-body {{ padding: 15px; line-height: 1.6; font-size: 13px; }}
            .score-box {{ background: var(--white); border: 3px solid var(--gold); border-radius: 8px; padding: 25px; text-align: center; margin-bottom: 20px; }}
            .score-num {{ font-size: 60px; font-weight: 800; color: var(--dark); margin: 10px 0; }}
            .veredito {{ background: var(--dark); color: white; padding: 12px; border-radius: 6px; font-weight: bold; text-transform: uppercase; }}
            .mercado-item {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px dashed #ccc; }}
            .photo-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; }}
            .img-mini {{ height: 100px; background-size: cover; background-position: center; border-radius: 4px; border: 1px solid #ddd; }}
            .main-img {{ height: 260px; background: #eee url('{foto_capa}') center/cover; border-radius: 8px; margin-bottom: 20px; }}
            pre {{ white-space: pre-wrap; font-family: inherit; margin: 0; }}
            .footer {{ grid-column: 1/-1; text-align: center; font-size: 10px; padding: 30px; color: #777; }}
        </style>
    </head>
    <body>
        <div class="container">
            <header class="header">
                <div><h1>LAUDO TÉCNICO PERICIAL</h1><span>ORIGINALIDADE E ANTIGOMOBILISMO</span></div>
                <div style="text-align: right; font-size: 12px;">ID: {id}<br>EMISSÃO: {d['data']}</div>
            </header>
            <div class="left-col">
                <div class="card"><div class="card-header">● DADOS E IDENTIFICAÇÃO</div><div class="card-body"><b>PROPRIETÁRIO:</b> {d['nome']}<br><pre>{sec_ident}</pre></div></div>
                <div class="card"><div class="card-header">I. EXTERIOR E CARROCERIA</div><div class="card-body"><pre>{sec_ext}</pre></div></div>
                <div class="card"><div class="card-header">II. INTERIOR E TAPEÇARIA</div><div class="card-body"><pre>{sec_int}</pre></div></div>
                <div class="card"><div class="card-header">III. MECÂNICA VISUAL</div><div class="card-body"><pre>{sec_mec}</pre></div></div>
                <div class="card"><div class="card-header">IV. CONSERVAÇÃO GERAL</div><div class="card-body"><pre>{sec_cons}</pre></div></div>
                <div class="card" style="border-left: 6px solid var(--dark);"><div class="card-header">🧠 RECOMENDAÇÕES</div><div class="card-body"><pre>{sec_recom}</pre></div></div>
            </div>
            <div class="right-col">
                <div class="main-img"></div>
                <div class="score-box">
                    <div style="font-family: Cinzel; color: var(--dark);">PONTUAÇÃO FINAL</div>
                    <div class="score-num">{score}<span style="font-size: 20px; color: #999;">/100</span></div>
                    <div class="veredito">{veredito} PARA PLACA PRETA</div>
                </div>
                <div class="card">
                    <div class="card-header">💰 ANÁLISE DE MERCADO</div>
                    <div class="card-body">
                        <div class="mercado-item"><span>Venda Rápida:</span> <b>{v_rapida.group(1) if v_rapida else "---"}</b></div>
                        <div class="mercado-item"><span>Particular:</span> <b>{v_part.group(1) if v_part else "---"}</b></div>
                        <div class="mercado-item"><span>Pós Placa:</span> <b>{v_pos.group(1) if v_pos else "---"}</b></div>
                    </div>
                </div>
                <div class="card"><div class="card-header">📷 REGISTRO FOTOGRÁFICO</div><div class="card-body"><div class="photo-grid">{fotos_html}</div></div></div>
            </div>
            <footer class="footer">SISTEMA DE AVALIAÇÃO DE ORIGINALIDADE • {datetime.now().year}</footer>
        </div>
    </body>
    </html>
    """