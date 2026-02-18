from __future__ import annotations

from datetime import datetime
import hashlib
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel

from services.marketaux_service import fetch_marketaux_headlines
from services.translation_service import translate_texts


router = APIRouter(prefix="/api/news", tags=["news"])


# =============================================================================
# COMEX NEWS MODELS
# =============================================================================

class COMEXNewsResponse(BaseModel):
    id: str
    title: str
    content: str
    source: str
    published_at: str
    impact_score: int
    direction: str
    direction_numeric: float
    confidence: int
    reasoning: str
    is_margin_related: bool
    is_rate_related: bool
    is_fed_related: bool


class COMEXImpactResponse(BaseModel):
    overall_impact: float
    impact_score: int
    confidence: int
    direction: str
    news_count: int
    should_block_trading: bool
    block_reason: str
    recent_news: List[COMEXNewsResponse]
    high_impact_news: List[COMEXNewsResponse]
    ml_features: Dict[str, float]
    last_update: str


# =============================================================================
# COMEX NEWS ENDPOINTS
# =============================================================================

@router.get("/comex", response_model=COMEXImpactResponse)
async def get_comex_news(
    use_ai: bool = Query(default=False, description="Use AI for analysis (slower but more accurate)")
) -> COMEXImpactResponse:
    """
    Get COMEX/CME news impact for gold trading.
    
    Returns analyzed news with sentiment, impact scores, and ML features.
    High impact news (score >= 85) may trigger trading blocks.
    """
    from services.comex_news_service import get_comex_service
    
    service = get_comex_service()
    impact = await service.get_comex_impact(use_ai=use_ai)
    
    def news_to_response(news) -> COMEXNewsResponse:
        return COMEXNewsResponse(
            id=news.id,
            title=news.title,
            content=news.content[:200] if news.content else "",
            source=news.source.split("/")[-1] if "/" in news.source else news.source,
            published_at=news.published_at.isoformat() + "Z",
            impact_score=news.impact_score,
            direction=news.direction,
            direction_numeric=news.direction_numeric,
            confidence=news.confidence,
            reasoning=news.reasoning,
            is_margin_related=news.is_margin_related,
            is_rate_related=news.is_rate_related,
            is_fed_related=news.is_fed_related,
        )
    
    return COMEXImpactResponse(
        overall_impact=impact.overall_impact,
        impact_score=impact.impact_score,
        confidence=impact.confidence,
        direction=impact.direction,
        news_count=impact.news_count,
        should_block_trading=impact.should_block_trading,
        block_reason=impact.block_reason,
        recent_news=[news_to_response(n) for n in impact.recent_news],
        high_impact_news=[news_to_response(n) for n in impact.high_impact_news],
        ml_features=impact.ml_features,
        last_update=impact.last_update.isoformat() + "Z",
    )


@router.get("/comex/check-block")
async def check_trading_block(symbol: str = Query(default="XAUUSD")) -> Dict[str, Any]:
    """
    Check if trading should be blocked due to critical COMEX news.
    
    Returns:
        blocked: bool - Whether trading should be paused
        reason: str - Reason for block
        duration_minutes: int - Suggested block duration
    """
    from services.comex_news_service import check_trading_block
    return await check_trading_block(symbol)


@router.get("/feed")
async def news_feed(
    impact: Optional[str] = Query(default=None),
    category: Optional[str] = Query(default=None),
    lang: str = Query(default="en"),
) -> Dict[str, Any]:
    """
    Minimal live news feed backed by Marketaux.
    Frontend expects: { total: number, news: NewsItem[] }
    """
    _ = impact
    _ = category

    # Marketaux symbols — include all tracked instruments
    headlines = await fetch_marketaux_headlines(["NDX", "XAUUSD", "GDAXI", "CL"])
    titles = [(h.get("title") or "").strip() for h in headlines]
    translated_titles = await translate_texts(titles, target_lang=lang)
    news = []
    for item, title in zip(headlines, translated_titles):
        title = (title or "").strip()
        source = (item.get("source") or "").strip() or "marketaux"
        if not title:
            continue
        published = (item.get("published_at") or "").strip()
        timestamp = published if published else datetime.utcnow().isoformat() + "Z"
        content = (item.get("description") or item.get("snippet") or "").strip()
        link = (item.get("url") or "").strip()
        stable_id = hashlib.md5(f"{title}|{source}".encode("utf-8")).hexdigest()
        news.append(
            {
                "type": "market_news",
                "id": stable_id,
                "timestamp": timestamp,
                "title": title,
                "content": content[:300] if content else "",
                "link": link,
                "source": source,
                "category": "market_news",
            }
        )

    return {"total": len(news), "news": news}


