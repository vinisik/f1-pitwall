from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from app.services.f1_data import obter_telemetria_piloto
from app.services.reports import gerar_pdf_estrategia
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
    previsao = prever_degradacao_pneu(telemetria if isinstance(telemetria, list) else [])
    
    if "erro" in previsao:
         raise HTTPException(status_code=400, detail=previsao["erro"])
         
    # Lógica de recomendação básica
    recomendacao = "Manter o ritmo."
    if float(previsao["degradacao_segundos_por_volta"]) > 0.15:
        recomendacao = "PREPARAR PIT STOP! Degradação crítica detectada."
        
    return {
        "driver": driver,
        "prediction": previsao,
        "action": recomendacao
    }

@app.post("/api/export-report")
def export_strategy_report():
    """
    Gera o relatório com o logo no topo de todas as páginas e retorna o arquivo.
    """
    dados_mock = {"status": "ok"} 
    
    try:
        caminho_arquivo = gerar_pdf_estrategia(dados_mock)
        return FileResponse(
            path=caminho_arquivo, 
            filename="relatorio_oficial.pdf", 
            media_type="application/pdf"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar o PDF: {str(e)}")