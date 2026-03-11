"""
News-Chart Correlation API
Endpoints for matching news events with candlestick data
"""

import logging
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, Query
from typing import Any, Dict, List, Optional

from database.supabase_client import get_supabase_client
from services.deepseek_json_client import call_deepseek_json
from services.news_candle_matcher import get_matching_impact, get_news_candle_matcher, get_symbol_variants
from services.translation_service import translate_texts

router = APIRouter(prefix="/api/news-correlation", tags=["news-correlation"])
logger = logging.getLogger(__name__)

URGENCY_PRIORITY = {"breaking": 4, "high": 3, "medium": 2, "low": 1}


def _normalize_lang(lang: Optional[str]) -> str:
    return (lang or "en").strip().lower()


async def _localize_text(text: str, lang: str) -> str:
    normalized = _normalize_lang(lang)
    if not text or normalized in {"", "tr"}:
        return text

    translated = await translate_texts([text], normalized)
    return translated[0] if translated else text


def _timeframe_to_minutes(timeframe: str) -> int:
    normalized = (timeframe or "1h").strip().lower()
    try:
        value = max(1, int(normalized[:-1]))
    except (TypeError, ValueError):
        value = 1

    unit = normalized[-1:] or "h"
    if unit == "m":
        return value
    if unit == "h":
        return value * 60
    if unit == "d":
        return value * 24 * 60
    return 60


def _extract_rows(result: Any) -> List[Dict[str, Any]]:
    if hasattr(result, "data"):
        return result.data or []
    if isinstance(result, dict):
        return result.get("data", []) or []
    return []


def _build_symbol_filter(symbol: str) -> str:
    variants = get_symbol_variants(symbol)
    return ",".join(f"symbol.eq.{variant}" for variant in variants)


def _attach_symbol_impacts(news_items: List[Dict[str, Any]], symbol: str) -> List[Dict[str, Any]]:
    related_news: List[Dict[str, Any]] = []

    for news in news_items:
        symbol_impact = get_matching_impact(news.get("impacts", []), symbol)
        if symbol_impact:
            related_news.append({**news, "symbol_impact": symbol_impact})

    related_news.sort(
        key=lambda item: (
            URGENCY_PRIORITY.get(item.get("urgency", "low"), 0),
            (item.get("symbol_impact") or {}).get("score", 0),
            item.get("ai_confidence", 0),
            item.get("timestamp", ""),
        ),
        reverse=True,
    )
    return related_news


def _build_move_explanation(symbol: str, change_percent: float, news_item: Dict[str, Any]) -> str:
    symbol_impact = news_item.get("symbol_impact") or {}
    headline = news_item.get("headline_tr") or news_item.get("headline") or "this news item"
    reasoning = symbol_impact.get("reasoning_tr") or symbol_impact.get("reasoning") or ""
    sentiment = news_item.get("sentiment")
    volatility = news_item.get("volatility_expectation")

    move_label = "yükseliş" if change_percent > 0 else "düşüş" if change_percent < 0 else "hareket"
    prefix = f"{symbol} fiyatındaki %{abs(change_percent):.2f} {move_label}"

    if reasoning:
        explanation = f"{prefix}, '{headline}' haberi için '{reasoning}' gerekçesiyle ilişkilendirildi."
    else:
        explanation = f"{prefix}, '{headline}' haberi ile zamanlama ve etki skoruna göre eşleşti."

    meta_parts = []
    if sentiment:
        meta_parts.append(f"sentiment: {sentiment}")
    if volatility:
        meta_parts.append(f"beklenen volatilite: {volatility}")

    if meta_parts:
        explanation = f"{explanation} ({', '.join(meta_parts)})"

    return explanation


