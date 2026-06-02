"""
RSS Router - API endpoints for RSS news aggregation
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, List, Any, Dict
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel

from services.rss_aggregator import get_rss_aggregator, RSS_SOURCES
from services.news_candle_matcher import get_matching_impact, symbols_match
from services.translation_service import translate_texts
from database.supabase_client import get_supabase_client

router = APIRouter(prefix="/api/rss", tags=["rss"])

# Request/Response Models
class RSSNewsResponse(BaseModel):
    id: str
    timestamp: str
    source: str
    headline: str
    headline_tr: Optional[str] = None  # Turkish translation
    content: Optional[str]
    content_tr: Optional[str] = None  # Turkish translation
    summary_en: Optional[str] = None
    summary_tr: Optional[str] = None
    analysis_en: Optional[str] = None
    analysis_tr: Optional[str] = None
    headline_locale: Optional[str] = None
    summary_locale: Optional[str] = None
    analysis_locale: Optional[str] = None
    category: str
    url: str
    impacts: List[dict]
    sentiment: str
    volatility_expectation: str
    urgency: str
    ai_confidence: float
    importance_level: Optional[str] = None
    importance_score: Optional[int] = None
    importance_reason: Optional[str] = None
    ai_model: Optional[str] = None
    duplicate_of: Optional[str]
    sources: List[str]
    # Chart markers
    show_on_chart: bool = False
    marker_type: str = "news"
    marker_color: str = "#3B82F6"

class RSSStatsResponse(BaseModel):
    fetched: int
    new: int
    duplicates: int
    ai_analyzed: int
    errors: int

class RSSSourceInfo(BaseModel):
    name: str
    priority: int
    category: str
    fetch_interval: int
    url: str


RUNTIME_TRANSLATION_BATCH_SIZE = 20


def _normalize_lang(lang: Optional[str]) -> str:
    if not isinstance(lang, str):
        return "en"
    normalized = lang.strip().lower()
    return normalized or "en"


def _needs_runtime_translation(lang: str) -> bool:
    return lang not in {"", "en", "tr"}


def _clean_turkish_text(value: Any) -> str:
    if not value:
        return ""
    from services.news_analyzer_v2 import RealNewsAnalyzer

    return RealNewsAnalyzer._validate_turkish(str(value))


def _normalize_article_confidence(value: Any) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return 0.0
    if numeric <= 1:
        numeric *= 100.0
    return round(max(0.0, min(100.0, numeric)), 2)


def _sanitize_impacts(impacts: Any) -> List[dict]:
    sanitized: List[dict] = []
    for raw_impact in impacts or []:
        if not isinstance(raw_impact, dict):
            continue
        impact = dict(raw_impact)
        impact["reasoning_tr"] = _clean_turkish_text(impact.get("reasoning_tr"))
        sanitized.append(impact)
    return sanitized


def _sanitize_news_item(item: Dict[str, Any]) -> Dict[str, Any]:
    sanitized = dict(item)
    ai_model = str(sanitized.get("ai_model") or "").lower()
    if ai_model == "fallback":
        sanitized["headline_tr"] = ""
        sanitized["content_tr"] = ""
        sanitized["summary_tr"] = ""
        sanitized["analysis_tr"] = ""
    else:
        sanitized["headline_tr"] = _clean_turkish_text(sanitized.get("headline_tr"))
        sanitized["content_tr"] = _clean_turkish_text(sanitized.get("content_tr"))
        sanitized["summary_tr"] = _clean_turkish_text(sanitized.get("summary_tr"))
        sanitized["analysis_tr"] = _clean_turkish_text(sanitized.get("analysis_tr"))
    from services.news_analyzer_v2 import enforce_news_analysis_consistency

    adjusted_impacts, adjusted_sentiment = enforce_news_analysis_consistency(
        headline=str(sanitized.get("headline") or ""),
        content=str(sanitized.get("content") or ""),
        summary_en=str(sanitized.get("summary_en") or ""),
        analysis_en=str(sanitized.get("analysis_en") or ""),
        summary_tr=str(sanitized.get("summary_tr") or ""),
        analysis_tr=str(sanitized.get("analysis_tr") or ""),
        impacts=sanitized.get("impacts"),
        sentiment=str(sanitized.get("sentiment") or "neutral"),
    )
    sanitized["sentiment"] = adjusted_sentiment
    sanitized["impacts"] = adjusted_impacts
    sanitized["impacts"] = _sanitize_impacts(sanitized.get("impacts"))
    sanitized["ai_confidence"] = _normalize_article_confidence(sanitized.get("ai_confidence"))
    return sanitized


def _normalize_marker_direction(value: Any) -> str:
    direction = str(value or "neutral").strip().lower()
    if direction in {"bullish", "bearish", "neutral"}:
        return direction
    return "neutral"


def _marker_position_for(direction: str, catalyst_type: str) -> str:
    return "aboveBar"


def _marker_shape_for(direction: str, catalyst_type: str, urgency: str) -> str:
    return "circle"


def _marker_text_for(catalyst_type: str, urgency: str) -> str:
    if catalyst_type == "economic":
        return "�"
    if catalyst_type == "earnings":
        return "�"
    return "🚨" if urgency == "breaking" else "📰"


def _marker_color_for(direction: str, catalyst_type: str, urgency: str) -> str:
    if catalyst_type == "economic":
        return "#F59E0B"
    if catalyst_type == "earnings":
        return "#38BDF8"
    if urgency == "breaking":
        return "#DC2626"
    return "#F97316"


def _marker_size_for(score: int, importance_score: int, catalyst_type: str, urgency: str) -> float:
    if catalyst_type == "economic":
        return 2.4 if importance_score >= 85 else 2.0 if importance_score >= 65 else 1.7
    if catalyst_type == "earnings":
        return 2.2 if importance_score >= 75 else 1.9 if importance_score >= 60 else 1.6
    if urgency == "breaking":
        return 2.5
    if score >= 8 or importance_score >= 80:
        return 2.0
    if score >= 6 or importance_score >= 70:
        return 1.6
    return 1.2


async def _translate_in_batches(texts: List[str], target_lang: str) -> List[str]:
    if not texts:
        return []

    translated: List[str] = []
    for start in range(0, len(texts), RUNTIME_TRANSLATION_BATCH_SIZE):
        chunk = texts[start:start + RUNTIME_TRANSLATION_BATCH_SIZE]
        translated.extend(await translate_texts(chunk, target_lang))
    return translated


async def _localize_news_items(items: List[dict], lang: str) -> List[dict]:
    if not _needs_runtime_translation(lang) or not items:
        return items

    headlines = [item.get("headline") or "" for item in items]
    summaries = [item.get("summary_en") or "" for item in items]
    analyses = [item.get("analysis_en") or "" for item in items]
    impact_reasonings: List[str] = []
    for item in items:
        impacts = item.get("impacts") or []
        for impact in impacts:
            impact_reasonings.append(impact.get("reasoning") or impact.get("reasoning_tr") or "")

    localized_headlines = await _translate_in_batches(headlines, lang)
    localized_summaries = await _translate_in_batches(summaries, lang)
    localized_analyses = await _translate_in_batches(analyses, lang)
    localized_reasonings = await _translate_in_batches(impact_reasonings, lang)

    localized_items: List[dict] = []
    reasoning_index = 0
    for item, headline_locale, summary_locale, analysis_locale in zip(items, localized_headlines, localized_summaries, localized_analyses):
        localized = dict(item)
        localized["headline_locale"] = headline_locale or localized.get("headline")
        localized["summary_locale"] = summary_locale or localized.get("summary_en") or localized.get("headline")
        localized["analysis_locale"] = analysis_locale or localized.get("analysis_en") or localized["summary_locale"]

        localized_impacts: List[dict] = []
        for impact in localized.get("impacts") or []:
            localized_impact = dict(impact)
            localized_impact["reasoning_locale"] = localized_reasonings[reasoning_index] if reasoning_index < len(localized_reasonings) else localized_impact.get("reasoning") or localized_impact.get("reasoning_tr")
            localized_impacts.append(localized_impact)
            reasoning_index += 1
        localized["impacts"] = localized_impacts
        localized_items.append(localized)

    return localized_items


async def _localize_candle_news_items(items: List[dict], lang: str) -> List[dict]:
    if not _needs_runtime_translation(lang) or not items:
        return items

    headlines = [item.get("headline_en") or item.get("headline") or "" for item in items]
    summaries = [item.get("summary_en") or "" for item in items]
    analyses = [item.get("analysis_en") or "" for item in items]
    reasonings = [item.get("reasoning") or item.get("reasoning_tr") or item.get("analysis_en") or item.get("summary_en") or "" for item in items]

    localized_headlines = await _translate_in_batches(headlines, lang)
    localized_summaries = await _translate_in_batches(summaries, lang)
    localized_analyses = await _translate_in_batches(analyses, lang)
    localized_reasonings = await _translate_in_batches(reasonings, lang)

    localized_items: List[dict] = []
    for item, headline_locale, summary_locale, analysis_locale, reasoning_locale in zip(
        items,
        localized_headlines,
        localized_summaries,
        localized_analyses,
        localized_reasonings,
    ):
        localized = dict(item)
        localized["headline_locale"] = headline_locale or localized.get("headline")
        localized["summary_locale"] = summary_locale or localized.get("summary_en") or localized.get("headline")
        localized["analysis_locale"] = analysis_locale or localized.get("analysis_en") or localized["summary_locale"]
        localized["reasoning_locale"] = reasoning_locale or localized.get("reasoning_tr")
        localized_items.append(localized)

    return localized_items


@router.get("/sources", response_model=List[RSSSourceInfo])
async def get_rss_sources():
    """Get list of configured RSS sources"""
    return [
        RSSSourceInfo(
            name=name,
            priority=config["priority"],
            category=config["category"],
            fetch_interval=config["fetch_interval"],
            url=config["url"]
        )
        for name, config in RSS_SOURCES.items()
    ]


@router.get("/news", response_model=List[RSSNewsResponse])
async def get_rss_news(
    symbol: Optional[str] = Query(None, description="Filter by affected symbol"),
    urgency: Optional[str] = Query(None, description="Filter by urgency: breaking, high, medium, low"),
    sentiment: Optional[str] = Query(None, description="Filter by sentiment"),
    hours: int = Query(24, ge=1, le=168, description="Lookback period in hours"),
    limit: int = Query(50, ge=1, le=200, description="Max items to return"),
    lang: str = Query("en", description="Preferred content language"),
    skip_ai_filtered: bool = Query(True, description="Skip low-priority non-AI analyzed items"),
    show_on_chart: Optional[bool] = Query(None, description="Filter by chart visibility")
):
    """
    Get RSS news with optional filtering
    """
    try:
        supabase = get_supabase_client()
        
        start_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        print(f"[RSS API] Querying news from last {hours}h (since {start_time.isoformat()})")
        
        # Build query
        query = (
            supabase.table("enriched_news")
            .select("*")
            .gte("timestamp", start_time.isoformat())
            .order("timestamp", desc=True)
            .limit(limit)
        )
        
        # Log total count for debugging (simplified)
        try:
            count_result = supabase.table("enriched_news").select("id").execute()
            total_in_db = len(count_result.get('data', [])) if isinstance(count_result, dict) else len(count_result.data or [])
            print(f"[RSS API] Total items in DB: {total_in_db}")
        except Exception as count_err:
            print(f"[RSS API] Count query failed: {count_err}")
        
        # Apply filters
        if urgency:
            query = query.eq("urgency", urgency)
        
        if sentiment:
            query = query.eq("sentiment", sentiment)
        
        # Skip low priority items if requested
        if skip_ai_filtered:
            query = query.neq("urgency", "low")
        
        # Filter by chart visibility
        if show_on_chart is not None:
            query = query.eq("show_on_chart", show_on_chart)
        
        result = query.execute()
        
        # Handle both old and new Supabase response formats
        if hasattr(result, 'data'):
            items = result.data or []
        elif isinstance(result, dict):
            items = result.get('data', []) or []
        else:
            items = []
        
        print(f"[RSS API] Found {len(items)} items from DB query")
        
        if not items:
            # Debug: Check total count without time filter
            count_result = supabase.table("enriched_news").select("id", count="exact").execute()
            total_count = getattr(count_result, 'count', 'unknown')
            print(f"[RSS API] No items found. Total items in table: {total_count}")
            return []
        if symbol:
            items = [
                item for item in items
                if any(
                    symbols_match(symbol, imp.get("symbol"))
                    for imp in item.get("impacts", [])
                )
            ]

        items = await _localize_news_items(items, _normalize_lang(lang))
        items = [_sanitize_news_item(item) for item in items]
        
        # Format response - WITH TURKISH TRANSLATIONS & OPTIONAL RUNTIME LOCALIZATION
        return [
            RSSNewsResponse(
                id=item["id"],
                timestamp=item["timestamp"],
                source=item["source"],
                headline=item["headline"],
                headline_tr=item.get("headline_tr"),
                content=item.get("content"),
                content_tr=item.get("content_tr"),
                summary_en=item.get("summary_en"),
                summary_tr=item.get("summary_tr"),
                analysis_en=item.get("analysis_en"),
                analysis_tr=item.get("analysis_tr"),
                headline_locale=item.get("headline_locale"),
                summary_locale=item.get("summary_locale"),
                analysis_locale=item.get("analysis_locale"),
                category=item.get("category", "general"),
                url=item.get("url", ""),
                impacts=item.get("impacts", []),
                sentiment=item.get("sentiment", "neutral"),
                volatility_expectation=item.get("volatility_expectation", "medium"),
                urgency=item.get("urgency", "medium"),
                ai_confidence=item.get("ai_confidence", 0),  # 0-100 scale, no division
                importance_level=item.get("importance_level"),
                importance_score=item.get("importance_score"),
                importance_reason=item.get("importance_reason"),
                ai_model=item.get("ai_model"),
                duplicate_of=item.get("duplicate_of"),
                sources=item.get("sources", [item["source"]]),
                show_on_chart=item.get("show_on_chart", False),
                marker_type=item.get("marker_type", "news"),
                marker_color=item.get("marker_color", "#3B82F6"),
            )
            for item in items
        ]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/latest-breaking")
async def get_latest_breaking(limit: int = Query(10, ge=1, le=50)):
    """
    Get only breaking/high urgency news from last hour
    """
    try:
        supabase = get_supabase_client()
        
        start_time = datetime.now(timezone.utc) - timedelta(hours=1)
        
        result = (
            supabase.table("enriched_news")
            .select("*")
            .gte("timestamp", start_time.isoformat())
            .in_("urgency", ["breaking", "high"])
            .order("timestamp", desc=True)
            .limit(limit)
            .execute()
        )
        
        # Handle both old and new Supabase response formats
        if hasattr(result, 'data'):
            data = result.data or []
        elif isinstance(result, dict):
            data = result.get('data', []) or []
        else:
            data = []
        
        return {
            "success": True,
            "count": len(data),
            "data": data
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chart-markers/{symbol}")
async def get_chart_news_markers(
    symbol: str,
    hours: int = Query(72, ge=1, le=2160, description="Lookback period in hours"),
    min_impact_score: int = Query(6, ge=1, le=10, description="Minimum impact score to show on chart"),
    max_markers: int = Query(60, ge=1, le=200, description="Maximum number of markers to return")
):
    """
    Get news markers for chart display - INTELLIGENT FILTERING.
    Only returns HIGH QUALITY markers that are likely to have caused price movements.
    """
    try:
        supabase = get_supabase_client()
        from routers.economic_calendar_router import generate_economic_events_between, generate_earnings_events_between

        start_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        end_time = datetime.now(timezone.utc)

        result = (
            supabase.table("enriched_news")
            .select("*")
            .gte("timestamp", start_time.isoformat())
            .or_("show_on_chart.eq.true,urgency.eq.breaking,and(urgency.eq.high,ai_confidence.gte.60)")
            .order("timestamp", desc=True)
            .limit(150)
            .execute()
        )
        
        # Handle both old and new Supabase response formats
        if hasattr(result, 'data'):
            items = result.data or []
        elif isinstance(result, dict):
            items = result.get('data', []) or []
        else:
            items = []

        if len(items) < max_markers:
            medium_result = (
                supabase.table("enriched_news")
                .select("*")
                .gte("timestamp", start_time.isoformat())
                .eq("urgency", "medium")
                .gte("ai_confidence", 70)
                .order("timestamp", desc=True)
                .limit(30)
                .execute()
            )
            
            medium_items = medium_result.data if hasattr(medium_result, 'data') else medium_result.get('data', [])
            
            # Merge without duplicates
            existing_ids = {item["id"] for item in items}
            for item in medium_items:
                if item["id"] not in existing_ids:
                    items.append(item)

        items = [_sanitize_news_item(item) for item in items]
        markers: List[Dict[str, Any]] = []
        for item in items:
            impacts = item.get("impacts", [])
            urgency = item.get("urgency", "medium")
            ai_confidence = _normalize_article_confidence(item.get("ai_confidence", 0))
            importance_level = item.get("importance_level")
            try:
                importance_score = int(item.get("importance_score") or 0)
            except (TypeError, ValueError):
                importance_score = 0

            # Check if this news affects the requested symbol
            symbol_impact = get_matching_impact(impacts, symbol)
            if symbol_impact:
                imp_score = symbol_impact.get("score", 0)
                if importance_score <= 0:
                    urgency_base = 85 if urgency == "breaking" else 72 if urgency == "high" else 58 if urgency == "medium" else 35
                    importance_score = max(urgency_base, int(imp_score) * 10)
                passes_importance = (
                    (urgency == "breaking" and importance_score >= 80)
                    or (urgency == "high" and importance_score >= 75)
                    or (urgency == "medium" and importance_score >= 70)
                    or (urgency == "low" and importance_score >= 75)
                )

                if not passes_importance:
                    if urgency == "breaking" and imp_score < 6:
                        symbol_impact = None
                    elif urgency == "high" and (imp_score < min_impact_score or ai_confidence < 50):
                        symbol_impact = None
                    elif urgency == "medium" and (imp_score < 8 or ai_confidence < 70):
                        symbol_impact = None
                    elif urgency == "low":
                        symbol_impact = None  # low urgency must pass importance gate

                if symbol_impact and not item.get("show_on_chart", True) and importance_score < 70:
                    symbol_impact = None
            
            if not symbol_impact:
                continue

            direction = _normalize_marker_direction(symbol_impact.get("direction", "neutral"))
            score = int(symbol_impact.get("score", 5) or 5)
            marker = {
                "id": item["id"],
                "time": item["timestamp"],
                "position": _marker_position_for(direction, "news"),
                "color": _marker_color_for(direction, "news", urgency),
                "shape": _marker_shape_for(direction, "news", urgency),
                "text": _marker_text_for("news", urgency),
                "size": _marker_size_for(score, importance_score, "news", urgency),
                "headline": item.get("headline_tr") or item["headline"],
                "headline_en": item["headline"],
                "direction": direction,
                "score": score,
                "urgency": urgency,
                "catalyst_type": "news",
                "is_economic_event": False,
                "is_earnings_event": False,
                "event_name": symbol_impact.get("event_name"),
                "event_id": None,
                "reasoning_tr": symbol_impact.get("reasoning_tr", ""),
                "importance_level": importance_level,
                "importance_score": importance_score,
                "importance_reason": item.get("importance_reason"),
                "url": item.get("url", ""),
                "ai_confidence": ai_confidence,
            }
            markers.append(marker)

        economic_events = generate_economic_events_between(start_time.replace(tzinfo=timezone.utc), end_time)
        for event in economic_events:
            affected_symbols = event.get("affected_symbols") or []
            if affected_symbols and not any(symbols_match(symbol, impacted) for impacted in affected_symbols):
                continue

            importance_score = int(event.get("importance_score") or 0)
            if importance_score <= 0:
                impact_label = str(event.get("impact") or "Medium").lower()
                importance_score = {"high": 90, "medium": 68, "low": 45}.get(impact_label, 60)
            if importance_score < 60:
                continue

            direction = _normalize_marker_direction(event.get("predicted_direction"))
            score = max(4, min(10, round(importance_score / 10)))
            urgency = "breaking" if importance_score >= 88 else "high" if importance_score >= 72 else "medium"
            markers.append({
                "id": f"{event.get('id')}:{event.get('timestamp')}",
                "time": event.get("timestamp"),
                "position": _marker_position_for(direction, "economic"),
                "color": _marker_color_for(direction, "economic", urgency),
                "shape": _marker_shape_for(direction, "economic", urgency),
                "text": _marker_text_for("economic", urgency),
                "size": _marker_size_for(score, importance_score, "economic", urgency),
                "headline": event.get("title_tr") or event.get("title"),
                "headline_en": event.get("title"),
                "direction": direction,
                "score": score,
                "urgency": urgency,
                "catalyst_type": "economic",
                "is_economic_event": True,
                "is_earnings_event": False,
                "event_name": event.get("title"),
                "event_id": event.get("id"),
                "reasoning_tr": event.get("impact_analysis_tr") or event.get("why_it_matters_tr") or event.get("title_tr") or "",
                "importance_level": event.get("importance_level"),
                "importance_score": importance_score,
                "importance_reason": event.get("importance_reason"),
                "url": event.get("url", ""),
                "ai_confidence": _normalize_article_confidence(event.get("confidence") or 0),
            })

        earnings_events = generate_earnings_events_between(start_time.replace(tzinfo=timezone.utc), end_time)
        for event in earnings_events:
            affected_symbols = event.get("affected_symbols") or []
            if affected_symbols and not any(symbols_match(symbol, impacted) for impacted in affected_symbols):
                continue

            importance_score = int(event.get("importance_score") or 0)
            if importance_score <= 0:
                ticker = str(event.get("ticker") or "").upper()
                importance_score = 80 if ticker in {"AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA"} else 68
            if importance_score < 58:
                continue

            direction = _normalize_marker_direction(event.get("predicted_direction"))
            score = max(4, min(10, round(importance_score / 10)))
            urgency = "high" if importance_score >= 72 else "medium"
            markers.append({
                "id": f"{event.get('id')}:{event.get('timestamp')}",
                "time": event.get("timestamp"),
                "position": _marker_position_for(direction, "earnings"),
                "color": _marker_color_for(direction, "earnings", urgency),
                "shape": _marker_shape_for(direction, "earnings", urgency),
                "text": _marker_text_for("earnings", urgency),
                "size": _marker_size_for(score, importance_score, "earnings", urgency),
                "headline": event.get("company") or event.get("ticker"),
                "headline_en": event.get("company") or event.get("ticker"),
                "direction": direction,
                "score": score,
                "urgency": urgency,
                "catalyst_type": "earnings",
                "is_economic_event": False,
                "is_earnings_event": True,
                "event_name": event.get("company"),
                "event_id": event.get("id"),
                "reasoning_tr": event.get("analysis_tr") or event.get("analysis") or "",
                "importance_level": event.get("importance_level"),
                "importance_score": importance_score,
                "importance_reason": event.get("importance_reason"),
                "url": event.get("url", ""),
                "ai_confidence": _normalize_article_confidence(event.get("confidence") or 0),
            })

        deduped_markers: List[Dict[str, Any]] = []
        seen_keys = set()
        for marker in markers:
            marker_key = (marker.get("id"), marker.get("time"), marker.get("catalyst_type"))
            if marker_key in seen_keys:
                continue
            seen_keys.add(marker_key)
            deduped_markers.append(marker)

        deduped_markers.sort(key=lambda x: x["time"], reverse=True)
        deduped_markers = deduped_markers[:max_markers]
        deduped_markers.sort(key=lambda x: x["time"], reverse=False)
        
        return {
            "success": True,
            "symbol": symbol,
            "count": len(deduped_markers),
            "filters_applied": {
                "min_impact_score": min_impact_score,
                "max_markers": max_markers,
                "urgency_filter": "news + economic + earnings"
            },
            "markers": deduped_markers
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/candle-news/{symbol}")
async def get_news_for_candle(
    symbol: str,
    candle_timestamp: str = Query(..., description="ISO timestamp of the candle"),
    candle_open: float = Query(..., description="Candle open price"),
    candle_close: float = Query(..., description="Candle close price"),
    candle_high: float = Query(..., description="Candle high price"),
    candle_low: float = Query(..., description="Candle low price"),
    timeframe: str = Query("1h", description="Candle timeframe"),
    lang: str = Query("en", description="Preferred content language")
):
    """
    INTELLIGENT: Get news that likely caused a specific candle's movement.
    Only returns HIGH RELEVANCE news (max 5 items).
    """
    try:
        from services.news_candle_matcher import get_news_candle_matcher
        
        matcher = get_news_candle_matcher()
        
        matched_news = await matcher.match_news_to_candle_simple_ai(
            symbol=symbol,
            candle_timestamp=candle_timestamp,
            candle_open=candle_open,
            candle_close=candle_close,
            candle_high=candle_high,
            candle_low=candle_low,
            timeframe=timeframe,
        )
        
        # Format response
        formatted_news = []
        for news in matched_news:
            cleaned_news = _sanitize_news_item(news)
            symbol_impact = news.get("symbol_impact", {})
            event_payload = news.get("event_payload") or {}
            formatted_news.append({
                "id": cleaned_news.get("id"),
                "headline": cleaned_news.get("headline_tr") or cleaned_news.get("headline"),
                "headline_en": cleaned_news.get("headline") or "",
                "summary_en": cleaned_news.get("summary_en") or cleaned_news.get("headline") or "",
                "summary_tr": cleaned_news.get("summary_tr") or "",
                "analysis_en": cleaned_news.get("analysis_en") or cleaned_news.get("summary_en") or cleaned_news.get("headline") or "",
                "analysis_tr": cleaned_news.get("analysis_tr") or "",
                "timestamp": cleaned_news.get("timestamp"),
                "source": cleaned_news.get("source"),
                "catalyst_type": news.get("catalyst_type", "news"),
                "match_quality": news.get("match_quality", "matched"),
                "urgency": cleaned_news.get("urgency"),
                "score": symbol_impact.get("score", 5),
                "direction": symbol_impact.get("direction", "neutral"),
                "reasoning": symbol_impact.get("reasoning") or news.get("importance_reason") or "",
                "reasoning_tr": news.get("ai_reasoning_tr") or symbol_impact.get("reasoning_tr", ""),
                "relevance_score": round(news.get("relevance_score", 0), 2),
                "importance_level": cleaned_news.get("importance_level"),
                "importance_score": cleaned_news.get("importance_score"),
                "importance_reason": news.get("ai_reasoning_tr") or news.get("importance_reason") or symbol_impact.get("reasoning_tr", ""),
                "ai_model": cleaned_news.get("ai_model"),
                "ai_confidence": cleaned_news.get("ai_confidence"),
                "ai_match_confidence": news.get("ai_match_confidence"),
                "event_id": event_payload.get("id"),
                "affected_symbols": event_payload.get("affected_symbols") or [symbol],
                "url": cleaned_news.get("url", ""),
            })

        formatted_news = await _localize_candle_news_items(formatted_news, _normalize_lang(lang))
        formatted_news = [_sanitize_news_item(item) for item in formatted_news]
        
        # Calculate candle stats
        change_pct = ((candle_close - candle_open) / candle_open) * 100 if candle_open != 0 else 0
        range_pct = ((candle_high - candle_low) / candle_open) * 100 if candle_open != 0 else 0
        
        return {
            "success": True,
            "symbol": symbol,
            "candle": {
                "timestamp": candle_timestamp,
                "change_pct": round(change_pct, 2),
                "range_pct": round(range_pct, 2),
                "is_significant": abs(change_pct) > 0.5 or range_pct > 1.0
            },
            "news_count": len(formatted_news),
            "news": formatted_news
        }
        
    except Exception as e:
        import traceback
        print(f"[CandleNews] Error: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/economic-calendar")
async def get_economic_calendar(
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format (default: today)"),
    currency: Optional[str] = Query(None, description="Filter by currency: USD, EUR, GBP, etc.")
):
    """
    Get economic calendar events for today or specific date
    """
    try:
        from services.economic_calendar_service import get_calendar_service
        
        calendar = get_calendar_service()
        events = await calendar.fetch_today_events()
        
        if currency:
            events = [e for e in events if e.currency == currency.upper()]
        
        return {
            "success": True,
            "date": date or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "count": len(events),
            "events": [
                {
                    "id": e.id,
                    "timestamp": e.timestamp.isoformat(),
                    "currency": e.currency,
                    "event_name": e.event_name,
                    "impact": e.impact,
                    "actual": e.actual,
                    "forecast": e.forecast,
                    "previous": e.previous,
                    "affected_symbols": e.affected_symbols,
                    "is_earnings": e.is_earnings,
                    "company": e.company
                }
                for e in events
            ]
        }
    
    except Exception as e:
        import traceback
        print(f"[EconomicCalendar] Error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/earnings")
async def get_earnings_calendar(
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format (default: today)"),
    symbol: Optional[str] = Query(None, description="Filter by symbol")
):
    """
    Get earnings calendar events for NASDAQ-100 and DAX companies
    """
    try:
        # For now return mock data - will integrate real data source later
        mock_earnings = [
            {
                "id": "AAPL_2026_03_05",
                "timestamp": "2026-03-05T16:00:00+00:00",
                "currency": "USD",
                "event_name": "Apple Inc. Q1 2026 Earnings",
                "impact": "High",
                "actual": None,
                "forecast": "$1.85 EPS",
                "previous": "$1.78 EPS",
                "affected_symbols": ["AAPL", "NDX", "QQQ"],
                "is_earnings": True,
                "company": "Apple Inc."
            },
            {
                "id": "MSFT_2026_03_06",
                "timestamp": "2026-03-06T16:00:00+00:00",
                "currency": "USD",
                "event_name": "Microsoft Corp. Q2 2026 Earnings",
                "impact": "High",
                "actual": None,
                "forecast": "$2.92 EPS",
                "previous": "$2.85 EPS",
                "affected_symbols": ["MSFT", "NDX", "QQQ"],
                "is_earnings": True,
                "company": "Microsoft Corp."
            }
        ]
        
        if symbol:
            mock_earnings = [e for e in mock_earnings if symbol.upper() in e.get("affected_symbols", [])]
        
        return {
            "success": True,
            "date": date or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "count": len(mock_earnings),
            "events": mock_earnings
        }
    
    except Exception as e:
        print(f"[EarningsCalendar] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/by-category/{category}")
async def get_news_by_category(
    category: str,
    hours: int = Query(24, ge=1, le=168),
    limit: int = Query(50, ge=1, le=200)
):
    """
    Get news by category (forex, markets, business, commodities, crypto)
    """
    try:
        supabase = get_supabase_client()
        
        start_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        result = (
            supabase.table("enriched_news")
            .select("*")
            .eq("category", category)
            .gte("timestamp", start_time.isoformat())
            .order("timestamp", desc=True)
            .limit(limit)
            .execute()
        )
        
        # Handle both old and new Supabase response formats
        if hasattr(result, 'data'):
            data = result.data or []
        elif isinstance(result, dict):
            data = result.get('data', []) or []
        else:
            data = []
        
        return {
            "success": True,
            "category": category,
            "count": len(data),
            "data": data
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/force-refresh")
async def force_refresh(background_tasks: BackgroundTasks):
    """
    Manually trigger RSS feed refresh (admin only)
    """
    async def run_refresh():
        aggregator = get_rss_aggregator()
        stats = await aggregator.run_aggregation_cycle()
        print(f"[RSS] Force refresh completed: {stats}")
    
    background_tasks.add_task(run_refresh)
    
    return {
        "success": True,
        "message": "RSS refresh triggered in background"
    }


@router.post("/backfill-translations")
async def backfill_turkish_translations(
    hours: int = Query(48, ge=1, le=168, description="Hours of news to translate"),
    limit: int = Query(100, ge=1, le=500, description="Max items to process")
):
    """
    Admin endpoint: Add Turkish translations to existing news without them
    """
    try:
        supabase = get_supabase_client()
        
        start_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        # Get news without headline_tr
        result = (
            supabase.table("enriched_news")
            .select("*")
            .is_("headline_tr", "null")
            .gte("timestamp", start_time.isoformat())
            .order("timestamp", desc=True)
            .limit(limit)
            .execute()
        )
        
        if hasattr(result, 'data'):
            items = result.data or []
        elif isinstance(result, dict):
            items = result.get('data', []) or []
        else:
            items = []
        
        if not items:
            return {
                "success": True,
                "message": "No items need translation",
                "processed": 0
            }
        
        # Simple translation helper
        translations = {
            "earnings": "kazanç", "revenue": "gelir", "profit": "kâr", "loss": "zarar",
            "beat": "tahminleri aştı", "miss": "tahminleri karşılayamadı",
            "growth": "büyüme", "decline": "düşüş", "surge": "yükseliş", "drop": "düşüş",
            "rise": "yükseliş", "fall": "düşüş", "strong": "güçlü", "weak": "zayıf",
            "market": "piyasa", "stock": "hisse", "price": "fiyat", "trading": "ticaret",
            "rate": "oran", "fed": "Fed", "cut": "indirim", "hike": "artış",
        }
        
        def quick_translate(text):
            if not text:
                return text
            translated = text.lower()
            for en, tr in translations.items():
                translated = translated.replace(en, tr)
            if translated == text.lower():
                return f"[TR] {text}"
            return translated.capitalize()
        
        updated = 0
        for item in items:
            try:
                headline_tr = quick_translate(item.get("headline", ""))
                content = item.get("content", "")
                content_tr = quick_translate(content[:200] + "..." if len(content) > 200 else content)
                
                # Update impacts with reasoning_tr
                impacts = item.get("impacts", [])
                for imp in impacts:
                    if "reasoning_tr" not in imp or not imp["reasoning_tr"]:
                        imp["reasoning_tr"] = ""
                
                update_result = supabase.table("enriched_news").eq("id", item["id"]).update({
                    "headline_tr": headline_tr,
                    "content_tr": content_tr,
                    "impacts": impacts
                })
                if isinstance(update_result, dict) and update_result.get("error"):
                    raise Exception(update_result["error"])
                
                updated += 1
            except Exception as e:
                print(f"[Backfill] Error updating {item.get('id')}: {e}")
                continue
        
        return {
            "success": True,
            "message": f"Updated {updated} items with Turkish translations",
            "processed": updated,
            "total": len(items)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-ai")
async def test_ai_analysis(
    headline: str = Query(..., description="News headline to analyze"),
    content: str = Query("", description="News content/summary"),
    source: str = Query("manual", description="News source")
):
    """
    TEST endpoint: Send a news item to Claude/DeepSeek AI and see the raw response
    Use this to verify AI is working correctly
    """
    try:
        import os
        import logging
        from services.news_analyzer_v2 import get_real_analyzer, DEEPSEEK_API_KEY
        
        logger = logging.getLogger(__name__)
        
        # Check API keys - CORRECT ENV VAR NAME
        anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
        deepseek_key = os.getenv("DEEP_SEEKR1", "")  # This is the correct env var name!
        
        logger.info(f"[Test-AI] ANTHROPIC_API_KEY present: {bool(anthropic_key)}")
        logger.info(f"[Test-AI] DEEP_SEEKR1 present: {bool(deepseek_key)}")
        logger.info(f"[Test-AI] Module-level DEEPSEEK_API_KEY present: {bool(DEEPSEEK_API_KEY)}")
        
        # Check for mismatch
        if deepseek_key and not DEEPSEEK_API_KEY:
            logger.error("[Test-AI] MISMATCH: DEEP_SEEKR1 is set but module didn't load it!")
        
        # Call AI
        logger.info(f"[Test-AI] Analyzing: {headline[:60]}...")
        analyzer = get_real_analyzer()
        
        result = await analyzer.analyze(
            headline=headline,
            content=content,
            source=source
        )
        
        # Determine which AI was used
        ai_used = "fallback"
        if result.confidence >= 70 and result.headline_tr and not result.headline_tr.startswith("["):
            ai_used = "deepseek"  # Real DeepSeek analysis
        elif result.confidence >= 60 and result.headline_tr and len(result.headline_tr) > 10:
            ai_used = "deepseek_partial"
        
        return {
            "success": True,
            "ai_used": ai_used,
            "api_keys": {
                "anthropic": bool(anthropic_key),
                "deepseek_env": bool(deepseek_key),
                "deepseek_module": bool(DEEPSEEK_API_KEY)
            },
            "analysis": {
                "summary_en": result.summary_en,
                "summary_tr": result.summary_tr,
                "analysis_en": result.analysis_en,
                "analysis_tr": result.analysis_tr,
                "headline_tr": result.headline_tr,
                "content_tr": result.content_tr,
                "sentiment": result.sentiment,
                "volatility_expectation": result.volatility_expectation,
                "urgency": result.urgency,
                "importance_level": result.importance_level,
                "importance_score": result.importance_score,
                "importance_reason": result.importance_reason,
                "ai_model": result.ai_model,
                "confidence": result.confidence,
                "impacts": [
                    {
                        "symbol": imp.symbol,
                        "direction": imp.direction,
                        "score": imp.score,
                        "confidence": imp.confidence,
                        "reasoning": imp.reasoning,
                        "reasoning_tr": imp.reasoning_tr
                    }
                    for imp in result.impacts
                ]
            }
        }
        
    except Exception as e:
        import os
        import traceback
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
            "api_keys": {
                "anthropic": bool(os.getenv("ANTHROPIC_API_KEY", "")),
                "deepseek": bool(os.getenv("DEEP_SEEKR1", ""))
            }
        }


@router.get("/stats")
async def get_rss_stats(hours: int = Query(24, ge=1, le=168)):
    """
    Get RSS aggregation statistics
    """
    try:
        supabase = get_supabase_client()
        
        start_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        # Get counts by urgency
        urgency_counts = (
            supabase.table("enriched_news")
            .select("urgency", count="exact")
            .gte("timestamp", start_time.isoformat())
            .execute()
        )
        
        # Get counts by sentiment
        sentiment_response = (
            supabase.table("enriched_news")
            .select("sentiment")
            .gte("timestamp", start_time.isoformat())
            .execute()
        )
        
        # Handle sentiment response
        if hasattr(sentiment_response, 'data'):
            sentiment_data = sentiment_response.data or []
        elif isinstance(sentiment_response, dict):
            sentiment_data = sentiment_response.get('data', []) or []
        else:
            sentiment_data = []
        
        sentiment_counts = {}
        for item in sentiment_data:
            sentiment = item.get("sentiment", "neutral")
            sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
        
        # Get counts by source
        source_response = (
            supabase.table("enriched_news")
            .select("source")
            .gte("timestamp", start_time.isoformat())
            .execute()
        )
        
        # Handle source response
        if hasattr(source_response, 'data'):
            source_data = source_response.data or []
        elif isinstance(source_response, dict):
            source_data = source_response.get('data', []) or []
        else:
            source_data = []
        
        source_counts = {}
        for item in source_data:
            source = item.get("source", "unknown")
            source_counts[source] = source_counts.get(source, 0) + 1
        
        # Get top impacted symbols
        all_news_result = (
            supabase.table("enriched_news")
            .select("impacts")
            .gte("timestamp", start_time.isoformat())
            .execute()
        )
        
        # Handle all news response
        if hasattr(all_news_result, 'data'):
            all_news = all_news_result.data or []
        elif isinstance(all_news_result, dict):
            all_news = all_news_result.get('data', []) or []
        else:
            all_news = []
        
        symbol_counts = {}
        for item in all_news:
            for impact in item.get("impacts", []):
                symbol = impact.get("symbol")
                if symbol:
                    symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1
        
        # Handle urgency counts
        if hasattr(urgency_counts, 'count'):
            total_items = urgency_counts.count
        elif hasattr(urgency_counts, 'data'):
            urgency_data = urgency_counts.data or []
            total_items = len(urgency_data)
        elif isinstance(urgency_counts, dict):
            urgency_data = urgency_counts.get('data', []) or []
            total_items = len(urgency_data)
        else:
            urgency_data = []
            total_items = 0
        
        return {
            "success": True,
            "period_hours": hours,
            "total_items": total_items,
            "by_urgency": {
                "breaking": len([x for x in urgency_data if x.get("urgency") == "breaking"]),
                "high": len([x for x in urgency_data if x.get("urgency") == "high"]),
                "medium": len([x for x in urgency_data if x.get("urgency") == "medium"]),
                "low": len([x for x in urgency_data if x.get("urgency") == "low"]),
            },
            "by_sentiment": sentiment_counts,
            "by_source": source_counts,
            "top_symbols": dict(sorted(symbol_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_rss_news(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(20, ge=1, le=100)
):
    """
    Search RSS news by keyword in title or content
    """
    try:
        supabase = get_supabase_client()
        
        # Search in headline (case-insensitive)
        result = (
            supabase.table("enriched_news")
            .select("*")
            .ilike("headline", f"%{q}%")
            .order("timestamp", desc=True)
            .limit(limit)
            .execute()
        )
        
        # Handle response
        if hasattr(result, 'data'):
            data = result.data or []
        elif isinstance(result, dict):
            data = result.get('data', []) or []
        else:
            data = []
        
        return {
            "success": True,
            "query": q,
            "count": len(data),
            "data": data
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/keywords")
async def get_monitored_keywords():
    """
    Get list of monitored keywords for RSS filtering
    """
    from services.rss_aggregator import HIGH_PRIORITY_KEYWORDS, SPAM_KEYWORDS
    
    return {
        "success": True,
        "high_priority_keywords": HIGH_PRIORITY_KEYWORDS,
        "spam_keywords": SPAM_KEYWORDS,
        "total_monitored": len(HIGH_PRIORITY_KEYWORDS),
    }


@router.get("/diagnostics")
async def get_rss_diagnostics():
    """
    Diagnostic endpoint: Check API key status, analysis health, and recent stats.
    Shows whether DeepSeek AI is actually analyzing news or falling back to rules.
    """
    import os
    
    try:
        supabase = get_supabase_client()
        
        # Check API key
        deepseek_key = os.getenv("DEEP_SEEKR1", "")
        anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
        
        # Get recent news stats
        start_time = datetime.now(timezone.utc) - timedelta(hours=24)
        
        result = (
            supabase.table("enriched_news")
            .select("id, headline, timestamp, headline_tr, ai_confidence, urgency, impacts, source, ai_model, importance_score")
            .gte("timestamp", start_time.isoformat())
            .order("timestamp", desc=True)
            .limit(100)
            .execute()
        )
        
        if hasattr(result, 'data'):
            items = result.data or []
        elif isinstance(result, dict):
            items = result.get('data', []) or []
        else:
            items = []
        
        # Analyze: how many used real AI vs fallback?
        ai_analyzed = 0
        fallback_analyzed = 0
        no_impacts = 0
        identical_impacts_count = 0
        
        # Track impact patterns to detect identical results
        impact_patterns = {}
        
        for item in items:
            sanitized_item = _sanitize_news_item(item)
            headline_tr = sanitized_item.get("headline_tr", "")
            confidence = sanitized_item.get("ai_confidence", 0)
            impacts = sanitized_item.get("impacts", [])
            ai_model = str(sanitized_item.get("ai_model", "") or "").lower()
            
            # Detect fallback: headline_tr starts with [TR] or low confidence
            if ai_model == "fallback" or headline_tr.startswith("[TR]") or confidence <= 50:
                fallback_analyzed += 1
            else:
                ai_analyzed += 1
            
            if not impacts:
                no_impacts += 1
            
            # Track impact pattern
            pattern_key = "|".join(
                f"{imp.get('symbol')}:{imp.get('direction')}" 
                for imp in sorted(impacts, key=lambda x: x.get("symbol", ""))
            )
            impact_patterns[pattern_key] = impact_patterns.get(pattern_key, 0) + 1
        
        # Find most common pattern (identical results indicator)
        most_common_pattern = max(impact_patterns.items(), key=lambda x: x[1]) if impact_patterns else ("none", 0)
        
        return {
            "success": True,
            "api_keys": {
                "DEEP_SEEKR1": "✅ SET" if deepseek_key else "❌ NOT SET",
                "ANTHROPIC_API_KEY": "✅ SET" if anthropic_key else "❌ NOT SET",
            },
            "last_24h_stats": {
                "total_news": len(items),
                "ai_analyzed": ai_analyzed,
                "fallback_analyzed": fallback_analyzed,
                "no_impacts": no_impacts,
                "ai_ratio": f"{(ai_analyzed / max(len(items), 1)) * 100:.1f}%",
            },
            "identical_pattern_analysis": {
                "most_common_pattern": most_common_pattern[0],
                "occurrences": most_common_pattern[1],
                "total_patterns": len(impact_patterns),
                "warning": "⚠️ Many identical patterns detected — fallback rule-based analysis likely" if most_common_pattern[1] > 5 else "✅ Diverse analysis patterns",
            },
            "latest_news_sample": [
                {
                    "headline": item.get("headline", "")[:80],
                    "headline_tr": _sanitize_news_item(item).get("headline_tr", "")[:80],
                    "confidence": _sanitize_news_item(item).get("ai_confidence", 0),
                    "importance_score": item.get("importance_score"),
                    "ai_model": item.get("ai_model"),
                    "impacts_count": len(_sanitize_news_item(item).get("impacts", [])),
                    "source": item.get("source", ""),
                    "is_fallback": (str(item.get("ai_model", "") or "").lower() == "fallback")
                                   or _sanitize_news_item(item).get("headline_tr", "").startswith("[TR]")
                                   or _sanitize_news_item(item).get("ai_confidence", 0) <= 50,
                }
                for item in items[:5]
            ],
        }
    
    except Exception as e:
        import os
        return {
            "success": False,
            "error": str(e),
            "api_keys": {
                "DEEP_SEEKR1": "✅ SET" if os.getenv("DEEP_SEEKR1", "") else "❌ NOT SET",
                "ANTHROPIC_API_KEY": "✅ SET" if os.getenv("ANTHROPIC_API_KEY", "") else "❌ NOT SET",
            },
        }


@router.post("/re-analyze")
async def re_analyze_fallback_news(
    background_tasks: BackgroundTasks,
    hours: int = Query(48, ge=1, le=168, description="Re-analyze news from last N hours"),
    limit: int = Query(50, ge=1, le=200, description="Max items to re-analyze"),
):
    """
    Re-analyze news items that used fallback (rule-based) instead of real AI.
    Detects fallback items by: headline_tr starting with '[TR]' or low ai_confidence.
    Re-sends them to DeepSeek for proper per-news analysis.
    """
    import os
    
    # Check if DeepSeek key is available
    deepseek_key = os.getenv("DEEP_SEEKR1", "")
    if not deepseek_key:
        raise HTTPException(
            status_code=400, 
            detail="DEEP_SEEKR1 environment variable not set. Cannot re-analyze without DeepSeek API key."
        )
    
    async def run_re_analysis():
        try:
            supabase = get_supabase_client()
            from services.news_analyzer_v2 import get_real_analyzer
            
            start_time = datetime.now(timezone.utc) - timedelta(hours=hours)
            
            # Get fallback-analyzed news (headline_tr starts with [TR] or low confidence)
            result = (
                supabase.table("enriched_news")
                .select("*")
                .gte("timestamp", start_time.isoformat())
                .order("timestamp", desc=True)
                .limit(limit * 2)  # Fetch more to filter
                .execute()
            )
            
            if hasattr(result, 'data'):
                items = result.data or []
            elif isinstance(result, dict):
                items = result.get('data', []) or []
            else:
                items = []
            
            # Filter to only fallback items
            fallback_items = [
                item for item in items
                if (
                    str(item.get("ai_model", "") or "").lower() == "fallback" or
                    item.get("headline_tr", "").startswith("[TR]") or
                    (item.get("ai_confidence", 0) <= 50) or
                    _has_identical_pattern(item.get("impacts", []))
                )
            ][:limit]
            
            print(f"[Re-analyze] Found {len(fallback_items)} fallback items to re-analyze")
            
            analyzer = get_real_analyzer()
            re_analyzed = 0
            errors = 0
            
            for item in fallback_items:
                try:
                    result = await analyzer.analyze(
                        headline=item.get("headline", ""),
                        content=item.get("content", ""),
                        source=item.get("source", "")
                    )
                    
                    # Check if result is real AI (not fallback)
                    if result.ai_model != "fallback" and result.confidence >= 60 and result.headline_tr and not result.headline_tr.startswith("["):
                        # Update in database
                        new_impacts = [
                            {
                                "symbol": imp.symbol,
                                "direction": imp.direction,
                                "score": imp.score,
                                "confidence": imp.confidence,
                                "reasoning": imp.reasoning,
                                "reasoning_tr": imp.reasoning_tr,
                                "emoji": "📈" if imp.direction == "bullish" else "📉" if imp.direction == "bearish" else "➡️",
                            }
                            for imp in result.impacts
                        ]
                        
                        update_data = {
                            "summary_en": result.summary_en,
                            "summary_tr": result.summary_tr,
                            "analysis_en": result.analysis_en,
                            "analysis_tr": result.analysis_tr,
                            "headline_tr": result.headline_tr,
                            "content_tr": result.content_tr,
                            "impacts": new_impacts,
                            "sentiment": result.sentiment,
                            "volatility_expectation": result.volatility_expectation,
                            "urgency": result.urgency,
                            "importance_level": result.importance_level,
                            "importance_score": result.importance_score,
                            "importance_reason": result.importance_reason,
                            "ai_model": result.ai_model,
                            "ai_confidence": result.confidence,
                            "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
                            "show_on_chart": (
                                result.urgency in ["high", "breaking"]
                                or result.importance_score >= 70
                                or any(imp.score >= 6 for imp in result.impacts)
                            ),
                        }
                        
                        update_result = supabase.table("enriched_news").eq("id", item["id"]).update(update_data)
                        if isinstance(update_result, dict) and update_result.get("error"):
                            raise Exception(update_result["error"])
                        re_analyzed += 1
                        print(f"[Re-analyze] ✅ Updated: {item.get('headline', '')[:60]}...")
                    else:
                        print(f"[Re-analyze] ⚠️ Still fallback for: {item.get('headline', '')[:60]}...")
                        
                except Exception as e:
                    print(f"[Re-analyze] ❌ Error: {e}")
                    errors += 1
                    
                # Small delay to avoid rate limiting
                import asyncio
                await asyncio.sleep(1)
            
            print(f"[Re-analyze] Complete: {re_analyzed} updated, {errors} errors out of {len(fallback_items)} items")
            
        except Exception as e:
            print(f"[Re-analyze] Fatal error: {e}")
    
    background_tasks.add_task(run_re_analysis)
    
    return {
        "success": True,
        "message": f"Re-analysis started in background. Will process up to {limit} fallback items from last {hours}h.",
        "api_key_status": "✅ SET" if deepseek_key else "❌ NOT SET",
    }


def _has_identical_pattern(impacts: list) -> bool:
    """Check if impacts match the common fallback pattern (all same direction)"""
    if not impacts or len(impacts) < 3:
        return False
    
    # Check if this is the generic geopolitical pattern
    symbols = {imp.get("symbol") for imp in impacts}
    if symbols >= {"XAUUSD", "USOIL", "VIX"}:
        # All bullish except one bearish = generic pattern
        directions = [imp.get("direction") for imp in impacts]
        bullish_count = directions.count("bullish")
        if bullish_count >= 3:
            return True
    
    return False


# Background task runner (to be called by scheduler)
async def run_rss_aggregation() -> dict:
    """
    Run RSS aggregation cycle (called by background scheduler)
    """
    aggregator = get_rss_aggregator()
    stats = await aggregator.run_aggregation_cycle()
    return stats

