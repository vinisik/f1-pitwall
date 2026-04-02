from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.services.f1_data import obter_telemetria_piloto

app = FastAPI(title="F1 Strategy Engine API")

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
    return {"status": "F1 Strategy API está online!"}

@app.get("/api/telemetry")
def get_telemetry(year: int, gp: str, driver: str):
    data = obter_telemetria_piloto(year, gp, driver)
    
    if "erro" in data:
        raise HTTPException(status_code=400, detail=data["erro"])
        
    return {"driver": driver, "gp": gp, "year": year, "laps": data}

@app.post("/api/export-report")
def export_strategy_report():
    return {"status": "Geração de PDF em desenvolvimento"}