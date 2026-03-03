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


# Background task runner (to be called by scheduler)
async def run_rss_aggregation() -> dict:
    """
    Run RSS aggregation cycle (called by background scheduler)
    """
    aggregator = get_rss_aggregator()
    stats = await aggregator.run_aggregation_cycle()
    return stats
