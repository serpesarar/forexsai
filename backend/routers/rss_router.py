"""
RSS Router - API endpoints for RSS news aggregation
"""

from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel

from services.rss_aggregator import get_rss_aggregator, RSS_SOURCES
from database.supabase_client import supabase

router = APIRouter(prefix="/api/rss", tags=["rss"])

# Request/Response Models
class RSSNewsResponse(BaseModel):
    id: str
    timestamp: str
    source: str
    headline: str
    content: Optional[str]
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
            query = query.not_eq("urgency", "low")
        
        response = query.execute()
        
        if not response.data:
            return []
        
        # Filter by symbol if specified
        items = response.data
        if symbol:
            items = [
                item for item in items
                if any(imp.get("symbol") == symbol or imp.get("symbol") == "*" 
                       for imp in item.get("impacts", []))
            ]
        
        # Format response
        return [
            RSSNewsResponse(
                id=item["id"],
                timestamp=item["timestamp"],
                source=item["source"],
                headline=item["headline"],
                content=item.get("content"),
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
        start_time = datetime.utcnow() - timedelta(hours=1)
        
        response = (
            supabase.table("enriched_news")
            .select("*")
            .gte("timestamp", start_time.isoformat())
            .in_("urgency", ["breaking", "high"])
            .order("timestamp", desc=True)
            .limit(limit)
            .execute()
        )
        
        return {
            "success": True,
            "count": len(response.data or []),
            "data": response.data or []
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
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        response = (
            supabase.table("enriched_news")
            .select("*")
            .eq("category", category)
            .gte("timestamp", start_time.isoformat())
            .order("timestamp", desc=True)
            .limit(limit)
            .execute()
        )
        
        return {
            "success": True,
            "category": category,
            "count": len(response.data or []),
            "data": response.data or []
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


@router.get("/stats")
async def get_rss_stats(hours: int = Query(24, ge=1, le=168)):
    """
    Get RSS aggregation statistics
    """
    try:
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
        
        sentiment_counts = {}
        for item in sentiment_response.data or []:
            sentiment = item.get("sentiment", "neutral")
            sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
        
        # Get counts by source
        source_response = (
            supabase.table("enriched_news")
            .select("source")
            .gte("timestamp", start_time.isoformat())
            .execute()
        )
        
        source_counts = {}
        for item in source_response.data or []:
            source = item.get("source", "unknown")
            source_counts[source] = source_counts.get(source, 0) + 1
        
        # Get top impacted symbols
        all_news = (
            supabase.table("enriched_news")
            .select("impacts")
            .gte("timestamp", start_time.isoformat())
            .execute()
        )
        
        symbol_counts = {}
        for item in all_news.data or []:
            for impact in item.get("impacts", []):
                symbol = impact.get("symbol")
                if symbol:
                    symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1
        
        return {
            "success": True,
            "period_hours": hours,
            "total_items": urgency_counts.count if hasattr(urgency_counts, 'count') else len(urgency_counts.data or []),
            "by_urgency": {
                "breaking": len([x for x in urgency_counts.data or [] if x.get("urgency") == "breaking"]),
                "high": len([x for x in urgency_counts.data or [] if x.get("urgency") == "high"]),
                "medium": len([x for x in urgency_counts.data or [] if x.get("urgency") == "medium"]),
                "low": len([x for x in urgency_counts.data or [] if x.get("urgency") == "low"]),
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
        # Search in headline (case-insensitive)
        response = (
            supabase.table("enriched_news")
            .select("*")
            .ilike("headline", f"%{q}%")
            .order("timestamp", desc=True)
            .limit(limit)
            .execute()
        )
        
        return {
            "success": True,
            "query": q,
            "count": len(response.data or []),
            "data": response.data or []
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
