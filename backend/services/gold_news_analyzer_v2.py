"""
Gold News Analyzer V2 - Advanced Production-Ready News Analysis for XAUUSD

Key Improvements over V1:
1. Context-aware NLP with negation detection
2. Source weighting based on reliability
3. Time decay for news freshness
4. Dynamic impact levels based on event type
5. Feedback loop with price validation
6. Economic surprise effects
7. Conflict detection (mixed signals)
"""
from __future__ import annotations

import logging
import re
import time
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
import httpx

from config import settings

logger = logging.getLogger(__name__)


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class NewsArticle:
    """Parsed news article with metadata"""
    title: str
    source: str
    timestamp: float  # Unix timestamp
    url: str = ""
    raw_sentiment: float = 0.0
    adjusted_sentiment: float = 0.0
    decay_factor: float = 1.0
    source_weight: float = 1.0
    impact_level: str = "low"
    negation_detected: bool = False
    context_modifier: float = 1.0
    final_score: float = 0.0
    validated: bool = False


@dataclass
class GoldNewsImpactV2:
    """Advanced impact analysis for gold from news"""
    sentiment_score: float  # -1 (bearish) to +1 (bullish for gold)
    confidence: float  # 0-100
    impact_level: str  # "high", "medium", "low"
    direction_bias: str  # "BUY", "SELL", "NEUTRAL"
    key_factors: List[str]
    news_count: int
    high_impact_events: List[Dict]
    # V2 additions
    conflicts: List[str] = field(default_factory=list)
    time_to_expiry_minutes: int = 60
    source_breakdown: Dict[str, int] = field(default_factory=dict)
    validation_status: str = "pending"
    economic_calendar_impact: float = 0.0


# =============================================================================
# SOURCE WEIGHTING - Reliability Scores
# =============================================================================

SOURCE_WEIGHTS = {
    # Tier 1: Most reliable financial news
    "reuters.com": 1.5,
    "bloomberg.com": 1.5,
    "wsj.com": 1.4,
    "ft.com": 1.4,
    "cnbc.com": 1.3,
    "marketwatch.com": 1.2,
    
    # Tier 2: Good financial sources
    "fxstreet.com": 1.1,
    "investing.com": 1.1,
    "forexlive.com": 1.0,
    "dailyfx.com": 1.0,
    "kitco.com": 1.1,  # Gold specialist
    
    # Tier 3: General news
    "yahoo.com": 0.9,
    "google.com": 0.9,
    "bbc.com": 0.9,
    "cnn.com": 0.8,
    
    # Tier 4: Speculative / Less reliable
    "zerohedge.com": 0.6,  # Often sensationalist
    "seekingalpha.com": 0.7,
    
    # Tier 5: Social media / Very risky
    "twitter.com": 0.3,
    "x.com": 0.3,
    "reddit.com": 0.4,
    
    # Default for unknown sources
    "default": 0.5,
}


def get_source_weight(source_url: str) -> float:
    """Get reliability weight for a news source"""
    if not source_url:
        return SOURCE_WEIGHTS["default"]
    
    source_lower = source_url.lower()
    for domain, weight in SOURCE_WEIGHTS.items():
        if domain in source_lower:
            return weight
    
    return SOURCE_WEIGHTS["default"]


# =============================================================================
# TIME DECAY - News Freshness
# =============================================================================

def calculate_time_decay(publish_timestamp: float, half_life_minutes: int = 30) -> float:
    """
    Calculate decay factor based on news age.
    
    Half-life of 30 minutes means:
    - 0 min old: 100% impact
    - 30 min old: 50% impact  
    - 60 min old: 25% impact
    - 120 min old: 6.25% impact
    
    Minimum 5% impact to not completely ignore old relevant news.
    """
    now = time.time()
    age_minutes = (now - publish_timestamp) / 60
    
    if age_minutes < 0:
        return 1.0  # Future dated (scheduled news)
    
    decay_factor = math.exp(-0.693 * age_minutes / half_life_minutes)  # ln(2) ≈ 0.693
    return max(decay_factor, 0.05)  # Minimum 5% impact


