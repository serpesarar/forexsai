"""
Pattern Analysis Stub Router
============================
Pattern analyzer silindiği için mock endpoint.
Gerçek implementasyon daha sonra eklenecek.
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/api/patterns", tags=["patterns"])

class PatternAnalysisResponse(BaseModel):
    symbol: str
    patterns: List[dict]
    summary: str

@router.post("/analyze-patterns")
async def analyze_patterns(symbol: str):
    """Mock pattern analysis endpoint"""
    return {
        "symbol": symbol,
        "patterns": [],
        "summary": "Pattern analysis temporarily unavailable",
        "message": "Pattern analyzer v2 is being developed"
    }
