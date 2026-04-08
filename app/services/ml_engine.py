import os
import pandas as pd
import numpy as np
import fastf1
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import joblib

# Caminho para guardar o modelo treinado na pasta de projeto
MODEL_PATH = os.path.join(os.path.dirname(__file__), "modelo_pneus_rf.joblib")
ENCODER_PATH = os.path.join(os.path.dirname(__file__), "label_encoder.joblib")

def preparar_dados_treino(ano, gps):
    print(f"A descarregar dados de {len(gps)} corridas do ano {ano}...")
    laps_data = []

    for gp in gps:
        try:
            session = fastf1.get_session(ano, gp, 'R') # 
            session.load(telemetry=False, weather=True)
            
            laps = session.laps
            
            # Filtra apenas voltas válidas (sem erros, sem pit stops, etc)
            laps = laps.pick_quicklaps()
            laps = laps.dropna(subset=['LapTime', 'Compound', 'TyreLife'])
            
            # Converte o Tempo de Volta para segundos em formato decimal
            laps['LapTime_s'] = laps['LapTime'].dt.total_seconds()
            
            df = laps[['Driver', 'Compound', 'TyreLife', 'LapNumber', 'LapTime_s']].copy()
            df['GP'] = gp
            
            laps_data.append(df)
            print(f"[OK] Dados de {gp} extraídos com sucesso.")
        except Exception as e:
            print(f"[ERRO] Falha ao extrair {gp}: {str(e)}")

    if not laps_data:
        raise ValueError("Nenhum dado foi extraído com sucesso.")

    # Junta todas as corridas num mega DataFrame
    dataset = pd.concat(laps_data, ignore_index=True)
    return dataset

def treinar_modelo_degradacao():
    """
    Função principal para treinar a Rede de Machine Learning.
    """
    gps_treino = ['Bahrain', 'Japan', 'Australia', 'Azerbaijan', 'Miami', 'Monaco', 'Brazil', 'Abu Dhabi']
    
    df = preparar_dados_treino(2025, gps_treino)
    
    print("\nA processar matriz de características (Feature Engineering)...")
    
    le = LabelEncoder()
    df['Compound_Encoded'] = le.fit_transform(df['Compound'])
    
    # Define o que a IA vai estudar (X) e o que ela tem de projetar (y)
    # X = Idade do Composto e Qual é o Composto
    X = df[['TyreLife', 'Compound_Encoded']]
    # y = O tempo de volta (o ritmo)
    y = df['LapTime_s']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("A iniciar o treino do algoritmo Random Forest (Isto pode demorar alguns segundos)...")
    # Cria o algoritmo com 500 árvores de decisão
    modelo = RandomForestRegressor(n_estimators=500, max_depth=10, random_state=42, n_jobs=-1)
    modelo.fit(X_train, y_train)
    
    # Avalia a precisão do modelo
    score = modelo.score(X_test, y_test)
    print(f"Treino concluído! Precisão (R² Score): {score:.2f}")
    
    # Guarda o modelo treinado no disco para o desktop app usar instantaneamente
    joblib.dump(modelo, MODEL_PATH)
    joblib.dump(le, ENCODER_PATH)
    print(f"Modelo guardado em: {MODEL_PATH}")


def prever_degradacao_pneu(voltas_a_simular, composto):
    if not os.path.exists(MODEL_PATH) or not os.path.exists(ENCODER_PATH):
        return {"erro": "O modelo de IA ainda não foi treinado. Execute ml_engine.py primeiro."}
    
    # Carrega o cérebro
    modelo = joblib.load(MODEL_PATH)
    le = joblib.load(ENCODER_PATH)
    
    try:
        composto_enc = le.transform([composto])[0]
    except ValueError:
        # Se pedirem um pneu estranho, assume MEDIUM como segurança
        composto_enc = le.transform(['MEDIUM'])[0]
    
    tempos_previstos = []
    
    # Prevê o tempo de volta para cada idade do composto que for simular
    for idade in voltas_a_simular:
        # Passa as características do composto
        features = pd.DataFrame([[idade, composto_enc]], columns=['TyreLife', 'Compound_Encoded'])
        tempo_previsto = modelo.predict(features)[0]
        tempos_previstos.append(round(tempo_previsto, 3))
        
    return tempos_previstos

if __name__ == "__main__":
    print("=== INICIANDO O CENTRO DE TREINAMENTO DA F1 ===")
    treinar_modelo_degradacao()