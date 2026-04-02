import fastf1
import pandas as pd
import numpy as np
import os

# Configuração de Cache para evitar downloads repetidos
CACHE_DIR = 'cache_f1'
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

fastf1.Cache.enable_cache(CACHE_DIR)

def obter_telemetria_piloto(ano: int, gp: str, piloto: str, sessao: str = 'R'):
    """
    Consome a API do FastF1, limpa os dados de telemetria e os formata
    para serem compatíveis com JSON (removendo NaNs e convertendo Timedeltas).
    """
    try:
        # Carrega a sessão 
        session = fastf1.get_session(ano, gp, sessao)
        
        session.load(laps=True, telemetry=False, weather=False, messages=False)
        
        # Filtra as voltas do piloto solicitado 
        laps = session.laps.pick_driver(piloto)
        
        if laps.empty:
            return {"erro": f"Nenhum dado encontrado para o piloto {piloto} no GP {gp} ({ano})."}

        # Seleciona colunas essenciais para a Engine de Estratégia
        colunas = [
            'LapNumber', 'Time', 'Sector1Time', 'Sector2Time', 
            'Sector3Time', 'Compound', 'TyreLife', 'FreshTyre'
        ]
        df = laps[colunas].copy()
        
        # Conversão de Timedeltas para Segundos
        cols_tempo = ['Time', 'Sector1Time', 'Sector2Time', 'Sector3Time']
        for col in cols_tempo:
            df[col] = df[col].dt.total_seconds()
            
        # Substitui NaN e Inf por None.
        df = df.replace([np.inf, -np.inf, np.nan], None)
        
        # Converte para lista de dicionários 
        return df.to_dict(orient='records')
        
    except Exception as e:
        print(f"Erro interno no serviço F1 Data: {e}")
        return {"erro": f"Falha ao processar telemetria: {str(e)}"}
    
def obter_resumo_corrida(ano: int, gp: str):
    """
    Analisa a corrida inteira, retornando posições, ganhos/perdas 
    e os pneus usados (stints) por todos os pilotos.
    """
    try:
        session = fastf1.get_session(ano, gp, 'R')
        session.load(telemetry=False, weather=False, messages=False)
        
        resultados = []
        
        # Iterar sobre todos os pilotos que participaram da sessão
        for drv in session.results['Abbreviation']:
            drv_laps = session.laps.pick_driver(drv)
            if drv_laps.empty:
                continue
                
            # Extração de Posições (usando float para evitar erros de tipos do Pandas, depois convertendo para int)
            try:
                grid_pos = int(float(session.results.loc[session.results['Abbreviation'] == drv, 'GridPosition'].values[0]))
                final_pos = int(float(session.results.loc[session.results['Abbreviation'] == drv, 'Position'].values[0]))
            except ValueError:
                # Pilotos que não largaram ou não classificaram corretamente
                continue

            # Agrupamento de Stints (Estratégia de Pneus)
            stints = []
            for stint, group in drv_laps.groupby('Stint'):
                composto = group['Compound'].iloc[0]
                voltas_stint = len(group)
                if pd.notna(composto): # Ignorar stints inválidos
                    stints.append({
                        "stint": int(stint),
                        "composto": str(composto),
                        "voltas": int(voltas_stint)
                    })
            
            saldo_posicoes = grid_pos - final_pos
            
            resultados.append({
                "piloto": str(drv),
                "largada": grid_pos,
                "chegada": final_pos,
                "saldo_posicoes": saldo_posicoes,
                "stints": stints
            })
            
        # Ordenar os resultados pela posição de chegada
        resultados.sort(key=lambda x: x['chegada'] if x['chegada'] > 0 else 99)
        return resultados
        
    except Exception as e:
        print(f"Erro no resumo da corrida: {e}")
        return {"erro": f"Falha ao gerar análise da corrida: {str(e)}"}
    

def comparar_telemetria(ano: int, gp: str, piloto1: str, piloto2: str, sessao: str = 'R'):
    """
    Extrai a volta mais rápida de dois pilotos na corrida, 
    cruza a distância e compara dados completos de telemetria (Velocidade, Acelerador, Freio, Marcha, RPM).
    """
    try:
        session = fastf1.get_session(ano, gp, sessao)
        session.load(telemetry=True, weather=False, messages=False)
        
        # Extrai as voltas primeiro para validar se existem
        laps1 = session.laps.pick_driver(piloto1)
        laps2 = session.laps.pick_driver(piloto2)
        
        if laps1.empty or laps2.empty:
            return {"erro": "Piloto não encontrado ou sem voltas para comparar."}

        lap1 = laps1.pick_fastest()
        lap2 = laps2.pick_fastest()

        if lap1 is None or lap1.empty or pd.isna(lap1.get('LapTime')):
            return {"erro": f"Não foi possível encontrar uma volta rápida válida para {piloto1}."}
        if lap2 is None or lap2.empty or pd.isna(lap2.get('LapTime')):
            return {"erro": f"Não foi possível encontrar uma volta rápida válida para {piloto2}."}

        # Definindo as colunas alvo da telemetria bruta
        colunas_alvo = ['Distance', 'Speed', 'Throttle', 'Brake', 'nGear', 'RPM']
        
        # Extraindo e renomeando dinamicamente para o Piloto 1
        tel1 = lap1.get_telemetry()[colunas_alvo].rename(columns={
            'Speed': f'Speed_{piloto1}',
            'Throttle': f'Throttle_{piloto1}',
            'Brake': f'Brake_{piloto1}',
            'nGear': f'nGear_{piloto1}',
            'RPM': f'RPM_{piloto1}'
        })
        
        # Extraindo e renomeando dinamicamente para o Piloto 2
        tel2 = lap2.get_telemetry()[colunas_alvo].rename(columns={
            'Speed': f'Speed_{piloto2}',
            'Throttle': f'Throttle_{piloto2}',
            'Brake': f'Brake_{piloto2}',
            'nGear': f'nGear_{piloto2}',
            'RPM': f'RPM_{piloto2}'
        })
        
        # Ordenar pela distância percorrida na pista
        tel1 = tel1.sort_values('Distance')
        tel2 = tel2.sort_values('Distance')
        
        # Junta os dados alinhando a distância mais próxima
        merged = pd.merge_asof(tel1, tel2, on='Distance', direction='nearest')
        
        # Reduzir a resolução para evitar sobrecarga de dados no front (1 a cada 3 pontos)
        merged = merged.iloc[::3, :]
        
        # Tratamento final de Infs e NaNs antes do JSON
        merged = merged.replace([np.inf, -np.inf], np.nan)
        merged = merged.where(pd.notnull(merged), None)
        
        return {
            "driver1": piloto1,
            "driver2": piloto2,
            "lap_time_1": round(lap1['LapTime'].total_seconds(), 3),
            "lap_time_2": round(lap2['LapTime'].total_seconds(), 3),
            "telemetry": merged.to_dict(orient='records')
        }
        
    except Exception as e:
        print(f"Erro na telemetria: {e}")
        return {"erro": f"Falha ao processar telemetria bruta: {str(e)}"}