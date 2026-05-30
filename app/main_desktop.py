import os
import sys
import numpy as np
from PySide6.QtWidgets import QApplication, QDialog, QMainWindow, QTextEdit, QWidget, QVBoxLayout, QTabWidget, QTableWidgetItem, QLabel, QHBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.gridspec import GridSpec
from app.ui.tabs import SummaryTabUI, TelemetryTabUI, StrategyPredictionUI, get_tire_style
from app.workers import SingleTelemetryWorker, TelemetryWorker, StrategyWorker, SummaryWorker, FuturePredictionWorker
from app.services.reports import gerar_pdf_estrategia, gerar_pdf_telemetria, gerar_pdf_resumo_corrida

class TerminalDialog(QDialog):
    def __init__(self, parent=None, title="Terminal de Engenharia"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(700, 450)
        self.setStyleSheet("""
            QDialog { background-color: #050505; border: 1px solid #27272a; }
            QTextEdit { 
                background-color: #050505; 
                color: #2ecc71; 
                font-family: 'Consolas', 'Courier New', monospace; 
                font-size: 13px;
                border: none;
                padding: 10px;
            }
            QScrollBar:vertical { background: #050505; width: 10px; }
            QScrollBar::handle:vertical { background: #27272a; border-radius: 5px; }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.terminal = QTextEdit()
        self.terminal.setReadOnly(True)
        layout.addWidget(self.terminal)

    def log(self, message):
        self.terminal.append(f"> {message}")
        scrollbar = self.terminal.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

class PitWallApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("F1 Pit Wall - Engenharia")
        self.resize(1300, 850)
        self.setMinimumSize(1000, 700)

        # Cores Padrão para os Gráficos
        self.color_d1 = "#e10600" 
        self.color_d2 = "#00aeef" 
        
        # Variáveis de controle de gráficos
        self.ind_canvas = None
        self.comp_canvas = None
        self.live_canvas = None
        self.oracle_canvas = None

        self.setup_ui()
        self.apply_theme()

    def setup_ui(self):
        # Container Central e Layout
        central_widget = QWidget()
        central_widget.setObjectName("central_widget")
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("MainTabs")
        main_layout.addWidget(self.tabs)

        self.ui_summary = SummaryTabUI()
        self.ui_summary.setObjectName("app_tab")
        
        self.ui_telemetry = TelemetryTabUI()
        self.ui_telemetry.setObjectName("app_tab")
        
        self.ui_prediction = StrategyPredictionUI()
        self.ui_prediction.setObjectName("app_tab")

        self.tabs.addTab(self.ui_summary, "Resumo da Corrida")
        self.tabs.addTab(self.ui_telemetry, "Análise de Telemetria")
        self.tabs.addTab(self.ui_prediction, "Estratégia e Previsões")

        # Conectando as ações
        self.conectar_sinais()
        self.tabs.setCurrentIndex(2)

    def conectar_sinais(self):
        """ Conecta os botões da View com as Funções lógicas do Controlador """        
        self.ui_summary.btn_summary.clicked.connect(self.iniciar_resumo)
        self.ui_summary.btn_export_sum.clicked.connect(self.exportar_pdf_resumo)
        
        self.ui_telemetry.btn_ind.clicked.connect(self.iniciar_telemetria_ind)
        self.ui_telemetry.btn_export_tel.clicked.connect(self.exportar_pdf_telemetria)
        self.ui_telemetry.btn_comp.clicked.connect(self.iniciar_telemetria_comp)
        
        self.ui_prediction.btn_predict.clicked.connect(self.iniciar_previsao_futura)
        self.ui_prediction.btn_live.clicked.connect(self.iniciar_estrategia)
        
        self.ui_prediction.btn_logs_oracle.clicked.connect(self.mostrar_log_oracle)
        self.ui_prediction.btn_logs_live.clicked.connect(self.mostrar_log_live)

    def mostrar_log_oracle(self):
        if not hasattr(self, 'janela_log_oracle'):
            self.janela_log_oracle = TerminalDialog(self, "Terminal - Previsão de Corrida")
            if hasattr(self, 'worker_oracle'):
                log_signal = getattr(self.worker_oracle, 'log_msg', None)
                if log_signal is not None:
                    log_signal.connect(self.janela_log_oracle.log)
        
        self.janela_log_oracle.show()

    def mostrar_log_live(self):
        if not hasattr(self, 'janela_log_live'):
            self.janela_log_live = TerminalDialog(self, "Terminal - Previsão de Estratégia")
            if hasattr(self, 'worker_strategy'):
                log_signal = getattr(self.worker_strategy, 'log_msg', None)
                if log_signal is not None:
                    log_signal.connect(self.janela_log_live.log)
        self.janela_log_live.show()


    # UTILS
    def mostrar_erro_aba(self, label, botao, mensagem):
        botao.setEnabled(True)
        label.setText(f"Erro: {mensagem}")
        label.setStyleSheet("color: #e10600;")


    # ABA DE RESUMO
    def iniciar_resumo(self):
        self.ui_summary.btn_summary.setEnabled(False)
        self.ui_summary.sum_status.setText("Buscando dados...")
        
        ano = int(self.ui_summary.sum_year.text())
        gp = self.ui_summary.sum_gp.text()
        
        self.worker_summary = SummaryWorker(ano, gp)
        self.worker_summary.success.connect(self.atualizar_resumo)
        self.worker_summary.error.connect(lambda e: self.mostrar_erro_aba(self.ui_summary.sum_status, self.ui_summary.btn_summary, e))
        self.worker_summary.start()

    def atualizar_resumo(self, resultados):
        self.ultimos_dados_resumo = resultados
        self.ui_summary.btn_summary.setEnabled(True)
        self.ui_summary.btn_export_sum.setEnabled(True) 
        self.ui_summary.sum_status.setText("Grid atualizado!")
        
        tabela = self.ui_summary.table
        tabela.setRowCount(0) 
        
        for i, row in enumerate(resultados):
            tabela.insertRow(i)
            
            item_pos = QTableWidgetItem(str(row.get('chegada', '')))
            item_pos.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            tabela.setItem(i, 0, item_pos)
            
            item_piloto = QTableWidgetItem(str(row.get('piloto', '')))
            item_piloto.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            tabela.setItem(i, 1, item_piloto)
            
            item_grid = QTableWidgetItem(f"P{row.get('largada', '')}")
            item_grid.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            tabela.setItem(i, 2, item_grid)
            
            var = row.get('saldo_posicoes', 0)
            var_text = f"+{var}" if var > 0 else str(var)
            var_item = QTableWidgetItem(var_text)
            var_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if var > 0: var_item.setForeground(QColor("#39b54a"))
            elif var < 0: var_item.setForeground(QColor("#ff4c4c"))
            tabela.setItem(i, 3, var_item)
            
            stints_widget = QWidget()
            stints_layout = QHBoxLayout(stints_widget)
            stints_layout.setContentsMargins(10, 2, 10, 2)
            stints_layout.setSpacing(8)
            stints_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            
            for stint in row.get('stints', []):
                composto = stint.get('composto', 'UNKNOWN')
                voltas = stint.get('voltas', 0)
                estilo = get_tire_style(composto)
                
                lbl_pneu = QLabel(f" {voltas}v ")
                lbl_pneu.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lbl_pneu.setStyleSheet(f"""
                    background-color: {estilo['bg']}; 
                    color: {estilo['fg']}; 
                    border-radius: 12px; 
                    padding: 4px 8px;
                    font-weight: bold;
                    font-size: 11px;
                """)
                stints_layout.addWidget(lbl_pneu)
                
            tabela.setCellWidget(i, 4, stints_widget)

    def exportar_pdf_resumo(self):
        try:
            if not hasattr(self, 'ultimos_dados_resumo'):
                self.ui_summary.sum_status.setText("Erro: Primeiro clique em 'Gerar Resumo'")
                self.ui_summary.sum_status.setStyleSheet("color: #e10600;")
                return

            ano = int(self.ui_summary.sum_year.text())
            gp = self.ui_summary.sum_gp.text()
            
            caminho = gerar_pdf_resumo_corrida(ano, gp, self.ultimos_dados_resumo)
            
            self.ui_summary.sum_status.setText(f"PDF salvo: {os.path.basename(caminho)}")
            self.ui_summary.sum_status.setStyleSheet("color: #2ecc71;")
            
        except Exception as e:
            self.ui_summary.sum_status.setText(f"Erro na exportação: {str(e)}")
            self.ui_summary.sum_status.setStyleSheet("color: #e10600;")


    # TELEMETRIA INDIVIDUAL
    def iniciar_telemetria_ind(self):
        self.ui_telemetry.btn_ind.setEnabled(False)
        self.ui_telemetry.ind_status.setText("Extraindo sensores do carro...")
        self.ui_telemetry.ind_status.setStyleSheet("color: #00aeef;")
        
        y = int(self.ui_telemetry.ind_year.text())
        gp = self.ui_telemetry.ind_gp.text()
        d1 = self.ui_telemetry.ind_d1.text().upper()
        
        self.worker_ind = SingleTelemetryWorker(y, gp, d1)
        self.worker_ind.success.connect(self.atualizar_telemetria_ind)
        self.worker_ind.error.connect(lambda e: self.mostrar_erro_aba(self.ui_telemetry.ind_status, self.ui_telemetry.btn_ind, e))
        self.worker_ind.start()

    def atualizar_telemetria_ind(self, dados, d1):
        self.ui_telemetry.btn_ind.setEnabled(True)
        self.ui_telemetry.ind_status.setText(f"Telemetria de {d1} carregada. Tempo de Volta: {dados.get('lap_time_1', 'N/A')}s")
        self.ui_telemetry.ind_status.setStyleSheet("color: #2ecc71;")
        self.ui_telemetry.btn_export_tel.setEnabled(True)
        
        self.ultimos_dados_ind = dados

        if self.ind_canvas:
            self.ui_telemetry.ind_chart_layout.removeWidget(self.ind_canvas)
            self.ind_canvas.deleteLater()
            plt.close('all')

        telemetry = dados.get('telemetry', [])
        valid_rows = [r for r in telemetry if r['Distance'] is not None]
        
        def get_val(row, key):
            if key in row and row[key] is not None: return row[key]
            elif f"{key}_x" in row and row[f"{key}_x"] is not None: return row[f"{key}_x"]
            return 0

        dist = np.array([r['Distance'] for r in valid_rows])
        s1 = [get_val(r, f'Speed_{d1}') for r in valid_rows]
        thr1 = [get_val(r, f'Throttle_{d1}') for r in valid_rows]
        brk1 = [get_val(r, f'Brake_{d1}') for r in valid_rows]
        gr1 = [get_val(r, f'nGear_{d1}') for r in valid_rows]
        x_map = np.array([get_val(r, f'X_{d1}') for r in valid_rows])
        y_map = np.array([get_val(r, f'Y_{d1}') for r in valid_rows])

        fig = plt.figure(figsize=(10, 10), facecolor='#1a1a1a', dpi=100)
        gs = GridSpec(5, 1, height_ratios=[3, 1.5, 1, 1, 1], hspace=0.3)
        fig.patch.set_facecolor('#1a1a1a')

        ax_map = fig.add_subplot(gs[0], facecolor='#1a1a1a')
        ax_spd = fig.add_subplot(gs[1], facecolor='#1a1a1a')
        ax_thr = fig.add_subplot(gs[2], facecolor='#1a1a1a', sharex=ax_spd)
        ax_brk = fig.add_subplot(gs[3], facecolor='#1a1a1a', sharex=ax_spd)
        ax_ger = fig.add_subplot(gs[4], facecolor='#1a1a1a', sharex=ax_spd)
        telemetry_axes = [ax_spd, ax_thr, ax_brk, ax_ger]

        for ax in telemetry_axes:
            ax.tick_params(colors='#94a3b8', labelsize=8)
            for spine in ax.spines.values(): spine.set_edgecolor('#334155')
            ax.grid(color='#334155', linestyle='--', linewidth=0.5)

        ax_map.plot(x_map, y_map, color='#475569', linewidth=4, zorder=1)
        ax_map.axis('off')
        ax_map.set_aspect('equal', adjustable='datalim')
        car_dot1, = ax_map.plot([], [], 'o', color=self.color_d1, markersize=8, zorder=5)
        
        vlines = [ax.axvline(x=0, color='#f8fafc', linestyle='-', linewidth=1, alpha=0, zorder=10) for ax in telemetry_axes]

        ax_spd.plot(dist, s1, color=self.color_d1, linewidth=1.5, label=f"Velocidade ({d1})")
        ax_spd.set_ylabel("Speed", color='#94a3b8', fontsize=9)
        ax_spd.legend(loc='upper right', facecolor='#1a1a1a', edgecolor='#334155', labelcolor='white', fontsize=8)

        ax_thr.plot(dist, thr1, color=self.color_d1, drawstyle='steps-post', linewidth=1.5)
        ax_thr.set_ylabel("Throttle", color='#94a3b8', fontsize=9)
        ax_thr.set_ylim(-5, 105)

        ax_brk.plot(dist, brk1, color=self.color_d1, drawstyle='steps-post', linewidth=1.5)
        ax_brk.set_ylabel("Brake", color='#94a3b8', fontsize=9)
        ax_brk.set_ylim(-5, 105)

        ax_ger.plot(dist, gr1, color=self.color_d1, drawstyle='steps-post', linewidth=1.5)
        ax_ger.set_ylabel("Gear", color='#94a3b8', fontsize=9)
        ax_ger.set_yticks(range(1, 9))
        ax_ger.set_ylim(0, 9)
        ax_ger.set_xlabel("Distância (m)", color='#94a3b8', fontsize=9)

        plt.setp(ax_spd.get_xticklabels(), visible=False)
        plt.setp(ax_thr.get_xticklabels(), visible=False)
        plt.setp(ax_brk.get_xticklabels(), visible=False)
        fig.tight_layout()

        self.ind_canvas = FigureCanvas(fig)
        self.ui_telemetry.ind_chart_layout.addWidget(self.ind_canvas)

        def on_mouse_move_ind(event):
            if event.inaxes in telemetry_axes:
                x_mouse = event.xdata
                if x_mouse is not None:
                    idx = (np.abs(dist - x_mouse)).argmin()
                    if idx < len(x_map): car_dot1.set_data([x_map[idx]], [y_map[idx]])
                    for vline in vlines:
                        vline.set_xdata([x_mouse, x_mouse])
                        vline.set_alpha(1)
                    fig.canvas.draw_idle()
            else:
                car_dot1.set_data([], [])
                for vline in vlines: vline.set_alpha(0)
                fig.canvas.draw_idle()

        fig.canvas.mpl_connect("motion_notify_event", on_mouse_move_ind)

    def exportar_pdf_telemetria(self):
        try:
            ano = int(self.ui_telemetry.ind_year.text())
            gp = self.ui_telemetry.ind_gp.text()
            piloto = self.ui_telemetry.ind_d1.text().upper()
            
            if hasattr(self, 'ultimos_dados_ind'):
                caminho = gerar_pdf_telemetria(ano, gp, piloto, self.ultimos_dados_ind)
                self.ui_telemetry.ind_status.setText(f"Sucesso: {os.path.basename(caminho)}")
            else:
                self.ui_telemetry.ind_status.setText("Erro: Analise o piloto antes de exportar.")
        except Exception as e:
            self.ui_telemetry.ind_status.setText(f"Erro ao gerar PDF: {str(e)}")


    # TELEMETRIA COMPARATIVA
    def iniciar_telemetria_comp(self):
        self.ui_telemetry.btn_comp.setEnabled(False)
        self.ui_telemetry.comp_status.setText("Cruzando telemetrias...")
        self.ui_telemetry.comp_status.setStyleSheet("color: #00aeef;")
        
        y = int(self.ui_telemetry.comp_year.text())
        gp = self.ui_telemetry.comp_gp.text()
        d1 = self.ui_telemetry.comp_d1.text().upper()
        d2 = self.ui_telemetry.comp_d2.text().upper()
        
        self.worker_comp = TelemetryWorker(y, gp, d1, d2)
        self.worker_comp.success.connect(self.atualizar_telemetria_comp)
        self.worker_comp.error.connect(lambda e: self.mostrar_erro_aba(self.ui_telemetry.comp_status, self.ui_telemetry.btn_comp, e))
        self.worker_comp.start()

    def atualizar_telemetria_comp(self, dados, d1, d2):
        self.ui_telemetry.btn_comp.setEnabled(True)
        self.ui_telemetry.comp_status.setText(f"Comparação carregada. {d1}: {dados['lap_time_1']}s | {d2}: {dados['lap_time_2']}s")
        self.ui_telemetry.comp_status.setStyleSheet("color: #2ecc71;")

        if self.comp_canvas:
            self.ui_telemetry.comp_chart_layout.removeWidget(self.comp_canvas)
            self.comp_canvas.deleteLater()
            plt.close('all')

        telemetry = dados.get('telemetry', [])
        valid_rows = [r for r in telemetry if r['Distance'] is not None]
        
        dist = np.array([r['Distance'] for r in valid_rows])
        s1 = [r.get(f'Speed_{d1}', 0) for r in valid_rows]
        s2 = [r.get(f'Speed_{d2}', 0) for r in valid_rows]
        thr1 = [r.get(f'Throttle_{d1}', 0) for r in valid_rows]
        thr2 = [r.get(f'Throttle_{d2}', 0) for r in valid_rows]
        brk1 = [r.get(f'Brake_{d1}', 0) for r in valid_rows]
        brk2 = [r.get(f'Brake_{d2}', 0) for r in valid_rows]
        gr1 = [r.get(f'nGear_{d1}', 0) for r in valid_rows]
        gr2 = [r.get(f'nGear_{d2}', 0) for r in valid_rows]
        
        x_map = np.array([r.get(f'X_{d1}', 0) for r in valid_rows])
        y_map = np.array([r.get(f'Y_{d1}', 0) for r in valid_rows])

        fig = plt.figure(figsize=(10, 10), facecolor='#1a1a1a', dpi=100)
        gs = GridSpec(5, 1, height_ratios=[3, 1.5, 1, 1, 1], hspace=0.3)
        fig.patch.set_facecolor('#1a1a1a')

        ax_map = fig.add_subplot(gs[0], facecolor='#1a1a1a')
        ax_spd = fig.add_subplot(gs[1], facecolor='#1a1a1a')
        ax_thr = fig.add_subplot(gs[2], facecolor='#1a1a1a', sharex=ax_spd)
        ax_brk = fig.add_subplot(gs[3], facecolor='#1a1a1a', sharex=ax_spd)
        ax_ger = fig.add_subplot(gs[4], facecolor='#1a1a1a', sharex=ax_spd)

        telemetry_axes = [ax_spd, ax_thr, ax_brk, ax_ger]

        for ax in telemetry_axes:
            ax.tick_params(colors='#94a3b8', labelsize=8)
            for spine in ax.spines.values(): spine.set_edgecolor('#334155')
            ax.grid(color='#334155', linestyle='--', linewidth=0.5)

        ax_map.plot(x_map, y_map, color='#475569', linewidth=4, zorder=1)
        ax_map.axis('off')
        ax_map.set_aspect('equal', adjustable='datalim')
        
        car_dot1, = ax_map.plot([], [], 'o', color=self.color_d1, markersize=8, zorder=5)
        car_dot2, = ax_map.plot([], [], 'o', color=self.color_d2, markersize=8, zorder=6)
        
        vlines = [ax.axvline(x=0, color='#f8fafc', linestyle='-', linewidth=1, alpha=0, zorder=10) for ax in telemetry_axes]

        ax_spd.plot(dist, s1, color=self.color_d1, linewidth=1.5, label=d1)
        ax_spd.plot(dist, s2, color=self.color_d2, linewidth=1.5, label=d2)
        ax_spd.set_ylabel("Speed", color='#94a3b8', fontsize=9)
        ax_spd.legend(loc='upper right', facecolor='#1a1a1a', edgecolor='#334155', labelcolor='white', fontsize=8)

        ax_thr.plot(dist, thr1, color=self.color_d1, drawstyle='steps-post', linewidth=1.5)
        ax_thr.plot(dist, thr2, color=self.color_d2, drawstyle='steps-post', linewidth=1.5)
        ax_thr.set_ylabel("Throttle", color='#94a3b8', fontsize=9)
        ax_thr.set_ylim(-5, 105)

        ax_brk.plot(dist, brk1, color=self.color_d1, drawstyle='steps-post', linewidth=1.5)
        ax_brk.plot(dist, brk2, color=self.color_d2, drawstyle='steps-post', linewidth=1.5)
        ax_brk.set_ylabel("Brake", color='#94a3b8', fontsize=9)
        ax_brk.set_ylim(-5, 105)

        ax_ger.plot(dist, gr1, color=self.color_d1, drawstyle='steps-post', linewidth=1.5)
        ax_ger.plot(dist, gr2, color=self.color_d2, drawstyle='steps-post', linewidth=1.5)
        ax_ger.set_ylabel("Gear", color='#94a3b8', fontsize=9)
        ax_ger.set_yticks(range(1, 9))
        ax_ger.set_ylim(0, 9)
        ax_ger.set_xlabel("Distância (m)", color='#94a3b8', fontsize=9)

        plt.setp(ax_spd.get_xticklabels(), visible=False)
        plt.setp(ax_thr.get_xticklabels(), visible=False)
        plt.setp(ax_brk.get_xticklabels(), visible=False)
        fig.tight_layout()

        self.comp_canvas = FigureCanvas(fig)
        self.ui_telemetry.comp_chart_layout.addWidget(self.comp_canvas)

        def on_mouse_move_comp(event):
            if event.inaxes in telemetry_axes:
                x_mouse = event.xdata
                if x_mouse is not None:
                    idx = (np.abs(dist - x_mouse)).argmin()
                    if idx < len(x_map):
                        car_dot1.set_data([x_map[idx]], [y_map[idx]])
                        car_dot2.set_data([x_map[idx]], [y_map[idx]])
                    
                    for vline in vlines:
                        vline.set_xdata([x_mouse, x_mouse])
                        vline.set_alpha(1)
                    fig.canvas.draw_idle()
            else:
                car_dot1.set_data([], [])
                car_dot2.set_data([], [])
                for vline in vlines: vline.set_alpha(0)
                fig.canvas.draw_idle()

        fig.canvas.mpl_connect("motion_notify_event", on_mouse_move_comp)


    # PREVISÃO E ESTRATÉGIA
    def iniciar_previsao_futura(self):
        self.ui_prediction.btn_predict.setEnabled(False)
        self.ui_prediction.fut_status.setText("Gerando permutações...")
        self.ui_prediction.fut_status.setStyleSheet("color: #00aeef;")
        
        gp = self.ui_prediction.fut_gp.text()
        laps = int(self.ui_prediction.fut_laps.text())
        chaos = float(self.ui_prediction.fut_chaos.text())
        
        if not hasattr(self, 'janela_log_oracle'):
            self.janela_log_oracle = TerminalDialog(self, "Terminal - Previsão de Corrida")
        
        self.janela_log_oracle.terminal.clear()
        
        self.worker_oracle = FuturePredictionWorker(gp, laps, chaos)
        
        self.worker_oracle.log_msg.connect(self.janela_log_oracle.log)
        
        self.worker_oracle.success.connect(self.atualizar_previsao)
        self.worker_oracle.error.connect(lambda e: self.mostrar_erro_aba(self.ui_prediction.fut_status, self.ui_prediction.btn_predict, e))
        self.worker_oracle.start()

    def atualizar_previsao(self, dados):
        self.ui_prediction.btn_predict.setEnabled(True)
        self.ui_prediction.fut_status.setText("Simulação Finalizada.")
        self.ui_prediction.fut_status.setStyleSheet("color: #2ecc71;")

        classificacao = dados["classificacao"] 
        voltas = dados["laps"]
        sc_start = dados.get("sc_start")
        sc_duration = dados.get("sc_duration")
        
        podio = [item["driver"] for item in classificacao[:3]]
        texto_podio = f"PREVISÃO DO PÓDIO: 1º {podio[0]}  |  2º {podio[1]}  |  3º {podio[2]}"
        self.ui_prediction.oracle_podium.setText(texto_podio)

        if self.oracle_canvas:
            self.ui_prediction.oracle_chart_layout.removeWidget(self.oracle_canvas)
            self.oracle_canvas.deleteLater()
            plt.close('all')

        fig, ax = plt.subplots(figsize=(10, 5), facecolor='#1a1a1a', dpi=100)
        fig.patch.set_facecolor('#1a1a1a')
        ax.set_facecolor('#1a1a1a')

        ax.tick_params(colors='#aaaaaa')
        for spine in ax.spines.values(): spine.set_edgecolor('#454548')
        ax.grid(color='#454548', linestyle='--', linewidth=0.5)

        # Faixa amarela sinalizando entrada do Safety Car
        if sc_start is not None and sc_duration is not None:
            ax.axvspan(sc_start, sc_start + sc_duration, color='#e2d014', alpha=0.15)
            ax.text(sc_start + (sc_duration / 2), ax.get_ylim()[0] + 5, 'SAFETY CAR', 
                    color='#e2d014', fontsize=12, weight='bold', ha='center', va='bottom', rotation=90)

        cores = ['#00aeef', '#ff8800', '#e10600', '#00ffaa', '#cccccc', '#ff00ff', '#ffff00']
        
        for i, item in enumerate(classificacao):
            driver = item["driver"]
            pace = item["pace"]
            cor_linha = cores[i%len(cores)]
            
            ax.plot(voltas, pace, color=cor_linha, linewidth=2, label=f"{driver}")
            
            # Label de PitStops
            for pit_lap in item.get("pit_laps", []):
                if pit_lap < len(pace) and not np.isnan(pace[pit_lap]):
                    ax.annotate('PIT', 
                                xy=(voltas[pit_lap], pace[pit_lap]), 
                                xytext=(0, 10), textcoords="offset points", 
                                ha='center', color=cor_linha, fontsize=8, weight='bold')

            # Label de DNF na última volta válida
            dnf_lap = item.get("dnf_lap")
            if dnf_lap is not None and dnf_lap < len(pace):
                volta_anterior = dnf_lap - 1
                if volta_anterior >= 0 and not np.isnan(pace[volta_anterior]):
                    ax.annotate('DNF', 
                                xy=(voltas[volta_anterior], pace[volta_anterior]), 
                                xytext=(0, 15), textcoords="offset points", 
                                ha='center', color='#ff1e15', fontsize=10, weight='bold',
                                arrowprops=dict(arrowstyle="->", color='#ff1e15'))

        ax.set_title(f"Evolução de Ritmo Prevista - GP de {dados['gp']}", color='#f5f5f5', pad=10)
        ax.set_xlabel("Voltas", color='#aaaaaa')
        ax.set_ylabel("Tempo de Volta Projetado (s)", color='#aaaaaa')
        ax.legend(facecolor='#1a1a1a', edgecolor='#454548', labelcolor='white')
        
        fig.tight_layout()

        self.oracle_canvas = FigureCanvas(fig)
        self.ui_prediction.oracle_chart_layout.addWidget(self.oracle_canvas)

    def iniciar_estrategia(self):
        self.ui_prediction.btn_live.setEnabled(False)
        self.ui_prediction.live_status.setText("Calculando...")
        self.ui_prediction.live_status.setStyleSheet("color: #00aeef;")
        
        y = int(self.ui_prediction.live_year.text())
        gp = self.ui_prediction.live_gp.text()
        driver = self.ui_prediction.live_driver.text().upper()
        
        if not hasattr(self, 'janela_log_live'):
            self.janela_log_live = TerminalDialog(self, "Terminal - Previsão de Estratégia")
            
        self.janela_log_live.terminal.clear()
        
        self.worker_strategy = StrategyWorker(y, gp, driver)
        
        log_signal = getattr(self.worker_strategy, 'log_msg', None)
        if log_signal is not None:
            log_signal.connect(self.janela_log_live.log)
            
        self.worker_strategy.success.connect(self.atualizar_estrategia)
        self.worker_strategy.error.connect(lambda e: self.mostrar_erro_aba(self.ui_prediction.live_status, self.ui_prediction.btn_live, e))
        self.worker_strategy.start()

    def atualizar_estrategia(self, dados):
        self.ui_prediction.btn_live.setEnabled(True)
        self.ui_prediction.live_status.setText("Simulação Concluída.")
        self.ui_prediction.live_status.setStyleSheet("color: #aaaaaa;")

        self.ui_prediction.kpi_recomendacao.setText(f"Engenheiro de Corrida: {dados['recomendacao']}")
        self.ui_prediction.kpi_pit_window.setText(f"Janela Ideal: {dados['pit_window']}")

        if self.live_canvas:
            self.ui_prediction.live_chart_layout.removeWidget(self.live_canvas)
            self.live_canvas.deleteLater()
            plt.close('all')

        voltas = dados['laps']
        pace_a = dados['pace_a']
        vida_a = dados['vida_a']
        pace_b = dados['pace_b']
        vida_b = dados['vida_b']
        delta = dados['delta']

        fig = plt.figure(figsize=(10, 8), facecolor='#1a1a1a', dpi=100)
        gs = GridSpec(3, 1, height_ratios=[2, 1, 1], hspace=0.35)
        fig.patch.set_facecolor('#1a1a1a')

        ax_pace = fig.add_subplot(gs[0], facecolor='#1a1a1a')
        ax_delta = fig.add_subplot(gs[1], facecolor='#1a1a1a', sharex=ax_pace)
        ax_life = fig.add_subplot(gs[2], facecolor='#1a1a1a', sharex=ax_pace)

        for ax in [ax_pace, ax_delta, ax_life]:
            ax.tick_params(colors='#aaaaaa', labelsize=8)
            for spine in ax.spines.values(): spine.set_edgecolor('#454548')
            ax.grid(color='#454548', linestyle='--', linewidth=0.5)

        ax_pace.plot(voltas, pace_a, color='#ffffff', linewidth=2, label="Plano A (1 Parada)")
        ax_pace.plot(voltas, pace_b, color='#e10600', linewidth=2, label="Plano B (2 Paradas)")
        ax_pace.set_ylim(75, 85) 
        ax_pace.set_title("Projeção de Ritmo de Corrida (Ignorando tempo de Pit Lane)", color='#f5f5f5', pad=10)
        ax_pace.set_ylabel("Tempo de Volta (s)", color='#aaaaaa', fontsize=9)
        ax_pace.legend(facecolor='#1a1a1a', edgecolor='#454548', labelcolor='white', fontsize=8)

        ax_delta.fill_between(voltas, 0, delta, where=(np.array(delta) >= 0).tolist(), color='#e10600', alpha=0.5, label="B à frente")
        ax_delta.fill_between(voltas, 0, delta, where=(np.array(delta) < 0).tolist(), color='#ffffff', alpha=0.5, label="A à frente")
        ax_delta.axhline(0, color='#aaaaaa', linewidth=1)
        ax_delta.set_title("Vantagem Cumulativa (Delta de Tempo Total)", color='#f5f5f5', pad=5, fontsize=10)
        ax_delta.set_ylabel("Delta (s)", color='#aaaaaa', fontsize=9)

        ax_life.plot(voltas, vida_a, color='#ffffff', linestyle='-', linewidth=2)
        ax_life.plot(voltas, vida_b, color='#e10600', linestyle='-', linewidth=2)
        ax_life.axhline(30, color='#ffcc00', linestyle=':', linewidth=1.5) 
        ax_life.axhline(10, color='#ff4c4c', linestyle=':', linewidth=1.5) 
        ax_life.set_title("Vida Útil Projetada do Composto (%)", color='#f5f5f5', pad=5, fontsize=10)
        ax_life.set_ylabel("Pneu %", color='#aaaaaa', fontsize=9)
        ax_life.set_xlabel("Voltas", color='#aaaaaa', fontsize=9)
        ax_life.set_ylim(0, 105)

        fig.tight_layout()

        self.live_canvas = FigureCanvas(fig)
        self.ui_prediction.live_chart_layout.addWidget(self.live_canvas)

    def apply_theme(self):
        qss = """
        /* Fundo */
        QMainWindow, QWidget#central_widget { 
            background-color: #1a1a1a; 
            color: #e4e4e7; 
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Arial, sans-serif; 
        }

        QWidget#app_tab {
            background-color: #121212; 
        }
        
        QTabWidget#MainTabs::pane { 
            border: none; 
            border-top: 1px solid #27272a; 
            background-color: #121212; 
        }

        QFrame {
            background-color: transparent;
            border: none;
        }

        /* Barra de Navegação (Header) */
        QTabWidget#MainTabs > QTabBar {
            background-color: transparent; 
        }
        QTabWidget#MainTabs > QTabBar::tab { 
            background: transparent; 
            color: #a1a1aa; 
            padding: 18px 24px; 
            font-weight: 600; 
            font-size: 18px; 
            border: none;
            border-bottom: 3px solid transparent; 
            margin: 0px; 
        }
        QTabWidget#MainTabs > QTabBar::tab:selected { 
            color: #ffffff; 
            border-bottom: 3px solid #e10600; 
        }
        QTabWidget#MainTabs > QTabBar::tab:hover:!selected { 
            color: #ffffff; 
            background-color: #27272a;
        }

        /* Sub-Abas */
        QTabWidget#subtabs::pane {
            border: none;
            padding-top: 10px;
        }
        QTabWidget#subtabs > QTabBar {
            background-color: transparent; 
        }
        QTabWidget#subtabs > QTabBar::tab {
            background: #1a1a1a; 
            color: #71717a;
            padding: 10px 24px;
            font-size: 14px;
            font-weight: 600;
            border: none;
            margin-right: 8px;
            border-radius: 4px;
            margin-top: 10px;
        }
        QTabWidget#subtabs > QTabBar::tab:selected {
            background-color: #27272a; 
            border-bottom: 3px solid #e10600; 
            color: #ffffff;
        }
        QTabWidget#subtabs > QTabBar::tab:hover:!selected {
            color: #e4e4e7;
            background-color: #27272a;
        }

        /* Formulários */
        QLineEdit { 
            background-color: #1a1a1a; 
            color: #ffffff; 
            border: 1px solid #27272a; 
            border-radius: 4px; 
            padding: 8px 14px; 
            font-weight: 500; 
            font-size: 13px;
        }
        QLineEdit:focus { 
            border: 1px solid #00aeef; 
            background-color: #27272a;
        }

        QPushButton { 
            background-color: #1a1a1a; 
            color: #ffffff; 
            border: 1px solid #27272a; 
            border-radius: 4px; 
            padding: 9px 20px; 
            font-weight: 600; 
            font-size: 13px; 
        }
        QPushButton:hover { background-color: #27272a; border-color: #3f3f46; }
        QPushButton:pressed { background-color: #121212; }
        QPushButton:disabled { background-color: #121212; color: #3f3f46; border: 1px dashed #27272a; }

        QPushButton#btn_primary { background-color: #e10600; color: #ffffff; border: none; }
        QPushButton#btn_primary:hover { background-color: #ff1e15; }
        QPushButton#btn_primary:disabled { background-color: #551111; color: #aaaaaa; }

        /* Tabelas */
        QTableWidget { 
            background-color: #1a1a1a; color: #e4e4e7; gridline-color: #27272a; 
            border: none; outline: 0; font-size: 13px;
        }
        QTableWidget::item { padding: 8px; border-bottom: 1px solid #27272a; }
        QTableWidget::item:selected { background-color: #27272a; color: #ffffff; }
        QHeaderView::section { 
            background-color: #121212; color: #a1a1aa; padding: 12px; border: none; 
            border-bottom: 2px solid #27272a; font-weight: 700; font-size: 12px; text-transform: uppercase;
        }
        QLabel { color: #d4d4d8; font-size: 13px; font-weight: 500;}
        QScrollBar:vertical { background: #121212; width: 10px; }
        QScrollBar::handle:vertical { background: #27272a; border-radius: 5px; }
        QScrollBar::handle:vertical:hover { background: #3f3f46; }
        """
        self.setStyleSheet(qss)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PitWallApp()
    window.show()
    sys.exit(app.exec())