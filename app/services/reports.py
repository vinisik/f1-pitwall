import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch

# Define o caminho onde o arquivo será salvo 
DIRETORIO_PDFS = "relatorios_gerados"
if not os.path.exists(DIRETORIO_PDFS):
    os.makedirs(DIRETORIO_PDFS)

def _adicionar_cabecalho_com_logo(canvas, doc):
    """Garante a aplicação estrita do logo da equipe no topo de todas as páginas."""
    canvas.saveState()
    
    caminho_base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    logo_path = os.path.join(caminho_base, "frontend", "src", "assets", "logo.png")
    
    if os.path.exists(logo_path):
        canvas.drawImage(logo_path, 40, 780, width=120, height=40, preserveAspectRatio=True, mask='auto')
    else:
        canvas.setFont('Helvetica-Bold', 14)
        canvas.drawString(40, 800, "[ LOGO DA APLICAÇÃO AQUI ]")
        
    canvas.setLineWidth(1)
    canvas.line(40, 770, 550, 770) 
    canvas.restoreState()

def gerar_pdf_resumo_corrida(ano, gp, dados_resumo):
    """
    Gera um relatório em PDF com o resumo de uma corrida (classificação e estratégia).
    """
    nome_arquivo = f"Resumo_Corrida_{gp}_{ano}.pdf"
    caminho_completo = os.path.join(DIRETORIO_PDFS, nome_arquivo)
    
    # Configuração básica da página
    doc = SimpleDocTemplate(
        caminho_completo, 
        pagesize=A4, 
        rightMargin=30, 
        leftMargin=30, 
        topMargin=50, 
        bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    Story = []

    # Título do Documento
    Story.append(Paragraph(f"Resumo Oficial da Corrida - GP de {gp} ({ano})", styles['Title']))
    Story.append(Spacer(1, 0.3 * inch))

    # Preparação dos Dados da Tabela
    # Cabeçalho
    dados_tabela = [["Pos", "Piloto", "Grid", "Variação", "Histórico de Pneus (Stints)"]]
    
    for piloto in dados_resumo:
        # Formata a informação dos pneus de forma compacta
        # Exemplo: SOFT (15v) | HARD (40v)
        stints = " | ".join([f"{s.get('composto')} ({s.get('voltas')}v)" for s in piloto.get('stints', [])])
        
        # Formata a variação de posições (ex: +2 ou -1)
        var = piloto.get('saldo_posicoes', 0)
        var_str = f"+{var}" if var > 0 else str(var)
        
        dados_tabela.append([
            str(piloto.get('chegada', '')),
            str(piloto.get('piloto', '')),
            f"P{piloto.get('largada', '')}",
            var_str,
            stints
        ])

    # Estilização da Tabela
    col_widths = [0.5 * inch, 1.5 * inch, 0.6 * inch, 0.8 * inch, 3.5 * inch]
    tabela = Table(dados_tabela, colWidths=col_widths)
    
    estilo = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d2d30')), # Cinza Escuro
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        
        # Estilo das Linhas de Dados
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f5f5f5')), # Cinza Claro
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')), # Bordas
    ])
    
    # Aplica cores na coluna de variação 
    for i in range(1, len(dados_tabela)):
        try:
            val = int(dados_tabela[i][3])
            if val > 0:
                estilo.add('TEXTCOLOR', (3, i), (3, i), colors.HexColor('#39b54a')) # Verde
            elif val < 0:
                estilo.add('TEXTCOLOR', (3, i), (3, i), colors.HexColor('#e10600')) # Vermelho
        except ValueError:
            pass # Ignora se o valor não for um número

    tabela.setStyle(estilo)
    Story.append(tabela)

    # Nota de Rodapé
    Story.append(Spacer(1, 0.5 * inch))
    Story.append(Paragraph("Relatório gerado automaticamente pelo sistema de telemetria.", styles['Italic']))

    # Constrói o PDF e guarda no disco
    doc.build(Story)
    
    return caminho_completo

def gerar_pdf_estrategia(ano, gp, dados_resumo):
    if isinstance(dados_resumo, dict):
        piloto = dados_resumo.get("driver", "N/A")
        previsao = dados_resumo.get("prediction", {})
        acao = dados_resumo.get("action", "N/A")
        previsoes_voltas = previsao.get("previsao_proximas_voltas", [])
    else:
        piloto = "Grid_Completo"
        acao = "Análise do Pelotão"
        previsao = {}
        previsoes_voltas = []

    nome_arquivo = f"Estrategia_{piloto}_{gp}_{ano}.pdf"

    caminho_completo = os.path.join(DIRETORIO_PDFS, nome_arquivo)
    doc = SimpleDocTemplate(caminho_completo, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=100, bottomMargin=40)
    styles = getSampleStyleSheet()
    Story = []

    # Título e Resumo
    Story.append(Paragraph(f"Relatório Técnico de Estratégia - {piloto}", styles['Title']))
    Story.append(Spacer(1, 0.2 * inch))
    
    Story.append(Paragraph("<b>Recomendação Estratégica:</b>", styles['Heading2']))
    Story.append(Paragraph(acao, styles['Normal']))
    Story.append(Spacer(1, 0.3 * inch))

    # Tabela de Previsões de Machine Learning
    if previsoes_voltas:
        Story.append(Paragraph("Previsão de Ritmo (Próximas Voltas)", styles['Heading3']))
        Story.append(Spacer(1, 0.1 * inch))

        # Preparar dados para a tabela: Cabeçalho + Linhas
        dados_tabela = [["Sequência", "Tempo Estimado (s)"]]
        for i, tempo in enumerate(previsoes_voltas, 1):
            dados_tabela.append([f"Próxima +{i}", f"{tempo}s"])

        # Estilizar a Tabela
        tabela = Table(dados_tabela, colWidths=[2 * inch, 2 * inch])
        estilo = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.red), # Cabeçalho vermelho (F1 style)
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ])
        tabela.setStyle(estilo)
        Story.append(tabela)

    doc.build(Story, onFirstPage=_adicionar_cabecalho_com_logo, onLaterPages=_adicionar_cabecalho_com_logo)
    return caminho_completo

def gerar_pdf_telemetria(ano, gp, piloto, dados):
    """
    Gera um relatório PDF técnico utilizando os dados processados pela interface.
    Recebe ano, gp e piloto para nomeação e cabeçalho, e o dicionário 'dados' com a telemetria.
    """
    nome_arquivo = f"Telemetria_{piloto}_{gp}_{ano}.pdf"
    caminho_completo = os.path.join(DIRETORIO_PDFS, nome_arquivo)
    
    doc = SimpleDocTemplate(
        caminho_completo, 
        pagesize=A4, 
        rightMargin=40, 
        leftMargin=40, 
        topMargin=100, 
        bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    styles['Title'].textColor = colors.HexColor('#1e1e1e')
    styles['Heading2'].textColor = colors.HexColor('#454548')
    
    Story = []

    d1 = piloto
    t1 = dados.get("lap_time_1", 0)
    telemetry = dados.get("telemetry", [])

    # Cálculo de métricas baseadas no piloto solicitado
    speed_key = f"Speed_{d1}"
    # Se os dados vierem da função de comparação para um piloto só, 
    if speed_key not in telemetry[0] and f"{speed_key}_x" in telemetry[0]:
        speed_key = f"{speed_key}_x"

    velocidades = [t.get(speed_key) for t in telemetry if t.get(speed_key) is not None]
    max_speed = max(velocidades, default=0)
    avg_speed = round(sum(velocidades) / len(velocidades), 1) if velocidades else 0

    # Início do conteúdo do PDF
    Story.append(Paragraph("Relatório Técnico de Telemetria", styles['Title']))
    Story.append(Spacer(1, 0.1 * inch))
    Story.append(Paragraph(f"Evento: {gp} - Temporada {ano}", styles['Normal']))
    Story.append(Spacer(1, 0.2 * inch))
    
    Story.append(Paragraph(f"Análise de Desempenho: Piloto {d1}", styles['Heading2']))
    Story.append(Spacer(1, 0.1 * inch))

    # Tabela de Comparação de Desempenho
    dados_tabela = [
        ["Métrica", "Valor Detectado", "Unidade"],
        ["Tempo de Volta", f"{t1}", "segundos"],
        ["Velocidade Máxima", f"{max_speed}", "km/h"],
        ["Velocidade Média", f"{avg_speed}", "km/h"],
        ["Status da Volta", "Válida (QuickLap)", "-"]
    ]

    tabela = Table(dados_tabela, colWidths=[2.5 * inch, 2 * inch, 1.5 * inch])
    
    estilo = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d2d30')), # Cinza Escuro
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f5f5f5')), # Cinza bem claro
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#1e1e1e')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#454548'))
    ])
    
    tabela.setStyle(estilo)
    Story.append(tabela)
    
    Story.append(Spacer(1, 0.5 * inch))
    Story.append(Paragraph("Nota: Este relatório foi gerado automaticamente pelo motor de IA do F1 Pit Wall.", 
                 styles['Italic']))

    # Construção do documento
    doc.build(Story, onFirstPage=_adicionar_cabecalho_com_logo, onLaterPages=_adicionar_cabecalho_com_logo)
    
    return caminho_completo