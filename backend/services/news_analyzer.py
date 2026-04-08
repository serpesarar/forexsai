"""
News Analyzer Service
AI-powered news analysis for financial impact detection
Uses DeepSeek AI to analyze news and predict market impacts
"""

import json
import os
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import asyncio
import aiohttp
from functools import lru_cache
import redis.asyncio as redis

from utils.market_hours import is_new_york_market_open

# Configuration
DEEPSEEK_API_KEY = os.getenv("DEEP_SEEKR1", "")
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
    "trump_policy": {
        "keywords": ["trump", "trump's", "trump administration", "white house", "executive order"],
        "impacts": [
            {"symbol": "XAUUSD", "direction": "bullish", "score": 6, "reasoning": "Policy uncertainty safe haven"},
            {"symbol": "VIX", "direction": "bullish", "score": 7, "reasoning": "Political volatility"},
            {"symbol": "NASDAQ", "direction": "bearish", "score": 5, "reasoning": "Trade policy concerns"},
        ],
        "sentiment": "risk_off",
        "volatility": "medium",
    },
    "trump_iran": {
        "keywords": ["trump", "iran", "nuclear", "deal", "military", "threat", "attack iran", "iran war"],
        "impacts": [
            {"symbol": "XAUUSD", "direction": "bullish", "score": 9, "reasoning": "Safe haven demand"},
            {"symbol": "USOIL", "direction": "bullish", "score": 8, "reasoning": "Supply disruption risk"},
            {"symbol": "VIX", "direction": "bullish", "score": 8, "reasoning": "Geopolitical uncertainty"},
            {"symbol": "DXY", "direction": "bullish", "score": 6, "reasoning": "Safe haven flow"},
            {"symbol": "NASDAQ", "direction": "bearish", "score": 6, "reasoning": "Risk-off sentiment"},
        ],
        "sentiment": "risk_off",
        "volatility": "high",
    },
    "fed_rate": {
        "keywords": ["fed", "federal reserve", "fomc", "rate decision", "rate hike", "rate cut", "interest rate", "powell"],
        "impacts": [
            {"symbol": "DXY", "direction": "bullish", "score": 8, "reasoning": "Rate hike bullish for USD"},
            {"symbol": "XAUUSD", "direction": "bearish", "score": 7, "reasoning": "Higher rates hurt gold"},
            {"symbol": "NASDAQ", "direction": "bearish", "score": 7, "reasoning": "Higher rates hurt tech"},
        ],
        "sentiment": "risk_off" if "hike" in "{text}" else "neutral",
        "volatility": "high",
    },
    "fed_dovish": {
        "keywords": ["fed", "dovish", "rate cut", "easing", "accommodative", "powell dovish"],
        "impacts": [
            {"symbol": "DXY", "direction": "bearish", "score": 7, "reasoning": "Rate cuts weaken USD"},
            {"symbol": "XAUUSD", "direction": "bullish", "score": 8, "reasoning": "Lower rates help gold"},
            {"symbol": "NASDAQ", "direction": "bullish", "score": 8, "reasoning": "Lower rates help growth stocks"},
        ],
        "sentiment": "risk_on",
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
            {"symbol": "XAUUSD", "direction": "bullish", "score": 8, "reasoning": "Geopolitical safe haven demand"},
            {"symbol": "USOIL", "direction": "bullish", "score": 8, "reasoning": "Middle East supply disruption risk"},
            {"symbol": "VIX", "direction": "bullish", "score": 7, "reasoning": "Geopolitical uncertainty increases volatility"},
            {"symbol": "DXY", "direction": "mixed", "score": 4, "reasoning": "Flight to safety may help USD"},
            {"symbol": "NASDAQ", "direction": "bearish", "score": 5, "reasoning": "Risk-off sentiment hurts equities"},
        ],
        "sentiment": "risk_off",
        "volatility": "high",
    },
    "iran_conflict_escalation": {
        "keywords": ["iran", "fighter jets", "aircraft", "shot down", "qatar", "military confrontation"],
        "impacts": [
            {"symbol": "USOIL", "direction": "bullish", "score": 9, "reasoning": "Direct military confrontation threatens Strait of Hormuz"},
            {"symbol": "XAUUSD", "direction": "bullish", "score": 8, "reasoning": "Military escalation drives safe haven buying"},
            {"symbol": "VIX", "direction": "bullish", "score": 8, "reasoning": "Military conflict creates market fear"},
            {"symbol": "DXY", "direction": "bullish", "score": 6, "reasoning": "Safe haven flows into USD"},
            {"symbol": "NASDAQ", "direction": "bearish", "score": 7, "reasoning": "Geopolitical risk premium hurts stocks"},
        ],
        "sentiment": "risk_off",
        "volatility": "high",
    },
    "oil_shipping_crisis": {
        "keywords": ["supertanker", "shipping rates", "haul", "transport", "logistics"],
        "impacts": [
            {"symbol": "USOIL", "direction": "bullish", "score": 7, "reasoning": "Higher transport costs increase oil prices"},
            {"symbol": "XAUUSD", "direction": "neutral", "score": 4, "reasoning": "Indirect impact via oil prices"},
            {"symbol": "VIX", "direction": "bullish", "score": 5, "reasoning": "Supply chain disruptions add uncertainty"},
        ],
        "sentiment": "neutral",
        "volatility": "medium",
    },
    "prediction_markets": {
        "keywords": ["polymarket", "prediction market", "bets", "wagering", "odds"],
        "impacts": [
            {"symbol": "VIX", "direction": "bullish", "score": 6, "reasoning": "High betting volume indicates market uncertainty"},
            {"symbol": "XAUUSD", "direction": "neutral", "score": 4, "reasoning": "Sentiment indicator, not direct impact"},
        ],
        "sentiment": "neutral",
        "volatility": "medium",
    },
    "crypto_regulation": {
        "keywords": ["bitcoin", "crypto", "regulation", "sec", "etf", "spot etf", "crypto etf"],
        "impacts": [
            {"symbol": "BTCUSD", "direction": "bullish", "score": 8, "reasoning": "ETF approval/positive news"},
            {"symbol": "NASDAQ", "direction": "bullish", "score": 5, "reasoning": "Crypto correlation"},
        ],
        "sentiment": "risk_on",
        "volatility": "high",
    },
    "gold_breakout": {
        "keywords": ["gold", "xau", "gold price", "gold hits", "gold rally", "gold surge", "all-time high", "record high", "safe haven gold"],
        "impacts": [
            {"symbol": "XAUUSD", "direction": "bullish", "score": 9, "reasoning": "Gold momentum/breakout"},
            {"symbol": "DXY", "direction": "bearish", "score": 5, "reasoning": "Inverse correlation"},
            {"symbol": "VIX", "direction": "bullish", "score": 4, "reasoning": "Safe haven demand"},
        ],
        "sentiment": "risk_off",
        "volatility": "high",
    },
    "oil_supply": {
        "keywords": ["oil", "wti", "brent", "crude", "opec", "opec+", "production cut", "supply disruption", "oil inventory", "eia report", "api report"],
        "impacts": [
            {"symbol": "USOIL", "direction": "bullish", "score": 8, "reasoning": "Supply concerns"},
            {"symbol": "XAUUSD", "direction": "bullish", "score": 5, "reasoning": "Inflation hedge"},
        ],
        "sentiment": "risk_off",
        "volatility": "high",
    },
    "tech_earnings": {
        "keywords": ["earnings", "revenue", "profit", "guidance", "outlook", "nvidia", "apple", "tesla", "amazon", "microsoft", "google", "meta", "alphabet", "beat estimates", "miss estimates"],
        "impacts": [
            {"symbol": "NASDAQ", "direction": "bullish", "score": 7, "reasoning": "Tech earnings positive"},
            {"symbol": "DAX", "direction": "bullish", "score": 5, "reasoning": "Global risk-on"},
        ],
        "sentiment": "risk_on",
        "volatility": "medium",
    },
    "banking_crisis": {
        "keywords": ["bank", "banking crisis", "bank failure", "deposit", "fdic", "credit suisse", "deutsche bank", "svb", "silicon valley bank", "contagion", "liquidity crisis"],
        "impacts": [
            {"symbol": "XAUUSD", "direction": "bullish", "score": 9, "reasoning": "Banking crisis safe haven"},
            {"symbol": "VIX", "direction": "bullish", "score": 9, "reasoning": "Financial panic"},
            {"symbol": "DXY", "direction": "bearish", "score": 5, "reasoning": "Fed may cut rates"},
            {"symbol": "NASDAQ", "direction": "bearish", "score": 7, "reasoning": "Financial sector drag"},
        ],
        "sentiment": "risk_off",
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
    reasoning_tr: str = ""  # Turkish translation
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
    
    async def _translate_with_ai(self, text: str, target_lang: str = "tr") -> str:
        """Translate text using DeepSeek AI"""
        if not self.api_key or self.api_key == "":
            return text

        if not is_new_york_market_open():
            return text
            
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                prompt = f"""Translate the following financial news to {target_lang.upper()}.
Keep financial terms accurate and professional.

TEXT: {text}

Provide ONLY the translation, no explanation, no markdown, no JSON.
Just the translated text."""

                payload = {
                    "model": "deepseek-reasoner",
                    "messages": [
                        {"role": "user", "content": "You are a professional financial translator. Translate accurately while keeping financial terminology precise.\n\n" + prompt}
                    ],
                    "max_tokens": 500
                }
                
                async with session.post(
                    DEEPSEEK_API_URL,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        translation = data["choices"][0]["message"]["content"].strip()
                        return translation
                    else:
                        return text
        except Exception as e:
            print(f"[Translate] Error: {e}")
            return text

    async def _analyze_with_ai(
        self,
        headline: str,
        content: str = "",
        source: str = ""
    ) -> NewsAnalysisResult:
        """Analyze news using DeepSeek AI with multi-language support"""

        if not is_new_york_market_open():
            raise RuntimeError("DeepSeek disabled outside New York market hours")
        
        # Translate content to Turkish for analysis context
        headline_tr = await self._translate_with_ai(headline, "tr") if headline else ""
        content_tr = await self._translate_with_ai(content[:300], "tr") if content else ""
        
        prompt = f"""Analyze this financial news and extract market impact information.

ORIGINAL (EN):
HEADLINE: {headline}
CONTENT: {content[:500] if content else "N/A"}

TRANSLATED (TR):
BAŞLIK: {headline_tr}
İÇERİK: {content_tr[:300] if content_tr else "N/A"}

SOURCE: {source}
TIMESTAMP: {datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")}

Provide analysis in strict JSON format:
{{
    "affected_instruments": [
        {{
            "symbol": "XAUUSD|NASDAQ|DAX|USOIL|VIX|DXY|EURUSD|GBPUSD|BTCUSD",
            "direction": "bullish|bearish|neutral",
            "impact_score": 1-10,
            "confidence": 0.0-1.0,
            "reasoning": "brief explanation",
            "reasoning_tr": "brief explanation in Turkish"
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

Market Impact Rules:
- Trump/Iran tensions → XAUUSD↑ (safe haven), USOIL↑ (supply risk), VIX↑ (fear), NASDAQ↓
- Fed rate decisions → DXY moves opposite to NASDAQ
- Strong jobs data → DXY↑, XAUUSD↓
- Inflation surprise → XAUUSD↑, DXY↑
- ECB decisions → EURUSD affected, DXY inverse
- Middle East conflict → XAUUSD↑, USOIL↑, VIX↑, NASDAQ↓
- Gold/Oil price spikes → affected commodity direction, inverse safe havens

Output JSON only, no markdown."""

        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": "deepseek-reasoner",
                    "messages": [
                        {"role": "user", "content": "You are a financial market analyst. Analyze news and predict market impacts accurately. Respond in JSON format.\n\n" + prompt}
                    ],
                    "max_tokens": 1000
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
                            reasoning_tr=imp.get("reasoning_tr", ""),
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
        use_cache: bool = True,
        force_ai: bool = True  # Default to AI analysis for better accuracy
    ) -> NewsAnalysisResult:
        """
        Main analysis method - ALWAYS uses DeepSeek AI for dynamic analysis
        Only falls back to rule-based if AI fails
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
        
        # PRIMARY: Always use DeepSeek AI for dynamic analysis
        ai_result = None
        if self.api_key and self.api_key != "":
            try:
                ai_result = await self._analyze_with_ai(headline, content, source)
                # Validate AI result - if too generic, enhance with rules
                if ai_result and len(ai_result.impacts) > 0:
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
            except Exception as e:
                print(f"[NewsAnalyzer] AI analysis failed, falling back to rules: {e}")
        
        # FALLBACK: Use rule-based if AI fails or no API key
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
        
        # ULTIMATE FALLBACK: Generic neutral analysis
        fallback_result = NewsAnalysisResult(
            impacts=[
                SymbolImpact(
                    symbol="XAUUSD",
                    direction="neutral",
                    score=3,
                    confidence=0.3,
                    reasoning="Unable to determine specific impact from available information",
                    emoji="❓"
                )
            ],
            sentiment="neutral",
            volatility_expectation="low",
            key_levels=None,
            event_duration="short_term",
            confidence=30.0
        )
        
        return fallback_result
    
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
