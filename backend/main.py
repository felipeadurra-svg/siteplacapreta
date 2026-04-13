from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from typing import Optional
from datetime import datetime
from zoneinfo import ZoneInfo
from openai import OpenAI
import mercadopago
import os
import uuid
import json
import base64
import re

app = FastAPI()

# 🔑 Configuração das APIs
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
sdk = mercadopago.SDK(os.getenv("MP_ACCESS_TOKEN"))
MODEL = "gpt-4o"

# 🌍 Configuração de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 📁 Configuração de Diretórios para Fotos
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# --- FUNÇÕES AUXILIARES ---

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
- REGRA DO 10/10: Se NÃO houver defeitos na seção de CONSERVAÇÃO, o subtotal DEVE ser 10/10.
- REGRA DO ESTADO IMPECÁVEL: Se NÃO houver reduções ou defeitos, a nota DEVE ser a máxima.
- Redução de 1 ponto: Itens desgastados ou peças de época não originais.
- Redução de 2 ou mais pontos: Faltas graves (ex: motor de outra marca, rebaixamento).

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
OBS: [Se houver desconto, descreva aqui]

2- INTERIOR  
-Painel: [comentário]
-Volante: [comentário]
-Bancos e tecidos: [comentário]
-Forração: [comentário]
-Conservação geral: [comentário]
Subtotal: XX/30
OBS: [Se houver desconto, descreva aqui]

3- MECÂNICA 
-Organização do cofre: [comentário]
-Fiação aparente: [comentário]
-Componentes originais visíveis: [comentário]
-Suspensão e rodas: [comentário]
Subtotal: XX/30
OBS: [Se houver desconto, descreva aqui]

4- CONSERVAÇÃO 
-Estrutura aparente: [comentário]
-Borrachas: [comentário]
-Desgaste natural: [comentário]
Subtotal: XX/10
OBS: [Se houver desconto, descreva aqui]

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
        if b64: 
            imgs.append({
                "type": "image_url", 
                "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
            })
    
    if not imgs: return "Erro: Fotos não processadas."

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": [{"type": "text", "text": gerar_prompt()}, *imgs]}],
            temperature=0.1
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Erro na análise da IA: {str(e)}"

# --- ROTAS DA API ---

@app.post("/create_preference")
async def create_preference(request: Request):
    try:
        body = await request.json()
        external_reference = body.get("external_reference")
        
        preference_data = {
            "items": [
                {
                    "title": "Laudo Técnico de Originalidade - MeuCarroAntigo",
                    "quantity": 1,
                    "unit_price": 1.00,
                    "currency_id": "BRL"
                }
            ],
            "external_reference": external_reference, # VINCULA O PAGAMENTO AO ID DO CLIENTE
            "back_urls": {
                "success": "https://meucarroantigo.com/avaliacao",
                "failure": "https://meucarroantigo.com/avaliacao",
                "pending": "https://meucarroantigo.com/avaliacao"
            },
            "auto_return": "approved",
            "notification_url": "https://siteplacapreta.onrender.com/webhook"
        }
        preference_response = sdk.preference().create(preference_data)
        return JSONResponse(content={"id": preference_response["response"]["id"]})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=400)

