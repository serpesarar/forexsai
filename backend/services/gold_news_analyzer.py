"""
Gold News Analyzer - Analyzes news specifically impacting XAUUSD (Gold)

Gold is heavily influenced by:
- Interest rate decisions (Fed, ECB, etc.)
- Inflation data (CPI, PPI)
- Geopolitical events (wars, tensions)
- USD strength/weakness
- Economic uncertainty/crisis
- Central bank gold reserves
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import httpx

from config import settings

logger = logging.getLogger(__name__)


@dataclass
class GoldNewsImpact:
    """Impact analysis for gold from news"""
    sentiment_score: float  # -1 (bearish) to +1 (bullish for gold)
    confidence: float  # 0-100
    impact_level: str  # "high", "medium", "low"
    direction_bias: str  # "BUY", "SELL", "NEUTRAL"
    key_factors: List[str]
    news_count: int
    high_impact_events: List[Dict]


# Keywords that impact gold prices
GOLD_BULLISH_KEYWORDS = [
    # Geopolitical risk (flight to safety)
    "war", "conflict", "military", "attack", "invasion", "nuclear", "missile",
    "tension", "escalation", "crisis", "sanctions", "geopolitical",
    # Economic uncertainty
    "recession", "crash", "collapse", "default", "bailout", "banking crisis",
    "financial crisis", "market panic", "volatility spike",
    # Inflation (gold hedge)
    "inflation rising", "inflation surges", "cpi higher", "inflation fears",
    "price pressures", "cost of living",
    # Dovish Fed / Rate cuts
    "rate cut", "dovish", "easing", "stimulus", "qe", "quantitative easing",
    "fed pivot", "pause rate", "lower rates",
    # USD weakness
    "dollar falls", "dollar drops", "dollar weakness", "usd down",
    "greenback falls", "dollar index falls",
    # Central bank gold buying
    "central bank gold", "gold reserves", "gold buying", "gold demand",
]

GOLD_BEARISH_KEYWORDS = [
    # Risk-on sentiment
    "risk on", "rally", "bullish stocks", "equity surge", "market optimism",
    # Hawkish Fed / Rate hikes
    "rate hike", "hawkish", "tightening", "higher rates", "fed raises",
    "rate increase", "monetary tightening",
    # Strong USD
    "dollar rises", "dollar surges", "dollar strength", "usd up",
    "greenback rallies", "dollar index rises", "dxy up",
    # Inflation cooling
    "inflation falls", "inflation eases", "cpi lower", "inflation cooling",
    "disinflation", "price stability",
    # Economic strength
    "strong jobs", "unemployment falls", "gdp growth", "economic recovery",
    "soft landing",
]

HIGH_IMPACT_EVENTS = [
    "fomc", "fed decision", "interest rate decision", "nfp", "non-farm payroll",
    "cpi", "inflation data", "ecb", "boe", "boj", "central bank",
    "gdp", "unemployment rate", "retail sales",
]


def analyze_headline(headline: str) -> Tuple[float, str]:
    """
    Analyze a single headline for gold impact.
    Returns: (sentiment_score, impact_level)
    """
    headline_lower = headline.lower()
    
    bullish_score = 0
    bearish_score = 0
    is_high_impact = False
    
    # Check for high impact events
    for event in HIGH_IMPACT_EVENTS:
        if event in headline_lower:
            is_high_impact = True
            break
    
    # Check bullish keywords
    for keyword in GOLD_BULLISH_KEYWORDS:
        if keyword in headline_lower:
            if keyword in ["war", "conflict", "nuclear", "invasion", "crisis"]:
                bullish_score += 2  # High impact geopolitical
            else:
                bullish_score += 1
    
    # Check bearish keywords
    for keyword in GOLD_BEARISH_KEYWORDS:
        if keyword in headline_lower:
            if keyword in ["rate hike", "hawkish", "dollar surges"]:
                bearish_score += 2  # High impact monetary
            else:
                bearish_score += 1
    
    # Calculate net score
    net_score = bullish_score - bearish_score
    
    # Normalize to -1 to +1 range
    max_possible = max(bullish_score + bearish_score, 1)
    sentiment = net_score / max_possible
    sentiment = max(-1, min(1, sentiment))
    
    impact_level = "high" if is_high_impact or abs(net_score) >= 2 else (
        "medium" if abs(net_score) >= 1 else "low"
    )
    
    return sentiment, impact_level


async def fetch_gold_news(limit: int = 30) -> List[Dict]:
    """Fetch news relevant to gold/XAUUSD.

    Vendor news API retired — live news now flows through the RSS aggregator /
 Telegram news detector (coming later). This returns sample data as a fallback.
    """
    return _sample_gold_news()


async def fetch_economic_calendar() -> List[Dict]:
    """Upcoming economic events impacting gold.

    Vendor economic-events API retired; returns empty until a new
    economic-calendar source is wired (see economic_calendar_service).
    """
    return []


async def analyze_gold_news_impact() -> GoldNewsImpact:
    """
    Analyze overall news impact on gold.
    Returns comprehensive sentiment analysis for trading decisions.
    """
    
    news = await fetch_gold_news(limit=50)
    events = await fetch_economic_calendar()
    
    if not news:
        return GoldNewsImpact(
            sentiment_score=0,
            confidence=30,
            impact_level="low",
            direction_bias="NEUTRAL",
            key_factors=["No recent news data available"],
            news_count=0,
            high_impact_events=[]
        )
    
    total_sentiment = 0
    high_impact_count = 0
    key_factors = []
    high_impact_news = []
    
    for article in news:
        title = article.get("title") or ""
        sentiment, impact = analyze_headline(title)
        
        total_sentiment += sentiment
        
        if impact == "high":
            high_impact_count += 1
            high_impact_news.append({
                "title": title[:100],
                "sentiment": "bullish" if sentiment > 0 else ("bearish" if sentiment < 0 else "neutral"),
                "date": article.get("date", "")
            })
            
            # Extract key factor
            title_lower = title.lower()
            for kw in GOLD_BULLISH_KEYWORDS[:10] + GOLD_BEARISH_KEYWORDS[:10]:
                if kw in title_lower:
                    factor = f"{'🟢' if sentiment > 0 else '🔴'} {kw.title()}"
                    if factor not in key_factors:
                        key_factors.append(factor)
                    break
    
    # Add upcoming events as factors
    for event in events[:3]:
        event_name = event.get("event", "")
        event_date = event.get("date", "")
        key_factors.append(f"📅 Upcoming: {event_name} ({event_date})")
    
    # Calculate average sentiment
    avg_sentiment = total_sentiment / len(news) if news else 0
    
    # Determine confidence based on news volume and impact
    base_confidence = 50
    if len(news) >= 20:
        base_confidence += 15
    if high_impact_count >= 3:
        base_confidence += 20
    if abs(avg_sentiment) > 0.3:
        base_confidence += 15
    
    confidence = min(95, base_confidence)
    
    # Determine direction bias
    if avg_sentiment > 0.15:
        direction_bias = "BUY"
    elif avg_sentiment < -0.15:
        direction_bias = "SELL"
    else:
        direction_bias = "NEUTRAL"
    
    # Determine overall impact level
    if high_impact_count >= 3 or abs(avg_sentiment) > 0.4:
        impact_level = "high"
    elif high_impact_count >= 1 or abs(avg_sentiment) > 0.2:
        impact_level = "medium"
    else:
        impact_level = "low"
    
    return GoldNewsImpact(
        sentiment_score=round(avg_sentiment, 3),
        confidence=round(confidence, 1),
        impact_level=impact_level,
        direction_bias=direction_bias,
        key_factors=key_factors[:10],
        news_count=len(news),
        high_impact_events=high_impact_news[:5]
    )


def _sample_gold_news() -> List[Dict]:
    """Sample news for when API is unavailable"""
    return [
        {"title": "Federal Reserve signals potential rate changes ahead", "date": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")},
        {"title": "Gold prices steady as investors await inflation data", "date": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")},
        {"title": "Geopolitical tensions continue to support safe haven demand", "date": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")},
    ]
