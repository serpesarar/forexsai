"""
News Correlation Router
API endpoints for news-chart correlation system
"""

import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import asyncio

from services.news_analyzer import (
    get_analyzer, 
    NewsAnalysisResult, 
    SymbolImpact,
    IMPACT_RULES
)
from database.supabase_client import get_supabase_client

router = APIRouter(prefix="/api/news-correlation", tags=["news-correlation"])

# Request/Response Models
class NewsAnalyzeRequest(BaseModel):
    headline: str
    content: Optional[str] = ""
    source: Optional[str] = ""
    timestamp: Optional[str] = None

class NewsAnalyzeResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class CorrelatedNewsRequest(BaseModel):
    symbol: str
    timeframe: str = "1h"
    start_time: Optional[int] = None
    end_time: Optional[int] = None
    impact_filter: Optional[str] = "all"

class EnrichedNewsResponse(BaseModel):
    id: str
    timestamp: str
    source: str
    headline: str
    content: Optional[str]
    impacts: List[Dict[str, Any]]
    sentiment: str
    volatility_expectation: str
    key_levels: Optional[Dict[str, List[float]]]
    event_duration: str
    ai_confidence: float


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.subscribed_symbols: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        # Remove from symbol subscriptions
        for symbol, connections in self.subscribed_symbols.items():
            if websocket in connections:
                connections.remove(websocket)
    
    async def subscribe_to_symbol(self, websocket: WebSocket, symbol: str):
        if symbol not in self.subscribed_symbols:
            self.subscribed_symbols[symbol] = []
        if websocket not in self.subscribed_symbols[symbol]:
            self.subscribed_symbols[symbol].append(websocket)
    
    async def broadcast_to_symbol(self, symbol: str, message: Dict[str, Any]):
        if symbol in self.subscribed_symbols:
            disconnected = []
            for connection in self.subscribed_symbols[symbol]:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.append(connection)
            
            # Clean up disconnected clients
            for conn in disconnected:
                self.subscribed_symbols[symbol].remove(conn)
    
    async def broadcast(self, message: Dict[str, Any]):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        
        for conn in disconnected:
            if conn in self.active_connections:
                self.active_connections.remove(conn)


manager = ConnectionManager()


@router.post("/analyze", response_model=NewsAnalyzeResponse)
async def analyze_news_endpoint(request: NewsAnalyzeRequest):
    """
    Analyze a single news item for market impact
    """
    try:
        analyzer = get_analyzer()
        result = await analyzer.analyze_news(
            headline=request.headline,
            content=request.content or "",
            source=request.source or ""
        )
        
        # Convert to dict
        response_data = {
            "impacts": [
                {
                    "symbol": i.symbol,
                    "direction": i.direction,
                    "score": i.score,
                    "confidence": i.confidence,
                    "reasoning": i.reasoning,
                    "emoji": i.emoji
                }
                for i in result.impacts
            ],
            "sentiment": result.sentiment,
            "volatility_expectation": result.volatility_expectation,
            "key_levels": result.key_levels,
            "event_duration": result.event_duration,
            "confidence": result.confidence
        }
        
        return NewsAnalyzeResponse(success=True, data=response_data)
    
    except Exception as e:
        return NewsAnalyzeResponse(success=False, error=str(e))


@router.get("/correlated/{symbol}", response_model=List[EnrichedNewsResponse])
async def get_correlated_news(
    symbol: str,
    timeframe: str = Query("1h", description="Chart timeframe"),
    start_time: Optional[int] = Query(None, description="Start timestamp (unix)"),
    end_time: Optional[int] = Query(None, description="End timestamp (unix)"),
    impact_filter: str = Query("all", description="Filter by impact: all, high, medium, low"),
    limit: int = Query(50, description="Max results", ge=1, le=200)
):
    """
    Get news correlated to a specific symbol within time range
    """
    try:
        supabase = get_supabase_client()
        
        # Default time range: last 24 hours
        if not end_time:
            end_time = int(datetime.utcnow().timestamp())
        if not start_time:
            # Default based on timeframe
            tf_hours = {"5m": 6, "15m": 12, "30m": 24, "1h": 48, "4h": 168, "1d": 720}
            hours = tf_hours.get(timeframe, 24)
            start_time = end_time - (hours * 3600)
        
        # Query Supabase for enriched news
        query = (
            supabase.table("enriched_news")
            .select("*")
            .gte("timestamp", datetime.fromtimestamp(start_time).isoformat())
            .lte("timestamp", datetime.fromtimestamp(end_time).isoformat())
            .order("timestamp", desc=True)
            .limit(limit)
        )
        
        response = query.execute()
        
        if not response.data:
            return []
        
        # Filter by symbol impact
        filtered_news = []
        for news in response.data:
            impacts = news.get("impacts", [])
            
            # Check if this symbol is affected
            symbol_impact = None
            for imp in impacts:
                if imp.get("symbol") == symbol or imp.get("symbol") == "*":
                    symbol_impact = imp
                    break
            
            # Also include news that affects correlated symbols
            if not symbol_impact and impacts:
                # Include as ghost marker (30% opacity on chart)
                symbol_impact = impacts[0]
                symbol_impact["is_ghost"] = True
            
            if symbol_impact:
                # Apply impact filter
                if impact_filter != "all":
                    score = symbol_impact.get("score", 5)
                    if impact_filter == "high" and score < 7:
                        continue
                    if impact_filter == "medium" and (score < 4 or score >= 7):
                        continue
                    if impact_filter == "low" and score >= 4:
                        continue
                
                enriched = EnrichedNewsResponse(
                    id=news.get("id"),
                    timestamp=news.get("timestamp"),
                    source=news.get("source", "Unknown"),
                    headline=news.get("headline"),
                    content=news.get("content"),
                    impacts=impacts,
                    sentiment=news.get("sentiment", "neutral"),
                    volatility_expectation=news.get("volatility_expectation", "medium"),
                    key_levels=news.get("key_levels"),
                    event_duration=news.get("event_duration", "short_term"),
                    ai_confidence=news.get("ai_confidence", 70.0)
                )
                filtered_news.append(enriched)
        
        return filtered_news
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recent")
async def get_recent_news(
    limit: int = Query(20, ge=1, le=100),
    symbols: Optional[str] = Query(None, description="Comma-separated symbols")
):
    """
    Get recent analyzed news
    """
    try:
        supabase = get_supabase_client()
        
        query = (
            supabase.table("enriched_news")
            .select("*")
            .order("timestamp", desc=True)
            .limit(limit)
        )
        
        if symbols:
            symbol_list = symbols.split(",")
            # Filter by JSONB contains - requires proper Supabase query
            # This is a simplified version
        
        response = query.execute()
        return {"success": True, "data": response.data or []}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/store")
