"""
Claude News Analyzer - AI-powered news sentiment analysis for trading

Uses Claude API to analyze cached news headlines with:
- Context-aware understanding
- Nuanced sentiment scoring
- Category classification
- Time sensitivity detection
- Override signals for extreme events

Cost-optimized: Only called on user request, uses cached news from Supabase
"""
from __future__ import annotations

import logging
import json
import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
import httpx

from config import settings

logger = logging.getLogger(__name__)


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class ClaudeNewsAnalysis:
    """Single news item analysis result from Claude"""
    headline: str
    sentiment: float  # -1.0 to +1.0
    confidence: int  # 0-100
    category: str  # geopolitical, monetary, economic, technical, commodity_specific
    time_sensitivity: str  # immediate, short_term, medium_term, long_term
    key_entities: List[str]
    rationale: str
    override_signal: Optional[str] = None  # FORCE_BUY, FORCE_SELL, or None
    source: str = ""
    published_at: str = ""
    error: Optional[str] = None


@dataclass  
class ClaudeAnalysisResult:
    """Complete analysis result for a symbol"""
    symbol: str
    timestamp: str
    news_count: int
    analyzed_count: int
    
    # Aggregated sentiment
    overall_sentiment: float
    overall_confidence: float
    direction_bias: str  # BUY, SELL, NEUTRAL
    
    # Individual analyses
    analyses: List[ClaudeNewsAnalysis]
    
    # Summary
    bullish_count: int = 0
    bearish_count: int = 0
    neutral_count: int = 0
    
    # Override detection
    has_override: bool = False
    override_signal: Optional[str] = None
    override_reason: Optional[str] = None
    
    # Categories breakdown
    categories: Dict[str, int] = field(default_factory=dict)
    
    # Cost tracking
    tokens_used: int = 0
    estimated_cost_usd: float = 0.0
    
    # AI commentary
    market_commentary: str = ""
    key_risks: List[str] = field(default_factory=list)
    key_opportunities: List[str] = field(default_factory=list)


# =============================================================================
# CLAUDE PROMPT - Hybrid V2/V3
# =============================================================================

CLAUDE_NEWS_PROMPT = """You are XAUUSD-GPT, a specialized sentiment analyzer for {symbol} trading.
Your task: Analyze news headlines and return STRICTLY VALID JSON.

### CURRENT MARKET CONTEXT:
- Symbol: {symbol}
- Current Price: {current_price}
- Analysis Time: {timestamp}

### NEWS HEADLINES TO ANALYZE:
{news_list}

### ANALYSIS RULES (Priority Order):

1. **SENTIMENT DETERMINATION** (-1.0 to +1.0):
   For XAUUSD (Gold):
   - **+0.8 to +1.0**: War outbreak, Fed cuts rates aggressively, dollar collapse
   - **+0.4 to +0.7**: Inflation concerns, geopolitical tensions, dovish Fed hints
   - **-0.1 to +0.3**: Mixed signals, minor events, consolidation news
   - **-0.4 to -0.1**: Strong jobs data, risk-on sentiment
   - **-1.0 to -0.5**: Fed hikes aggressively, dollar surges, disinflation confirmed
   
   For NASDAQ/NDX:
   - **+0.8 to +1.0**: Fed cuts, strong tech earnings, AI breakthroughs
   - **+0.4 to +0.7**: Dovish signals, economic recovery, tech sector strength
   - **-0.1 to +0.3**: Mixed signals, consolidation
   - **-0.4 to -0.1**: Inflation worries, regulation threats
   - **-1.0 to -0.5**: Fed hikes, recession fears, tech selloff

2. **CONFIDENCE SCORING** (0-100):
   - **90-100**: Confirmed facts, official statements, concrete numbers
   - **70-89**: Strong signals from reliable sources
   - **40-69**: Moderate speculation, "might", "could", "expected"
   - **10-39**: Weak signals, rumors, unconfirmed
   - **0-9**: Ambiguous, no clear impact

3. **SOURCE RELIABILITY MODIFIERS**:
   - Reuters, Bloomberg, WSJ: +15 confidence
   - CNBC, FT: +10 confidence
   - Twitter, blogs: -20 confidence
   - Unknown source: -10 confidence

4. **CRITICAL FILTERS**:
   - Contains "rumor", "unconfirmed": -30 confidence
   - Contains "may", "might", "could": -20 confidence
   - Contains specific numbers/dates: +10 confidence
   - Multiple confirming sources: +15 confidence

5. **CATEGORY CLASSIFICATION**:
   - `geopolitical`: War, conflict, sanctions, trade wars
   - `monetary`: Fed, ECB, rates, QE, tapering
   - `economic`: NFP, CPI, GDP, employment, retail
   - `technical`: Price levels, breakouts, support/resistance
   - `commodity_specific`: Gold supply, mining, central bank reserves

6. **TIME SENSITIVITY**:
   - `immediate`: 0-2 hours (rate decisions, war, major events)
   - `short_term`: 2-24 hours (economic data, speeches)
   - `medium_term`: 1-7 days (policy shifts, trends)
   - `long_term`: 7+ days (structural changes)

7. **OVERRIDE SIGNALS** (Use sparingly!):
   - `FORCE_BUY`: Only if sentiment > 0.7 AND confidence > 85 AND immediate impact
   - `FORCE_SELL`: Only if sentiment < -0.7 AND confidence > 85 AND immediate impact
   - `null`: Default for most cases

### OUTPUT SCHEMA (STRICT JSON):
{{
  "analyses": [
    {{
      "headline": "string (original headline)",
      "sentiment": float (-1.00 to +1.00),
      "confidence": int (0-100),
      "category": "string",
      "time_sensitivity": "string",
      "key_entities": ["entity1", "entity2"],
      "rationale": "string (max 100 chars)",
      "override_signal": "FORCE_BUY" | "FORCE_SELL" | null
    }}
  ],
  "market_commentary": "string (2-3 sentence market overview based on news)",
  "key_risks": ["risk1", "risk2"],
  "key_opportunities": ["opportunity1", "opportunity2"],
  "overall_bias": "BULLISH" | "BEARISH" | "NEUTRAL"
}}

### IMPORTANT RULES:
- Return ONLY valid JSON, no markdown, no explanations
- Analyze ALL provided headlines
- Be precise: low confidence is better than wrong signal
- Consider {symbol}-specific factors
- If headline is ambiguous: sentiment=0, confidence=30

Return the JSON now:"""


