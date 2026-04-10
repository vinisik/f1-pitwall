import os
import sys
import numpy as np
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QTabWidget, QLineEdit, QPushButton, 
                               QLabel, QFrame, QTableWidget, QTableWidgetItem, QHeaderView)
from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtGui import QFont, QColor

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.gridspec import GridSpec
from app.services.f1_data import obter_telemetria_piloto, obter_resumo_corrida, comparar_telemetria
from app.services.reports import gerar_pdf_estrategia, gerar_pdf_telemetria, gerar_pdf_resumo_corrida
from app.services.ml_engine import prever_degradacao_pneu

# Helpers de interface
def get_tire_style(compound):
    """Retorna as cores reais dos compostos da Pirelli"""
    styles = {
        'SOFT': {'bg': '#e10600', 'fg': '#ffffff'},
        'MEDIUM': {'bg': '#e2d014', 'fg': '#000000'},
        'HARD': {'bg': '#ffffff', 'fg': '#000000'},
        'INTERMEDIATE': {'bg': '#39b54a', 'fg': '#ffffff'},
        'WET': {'bg': '#00aeef', 'fg': '#ffffff'},
    }
    return styles.get(compound.upper(), {'bg': '#888888', 'fg': '#ffffff'})


# Workers para processamento em background
class SingleTelemetryWorker(QThread):
    """Extrai a telemetria completa de apenas UM piloto"""
    success = Signal(dict, str)
    error = Signal(str)

    def __init__(self, year, gp, d1):
        super().__init__()
        self.year, self.gp, self.d1 = year, gp, d1

    def run(self):
        try:
            dados = comparar_telemetria(self.year, self.gp, self.d1, self.d1)
            
            if "erro" in dados:
                self.error.emit(dados["erro"])
            else:
                self.success.emit(dados, self.d1)
        except Exception as e:
            self.error.emit(f"Falha na extração individual: {str(e)}")

class TelemetryWorker(QThread):
    """Extrai a telemetria cruzada de DOIS ou mais pilotos"""
    success = Signal(dict, str, str)
    error = Signal(str)

    def __init__(self, year, gp, d1, d2):
        super().__init__()
        self.year, self.gp, self.d1, self.d2 = year, gp, d1, d2

    def run(self):
        try:
            dados = comparar_telemetria(self.year, self.gp, self.d1, self.d2)
            if "erro" in dados:
                self.error.emit(dados["erro"])
            else:
                self.success.emit(dados, self.d1, self.d2)
        except Exception as e:
            self.error.emit(f"Falha na extração: {str(e)}")

class StrategyWorker(QThread):
    success = Signal(dict)
    error = Signal(str)

    def __init__(self, year, gp, driver):
        super().__init__()
        self.year, self.gp, self.driver = year, gp, driver

    def run(self):
        try:
            import numpy as np
            from app.services.ml_engine import prever_degradacao_pneu
            
            total_laps = 50
            voltas = np.arange(1, total_laps + 1)
            
            # Chama a IA para prever a curva de degradação do pneu para o piloto e composto escolhido
            pace_medio_a = list(prever_degradacao_pneu(range(1, 23), 'MEDIUM'))
            pace_duro_a = list(prever_degradacao_pneu(range(1, 29), 'HARD'))
            pace_a = np.array(pace_medio_a + pace_duro_a)
            pace_a[21] += 22.0 # Adiciona tempo de Pit Stop
            
            # Prever ritmo para Estratégia B 
            pace_macio1 = list(prever_degradacao_pneu(range(1, 16), 'SOFT'))
            pace_medio_b = list(prever_degradacao_pneu(range(1, 21), 'MEDIUM'))
            pace_macio2 = list(prever_degradacao_pneu(range(1, 16), 'SOFT'))
            pace_b = np.array(pace_macio1 + pace_medio_b + pace_macio2)
            pace_b[14] += 22.0 # Pit 1
            pace_b[34] += 22.0 # Pit 2
            
            vida_a = np.where(voltas <= 22, 100 - (voltas * 3.5),
                              100 - ((voltas - 22) * 4.5))
            vida_a = np.clip(vida_a, 0, 100)

            vida_b = np.where(voltas <= 15, 100 - (voltas * 5.0),
                     np.where(voltas <= 35, 100 - ((voltas - 15) * 3.5),
                                            100 - ((voltas - 35) * 5.0)))
            vida_b = np.clip(vida_b, 0, 100)

            # Calcula o tempo total de corrida (Soma cumulativa)
            race_time_a = np.cumsum(pace_a)
            race_time_b = np.cumsum(pace_b)
            delta_b_to_a = race_time_a - race_time_b # Positivo significa que B é mais rápido

            dados_estrategia = {
                "driver": self.driver,
                "laps": voltas.tolist(),
                "pace_a": pace_a.tolist(),
                "vida_a": vida_a.tolist(),
                "pace_b": pace_b.tolist(),
                "vida_b": vida_b.tolist(),
                "delta": delta_b_to_a.tolist(),
                "recomendacao": "Plano B (2 Stops) é estaticamente -3.2s mais rápido no final.",
                "pit_window": "Volta 14 - 17"
            }
            
            self.success.emit(dados_estrategia)
        except Exception as e:
            self.error.emit(f"Falha na projeção de corrida: {str(e)}")

