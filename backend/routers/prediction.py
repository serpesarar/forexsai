"""
API Router for ML Predictions
"""
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/api/prediction", tags=["prediction"])


class KeyLevel(BaseModel):
    type: Optional[str] = None
    price: Optional[float] = None
    distance: Optional[str] = None  # optional: XAUUSD v2 S/R levels omit distance → was 500


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
    ),
    strategy: Optional[str] = Query(
        default="balanced",
        description="Preset strategy: main, ultra_safe, balanced, full_power, aggressive, nasdaq_precision"
    ),
    log_to_db: bool = Query(
        default=False,
        description="Log this prediction to database for learning"
    )
):
    """
    Get ML prediction for a symbol.
    
    Returns direction (BUY/SELL/HOLD), confidence, pip targets, and analysis.
    - enabled_factors: Filter which confidence factors are applied
    - strategy: Preset layer configuration (main, ultra_safe, balanced, full_power, aggressive, nasdaq_precision)
    - log_to_db: If true, logs prediction to database for learning system
    """
    from services.ml_prediction_service import get_ml_prediction
    
    # Parse enabled factors if provided
    factor_list = None
    if enabled_factors:
        factor_list = [f.strip() for f in enabled_factors.split(",") if f.strip()]
    
    # Validate strategy
    valid_strategies = ["main", "ultra_safe", "balanced", "full_power", "aggressive", "nasdaq_precision"]
    if strategy not in valid_strategies:
        strategy = "balanced"
    
    result = await get_ml_prediction(symbol, enabled_factors=factor_list, strategy=strategy)
    
    # Log to database if requested (for learning system)
    if log_to_db:
        try:
            from services.prediction_logger import log_prediction
            from database.supabase_client import is_db_available
            
            if is_db_available():
                context = {
                    "symbol": symbol,
                    "ml_prediction": {
                        "direction": result.direction,
                        "confidence": result.confidence,
                        "probability_up": result.probability_up,
                        "probability_down": result.probability_down,
                        "entry_price": result.entry_price,
                        "target_price": result.target_price,
                        "stop_price": result.stop_price,
                    },
                    "ta": {},
                    "distances": {},
                    "volume": {},
                    "trend_channel": {},
                    "macro": {},
                    "news": {},
                }
                analysis = {
                    "final_decision": result.direction,
                    "confidence": result.confidence,
                    "model_used": result.model_version,
                }
                await log_prediction(
                    symbol=symbol,
                    context=context,
                    analysis=analysis,
                    timeframe="30m",
                    strategy=strategy
                )
        except Exception as e:
            import logging
            logging.warning(f"Failed to log prediction: {e}")
    
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
