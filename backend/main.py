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


@app.get("/cliente/{id}", response_class=HTMLResponse)
def cliente(id: str):
    path = os.path.join(UPLOAD_DIR, id, "dados.json")
    if not os.path.exists(path): return HTMLResponse("Erro: Laudo não encontrado.")

    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)

    texto = d.get("relatorio_ai", "")

    # Função ultra-flexível para capturar as seções pelos algarismos romanos
    def capturar_secao(romano_atual, proximo_romano, texto_completo):
        try:
            # Busca o bloco entre um romano e outro (ex: I. até II.)
            padrao = f"{romano_atual}\\..*?(?={proximo_romano}\\.|$)"
            match = re.search(padrao, texto_completo, re.DOTALL | re.IGNORECASE)
            if not match: return "Informação não detectada.", "00/00"
            
            bloco = match.group(0)
            
            # 1. Extrai o Subtotal (procura algo como 29 / 30 ou 29/30)
            sub_match = re.search(r"(\d+\s*/\s*\d+)", bloco)
            sub_valor = sub_match.group(1) if sub_match else "--/--"
            
            # 2. Limpa o texto: Remove o título da seção e o subtotal do corpo
            linhas = bloco.split('\n')
            corpo_limpo = []
            for linha in linhas:
                # Pula a linha que contém o algarismo romano (título) ou a palavra Subtotal
                if re.search(f"^{romano_atual}\\.", linha) or "Subtotal" in linha:
                    continue
                
                # Formatação: Coloca negrito no que vem antes de ":"
                if ":" in linha:
                    linha = re.sub(r"([\w\sáéíóúâêîôûãõç]+):", r"**\1:**", linha)
                
                if linha.strip(): corpo_limpo.append(linha.strip())
            
            return "\n".join(corpo_limpo), sub_valor
        except:
            return "Erro ao processar seção.", "00"

    # Fatiamento das seções
    ext_txt, ext_pts = capturar_secao("I", "II", texto)
    int_txt, int_pts = capturar_secao("II", "III", texto)
    mec_txt, mec_pts = capturar_secao("III", "IV", texto)
    cons_txt, cons_pts = capturar_secao("IV", "📊 RESULTADO", texto)
    
    # Recomendações (fica entre Recomendações e Assinatura)
    rec_txt = ""
    rec_match = re.search(r"RECOMENDAÇÕES(.*?)(?=✍️ ASSINATURA|$)", texto, re.DOTALL | re.IGNORECASE)
    if rec_match:
        rec_txt = rec_match.group(1).strip()

    # Score e Mercado
    score_search = re.search(r"TOTAL:\s*(\d+)", texto)
    score = score_search.group(1) if score_search else "00"
    
    def buscar_valor_mercado(label):
        m = re.search(f"{label}:?\\s*(.*)", texto, re.IGNORECASE)
        return m.group(1).split('\n').strip() if m else "---"

    v_rapida = buscar_valor_mercado("Venda rápida")
    v_part = buscar_valor_mercado("Mercado particular")
    v_pos = buscar_valor_mercado("Pós placa preta")

    # Fotos
    fotos_dir = os.path.join(UPLOAD_DIR, id)
    arquivos = sorted([f for f in os.listdir(fotos_dir) if f.endswith(".jpg")])
    foto_capa = f"/uploads/{id}/frente.jpg" if "frente.jpg" in arquivos else f"/uploads/{id}/{arquivos}" if arquivos else ""
    fotos_html = "".join([f'<div class="img-mini" style="background-image:url(\'/uploads/{id}/{f}\')"></div>' for f in arquivos])

    return f"""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@700&family=Montserrat:wght@300;400;700&display=swap" rel="stylesheet">
        <style>
            :root {{ --dark: #052e22; --gold: #b59a5d; --bg: #e6e2d8; --white: #ffffff; }}
            body {{ font-family: 'Montserrat', sans-serif; background: var(--bg); margin: 0; padding: 20px; }}
            .container {{ width: 1000px; margin: auto; display: grid; grid-template-columns: 1.8fr 1fr; gap: 20px; }}
            
            .header {{ grid-column: 1/-1; background: var(--dark); color: white; padding: 25px; border-radius: 8px; border-bottom: 5px solid var(--gold); display: flex; justify-content: space-between; align-items: center; }}
            .header h1 {{ font-family: 'Cinzel', serif; margin: 0; font-size: 28px; }}

            .card {{ background: var(--white); border-radius: 8px; margin-bottom: 15px; border: 1px solid #ddd; overflow: hidden; }}
            .card-header {{ background: var(--dark); color: white; padding: 12px 15px; font-weight: bold; font-size: 13px; display: flex; justify-content: space-between; align-items: center; }}
            .pts-badge {{ background: var(--gold); color: var(--dark); padding: 2px 10px; border-radius: 4px; font-size: 14px; font-weight: 800; }}
            .card-body {{ padding: 15px; font-size: 13px; line-height: 1.6; }}
            
            .score-box {{ background: var(--white); border: 3px solid var(--gold); border-radius: 8px; padding: 20px; text-align: center; }}
            .score-num {{ font-size: 55px; font-weight: 800; color: var(--dark); }}
            
            .mercado-item {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px dashed #ccc; font-size: 12px; }}
            .photo-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 5px; }}
            .img-mini {{ height: 85px; background-size: cover; background-position: center; border-radius: 4px; }}
            
            .main-img {{ height: 250px; background: url('{foto_capa}') center/cover; border-radius: 8px; margin-bottom: 15px; border: 1px solid #ccc; }}
            pre {{ white-space: pre-wrap; font-family: inherit; margin: 0; }}
            strong {{ color: var(--dark); }}
        </style>
    </head>
    <body>
        <div class="container">
            <header class="header">
                <div><h1>LAUDO TÉCNICO PERICIAL</h1><span>ORIGINALIDADE E ANTIGOMOBILISMO</span></div>
                <div style="text-align:right">ID: {id}<br>{d['data']}</div>
            </header>

            <div class="left">
                <div class="card">
                    <div class="card-header">I. EXTERIOR E CARROCERIA <span class="pts-badge">{ext_pts}</span></div>
                    <div class="card-body"><pre>{ext_txt}</pre></div>
                </div>
                <div class="card">
                    <div class="card-header">II. INTERIOR E TAPEÇARIA <span class="pts-badge">{int_pts}</span></div>
                    <div class="card-body"><pre>{int_txt}</pre></div>
                </div>
                <div class="card">
                    <div class="card-header">III. MECÂNICA VISUAL <span class="pts-badge">{mec_pts}</span></div>
                    <div class="card-body"><pre>{mec_txt}</pre></div>
                </div>
                <div class="card">
                    <div class="card-header">IV. CONSERVAÇÃO GERAL <span class="pts-badge">{cons_pts}</span></div>
                    <div class="card-body"><pre>{cons_txt}</pre></div>
                </div>
                <div class="card" style="border-left: 5px solid var(--dark);">
                    <div class="card-header">🧠 RECOMENDAÇÕES TÉCNICAS</div>
                    <div class="card-body"><pre>{rec_txt}</pre></div>
                </div>
            </div>

            <div class="right">
                <div class="main-img"></div>
                <div class="score-box">
                    <div style="font-weight:bold; color:var(--gold)">PONTUAÇÃO FINAL</div>
                    <div class="score-num">{score}</div>
                    <div style="background:var(--dark); color:white; padding:10px; border-radius:4px; font-weight:bold;">
                        {"APROVADO" if int(score) >= 80 else "EM ANÁLISE"}
                    </div>
                </div>
                <br>
                <div class="card">
                    <div class="card-header">💰 ANÁLISE DE MERCADO</div>
                    <div class="card-body">
                        <div class="mercado-item"><span>Venda Rápida:</span> <b>{v_rapida}</b></div>
                        <div class="mercado-item"><span>Particular:</span> <b>{v_part}</b></div>
                        <div class="mercado-item"><span>Pós Placa:</span> <b>{v_pos}</b></div>
                    </div>
                </div>
                <div class="card">
                    <div class="card-header">📷 REGISTRO FOTOGRÁFICO</div>
                    <div class="card-body"><div class="photo-grid">{fotos_html}</div></div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """