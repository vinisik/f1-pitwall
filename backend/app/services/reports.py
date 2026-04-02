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

def gerar_pdf_estrategia(dados_corrida: dict, nome_arquivo: str = "relatorio_estrategia.pdf"):
    caminho_completo = os.path.join(DIRETORIO_PDFS, nome_arquivo)
    doc = SimpleDocTemplate(caminho_completo, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=100, bottomMargin=40)
    styles = getSampleStyleSheet()
    Story = []

    piloto = dados_corrida.get("driver", "N/A")
    previsao = dados_corrida.get("prediction", {})
    acao = dados_corrida.get("action", "N/A")
    previsoes_voltas = previsao.get("previsao_proximas_voltas", [])

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