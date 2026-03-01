"""
News Analyzer Service
AI-powered news analysis for financial impact detection
Uses DeepSeek AI to analyze news and predict market impacts
"""

import json
import os
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import asyncio
import aiohttp
from functools import lru_cache
import redis.asyncio as redis

# Configuration
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Supported symbols with their characteristics
SUPPORTED_SYMBOLS = {
    "XAUUSD": {"name": "Gold", "type": "commodity", "safe_haven": True},
    "NASDAQ": {"name": "NASDAQ Composite", "type": "index", "risk_asset": True},
    "DAX": {"name": "DAX 40", "type": "index", "risk_asset": True},
    "USOIL": {"name": "WTI Crude Oil", "type": "commodity", "risk_asset": True},
    "VIX": {"name": "VIX Volatility Index", "type": "index", "fear_gauge": True},
    "DXY": {"name": "US Dollar Index", "type": "currency", "safe_haven": True},
    "EURUSD": {"name": "Euro/USD", "type": "forex", "risk_asset": False},
    "GBPUSD": {"name": "GBP/USD", "type": "forex", "risk_asset": False},
    "BTCUSD": {"name": "Bitcoin/USD", "type": "crypto", "risk_asset": True},
}

# Impact rules for common scenarios
IMPACT_RULES = {
    "trump_iran": {
        "keywords": ["trump", "iran", "nuclear", "deal", "military", "threat"],
        "impacts": [
            {"symbol": "XAUUSD", "direction": "bullish", "score": 8, "reasoning": "Safe haven demand"},
            {"symbol": "USOIL", "direction": "bullish", "score": 7, "reasoning": "Supply disruption risk"},
            {"symbol": "VIX", "direction": "bullish", "score": 6, "reasoning": "Geopolitical uncertainty"},
            {"symbol": "DXY", "direction": "bullish", "score": 5, "reasoning": "Safe haven flow"},
            {"symbol": "NASDAQ", "direction": "bearish", "score": 5, "reasoning": "Risk-off sentiment"},
        ],
        "sentiment": "risk_off",
        "volatility": "high",
    },
    "fed_rate": {
        "keywords": ["fed", "federal reserve", "rate", "interest", "hike", "cut", "powell"],
        "impacts": [
            {"symbol": "DXY", "direction": "bullish", "score": 8, "reasoning": "Rate hike bullish for USD"},
            {"symbol": "XAUUSD", "direction": "bearish", "score": 7, "reasoning": "Higher rates hurt gold"},
            {"symbol": "NASDAQ", "direction": "bearish", "score": 7, "reasoning": "Higher rates hurt tech"},
        ],
        "sentiment": "risk_off" if "hike" in "{text}" else "neutral",
        "volatility": "high",
    },
    "inflation_data": {
        "keywords": ["inflation", "cpi", "ppi", "price index"],
        "impacts": [
            {"symbol": "XAUUSD", "direction": "bullish", "score": 6, "reasoning": "Inflation hedge"},
            {"symbol": "DXY", "direction": "bullish", "score": 7, "reasoning": "Fed may hike rates"},
        ],
        "sentiment": "neutral",
        "volatility": "high",
    },
    "nfp_jobs": {
        "keywords": ["jobs", "employment", "nfp", "non-farm", "payrolls", "unemployment"],
        "impacts": [
            {"symbol": "DXY", "direction": "bullish", "score": 7, "reasoning": "Strong jobs = hawkish Fed"},
            {"symbol": "XAUUSD", "direction": "bearish", "score": 6, "reasoning": "Strong economy hurts gold"},
            {"symbol": "NASDAQ", "direction": "bullish", "score": 6, "reasoning": "Economic strength"},
        ],
        "sentiment": "risk_on",
        "volatility": "high",
    },
    "ecb_policy": {
        "keywords": ["ecb", "european central bank", "lagarde", "eurozone"],
        "impacts": [
            {"symbol": "EURUSD", "direction": "bullish", "score": 7, "reasoning": "ECB policy impact"},
            {"symbol": "DXY", "direction": "bearish", "score": 6, "reasoning": "Inverse correlation"},
        ],
        "sentiment": "neutral",
        "volatility": "medium",
    },
    "middle_east": {
        "keywords": ["israel", "gaza", "palestine", "middle east", "war", "conflict"],
        "impacts": [
            {"symbol": "XAUUSD", "direction": "bullish", "score": 8, "reasoning": "Geopolitical safe haven"},
            {"symbol": "USOIL", "direction": "bullish", "score": 8, "reasoning": "Middle East supply risk"},
            {"symbol": "VIX", "direction": "bullish", "score": 7, "reasoning": "Uncertainty spike"},
        ],
        "sentiment": "risk_off",
        "volatility": "high",
    },
    "crypto_regulation": {
        "keywords": ["bitcoin", "crypto", "regulation", "sec", "etf"],
        "impacts": [
            {"symbol": "BTCUSD", "direction": "bullish", "score": 8, "reasoning": "ETF approval/positive news"},
            {"symbol": "NASDAQ", "direction": "bullish", "score": 5, "reasoning": "Crypto correlation"},
        ],
        "sentiment": "risk_on",
        "volatility": "high",
    },
}


