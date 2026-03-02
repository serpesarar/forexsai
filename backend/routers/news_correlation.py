"""
News-Chart Correlation API
Endpoints for matching news events with candlestick data
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import os

from database.supabase_client import get_supabase_client

router = APIRouter(prefix="/api/news-correlation", tags=["news-correlation"])


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
        candle_time = datetime.fromtimestamp(timestamp)
        start_time = candle_time - timedelta(minutes=window_minutes)
        end_time = candle_time + timedelta(minutes=window_minutes)
        
        # Fetch news in time window
        result = supabase.table("enriched_news")\
            .select("*")\
            .gte("timestamp", start_time.isoformat())\
            .lte("timestamp", end_time.isoformat())\
            .order("timestamp", desc=True)\
            .execute()
        
        # Filter news that impacts this symbol
        related_news = []
        for news in result.data:
            impacts = news.get("impacts", [])
            # Check if symbol is directly mentioned
            symbol_impact = next((i for i in impacts if i.get("symbol") == symbol), None)
            # Or check for global impacts (all symbols affected)
            global_impact = next((i for i in impacts if i.get("symbol") in ["*", "ALL"]), None)
            
            if symbol_impact or global_impact:
                related_news.append({
                    **news,
                    "symbol_impact": symbol_impact or global_impact
                })
        
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
        print(f"Error fetching candle news: {e}")
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
            .eq("symbol", symbol)\
            .eq("timeframe", timeframe)\
            .gte("timestamp", from_time.isoformat())\
            .order("timestamp", desc=True)\
            .execute()
        
        big_moves = []
        for candle in result.data:
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
                
                # Filter relevant news
                related_news = [
                    n for n in news_result.data
                    if any(i.get("symbol") == symbol for i in n.get("impacts", []))
                ]
                
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
        print(f"Error fetching big moves: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/explain-move")
async def explain_price_move(
    symbol: str,
    timestamp: int,
    ai_explain: bool = True
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
        candle_time = datetime.fromtimestamp(timestamp)
        
        # Get candle
        candle_result = supabase.table("candle_cache")\
            .select("*")\
            .eq("symbol", symbol)\
            .gte("timestamp", candle_time.isoformat())\
            .lte("timestamp", (candle_time + timedelta(minutes=1)).isoformat())\
            .limit(1)\
            .execute()
        
        if not candle_result.data:
            return {
                "success": False,
                "error": "Candle not found"
            }
        
        candle = candle_result.data[0]
        
        # Get related news
        news_result = supabase.table("enriched_news")\
            .select("*")\
            .gte("timestamp", (candle_time - timedelta(minutes=30)).isoformat())\
            .lte("timestamp", (candle_time + timedelta(minutes=30)).isoformat())\
            .order("urgency")\
            .execute()
        
        # Filter relevant news
        relevant_news = [
            n for n in news_result.data
            if any(i.get("symbol") == symbol for i in n.get("impacts", []))
        ]
        
        # Calculate price change
        change_percent = ((candle["close"] - candle["open"]) / candle["open"]) * 100
        
        # Generate AI explanation
        explanation = ""
        if ai_explain and relevant_news:
            top_news = relevant_news[0]
            impact = next((i for i in top_news.get("impacts", []) if i.get("symbol") == symbol), None)
            
            if change_percent > 0:
                explanation = f"The {change_percent:.2f}% surge in {symbol} was primarily driven by: {top_news.get('headline')}. "
                if impact:
                    explanation += f"AI analysis indicates {impact.get('reasoning', 'positive sentiment')}. "
            else:
                explanation = f"The {abs(change_percent):.2f}% decline in {symbol} was influenced by: {top_news.get('headline')}. "
                if impact:
                    explanation += f"AI analysis suggests {impact.get('reasoning', 'negative sentiment')}. "
            
            explanation += f"Market sentiment was {top_news.get('sentiment', 'neutral')} with {top_news.get('volatility_expectation', 'medium')} volatility expected."
        
        return {
            "success": True,
            "data": {
                "symbol": symbol,
                "timestamp": timestamp,
                "candle": candle,
                "change_percent": round(change_percent, 2),
                "direction": "up" if change_percent > 0 else "down",
                "related_news": relevant_news,
                "ai_explanation": explanation if ai_explain else None
            }
        }
        
    except Exception as e:
        print(f"Error explaining move: {e}")
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
        print(f"Error fetching economic events: {e}")
        raise HTTPException(status_code=500, detail=str(e))