def parse_news_timestamp(date_str: str) -> float:
    """Parse various date formats to Unix timestamp"""
    if not date_str:
        return time.time() - 3600  # Default: 1 hour ago
    
    formats = [
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.timestamp()
        except ValueError:
            continue
    
    return time.time() - 3600  # Default if parsing fails


# =============================================================================
# DYNAMIC IMPACT LEVELS - Event-Based Scoring
# =============================================================================

EVENT_IMPACT_SCORES = {
    # Tier 1: Major market movers (0.35-0.45)
    "fed rate decision": 0.45,
    "fomc": 0.45,
    "interest rate decision": 0.40,
    "nfp": 0.40,
    "non-farm payroll": 0.40,
    "cpi release": 0.38,
    "inflation data": 0.35,
    
    # Tier 2: Significant events (0.25-0.35)
    "ecb decision": 0.35,
    "boe decision": 0.32,
    "gdp": 0.30,
    "pce": 0.30,
    "core inflation": 0.30,
    "nuclear": 0.35,
    "war": 0.35,
    "invasion": 0.35,
    
    # Tier 3: Moderate impact (0.15-0.25)
    "unemployment": 0.25,
    "retail sales": 0.22,
    "pmi": 0.20,
    "consumer confidence": 0.18,
    "fed member": 0.15,
    "central bank": 0.20,
    "geopolitical": 0.22,
    "sanctions": 0.20,
    
    # Tier 4: Lower impact (0.05-0.15)
    "rumor": 0.08,
    "speculation": 0.08,
    "analyst": 0.10,
    "forecast": 0.10,
}

# Gold-specific keyword impacts (more precise than V1)
GOLD_KEYWORDS_V2 = {
    # === BULLISH FOR GOLD ===
    "bullish": {
        # Real yields (most important gold driver)
        "real yields fall": 0.40,
        "real yields decline": 0.40,
        "real rates negative": 0.35,
        "tips yields fall": 0.35,
        
        # Central bank gold activity
        "central bank gold buying": 0.35,
        "gold reserves increase": 0.30,
        "etf inflows gold": 0.28,
        "gold demand surge": 0.25,
        
        # Geopolitical (flight to safety)
        "war escalat": 0.35,
        "military conflict": 0.32,
        "nuclear threat": 0.38,
        "geopolitical crisis": 0.30,
        "sanctions imposed": 0.25,
        
        # Fed dovish
        "rate cut announce": 0.35,
        "fed cuts rate": 0.35,
        "dovish fed": 0.30,
        "fed pivot": 0.30,
        "quantitative easing": 0.28,
        "pause rate hike": 0.25,
        
        # Inflation concerns
        "inflation surge": 0.28,
        "cpi higher than expected": 0.30,
        "inflation accelerat": 0.25,
        "stagflation": 0.30,
        
        # Dollar weakness
        "dollar plunge": 0.30,
        "dollar weakness": 0.25,
        "dxy falls": 0.25,
        "greenback tumble": 0.25,
        
        # Economic uncertainty
        "recession fear": 0.28,
        "banking crisis": 0.35,
        "financial crisis": 0.35,
        "market crash": 0.30,
        "default risk": 0.28,
    },
    
    # === BEARISH FOR GOLD ===
    "bearish": {
        # Real yields rising
        "real yields rise": -0.40,
        "real yields surge": -0.38,
        "real rates positive": -0.35,
        
        # Central bank gold activity
        "gold etf outflow": -0.28,
        "gold reserves decrease": -0.25,
        "gold selling": -0.22,
        
        # Fed hawkish
        "rate hike announce": -0.35,
        "fed raises rate": -0.35,
        "hawkish fed": -0.30,
        "aggressive tightening": -0.30,
        "rate hike accelerat": -0.28,
        
        # Inflation cooling
        "inflation fall": -0.25,
        "cpi lower than expected": -0.30,
        "inflation cool": -0.22,
        "disinflation": -0.20,
        
        # Dollar strength
        "dollar surge": -0.30,
        "dollar strength": -0.25,
        "dxy rises": -0.25,
        "greenback rally": -0.25,
        
        # Risk-on sentiment
        "risk on": -0.22,
        "equity rally": -0.20,
        "stock market surge": -0.20,
        "soft landing": -0.18,
        
        # Economic strength
        "strong jobs report": -0.25,
        "nfp beats": -0.28,
        "unemployment falls": -0.22,
        "gdp growth strong": -0.20,
    }
}


def get_event_impact_multiplier(headline: str) -> float:
    """Get impact multiplier based on event type in headline"""
    headline_lower = headline.lower()
    
    max_impact = 0.10  # Default baseline
    
    for event, impact in EVENT_IMPACT_SCORES.items():
        if event in headline_lower:
            max_impact = max(max_impact, impact)
    
    return max_impact


# =============================================================================
# CONTEXT-AWARE NLP - Negation & Modifier Detection
# =============================================================================

NEGATION_WORDS = [
    "not", "no", "never", "neither", "nobody", "nothing", "nowhere",
    "cancel", "cancelled", "delay", "delayed", "postpone", "postponed",
    "unlikely", "fail", "failed", "reject", "rejected", "deny", "denied",
    "halt", "halted", "pause", "paused", "stop", "stopped",
    "reverse", "reversed", "undo", "undone",
]

UNCERTAINTY_WORDS = [
    "may", "might", "could", "would", "possibly", "perhaps", "maybe",
    "consider", "considering", "contemplate", "discuss", "discussing",
    "potential", "potentially", "expect", "expected", "anticipate",
    "speculation", "rumor", "rumour", "unconfirmed",
]

CONFIRMATION_WORDS = [
    "announce", "announced", "confirm", "confirmed", "official",
    "decide", "decided", "approve", "approved", "implement",
    "immediately", "effective", "will", "has", "have",
]

INTENSIFIER_WORDS = [
    "surge", "plunge", "crash", "soar", "spike", "collapse",
    "historic", "unprecedented", "massive", "dramatic", "extreme",
    "sharply", "significantly", "substantially",
]


def detect_negation(headline: str) -> bool:
    """Detect if headline contains negation that reverses meaning"""
    headline_lower = headline.lower()
    
    for neg in NEGATION_WORDS:
        if neg in headline_lower:
            return True
    
    return False


def calculate_context_modifier(headline: str) -> float:
    """
    Calculate context modifier based on certainty/uncertainty.
    Returns: 0.3 (very uncertain) to 1.5 (confirmed + intense)
    """
    headline_lower = headline.lower()
    modifier = 1.0
    
    # Check for uncertainty (reduces impact)
    uncertainty_count = sum(1 for word in UNCERTAINTY_WORDS if word in headline_lower)
    if uncertainty_count > 0:
        modifier *= (0.7 ** uncertainty_count)  # Each uncertainty word reduces by 30%
    
    # Check for confirmation (increases impact)
    confirmation_count = sum(1 for word in CONFIRMATION_WORDS if word in headline_lower)
    if confirmation_count > 0:
        modifier *= (1.15 ** min(confirmation_count, 2))  # Max 32% boost
    
    # Check for intensifiers
    intensifier_count = sum(1 for word in INTENSIFIER_WORDS if word in headline_lower)
    if intensifier_count > 0:
        modifier *= (1.1 ** min(intensifier_count, 2))  # Max 21% boost
    
    return max(0.3, min(1.5, modifier))


def analyze_headline_v2(headline: str, source: str = "", timestamp: float = None) -> NewsArticle:
    """
    Advanced headline analysis with context awareness.
    
    Example:
    "Fed delays rate cut" -> Negation detected, BEARISH (not bullish)
    "Fed may consider rate cut" -> Uncertainty, weak bullish
    "Fed announces immediate rate cut" -> Confirmed, strong bullish
    """
    if timestamp is None:
        timestamp = time.time()
    
    headline_lower = headline.lower()
    
    # Initialize article
    article = NewsArticle(
        title=headline,
        source=source,
        timestamp=timestamp,
    )
    
    # 1. Get source weight
    article.source_weight = get_source_weight(source)
    
    # 2. Calculate time decay
    article.decay_factor = calculate_time_decay(timestamp)
    
    # 3. Detect negation
    article.negation_detected = detect_negation(headline)
    
    # 4. Calculate context modifier
    article.context_modifier = calculate_context_modifier(headline)
    
    # 5. Calculate raw sentiment from keywords
    raw_score = 0.0
    matched_keywords = []
    
    # Check bullish keywords
    for keyword, impact in GOLD_KEYWORDS_V2["bullish"].items():
        if keyword in headline_lower:
            raw_score += impact
            matched_keywords.append(f"🟢 {keyword}")
    
    # Check bearish keywords
    for keyword, impact in GOLD_KEYWORDS_V2["bearish"].items():
        if keyword in headline_lower:
            raw_score += impact  # Already negative
            matched_keywords.append(f"🔴 {keyword}")
    
    article.raw_sentiment = raw_score
    
    # 6. Apply negation (reverses sentiment!)
    if article.negation_detected and abs(raw_score) > 0:
        raw_score = -raw_score * 0.8  # Reverse with 80% magnitude
        logger.debug(f"Negation applied: {headline[:50]}...")
    
    # 7. Apply all modifiers
    adjusted_score = raw_score * article.context_modifier
    
    # 8. Calculate final score with decay and source weight
    article.final_score = adjusted_score * article.decay_factor * article.source_weight
    article.adjusted_sentiment = adjusted_score
    
    # 9. Determine impact level
    event_impact = get_event_impact_multiplier(headline)
    if event_impact >= 0.30 or abs(article.final_score) >= 0.25:
        article.impact_level = "high"
    elif event_impact >= 0.15 or abs(article.final_score) >= 0.12:
        article.impact_level = "medium"
    else:
        article.impact_level = "low"
    
    return article


# =============================================================================
# ECONOMIC CALENDAR - Surprise Effects
# =============================================================================

def calculate_economic_surprise(event: str, forecast: float, actual: float) -> float:
    """
    Calculate impact of economic surprise (actual vs forecast).
    
    For gold:
    - Higher CPI than expected = BULLISH (inflation hedge)
    - Higher NFP than expected = BEARISH (strong economy = hawkish fed)
    - Lower unemployment = BEARISH (strong economy)
    """
    if forecast is None or actual is None:
        return 0.0
    
    event_lower = event.lower()
    surprise_pct = (actual - forecast) / (abs(forecast) + 0.0001) * 100
    
    # CPI / Inflation: Higher = Bullish for gold
    if "cpi" in event_lower or "inflation" in event_lower:
        return min(0.35, max(-0.35, surprise_pct * 0.05))
    
    # NFP / Jobs: Higher = Bearish for gold
    if "nfp" in event_lower or "payroll" in event_lower or "employment" in event_lower:
        return min(0.35, max(-0.35, -surprise_pct * 0.04))
    
    # Unemployment: Higher = Bullish for gold (weak economy)
    if "unemployment" in event_lower:
        return min(0.30, max(-0.30, surprise_pct * 0.06))
    
    # GDP: Higher = Bearish for gold (strong economy)
    if "gdp" in event_lower:
        return min(0.25, max(-0.25, -surprise_pct * 0.03))
    
    return 0.0


# =============================================================================
# CONFLICT DETECTION - Mixed Signals
# =============================================================================

def detect_conflicts(articles: List[NewsArticle]) -> List[str]:
    """
    Detect conflicting signals in news batch.
    Returns list of conflict descriptions.
    """
    conflicts = []
    
    bullish_count = sum(1 for a in articles if a.final_score > 0.1)
    bearish_count = sum(1 for a in articles if a.final_score < -0.1)
    
    # Major conflict: significant bullish AND bearish signals
    if bullish_count >= 2 and bearish_count >= 2:
        conflicts.append(f"⚠️ Mixed signals: {bullish_count} bullish vs {bearish_count} bearish headlines")
    
    # Check for specific contradictions
    headlines_lower = [a.title.lower() for a in articles]
    
    if any("rate cut" in h for h in headlines_lower) and any("rate hike" in h for h in headlines_lower):
        conflicts.append("⚠️ Conflicting rate expectations in news")
    
    if any("dollar strength" in h or "dollar surge" in h for h in headlines_lower) and \
       any("dollar weakness" in h or "dollar fall" in h for h in headlines_lower):
        conflicts.append("⚠️ Conflicting USD direction signals")
    
    return conflicts


# =============================================================================
# MAIN ANALYSIS FUNCTION
# =============================================================================

async def fetch_gold_news_v2(limit: int = 50) -> List[Dict]:
    """Fetch news relevant to gold/XAUUSD with source info"""
    
    if not settings.eodhd_api_key:
        return _sample_gold_news_v2()
    
    params = {
        "api_token": settings.eodhd_api_key,
        "limit": limit,
        "fmt": "json",
        "s": "XAUUSD,GLD.US,GC.CMX,DXY.INDX",  # Gold + Dollar index
    }
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                "https://eodhistoricaldata.com/api/news",
                params=params
            )
            response.raise_for_status()
            return response.json() or []
    except Exception as e:
        logger.warning(f"Failed to fetch gold news: {e}")
        return _sample_gold_news_v2()


