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
async def get_prediction(symbol: str):
    """
    Get ML prediction for a symbol.
    
    Returns direction (BUY/SELL/HOLD), confidence, pip targets, and analysis.
    """
    from services.ml_prediction_service import get_ml_prediction
    
    result = await get_ml_prediction(symbol)
    
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
