import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
import numpy as np

def prever_degradacao_pneu(dados_laps: list):
    """
    Treina um modelo simples sob demanda para prever a perda de performance.
    Recebe a lista de dicionários vinda de obter_telemetria_piloto().
    """
    df = pd.DataFrame(dados_laps)
    
    # Filtrando apenas voltas válidas (sem safety car, pit stops de entrada, etc)
    # Voltas normais de corrida geralmente duram menos de 100 segundos na maioria das pistas  
    df_clean = df.dropna(subset=['Time', 'TyreLife', 'Compound']).copy()
    
    composto_principal = df_clean['Compound'].mode()[0]
    df_composto = df_clean[df_clean['Compound'] == composto_principal]
    
    if len(df_composto) < 10:
        return {"erro": "Dados insuficientes para treinar o modelo neste composto."}

    # Separando Variáveis 
    X = df_composto[['TyreLife']]
    y = df_composto['Time']
    
    # Criando e treinando o modelo de regressão linear
    modelo = LinearRegression()
    modelo.fit(X, y)
    
    # O coeficiente diz quantos segundos o piloto perde por volta
    degradacao_por_volta = modelo.coef_[0]
    
    # Previsão para as próximas 3 voltas baseadas na última volta registrada
    ultima_volta = df_composto['TyreLife'].max()
    proximas_voltas = np.array([[ultima_volta + 1], [ultima_volta + 2], [ultima_volta + 3]])
    previsoes = modelo.predict(proximas_voltas)
    
    return {
        "composto_analisado": composto_principal,
        "degradacao_segundos_por_volta": round(degradacao_por_volta, 3),
        "previsao_proximas_voltas": [round(p, 3) for p in previsoes]
    }