# =============================================================================
# SUPABASE INTEGRATION
# =============================================================================

async def get_supabase_client():
    """Get Supabase client"""
    if not settings.supabase_url or not settings.supabase_key:
        return None
    
    try:
        from supabase import create_client
        return create_client(settings.supabase_url, settings.supabase_key)
    except Exception as e:
        logger.warning(f"Could not create Supabase client: {e}")
        return None


def generate_headline_hash(headline: str) -> str:
    """Generate unique hash for headline to avoid duplicates"""
    return hashlib.sha256(headline.encode()).hexdigest()[:32]


async def save_news_to_cache(
    news_items: List[Dict],
    symbol: str,
    keyword_analysis: Optional[Dict] = None
) -> int:
    """
    Save news items to Supabase cache.
    Returns number of items saved (excluding duplicates).
    """
    client = await get_supabase_client()
    if not client:
        logger.warning("Supabase not configured, skipping news cache")
        return 0
    
    saved_count = 0
    
    for item in news_items:
        headline = item.get("title") or item.get("headline") or ""
        if not headline:
            continue
        
        headline_hash = generate_headline_hash(headline)
        
        # Prepare record
        record = {
            "headline": headline[:500],  # Limit length
            "headline_hash": headline_hash,
            "source": item.get("source", ""),
            "source_url": item.get("link") or item.get("url") or "",
            "published_at": item.get("date") or item.get("published_at"),
            "symbol": symbol,
            "keyword_sentiment": keyword_analysis.get("sentiment", 0) if keyword_analysis else 0,
            "keyword_confidence": keyword_analysis.get("confidence", 0) if keyword_analysis else 0,
            "keyword_impact_level": keyword_analysis.get("impact_level", "low") if keyword_analysis else "low",
            "source_weight": keyword_analysis.get("source_weight", 1.0) if keyword_analysis else 1.0,
        }
        
        try:
            # Upsert to avoid duplicates
            client.table("news_cache").upsert(
                record,
                on_conflict="headline_hash"
            ).execute()
            saved_count += 1
        except Exception as e:
            logger.debug(f"Could not save news item: {e}")
    
    logger.info(f"Saved {saved_count} news items to cache for {symbol}")
    return saved_count