def _serialize_news_for_ai(news_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    serialized: List[Dict[str, Any]] = []
    for news in news_items[:5]:
        symbol_impact = news.get("symbol_impact") or {}
        serialized.append(
            {
                "id": news.get("id"),
                "timestamp": news.get("timestamp"),
                "headline": news.get("headline_tr") or news.get("headline"),
                "urgency": news.get("urgency"),
                "ai_confidence": news.get("ai_confidence", 0),
                "impact_direction": symbol_impact.get("direction", "neutral"),
                "impact_score": symbol_impact.get("score", 0),
                "impact_reasoning_tr": symbol_impact.get("reasoning_tr") or symbol_impact.get("reasoning") or "",
            }
        )
    return serialized


async def _generate_move_explanation(
    symbol: str,
    candle: Dict[str, Any],
    candle_time: datetime,
    change_percent: float,
    related_news: List[Dict[str, Any]],
    lang: str = "tr",
) -> Dict[str, Any]:
    if not related_news:
        return {
            "explanation": await _localize_text(
                f"{symbol} için bu mumun çevresinde fiyat hareketini güvenle açıklayan güçlü bir catalyst bulunamadı.",
                lang,
            ),
            "confidence": 0,
        }

    fallback_explanation = _build_move_explanation(symbol, change_percent, related_news[0])
    fallback_confidence = int((related_news[0].get("ai_confidence") or 0))

    prompt = f"""You are explaining a specific candle move to a trader. Return ONLY valid JSON.

JSON schema:
{{
  "explanation": "2-4 cümlelik Türkçe açıklama",
  "confidence": 0-100,
  "primary_news_id": "string veya null"
}}

Rules:
- Sadece verilen haber adaylarını kullan.
- Haberler zayıfsa bunu açıkça söyle; kesin neden uydurma.
- Mum yönü ve haber yönü çelişiyorsa bunu belirt.
- Açıklama kısa, somut ve trader odaklı olsun.

CANDLE:
{{
  "symbol": "{symbol}",
  "timestamp": "{candle_time.isoformat()}",
  "open": {candle.get("open", 0)},
  "high": {candle.get("high", 0)},
  "low": {candle.get("low", 0)},
  "close": {candle.get("close", 0)},
  "change_percent": {round(change_percent, 4)},
  "direction": "{"up" if change_percent > 0 else "down" if change_percent < 0 else "flat"}"
}}

RELATED_NEWS:
{_serialize_news_for_ai(related_news)}
"""

    ai_payload = await call_deepseek_json(prompt, max_tokens=700, temperature=0.2, timeout_seconds=30)
    explanation = str((ai_payload or {}).get("explanation") or "").strip()

    if explanation:
        explanation = await _localize_text(explanation, lang)
        return {
            "explanation": explanation,
            "confidence": int((ai_payload or {}).get("confidence") or fallback_confidence),
        }

    return {
        "explanation": await _localize_text(fallback_explanation, lang),
        "confidence": fallback_confidence,
    }


@router.get("/candle-news/{symbol}")
async def get_candle_news(
    symbol: str,
    timestamp: int,
    timeframe: str = "1h",
    window_minutes: int = 30
):
    """
    Get news events related to a specific candle/time
    
    Args:
        symbol: Trading symbol (e.g., XAUUSD)
        timestamp: Unix timestamp of the candle
        timeframe: Candle timeframe
        window_minutes: Time window to search for news (before and after)
    """
    try:
        supabase = get_supabase_client()
        
        # Calculate time range
        candle_time = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        start_time = candle_time - timedelta(minutes=window_minutes)
        end_time = candle_time + timedelta(minutes=window_minutes)
        
        # Fetch news in time window
        result = supabase.table("enriched_news")\
            .select("*")\
            .gte("timestamp", start_time.isoformat())\
            .lte("timestamp", end_time.isoformat())\
            .order("timestamp", desc=True)\
            .execute()

        related_news = _attach_symbol_impacts(_extract_rows(result), symbol)
        
        return {
            "success": True,
            "data": {
                "symbol": symbol,
                "candle_time": candle_time.isoformat(),
                "timeframe": timeframe,
                "news_count": len(related_news),
                "news": related_news
            }
        }
        
    except Exception as e:
        logger.exception("Error fetching candle news for %s at %s", symbol, timestamp)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/big-moves/{symbol}")
async def get_big_moves(
    symbol: str,
    timeframe: str = "1h",
    threshold_percent: float = 1.5,
    hours: int = 24
):
    """
    Identify candles with big price movements and their related news
    
    Args:
        symbol: Trading symbol
        timeframe: Candle timeframe
        threshold_percent: Minimum % change to be considered "big move"
        hours: How many hours back to analyze
    """
    try:
        supabase = get_supabase_client()
        
        # Get candles with big moves from cache
        from_time = datetime.utcnow() - timedelta(hours=hours)
        
        result = supabase.table("candle_cache")\
            .select("*")\
            .or_(_build_symbol_filter(symbol))\
            .eq("timeframe", timeframe)\
            .gte("timestamp", from_time.isoformat())\
            .order("timestamp", desc=True)\
            .execute()

        big_moves = []
        for candle in _extract_rows(result):
            open_price = candle.get("open", 0)
            close_price = candle.get("close", 0)
            
            if open_price == 0:
                continue
                
            change_percent = ((close_price - open_price) / open_price) * 100
            
            if abs(change_percent) >= threshold_percent:
                # Get news for this candle
                candle_time = datetime.fromisoformat(candle["timestamp"])
                news_result = supabase.table("enriched_news")\
                    .select("*")\
                    .gte("timestamp", (candle_time - timedelta(minutes=30)).isoformat())\
                    .lte("timestamp", (candle_time + timedelta(minutes=30)).isoformat())\
                    .execute()

                related_news = _attach_symbol_impacts(_extract_rows(news_result), symbol)
                
                big_moves.append({
                    "timestamp": candle["timestamp"],
                    "unix_time": int(candle_time.timestamp()),
                    "open": open_price,
                    "close": close_price,
                    "high": candle.get("high"),
                    "low": candle.get("low"),
                    "change_percent": round(change_percent, 2),
                    "direction": "up" if change_percent > 0 else "down",
                    "related_news_count": len(related_news),
                    "related_news": related_news[:3]  # Top 3 news items
                })
        
        return {
            "success": True,
            "data": {
                "symbol": symbol,
                "timeframe": timeframe,
                "threshold_percent": threshold_percent,
                "big_moves_count": len(big_moves),
                "big_moves": big_moves
            }
        }
        
    except Exception as e:
        logger.exception("Error fetching big moves for %s", symbol)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/explain-move")
async def explain_price_move(
    symbol: str,
    timestamp: int,
    timeframe: str = "1h",
    ai_explain: bool = True,
    lang: str = Query("en", description="Preferred explanation language"),
):
    """
    Get AI explanation for a specific price movement
    
    Args:
        symbol: Trading symbol
        timestamp: Unix timestamp of the move
        ai_explain: Whether to include AI-generated explanation
    """
    try:
        # First get the candle data
        supabase = get_supabase_client()
        candle_time = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        timeframe_minutes = _timeframe_to_minutes(timeframe)
        candle_end_time = candle_time + timedelta(minutes=timeframe_minutes)
        
        # Get candle
        candle_result = supabase.table("candle_cache")\
            .select("*")\
            .or_(_build_symbol_filter(symbol))\
            .gte("timestamp", candle_time.isoformat())\
            .lt("timestamp", candle_end_time.isoformat())\
            .limit(1)\
            .execute()

        candle_rows = _extract_rows(candle_result)
        if not candle_rows:
            return {
                "success": False,
                "error": "Candle not found"
            }

        candle = candle_rows[0]
        
        matcher = get_news_candle_matcher()
        relevant_news = await matcher.match_news_to_candle_simple_ai(
            symbol=symbol,
            candle_timestamp=candle_time.isoformat(),
            candle_open=float(candle.get("open", 0)),
            candle_close=float(candle.get("close", 0)),
            candle_high=float(candle.get("high", 0)),
            candle_low=float(candle.get("low", 0)),
            timeframe=timeframe,
        )
        
        # Calculate price change
        change_percent = ((candle["close"] - candle["open"]) / candle["open"]) * 100
        
        # Generate AI explanation
        explanation = ""
        confidence = 0
        if ai_explain:
            ai_result = await _generate_move_explanation(symbol, candle, candle_time, change_percent, relevant_news, lang=_normalize_lang(lang))
            explanation = ai_result.get("explanation", "")
            confidence = ai_result.get("confidence", 0)
        
        return {
            "success": True,
            "data": {
                "symbol": symbol,
                "timestamp": timestamp,
                "candle": candle,
                "change_percent": round(change_percent, 2),
                "direction": "up" if change_percent > 0 else "down",
                "related_news": relevant_news,
                "confidence": confidence,
                "explanation": explanation if ai_explain else None,
                "ai_explanation": explanation if ai_explain else None
            }
        }
        
    except Exception as e:
        logger.exception("Error explaining move for %s at %s", symbol, timestamp)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/economic-events/{symbol}")
async def get_economic_events(
    symbol: str,
    hours_ahead: int = 24,
    impact_filter: Optional[str] = None
):
    """
    Get upcoming economic events that may affect the symbol
    
    Args:
        symbol: Trading symbol
        hours_ahead: How many hours ahead to look
        impact_filter: Filter by impact level (high, medium, low)
    """
    try:
        supabase = get_supabase_client()
        
        now = datetime.utcnow()
        future = now + timedelta(hours=hours_ahead)
        
        # Map symbols to relevant currencies/countries
        symbol_mapping = {
            "XAUUSD": ["USD", "ALL"],
            "NDX": ["USD", "ALL"],
            "DAX": ["EUR", "DE", "ALL"],
            "USOIL": ["USD", "ALL"],
            "VIX": ["USD", "ALL"],
            "DXY": ["USD", "ALL"],
        }
        
        relevant_currencies = symbol_mapping.get(symbol, ["ALL"])
        
        # This would typically query an economic calendar table
        # For now, return mock data structure
        events = [
            {
                "time": (now + timedelta(hours=4)).isoformat(),
                "currency": "USD",
                "event": "Non-Farm Payrolls",
                "impact": "high",
                "forecast": "185K",
                "previous": "175K",
                "expected_impact": f"High volatility expected in {symbol}"
            },
            {
                "time": (now + timedelta(hours=12)).isoformat(),
                "currency": "USD",
                "event": "FOMC Meeting Minutes",
                "impact": "high",
                "forecast": "-",
                "previous": "-",
                "expected_impact": f"Potential trend change for {symbol}"
            }
        ]
        
        if impact_filter:
            events = [e for e in events if e["impact"] == impact_filter]
        
        return {
            "success": True,
            "data": {
                "symbol": symbol,
                "events_count": len(events),
                "events": events
            }
        }
        
    except Exception as e:
        logger.exception("Error fetching economic events for %s", symbol)
        raise HTTPException(status_code=500, detail=str(e))
