from fastapi import FastAPI, HTTPException
from justice_graph.models import BacklogPredictor, CaseDurationRegressor, DistrictBacklogPredictor
from .schemas import CaseAttributes, CaseDetails, RiskResponse, DurationResponse, DistrictBacklogRequest, DistrictBacklogResponse
import pandas as pd
import os

app = FastAPI(
    title="JusticeGraph API",
    description="Minimal ML Inference API for JusticeGraph",
    version="2.1.0"
)

# Load Models
# Models are expected to be in the 'models' directory at the project root.
# On Render, the working directory is usually the root.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODELS_DIR = os.path.join(BASE_DIR, "models")

print(f"Loading models from: {MODELS_DIR}")

# Initialize models (inference-only)
backlog_model = BacklogPredictor(model_path=os.path.join(MODELS_DIR, "backlog_model.pkl"))
duration_model = CaseDurationRegressor(model_path=os.path.join(MODELS_DIR, "duration_model.pkl"))
district_model = DistrictBacklogPredictor(data_path=os.path.join(BASE_DIR, "data", "raw", "data2.csv"))

@app.get("/")
def home():
    return {"status": "healthy", "service": "JusticeGraph Inference API. Endpoints: /predict/backlog, /predict/duration"}

@app.post("/predict/backlog", response_model=RiskResponse)
def predict_backlog(attributes: CaseAttributes):
    try:
        features = pd.DataFrame({
            'judge_strength': [attributes.judge_strength], 
            'pending_cases': [attributes.pending_cases], 
            'filing_rate': [attributes.filing_rate], 
            'disposal_rate': [attributes.disposal_rate],
            'budget_per_capita': [attributes.budget_per_capita],
            'courthall_shortfall': [attributes.courthall_shortfall]
        })

        prob = backlog_model.predict(features)[0]
        risk_level = "High" if prob > 0.7 else "Moderate" if prob > 0.3 else "Low"
        explanation = backlog_model.explain(features)
        
        return {
            "risk_score": float(prob),
            "risk_level": risk_level,
            "explanation": explanation
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict/duration", response_model=DurationResponse)
def predict_duration(details: CaseDetails):
    try:
        # Construct DataFrame from input
        features = pd.DataFrame([details.dict()])
        days = duration_model.predict(features)[0]
        return {"predicted_days": float(days)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict/district-backlog", response_model=DistrictBacklogResponse)
def predict_district_backlog(data: DistrictBacklogRequest):
    try:
        result = district_model.predict(data.dict())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