async def analyze_gold_news_impact_v2() -> GoldNewsImpactV2:
    """
    Advanced analysis of news impact on gold.
    
    Improvements over V1:
    - Context-aware with negation detection
    - Source reliability weighting
    - Time decay for freshness
    - Dynamic event-based impact
    - Conflict detection
    """
    
    raw_news = await fetch_gold_news_v2(limit=50)
    
    if not raw_news:
        return GoldNewsImpactV2(
            sentiment_score=0,
            confidence=20,
            impact_level="low",
            direction_bias="NEUTRAL",
            key_factors=["No recent news data available"],
            news_count=0,
            high_impact_events=[],
            conflicts=["Unable to fetch news"],
            time_to_expiry_minutes=0,
        )
    
    # Parse and analyze each article
    articles: List[NewsArticle] = []
    source_counts: Dict[str, int] = {}
    
    for item in raw_news:
        title = item.get("title") or ""
        source = item.get("link") or item.get("source") or ""
        date_str = item.get("date") or ""
        
        if not title:
            continue
        
        timestamp = parse_news_timestamp(date_str)
        article = analyze_headline_v2(title, source, timestamp)
        articles.append(article)
        
        # Track source distribution
        for domain in SOURCE_WEIGHTS.keys():
            if domain != "default" and domain in source.lower():
                source_counts[domain] = source_counts.get(domain, 0) + 1
                break
    
    if not articles:
        return GoldNewsImpactV2(
            sentiment_score=0,
            confidence=20,
            impact_level="low",
            direction_bias="NEUTRAL",
            key_factors=["No parseable news articles"],
            news_count=0,
            high_impact_events=[],
        )
    
    # Calculate weighted sentiment
    total_weight = sum(a.decay_factor * a.source_weight for a in articles)
    weighted_sentiment = sum(a.final_score for a in articles) / max(total_weight, 1)
    
    # Detect conflicts
    conflicts = detect_conflicts(articles)
    
    # If major conflicts, reduce confidence
    conflict_penalty = len(conflicts) * 10
    
    # Get high impact articles
    high_impact_articles = sorted(
        [a for a in articles if a.impact_level == "high"],
        key=lambda x: abs(x.final_score),
        reverse=True
    )[:5]
    
    # Build key factors
    key_factors = []
    for article in high_impact_articles:
        sentiment_icon = "🟢" if article.final_score > 0 else ("🔴" if article.final_score < 0 else "⚪")
        decay_info = f"({article.decay_factor*100:.0f}% fresh)"
        key_factors.append(f"{sentiment_icon} {article.title[:60]}... {decay_info}")
    
    # Calculate confidence
    high_impact_count = len(high_impact_articles)
    base_confidence = 40
    
    if len(articles) >= 20:
        base_confidence += 15
    if high_impact_count >= 3:
        base_confidence += 20
    if abs(weighted_sentiment) > 0.15:
        base_confidence += 15
    
    # Apply conflict penalty
    confidence = max(20, min(95, base_confidence - conflict_penalty))
    
    # Determine direction bias with higher threshold due to noise
    if weighted_sentiment > 0.10:
        direction_bias = "BUY"
    elif weighted_sentiment < -0.10:
        direction_bias = "SELL"
    else:
        direction_bias = "NEUTRAL"
    
    # Calculate time to expiry (based on freshest high-impact news)
    if high_impact_articles:
        freshest_age = min((time.time() - a.timestamp) / 60 for a in high_impact_articles)
        time_to_expiry = max(0, int(60 - freshest_age))  # 60 min total window
    else:
        time_to_expiry = 0
    
    # Determine overall impact level
    if high_impact_count >= 3 or abs(weighted_sentiment) > 0.20:
        impact_level = "high"
    elif high_impact_count >= 1 or abs(weighted_sentiment) > 0.10:
        impact_level = "medium"
    else:
        impact_level = "low"
    
    # Build high impact events list
    high_impact_events = []
    for article in high_impact_articles:
        high_impact_events.append({
            "headline": article.title[:100],
            "source": article.source[:50] if article.source else "unknown",
            "timestamp": int(article.timestamp),
            "individual_score": round(article.final_score, 3),
            "decay_factor": round(article.decay_factor, 2),
            "source_weight": round(article.source_weight, 2),
            "negation_detected": article.negation_detected,
            "sentiment": "bullish" if article.final_score > 0.05 else (
                "bearish" if article.final_score < -0.05 else "neutral"
            ),
        })
    
    return GoldNewsImpactV2(
        sentiment_score=round(weighted_sentiment, 4),
        confidence=round(confidence, 1),
        impact_level=impact_level,
        direction_bias=direction_bias,
        key_factors=key_factors,
        news_count=len(articles),
        high_impact_events=high_impact_events,
        conflicts=conflicts,
        time_to_expiry_minutes=time_to_expiry,
        source_breakdown=source_counts,
        validation_status="pending",
    )


