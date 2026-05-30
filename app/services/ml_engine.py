import os
import pandas as pd
import numpy as np
import fastf1
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import joblib
import warnings
import datetime

warnings.filterwarnings("ignore", category=UserWarning)

MODEL_PATH = os.path.join(os.path.dirname(__file__), "modelo_pneus_rf.joblib")
ENCODER_PATH = os.path.join(os.path.dirname(__file__), "label_encoder.joblib")

def preparar_dados_treino(ano, gps):
    print(f"A descarregar dados de {len(gps)} corridas do ano {ano}...")
    laps_data = []

    for gp in gps:
        try:
            session = fastf1.get_session(ano, gp, 'R')
            session.load(telemetry=False, weather=True)
            
            laps = session.laps
            laps = laps.pick_quicklaps()
            laps = laps.dropna(subset=['LapTime', 'Compound', 'TyreLife'])
            
            laps['LapTime_s'] = laps['LapTime'].dt.total_seconds()
            
            df = laps[['Driver', 'Compound', 'TyreLife', 'LapNumber', 'LapTime_s']].copy()
            df['GP'] = gp
            
            laps_data.append(df)
            print(f"[OK] Dados de {gp} extraídos com sucesso.")
        except Exception as e:
            print(f"[ERRO] Falha ao extrair {gp}: {str(e)}")

    if not laps_data:
        raise ValueError("Nenhum dado foi extraído com sucesso.")

    return pd.concat(laps_data, ignore_index=True)

def treinar_modelo_degradacao():
    ano_atual = datetime.datetime.now().year
    
    print(f"A consultar o calendário oficial da temporada {ano_atual}...")
    
    # Busca o calendário completo do ano atual na API
    schedule = fastf1.get_event_schedule(ano_atual)
    hoje = pd.Timestamp.now()
    
    # Filtra apenas os eventos que já aconteceram e remove testes de pré-temporada
    corridas_concluidas = schedule[(schedule['EventDate'] < hoje) & (schedule['EventFormat'] != 'testing')]
    gps_treino = corridas_concluidas['EventName'].tolist()
    
    if not gps_treino:
        print(f"Nenhuma corrida encontrada em {ano_atual} até o momento. Retornando ao calendário do ano anterior.")
        ano_atual -= 1
        schedule = fastf1.get_event_schedule(ano_atual)
        corridas_concluidas = schedule[(schedule['EventDate'] < hoje) & (schedule['EventFormat'] != 'testing')]
        gps_treino = corridas_concluidas['EventName'].tolist()

    print(f"Foram identificadas {len(gps_treino)} etapas concluídas. Iniciando ingestão de dados...")
    
    df = preparar_dados_treino(ano_atual, gps_treino)
    print("\nA processar matriz de características (Feature Engineering)...")
    
    le = LabelEncoder()
    df['Compound_Encoded'] = le.fit_transform(df['Compound'])
    
    X = df[['TyreLife', 'Compound_Encoded']]
    y = df['LapTime_s']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("A iniciar o treino do algoritmo Random Forest com os regulamentos mais recentes...")
    modelo = RandomForestRegressor(n_estimators=500, max_depth=10, random_state=42, n_jobs=-1)
    modelo.fit(X_train, y_train)
    
    score = modelo.score(X_test, y_test)
    print(f"Treino concluído! Precisão (R² Score): {score:.2f}")
    
    joblib.dump(modelo, MODEL_PATH)
    joblib.dump(le, ENCODER_PATH)
    print(f"Modelo guardado em: {MODEL_PATH}")

def prever_degradacao_pneu(voltas_a_simular, composto):
    """
    Prevê o tempo de volta com base no composto e na idade do pneu.
    """
    if not os.path.exists(MODEL_PATH) or not os.path.exists(ENCODER_PATH):
        return {"erro": "O modelo de IA ainda não foi treinado. Execute ml_engine.py primeiro."}
    
    modelo = joblib.load(MODEL_PATH)
    le = joblib.load(ENCODER_PATH)
    
    try:
        composto_enc = le.transform([composto])[0]
    except ValueError:
        composto_enc = le.transform(['MEDIUM'])[0]
    
    # Prepara o DataFrame de entrada para a IA para evitar alertas de Warning do Scikit
    features = pd.DataFrame({
        'TyreLife': voltas_a_simular,
        'Compound_Encoded': [composto_enc] * len(voltas_a_simular)
    })
    
    tempos_previstos = modelo.predict(features)
    
    return [round(t, 3) for t in tempos_previstos]

if __name__ == "__main__":
    print("=== INICIANDO PAINEL DE ESTATÍSTICAS ===")
    treinar_modelo_degradacao()