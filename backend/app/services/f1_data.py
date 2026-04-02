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