async def get_cached_news(
    symbol: str,
    limit: int = 20,
    hours_back: int = 24,
    only_unanalyzed: bool = False
) -> List[Dict]:
    """
    Get cached news from Supabase for Claude analysis.
    """
    client = await get_supabase_client()
    if not client:
        logger.warning("Supabase not configured")
        return []
    
    try:
        cutoff = datetime.utcnow() - timedelta(hours=hours_back)
        
        query = client.table("news_cache")\
            .select("*")\
            .eq("symbol", symbol)\
            .gte("fetched_at", cutoff.isoformat())\
            .order("fetched_at", desc=True)\
            .limit(limit)
        
        if only_unanalyzed:
            query = query.eq("claude_analyzed", False)
        
        result = query.execute()
        return result.data or []
        
    except Exception as e:
        logger.error(f"Error fetching cached news: {e}")
        return []


async def update_claude_analysis(
    headline_hash: str,
    analysis: ClaudeNewsAnalysis
) -> bool:
    """Update news cache with Claude analysis result"""
    client = await get_supabase_client()
    if not client:
        return False
    
    try:
        client.table("news_cache").update({
            "claude_analyzed": True,
            "claude_analyzed_at": datetime.utcnow().isoformat(),
            "claude_sentiment": analysis.sentiment,
            "claude_confidence": analysis.confidence,
            "claude_category": analysis.category,
            "claude_time_sensitivity": analysis.time_sensitivity,
            "claude_key_entities": analysis.key_entities,
            "claude_rationale": analysis.rationale,
            "claude_override_signal": analysis.override_signal,
        }).eq("headline_hash", headline_hash).execute()
        
        return True
    except Exception as e:
        logger.error(f"Error updating Claude analysis: {e}")
        return False


# =============================================================================
# CLAUDE API INTEGRATION
# =============================================================================

async def call_claude_api(
    prompt: str,
    max_tokens: int = 2000,
    temperature: float = 0.0
) -> Optional[Dict]:
    """
    Call Claude API with the given prompt.
    Returns parsed JSON response or None on error.
    """
    if not settings.anthropic_api_key:
        logger.error("ANTHROPIC_API_KEY not configured")
        return None
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": settings.anthropic_api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-3-5-sonnet-20241022",
                    "max_tokens": max_tokens,
                    "temperature": temperature,  # Deterministic
                    "messages": [{"role": "user", "content": prompt}],
                }
            )
            response.raise_for_status()
            data = response.json()
            
            # Extract text content
            text = ""
            for block in data.get("content", []):
                if block.get("type") == "text":
                    text = block.get("text", "")
                    break
            
            # Parse JSON
            # Clean up any markdown formatting
            text = text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
            
            result = json.loads(text)
            
            # Add token usage for cost tracking
            usage = data.get("usage", {})
            result["_tokens"] = {
                "input": usage.get("input_tokens", 0),
                "output": usage.get("output_tokens", 0),
            }
            
            return result
            
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Claude response as JSON: {e}")
        return None
    except Exception as e:
        logger.error(f"Claude API error: {e}")
        return None


# =============================================================================
# MAIN ANALYSIS FUNCTION
# =============================================================================

