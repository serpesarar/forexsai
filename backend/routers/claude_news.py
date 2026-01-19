"""
Claude News Analysis Router - AI-powered news sentiment analysis

Endpoints:
- POST /api/claude-news/analyze - Analyze cached news with Claude
- GET /api/claude-news/cached - Get cached news without analysis
- POST /api/claude-news/refresh - Fetch fresh news and cache it
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from datetime import datetime

from services.claude_news_analyzer import (
    analyze_news_with_claude,
    analyze_all_symbols_with_claude,
    get_cached_news,
    save_news_to_cache,
    ClaudeAnalysisResult,
)

router = APIRouter(prefix="/api/claude-news", tags=["claude-news"])


# =============================================================================
# Response Models
# =============================================================================

class NewsAnalysisItem(BaseModel):
    headline: str
    sentiment: float
    confidence: int
    category: str
    time_sensitivity: str
    key_entities: List[str]
    rationale: str
    override_signal: Optional[str] = None


class ClaudeAnalysisResponse(BaseModel):
    symbol: str
    timestamp: str
    news_count: int
    analyzed_count: int
    overall_sentiment: float
    overall_confidence: float
    direction_bias: str
    analyses: List[NewsAnalysisItem]
    bullish_count: int
    bearish_count: int
    neutral_count: int
    has_override: bool
    override_signal: Optional[str] = None
    override_reason: Optional[str] = None
    categories: Dict[str, int]
    tokens_used: int
    estimated_cost_usd: float
    market_commentary: str
    key_risks: List[str]
    key_opportunities: List[str]


class MultiSymbolResponse(BaseModel):
    XAUUSD: Optional[ClaudeAnalysisResponse] = None
    NDX_INDX: Optional[ClaudeAnalysisResponse] = None
    total_cost_usd: float
    timestamp: str


class CachedNewsItem(BaseModel):
    headline: str
    source: str
    published_at: Optional[str] = None
    fetched_at: str
    keyword_sentiment: float
    keyword_confidence: float
    claude_analyzed: bool
    claude_sentiment: Optional[float] = None


class CachedNewsResponse(BaseModel):
    symbol: str
    news_count: int
    news: List[CachedNewsItem]


class RefreshRequest(BaseModel):
    symbol: str = "XAUUSD"
    limit: int = 30


class RefreshResponse(BaseModel):
    symbol: str
    fetched_count: int
    saved_count: int
    message: str


# =============================================================================
# Endpoints
# =============================================================================

@router.post("/analyze/{symbol}", response_model=ClaudeAnalysisResponse)
async def analyze_symbol_news(
    symbol: str,
    limit: int = Query(default=15, ge=1, le=30),
    hours_back: int = Query(default=24, ge=1, le=168)
) -> ClaudeAnalysisResponse:
    """
    Analyze cached news for a specific symbol using Claude AI.
    
    This endpoint calls Claude API and incurs costs (~$0.01-0.05 per call).
    
    Parameters:
    - symbol: Trading symbol (XAUUSD, NDX.INDX, NASDAQ)
    - limit: Max number of news items to analyze (1-30)
    - hours_back: How far back to look for news (1-168 hours)
    """
    # Normalize symbol
    if symbol.upper() in ["NASDAQ", "NDX"]:
        symbol = "NDX.INDX"
    else:
        symbol = symbol.upper()
    
    if symbol not in ["XAUUSD", "NDX.INDX"]:
        raise HTTPException(status_code=400, detail=f"Unsupported symbol: {symbol}")
    
    result = await analyze_news_with_claude(
        symbol=symbol,
        limit=limit,
        hours_back=hours_back
    )
    
    # Convert to response model
    return ClaudeAnalysisResponse(
        symbol=result.symbol,
        timestamp=result.timestamp,
        news_count=result.news_count,
        analyzed_count=result.analyzed_count,
        overall_sentiment=result.overall_sentiment,
        overall_confidence=result.overall_confidence,
        direction_bias=result.direction_bias,
        analyses=[
            NewsAnalysisItem(
                headline=a.headline,
                sentiment=a.sentiment,
                confidence=a.confidence,
                category=a.category,
                time_sensitivity=a.time_sensitivity,
                key_entities=a.key_entities,
                rationale=a.rationale,
                override_signal=a.override_signal,
            )
            for a in result.analyses
        ],
        bullish_count=result.bullish_count,
        bearish_count=result.bearish_count,
        neutral_count=result.neutral_count,
        has_override=result.has_override,
        override_signal=result.override_signal,
        override_reason=result.override_reason,
        categories=result.categories,
        tokens_used=result.tokens_used,
        estimated_cost_usd=result.estimated_cost_usd,
        market_commentary=result.market_commentary,
        key_risks=result.key_risks,
        key_opportunities=result.key_opportunities,
    )


@router.post("/analyze-all", response_model=MultiSymbolResponse)
async def analyze_all_news() -> MultiSymbolResponse:
    """
    Analyze news for both XAUUSD and NASDAQ using Claude AI.
    
    This endpoint calls Claude API twice and incurs costs (~$0.02-0.10 per call).
    """
    results = await analyze_all_symbols_with_claude()
    
    total_cost = 0
    
    def convert_result(r: ClaudeAnalysisResult) -> ClaudeAnalysisResponse:
        return ClaudeAnalysisResponse(
            symbol=r.symbol,
            timestamp=r.timestamp,
            news_count=r.news_count,
            analyzed_count=r.analyzed_count,
            overall_sentiment=r.overall_sentiment,
            overall_confidence=r.overall_confidence,
            direction_bias=r.direction_bias,
            analyses=[
                NewsAnalysisItem(
                    headline=a.headline,
                    sentiment=a.sentiment,
                    confidence=a.confidence,
                    category=a.category,
                    time_sensitivity=a.time_sensitivity,
                    key_entities=a.key_entities,
                    rationale=a.rationale,
                    override_signal=a.override_signal,
                )
                for a in r.analyses
            ],
            bullish_count=r.bullish_count,
            bearish_count=r.bearish_count,
            neutral_count=r.neutral_count,
            has_override=r.has_override,
            override_signal=r.override_signal,
            override_reason=r.override_reason,
            categories=r.categories,
            tokens_used=r.tokens_used,
            estimated_cost_usd=r.estimated_cost_usd,
            market_commentary=r.market_commentary,
            key_risks=r.key_risks,
            key_opportunities=r.key_opportunities,
        )
    
    xauusd_result = None
    ndx_result = None
    
    if "XAUUSD" in results:
        xauusd_result = convert_result(results["XAUUSD"])
        total_cost += results["XAUUSD"].estimated_cost_usd
    
    if "NDX.INDX" in results:
        ndx_result = convert_result(results["NDX.INDX"])
        total_cost += results["NDX.INDX"].estimated_cost_usd
    
    return MultiSymbolResponse(
        XAUUSD=xauusd_result,
        NDX_INDX=ndx_result,
        total_cost_usd=round(total_cost, 4),
        timestamp=datetime.utcnow().isoformat() + "Z",
    )


@router.get("/cached/{symbol}", response_model=CachedNewsResponse)
async def get_cached_symbol_news(
    symbol: str,
    limit: int = Query(default=20, ge=1, le=100),
    hours_back: int = Query(default=24, ge=1, le=168)
) -> CachedNewsResponse:
    """
    Get cached news for a symbol without calling Claude API.
    
    This is free and fast - use it to preview news before analysis.
    """
    # Normalize symbol
    if symbol.upper() in ["NASDAQ", "NDX"]:
        symbol = "NDX.INDX"
    else:
        symbol = symbol.upper()
    
    cached = await get_cached_news(
        symbol=symbol,
        limit=limit,
        hours_back=hours_back
    )
    
    return CachedNewsResponse(
        symbol=symbol,
        news_count=len(cached),
        news=[
            CachedNewsItem(
                headline=item.get("headline", ""),
                source=item.get("source", ""),
                published_at=item.get("published_at"),
                fetched_at=item.get("fetched_at", ""),
                keyword_sentiment=item.get("keyword_sentiment", 0),
                keyword_confidence=item.get("keyword_confidence", 0),
                claude_analyzed=item.get("claude_analyzed", False),
                claude_sentiment=item.get("claude_sentiment"),
            )
            for item in cached
        ]
    )


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_news_cache(request: RefreshRequest) -> RefreshResponse:
    """
    Fetch fresh news and save to cache.
    
    This does NOT call Claude API - it only fetches and caches news.
    Use /analyze endpoint after this to analyze with Claude.
    """
    from services.gold_news_analyzer_v2 import fetch_gold_news_v2
    from services.news_fetcher import fetch_market_news
    
    symbol = request.symbol.upper()
    if symbol in ["NASDAQ", "NDX"]:
        symbol = "NDX.INDX"
    
    # Fetch news based on symbol
    if symbol == "XAUUSD":
        news = await fetch_gold_news_v2(limit=request.limit)
    else:
        news = await fetch_market_news(limit=request.limit)
    
    if not news:
        return RefreshResponse(
            symbol=symbol,
            fetched_count=0,
            saved_count=0,
            message="No news fetched from API"
        )
    
    # Save to cache
    saved = await save_news_to_cache(news, symbol)
    
    return RefreshResponse(
        symbol=symbol,
        fetched_count=len(news),
        saved_count=saved,
        message=f"Successfully cached {saved} news items for {symbol}"
    )
