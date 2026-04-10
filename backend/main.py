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
Você é um PERITO AUTOMOTIVO ESPECIALISTA EM ANTIGOMOBILISMO.
Produza um LAUDO TÉCNICO seguindo rigorosamente os itens abaixo.

⚠️ REGRAS DE FORMATAÇÃO (ESTRITA):
- NÃO USE EMOJIS (nada de 📌, 🚗, ✅, ❌).
- Use exatamente os tópicos listados abaixo.
- Formato: "- **Item** : Comentário técnico" (Negrito, espaço, dois pontos).

⚠️ REGRAS CRÍTICAS:
- NÃO inventar peças não visíveis
- NÃO usar fórmulas ou cálculos no texto
- Linguagem técnica estilo clube de antigomobilismo
- Base exclusivamente em evidência visual
- Todo desconto deve vir acompanhado de justificativa técnica objetiva



⚖️ CRITÉRIOS DE PONTUAÇÃO:
- Redução de 1 ponto: Padrão para desvios comuns (pneus modernos, filtros, pequenos desgastes).
- Redução de 2 ou mais pontos: Apenas para modificações graves ou falta de originalidade crítica.

ESTRUTURA OBRIGATÓRIA:

1- EXTERIOR E CARROCERIA (0-30pts)
- **Alinhamento de porta** : 
- **Pintura** : 
- **Cromados e lanternas** : 
- **Rodas e pneus** : 
- **Sinais de restauração** : 
DESCONTO: (Se houver, descreva aqui. Se não, escreva "Sem descontos")
Subtotal: XX/30

2- INTERIOR E TAPEÇARIA (0-30pts)
- **Painel** : 
- **Volante** : 
- **Bancos e tecidos** : 
- **Forração** : 
- **Conservação geral** : 
DESCONTO: (Se houver, descreva aqui. Se não, escreva "Sem descontos")
Subtotal: XX/30

3- MECÂNICA / VISUAL (0-30pts)
- **Organização do cofre** : 
- **Fiação aparente** : 
- **Componentes originais visíveis** : 
- **Suspensão e rodas** : 
DESCONTO: (Se houver, descreva aqui. Se não, escreva "Sem descontos")
Subtotal: XX/30

4- CONSERVAÇÃO (0-10pts)
- **Estrutura aparente** : 
- **Borrachas** : 
- **Desgaste natural** : 
DESCONTO: (Se houver, descreva aqui. Se não, escreva "Sem descontos")
Subtotal: XX/10

📊 RESULTADO FINAL
TOTAL: XX/100
🏁 VEREDITO: (APROVADO ou REPROVADO)

💰 ANÁLISE DE MERCADO
Venda rápida: R$ XXX
Mercado particular: R$ XXX
Pós placa preta: R$ XXX

