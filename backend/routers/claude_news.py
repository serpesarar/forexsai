from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Query
from pydantic import BaseModel

from database.supabase_client import get_supabase_client
from services.news_candle_matcher import get_matching_impact
from services.rss_aggregator import get_rss_aggregator

router = APIRouter(prefix="/api/claude-news", tags=["claude_news_compat"])


class RefreshRequest(BaseModel):
    symbol: str
    limit: int = 30


def _result_rows(result: Any) -> list[dict]:
    if isinstance(result, dict):
        return result.get("data", []) or []
    if hasattr(result, "data"):
        return result.data or []
    return []


def _signed_sentiment(item: dict, impact: dict | None) -> float:
    if impact and impact.get("direction") == "bullish":
        return round(min(float(impact.get("score", 0)) / 10.0, 1.0), 3)
    if impact and impact.get("direction") == "bearish":
        return round(max(-float(impact.get("score", 0)) / 10.0, -1.0), 3)
    sentiment = str(item.get("sentiment", "neutral")).lower()
    if sentiment == "bullish":
        return 0.35
    if sentiment == "bearish":
        return -0.35
    return 0.0


def _load_news(symbol: str, hours_back: int, limit: int) -> list[dict]:
    supabase = get_supabase_client()
    start_time = datetime.utcnow() - timedelta(hours=hours_back)
    result = (
        supabase.table("enriched_news")
        .select("id, timestamp, source, headline, impacts, sentiment, ai_confidence, category, analysis_timestamp, analysis_tr")
        .gte("timestamp", start_time.isoformat())
        .order("timestamp", desc=True)
        .limit(max(limit * 4, 100))
        .execute()
    )
    rows = _result_rows(result)
    filtered = [row for row in rows if get_matching_impact(row.get("impacts", []), symbol)]
    return filtered[:limit]


@router.post("/analyze/{symbol}")
async def analyze_news(symbol: str, limit: int = Query(15, ge=1, le=50), hours_back: int = Query(24, ge=1, le=168)):
    items = _load_news(symbol, hours_back, limit)
    analyses = []
    scores = []
    bullish = bearish = neutral = 0
    for item in items:
        impact = get_matching_impact(item.get("impacts", []), symbol)
        score = _signed_sentiment(item, impact)
        scores.append(score)
        bullish += int(score > 0.05)
        bearish += int(score < -0.05)
        neutral += int(abs(score) <= 0.05)
        analyses.append({
            "headline": item.get("headline", ""),
            "sentiment": score,
            "confidence": round(float(item.get("ai_confidence", 0) or 0) / 100.0, 3),
            "category": item.get("category", "general"),
            "time_sensitivity": "high" if impact and impact.get("score", 0) >= 8 else "medium",
            "key_entities": [impact.get("symbol")] if impact and impact.get("symbol") else [],
            "rationale": (impact or {}).get("reasoning_tr") or item.get("analysis_tr") or "Derived from cached RSS analysis.",
            "override_signal": impact.get("direction") if impact and impact.get("score", 0) >= 9 else None,
        })

    overall_sentiment = round(sum(scores) / len(scores), 3) if scores else 0.0
    direction_bias = "bullish" if overall_sentiment > 0.05 else "bearish" if overall_sentiment < -0.05 else "neutral"
    return {
        "symbol": symbol,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "news_count": len(items),
        "analyzed_count": len(analyses),
        "overall_sentiment": overall_sentiment,
        "overall_confidence": round(sum(a["confidence"] for a in analyses) / len(analyses), 3) if analyses else 0.0,
        "direction_bias": direction_bias,
        "analyses": analyses,
        "bullish_count": bullish,
        "bearish_count": bearish,
        "neutral_count": neutral,
        "has_override": any(a["override_signal"] for a in analyses),
        "override_signal": next((a["override_signal"] for a in analyses if a["override_signal"]), None),
        "override_reason": next((a["rationale"] for a in analyses if a["override_signal"]), None),
        "categories": {a["category"]: sum(1 for item in analyses if item["category"] == a["category"]) for a in analyses},
        "tokens_used": 0,
        "estimated_cost_usd": 0.0,
        "market_commentary": "Compatibility response derived from cached RSS-enriched news.",
        "key_risks": [a["rationale"] for a in analyses[:3] if a["sentiment"] < 0],
        "key_opportunities": [a["rationale"] for a in analyses[:3] if a["sentiment"] > 0],
    }


@router.get("/cached/{symbol}")
async def get_cached_news(symbol: str, limit: int = Query(20, ge=1, le=100), hours_back: int = Query(24, ge=1, le=168)):
    items = _load_news(symbol, hours_back, limit)
    return {
        "symbol": symbol,
        "news_count": len(items),
        "news": [
            {
                "headline": item.get("headline", ""),
                "source": item.get("source", ""),
                "published_at": item.get("timestamp"),
                "fetched_at": item.get("analysis_timestamp") or item.get("timestamp"),
                "keyword_sentiment": _signed_sentiment(item, get_matching_impact(item.get("impacts", []), symbol)),
                "keyword_confidence": round(float(item.get("ai_confidence", 0) or 0) / 100.0, 3),
                "claude_analyzed": bool(item.get("ai_confidence")),
                "claude_sentiment": _signed_sentiment(item, get_matching_impact(item.get("impacts", []), symbol)),
            }
            for item in items
        ],
    }


@router.post("/refresh")
async def refresh_news_cache(payload: RefreshRequest):
    stats = await get_rss_aggregator().run_aggregation_cycle()
    return {
        "symbol": payload.symbol,
        "fetched_count": stats.get("fetched", 0),
        "saved_count": stats.get("new", 0),
        "message": "RSS refresh completed for claude-news compatibility endpoints.",
    }