class SummaryWorker(QThread):
    success = Signal(list)
    error = Signal(str)

    def __init__(self, year, gp):
        super().__init__()
        self.year, self.gp = year, gp

    def run(self):
        try:
            dados = obter_resumo_corrida(self.year, self.gp)
            self.success.emit(dados)
        except Exception as e:
            self.error.emit(f"Falha ao gerar resumo: {str(e)}")

class FuturePredictionWorker(QThread):
    success = Signal(dict)
    error = Signal(str)

    def __init__(self, gp, laps, weather_chaos):
        super().__init__()
        self.gp = gp
        self.laps = laps
        self.weather_chaos = weather_chaos # 0.0 a 1.0

    def run(self):
        try:
            import numpy as np
            import random
            from app.services.ml_engine import prever_degradacao_pneu
            
            teams_pace = {
                "NOR (McLaren)": 74.40,  
                "VER (Red Bull)": 74.45, 
                "LEC (Ferrari)": 74.50,
                "HAM (Ferrari)": 74.55,  
                "RUS (Mercedes)": 74.60,
                "PIA (McLaren)": 74.65,
                "ALO (Aston Martin)": 74.80
            }
            
            voltas = np.arange(1, self.laps + 1)
            resultados = {}
            
            try:
                ia_pace_curve = prever_degradacao_pneu(voltas.tolist(), 'MEDIUM')
                if isinstance(ia_pace_curve, dict):
                    ia_pace_values = list(ia_pace_curve.values())
                else:
                    ia_pace_values = list(ia_pace_curve)
                curva_degradacao = np.array(ia_pace_values) - ia_pace_values[0]
            except Exception:
                curva_degradacao = voltas * 0.08
            
            # SAFETY CAR
            # Agora o Safety Car afeta TODOS os pilotos ao mesmo tempo no gráfico
            impacto_safety_car = np.zeros(self.laps)
            if random.random() < self.weather_chaos:
                sc_start = random.randint(10, self.laps - 15)
                sc_duration = random.randint(3, 6)
                # Todos perdem 20 segundos de ritmo nessas voltas
                impacto_safety_car[sc_start:sc_start+sc_duration] = 20.0 
            
            # Simulação de corrida para cada piloto
            for driver, base_pace in teams_pace.items():
                
                # Variabilidade Volta a Volta (Micro-erros, tráfego, zebras)
                # Gera uma matriz onde cada volta tem uma variação aleatória de ~0.3s
                lap_volatility = np.random.normal(0, 0.3, self.laps)
                
                # Pace Final junta tudo
                pace = base_pace + curva_degradacao + lap_volatility + impacto_safety_car
                
                # Pit Stops
                pit_lap = int(self.laps / 2) + random.randint(-4, 4) 
                if pit_lap < self.laps:
                    # Simula o tempo de pit stop usando uma curva Normal
                    # Média de 22s, mas com desvio padrão de 1.5s para criar variação realista
                    tempo_pit = np.random.normal(22.0, 1.5)
                    pace[pit_lap] += tempo_pit
                
                # 3. Erro Crítico (Fator Humano)
                # 15% de chance do piloto dar uma travada de pneu feia ou espalhar na curva
                if random.random() < 0.15:
                    erro_lap = random.randint(1, self.laps - 1)
                    pace[erro_lap] += random.uniform(2.5, 6.0) # Perde de 2 a 6 segundos
                
                total_time = np.sum(pace)
                resultados[driver] = {"total_time": total_time, "pace": pace.tolist()}
            
            classificacao_lista = []
            for driver, info in sorted(resultados.items(), key=lambda item: item[1]["total_time"]):
                classificacao_lista.append({
                    "driver": driver,
                    "total_time": info["total_time"],
                    "pace": info["pace"]
                })
            
            dados = {
                "gp": self.gp,
                "laps": voltas.tolist(),
                "classificacao": classificacao_lista
            }
            
            self.success.emit(dados)
        except Exception as e:
            self.error.emit(f"Falha na previsão de Machine Learning: {str(e)}")