🧠 RECOMENDAÇÕES
(Liste as sugestões técnicas aqui no formato - **Item** : Sugestão)
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

    # Função para limpar e converter Markdown em HTML simples
    def formatar(txt):
        if not txt: return ""
        # Converte **Texto** para <b>Texto</b>
        txt = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", txt)
        # Converte quebras de linha em <br>
        return txt.replace("\n", "<br>")

    def parse_section(num_id, texto_bruto):
        try:
            # Regex para capturar da seção X- até a próxima seção ou marcador final
            padrao = rf"{num_id}.*?\n(.*?)(?=\n\d-|\n📊|\n🏁|\n💰|\n🧠|$)"
            match = re.search(padrao, texto_bruto, re.DOTALL | re.IGNORECASE)
            if not match: return "Dados não localizados.", "Sem descontos.", "0"
            
            bloco = match.group(1).strip()
            
            # Extração da nota numérica do subtotal
            score_match = re.search(r"Subtotal:\s*(\d+)", bloco, re.IGNORECASE)
            score = score_match.group(1) if score_match else "0"
            
            # Divisão entre Observações e Descontos baseada na palavra DESCONTO:
            partes = re.split(r"(?i)DESCONTO:", bloco)
            obs = partes.strip()
            
            # Limpa o texto das observações removendo a linha final de subtotal que a IA possa ter repetido
            obs = re.sub(r"(?i)Subtotal:.*", "", obs).strip()
            
            desc = partes.split("Subtotal").strip() if len(partes) > 1 else "Sem descontos técnicos visíveis."
            
            return formatar(obs), formatar(desc), score
        except: return "Erro no processamento", "Erro", "0"

    # Extração das 4 seções baseadas nos números 1-, 2-, 3-, 4-
    ext_obs, ext_desc, ext_pts = parse_section("1-", texto)
    int_obs, int_desc, int_pts = parse_section("2-", texto)
    mec_obs, mec_desc, mec_pts = parse_section("3-", texto)
    cons_obs, cons_desc, cons_pts = parse_section("4-", texto)
    
    # Captura de Valores de Mercado
    def get_val(regex, txt):
        m = re.search(regex, txt, re.IGNORECASE)
        return m.group(1).strip() if m else "Consulte"

    v_rapida = get_val(r"Venda rápida:?\s*(.*)", texto)
    v_part = get_val(r"Mercado particular:?\s*(.*)", texto)
    v_pos = get_val(r"Pós placa preta:?\s*(.*)", texto)

    # Captura de Recomendações e Veredito
    recom_match = re.search(r"RECOMENDAÇÕES(.*?)(?=$)", texto, re.DOTALL | re.IGNORECASE)
    recom = formatar(recom_match.group(1).strip()) if recom_match else "Sem recomendações adicionais."
    
    score_final = (re.findall(r"TOTAL:\s*(\d+)", texto) or ["00"])[-1]
    veredito = "APROVADO" if "APROVADO" in texto.upper() else "REPROVADO"

    fotos_dir = os.path.join(UPLOAD_DIR, id)
    arquivos = sorted([f for f in os.listdir(fotos_dir) if f.endswith(".jpg")])
    fotos_html = "".join([f'<div class="img-mini" style="background-image:url(\'/uploads/{id}/{f}\')"></div>' for f in arquivos])

    return f"""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <title>Laudo Técnico - {id}</title>
        <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;700&display=swap" rel="stylesheet">
        <style>
            :root {{ --dark: #052e22; --gold: #b59a5d; --bg: #d9d4c7; --white: #ffffff; }}
            body {{ font-family: 'Montserrat', sans-serif; background: var(--bg); margin: 0; padding: 40px; color: #333; }}
            .paper {{ width: 900px; margin: auto; background: var(--white); padding: 40px; border-radius: 4px; box-shadow: 0 10px 30px rgba(0,0,0,0.15); }}
            
            .header-laudo {{ background: var(--dark); color: white; padding: 25px; border-radius: 4px; margin-bottom: 30px; display: flex; justify-content: space-between; align-items: center; border-bottom: 4px solid var(--gold); }}
            .header-laudo h1 {{ margin: 0; font-size: 24px; letter-spacing: 1px; }}
            
            .card-secao {{ margin-bottom: 20px; border: 1px solid #ddd; border-radius: 8px; overflow: hidden; }}
            .card-header {{ background: var(--dark); color: white; padding: 10px 15px; font-weight: bold; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px; }}
            .card-content {{ display: flex; min-height: 140px; }}
            
            .col-main {{ width: 68%; padding: 15px; border-right: 1px solid #eee; font-size: 13px; line-height: 1.6; }}
            .col-side {{ width: 32%; padding: 15px; background: #fcfcfc; display: flex; flex-direction: column; justify-content: space-between; }}
            
            .label-tec {{ font-size: 10px; font-weight: 700; color: #999; text-transform: uppercase; margin-bottom: 4px; display: block; }}
            .desc-txt {{ font-size: 11.5px; color: #444; line-height: 1.4; }}
            
            .subtotal-tag {{ background: var(--dark); color: white; text-align: center; padding: 8px; border-radius: 4px; margin-top: 10px; }}
            .subtotal-tag small {{ font-size: 9px; display: block; opacity: 0.7; text-transform: uppercase; }}
            .subtotal-tag b {{ font-size: 20px; }}

            .recom-box {{ background: #fffde7; border: 1px solid #e6d8ad; padding: 20px; border-radius: 8px; margin-top: 20px; font-size: 13px; }}
            
            .mercado-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-top: 20px; }}
            .mercado-item {{ background: #f4f4f4; padding: 15px; border-radius: 6px; text-align: center; border-bottom: 3px solid var(--gold); }}
            .mercado-item span {{ font-size: 10px; color: #777; font-weight: bold; text-transform: uppercase; }}
            .mercado-item div {{ font-size: 14px; font-weight: bold; color: var(--dark); margin-top: 5px; }}

            .score-final-box {{ text-align: center; padding: 30px; border: 5px solid var(--dark); margin-top: 30px; border-radius: 10px; }}
            .veredito-label {{ background: var(--dark); color: white; padding: 12px; font-weight: bold; margin-top: 15px; display: inline-block; width: 80%; border-radius: 4px; }}
            
            .grid-fotos {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-top: 30px; border-top: 1px solid #eee; padding-top: 20px; }}
            .img-mini {{ height: 85px; background-size: cover; background-position: center; border: 1px solid #ddd; border-radius: 4px; }}
        </style>
    </head>
    <body>
        <div class="paper">
            <header class="header-laudo">
                <div><h1>RELATÓRIO DE VISTORIA</h1><small>AVALIAÇÃO TÉCNICA DE ORIGINALIDADE</small></div>
                <div style="text-align:right; font-size: 12px;"><b>PROPRIETÁRIO:</b> {d['nome']}<br><b>EMISSÃO:</b> {d['data']}</div>
            </header>

            <div class="card-secao">
                <div class="card-header">1- EXTERIOR E CARROCERIA (0-30pts)</div>
                <div class="card-content">
                    <div class="col-main">{ext_obs}</div>
                    <div class="col-side">
                        <div><span class="label-tec">Observações técnicas:</span><div class="desc-txt">{ext_desc}</div></div>
                        <div class="subtotal-tag"><small>SUBTOTAL</small><b>{ext_pts} / 30</b></div>
                    </div>
                </div>
            </div>

            <div class="card-secao">
                <div class="card-header">2- INTERIOR E TAPEÇARIA (0-30pts)</div>
                <div class="card-content">
                    <div class="col-main">{int_obs}</div>
                    <div class="col-side">
                        <div><span class="label-tec">Observações técnicas:</span><div class="desc-txt">{int_desc}</div></div>
                        <div class="subtotal-tag"><small>SUBTOTAL</small><b>{int_pts} / 30</b></div>
                    </div>
                </div>
            </div>

            <div class="card-secao">
                <div class="card-header">3- MECÂNICA / VISUAL (0-30pts)</div>
                <div class="card-content">
                    <div class="col-main">{mec_obs}</div>
                    <div class="col-side">
                        <div><span class="label-tec">Observações técnicas:</span><div class="desc-txt">{mec_desc}</div></div>
                        <div class="subtotal-tag"><small>SUBTOTAL</small><b>{mec_pts} / 30</b></div>
                    </div>
                </div>
            </div>

            <div class="card-secao">
                <div class="card-header">4- CONSERVAÇÃO (0-10pts)</div>
                <div class="card-content">
                    <div class="col-main">{cons_obs}</div>
                    <div class="col-side">
                        <div><span class="label-tec">Observações técnicas:</span><div class="desc-txt">{cons_desc}</div></div>
                        <div class="subtotal-tag"><small>SUBTOTAL</small><b>{cons_pts} / 10</b></div>
                    </div>
                </div>
            </div>

            <div class="recom-box"><b>RECOMENDAÇÕES TÉCNICAS:</b><br>{recom}</div>

            <div class="mercado-grid">
                <div class="mercado-item"><span>Venda Rápida</span><div>{v_rapida}</div></div>
                <div class="mercado-item"><span>Particular</span><div>{v_part}</div></div>
                <div class="mercado-item"><span>Pós Placa Preta</span><div>{v_pos}</div></div>
            </div>

            <div class="score-final-box">
                <span style="font-size:13px; font-weight:bold; color:#777;">PONTUAÇÃO FINAL</span><br>
                <span style="font-size:60px; font-weight:900; color:var(--dark)">{score_final} / 100</span><br>
                <div class="veredito-label">{veredito} PARA PLACA PRETA</div>
            </div>

            <div class="grid-fotos">{fotos_html}</div>
            
            <p style="text-align:center; font-size:10px; color:#999; margin-top:30px;">
                Este laudo é uma análise visual baseada nas imagens fornecidas. Para certificação oficial, é necessária vistoria presencial por clube credenciado ao Denatran.
            </p>
        </div>
    </body>
    </html>
    """