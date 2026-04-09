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
import re

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


# 🧠 PROMPT (ABSOLUTAMENTE INTACTO CONFORME SOLICITADO)
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
        if not path or not os.path.exists(path): continue
        b64 = to_base64(path)
        if not b64: continue
        imgs.append({
            "type": "image_url", 
            "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
        })

    prompt = gerar_prompt()
    
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{
                "role": "user", 
                "content": [
                    {"type": "text", "text": prompt},
                    *imgs
                ]
            }],
            temperature=0.1
        )
        # CORREÇÃO AQUI: Acessando o conteúdo de forma segura
        return response.choices[0].message.content
    except Exception as e:
        return f"Erro ao processar IA: {str(e)}"


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
    cliente_id = f"{nome}_{uuid.uuid4().hex[:6]}".replace(" ", "_")
    pasta = os.path.join(UPLOAD_DIR, cliente_id)
    os.makedirs(pasta, exist_ok=True)

    dados = {
        "nome": nome, "email": email, "telefone": telefone,
        "veiculo": {"marca": marca, "modelo": modelo, "ano": ano},
        "data": datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M"),
        "id": cliente_id
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

    return {"ok": True, "id": cliente_id}


# 📊 DASHBOARD
@app.get("/avaliacoes", response_class=HTMLResponse)
def avaliacoes():
    clientes = []
    for pasta in os.listdir(UPLOAD_DIR):
        path = os.path.join(UPLOAD_DIR, pasta, "dados.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                clientes.append((pasta, json.load(f)))
    clientes.reverse()

    html = """<html><head><style>
        body { font-family: Arial; background: #f2f2f2; padding: 20px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 16px; }
        .card { background: #fff; border-radius: 14px; padding: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
        .btn { display: inline-block; margin-top: 10px; padding: 10px 12px; background: #111; color: #fff; border-radius: 8px; text-decoration: none; font-size: 13px; }
    </style></head><body><h1>Dashboard</h1><div class="grid">"""

    for id_, d in clientes:
        v = d.get("veiculo", {})
        html += f"""<div class="card"><b>{d.get('nome')}</b><br>
        🚗 {v.get('marca')} {v.get('modelo')} ({v.get('ano')})<br>📅 {d.get('data')}<br>
        <a class="btn" href="/cliente/{id_}">Abrir laudo completo →</a></div>"""
    
    html += "</div></body></html>"
    return HTMLResponse(html)


# 👤 CLIENTE (COM O ESTILO DE DUAS COLUNAS SOLICITADO)
@app.get("/cliente/{id}", response_class=HTMLResponse)
def cliente(id: str):
    path = os.path.join(UPLOAD_DIR, id, "dados.json")
    if not os.path.exists(path): return HTMLResponse("Laudo não encontrado.")

    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)

    relatorio_texto = d.get("relatorio_ai", "")
    
    # ⛏️ Extração de dados da IA para preencher os campos do layout
    score_match = re.search(r"TOTAL:\s*(\d+)", relatorio_texto)
    score = score_match.group(1) if score_match else "00"
    
    veredito = "APROVADO" if "APROVADO" in relatorio_texto.upper() else "EM ANÁLISE"
    
    # Capturar valores de mercado
    v_rapida = re.search(r"Venda rápida:\s*(R\$\s*[\d\.\,kK\s-]+(a R\$\s*[\d\.\,kK\s-]+)?)", relatorio_texto)
    v_particular = re.search(r"Mercado particular:\s*(R\$\s*[\d\.\,kK\s-]+(a R\$\s*[\d\.\,kK\s-]+)?)", relatorio_texto)
    v_pos = re.search(r"Pós placa preta:\s*(R\$\s*[\d\.\,kK\s-]+(a R\$\s*[\d\.\,kK\s-]+)?)", relatorio_texto)

    # Fotos reais do diretório
    fotos_dir = os.path.join(UPLOAD_DIR, id)
    arquivos_fotos = sorted([f for f in os.listdir(fotos_dir) if f.endswith(".jpg")])
    
    foto_principal = f"/uploads/{id}/frente.jpg" if "frente.jpg" in arquivos_fotos else f"/uploads/{id}/{arquivos_fotos}" if arquivos_fotos else ""
    
    fotos_html = ""
    for f in arquivos_fotos:
        fotos_html += f'<div class="photo-box" style="background-image: url(\'/uploads/{id}/{f}\')"></div>'

    html_template = f"""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Laudo Técnico - {d.get('veiculo',{}).get('modelo')}</title>
    <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&family=Montserrat:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{ --verde-escuro: #052e22; --verde-medio: #145c43; --dourado: #b59a5d; --bege-fundo: #e6e2d8; --branco: #ffffff; }}
        body {{ margin: 0; padding: 20px; background: var(--bege-fundo); font-family: 'Montserrat', sans-serif; color: #333; }}
        .container {{ width: 1000px; margin: auto; display: grid; grid-template-columns: 1.8fr 1fr; gap: 15px; }}
        .header {{ grid-column: 1 / -1; background: linear-gradient(90deg, #052e22, #1a4a3a); color: white; padding: 15px 25px; display: flex; align-items: center; justify-content: space-between; border-radius: 8px; border-bottom: 4px solid var(--dourado); }}
        .header h1 {{ font-family: 'Cinzel', serif; font-size: 32px; margin: 0; letter-spacing: 2px; }}
        .card {{ background: var(--branco); border-radius: 8px; overflow: hidden; box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-bottom: 15px; }}
        .card-title {{ background: var(--verde-escuro); color: var(--branco); padding: 8px 15px; font-size: 13px; font-weight: 700; text-transform: uppercase; }}
        .card-body {{ padding: 12px 15px; position: relative; }}
        .info-row {{ display: flex; margin-bottom: 8px; border-bottom: 1px solid #eee; padding-bottom: 4px; font-size: 13px; }}
        .info-label {{ font-weight: 700; width: 120px; color: var(--verde-escuro); }}
        .resultado-box {{ text-align: center; border: 2px solid var(--dourado); padding: 15px; border-radius: 8px; background: white; }}
        .total-score {{ font-size: 48px; font-weight: 800; color: var(--verde-escuro); margin: 5px 0; }}
        .veradito-badge {{ background: var(--verde-escuro); color: white; padding: 10px; border-radius: 6px; font-weight: 700; margin-top: 10px; }}
        .mercado-item {{ display: flex; justify-content: space-between; padding: 5px 0; border-bottom: 1px dashed #ccc; font-size: 12px; }}
        .photo-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 5px; }}
        .photo-box {{ background: #ddd; height: 80px; border-radius: 4px; background-size: cover; background-position: center; }}
        pre {{ white-space: pre-wrap; font-family: inherit; font-size: 12px; line-height: 1.5; color: #444; background: #fafafa; padding: 10px; border-radius: 5px; }}
        .footer {{ grid-column: 1 / -1; text-align: center; font-size: 10px; color: #666; padding: 20px; }}
    </style>
    </head>
    <body>
    <div class="container">
        <header class="header">
            <div><h1>LAUDO TÉCNICO PERICIAL</h1><span>ORIGINALIDADE E ANTIGOMOBILISMO</span></div>
            <div style="background: var(--dourado); color: white; padding: 4px 10px; border-radius: 4px; font-size: 10px; font-weight: bold;">CERTIFICADO PREMIUM</div>
        </header>

        <div class="left-col">
            <div class="card">
                <div class="card-title">● DADOS DO VEÍCULO</div>
                <div class="card-body">
                    <div class="info-row"><span class="info-label">PROPRIETÁRIO:</span> {d.get('nome')}</div>
                    <div class="info-row"><span class="info-label">VEÍCULO:</span> {d.get('veiculo',{}).get('marca')} {d.get('veiculo',{}).get('modelo')} ({d.get('veiculo',{}).get('ano')})</div>
                    <div class="info-row"><span class="info-label">DATA:</span> {d.get('data')}</div>
                </div>
            </div>

            <div class="card">
                <div class="card-title">● RELATÓRIO DE VISTORIA DETALHADO</div>
                <div class="card-body">
                    <pre>{relatorio_texto}</pre>
                </div>
            </div>
        </div>

        <div class="right-col">
            <div class="card">
                <div style="height: 200px; background: #f0f0f0 url('{foto_principal}') center/cover no-repeat;">
                    {"" if foto_principal else "[ Foto Principal ]"}
                </div>
            </div>

            <div class="resultado-box">
                <span style="font-family: 'Cinzel'; font-weight: bold; color: var(--verde-escuro);">PONTUAÇÃO FINAL</span>
                <div class="total-score">{score} <span style="font-size: 20px; color: #999;">/ 100</span></div>
                <div class="veradito-badge">{veredito} PARA PLACA PRETA</div>
            </div>

            <div class="card" style="margin-top: 15px;">
                <div class="card-title">● ANÁLISE DE MERCADO (BRASIL)</div>
                <div class="card-body">
                    <div class="mercado-item"><span>Venda rápida:</span> <b>{v_rapida.group(1) if v_rapida else "Consulte Relatório"}</b></div>
                    <div class="mercado-item"><span>Particular:</span> <b>{v_particular.group(1) if v_particular else "Consulte Relatório"}</b></div>
                    <div class="mercado-item"><span>Pós Placa Preta:</span> <b>{v_pos.group(1) if v_pos else "Consulte Relatório"}</b></div>
                </div>
            </div>

            <div class="card">
                <div class="card-title">● FOTOS DO VEÍCULO ({len(arquivos_fotos)})</div>
                <div class="card-body">
                    <div class="photo-grid">{fotos_html}</div>
                </div>
            </div>
        </div>

        <footer class="footer">SISTEMA DE AVALIAÇÃO DE ORIGINALIDADE • LAUDO GERADO EM {datetime.now().year}</footer>
    </div>
    </body>
    </html>
    """
    return HTMLResponse(html_template)