async def store_analyzed_news(news_data: Dict[str, Any]):
    """
    Store pre-analyzed news to database
    """
    try:
        supabase = get_supabase_client()
        
        # Ensure required fields
        if "id" not in news_data:
            news_data["id"] = f"news_{datetime.utcnow().timestamp()}"
        
        if "analysis_timestamp" not in news_data:
            news_data["analysis_timestamp"] = datetime.utcnow().isoformat()
        
        response = supabase.table("enriched_news").insert(news_data).execute()
        
        # Broadcast to WebSocket subscribers
        affected_symbols = [i.get("symbol") for i in news_data.get("impacts", [])]
        for symbol in set(affected_symbols):
            if symbol:
                await manager.broadcast_to_symbol(symbol, {
                    "type": "news",
                    "data": news_data,
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        return {"success": True, "id": news_data["id"]}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/impact-rules")
async def get_impact_rules():
    """
    Get all defined impact rules for reference
    """
    return {
        "success": True,
        "rules": {
            name: {
                "keywords": rule["keywords"],
                "sentiment": rule["sentiment"],
                "volatility": rule["volatility"]
            }
            for name, rule in IMPACT_RULES.items()
        }
    }


@router.get("/supported-symbols")
async def get_supported_symbols():
    """
    Get list of supported symbols and their characteristics
    """
    from services.news_analyzer import SUPPORTED_SYMBOLS
    return {
        "success": True,
        "symbols": SUPPORTED_SYMBOLS
    }


# WebSocket endpoint for real-time news
@router.websocket("/ws/news")
async def news_websocket(websocket: WebSocket):
    """
    WebSocket for real-time news updates
    Clients can subscribe to specific symbols
    """
    await manager.connect(websocket)
    
    try:
        while True:
            # Receive messages from client (subscription requests)
            data = await websocket.receive_json()
            
            message_type = data.get("type")
            
            if message_type == "subscribe":
                symbol = data.get("symbol")
                if symbol:
                    await manager.subscribe_to_symbol(websocket, symbol)
                    await websocket.send_json({
                        "type": "subscribed",
                        "symbol": symbol
                    })
            
            elif message_type == "unsubscribe":
                symbol = data.get("symbol")
                if symbol and symbol in manager.subscribed_symbols:
                    if websocket in manager.subscribed_symbols[symbol]:
                        manager.subscribed_symbols[symbol].remove(websocket)
            
            elif message_type == "ping":
                await websocket.send_json({"type": "pong"})
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)


@router.get("/stats")
async def get_news_stats(
    symbol: Optional[str] = Query(None),
    days: int = Query(7, ge=1, le=30)
):
    """
    Get news analysis statistics
    """
    try:
        supabase = get_supabase_client()
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Query for stats
        query = (
            supabase.table("enriched_news")
            .select("sentiment, impacts, ai_confidence")
            .gte("timestamp", start_date.isoformat())
        )
        
        response = query.execute()
        data = response.data or []
        
        # Calculate stats
        total = len(data)
        sentiment_counts = {"risk_on": 0, "risk_off": 0, "neutral": 0}
        volatility_counts = {"high": 0, "medium": 0, "low": 0}
        symbol_mentions = {}
        avg_confidence = 0
        
        for item in data:
            sentiment_counts[item.get("sentiment", "neutral")] += 1
            avg_confidence += item.get("ai_confidence", 70)
            
            for impact in item.get("impacts", []):
                sym = impact.get("symbol")
                if sym:
                    symbol_mentions[sym] = symbol_mentions.get(sym, 0) + 1
        
        avg_confidence = avg_confidence / total if total > 0 else 0
        
        return {
            "success": True,
            "stats": {
                "total_news": total,
                "sentiment_distribution": sentiment_counts,
                "average_confidence": round(avg_confidence, 2),
                "symbol_mentions": symbol_mentions,
                "period_days": days
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
