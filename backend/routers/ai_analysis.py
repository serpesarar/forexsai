"""
API Router for AI-powered Signal Analysis
Combines ML predictions with Claude AI review
"""
import asyncio
from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict
from typing import Any, Dict, List, Optional

router = APIRouter(prefix="/api/ai-analysis", tags=["ai-analysis"])


class TASnapshot(BaseModel):
    model_config = ConfigDict(extra="allow")
    close: float
    ema_20: float
    ema_50: float
    ema_200: float
    rsi_14: float
    macd_hist: float
    atr_14: float
    boll_zscore: float


class KeyLevel(BaseModel):
    model_config = ConfigDict(extra="allow")
    type: str
    price: float
    distance: str


class MLPrediction(BaseModel):
    model_config = ConfigDict(extra="allow")
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
    model_config = ConfigDict(extra="allow")
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
    model_config = ConfigDict(extra="allow")
    ml_prediction: MLPrediction
    claude_analysis: ClaudeAnalysis
    ta_snapshot: TASnapshot


class DetailedAnalysisResponse(BaseModel):
    symbol: str
    context: Dict[str, Any]
    analysis: Dict[str, Any]


@router.get("/{symbol}", response_model=FullAnalysisResponse)
async def get_ai_analysis(symbol: str, force_refresh: bool = False):
    """
    Get full AI analysis for a symbol.
    
    Combines:
    1. ML model prediction (LightGBM trained on historical patterns)
    2. Claude AI review (independent assessment of signals + TA data)
    3. Technical analysis snapshot
    """
    from services.claude_signal_analyzer import get_full_analysis

    return await get_full_analysis(symbol, force_refresh=force_refresh)


@router.get("/", response_model=List[FullAnalysisResponse])
async def get_all_ai_analysis():
    """Get AI analysis for both NASDAQ and XAUUSD."""
    from services.ai_panel_analysis_service import get_supported_ai_symbols
    from services.claude_signal_analyzer import get_full_analysis

    symbols = get_supported_ai_symbols()
    return await asyncio.gather(*(get_full_analysis(symbol) for symbol in symbols))


@router.get("/detailed/{symbol}")
async def get_detailed_ai_analysis(symbol: str):
    try:
        from services.detailed_ai_analysis_service import get_detailed_analysis
        result = await get_detailed_analysis(symbol)
        return {
            "symbol": result.get("symbol", symbol),
            "context": result.get("context", {}),
            "analysis": result.get("analysis", {}),
        }
    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc(),
            "symbol": symbol,
        }