@dataclass
class SymbolImpact:
    symbol: str
    direction: str  # bullish, bearish, neutral
    score: int  # 1-10
    confidence: float  # 0-1
    reasoning: str
    emoji: str = ""


@dataclass
class NewsAnalysisResult:
    impacts: List[SymbolImpact]
    sentiment: str  # risk_on, risk_off, neutral
    volatility_expectation: str  # high, medium, low
    key_levels: Optional[Dict[str, List[float]]]
    event_duration: str  # immediate, short_term, long_term
    confidence: float  # 0-100
    source_rules: Optional[List[str]] = None


class NewsAnalyzer:
    """AI-powered news analyzer for financial markets"""
    
    def __init__(self):
        self.api_key = DEEPSEEK_API_KEY
        self.redis: Optional[redis.Redis] = None
        self._redis_available = False
        
    async def _get_redis(self) -> Optional[redis.Redis]:
        """Get or create Redis connection"""
        if not self._redis_available:
            return None
        if self.redis is None:
            try:
                self.redis = redis.from_url(REDIS_URL, decode_responses=True)
                await self.redis.ping()
                self._redis_available = True
            except Exception:
                self._redis_available = False
                return None
        return self.redis
    
    def _get_cache_key(self, headline: str, content: str = "") -> str:
        """Generate cache key for news analysis"""
        text = f"{headline}:{content}"
        return f"news_analysis:{hashlib.md5(text.encode()).hexdigest()}"
    
    def _check_rule_based_impact(self, headline: str, content: str = "") -> Optional[NewsAnalysisResult]:
        """Check if news matches known patterns for quick rule-based analysis"""
        text = f"{headline} {content}".lower()
        
        for rule_name, rule in IMPACT_RULES.items():
            if any(keyword in text for keyword in rule["keywords"]):
                impacts = []
                for imp in rule["impacts"]:
                    emoji = "📈" if imp["direction"] == "bullish" else "📉" if imp["direction"] == "bearish" else "➡️"
                    impacts.append(SymbolImpact(
                        symbol=imp["symbol"],
                        direction=imp["direction"],
                        score=imp["score"],
                        confidence=0.75,
                        reasoning=imp["reasoning"],
                        emoji=emoji
                    ))
                
                return NewsAnalysisResult(
                    impacts=impacts,
                    sentiment=rule["sentiment"],
                    volatility_expectation=rule["volatility"],
                    key_levels=None,
                    event_duration="short_term",
                    confidence=75.0,
                    source_rules=[rule_name]
                )
        
        return None
    
    async def _analyze_with_ai(
        self,
        headline: str,
        content: str = "",
        source: str = ""
    ) -> NewsAnalysisResult:
        """Analyze news using DeepSeek AI"""
        
        prompt = f"""Analyze this financial news and extract market impact information:

HEADLINE: {headline}
CONTENT: {content[:500] if content else "N/A"}
SOURCE: {source}
TIMESTAMP: {datetime.utcnow().isoformat()}

Provide analysis in strict JSON format:
{{
    "affected_instruments": [
        {{
            "symbol": "XAUUSD|NASDAQ|DAX|USOIL|VIX|DXY|EURUSD|GBPUSD|BTCUSD",
            "direction": "bullish|bearish|neutral",
            "impact_score": 1-10,
            "confidence": 0.0-1.0,
            "reasoning": "brief explanation"
        }}
    ],
    "market_sentiment": "risk_on|risk_off|neutral",
    "volatility_expectation": "high|medium|low",
    "key_levels": {{
        "support": [price1, price2],
        "resistance": [price3, price4]
    }},
    "event_duration": "immediate|short_term|long_term",
    "analysis_confidence": 0-100
}}

Rules:
- Trump/Iran tensions → XAUUSD↑ (safe haven), USOIL↑ (supply risk), VIX↑ (fear)
- Fed rate decisions → DXY moves, NASDAQ opposite direction
- Strong jobs data → DXY↑, XAUUSD↓
- Inflation surprise → XAUUSD↑, DXY↑ (hawkish expectation)
- ECB decisions → EURUSD affected, DXY inverse
- Middle East conflict → XAUUSD↑, USOIL↑, VIX↑
- Inverse correlations: XAUUSD vs DXY, NASDAQ vs VIX

Output JSON only, no markdown."""

        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": "You are a financial market analyst. Analyze news and predict market impacts accurately."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 800,
                    "response_format": {"type": "json_object"}
                }
                
                async with session.post(
                    DEEPSEEK_API_URL,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"DeepSeek API error: {response.status} - {error_text}")
                    
                    data = await response.json()
                    content = data["choices"][0]["message"]["content"]
                    result = json.loads(content)
                    
                    # Parse AI response
                    impacts = []
                    for imp in result.get("affected_instruments", []):
                        direction = imp.get("direction", "neutral")
                        emoji = "📈" if direction == "bullish" else "📉" if direction == "bearish" else "➡️"
                        
                        impacts.append(SymbolImpact(
                            symbol=imp.get("symbol", "XAUUSD"),
                            direction=direction,
                            score=imp.get("impact_score", 5),
                            confidence=imp.get("confidence", 0.7),
                            reasoning=imp.get("reasoning", ""),
                            emoji=emoji
                        ))
                    
                    key_levels = result.get("key_levels")
                    if key_levels:
                        key_levels = {
                            "support": key_levels.get("support", []),
                            "resistance": key_levels.get("resistance", [])
                        }
                    
                    return NewsAnalysisResult(
                        impacts=impacts,
                        sentiment=result.get("market_sentiment", "neutral"),
                        volatility_expectation=result.get("volatility_expectation", "medium"),
                        key_levels=key_levels,
                        event_duration=result.get("event_duration", "short_term"),
                        confidence=result.get("analysis_confidence", 70.0)
                    )
                    
        except Exception as e:
            # Fallback to generic analysis
            return NewsAnalysisResult(
                impacts=[
                    SymbolImpact(
                        symbol="XAUUSD",
                        direction="neutral",
                        score=3,
                        confidence=0.3,
                        reasoning=f"AI analysis failed: {str(e)[:50]}",
                        emoji="❓"
                    )
                ],
                sentiment="neutral",
                volatility_expectation="medium",
                key_levels=None,
                event_duration="short_term",
                confidence=30.0
            )
    
    async def analyze_news(
        self,
        headline: str,
        content: str = "",
        source: str = "",
        use_cache: bool = True
    ) -> NewsAnalysisResult:
        """
        Main analysis method - checks cache, rules, then AI
        """
        # Check cache first
        if use_cache:
            redis_client = await self._get_redis()
            if redis_client:
                cache_key = self._get_cache_key(headline, content)
                cached = await redis_client.get(cache_key)
                if cached:
                    data = json.loads(cached)
                    return NewsAnalysisResult(
                        impacts=[SymbolImpact(**i) for i in data.get("impacts", [])],
                        sentiment=data.get("sentiment", "neutral"),
                        volatility_expectation=data.get("volatility_expectation", "medium"),
                        key_levels=data.get("key_levels"),
                        event_duration=data.get("event_duration", "short_term"),
                        confidence=data.get("confidence", 70.0)
                    )
        
        # Check rule-based patterns
        rule_result = self._check_rule_based_impact(headline, content)
        if rule_result:
            # Cache rule-based result
            if use_cache:
                redis_client = await self._get_redis()
                if redis_client:
                    cache_key = self._get_cache_key(headline, content)
                    await redis_client.setex(
                        cache_key,
                        timedelta(hours=24),
                        json.dumps(asdict(rule_result), default=str)
                    )
            return rule_result
        
        # Fall back to AI analysis
        ai_result = await self._analyze_with_ai(headline, content, source)
        
        # Cache AI result
        if use_cache:
            redis_client = await self._get_redis()
            if redis_client:
                cache_key = self._get_cache_key(headline, content)
                await redis_client.setex(
                    cache_key,
                    timedelta(hours=24),
                    json.dumps(asdict(ai_result), default=str)
                )
        
        return ai_result
    
    async def batch_analyze(
        self,
        news_items: List[Dict[str, Any]],
        max_concurrent: int = 5
    ) -> List[NewsAnalysisResult]:
        """Analyze multiple news items concurrently"""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def analyze_with_limit(item):
            async with semaphore:
                return await self.analyze_news(
                    headline=item.get("headline", ""),
                    content=item.get("content", ""),
                    source=item.get("source", "")
                )
        
        tasks = [analyze_with_limit(item) for item in news_items]
        return await asyncio.gather(*tasks, return_exceptions=True)


# Singleton instance
_analyzer: Optional[NewsAnalyzer] = None


def get_analyzer() -> NewsAnalyzer:
    """Get or create analyzer singleton"""
    global _analyzer
    if _analyzer is None:
        _analyzer = NewsAnalyzer()
    return _analyzer
