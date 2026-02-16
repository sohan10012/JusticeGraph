from pydantic import BaseModel
from typing import Optional, List

# --- Request Models ---

class CaseAttributes(BaseModel):
    judge_strength: int
    pending_cases: int
    filing_rate: float
    disposal_rate: float
    budget_per_capita: float
    courthall_shortfall: float

class CaseDetails(BaseModel):
    case_type_encoded: int
    priority_encoded: int
    act_count: int
    court_load: float

class DistrictBacklogRequest(BaseModel):
    state: str
    district: str
    case_type: str

# --- Response Models ---

class RiskResponse(BaseModel):
    risk_score: float
    risk_level: str
    explanation: dict
    
class DistrictBacklogResponse(BaseModel):
    estimated_duration_days: float
    estimated_duration_years: float
    confidence: str
    explanation: str

class DurationResponse(BaseModel):
    predicted_days: float
