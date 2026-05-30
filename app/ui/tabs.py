from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
                               QLineEdit, QPushButton, QLabel, QFrame, 
                               QTableWidget, QHeaderView)
from PySide6.QtCore import Qt

# Helper de Cores de Pneus
def get_tire_style(compound):
    styles = {
        'SOFT': {'bg': '#e10600', 'fg': '#ffffff'},
        'MEDIUM': {'bg': '#e2d014', 'fg': '#000000'},
        'HARD': {'bg': '#ffffff', 'fg': '#000000'},
        'INTERMEDIATE': {'bg': '#39b54a', 'fg': '#ffffff'},
        'WET': {'bg': '#00aeef', 'fg': '#ffffff'},
    }
    return styles.get(compound.upper(), {'bg': '#888888', 'fg': '#ffffff'})

class SummaryTabUI(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        control_frame = QFrame()
        control_layout = QHBoxLayout(control_frame)
        
        self.sum_year = QLineEdit("2025")
        self.sum_year.setFixedWidth(80)
        self.sum_gp = QLineEdit("Brazil")
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

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Pos", "Piloto", "Grid", "Variação", "Histórico de Pneus"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table, stretch=1)

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
        
        self.ind_year = QLineEdit("2025"); self.ind_year.setFixedWidth(80)
        self.ind_gp = QLineEdit("Brazil"); self.ind_gp.setFixedWidth(150)
        self.ind_d1 = QLineEdit("VER"); self.ind_d1.setFixedWidth(80)
        
        self.btn_ind = QPushButton("Analisar Piloto")
        self.btn_ind.setObjectName("btn_primary")
        self.btn_export_tel = QPushButton("Exportar PDF")
        self.btn_export_tel.setStyleSheet("background-color: #454548; color: #ffffff;")
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

    def setup_comp(self):
        layout = QVBoxLayout(self.subtab_comp)
        control_frame = QFrame()
        control_layout = QHBoxLayout(control_frame)
        
        self.comp_year = QLineEdit("2025"); self.comp_year.setFixedWidth(80)
        self.comp_gp = QLineEdit("Brazil"); self.comp_gp.setFixedWidth(150)
        self.comp_d1 = QLineEdit("VER"); self.comp_d1.setFixedWidth(80); self.comp_d1.setPlaceholderText("Alvo 1")
        self.comp_d2 = QLineEdit("NOR"); self.comp_d2.setFixedWidth(80); self.comp_d2.setPlaceholderText("Alvo 2")
        
        self.btn_comp = QPushButton("Comparar Pilotos")
        self.btn_comp.setObjectName("btn_primary")
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

class StrategyPredictionUI(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.subtabs_strategy = QTabWidget()
        self.subtabs_strategy.setObjectName("subtabs") 
        layout.addWidget(self.subtabs_strategy)
        
        self.subtab_oracle = QWidget()
        self.subtab_race_control = QWidget()
        self.subtabs_strategy.addTab(self.subtab_oracle, "Prever Corrida Futura")
        self.subtabs_strategy.addTab(self.subtab_race_control, "Simular Estratégia")
        
        self.setup_oracle()
        self.setup_race_control()

    def setup_oracle(self):
        layout = QVBoxLayout(self.subtab_oracle)
        control_frame = QFrame()
        control_layout = QHBoxLayout(control_frame)
        
        self.fut_gp = QLineEdit("Monza"); self.fut_gp.setPlaceholderText("Circuito")
        self.fut_laps = QLineEdit("53"); self.fut_laps.setFixedWidth(60)
        self.fut_chaos = QLineEdit("0.2"); self.fut_chaos.setFixedWidth(80)
        
        self.btn_predict = QPushButton("Rodar Simulação")
        self.btn_predict.setObjectName("btn_primary")
        
        self.btn_logs_oracle = QPushButton("Terminal")
        self.btn_logs_oracle.setStyleSheet("background-color: #27272a; color: #a1a1aa; border: 1px solid #3f3f46;")
        
        self.fut_status = QLabel("")

        control_layout.addWidget(QLabel("GP Futuro:"))
        control_layout.addWidget(self.fut_gp)
        control_layout.addWidget(QLabel("Nº Voltas:"))
        control_layout.addWidget(self.fut_laps)
        control_layout.addWidget(QLabel("Prob. Chuva/SC:"))
        control_layout.addWidget(self.fut_chaos)
        control_layout.addWidget(self.btn_predict)
        control_layout.addWidget(self.btn_logs_oracle) 
        control_layout.addWidget(self.fut_status)
        control_layout.addStretch()
        layout.addWidget(control_frame)

        self.oracle_podium = QLabel("Simule para ver o pódio previsto...")
        self.oracle_podium.setStyleSheet("font-size: 18px; color: #e2d014; font-weight: bold; padding: 10px; background-color: #1a1a1a; border-radius: 6px;")
        self.oracle_podium.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.oracle_podium)

        self.oracle_chart_frame = QFrame()
        self.oracle_chart_layout = QVBoxLayout(self.oracle_chart_frame)
        self.oracle_chart_frame.setStyleSheet("background-color: #1a1a1a; border-radius: 8px;")
        layout.addWidget(self.oracle_chart_frame, stretch=1)

    def setup_race_control(self):
        layout = QVBoxLayout(self.subtab_race_control)
        control_frame = QFrame()
        control_layout = QHBoxLayout(control_frame)
        
        self.live_year = QLineEdit("2026") 
        self.live_year.setFixedWidth(80)
        self.live_gp = QLineEdit("Brazil")
        self.live_gp.setFixedWidth(150)
        self.live_driver = QLineEdit("VER")
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