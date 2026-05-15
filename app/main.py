from pydantic import BaseModel
from typing import Any, Dict
from fastapi import FastAPI, HTTPException  
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from app.services.f1_data import obter_telemetria_piloto, obter_resumo_corrida, comparar_telemetria
from app.services.reports import gerar_pdf_estrategia, gerar_pdf_telemetria
from app.services.ml_engine import prever_degradacao_pneu

app = FastAPI(title="F1 Pit Wall API")

# CORS para requisições do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class StrategyData(BaseModel):
    driver: str
    prediction: Dict[str, Any]
    action: str


class TelemetryDataObj(BaseModel):
    year: int
    gp: str
    driver1: str
    driver2: str
    lap_time_1: float
    lap_time_2: float
    telemetry: list

@app.get("/")
def read_root():
    return {"status": "F1 Pit Wall API está online!"}

@app.get("/api/telemetry")
def get_telemetry(year: int, gp: str, driver: str):
    data = obter_telemetria_piloto(year, gp, driver)
    
    if isinstance(data, dict) and "erro" in data:
        raise HTTPException(status_code=400, detail=data["erro"])
        
    return {"driver": driver, "gp": gp, "year": year, "laps": data}

@app.get("/api/predict-strategy")
def predict_strategy(year: int, gp: str, driver: str):
    """
    Busca os dados do piloto e aplica o modelo de Machine Learning 
    para prever a degradação e sugerir a janela de pit stop.
    """
    #. Busca os dados reais
    telemetria = obter_telemetria_piloto(year, gp, driver)
    
    if isinstance(telemetria, dict) and "erro" in telemetria:
        raise HTTPException(status_code=400, detail=telemetria["erro"])
        
    # Roda o modelo preditivo
    previsao = prever_degradacao_pneu(telemetria if isinstance(telemetria, list) else [], composto="medium")
    
    if not isinstance(previsao, dict):
        raise HTTPException(status_code=500, detail="Erro interno no modelo de previsão.")

    if "erro" in previsao:
        raise HTTPException(status_code=400, detail=previsao["erro"])
        
    # Lógica de recomendação básica
    recomendacao = "Manter o ritmo."
    if float(previsao.get("degradacao_segundos_por_volta", 0)) > 0.15:
        recomendacao = "PREPARAR PIT STOP! Degradação crítica detectada."
        
    return {
        "driver": driver,
        "prediction": previsao,
        "action": recomendacao
    }

@app.get("/api/race-summary")
def get_race_summary(year: int, gp: str):
    data = obter_resumo_corrida(year, gp)
    
    if isinstance(data, dict) and "erro" in data:
        raise HTTPException(status_code=400, detail=data["erro"])
        
    return {"gp": gp, "year": year, "results": data}

@app.get("/api/telemetry-compare")
def get_telemetry_compare(year: int, gp: str, driver1: str, driver2: str):
    data = comparar_telemetria(year, gp, driver1, driver2)
    
    if isinstance(data, dict) and "erro" in data:
        raise HTTPException(status_code=400, detail=data["erro"])
        
    return data

@app.post("/api/export-report")
def export_strategy_report(data: StrategyData):
    try:
        # data.model_dump() converte o objeto Pydantic em um dicionário para o ReportLab
        caminho_arquivo = gerar_pdf_estrategia(data.driver, data.model_dump(), data.prediction)
        return FileResponse(
            path=caminho_arquivo, 
            filename=f"relatorio_{data.driver}.pdf", 
            media_type="application/pdf"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar o PDF: {str(e)}")
    
@app.post("/api/export-telemetry-report")
def export_telemetry_report(data: TelemetryDataObj):
    try:
        ano = data.year
        gp = data.gp
        piloto = data.driver1 
        dados_dict = data.model_dump()
        caminho_arquivo = gerar_pdf_telemetria(ano, gp, piloto, dados_dict)
        
        return FileResponse(
            path=caminho_arquivo, 
            filename=f"telemetria_{data.driver1}_vs_{data.driver2}.pdf", 
            media_type="application/pdf"
        )
    except Exception as e:
        print(f"Erro: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao gerar o PDF: {str(e)}")