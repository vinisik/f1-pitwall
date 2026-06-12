from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
                               QLineEdit, QPushButton, QLabel, QFrame, 
                               QTableWidget, QHeaderView, QComboBox)
from PySide6.QtCore import Qt
from app.constants import CIRCUITOS_F1, ANOS_F1, PILOTOS_F1

class SummaryTabUI(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        control_frame = QFrame()
        control_layout = QHBoxLayout(control_frame)
        
        self.sum_year = QComboBox()
        self.sum_year.addItems(ANOS_F1)
        self.sum_year.setPlaceholderText("Ano")
        self.sum_year.setCurrentIndex(-1) 
        self.sum_year.setFixedWidth(80)
        
        self.sum_gp = QComboBox()
        self.sum_gp.addItems(list(CIRCUITOS_F1.keys()))
        self.sum_gp.setPlaceholderText("Circuito")
        self.sum_gp.setCurrentIndex(-1) 
        self.sum_gp.setFixedWidth(150)
        
        self.btn_summary = QPushButton("Gerar Resumo Oficial")
        self.btn_summary.setObjectName("btn_primary")
        self.btn_export_sum = QPushButton("Exportar Relatório")
        self.btn_export_sum.setStyleSheet("background-color: #454548; color: #ffffff;")
        self.sum_status = QLabel("")

        control_layout.addWidget(self.sum_year)
        control_layout.addWidget(self.sum_gp)
        control_layout.addWidget(self.btn_summary)
        control_layout.addWidget(self.btn_export_sum)
        control_layout.addWidget(self.sum_status)
        control_layout.addStretch()
        layout.addWidget(control_frame)

        self.subtabs_sum = QTabWidget()
        self.subtabs_sum.setObjectName("subtabs")
        layout.addWidget(self.subtabs_sum, stretch=1)

        # Tabela 
        self.tab_table = QWidget()
        tab_layout = QVBoxLayout(self.tab_table)
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Pos", "Piloto", "Grid", "Variação", "Histórico de Pneus"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        tab_layout.addWidget(self.table)
        
        # Posições
        self.tab_pos = QWidget()
        self.pos_chart_layout = QVBoxLayout(self.tab_pos)

        # Ritmo
        self.tab_pace = QWidget()
        self.pace_chart_layout = QVBoxLayout(self.tab_pace)

        # Tempo Pitstops
        self.tab_pit = QWidget()
        self.pit_chart_layout = QVBoxLayout(self.tab_pit)

        # Speedtrap
        self.tab_speed = QWidget()
        self.speed_chart_layout = QVBoxLayout(self.tab_speed)

        # Menu
        self.subtabs_sum.addTab(self.tab_table, "Resumo Completo")
        self.subtabs_sum.addTab(self.tab_pos, "Ganho/Perda de Posições")
        self.subtabs_sum.addTab(self.tab_pace, "Ritmo (Pace)")
        self.subtabs_sum.addTab(self.tab_pit, "Tempos de Pit Lane")
        self.subtabs_sum.addTab(self.tab_speed, "Speed Trap")

        
class TelemetryTabUI(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.subtabs_tel = QTabWidget()
        self.subtabs_tel.setObjectName("subtabs")
        layout.addWidget(self.subtabs_tel)
        
        # Sub-abas
        self.subtab_ind = QWidget()
        self.subtab_comp = QWidget()
        self.subtabs_tel.addTab(self.subtab_ind, "Piloto Único")
        self.subtabs_tel.addTab(self.subtab_comp, "Comparar Pilotos")
        
        self.setup_ind()
        self.setup_comp()

    def setup_ind(self):
        layout = QVBoxLayout(self.subtab_ind)
        control_frame = QFrame()
        control_layout = QHBoxLayout(control_frame)
        
        self.ind_year = QComboBox()
        self.ind_year.addItems(ANOS_F1)
        self.ind_year.setPlaceholderText("Ano")
        self.ind_year.setCurrentIndex(-1)
        self.ind_year.setFixedWidth(80)
        
        self.ind_gp = QComboBox()
        self.ind_gp.addItems(list(CIRCUITOS_F1.keys()))
        self.ind_gp.setPlaceholderText("Circuito")
        self.ind_gp.setCurrentIndex(-1)
        self.ind_gp.setFixedWidth(150)

        self.ind_d1 = QComboBox()
        self.ind_d1.addItems(list(PILOTOS_F1.keys()))
        self.ind_d1.setPlaceholderText("Piloto")
        self.ind_d1.setCurrentIndex(-1) 
        self.ind_d1.setFixedWidth(80)
        
        # Campo para escolher a volta específica 
        self.ind_lap = QLineEdit("")
        self.ind_lap.setFixedWidth(70)
        self.ind_lap.setPlaceholderText("Volta")

        self.ind_session = QComboBox()
        self.ind_session.addItem("Corrida", "R")
        self.ind_session.addItem("Classificação", "Q")
        self.ind_session.addItem("Sprint", "S")
        self.ind_session.addItem("Sprint Qualy", "SQ")
        self.ind_session.addItem("Treino 1", "FP1")
        self.ind_session.addItem("Treino 2", "FP2")
        self.ind_session.addItem("Treino 3", "FP3")
        self.ind_session.setFixedWidth(110)
        
        self.btn_ind = QPushButton("Analisar Piloto")
        self.btn_ind.setObjectName("btn_primary")
        self.btn_export_tel = QPushButton("Exportar PDF")
        self.btn_export_tel.setStyleSheet("background-color: #454548; color: #ffffff;")
        self.ind_status = QLabel("")

        control_layout.addWidget(self.ind_year)
        control_layout.addWidget(self.ind_gp)
        control_layout.addWidget(self.ind_session)
        control_layout.addWidget(self.ind_d1)
        control_layout.addWidget(self.ind_lap) 
        control_layout.addWidget(self.btn_ind)
        control_layout.addWidget(self.btn_export_tel)
        control_layout.addWidget(self.ind_status)
        control_layout.addStretch()
        layout.addWidget(control_frame)

        self.ind_chart_frame = QFrame()
        self.ind_chart_layout = QVBoxLayout(self.ind_chart_frame)
        layout.addWidget(self.ind_chart_frame, stretch=1)

    def setup_comp(self):
        layout = QVBoxLayout(self.subtab_comp)
        control_frame = QFrame()
        control_layout = QHBoxLayout(control_frame)
        
        self.comp_year = QComboBox()
        self.comp_year.addItems(ANOS_F1)
        self.comp_year.setPlaceholderText("Ano")
        self.comp_year.setCurrentIndex(-1)
        self.comp_year.setFixedWidth(80)
        
        self.comp_gp = QComboBox()
        self.comp_gp.addItems(list(CIRCUITOS_F1.keys()))
        self.comp_gp.setPlaceholderText("Circuito")
        self.comp_gp.setCurrentIndex(-1)
        self.comp_gp.setFixedWidth(150)

        self.comp_d1 = QComboBox()
        self.comp_d1.addItems(list(PILOTOS_F1.keys()))
        self.comp_d1.setPlaceholderText("Piloto 1")
        self.comp_d1.setCurrentIndex(-1)
        self.comp_d1.setFixedWidth(80)

        self.comp_d2 = QComboBox()
        self.comp_d2.addItems(list(PILOTOS_F1.keys()))
        self.comp_d2.setPlaceholderText("Piloto 2")
        self.comp_d2.setCurrentIndex(-1)
        self.comp_d2.setFixedWidth(80)

        self.comp_session = QComboBox()
        self.comp_session.addItem("Corrida", "R")
        self.comp_session.addItem("Classificação", "Q")
        self.comp_session.addItem("Sprint", "S")
        self.comp_session.addItem("Sprint Qualy", "SQ")
        self.comp_session.addItem("Treino 1", "FP1")
        self.comp_session.addItem("Treino 2", "FP2")
        self.comp_session.addItem("Treino 3", "FP3")
        self.comp_session.setFixedWidth(110)
        
        self.btn_comp = QPushButton("Comparar Pilotos")
        self.btn_comp.setObjectName("btn_primary")
        self.comp_status = QLabel("")

        control_layout.addWidget(self.comp_year)
        control_layout.addWidget(self.comp_gp)
        control_layout.addWidget(self.comp_session)
        control_layout.addWidget(self.comp_d1)
        control_layout.addWidget(self.comp_d2)
        control_layout.addWidget(self.btn_comp)
        control_layout.addWidget(self.comp_status)
        control_layout.addStretch()
        layout.addWidget(control_frame)

        self.comp_chart_frame = QFrame()
        self.comp_chart_layout = QVBoxLayout(self.comp_chart_frame)
        layout.addWidget(self.comp_chart_frame, stretch=1)

class StrategyPredictionUI(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.subtabs_strategy = QTabWidget()
        self.subtabs_strategy.setObjectName("subtabs") 
        layout.addWidget(self.subtabs_strategy)
        
        self.subtab_oraculo = QWidget()
        self.subtab_race_control = QWidget()
        self.subtabs_strategy.addTab(self.subtab_oraculo, "Prever Corrida Futura")
        self.subtabs_strategy.addTab(self.subtab_race_control, "Simular Estratégia")
        
        self.setup_oraculo()
        self.setup_race_control()

    def setup_oraculo(self):
        layout = QVBoxLayout(self.subtab_oraculo)
        control_frame = QFrame()
        control_layout = QHBoxLayout(control_frame)
        
        self.fut_gp = QComboBox()
        self.fut_gp.addItems(list(CIRCUITOS_F1.keys()))
        self.fut_gp.setPlaceholderText("Circuito")
        self.fut_gp.setCurrentIndex(-1)
        self.fut_gp.setFixedWidth(150)
        
        self.fut_laps = QLineEdit()
        self.fut_laps.setFixedWidth(60)
        self.fut_laps.setReadOnly(True)
        self.fut_laps.setStyleSheet("background-color: #27272a; color: #a1a1aa; border: 1px solid #3f3f46;")
        
        self.fut_chaos = QLineEdit()
        self.fut_chaos.setFixedWidth(80)
        self.fut_chaos.setReadOnly(True)
        self.fut_chaos.setStyleSheet("background-color: #27272a; color: #a1a1aa; border: 1px solid #3f3f46;")
        
        self.btn_predict = QPushButton("Rodar Simulação")
        self.btn_predict.setObjectName("btn_primary")
        
        self.btn_logs_oraculo = QPushButton("Terminal")
        self.btn_logs_oraculo.setStyleSheet("background-color: #27272a; color: #a1a1aa; border: 1px solid #3f3f46;")
        
        self.fut_status = QLabel("")

        control_layout.addWidget(QLabel("GP Futuro:"))
        control_layout.addWidget(self.fut_gp)
        control_layout.addWidget(QLabel("Nº Voltas:"))
        control_layout.addWidget(self.fut_laps)
        control_layout.addWidget(QLabel("Prob. Chuva/SC:"))
        control_layout.addWidget(self.fut_chaos)
        control_layout.addWidget(self.btn_predict)
        control_layout.addWidget(self.btn_logs_oraculo) 
        control_layout.addWidget(self.fut_status)
        control_layout.addStretch()
        layout.addWidget(control_frame)

        self.oraculo_podium = QLabel("Simule para ver o pódio previsto...")
        self.oraculo_podium.setStyleSheet("font-size: 18px; color: #e2d014; font-weight: bold; padding: 10px; background-color: #1a1a1a; border-radius: 6px;")
        self.oraculo_podium.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.oraculo_podium)

        self.oraculo_chart_frame = QFrame()
        self.oraculo_chart_layout = QVBoxLayout(self.oraculo_chart_frame)
        self.oraculo_chart_frame.setStyleSheet("background-color: #1a1a1a; border-radius: 8px;")
        layout.addWidget(self.oraculo_chart_frame, stretch=1)

        # Conectar o sinal de mudança do combobox e forçar atualização inicial
        self.fut_gp.currentTextChanged.connect(self.atualizar_dados_circuito)

    def atualizar_dados_circuito(self, circuito_nome):
        if not circuito_nome:
            self.fut_laps.setText("")
            self.fut_chaos.setText("")
            return
        dados = CIRCUITOS_F1.get(circuito_nome, {"laps": 50, "chaos": 0.3})
        self.fut_laps.setText(str(dados["laps"]))
        self.fut_chaos.setText(str(dados["chaos"]))

    def setup_race_control(self):
        layout = QVBoxLayout(self.subtab_race_control)
        control_frame = QFrame()
        control_layout = QHBoxLayout(control_frame)
        
        self.live_year = QComboBox()
        self.live_year.addItems(ANOS_F1)
        self.live_year.setPlaceholderText("Ano")
        self.live_year.setCurrentIndex(-1)
        self.live_year.setFixedWidth(80)
        
        self.live_gp = QComboBox()
        self.live_gp.addItems(list(CIRCUITOS_F1.keys()))
        self.live_gp.setPlaceholderText("Circuito")
        self.live_gp.setCurrentIndex(-1)
        self.live_gp.setFixedWidth(150)
        
        self.live_driver = QComboBox()
        self.live_driver.addItems(list(PILOTOS_F1.keys()))
        self.live_driver.setPlaceholderText("Piloto")
        self.live_driver.setCurrentIndex(-1)
        self.live_driver.setFixedWidth(80)
        
        self.btn_live = QPushButton("Gerar Estratégia")
        self.btn_live.setObjectName("btn_primary")
        
        self.btn_export_est = QPushButton("Exportar PDF")
        self.btn_export_est.setEnabled(False) 
        
        self.btn_logs_live = QPushButton("Terminal")
        self.btn_logs_live.setStyleSheet("background-color: #27272a; color: #a1a1aa; border: 1px solid #3f3f46;")
        
        self.live_status = QLabel("")

        control_layout.addWidget(QLabel("Ano:"))
        control_layout.addWidget(self.live_year)
        control_layout.addWidget(QLabel("GP:"))
        control_layout.addWidget(self.live_gp)
        control_layout.addWidget(QLabel("Piloto:"))
        control_layout.addWidget(self.live_driver)
        control_layout.addWidget(self.btn_live)
        control_layout.addWidget(self.btn_export_est) 
        control_layout.addWidget(self.btn_logs_live) 
        control_layout.addWidget(self.live_status)
        control_layout.addStretch()
        layout.addWidget(control_frame)

        kpi_frame = QFrame()
        kpi_layout = QHBoxLayout(kpi_frame)
        self.kpi_recomendacao = QLabel("Aguardando simulação...")
        self.kpi_recomendacao.setStyleSheet("font-size: 14px; color: #ffffff; font-weight: bold;")
        self.kpi_pit_window = QLabel("")
        self.kpi_pit_window.setStyleSheet("font-size: 14px; color: #00aeef; font-weight: bold;")
        
        kpi_layout.addWidget(self.kpi_recomendacao)
        kpi_layout.addWidget(self.kpi_pit_window)
        kpi_layout.addStretch()
        layout.addWidget(kpi_frame)

        self.live_chart_frame = QFrame()
        self.live_chart_layout = QVBoxLayout(self.live_chart_frame)
        self.live_chart_frame.setStyleSheet("background-color: #1a1a1a; border-radius: 8px;")
        layout.addWidget(self.live_chart_frame, stretch=1)