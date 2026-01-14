"""
API Router for AI-powered Signal Analysis
Combines ML predictions with Claude AI review
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

router = APIRouter(prefix="/api/ai-analysis", tags=["ai-analysis"])


class TASnapshot(BaseModel):
    close: float
    ema_20: float
    ema_50: float
    ema_200: float
    rsi_14: float
    macd_hist: float
    atr_14: float
    boll_zscore: float


class KeyLevel(BaseModel):
    type: str
    price: float
    distance: str


class MLPrediction(BaseModel):
    symbol: str
    direction: str
    confidence: float
    probability_up: float
    probability_down: float
    target_pips: float
    stop_pips: float
    risk_reward: float
    entry_price: float
    target_price: float
    stop_price: float
    technical_score: float
    momentum_score: float
    trend_score: float
    volatility_regime: str
    reasoning: List[str]
    key_levels: List[KeyLevel]


class ClaudeAnalysis(BaseModel):
    symbol: str
    ml_direction: str
    claude_direction: str
    claude_confidence: float
    agreement: bool
    general_assessment: str
    strengths: List[str]
    weaknesses: List[str]
    recommended_entry: float
    recommended_sl: float
    recommended_tp: float
    position_size_suggestion: str
    key_observations: List[str]
    risk_factors: List[str]
    timestamp: str
    model_used: str


class FullAnalysisResponse(BaseModel):
    ml_prediction: MLPrediction
    claude_analysis: ClaudeAnalysis
    ta_snapshot: TASnapshot


class DetailedAnalysisResponse(BaseModel):
    symbol: str
    context: Dict[str, Any]
    analysis: Dict[str, Any]


@router.get("/{symbol}", response_model=FullAnalysisResponse)
async def get_ai_analysis(symbol: str):
    """
    Get full AI analysis for a symbol.
    
    Combines:
    1. ML model prediction (LightGBM trained on historical patterns)
    2. Claude AI review (independent assessment of signals + TA data)
    3. Technical analysis snapshot
    """
    from backend.services.claude_signal_analyzer import get_full_analysis
    
    result = await get_full_analysis(symbol)
    
    return FullAnalysisResponse(
        ml_prediction=MLPrediction(**result["ml_prediction"]),
        claude_analysis=ClaudeAnalysis(**result["claude_analysis"]),
        ta_snapshot=TASnapshot(**result["ta_snapshot"])
    )


@router.get("/", response_model=List[FullAnalysisResponse])
async def get_all_ai_analysis():
    """Get AI analysis for both NASDAQ and XAUUSD."""
    from backend.services.claude_signal_analyzer import get_full_analysis
    
    nasdaq = await get_full_analysis("NDX.INDX")
    xauusd = await get_full_analysis("XAUUSD")
    
    return [
        FullAnalysisResponse(
            ml_prediction=MLPrediction(**nasdaq["ml_prediction"]),
            claude_analysis=ClaudeAnalysis(**nasdaq["claude_analysis"]),
            ta_snapshot=TASnapshot(**nasdaq["ta_snapshot"])
        ),
        FullAnalysisResponse(
            ml_prediction=MLPrediction(**xauusd["ml_prediction"]),
            claude_analysis=ClaudeAnalysis(**xauusd["claude_analysis"]),
            ta_snapshot=TASnapshot(**xauusd["ta_snapshot"])
        ),
    ]


@router.get("/detailed/{symbol}", response_model=DetailedAnalysisResponse)
async def get_detailed_ai_analysis(symbol: str):
    from backend.services.detailed_ai_analysis_service import get_detailed_analysis

    result = await get_detailed_analysis(symbol)
    return DetailedAnalysisResponse(
        symbol=result.get("symbol", symbol),
        context=result.get("context", {}),
        analysis=result.get("analysis", {}),
    )
