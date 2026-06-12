import os
import numpy as np
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from datetime import datetime

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
        canvas.drawString(40, 800, "[ F1 Pit Wall ]")
        
    canvas.setLineWidth(1)
    canvas.line(40, 770, 550, 770) 
    canvas.restoreState()

def gerar_pdf_resumo_corrida(ano, gp, dados):
    """
    Gera um relatório em PDF com o resumo completo de uma corrida .
    """
    os.makedirs("Relatórios", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    caminho_arquivo = os.path.join("Relatórios", f"Relatorio_{gp}_{ano}_{timestamp}.pdf")

    def aplicar_estilo(ax, titulo, xlabel, ylabel):
        ax.set_facecolor('#1a1a1a')
        ax.tick_params(colors='#aaaaaa', labelsize=9)
        for spine in ax.spines.values(): spine.set_edgecolor('#454548')
        ax.grid(color='#454548', linestyle='--', linewidth=0.5, alpha=0.5)
        ax.set_title(titulo, color='#f5f5f5', pad=15, fontsize=14, weight='bold')
        if xlabel: ax.set_xlabel(xlabel, color='#aaaaaa', fontsize=11)
        if ylabel: ax.set_ylabel(ylabel, color='#aaaaaa', fontsize=11)

    with PdfPages(caminho_arquivo) as pdf:
        
        # Tabela Resumo e Stints
        fig_tab, ax_tab = plt.subplots(figsize=(11, 8.5), facecolor='#ffffff')
        ax_tab.axis('off')
        ax_tab.set_title(f"RELATÓRIO DE CORRIDA - GP {str(gp).upper()} ({ano})", color='#e10600', fontsize=18, weight='bold', pad=20)

        col_labels = ['Pos', 'Piloto', 'Grid', 'Variação', 'Estratégia de Pneus (Stints)']
        table_data = []
        
        # Abreviação dos compostos de pneus para a tabela
        def abrev_pneu(comp):
            mapa = {'SOFT': 'S', 'MEDIUM': 'M', 'HARD': 'H', 'INTERMEDIATE': 'I', 'WET': 'W'}
            return mapa.get(comp.upper(), comp[:1])
        
        for row in dados.get('tabela', []):
            stints_str = " -> ".join([f"{s['voltas']}v {abrev_pneu(s['composto'])}" for s in row.get('stints', [])])
            var = row.get('saldo_posicoes', 0)
            var_str = f"+{var}" if var > 0 else str(var)
            
            table_data.append([
                str(row.get('chegada', '')),
                str(row.get('piloto', '')),
                f"P{row.get('largada', '')}",
                var_str,
                stints_str
            ])

        if table_data:
            table = ax_tab.table(cellText=table_data, colLabels=col_labels, loc='center', cellLoc='center')
            table.auto_set_font_size(False)
            table.set_fontsize(10)
            table.scale(1, 1.8)
            
            table.auto_set_column_width(col=list(range(len(col_labels))))

            # Estiliza a tabela com o fundo da página branco
            for (i, j), cell in table.get_celld().items():
                if i == 0:
                    cell.set_text_props(weight='bold', color='white')
                    cell.set_facecolor('#e10600')
                    cell.set_edgecolor('#cccccc')
                else:
                    peso_fonte = 'bold' if j == 1 else 'normal'
                    cell.set_text_props(color='#000000', weight=peso_fonte)
                    cell.set_facecolor('#ffffff')
                    cell.set_edgecolor('#cccccc')

        pdf.savefig(fig_tab, facecolor=fig_tab.get_facecolor())
        plt.close(fig_tab)

        # Gráfico de Evolução de Posições
        fig_pos, ax_pos = plt.subplots(figsize=(11, 8.5), facecolor='#1a1a1a')
        aplicar_estilo(ax_pos, "Evolução de Posições ao Longo da Corrida", "Voltas", "Posição")
        cores = plt.get_cmap('tab20')(range(20))
        
        for i, (piloto, pdados) in enumerate(dados.get('posicoes', {}).items()):
            ax_pos.plot(pdados['laps'], pdados['pos'], label=piloto, linewidth=2, color=cores[i % 20])
            
        ax_pos.invert_yaxis()
        ax_pos.set_yticks(range(1, 21))
        ax_pos.legend(loc='center left', bbox_to_anchor=(1.02, 0.5), facecolor='#1a1a1a', edgecolor='#454548', labelcolor='white')
        fig_pos.tight_layout(rect=(0, 0, 0.85, 1))
        
        pdf.savefig(fig_pos, facecolor=fig_pos.get_facecolor())
        plt.close(fig_pos)

        # Gráfico de Ritmo de Corrida 
        fig_pace, ax_pace = plt.subplots(figsize=(11, 8.5), facecolor='#1a1a1a')
        aplicar_estilo(ax_pace, "Ritmo de Corrida (Distribuição de Voltas Limpas)", "Pilotos", "Tempo da Volta (segundos)")
        
        pace_labels = []
        pace_data = []
        for row in dados.get('tabela', []):
            drv = row['piloto']
            if drv in dados.get('pace', {}) and len(dados['pace'][drv]) > 0:
                pace_labels.append(drv)
                pace_data.append(dados['pace'][drv])
                
        if pace_data:
            ax_pace.boxplot(pace_data, patch_artist=True, notch=False, vert=True,
                            boxprops=dict(facecolor='#00aeef', color='#ffffff', alpha=0.6),
                            capprops=dict(color='#ffffff'), whiskerprops=dict(color='#ffffff'),
                            flierprops=dict(marker='o', color='#e10600', markersize=3, alpha=0.5),
                            medianprops=dict(color='#e10600', linewidth=2))
            ax_pace.set_xticks(range(1, len(pace_labels) + 1))
            ax_pace.set_xticklabels(pace_labels, rotation=45, ha='right', color='white')
        
        fig_pace.tight_layout()
        pdf.savefig(fig_pace, facecolor=fig_pace.get_facecolor())
        plt.close(fig_pace)

        # Gráfico de Pit Stops
        fig_pit, ax_pit = plt.subplots(figsize=(11, 8.5), facecolor='#1a1a1a')
        aplicar_estilo(ax_pit, "Tempos Gastos no Pit Lane (In/Out)", "Volta da Corrida", "Duração (segundos)")
        
        pitstops = dados.get('pitstops', [])
        if pitstops:
            v_pit = [p['volta'] for p in pitstops]
            t_pit = [p['tempo'] for p in pitstops]
            p_pit = [p['piloto'] for p in pitstops]
            
            ax_pit.scatter(v_pit, t_pit, c='#e2d014', s=120, edgecolors='#ffffff', alpha=0.8)
            for i, txt in enumerate(p_pit):
                ax_pit.annotate(txt, (v_pit[i], t_pit[i]), xytext=(0, 10), textcoords='offset points', ha='center', color='white', fontsize=8, weight='bold')
        else:
            ax_pit.text(0.5, 0.5, "Nenhum Pit Stop Registrado / Dados Indisponíveis", color='white', ha='center', fontsize=14, transform=ax_pit.transAxes)
            
        fig_pit.tight_layout()
        pdf.savefig(fig_pit, facecolor=fig_pit.get_facecolor())
        plt.close(fig_pit)

        # Gráfico de Speed Trap 
        fig_spd, ax_spd = plt.subplots(figsize=(11, 8.5), facecolor='#1a1a1a')
        aplicar_estilo(ax_spd, "Speed Trap", "Velocidade (km/h)", "Pilotos")
        
        speedtrap_data = dados.get('speedtrap', {})
        spd_drivers = [d for d, s in speedtrap_data.items() if s > 0]
        spd_vals = [speedtrap_data[d] for d in spd_drivers]
        
        if spd_vals:
            spd_sorted = sorted(zip(spd_drivers, spd_vals), key=lambda x: x[1])
            y_pos = np.arange(len(spd_sorted))
            bars = ax_spd.barh(y_pos, [x[1] for x in spd_sorted], color='#e10600', height=0.6)
            
            ax_spd.set_yticks(y_pos)
            ax_spd.set_yticklabels([x[0] for x in spd_sorted])
            ax_spd.set_xlim(min(spd_vals) - 15, max(spd_vals) + 10) 
            
            for bar in bars:
                ax_spd.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2, f"{bar.get_width():.1f}", 
                            va='center', color='white', fontsize=9, weight='bold')

        fig_spd.tight_layout()
        pdf.savefig(fig_spd, facecolor=fig_spd.get_facecolor())
        plt.close(fig_spd)

    return caminho_arquivo

def gerar_pdf_estrategia(ano, gp, dados_resumo):
    """
    Gera o relatório em PDF com a estratégia e a previsão.
    """
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
            ('BACKGROUND', (0, 0), (-1, 0), colors.red), 
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
    # Se os dados vierem da função de comparação para um piloto só 
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
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d2d30')), 
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f5f5f5')), 
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