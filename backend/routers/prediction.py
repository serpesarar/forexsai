"""
API Router for ML Predictions
"""
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/api/prediction", tags=["prediction"])


class KeyLevel(BaseModel):
    type: str
    price: float
    distance: str


class PredictionResponse(BaseModel):
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
    timestamp: str
    model_version: str


@router.get("/{symbol}", response_model=PredictionResponse)
async def get_prediction(
    symbol: str,
    enabled_factors: Optional[str] = Query(
        default=None,
        description="Comma-separated list of enabled factor IDs (trend,confluence,session,pattern,candle,cot,sr,news,regime)"
    )
):
    """
    Get ML prediction for a symbol.
    
    Returns direction (BUY/SELL/HOLD), confidence, pip targets, and analysis.
    Optional enabled_factors query param to filter which confidence factors are applied.
    """
    from services.ml_prediction_service import get_ml_prediction
    
    # Parse enabled factors if provided
    factor_list = None
    if enabled_factors:
        factor_list = [f.strip() for f in enabled_factors.split(",") if f.strip()]
    
    result = await get_ml_prediction(symbol, enabled_factors=factor_list)
    
    return PredictionResponse(
        symbol=result.symbol,
        direction=result.direction,
        confidence=result.confidence,
        probability_up=result.probability_up,
        probability_down=result.probability_down,
        target_pips=result.target_pips,
        stop_pips=result.stop_pips,
        risk_reward=result.risk_reward,
        entry_price=result.entry_price,
        target_price=result.target_price,
        stop_price=result.stop_price,
        technical_score=result.technical_score,
        momentum_score=result.momentum_score,
        trend_score=result.trend_score,
        volatility_regime=result.volatility_regime,
        reasoning=result.reasoning,
        key_levels=[KeyLevel(**kl) for kl in result.key_levels],
        timestamp=result.timestamp,
        model_version=result.model_version
    )


@router.get("/", response_model=List[PredictionResponse])
async def get_all_predictions():
    """Get predictions for both NASDAQ and XAUUSD."""
    from services.ml_prediction_service import get_ml_prediction
    
    nasdaq = await get_ml_prediction("NDX.INDX")
    xauusd = await get_ml_prediction("XAUUSD")
    
    results = []
    for result in [nasdaq, xauusd]:
        results.append(PredictionResponse(
            symbol=result.symbol,
            direction=result.direction,
            confidence=result.confidence,
            probability_up=result.probability_up,
            probability_down=result.probability_down,
            target_pips=result.target_pips,
            stop_pips=result.stop_pips,
            risk_reward=result.risk_reward,
            entry_price=result.entry_price,
            target_price=result.target_price,
            stop_price=result.stop_price,
            technical_score=result.technical_score,
            momentum_score=result.momentum_score,
            trend_score=result.trend_score,
            volatility_regime=result.volatility_regime,
            reasoning=result.reasoning,
            key_levels=[KeyLevel(**kl) for kl in result.key_levels],
            timestamp=result.timestamp,
            model_version=result.model_version
        ))
    
    return results
