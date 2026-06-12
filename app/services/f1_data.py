import fastf1
import pandas as pd
import numpy as np
import os
from datetime import datetime

CACHE_DIR = 'cache_f1'
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

fastf1.Cache.enable_cache(CACHE_DIR)

def obter_comportamento_historico_pista(ano_alvo: int, gp: str) -> dict:
    """
    Tenta extrair o comportamento histórico da pista para o GP e ano especificados.
     Se os dados do ano atual não estiverem disponíveis, retrocede para o ano anterior.
    """
    anos_para_tentar = [ano_alvo, ano_alvo - 1]
    
    for ano in anos_para_tentar:
        try:
            print(f"Tentando extrair baseline da pista de {gp} ({ano})...")
            session = fastf1.get_session(ano, gp, 'R')
            session.load(telemetry=False, weather=False, messages=False)
            laps = session.laps
            
            if laps.empty:
                continue # Pula para a tentativa do ano anterior
                
            voltas_validas = laps.pick_track_status('1')
            stints = voltas_validas[['Driver', 'Stint', 'Compound', 'LapNumber']].dropna()
            
            tamanho_stints = stints.groupby(['Driver', 'Stint', 'Compound'])['LapNumber'].count().reset_index()
            tamanho_stints.rename(columns={'LapNumber': 'Voltas_Sobrevividas'}, inplace=True)
            medias_pista = tamanho_stints.groupby('Compound')['Voltas_Sobrevividas'].median().to_dict()
            
            voltas_rapidas = voltas_validas.pick_quicklaps()
            base_pace = voltas_rapidas['LapTime'].dt.total_seconds().median()
            
            if pd.isna(base_pace):
                base_pace = 80.0 
                
            total_voltas = session.total_laps if session.total_laps else 50
            
            print(f"Sucesso! Base de dados ancorada em {ano}.")
            return {
                'SOFT': int(medias_pista.get('SOFT', 15)),
                'MEDIUM': int(medias_pista.get('MEDIUM', 25)),
                'HARD': int(medias_pista.get('HARD', 38)),
                'TOTAL_LAPS': total_voltas,
                'BASE_PACE': round(base_pace, 2)
            }
            
        except Exception as e:
            print(f"Dados indisponíveis para {ano}. Motivo: {e}")
            continue
            
    print(f"Alerta: Falha na extração histórica. Assumindo parâmetros padrão para {gp}.")
    return {'SOFT': 15, 'MEDIUM': 25, 'HARD': 38, 'TOTAL_LAPS': 50, 'BASE_PACE': 80.0}

def obter_telemetria_piloto(ano: int, gp: str, piloto: str, sessao: str = 'R'):
    """Busca os dados de telemetria para um piloto específico em um GP e sessão determinados."""
    try:
        session = fastf1.get_session(ano, gp, sessao)
        session.load(laps=True, telemetry=False, weather=False, messages=False)
        laps = session.laps.pick_drivers(piloto)
        
        if laps.empty:
            return {"erro": f"Nenhum dado encontrado para o piloto {piloto} no GP {gp} ({ano})."}

        colunas = ['LapNumber', 'Time', 'Sector1Time', 'Sector2Time', 'Sector3Time', 'Compound', 'TyreLife', 'FreshTyre']
        df = laps[colunas].copy()
        
        cols_tempo = ['Time', 'Sector1Time', 'Sector2Time', 'Sector3Time']
        for col in cols_tempo: df[col] = df[col].dt.total_seconds()
            
        df = df.replace([np.inf, -np.inf, np.nan], None)
        return df.to_dict(orient='records')
        
    except Exception as e:
        print(f"Erro interno no serviço F1 Data: {e}")
        return {"erro": f"Falha ao processar telemetria: {str(e)}"}
    
