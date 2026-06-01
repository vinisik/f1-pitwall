import numpy as np
import random
from PySide6.QtCore import QThread, Signal
from app.services.f1_data import comparar_telemetria, obter_resumo_corrida, obter_comportamento_historico_pista, obter_hierarquia_atual
from app.services.ml_engine import prever_degradacao_pneu
import datetime


class SingleTelemetryWorker(QThread):
    success = Signal(dict, str)
    error = Signal(str)

    def __init__(self, year, gp, d1, lap_num=None):
        super().__init__()
        self.year, self.gp, self.d1, self.lap_num = year, gp, d1, lap_num

    def run(self):
        try:
            # Passa a volta para a API
            dados = comparar_telemetria(self.year, self.gp, self.d1, self.d1, lap_num1=self.lap_num, lap_num2=self.lap_num)
            if "erro" in dados: self.error.emit(dados["erro"])
            else: self.success.emit(dados, self.d1)
        except Exception as e:
            self.error.emit(f"Falha na extração individual: {str(e)}")


class TelemetryWorker(QThread):
    success = Signal(dict, str, str)
    error = Signal(str)

    def __init__(self, year, gp, d1, d2):
        super().__init__()
        self.year, self.gp, self.d1, self.d2 = year, gp, d1, d2

    def run(self):
        try:
            dados = comparar_telemetria(self.year, self.gp, self.d1, self.d2)
            if "erro" in dados: self.error.emit(dados["erro"])
            else: self.success.emit(dados, self.d1, self.d2)
        except Exception as e:
            self.error.emit(f"Falha na extração: {str(e)}")