# Interface principal
class PitWallApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("F1 Pit Wall - Engenharia")
        self.resize(1300, 850)
        self.setMinimumSize(1000, 700)

        # Cores Padrão para os Gráficos
        self.color_d1 = "#e10600" 
        self.color_d2 = "#00aeef" 

        self.setup_ui()
        self.apply_theme()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        self.tab_live = QWidget()
        self.tab_summary = QWidget()
        self.tab_telemetry = QWidget()

        self.tabs.addTab(self.tab_summary, "Resumo da Corrida")
        self.tabs.addTab(self.tab_telemetry, "Análise de Telemetria")
        self.tabs.addTab(self.tab_live, "Estratégia ao Vivo")

        self.setup_live_tab()
        self.setup_summary_tab()
        self.setup_telemetry_tab()

        self.tabs.setCurrentIndex(2)

    # Estratégia ao Vivo
    def setup_live_tab(self):
        layout = QVBoxLayout(self.tab_live)
        
        self.subtabs_strategy = QTabWidget()
        layout.addWidget(self.subtabs_strategy)
        
        self.subtab_race_control = QWidget()
        self.subtab_oracle = QWidget()
        
        self.subtabs_strategy.addTab(self.subtab_race_control, "Race Control - Simular Estratégia")
        self.subtabs_strategy.addTab(self.subtab_oracle, "Prever Corrida Futura")
        
        self.setup_race_control() 
        
        self.setup_oracle()

    def setup_race_control(self):
        layout = QVBoxLayout(self.subtab_race_control)
        
        # Controles da Estratégia
        control_frame = QFrame()
        control_layout = QHBoxLayout(control_frame)
        
        self.live_year = QLineEdit("2025"); self.live_year.setFixedWidth(80)
        self.live_gp = QLineEdit("Brazil"); self.live_gp.setFixedWidth(150)
        self.live_driver = QLineEdit("VER"); self.live_driver.setFixedWidth(80)
        
        self.btn_live = QPushButton("Calcular Estratégia")
        self.btn_live.clicked.connect(self.iniciar_estrategia)
        self.live_status = QLabel("")
        self.live_status.setStyleSheet("color: #aaaaaa; font-weight: bold;")

        control_layout.addWidget(QLabel("Ano:"))
        control_layout.addWidget(self.live_year)
        control_layout.addWidget(QLabel("GP:"))
        control_layout.addWidget(self.live_gp)
        control_layout.addWidget(QLabel("Piloto:"))
        control_layout.addWidget(self.live_driver)
        control_layout.addWidget(self.btn_live)
        control_layout.addWidget(self.live_status)
        control_layout.addStretch()
        layout.addWidget(control_frame)

        # KPIs de Engenharia
        kpi_frame = QFrame()
        kpi_layout = QHBoxLayout(kpi_frame)
        kpi_layout.setContentsMargins(0, 10, 0, 10)
        
        self.kpi_recomendacao = QLabel("Aguardando simulação...")
        self.kpi_recomendacao.setStyleSheet("font-size: 14px; color: #ffffff; font-weight: bold;")
        self.kpi_pit_window = QLabel("")
        self.kpi_pit_window.setStyleSheet("font-size: 14px; color: #00aeef; font-weight bold;")
        
        kpi_layout.addWidget(self.kpi_recomendacao)
        kpi_layout.addWidget(self.kpi_pit_window)
        kpi_layout.addStretch()
        layout.addWidget(kpi_frame)

        # Gráfico de Estratégia
        self.live_chart_frame = QFrame()
        self.live_chart_layout = QVBoxLayout(self.live_chart_frame)
        self.live_chart_frame.setStyleSheet("background-color: #2d2d30; border-radius: 8px;")
        layout.addWidget(self.live_chart_frame, stretch=1)
        self.live_canvas = None

    def setup_oracle(self):
        layout = QVBoxLayout(self.subtab_oracle)
        
        # Controles da Previsão
        control_frame = QFrame()
        control_layout = QHBoxLayout(control_frame)
        self.fut_gp = QLineEdit("Monza"); self.fut_gp.setPlaceholderText("Circuito")
        self.fut_laps = QLineEdit("53"); self.fut_laps.setPlaceholderText("Voltas")
        self.fut_laps.setFixedWidth(60)
        self.fut_chaos = QLineEdit("0.2"); self.fut_chaos.setPlaceholderText("Caos (0 a 1)")
        self.fut_chaos.setFixedWidth(80)
        
        self.btn_predict = QPushButton("Rodar Simulação")
        self.btn_predict.clicked.connect(self.iniciar_previsao_futura)
        self.fut_status = QLabel("")
        self.fut_status.setStyleSheet("color: #aaaaaa; font-weight: bold;")

        control_layout.addWidget(QLabel("GP Futuro:"))
        control_layout.addWidget(self.fut_gp)
        control_layout.addWidget(QLabel("Nº Voltas:"))
        control_layout.addWidget(self.fut_laps)
        control_layout.addWidget(QLabel("Prob. Chuva/SC:"))
        control_layout.addWidget(self.fut_chaos)
        control_layout.addWidget(self.btn_predict)
        control_layout.addWidget(self.fut_status)
        control_layout.addStretch()
        layout.addWidget(control_frame)

        # Grid do Pódio e Gráfico
        self.oracle_podium = QLabel("Simule para ver o pódio previsto...")
        self.oracle_podium.setStyleSheet("font-size: 18px; color: #e2d014; font-weight: bold; padding: 10px; background-color: #2d2d30; border-radius: 6px;")
        self.oracle_podium.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.oracle_podium)

        self.oracle_chart_frame = QFrame()
        self.oracle_chart_layout = QVBoxLayout(self.oracle_chart_frame)
        self.oracle_chart_frame.setStyleSheet("background-color: #2d2d30; border-radius: 8px;")
        layout.addWidget(self.oracle_chart_frame, stretch=1)
        self.oracle_canvas = None

    def exportar_pdf_telemetria(self):
        try:
            ano = int(self.ind_year.text())
            gp = self.ind_gp.text()
            piloto = self.ind_d1.text().upper()
            
            if hasattr(self, 'ultimos_dados_ind'):
                caminho = gerar_pdf_telemetria(ano, gp, piloto, self.ultimos_dados_ind)
                self.ind_status.setText(f"Sucesso: {os.path.basename(caminho)}")
            else:
                self.ind_status.setText("Erro: Analise o piloto antes de exportar.")
        except Exception as e:
            self.ind_status.setText(f"Erro ao gerar PDF: {str(e)}")

    def exportar_pdf_resumo(self):
        try:
            if not hasattr(self, 'ultimos_dados_resumo'):
                self.sum_status.setText("Erro: Primeiro clique em 'Gerar Resumo'")
                self.sum_status.setStyleSheet("color: #e10600;")
                return

            ano = int(self.sum_year.text())
            gp = self.sum_gp.text()
            
            caminho = gerar_pdf_resumo_corrida(ano, gp, self.ultimos_dados_resumo)
            
            self.sum_status.setText(f"PDF salvo: {os.path.basename(caminho)}")
            self.sum_status.setStyleSheet("color: #2ecc71;")
            
        except Exception as e:
            self.sum_status.setText(f"Erro na exportação: {str(e)}")
            self.sum_status.setStyleSheet("color: #e10600;")

    def iniciar_previsao_futura(self):
        self.btn_predict.setEnabled(False)
        self.fut_status.setText("Gerando milhares de permutações...")
        self.fut_status.setStyleSheet("color: #00aeef;")
        
        gp = self.fut_gp.text()
        laps = int(self.fut_laps.text())
        chaos = float(self.fut_chaos.text())
        
        self.worker_oracle = FuturePredictionWorker(gp, laps, chaos)
        self.worker_oracle.success.connect(self.atualizar_previsao)
        self.worker_oracle.error.connect(lambda e: self.mostrar_erro_aba(self.fut_status, self.btn_predict, e))
        self.worker_oracle.start()

    def atualizar_previsao(self, dados):
        self.btn_predict.setEnabled(True)
        self.fut_status.setText("Simulação Finalizada.")
        self.fut_status.setStyleSheet("color: #2ecc71;")

        classificacao = dados["classificacao"] 
        voltas = dados["laps"]
        
        # Pega os 3 primeiros da lista
        podio = [item["driver"] for item in classificacao[:3]]
        texto_podio = f"PREVISÃO DO PÓDIO: 1º {podio[0]}  |  2º {podio[1]}  |  3º {podio[2]}"
        self.oracle_podium.setText(texto_podio)

        if self.oracle_canvas:
            self.oracle_chart_layout.removeWidget(self.oracle_canvas)
            self.oracle_canvas.deleteLater()
            import matplotlib.pyplot as plt
            plt.close('all')

        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(10, 5), facecolor='#2d2d30', dpi=100)
        fig.patch.set_facecolor('#1e1e1e')
        ax.set_facecolor('#1e1e1e')

        ax.tick_params(colors='#aaaaaa')
        for spine in ax.spines.values(): spine.set_edgecolor('#454548')
        ax.grid(color='#454548', linestyle='--', linewidth=0.5)

        cores = ['#00aeef', '#ff8800', '#e10600', '#00ffaa', '#cccccc', '#ff00ff', '#ffff00']
        
        # Plota as linhas iterando sobre a lista
        for i, item in enumerate(classificacao):
            driver = item["driver"]
            pace = item["pace"]
            ax.plot(voltas, pace, color=cores[i%len(cores)], linewidth=2, label=f"{driver}")

        ax.set_title(f"Evolução de Ritmo Prevista - GP de {dados['gp']}", color='#f5f5f5', pad=10)
        ax.set_xlabel("Voltas", color='#aaaaaa')
        ax.set_ylabel("Tempo de Volta Projetado (s)", color='#aaaaaa')
        ax.legend(facecolor='#2d2d30', edgecolor='#454548', labelcolor='white')
        
        fig.tight_layout()

        from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
        self.oracle_canvas = FigureCanvas(fig)
        self.oracle_chart_layout.addWidget(self.oracle_canvas)

    def iniciar_estrategia(self):
        self.btn_live.setEnabled(False)
        self.live_status.setText("Calculando permutações de corrida e degradação...")
        self.live_status.setStyleSheet("color: #00aeef;")
        self.worker_strategy = StrategyWorker(int(self.live_year.text()), self.live_gp.text(), self.live_driver.text().upper())
        self.worker_strategy.success.connect(self.atualizar_estrategia)
        self.worker_strategy.error.connect(lambda e: self.mostrar_erro_aba(self.live_status, self.btn_live, e))
        self.worker_strategy.start()

    def atualizar_estrategia(self, dados):
        self.btn_live.setEnabled(True)
        self.live_status.setText("Simulação Concluída.")
        self.live_status.setStyleSheet("color: #aaaaaa;")

        # Atualiza KPIs
        self.kpi_recomendacao.setText(f"Engenheiro de Corrida: {dados['recomendacao']}")
        self.kpi_pit_window.setText(f"Janela Ideal: {dados['pit_window']}")

        if self.live_canvas:
            self.live_chart_layout.removeWidget(self.live_canvas)
            self.live_canvas.deleteLater()
            import matplotlib.pyplot as plt
            plt.close('all')

        voltas = dados['laps']
        pace_a = dados['pace_a']
        vida_a = dados['vida_a']
        pace_b = dados['pace_b']
        vida_b = dados['vida_b']
        delta = dados['delta']

        from matplotlib.gridspec import GridSpec
        import matplotlib.pyplot as plt

        fig = plt.figure(figsize=(10, 8), facecolor='#2d2d30', dpi=100)
        gs = GridSpec(3, 1, height_ratios=[2, 1, 1], hspace=0.35)
        fig.patch.set_facecolor('#1e1e1e')

        ax_pace = fig.add_subplot(gs[0], facecolor='#1e1e1e')
        ax_delta = fig.add_subplot(gs[1], facecolor='#1e1e1e', sharex=ax_pace)
        ax_life = fig.add_subplot(gs[2], facecolor='#1e1e1e', sharex=ax_pace)

        for ax in [ax_pace, ax_delta, ax_life]:
            ax.tick_params(colors='#aaaaaa', labelsize=8)
            for spine in ax.spines.values(): spine.set_edgecolor('#454548')
            ax.grid(color='#454548', linestyle='--', linewidth=0.5)

        # Gráfico de Ritmo 
        ax_pace.plot(voltas, pace_a, color='#ffffff', linewidth=2, label="Plano A (1 Parada)")
        ax_pace.plot(voltas, pace_b, color='#e10600', linewidth=2, label="Plano B (2 Paradas)")
        ax_pace.set_ylim(75, 85) 
        ax_pace.set_title("Projeção de Ritmo de Corrida (Ignorando tempo de Pit Lane)", color='#f5f5f5', pad=10)
        ax_pace.set_ylabel("Tempo de Volta (s)", color='#aaaaaa', fontsize=9)
        ax_pace.legend(facecolor='#2d2d30', edgecolor='#454548', labelcolor='white', fontsize=8)

        # Gráfico de Delta 
        ax_delta.fill_between(voltas, 0, delta, where=(np.array(delta) >= 0).tolist(), color='#e10600', alpha=0.5, label="B à frente")
        ax_delta.fill_between(voltas, 0, delta, where=(np.array(delta) < 0).tolist(), color='#ffffff', alpha=0.5, label="A à frente")
        ax_delta.axhline(0, color='#aaaaaa', linewidth=1)
        ax_delta.set_title("Vantagem Cumulativa (Delta de Tempo Total)", color='#f5f5f5', pad=5, fontsize=10)
        ax_delta.set_ylabel("Delta (s)", color='#aaaaaa', fontsize=9)

        # Gráfico de Vida Útil do Pneu
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
        self.live_chart_layout.addWidget(self.live_canvas)

    # Resumo da Corrida
    def setup_summary_tab(self):
        layout = QVBoxLayout(self.tab_summary)

        control_frame = QFrame()
        control_layout = QHBoxLayout(control_frame)
        self.sum_year = QLineEdit("2025"); self.sum_year.setFixedWidth(80)
        self.sum_gp = QLineEdit("Brazil"); self.sum_gp.setFixedWidth(150)
        self.btn_summary = QPushButton("Gerar Resumo Oficial")
        self.btn_summary.clicked.connect(self.iniciar_resumo)

        # Botão de Exportar PDF 
        self.btn_export_sum = QPushButton("Exportar Relatório")
        self.btn_export_sum.setStyleSheet("background-color: #454548; color: #ffffff;")
        self.btn_export_sum.clicked.connect(self.exportar_pdf_resumo)
        self.btn_export_sum.setEnabled(True)

        self.sum_status = QLabel("")

        control_layout.addWidget(self.sum_year)
        control_layout.addWidget(self.sum_gp)
        control_layout.addWidget(self.btn_summary)
        control_layout.addWidget(self.btn_export_sum)
        control_layout.addWidget(self.sum_status)
        control_layout.addStretch()
        layout.addWidget(control_frame)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Pos", "Piloto", "Grid", "Variação", "Histórico de Pneus"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table, stretch=1)

    def iniciar_resumo(self):
        self.btn_summary.setEnabled(False)
        self.sum_status.setText("Buscando dados...")
        self.worker_summary = SummaryWorker(int(self.sum_year.text()), self.sum_gp.text())
        self.worker_summary.success.connect(self.atualizar_resumo)
        self.worker_summary.error.connect(lambda e: self.mostrar_erro_aba(self.sum_status, self.btn_summary, e))
        self.worker_summary.start()

    def atualizar_resumo(self, resultados):
        self.ultimos_dados_resumo = resultados
        self.btn_summary.setEnabled(True)
        self.btn_export_tel.setEnabled(True) 
        self.sum_status.setText("Grid atualizado!")
        self.table.setRowCount(0) 
        
        for i, row in enumerate(resultados):
            self.table.insertRow(i)
            
            item_pos = QTableWidgetItem(str(row.get('chegada', '')))
            item_pos.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(i, 0, item_pos)
            
            item_piloto = QTableWidgetItem(str(row.get('piloto', '')))
            item_piloto.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(i, 1, item_piloto)
            
            item_grid = QTableWidgetItem(f"P{row.get('largada', '')}")
            item_grid.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(i, 2, item_grid)
            
            var = row.get('saldo_posicoes', 0)
            var_text = f"+{var}" if var > 0 else str(var)
            var_item = QTableWidgetItem(var_text)
            var_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if var > 0: var_item.setForeground(QColor("#39b54a"))
            elif var < 0: var_item.setForeground(QColor("#ff4c4c"))
            self.table.setItem(i, 3, var_item)
            
            # Pílulas Coloridas dos Pneus
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
                
            self.table.setCellWidget(i, 4, stints_widget)
           

    # Análise de Telemetria
    def setup_telemetry_tab(self):
        layout = QVBoxLayout(self.tab_telemetry)
        
        # Cria as Sub-Abas dentro da aba de Telemetria principal
        self.subtabs_tel = QTabWidget()
        layout.addWidget(self.subtabs_tel)
        
        self.subtab_ind = QWidget()
        self.subtab_comp = QWidget()
        
        self.subtabs_tel.addTab(self.subtab_ind, "Piloto Único")
        self.subtabs_tel.addTab(self.subtab_comp, "Comparar Pilotos")
        
        self.setup_tel_individual()
        self.setup_tel_comparacao()

    # Telemetria Individual
    def setup_tel_individual(self):
        layout = QVBoxLayout(self.subtab_ind)

        control_frame = QFrame()
        control_layout = QHBoxLayout(control_frame)
        self.ind_year = QLineEdit("2025"); self.ind_year.setFixedWidth(80)
        self.ind_gp = QLineEdit("Brazil"); self.ind_gp.setFixedWidth(150)
        self.ind_d1 = QLineEdit("VER"); self.ind_d1.setFixedWidth(80)
        self.btn_ind = QPushButton("Analisar Piloto")
        self.btn_ind.clicked.connect(self.iniciar_telemetria_ind)
        
        # Botão de Exportar PDF
        self.btn_export_tel = QPushButton("Exportar PDF")
        self.btn_export_tel.setStyleSheet("background-color: #454548; color: #ffffff;") # Cinza neutro
        self.btn_export_tel.clicked.connect(self.exportar_pdf_telemetria)
        self.btn_export_tel.setEnabled(True) # Habilitar somente após análise
        
        self.ind_status = QLabel("")

        control_layout.addWidget(self.ind_year)
        control_layout.addWidget(self.ind_gp)
        control_layout.addWidget(self.ind_d1)
        control_layout.addWidget(self.btn_ind)
        control_layout.addWidget(self.btn_export_tel)
        control_layout.addWidget(self.ind_status)
        control_layout.addStretch()
        layout.addWidget(control_frame)

        self.ind_chart_frame = QFrame()
        self.ind_chart_layout = QVBoxLayout(self.ind_chart_frame)
        layout.addWidget(self.ind_chart_frame, stretch=1)
        self.ind_canvas = None

    def iniciar_telemetria_ind(self):
        self.btn_ind.setEnabled(False)
        self.ind_status.setText("Extraindo sensores do carro...")
        self.ind_status.setStyleSheet("color: #00aeef;")
        
        y, gp, d1 = int(self.ind_year.text()), self.ind_gp.text(), self.ind_d1.text().upper()
        
        self.worker_ind = SingleTelemetryWorker(y, gp, d1)
        self.worker_ind.success.connect(self.atualizar_telemetria_ind)
        self.worker_ind.error.connect(lambda e: self.mostrar_erro_aba(self.ind_status, self.btn_ind, e))
        self.worker_ind.start()

    def atualizar_telemetria_ind(self, dados, d1):
        self.btn_ind.setEnabled(True)
        self.ind_status.setText(f"Telemetria de {d1} carregada. Tempo de Volta: {dados.get('lap_time_1', 'N/A')}s")
        self.ind_status.setStyleSheet("color: #2ecc71;")
        self.btn_export_tel.setEnabled(True)
        
        # Armazena os dados para exportação posterior
        self.ultimos_dados_ind = dados

        if self.ind_canvas:
            self.ind_chart_layout.removeWidget(self.ind_canvas)
            self.ind_canvas.deleteLater()
            plt.close('all')

        telemetry = dados.get('telemetry', [])
        valid_rows = [r for r in telemetry if r['Distance'] is not None]
        
        def get_val(row, key):
            if key in row and row[key] is not None:
                return row[key]
            elif f"{key}_x" in row and row[f"{key}_x"] is not None:
                return row[f"{key}_x"]
            return 0

        dist = np.array([r['Distance'] for r in valid_rows])
        
        s1 = [get_val(r, f'Speed_{d1}') for r in valid_rows]
        thr1 = [get_val(r, f'Throttle_{d1}') for r in valid_rows]
        brk1 = [get_val(r, f'Brake_{d1}') for r in valid_rows]
        gr1 = [get_val(r, f'nGear_{d1}') for r in valid_rows]
        x_map = np.array([get_val(r, f'X_{d1}') for r in valid_rows])
        y_map = np.array([get_val(r, f'Y_{d1}') for r in valid_rows])

        fig = plt.figure(figsize=(10, 10), facecolor='#2d2d30', dpi=100)
        gs = GridSpec(5, 1, height_ratios=[3, 1.5, 1, 1, 1], hspace=0.3)
        fig.patch.set_facecolor('#2d2d30')

        ax_map = fig.add_subplot(gs[0], facecolor='#2d2d30')
        ax_spd = fig.add_subplot(gs[1], facecolor='#2d2d30')
        ax_thr = fig.add_subplot(gs[2], facecolor='#2d2d30', sharex=ax_spd)
        ax_brk = fig.add_subplot(gs[3], facecolor='#2d2d30', sharex=ax_spd)
        ax_ger = fig.add_subplot(gs[4], facecolor='#2d2d30', sharex=ax_spd)
        telemetry_axes = [ax_spd, ax_thr, ax_brk, ax_ger]

        for ax in telemetry_axes:
            ax.tick_params(colors='#94a3b8', labelsize=8)
            for spine in ax.spines.values(): spine.set_edgecolor('#334155')
            ax.grid(color='#334155', linestyle='--', linewidth=0.5)

        # MAPA
        ax_map.plot(x_map, y_map, color='#475569', linewidth=4, zorder=1)
        ax_map.axis('off')
        ax_map.set_aspect('equal', adjustable='datalim')
        car_dot1, = ax_map.plot([], [], 'o', color=self.color_d1, markersize=8, zorder=5)
        
        vlines = [ax.axvline(x=0, color='#f8fafc', linestyle='-', linewidth=1, alpha=0, zorder=10) for ax in telemetry_axes]

        # SENSORES
        ax_spd.plot(dist, s1, color=self.color_d1, linewidth=1.5, label=f"Velocidade ({d1})")
        ax_spd.set_ylabel("Speed", color='#94a3b8', fontsize=9)
        ax_spd.legend(loc='upper right', facecolor='#1e293b', edgecolor='#334155', labelcolor='white', fontsize=8)

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
        self.ind_chart_layout.addWidget(self.ind_canvas)

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


    # Comparar Pilotos
    def setup_tel_comparacao(self):
        layout = QVBoxLayout(self.subtab_comp)

        control_frame = QFrame()
        control_layout = QHBoxLayout(control_frame)
        self.comp_year = QLineEdit("2025"); self.comp_year.setFixedWidth(80)
        self.comp_gp = QLineEdit("Brazil"); self.comp_gp.setFixedWidth(150)
        self.comp_d1 = QLineEdit("VER"); self.comp_d1.setFixedWidth(80); self.comp_d1.setPlaceholderText("Alvo 1")
        self.comp_d2 = QLineEdit("NOR"); self.comp_d2.setFixedWidth(80); self.comp_d2.setPlaceholderText("Alvo 2")
        self.btn_comp = QPushButton("Comparar Pilotos")
        self.btn_comp.clicked.connect(self.iniciar_telemetria_comp)
        self.comp_status = QLabel("")

        control_layout.addWidget(self.comp_year)
        control_layout.addWidget(self.comp_gp)
        control_layout.addWidget(self.comp_d1)
        control_layout.addWidget(self.comp_d2)
        control_layout.addWidget(self.btn_comp)
        control_layout.addWidget(self.comp_status)
        control_layout.addStretch()
        layout.addWidget(control_frame)

        self.comp_chart_frame = QFrame()
        self.comp_chart_layout = QVBoxLayout(self.comp_chart_frame)
        layout.addWidget(self.comp_chart_frame, stretch=1)
        self.comp_canvas = None

    def iniciar_telemetria_comp(self):
        self.btn_comp.setEnabled(False)
        self.comp_status.setText("Cruzando telemetrias...")
        self.comp_status.setStyleSheet("color: #00aeef;")
        
        y, gp = int(self.comp_year.text()), self.comp_gp.text()
        d1, d2 = self.comp_d1.text().upper(), self.comp_d2.text().upper()
        
        self.worker_comp = TelemetryWorker(y, gp, d1, d2)
        self.worker_comp.success.connect(self.atualizar_telemetria_comp)
        self.worker_comp.error.connect(lambda e: self.mostrar_erro_aba(self.comp_status, self.btn_comp, e))
        self.worker_comp.start()

    def atualizar_telemetria_comp(self, dados, d1, d2):
        self.btn_comp.setEnabled(True)
        self.comp_status.setText(f"Comparação carregada. {d1}: {dados['lap_time_1']}s | {d2}: {dados['lap_time_2']}s")
        self.comp_status.setStyleSheet("color: #2ecc71;")

        if self.comp_canvas:
            self.comp_chart_layout.removeWidget(self.comp_canvas)
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
        
        # Mapa usando o traçado do Piloto 1 como base
        x_map = np.array([r.get(f'X_{d1}', 0) for r in valid_rows])
        y_map = np.array([r.get(f'Y_{d1}', 0) for r in valid_rows])

        fig = plt.figure(figsize=(10, 10), facecolor='#1e293b', dpi=100)
        gs = GridSpec(5, 1, height_ratios=[3, 1.5, 1, 1, 1], hspace=0.3)
        fig.patch.set_facecolor('#0f172a')

        ax_map = fig.add_subplot(gs[0], facecolor='#0f172a')
        ax_spd = fig.add_subplot(gs[1], facecolor='#0f172a')
        ax_thr = fig.add_subplot(gs[2], facecolor='#0f172a', sharex=ax_spd)
        ax_brk = fig.add_subplot(gs[3], facecolor='#0f172a', sharex=ax_spd)
        ax_ger = fig.add_subplot(gs[4], facecolor='#0f172a', sharex=ax_spd)

        telemetry_axes = [ax_spd, ax_thr, ax_brk, ax_ger]

        for ax in telemetry_axes:
            ax.tick_params(colors='#94a3b8', labelsize=8)
            for spine in ax.spines.values(): spine.set_edgecolor('#334155')
            ax.grid(color='#334155', linestyle='--', linewidth=0.5)

        # MAPA
        ax_map.plot(x_map, y_map, color='#475569', linewidth=4, zorder=1)
        ax_map.axis('off')
        ax_map.set_aspect('equal', adjustable='datalim')
        
        car_dot1, = ax_map.plot([], [], 'o', color=self.color_d1, markersize=8, zorder=5)
        car_dot2, = ax_map.plot([], [], 'o', color=self.color_d2, markersize=8, zorder=6) # Segundo carro
        
        vlines = [ax.axvline(x=0, color='#f8fafc', linestyle='-', linewidth=1, alpha=0, zorder=10) for ax in telemetry_axes]

        # SENSORES
        ax_spd.plot(dist, s1, color=self.color_d1, linewidth=1.5, label=d1)
        ax_spd.plot(dist, s2, color=self.color_d2, linewidth=1.5, label=d2)
        ax_spd.set_ylabel("Speed", color='#94a3b8', fontsize=9)
        ax_spd.legend(loc='upper right', facecolor='#1e293b', edgecolor='#334155', labelcolor='white', fontsize=8)

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
        self.comp_chart_layout.addWidget(self.comp_canvas)

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


    # UTILS E TEMA QSS
    def mostrar_erro_aba(self, label, botao, mensagem):
        botao.setEnabled(True)
        label.setText(f"Erro: {mensagem}")
        label.setStyleSheet("color: #e10600;")

    def apply_theme(self):
        qss = """
        QMainWindow, QWidget { background-color: #1e1e1e; color: #f5f5f5; font-family: 'Segoe UI', Arial, sans-serif; }
        
        QTabWidget::pane { border: 1px solid #454548; background: #1e1e1e; border-radius: 6px; }
        QTabBar::tab { background: #2d2d30; color: #aaaaaa; padding: 12px 25px; border: 1px solid #454548; font-weight: bold; font-size: 13px; }
        QTabBar::tab:selected { background: #1e1e1e; color: #ffffff; border-bottom: 3px solid #aaaaaa; }
        QTabBar::tab:hover:!selected { background: #454548; color: #e0e0e0; }

        QLineEdit { background-color: #2d2d30; color: #f5f5f5; border: 1px solid #454548; border-radius: 6px; padding: 8px; font-weight: bold; }
        QLineEdit:focus { border: 1px solid #888888; }

        QPushButton { background-color: #555555; color: #ffffff; border: none; border-radius: 6px; padding: 8px 18px; font-weight: bold; font-size: 13px; }
        QPushButton:hover { background-color: #666666; }
        QPushButton:disabled { background-color: #333333; color: #777777; }
        
        QTableWidget { background-color: #2d2d30; color: #f5f5f5; gridline-color: #454548; border: 1px solid #454548; border-radius: 6px; outline: 0; }
        QHeaderView::section { background-color: #1e1e1e; color: #aaaaaa; padding: 8px; border: 1px solid #454548; font-weight: bold; font-size: 12px; }
        QTableWidget::item { padding: 5px; }
        QTableWidget::item:selected { background-color: #454548; }
        QScrollBar:vertical { background: #1e1e1e; width: 10px; }
        QScrollBar::handle:vertical { background: #454548; border-radius: 5px; }
        """
        self.setStyleSheet(qss)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PitWallApp()
    window.show()
    sys.exit(app.exec())