def obter_resumo_corrida(ano: int, gp: str):
    """Gera um resumo detalhado da corrida, incluindo posições, stints, pit stops e gráficos de desempenho."""
    try:
        session = fastf1.get_session(ano, gp, 'R')
        session.load(telemetry=False, weather=False, messages=False)
        
        resultados = []
        posicoes = {}
        pace = {}
        speedtrap = {}
        pitstops = []
        
        laps = session.laps
        
        for drv in session.results['Abbreviation']:
            drv_laps = laps.pick_drivers(drv)
            if drv_laps.empty: continue
                
            try:
                row = session.results[session.results['Abbreviation'] == drv]
                if row.empty: continue
                grid_pos = int(float(row['GridPosition'].values[0]))
                final_pos = int(float(row['Position'].values[0]))
            except (ValueError, IndexError, KeyError):
                continue

            stints = []
            for stint, group in drv_laps.groupby('Stint'):
                compostos_validos = group['Compound'].dropna()
                composto = compostos_validos.iloc[0] if not compostos_validos.empty else "UNKNOWN"
                voltas_stint = len(group)
                try:
                    stint_int = int(float(str(stint)))
                except (ValueError, TypeError):
                    stint_int = len(stints) + 1
                stints.append({"stint": stint_int, "composto": str(composto), "voltas": int(voltas_stint)})
            
            saldo_posicoes = grid_pos - final_pos
            resultados.append({
                "piloto": str(drv), "largada": grid_pos, "chegada": final_pos,
                "saldo_posicoes": saldo_posicoes, "stints": stints
            })
            
            # Gráfico de Posições
            pos_laps = drv_laps['LapNumber'].tolist()
            pos_vals = drv_laps['Position'].tolist()
            posicoes[str(drv)] = {"laps": pos_laps, "pos": pos_vals}
            
            # Gráfico de Ritmo (Boxplot)
            # Filtra apenas voltas limpas (Status 1) para o pace real
            paces = drv_laps.pick_track_status('1')['LapTime'].dt.total_seconds().dropna().tolist()
            pace[str(drv)] = paces
            
            # Gráfico de Speed Trap 
            st_speeds = drv_laps['SpeedST'].dropna()
            speedtrap[str(drv)] = float(st_speeds.max()) if not st_speeds.empty else 0.0
            
            # Tempos de Pit Stop 
            # Calcula o tempo total no Pit Lane (Diferença entre Pit In e Pit Out)
            in_laps = drv_laps[drv_laps['PitInTime'].notna()]
            for _, lap in in_laps.iterrows():
                lap_num = lap['LapNumber']
                out_lap = drv_laps[drv_laps['LapNumber'] == lap_num + 1]
                if not out_lap.empty:
                    out_lap = out_lap.iloc[0]
                    if pd.notna(lap['PitInTime']) and pd.notna(out_lap['PitOutTime']):
                        pit_time = (out_lap['PitOutTime'] - lap['PitInTime']).total_seconds()
                        pitstops.append({"piloto": str(drv), "volta": int(lap_num), "tempo": float(pit_time)})
            
        resultados.sort(key=lambda x: x['chegada'] if x['chegada'] > 0 else 99)
        
        # Retorna todos os dados de telemetria
        return {
            "tabela": resultados,
            "posicoes": posicoes,
            "pace": pace,
            "pitstops": pitstops,
            "speedtrap": speedtrap
        }
        
    except Exception as e:
        print(f"Erro no resumo da corrida: {e}")
        return {"erro": f"Falha ao gerar análise da corrida: {str(e)}"}
    
def comparar_telemetria(ano: int, gp: str, piloto1: str, piloto2: str, sessao: str = 'R', lap_num1=None, lap_num2=None):
    try:
        session = fastf1.get_session(ano, gp, sessao)
        session.load(telemetry=True, weather=False, messages=False)
        
        laps1 = session.laps.pick_drivers(piloto1)
        laps2 = session.laps.pick_drivers(piloto2)
        
        if laps1.empty or laps2.empty: return {"erro": "Piloto não encontrado ou sem voltas."}

        # Filtro de voltas
        if lap_num1:
            try: lap1 = laps1[laps1['LapNumber'] == float(lap_num1)].iloc[0]
            except: lap1 = laps1.pick_fastest()
        else:
            lap1 = laps1.pick_fastest()

        if lap_num2:
            try: lap2 = laps2[laps2['LapNumber'] == float(lap_num2)].iloc[0]
            except: lap2 = laps2.pick_fastest()
        else:
            lap2 = laps2.pick_fastest()

        # Validação de voltas
        if lap1 is None or lap1.empty or pd.isna(lap1.get('LapTime')): return {"erro": f"Volta inválida para {piloto1}."}
        if lap2 is None or lap2.empty or pd.isna(lap2.get('LapTime')): return {"erro": f"Volta inválida para {piloto2}."}

        colunas_alvo = ['Distance', 'Speed', 'Throttle', 'Brake', 'nGear', 'RPM', 'X', 'Y']
        
        # Renomeia as colunas para evitar conflitos e facilitar a comparação
        tel1 = lap1.get_telemetry()[colunas_alvo].rename(columns={col: f'{col}_{piloto1}' for col in colunas_alvo if col != 'Distance'})
        tel2 = lap2.get_telemetry()[colunas_alvo].rename(columns={col: f'{col}_{piloto2}' for col in colunas_alvo if col != 'Distance'})
        
        tel1 = tel1.sort_values('Distance')
        tel2 = tel2.sort_values('Distance')
        
        merged = pd.merge_asof(tel1, tel2, on='Distance', direction='nearest')
        merged = merged.iloc[::3, :] 
        
        merged = merged.replace([np.inf, -np.inf], np.nan)
        merged = merged.where(pd.notnull(merged), None)
        
        return {
            "driver1": piloto1, "driver2": piloto2,
            "lap_time_1": round(lap1['LapTime'].total_seconds(), 3),
            "lap_time_2": round(lap2['LapTime'].total_seconds(), 3),
            "telemetry": merged.to_dict(orient='records')
        }
    except Exception as e:
        print(f"Erro na telemetria: {e}")
        return {"erro": f"Falha ao processar telemetria bruta: {str(e)}"}
    

