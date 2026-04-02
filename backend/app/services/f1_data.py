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