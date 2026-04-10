@app.get("/cliente/{id}", response_class=HTMLResponse)
def cliente(id: str):
    path = os.path.join(UPLOAD_DIR, id, "dados.json")
    if not os.path.exists(path): return HTMLResponse("Erro: Laudo não encontrado.")
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)
    
    texto = d.get("relatorio_ai", "")

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

    # --- LÓGICA DE FOTOS CORRIGIDA ---
    fotos_dir = os.path.join(UPLOAD_DIR, id)
    arquivos = sorted([f for f in os.listdir(fotos_dir) if f.endswith(".jpg")])
    
    # Busca especificamente pela frente.jpg ou a primeira da lista
    if "frente.jpg" in arquivos:
        foto_capa = f"/uploads/{id}/frente.jpg"
    elif arquivos:
        foto_capa = f"/uploads/{id}/{arquivos}"
    else:
        foto_capa = "https://via.placeholder.com/800x400?text=Sem+Foto"

    fotos_grid_html = "".join([f'<div class="mini-foto" style="background-image:url(\'/uploads/{id}/{f}\'); background-size:cover; background-position:center;"></div>' for f in arquivos])
    # ---------------------------------

    return f"""
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>Laudo Técnico Pericial - {id}</title>
    <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&family=Montserrat:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{ --verde-escuro: #062b21; --verde-medio: #0b3b2e; --verde-claro: #1f6b4a; --bege-fundo: #e3e8e1; --bege-card: #f1f4ef; --dourado: #c8a96a; }}
        * {{ box-sizing: border-box; }}
        body {{ background-color: #222; font-family: 'Montserrat', sans-serif; margin: 0; padding: 20px; display: flex; justify-content: center; }}
        .laudo-folha {{ width: 1000px; background-color: var(--bege-fundo); padding: 30px; border-radius: 5px; position: relative; box-shadow: 0 0 30px rgba(0,0,0,0.5); }}
        .header {{ background: linear-gradient(135deg, var(--verde-escuro), var(--verde-claro)); color: white; padding: 20px; border-radius: 10px; text-align: center; border-bottom: 4px solid var(--dourado); margin-bottom: 20px; }}
        .header h1 {{ font-family: 'Cinzel', serif; margin: 0; font-size: 42px; letter-spacing: 2px; }}
        .header p {{ margin: 5px 0 0; font-size: 16px; letter-spacing: 4px; font-weight: 300; }}
        .topo-container {{ display: grid; grid-template-columns: 400px 1fr; gap: 20px; margin-bottom: 20px; }}
        .dados-proprietario {{ background: var(--bege-card); border: 1px solid #c0c5bd; border-radius: 12px; padding: 15px; }}
        .info-row {{ display: flex; align-items: center; gap: 15px; padding: 10px 0; border-bottom: 1px solid #d0d5cd; }}
        .info-row:last-child {{ border: none; }}
        .info-row .icon {{ font-size: 24px; width: 30px; text-align: center; }}
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