def obter_hierarquia_atual(ano_alvo: int, tentativas: int = 0) -> dict:
    """
    Busca a última corrida concluída para extrair o pace das equipes.
     Se a corrida do ano atual não estiver disponível, retrocede para o ano anterior."""
    if tentativas > 2:
        print("Limite de recursão atingido. Abortando busca de hierarquia.")
        return {}
        
    try:
        try:
            schedule = fastf1.get_event_schedule(ano_alvo)
        except Exception:
            print(f"Calendário de {ano_alvo} indisponível. Retrocedendo...")
            return obter_hierarquia_atual(ano_alvo - 1, tentativas + 1)
            
        hoje = pd.Timestamp.now(tz='UTC')
        
        # Garantir que as datas estejam em UTC para comparação correta
        datas_eventos = schedule['EventDate']
        if datas_eventos.dt.tz is None:
            schedule['EventDate'] = datas_eventos.dt.tz_localize('UTC')
        else:
            schedule['EventDate'] = datas_eventos.dt.tz_convert('UTC')
            
        corridas_concluidas = schedule[(schedule['EventDate'] < hoje) & (schedule['EventFormat'] != 'testing')]
        
        if corridas_concluidas.empty:
            print(f"Nenhuma corrida validada em {ano_alvo} ainda. Buscando ano anterior.")
            return obter_hierarquia_atual(ano_alvo - 1, tentativas + 1)
            
        ultima_etapa = corridas_concluidas.iloc[-1]['EventName']
        print(f"Calculando Power Ranking baseado na última etapa validada: {ultima_etapa} ({ano_alvo})...")
        
        session = fastf1.get_session(ano_alvo, ultima_etapa, 'R')
        session.load(telemetry=False, weather=False, messages=False)
        
        if session.laps.empty:
            print(f"Sem voltas registradas em {ultima_etapa}. Tentando etapa anterior...")
            return obter_hierarquia_atual(ano_alvo - 1, tentativas + 1)
        
        # Extrai as matrizes de voltas rápidas e cria uma cópia para manipulação
        voltas = session.laps.pick_track_status('1').pick_quicklaps().copy()
        
        # Converte os tempos de volta para segundos
        voltas['LapTime_s'] = voltas['LapTime'].dt.total_seconds()
        
        # Ritmo mediano da corrida 
        pace_geral = voltas['LapTime_s'].median()
        
        # Ritmo mediano individual por piloto 
        pace_pilotos = voltas.groupby('Driver')['LapTime_s'].median()
        
        hierarquia = {}
        for driver, pace in pace_pilotos.items():
            if pd.notna(pace):
                hierarquia[str(driver)] = round(pace - pace_geral, 3)
                
        if not hierarquia:
            print("Grid resultante vazio. Acionando contingência temporal.")
            return obter_hierarquia_atual(ano_alvo - 1, tentativas + 1)
            
        print(f"Hierarquia do grid carregada com sucesso! ({len(hierarquia)} pilotos)")
        return hierarquia
        
    except Exception as e:
        print(f"Erro não previsto ao calcular hierarquia dinâmica: {e}")
        return obter_hierarquia_atual(ano_alvo - 1, tentativas + 1)
    
def obter_corridas_futuras(ano):
    """
    Conecta à API do FastF1 para buscar o calendário oficial do ano indicado
    e retorna apenas os GPs que ainda não aconteceram.
    """
    try:
        schedule = fastf1.get_event_schedule(ano)
        hoje = datetime.now()
        gps_futuros = []
        
        for index, row in schedule.iterrows():
            if row['EventFormat'] == 'testing':
                continue
                
            data_corrida = row['EventDate']
            
            if data_corrida >= hoje:
                country = row['Country']
                
                location = str(row.get('Location', ''))
                event_name = str(row.get('EventName', ''))
                
                # Padroniza o nome do país
                if country == "United States": country = "USA"
                if country == "UK": country = "Great Britain"
                if country == "United Arab Emirates": country = "Abu Dhabi"
                
                # Tratamento para o GP da Espanha 
                if country == "Spain":
                    if "Madrid" in location or "Madrid" in event_name:
                        country = "Madrid"
                    else:
                        country = "Barcelona"
                        
                # Tratamento para Imola e Monza
                if country == "Italy" and ("Imola" in location or "Emilia Romagna" in event_name):
                    country = "Emilia Romagna"
                elif country == "Italy":
                    country = "Italy" 
                
                if not gps_futuros or gps_futuros[-1] != country:
                    gps_futuros.append(country)
                
        return gps_futuros if gps_futuros else ["Temporada Encerrada"]
        
    except Exception as e:
        print(f"Erro ao buscar calendário na API: {e}")
        return ["Erro de Conexão"]

def verificar_sprint(ano: int, gp: str) -> bool:
    """
    Consulta o calendário oficial da FIA via FastF1 para verificar
    se o formato do evento contém sessões de Sprint.
    """
    try:
        evento = fastf1.get_event(ano, gp)
        formato = str(evento.EventFormat).lower()
        return 'sprint' in formato
    except Exception:
        # Se houver erro, assume que não é sprint para evitar falhas 
        return False