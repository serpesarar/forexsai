from fastapi import APIRouter
from typing import List, Dict

from models.responses import SignalResponse
from services.ml_service import run_xauusd_signal_async
from services.gold_news_analyzer_v2 import analyze_gold_news_impact_v2
from pydantic import BaseModel

router = APIRouter(prefix="/api/run", tags=["xauusd"])


class GoldNewsResponse(BaseModel):
    """V2 Gold News Impact Response"""
    sentiment_score: float
    confidence: float
    impact_level: str
    direction_bias: str
    key_factors: List[str]
    news_count: int
    high_impact_events: List[dict]
    # V2 additions
    conflicts: List[str] = []
    time_to_expiry_minutes: int = 60
    source_breakdown: Dict[str, int] = {}
    validation_status: str = "pending"


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
    Analyze news impact on gold prices (XAUUSD) - V2 Advanced Analysis.
    
    Features:
    - Context-aware NLP with negation detection
    - Source reliability weighting (Reuters > Zerohedge)
    - Time decay (30 min half-life)
    - Dynamic event-based impact levels
    - Conflict detection for mixed signals
    
    Gold is heavily influenced by:
    - Interest rate decisions (Fed, ECB)
    - Inflation data (CPI, PPI)
    - Geopolitical events (wars, tensions)
    - USD strength/weakness
    - Real yields
    """
    impact = await analyze_gold_news_impact_v2()
    return GoldNewsResponse(
        sentiment_score=impact.sentiment_score,
        confidence=impact.confidence,
        impact_level=impact.impact_level,
        direction_bias=impact.direction_bias,
        key_factors=impact.key_factors,
        news_count=impact.news_count,
        high_impact_events=impact.high_impact_events,
        conflicts=impact.conflicts,
        time_to_expiry_minutes=impact.time_to_expiry_minutes,
        source_breakdown=impact.source_breakdown,
        validation_status=impact.validation_status,
    )
