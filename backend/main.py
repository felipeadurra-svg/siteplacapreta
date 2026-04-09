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


# 🧠 PROMPT ORIGINAL (INTACTO)
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


@app.get("/cliente/{id}", response_class=HTMLResponse)
def cliente(id: str):
    path = os.path.join(UPLOAD_DIR, id, "dados.json")
    if not os.path.exists(path): return HTMLResponse("Erro")

    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)

    texto = d.get("relatorio_ai", "")

    # Função para extrair a seção e formatar os itens e subtotais
    def processar_secao(chave_inicio, chave_fim, texto_completo):
        try:
            inicio = texto_completo.find(chave_inicio)
            if inicio == -1: return "Dados não disponíveis.", "00"
            
            parte = texto_completo[inicio:]
            fim = parte.find(chave_fim) if chave_fim in parte else len(parte)
            conteudo = parte[:fim].strip()

            # Extrai o subtotal (ex: 29 / 30) para colocar no distintivo do card
            sub_match = re.search(r"Subtotal:\s*(\d+\s*/\s*\d+)", conteudo, re.IGNORECASE)
            sub_valor = sub_match.group(1) if sub_match else "-- / --"

            # Formatação visual: coloca negrito antes dos dois pontos (ex: Pintura:)
            # E remove a linha do subtotal do corpo do texto para não repetir
            linhas = conteudo.split('\n')
            texto_limpo = []
            for l in linhas:
                if "Subtotal:" in l or chave_inicio in l: continue
                # Transforma "- Item: desc" em "• **Item:** desc"
                l = re.sub(r"^-?\s*([\w\s]+):", r"• **\1:**", l)
                texto_limpo.append(l)

            return "\n".join(texto_limpo).strip(), sub_valor
        except:
            return "Erro no processamento.", "00"

    # Extraindo conteúdo e subtotais de cada área
    ext_txt, ext_sub = processar_secao("I. 🚗 EXTERIOR", "II. 🪑 INTERIOR", texto)
    int_txt, int_sub = processar_secao("II. 🪑 INTERIOR", "III. 🧰 MECÂNICA", texto)
    mec_txt, mec_sub = processar_secao("III. 🧰 MECÂNICA", "IV. 🧼 CONSERVAÇÃO", texto)
    cons_txt, cons_sub = processar_secao("IV. 🧼 CONSERVAÇÃO", "📊 RESULTADO FINAL", texto)
    
    # Recomendações (sem subtotal)
    rec_txt = processar_secao("🧠 RECOMENDAÇÕES", "✍️ ASSINATURA", texto)

    # ... (Resto da lógica de score, mercado e fotos permanece a mesma)

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            /* Adicione este estilo para o Subtotal dentro do Card */
            .subtotal-badge {{
                float: right;
                background: var(--dark);
                color: var(--gold);
                padding: 5px 15px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 16px;
                margin-top: -5px;
            }}
            .card-body {{ padding: 20px; }}
            .card-body b {{ color: var(--dark); }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="card">
                <div class="card-header">
                    I. EXTERIOR E CARROCERIA
                    <span class="subtotal-badge">{ext_sub}</span>
                </div>
                <div class="card-body">
                    <pre style="white-space: pre-wrap;">{ext_txt}</pre>
                </div>
            </div>
            
            </div>
    </body>
    </html>
    """