class StrategyWorker(QThread):
    """
    Consulta o ano anterior para descobrir o comportamento
    real da pista antes de gerar os gráficos de estratégia.
    """
    success = Signal(dict)
    error = Signal(str)

    def __init__(self, year, gp, driver):
        super().__init__()
        self.year, self.gp, self.driver = year, gp, driver

    def run(self):
        try:
            inteligencia_pista = obter_comportamento_historico_pista(self.year, self.gp)
            total_laps = inteligencia_pista['TOTAL_LAPS']
            voltas = np.arange(1, total_laps + 1)
            
            # Limites dinâmicos baseados no asfalto real do circuito
            limite_soft = inteligencia_pista['SOFT']
            limite_medium = inteligencia_pista['MEDIUM']
            
            # Helper para obter o ritmo previsto pela IA
            def obter_ritmo_seguro(laps_range, compound):
                laps_list = list(laps_range)
                try:
                    res = prever_degradacao_pneu(laps_list, compound)
                    if isinstance(res, dict) and "erro" in [k.lower() for k in res.keys()]:
                        raise ValueError("IA retornou erro")
                    
                    if isinstance(res, dict):
                        vals = list(res.values())
                        if len(vals) == len(laps_list): return vals
                    elif len(list(res)) == len(laps_list):
                        return list(res)
                    raise ValueError("Tamanho inesperado")
                except Exception:
                    # Fator de degradação genérico matemático (Fallback seguro)
                    deg = 0.08 if compound == 'SOFT' else (0.05 if compound == 'MEDIUM' else 0.03)
                    return [75.0 + (i * deg) for i in range(len(laps_list))]

            # Plano A - Garantindo que não aplique no final da corrida
            pit_a_lap = min(limite_medium, total_laps - 10) 
            
            pace_medio_a = obter_ritmo_seguro(range(1, pit_a_lap + 1), 'MEDIUM')
            pace_duro_a = obter_ritmo_seguro(range(pit_a_lap + 1, total_laps + 1), 'HARD')
            
            pace_a = np.array(pace_medio_a + pace_duro_a)
            if len(pace_a) > (pit_a_lap - 1):
                pace_a[pit_a_lap - 1] += 22.0 # Injeta os 22s do Pit Stop na volta calculada
            
            # Plano B (Dinâmico: Soft -> Medium -> Soft)
            pit_b1_lap = limite_soft
            pit_b2_lap = min(pit_b1_lap + limite_medium, total_laps - limite_soft)
            
            pace_macio1 = obter_ritmo_seguro(range(1, pit_b1_lap + 1), 'SOFT')
            pace_medio_b = obter_ritmo_seguro(range(pit_b1_lap + 1, pit_b2_lap + 1), 'MEDIUM')
            pace_macio2 = obter_ritmo_seguro(range(pit_b2_lap + 1, total_laps + 1), 'SOFT')
            
            pace_b = np.array(pace_macio1 + pace_medio_b + pace_macio2)
            if len(pace_b) > (pit_b1_lap - 1): pace_b[pit_b1_lap - 1] += 22.0
            if len(pace_b) > (pit_b2_lap - 1): pace_b[pit_b2_lap - 1] += 22.0

            # Cálculos Analíticos Consolidados para os Gráficos
            vida_a = np.where(voltas <= pit_a_lap, 
                              100 - (voltas * (100 / limite_medium)),
                              100 - ((voltas - pit_a_lap) * (100 / inteligencia_pista['HARD'])))
            
            vida_b = np.where(voltas <= pit_b1_lap, 
                              100 - (voltas * (100 / limite_soft)),
                     np.where(voltas <= pit_b2_lap, 
                              100 - ((voltas - pit_b1_lap) * (100 / limite_medium)),
                              100 - ((voltas - pit_b2_lap) * (100 / limite_soft))))

            vida_a = np.clip(vida_a, 0, 100)
            vida_b = np.clip(vida_b, 0, 100)

            race_time_a = np.cumsum(pace_a)
            race_time_b = np.cumsum(pace_b)
            delta_b_to_a = race_time_a - race_time_b 

            tempo_final_a = race_time_a[-1]
            tempo_final_b = race_time_b[-1]
            estrategia_vencedora = "Plano A (1 Stop)" if tempo_final_a < tempo_final_b else "Plano B (2 Stops)"
            vantagem = abs(tempo_final_a - tempo_final_b)

            dados_estrategia = {
                "driver": self.driver,
                "laps": voltas.tolist(),
                "pace_a": pace_a.tolist(),
                "vida_a": vida_a.tolist(),
                "pace_b": pace_b.tolist(),
                "vida_b": vida_b.tolist(),
                "delta": delta_b_to_a.tolist(),
                "recomendacao": f"{estrategia_vencedora} é estatisticamente {vantagem:.1f}s mais rápido.",
                "pit_window": f"Volta {pit_b1_lap - 2} a {pit_b1_lap + 1}"
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
    log_msg = Signal(str) 

    def __init__(self, gp, laps, weather_chaos):
        super().__init__()
        self.gp = gp
        self.laps = laps
        self.weather_chaos = weather_chaos 

    def run(self):
        try:
            self.log_msg.emit("[SISTEMA] Iniciando Kernel de Simulação Monte Carlo...")
            ano_atual = datetime.datetime.now().year
            
            self.log_msg.emit(f"[API] Conectando ao banco de dados para o GP: {self.gp}...")
            inteligencia_pista = obter_comportamento_historico_pista(ano_atual, self.gp)
            base_pace_circuito = inteligencia_pista.get('BASE_PACE', 80.0)
            self.log_msg.emit(f"[CALC] Pace Base Histórico estabelecido em {base_pace_circuito:.3f}s")
            
            self.log_msg.emit("[API] Extraindo hierarquia e deltas da última corrida...")
            hierarquia_atual = obter_hierarquia_atual(ano_atual)
            
            if not hierarquia_atual:
                self.log_msg.emit("[AVISO] Falha na API. Usando Hierarquia de Fallback.")
                hierarquia_atual = {"VER": -0.2, "NOR": -0.15, "LEC": 0.05, "HAM": 0.15, "RUS": 0.25, "ALO": 0.60}
            
            laps_to_simulate = self.laps if self.laps > 0 else inteligencia_pista['TOTAL_LAPS']
            voltas = np.arange(1, laps_to_simulate + 1)
            resultados = {}
            
            self.log_msg.emit("[ML] Invocando Regressão para curva de degradação...")
            try:
                ia_pace_curve = prever_degradacao_pneu(voltas.tolist(), 'MEDIUM')
                if isinstance(ia_pace_curve, dict):
                    ia_pace_values = list(ia_pace_curve.values())
                else:
                    ia_pace_values = list(ia_pace_curve)
                curva_degradacao = np.array(ia_pace_values) - ia_pace_values[0]
                self.log_msg.emit("[ML] Curva de degradação térmica calculada com sucesso.")
            except Exception:
                curva_degradacao = voltas * 0.05
                self.log_msg.emit("[AVISO] Fallback de degradação linear aplicado.")
            
            impacto_safety_car = np.zeros(laps_to_simulate)
            sc_start = None
            sc_duration = None
            
            self.log_msg.emit(f"[MONTE CARLO] Sorteando probabilidade de Caos Climático/SC: {self.weather_chaos*100}%")
            if random.random() < self.weather_chaos:
                sc_start = random.randint(10, laps_to_simulate - 15)
                sc_duration = random.randint(3, 6)
                impacto_safety_car[sc_start:sc_start+sc_duration] = 20.0 
                self.log_msg.emit(f"[ALERTA GERAL] SAFETY CAR previsto da volta {sc_start} até {sc_start+sc_duration}!")
            else:
                self.log_msg.emit("[STATUS] Bandeira verde cravada. Sem SC nesta simulação.")
            
            self.log_msg.emit("[MONTE CARLO] Computando matrizes de variância de pilotos...")
            for driver, delta in hierarquia_atual.items():
                fator_setup = np.random.normal(0, 0.35) 
                base_pace_piloto = base_pace_circuito + delta + fator_setup
                
                lap_volatility = np.random.normal(0, 0.45, laps_to_simulate)
                pace = base_pace_piloto + curva_degradacao + lap_volatility + impacto_safety_car
                
                pit_laps = []
                erro_laps = []
                dnf_lap_num = None
                
                pit_lap = int(laps_to_simulate / 2) + random.randint(-6, 6) 
                if pit_lap < laps_to_simulate:
                    tempo_pit = np.random.normal(22.0, 2.0)
                    pace[pit_lap] += tempo_pit
                    pit_laps.append(pit_lap)
                
                for _ in range(random.randint(0, 2)):
                    if random.random() < 0.25: 
                        erro_lap = random.randint(1, laps_to_simulate - 1)
                        pace[erro_lap] += random.uniform(2.0, 6.0) 
                        erro_laps.append(erro_lap)
                
                is_dnf = False
                chance_dnf = 0.02 + (self.weather_chaos * 0.08)
                if random.random() < chance_dnf:
                    dnf_lap = random.randint(5, laps_to_simulate - 5)
                    pace[dnf_lap:] = np.nan 
                    is_dnf = True
                    dnf_lap_num = dnf_lap
                    self.log_msg.emit(f"[FATAL] Piloto {driver} sofreu quebra terminal na volta {dnf_lap}. (DNF)")
                
                total_time = np.nansum(pace) if not is_dnf else float('inf')
                
                resultados[driver] = {
                    "total_time": total_time, 
                    "pace": pace.tolist(),
                    "pit_laps": pit_laps,
                    "erro_laps": erro_laps,
                    "dnf_lap": dnf_lap_num
                }
            
            self.log_msg.emit("[SISTEMA] Permutações finalizadas. Consolidando posições...")
            classificacao_lista = []
            for driver, info in sorted(resultados.items(), key=lambda item: item[1]["total_time"]):
                classificacao_lista.append({
                    "driver": driver,
                    "total_time": info["total_time"],
                    "pace": info["pace"],
                    "pit_laps": info["pit_laps"],
                    "erro_laps": info["erro_laps"],
                    "dnf_lap": info["dnf_lap"]
                })
            
            dados = {
                "gp": self.gp,
                "laps": voltas.tolist(),
                "classificacao": classificacao_lista,
                "sc_start": sc_start,
                "sc_duration": sc_duration
            }
            
            self.log_msg.emit("[SISTEMA] Processo concluído com sucesso. Plotando gráficos.")
            self.success.emit(dados)
        except Exception as e:
            self.log_msg.emit(f"[ERRO CRÍTICO] {str(e)}")
            self.error.emit(f"Falha na previsão de Machine Learning: {str(e)}")