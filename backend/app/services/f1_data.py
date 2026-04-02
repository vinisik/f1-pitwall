import fastf1
import pandas as pd
import os

# Cria o diretório de cache
CACHE_DIR = 'cache_f1'
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

fastf1.Cache.enable_cache(CACHE_DIR)

def obter_telemetria_piloto(ano: int, gp: str, piloto: str, sessao: str = 'R'):
    """
    Baixa os dados da corrida e retorna a telemetria básica de um piloto.
    """
    try:
        session = fastf1.get_session(ano, gp, sessao)
        session.load(weather=False, messages=False) # Carregamento mais rápido
        
        laps = session.laps.pick_driver(piloto)
        
        # Filtra as colunas mais importantes para a estratégia
        df = laps[['LapNumber', 'Time', 'Sector1Time', 'Sector2Time', 'Sector3Time', 'Compound', 'TyreLife']]
        
        # Converte tempos para segundos em formato float para o JSON
        for col in ['Time', 'Sector1Time', 'Sector2Time', 'Sector3Time']:
            df[col] = df[col].dt.total_seconds()
            
        # Preenche valores nulos com None para compatibilidade com JSON
        df = df.where(pd.notnull(df), None)
        
        return df.to_dict(orient='records')
        
    except Exception as e:
        return {"erro": str(e)}