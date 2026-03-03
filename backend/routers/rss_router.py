"""
RSS Router - API endpoints for RSS news aggregation
"""

from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel

from services.rss_aggregator import get_rss_aggregator, RSS_SOURCES
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
    category: str
    url: str
    impacts: List[dict]
    sentiment: str
    volatility_expectation: str
    urgency: str
    ai_confidence: float
    duplicate_of: Optional[str]
    sources: List[str]

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
    skip_ai_filtered: bool = Query(True, description="Skip low-priority non-AI analyzed items")
):
    """
    Get RSS news with optional filtering
    """
    try:
        supabase = get_supabase_client()
        
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Build query
        query = (
            supabase.table("enriched_news")
            .select("*")
            .gte("timestamp", start_time.isoformat())
            .order("timestamp", desc=True)
            .limit(limit)
        )
        
        # Apply filters
        if urgency:
            query = query.eq("urgency", urgency)
        
        if sentiment:
            query = query.eq("sentiment", sentiment)
        
        # Skip low priority items if requested
        if skip_ai_filtered:
            query = query.neq("urgency", "low")
        
        result = query.execute()
        
        # Handle both old and new Supabase response formats
        if hasattr(result, 'data'):
            items = result.data or []
        elif isinstance(result, dict):
            items = result.get('data', []) or []
        else:
            items = []
        
        if not items:
            return []
        if symbol:
            items = [
                item for item in items
                if any(imp.get("symbol") == symbol or imp.get("symbol") == "*" 
                       for imp in item.get("impacts", []))
            ]
        
        # Format response - WITH TURKISH TRANSLATIONS
        return [
            RSSNewsResponse(
                id=item["id"],
                timestamp=item["timestamp"],
                source=item["source"],
                headline=item["headline"],
                headline_tr=item.get("headline_tr"),
                content=item.get("content"),
                content_tr=item.get("content_tr"),
                category=item.get("category", "general"),
                url=item.get("url", ""),
                impacts=item.get("impacts", []),
                sentiment=item.get("sentiment", "neutral"),
                volatility_expectation=item.get("volatility_expectation", "medium"),
                urgency=item.get("urgency", "medium"),
                ai_confidence=item.get("ai_confidence", 0) / 100,
                duplicate_of=item.get("duplicate_of"),
                sources=item.get("sources", [item["source"]]),
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
        
        start_time = datetime.utcnow() - timedelta(hours=1)
        
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
    hours: int = Query(24, ge=1, le=168, description="Lookback period in hours"),
    min_impact_score: int = Query(5, ge=1, le=10, description="Minimum impact score to show on chart")
):
    """
    Get news markers for chart display.
    Returns news that should be shown as markers on the candlestick chart.
    """
    try:
        supabase = get_supabase_client()
        
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Get news that:
        # 1. Has show_on_chart = true
        # 2. OR has high urgency
        # 3. OR affects the requested symbol with score >= min_impact_score
        result = (
            supabase.table("enriched_news")
            .select("*")
            .gte("timestamp", start_time.isoformat())
            .or_(f"show_on_chart.eq.true,urgency.in.(high,breaking)")
            .order("timestamp", desc=True)
            .limit(100)
            .execute()
        )
        
        # Handle both old and new Supabase response formats
        if hasattr(result, 'data'):
            items = result.data or []
        elif isinstance(result, dict):
            items = result.get('data', []) or []
        else:
            items = []
        
        # Filter for symbol-specific impacts
        markers = []
        for item in items:
            impacts = item.get("impacts", [])
            
            # Check if this news affects the requested symbol
            symbol_impact = None
            for imp in impacts:
                if imp.get("symbol") == symbol and imp.get("score", 0) >= min_impact_score:
                    symbol_impact = imp
                    break
            
            # Include if it affects this symbol or is a major economic event
            is_economic_event = any(imp.get("is_economic_event") for imp in impacts)
            
            if symbol_impact or is_economic_event or item.get("urgency") in ["breaking", "high"]:
                # Determine marker appearance
                direction = symbol_impact.get("direction", "neutral") if symbol_impact else "neutral"
                score = symbol_impact.get("score", 5) if symbol_impact else 5
                
                marker = {
                    "id": item["id"],
                    "time": item["timestamp"],
                    "position": "aboveBar" if direction == "bullish" else "belowBar" if direction == "bearish" else "inBar",
                    "color": item.get("marker_color", "#3B82F6"),
                    "shape": "circle" if item.get("urgency") == "breaking" else "square" if is_economic_event else "arrowUp" if direction == "bullish" else "arrowDown" if direction == "bearish" else "circle",
                    "text": "📰",
                    "size": 2 if score >= 8 else 1.5 if score >= 6 else 1,
                    "headline": item.get("headline_tr") or item["headline"],
                    "headline_en": item["headline"],
                    "direction": direction,
                    "score": score,
                    "urgency": item.get("urgency", "medium"),
                    "is_economic_event": is_economic_event,
                    "event_name": symbol_impact.get("event_name") if symbol_impact else None,
                    "reasoning_tr": symbol_impact.get("reasoning_tr") if symbol_impact else None,
                    "url": item.get("url", ""),
                }
                markers.append(marker)
        
        return {
            "success": True,
            "symbol": symbol,
            "count": len(markers),
            "markers": markers
        }
    
    except Exception as e:
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
            "date": date or datetime.utcnow().strftime("%Y-%m-%d"),
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
        
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
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
        
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
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
                        direction = imp.get("direction", "neutral")
                        direction_tr = "yükseliş" if direction == "bullish" else "düşüş" if direction == "bearish" else "nötr"
                        imp["reasoning_tr"] = f"{imp.get('symbol', 'Sembol')} için {direction_tr} etki"
                
                supabase.table("enriched_news").update({
                    "headline_tr": headline_tr,
                    "content_tr": content_tr,
                    "impacts": impacts
                }).eq("id", item["id"]).execute()
                
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
        from services.news_analyzer_v2 import get_real_analyzer
        
        # Check API keys
        anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
        deepseek_key = os.getenv("DEEPSEEK_API_KEY", "")
        
        print(f"[Test] ANTHROPIC_API_KEY present: {bool(anthropic_key)}")
        print(f"[Test] DEEPSEEK_API_KEY present: {bool(deepseek_key)}")
        
        # Call AI
        print(f"[Test] Analyzing: {headline[:60]}...")
        analyzer = get_real_analyzer()
        
        import asyncio
        result = await analyzer.analyze(
            headline=headline,
            content=content,
            source=source
        )
        
        # Determine which AI was used (Claude or DeepSeek or fallback)
        ai_used = "fallback"
        if result.confidence >= 70 and result.headline_tr and not result.headline_tr.startswith("["):
            ai_used = "claude"  # Claude yüksek kaliteli çeviri yapar
        elif result.headline_tr and result.headline_tr.startswith("["):
            ai_used = "fallback"
        
        return {
            "success": True,
            "ai_used": ai_used,
            "api_keys": {
                "anthropic": bool(anthropic_key),
                "deepseek": bool(deepseek_key)
            },
            "analysis": {
                "headline_tr": result.headline_tr,
                "content_tr": result.content_tr,
                "sentiment": result.sentiment,
                "volatility_expectation": result.volatility_expectation,
                "urgency": result.urgency,
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
        return {
            "success": False,
            "error": str(e),
            "api_keys": {
                "anthropic": bool(os.getenv("ANTHROPIC_API_KEY", "")),
                "deepseek": bool(os.getenv("DEEPSEEK_API_KEY", ""))
            }
        }


@router.get("/stats")
async def get_rss_stats(hours: int = Query(24, ge=1, le=168)):
    """
    Get RSS aggregation statistics
    """
    try:
        supabase = get_supabase_client()
        
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
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
        start_time = datetime.utcnow() - timedelta(hours=24)
        
        result = (
            supabase.table("enriched_news")
            .select("id, timestamp, headline_tr, ai_confidence, urgency, impacts, source")
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
            headline_tr = item.get("headline_tr", "")
            confidence = item.get("ai_confidence", 0)
            impacts = item.get("impacts", [])
            
            # Detect fallback: headline_tr starts with [TR] or low confidence
            if headline_tr.startswith("[TR]") or confidence <= 50:
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
                    "headline_tr": item.get("headline_tr", "")[:80],
                    "confidence": item.get("ai_confidence", 0),
                    "impacts_count": len(item.get("impacts", [])),
                    "source": item.get("source", ""),
                    "is_fallback": item.get("headline_tr", "").startswith("[TR]") or item.get("ai_confidence", 0) <= 50,
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
            
            start_time = datetime.utcnow() - timedelta(hours=hours)
            
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
                    if result.confidence >= 60 and result.headline_tr and not result.headline_tr.startswith("["):
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
                            "headline_tr": result.headline_tr,
                            "content_tr": result.content_tr,
                            "impacts": new_impacts,
                            "sentiment": result.sentiment,
                            "volatility_expectation": result.volatility_expectation,
                            "urgency": result.urgency,
                            "ai_confidence": result.confidence,
                            "analysis_timestamp": datetime.utcnow().isoformat(),
                            "show_on_chart": result.urgency in ["high", "breaking"] or any(imp.score >= 6 for imp in result.impacts),
                        }
                        
                        supabase.table("enriched_news").update(update_data).eq("id", item["id"]).execute()
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