@app.post("/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
        if data.get("type") == "payment":
            payment_id = data.get("data", {}).get("id")
            payment_info = sdk.payment().get(payment_id)
            
            if payment_info["response"]["status"] == "approved":
                cliente_id = payment_info["response"]["external_reference"]
                pasta = os.path.join(UPLOAD_DIR, cliente_id)
                json_path = os.path.join(pasta, "dados.json")
                
                if os.path.exists(json_path):
                    with open(json_path, "r", encoding="utf-8") as f:
                        dados = json.load(f)
                    
                    # SÓ GERA O RELATÓRIO SE AINDA NÃO FOI PAGO
                    if not dados.get("pago"):
                        relatorio = gerar_relatorio(dados["fotos_map"])
                        dados["relatorio_ai"] = relatorio
                        dados["pago"] = True
                        
                        with open(json_path, "w", encoding="utf-8") as f:
                            json.dump(dados, f, ensure_ascii=False, indent=4)
    except:
        pass
    return {"status": "ok"}

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
    
    # SALVA TUDO, MAS NÃO CHAMA A IA AINDA
    dados = {
        "nome": nome, 
        "veiculo": {"marca": marca, "modelo": modelo, "ano": ano},
        "data": datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M"),
        "relatorio_ai": "Aguardando confirmação do pagamento...",
        "fotos_map": fotos_map,
        "pago": False
    }
    
    with open(f"{pasta}/dados.json", "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)
        
    return {"ok": True, "id": cliente_id}

@app.get("/check_status/{id}")
async def check_status(id: str):
    path = os.path.join(UPLOAD_DIR, id, "dados.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            dados = json.load(f)
        if dados.get("pago") == True:
            return {"status": "ready"}
    return {"status": "pending"}

@app.get("/avaliacoes", response_class=HTMLResponse)
def listar_avaliacoes():
    clientes = []
    if os.path.exists(UPLOAD_DIR):
        for pasta in os.listdir(UPLOAD_DIR):
            path = os.path.join(UPLOAD_DIR, pasta, "dados.json")
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    clientes.append((pasta, json.load(f)))
    clientes.reverse()
    html = "<html><body><h1>Dashboard</h1>"
    for id_, d in clientes:
        status = "PAGO" if d.get("pago") else "PENDENTE"
        html += f"<p>[{status}] {d.get('nome')} - <a href='/cliente/{id_}'>Abrir Laudo</a></p>"
    return HTMLResponse(html + "</body></html>")

@app.get("/cliente/{id}", response_class=HTMLResponse)
def ver_laudo_cliente(id: str):
    path = os.path.join(UPLOAD_DIR, id, "dados.json")
    if not os.path.exists(path): return HTMLResponse("Erro: Laudo não encontrado.")
    
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)
    
    texto = d.get("relatorio_ai", "")

    def extrair_secao_v2(prefixo, proximo, original):
        try:
            padrao = rf"{re.escape(prefixo)}(.*?)(?={re.escape(proximo)}|$)"
            match = re.search(padrao, original, re.DOTALL | re.IGNORECASE)
            if match:
                bloco_total = match.group(1).strip()
                sub_match = re.search(r"(?:Subtotal:|Sub:)\s*([\d\-]+\s*/\s*[\d\-]+)", bloco_total, re.IGNORECASE)
                sub_val = sub_match.group(1).replace(" ", "") if sub_match else "0/0"
                obs_match = re.search(r"OBS:\s*(.*?)(?=Subtotal:|Sub:|$)", bloco_total, re.DOTALL | re.IGNORECASE)
                obs_val = obs_match.group(1).strip() if obs_match and obs_match.group(1).strip() else "Sem observações específicas."
                res_limpo = re.sub(r"OBS:.*", "", bloco_total, flags=re.DOTALL | re.IGNORECASE)
                res_limpo = re.sub(r"(?:Subtotal|Sub):.*", "", res_limpo, flags=re.IGNORECASE)
                return res_limpo.strip(), sub_val, obs_val
            return "Dados não localizados.", "0/0", "N/A"
        except: return "Erro.", "0/0", "Erro"

    sec_ext, sub_ext, obs_ext = extrair_secao_v2("1- EXTERIOR", "2- INTERIOR", texto)
    sec_int, sub_int, obs_int = extrair_secao_v2("2- INTERIOR", "3- MECÂNICA", texto)
    sec_mec, sub_mec, obs_mec = extrair_secao_v2("3- MECÂNICA", "4- CONSERVAÇÃO", texto)
    sec_cons, sub_cons, obs_cons = extrair_secao_v2("4- CONSERVAÇÃO", "TOTAL:", texto)
    
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
    foto_capa = f"/uploads/{id}/frente.jpg" if "frente.jpg" in arquivos else ""
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
        .header h1 {{ font-family: 'Cinzel', serif; margin: 0; font-size: 42px; }}
        .topo-container {{ display: grid; grid-template-columns: 400px 1fr; gap: 20px; margin-bottom: 20px; }}
        .dados-proprietario {{ background: var(--bege-card); border-radius: 12px; padding: 15px; border: 1px solid #c0c5bd; }}
        .info-row {{ display: flex; align-items: center; gap: 15px; padding: 8px 0; border-bottom: 1px solid #d0d5cd; }}
        .foto-principal {{ border: 5px solid #fff; border-radius: 15px; overflow: hidden; height: 250px; }}
        .foto-principal img {{ width: 100%; height: 100%; object-fit: cover; }}
        .card-avaliacao {{ background: var(--bege-card); border-radius: 10px; margin-bottom: 15px; border: 1px solid #c0c5bd; overflow: hidden; }}
        .card-header {{ background: var(--verde-escuro); color: white; padding: 8px 15px; display: flex; justify-content: space-between; }}
        .card-body {{ display: grid; grid-template-columns: 1fr 200px; padding: 12px; gap: 15px; }}
        .obs-tecnica {{ font-size: 10px; background: #fff; padding: 8px; border-radius: 5px; border-left: 3px solid var(--verde-claro); }}
        .subtotal-box {{ grid-column: span 2; background: var(--verde-escuro); color: white; text-align: right; padding: 5px 15px; font-weight: bold; }}
        .sidebar-card {{ background: var(--bege-card); border: 1px solid #c0c5bd; border-radius: 10px; padding: 15px; margin-bottom: 15px; }}
        .score-grande {{ font-size: 48px; font-weight: 800; color: var(--verde-escuro); text-align: center; }}
        .veredito-tag {{ background: var(--verde-escuro); color: white; padding: 10px; text-align: center; border-radius: 8px; }}
        .mini-foto {{ aspect-ratio: 1; background-size: cover; background-position: center; border-radius: 4px; }}
        .foto-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 5px; }}
    </style>
</head>
<body>
<div class="laudo-folha">
    <div class="header"><h1>LAUDO TÉCNICO PERICIAL</h1><p>ORIGINALIDADE E ANTIGOMOBILISMO</p></div>
    <div class="topo-container">
        <div class="dados-proprietario">
            <div class="info-row"><b>Proprietário:</b> {d['nome']}</div>
            <div class="info-row"><b>Veículo:</b> {d['veiculo']['marca']} {d['veiculo']['modelo']}</div>
            <div class="info-row"><b>Ano:</b> {d['veiculo']['ano']}</div>
            <div class="info-row"><b>Data:</b> {d['data']}</div>
        </div>
        <div class="foto-principal"><img src="{foto_capa}"></div>
    </div>
    <div style="display: grid; grid-template-columns: 1fr 300px; gap: 20px;">
        <div>
            <div class="card-avaliacao"><div class="card-header">I. EXTERIOR</div><div class="card-body"><div>{sec_ext}</div><div class="obs-tecnica">{obs_ext}</div><div class="subtotal-box">Subtotal: {sub_ext}</div></div></div>
            <div class="card-avaliacao"><div class="card-header">II. INTERIOR</div><div class="card-body"><div>{sec_int}</div><div class="obs-tecnica">{obs_int}</div><div class="subtotal-box">Subtotal: {sub_int}</div></div></div>
            <div class="card-avaliacao"><div class="card-header">III. MECÂNICA</div><div class="card-body"><div>{sec_mec}</div><div class="obs-tecnica">{obs_mec}</div><div class="subtotal-box">Subtotal: {sub_mec}</div></div></div>
            <div class="card-avaliacao"><div class="card-header">IV. CONSERVAÇÃO</div><div class="card-body"><div>{sec_cons}</div><div class="obs-tecnica">{obs_cons}</div><div class="subtotal-box">Subtotal: {sub_cons}</div></div></div>
        </div>
        <div>
            <div class="sidebar-card"><div class="score-grande">{score}/100</div><div class="veredito-tag">{veredito}</div></div>
            <div class="sidebar-card"><b>Mercado:</b><br>Rápida: {v_rapida}<br>Particular: {v_part}<br>Placa Preta: {v_pos}</div>
            <div class="sidebar-card"><b>Fotos:</b><div class="foto-grid">{fotos_grid_html}</div></div>
        </div>
    </div>
</div>
</body>
</html>
"""