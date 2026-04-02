import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
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

    # Extração de dados dinâmicos
    piloto = dados_corrida.get("driver", "Desconhecido")
    previsao = dados_corrida.get("prediction", {})
    acao = dados_corrida.get("action", "Sem recomendação")
    
    composto = previsao.get("composto_analisado", "N/A")
    degradacao = previsao.get("degradacao_segundos_por_volta", 0)

    # Injeção no Layout
    Story.append(Paragraph(f"Relatório de Estratégia: Piloto {piloto}", styles['Title']))
    Story.append(Spacer(1, 0.2 * inch))
    
    Story.append(Paragraph("Decisão Estratégica", styles['Heading2']))
    Story.append(Paragraph(f"<b>Recomendação do Motor Preditivo:</b> {acao}", styles['Normal']))
    Story.append(Spacer(1, 0.2 * inch))
    
    Story.append(Paragraph("Métricas de Desempenho", styles['Heading3']))
    Story.append(Paragraph(f"- Composto Analisado: {composto}", styles['Normal']))
    Story.append(Paragraph(f"- Degradação Estimada: +{degradacao} segundos por volta", styles['Normal']))
    
    doc.build(Story, onFirstPage=_adicionar_cabecalho_com_logo, onLaterPages=_adicionar_cabecalho_com_logo)
    
    return caminho_completo