async def analyze_news_with_claude(
    symbol: str,
    limit: int = 15,
    hours_back: int = 24,
    current_price: Optional[float] = None
) -> ClaudeAnalysisResult:
    """
    Analyze cached news for a symbol using Claude API.
    
    This is the main function called when user clicks the analysis button.
    It fetches cached news from Supabase and sends them to Claude for analysis.
    """
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    # Fetch cached news
    cached_news = await get_cached_news(
        symbol=symbol,
        limit=limit,
        hours_back=hours_back,
        only_unanalyzed=False  # Analyze all recent news
    )
    
    if not cached_news:
        return ClaudeAnalysisResult(
            symbol=symbol,
            timestamp=timestamp,
            news_count=0,
            analyzed_count=0,
            overall_sentiment=0,
            overall_confidence=0,
            direction_bias="NEUTRAL",
            analyses=[],
            market_commentary="No recent news available for analysis.",
            key_risks=["Insufficient data for analysis"],
            key_opportunities=[],
        )
    
    # Format news for prompt
    news_list = ""
    for i, item in enumerate(cached_news, 1):
        source = item.get("source", "Unknown")
        headline = item.get("headline", "")
        published = item.get("published_at", "")
        news_list += f"{i}. [{source}] {headline} (Published: {published})\n"
    
    # Get current price if not provided
    if current_price is None:
        try:
            from services.data_fetcher import fetch_latest_price
            current_price = await fetch_latest_price(symbol) or 0
        except:
            current_price = 0
    
    # Build prompt
    prompt = CLAUDE_NEWS_PROMPT.format(
        symbol=symbol,
        current_price=f"{current_price:.2f}" if current_price else "N/A",
        timestamp=timestamp,
        news_list=news_list
    )
    
    # Call Claude
    logger.info(f"Calling Claude API for {symbol} with {len(cached_news)} news items")
    claude_response = await call_claude_api(prompt)
    
    if not claude_response:
        return ClaudeAnalysisResult(
            symbol=symbol,
            timestamp=timestamp,
            news_count=len(cached_news),
            analyzed_count=0,
            overall_sentiment=0,
            overall_confidence=0,
            direction_bias="NEUTRAL",
            analyses=[],
            market_commentary="Claude API analysis failed. Please try again.",
            key_risks=["API error"],
            key_opportunities=[],
        )
    
    # Parse response
    analyses: List[ClaudeNewsAnalysis] = []
    categories: Dict[str, int] = {}
    total_sentiment = 0
    total_confidence = 0
    bullish = 0
    bearish = 0
    neutral = 0
    override_detected = None
    override_reason = None
    
    for item in claude_response.get("analyses", []):
        analysis = ClaudeNewsAnalysis(
            headline=item.get("headline", ""),
            sentiment=float(item.get("sentiment", 0)),
            confidence=int(item.get("confidence", 0)),
            category=item.get("category", "unknown"),
            time_sensitivity=item.get("time_sensitivity", "short_term"),
            key_entities=item.get("key_entities", []),
            rationale=item.get("rationale", ""),
            override_signal=item.get("override_signal"),
        )
        analyses.append(analysis)
        
        # Aggregate stats
        total_sentiment += analysis.sentiment * (analysis.confidence / 100)
        total_confidence += analysis.confidence
        
        # Count sentiment
        if analysis.sentiment > 0.1:
            bullish += 1
        elif analysis.sentiment < -0.1:
            bearish += 1
        else:
            neutral += 1
        
        # Track categories
        cat = analysis.category
        categories[cat] = categories.get(cat, 0) + 1
        
        # Check for override
        if analysis.override_signal and not override_detected:
            override_detected = analysis.override_signal
            override_reason = analysis.headline[:100]
        
        # Update cache with analysis
        if item.get("headline"):
            headline_hash = generate_headline_hash(item["headline"])
            await update_claude_analysis(headline_hash, analysis)
    
    # Calculate averages
    n = len(analyses) or 1
    avg_sentiment = total_sentiment / n
    avg_confidence = total_confidence / n
    
    # Determine direction
    if avg_sentiment > 0.15:
        direction = "BUY"
    elif avg_sentiment < -0.15:
        direction = "SELL"
    else:
        direction = "NEUTRAL"
    
    # Calculate cost
    tokens = claude_response.get("_tokens", {})
    input_tokens = tokens.get("input", 0)
    output_tokens = tokens.get("output", 0)
    # Claude 3.5 Sonnet pricing: $3/1M input, $15/1M output
    cost = (input_tokens * 3 / 1_000_000) + (output_tokens * 15 / 1_000_000)
    
    return ClaudeAnalysisResult(
        symbol=symbol,
        timestamp=timestamp,
        news_count=len(cached_news),
        analyzed_count=len(analyses),
        overall_sentiment=round(avg_sentiment, 3),
        overall_confidence=round(avg_confidence, 1),
        direction_bias=direction,
        analyses=analyses,
        bullish_count=bullish,
        bearish_count=bearish,
        neutral_count=neutral,
        has_override=override_detected is not None,
        override_signal=override_detected,
        override_reason=override_reason,
        categories=categories,
        tokens_used=input_tokens + output_tokens,
        estimated_cost_usd=round(cost, 4),
        market_commentary=claude_response.get("market_commentary", ""),
        key_risks=claude_response.get("key_risks", []),
        key_opportunities=claude_response.get("key_opportunities", []),
    )


# =============================================================================
# COMBINED ANALYSIS (Both Symbols)
# =============================================================================

async def analyze_all_symbols_with_claude() -> Dict[str, ClaudeAnalysisResult]:
    """
    Analyze news for both XAUUSD and NASDAQ.
    Returns dict with results for each symbol.
    """
    results = {}
    
    for symbol in ["XAUUSD", "NDX.INDX"]:
        try:
            result = await analyze_news_with_claude(symbol)
            results[symbol] = result
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            results[symbol] = ClaudeAnalysisResult(
                symbol=symbol,
                timestamp=datetime.utcnow().isoformat() + "Z",
                news_count=0,
                analyzed_count=0,
                overall_sentiment=0,
                overall_confidence=0,
                direction_bias="NEUTRAL",
                analyses=[],
                market_commentary=f"Error analyzing {symbol}: {str(e)}",
            )
    
    return results
