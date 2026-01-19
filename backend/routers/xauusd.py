from fastapi import APIRouter
from typing import List

from models.responses import SignalResponse
from services.ml_service import run_xauusd_signal_async
from services.gold_news_analyzer import analyze_gold_news_impact, GoldNewsImpact
from pydantic import BaseModel

router = APIRouter(prefix="/api/run", tags=["xauusd"])


class GoldNewsResponse(BaseModel):
    sentiment_score: float
    confidence: float
    impact_level: str
    direction_bias: str
    key_factors: List[str]
    news_count: int
    high_impact_events: List[dict]


@router.post("/xauusd", response_model=SignalResponse)
async def run_xauusd() -> SignalResponse:
    """
    Run XAUUSD trend analysis using real-time data and trend_analyzer.
    Returns signal, confidence, reasoning, and metrics.
    """
    result = await run_xauusd_signal_async()
    return SignalResponse(
        signal=result.signal,
        confidence=result.confidence,
        reasoning=result.reasoning,
        metrics=result.metrics,
        timestamp=result.timestamp,
        model_status=result.model_status,
    )


@router.get("/gold-news-impact", response_model=GoldNewsResponse)
async def get_gold_news_impact() -> GoldNewsResponse:
    """
    Analyze news impact on gold prices (XAUUSD).
    Returns sentiment score, confidence, and key factors.
    
    Gold is heavily influenced by:
    - Interest rate decisions (Fed, ECB)
    - Inflation data (CPI, PPI)
    - Geopolitical events (wars, tensions)
    - USD strength/weakness
    """
    impact = await analyze_gold_news_impact()
    return GoldNewsResponse(
        sentiment_score=impact.sentiment_score,
        confidence=impact.confidence,
        impact_level=impact.impact_level,
        direction_bias=impact.direction_bias,
        key_factors=impact.key_factors,
        news_count=impact.news_count,
        high_impact_events=impact.high_impact_events
    )
