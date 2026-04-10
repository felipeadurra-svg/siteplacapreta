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
        return response.choices.message.content
    except Exception as e:
        return f"Erro na IA: {str(e)}"

def renderizar_laudo_html(id_cliente, dados_json):
    """Lógica que transforma o texto da IA no HTML estilizado (o mesmo que você já usa)"""
    texto = dados_json.get("relatorio_ai", "")
    
    def extrair_secao_v2(prefixo, proximo, original):
        try:
            padrao = rf"{prefixo}(.*?)(?={proximo}|$)"
            match = re.search(padrao, original, re.DOTALL | re.IGNORECASE)
            if match:
                res = match.group(1).strip()
                sub = re.search(r"Subtotal:\s*(\d+/\d+)", res, re.IGNORECASE)
                sub_val = sub.group(1) if sub else "-- / --"
                obs = re.search(r"OBS:\s*(.*)", res, re.IGNORECASE)
                obs_val = obs.group(1).strip() if obs else "Sem descontos visíveis."
                res_limpo = re.sub(r"Subtotal:.*", "", res, flags=re.IGNORECASE)
                res_limpo = re.sub(r"OBS:.*", "", res_limpo, flags=re.IGNORECASE).strip()
                return res_limpo, sub_val, obs_val
            return "Dados não localizados.", "-- / --", "N/A"
        except: return "Erro", "-- / --", "Erro"

    sec_ext, sub_ext, obs_ext = extrair_secao_v2("1- EXTERIOR", "2- INTERIOR", texto)
    sec_int, sub_int, obs_int = extrair_secao_v2("2- INTERIOR", "3- MECÂNICA", texto)
    sec_mec, sub_mec, obs_mec = extrair_secao_v2("3- MECÂNICA", "4- CONSERVAÇÃO", texto)
    sec_cons, sub_cons, obs_cons = extrair_secao_v2("4- CONSERVAÇÃO", "RESULTADO FINAL", texto)
    
    score = (re.findall(r"TOTAL:\s*(\d+)", texto) or ["00"])[-1]
    veredito = "APROVADO" if "APROVADO" in texto.upper() else "REPROVADO"
    
    def get_val(regex, txt):
        m = re.search(regex, txt, re.IGNORECASE)
        return m.group(1).strip() if m else "R$ --"

    v_rapida = get_val(r"Venda rápida:?\s*(.*)", texto)
    v_part = get_val(r"Mercado particular:?\s*(.*)", texto)
    v_pos = get_val(r"Pós placa preta:?\s*(.*)", texto)

    fotos_dir = os.path.join(UPLOAD_DIR, id_cliente)
    arquivos = sorted([f for f in os.listdir(fotos_dir) if f.endswith(".jpg")])
    
    foto_capa = f"/uploads/{id_cliente}/frente.jpg" if "frente.jpg" in arquivos else "https://via.placeholder.com/800x400"
    fotos_grid_html = "".join([f'<div class="mini-foto" style="background-image:url(\'/uploads/{id_cliente}/{f}\');"></div>' for f in arquivos])

    return f"""
    <div class="laudo-folha">
        <style>
            :root {{ --verde-escuro: #062b21; --verde-medio: #0b3b2e; --verde-claro: #1f6b4a; --bege-fundo: #e3e8e1; --bege-card: #f1f4ef; --dourado: #c8a96a; }}
            .laudo-folha {{ width: 100%; max-width: 1000px; background-color: var(--bege-fundo); padding: 30px; border-radius: 5px; margin: auto; color: #333; text-align: left; }}
            .header-laudo {{ background: linear-gradient(135deg, var(--verde-escuro), var(--verde-claro)); color: white; padding: 20px; border-radius: 10px; text-align: center; border-bottom: 4px solid var(--dourado); margin-bottom: 20px; }}
            .header-laudo h1 {{ font-family: 'Cinzel', serif; margin: 0; font-size: 32px; }}
            .topo-container {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }}
            .dados-proprietario {{ background: var(--bege-card); border: 1px solid #c0c5bd; border-radius: 12px; padding: 15px; font-size: 14px; }}
            .foto-principal {{ border: 5px solid #fff; border-radius: 15px; overflow: hidden; height: 200px; }}
            .foto-principal img {{ width: 100%; height: 100%; object-fit: cover; }}
            .card-avaliacao {{ background: var(--bege-card); border: 1px solid #c0c5bd; border-radius: 10px; margin-bottom: 15px; overflow: hidden; }}
            .card-header {{ background: var(--verde-escuro); color: white; padding: 8px 15px; font-weight: bold; display: flex; justify-content: space-between; }}
            .card-body {{ padding: 12px; display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }}
            .subtotal-box {{ grid-column: span 2; background: var(--verde-escuro); color: white; text-align: right; padding: 5px 15px; font-weight: bold; border-radius: 5px; }}
            .mini-foto {{ width: 60px; height: 60px; background-size: cover; background-position: center; border-radius: 4px; display: inline-block; margin: 2px; }}
            .veredito-tag {{ background: var(--verde-escuro); color: white; padding: 10px; border-radius: 8px; text-align: center; font-weight: bold; }}
        </style>
        <div class="header-laudo"><h1>LAUDO TÉCNICO PERICIAL</h1><p>ORIGINALIDADE E ANTIGOMOBILISMO</p></div>
        <div class="topo-container">
            <div class="dados-proprietario">
                <b>Proprietário:</b> {dados_json['nome']}<br>
                <b>Veículo:</b> {dados_json['veiculo']['marca']} {dados_json['veiculo']['modelo']}<br>
                <b>Ano:</b> {dados_json['veiculo']['ano']}<br>
                <b>Data:</b> {dados_json['data']}
            </div>
            <div class="foto-principal"><img src="{foto_capa}"></div>
        </div>
        <div class="card-avaliacao">
            <div class="card-header">EXTERIOR <span>{sub_ext}</span></div>
            <div class="card-body"><div>{sec_ext}</div><div style="font-size:10px; background:#fff; padding:5px;">{obs_ext}</div></div>
        </div>
        <div class="card-avaliacao">
            <div class="card-header">INTERIOR <span>{sub_int}</span></div>
            <div class="card-body"><div>{sec_int}</div><div style="font-size:10px; background:#fff; padding:5px;">{obs_int}</div></div>
        </div>
        <div class="card-avaliacao">
            <div class="card-header">MECÂNICA <span>{sub_mec}</span></div>
            <div class="card-body"><div>{sec_mec}</div><div style="font-size:10px; background:#fff; padding:5px;">{obs_mec}</div></div>
        </div>
        <div class="veredito-tag">{veredito} - {score}/100 PONTOS</div>
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
    
    # Gerar o HTML do laudo para retornar ao front
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
    return HTMLResponse(f"<html><body style='background:#222; padding:20px;'>{renderizar_laudo_html(id, d)}</body></html>")