# =============================================================================
# FEEDBACK LOOP - Price Validation
# =============================================================================

async def validate_news_prediction(
    symbol: str,
    news_time: float,
    expected_direction: str,
    check_after_minutes: int = 5
) -> Dict[str, Any]:
    """
    Validate news prediction against actual price movement.
    
    Returns validation result with accuracy score.
    """
    from services.data_fetcher import fetch_latest_price
    
    # This would need historical price data - simplified version
    current_price = await fetch_latest_price(symbol)
    
    return {
        "validated": False,
        "reason": "Price validation requires historical data integration",
        "expected_direction": expected_direction,
        "recommendation": "Implement with historical price fetch for full validation"
    }


# =============================================================================
# SAMPLE DATA
# =============================================================================

def _sample_gold_news_v2() -> List[Dict]:
    """Sample news for when API is unavailable"""
    now = datetime.utcnow()
    return [
        {
            "title": "Federal Reserve signals potential rate changes ahead",
            "date": now.isoformat(),
            "link": "https://reuters.com/fed-signals"
        },
        {
            "title": "Gold prices steady as investors await inflation data",
            "date": (now - timedelta(hours=1)).isoformat(),
            "link": "https://bloomberg.com/gold-steady"
        },
        {
            "title": "Geopolitical tensions continue to support safe haven demand",
            "date": (now - timedelta(hours=2)).isoformat(),
            "link": "https://cnbc.com/geopolitical"
        },
    ]


# =============================================================================
# BACKWARD COMPATIBILITY - Export V1 interface
# =============================================================================

# Alias for backward compatibility
GoldNewsImpact = GoldNewsImpactV2


async def analyze_gold_news_impact() -> GoldNewsImpactV2:
    """Backward compatible function name"""
    return await analyze_gold_news_impact_v2()
