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
    """
    Função interna de callback que o ReportLab chama a cada nova página gerada.
    Garante o logo no topo de todas as páginas.
    """
    canvas.saveState()
    
    # Navega até o diretório raiz do projeto para encontrar o logo 
    caminho_base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    logo_path = os.path.join(caminho_base, "frontend", "src", "assets", "logo.png")
    
    # Se a imagem física do logo existir, ele a renderiza.  
    if os.path.exists(logo_path):
        # Caso contrário, usa um texto de marcação
        canvas.drawImage(logo_path, 40, 780, width=120, height=40, preserveAspectRatio=True, mask='auto')
    else:
        canvas.setFont('Helvetica-Bold', 14)
        canvas.drawString(40, 800, "[ LOGO DA APLICAÇÃO AQUI ]")
        
    canvas.setLineWidth(1)
    canvas.line(40, 770, 550, 770) 
    canvas.restoreState()

def gerar_pdf_estrategia(dados_corrida: dict, nome_arquivo: str = "relatorio_estrategia.pdf"):
    """
    Constrói a estrutura do documento.
    """
    caminho_completo = os.path.join(DIRETORIO_PDFS, nome_arquivo)
    
    # Configura o documento com margem superior maior para acomodar o logo
    doc = SimpleDocTemplate(
        caminho_completo, 
        pagesize=A4, 
        rightMargin=40, 
        leftMargin=40, 
        topMargin=100, 
        bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    Story = []

    # Construindo o conteúdo de exemplo
    Story.append(Paragraph(f"Relatório de Estratégia Pós-Corrida", styles['Title']))
    Story.append(Spacer(1, 0.2 * inch))
    
    Story.append(Paragraph("Resumo da Sessão", styles['Heading2']))
    Story.append(Paragraph("A análise preditiva indicou a necessidade de parada na volta analisada para evitar a perda de rendimento e o undercut dos adversários diretos.", styles['Normal']))
    Story.append(Spacer(1, 0.2 * inch))
    
    Story.append(Paragraph("Métricas Analisadas:", styles['Heading3']))
    Story.append(Paragraph("- Degradação de compostos Macios/Duros", styles['Normal']))
    Story.append(Paragraph("- Estimativa de tráfego na saída do pit lane", styles['Normal']))
    
    doc.build(Story, onFirstPage=_adicionar_cabecalho_com_logo, onLaterPages=_adicionar_cabecalho_com_logo)
    
    return caminho_completo