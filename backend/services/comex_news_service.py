"""
COMEX/CME News Service
Anlık vadeli işlem haberleri ve faiz kararları takibi

Kaynaklar:
1. CME Group RSS Feeds (resmi, 15-30sn gecikme)
2. Investing.com RSS (alternatif)
3. FXStreet RSS (alternatif)

Analiz: Groq/Claude ile hızlı sentiment analizi (ücretsiz tier)
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import xml.etree.ElementTree as ET
import re

import httpx

from config import settings

logger = logging.getLogger(__name__)


# =============================================================================
# RSS FEED SOURCES
# =============================================================================

CME_RSS_FEEDS = {
    "gold_futures": "https://www.cmegroup.com/rss/news/gold.xml",
    "silver_futures": "https://www.cmegroup.com/rss/news/silver.xml",
    "interest_rates": "https://www.cmegroup.com/rss/news/interest-rates.xml",
    "fed_watch": "https://www.cmegroup.com/rss/news/fed-funds.xml",
    "metals": "https://www.cmegroup.com/rss/news/metals.xml",
}

ALTERNATIVE_RSS_FEEDS = {
    "investing_gold": "https://www.investing.com/rss/news_301.rss",  # Gold news
    "investing_commodities": "https://www.investing.com/rss/news_14.rss",  # Commodities
    "fxstreet_gold": "https://www.fxstreet.com/rss/gold",
}

# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class COMEXNewsItem:
    """Tek bir COMEX haberi"""
    id: str
    title: str
    content: str
    source: str
    published_at: datetime
    link: str
    
    # Analiz sonuçları
    impact_score: int = 0  # 0-100
    direction: str = "neutral"  # bullish, bearish, neutral
    direction_numeric: float = 0.0  # -1.0 to +1.0
    symbols_affected: List[str] = field(default_factory=list)
    confidence: int = 50
    reasoning: str = ""
    
    # Kategoriler
    is_margin_related: bool = False
    is_rate_related: bool = False
    is_fed_related: bool = False
    is_comex_official: bool = False


@dataclass
class COMEXNewsImpact:
    """Birleştirilmiş COMEX haber etkisi"""
    
    # Ana metrikler
    overall_impact: float  # -1.0 to +1.0
    impact_score: int  # 0-100
    confidence: int  # 0-100
    direction: str  # BUY, SELL, HOLD
    
    # Detaylar
    recent_news: List[COMEXNewsItem]
    high_impact_news: List[COMEXNewsItem]
    
    # ML Features
    ml_features: Dict[str, float]
    
    # Meta
    last_update: datetime
    news_count: int
    should_block_trading: bool = False
    block_reason: str = ""


# =============================================================================
# KEYWORD ANALYSIS
# =============================================================================

# COMEX/CME için kritik kelimeler
BEARISH_KEYWORDS = {
    # Margin artışı = bearish (maliyet artar, long pozisyonlar kapanır)
    "margin increase": -0.8,
    "margin hike": -0.8,
    "margin requirement": -0.6,
    "margin raised": -0.7,
    "higher margin": -0.6,
    
    # Faiz artışı = bearish for gold
    "rate hike": -0.7,
    "rate increase": -0.6,
    "hawkish": -0.5,
    "tightening": -0.5,
    "higher rates": -0.5,
    
    # Dolar güçlenmesi = bearish
    "dollar strength": -0.4,
    "dollar rally": -0.4,
    "usd surge": -0.4,
    
    # Risk-on = bearish for gold
    "risk on": -0.3,
    "equity rally": -0.3,
    "stock surge": -0.3,
}

BULLISH_KEYWORDS = {
    # Margin düşüşü = bullish
    "margin decrease": 0.6,
    "margin cut": 0.6,
    "margin reduced": 0.5,
    "lower margin": 0.5,
    
    # Faiz düşüşü = bullish for gold
    "rate cut": 0.7,
    "rate decrease": 0.6,
    "dovish": 0.5,
    "easing": 0.5,
    "lower rates": 0.5,
    
    # Güvenli liman = bullish
    "safe haven": 0.6,
    "gold surge": 0.5,
    "gold rally": 0.5,
    "flight to safety": 0.6,
    
    # Enflasyon = bullish for gold
    "inflation rise": 0.5,
    "inflation surge": 0.6,
    "cpi higher": 0.4,
    
    # Jeopolitik = bullish
    "geopolitical": 0.4,
    "tension": 0.3,
    "crisis": 0.5,
    "war": 0.5,
    "sanctions": 0.4,
}

HIGH_IMPACT_KEYWORDS = [
    "margin", "comex", "cme", "fed", "fomc", "rate decision",
    "interest rate", "powell", "emergency", "halt", "suspend",
    "circuit breaker", "limit", "settlement"
]


# =============================================================================
# RSS PARSER
# =============================================================================

async def fetch_rss_feed(url: str, timeout: float = 10.0) -> List[Dict[str, Any]]:
    """RSS feed'den haberleri çek"""
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            headers = {
                "User-Agent": "Mozilla/5.0 (compatible; ForexsAI/1.0; +https://forexsai.com)"
            }
            response = await client.get(url, headers=headers)
            
            if response.status_code != 200:
                logger.warning(f"RSS fetch failed for {url}: {response.status_code}")
                return []
            
            # Parse XML
            root = ET.fromstring(response.text)
            items = []
            
            # Standard RSS format
            for item in root.findall(".//item"):
                title = item.findtext("title", "")
                description = item.findtext("description", "")
                link = item.findtext("link", "")
                pub_date = item.findtext("pubDate", "")
                
                if title:
                    items.append({
                        "title": title.strip(),
                        "content": description.strip() if description else "",
                        "link": link.strip() if link else "",
                        "pub_date": pub_date.strip() if pub_date else "",
                        "source": url
                    })
            
            # Atom format fallback
            if not items:
                ns = {"atom": "http://www.w3.org/2005/Atom"}
                for entry in root.findall(".//atom:entry", ns):
                    title = entry.findtext("atom:title", "", ns)
                    content = entry.findtext("atom:summary", "", ns) or entry.findtext("atom:content", "", ns)
                    link_elem = entry.find("atom:link", ns)
                    link = link_elem.get("href", "") if link_elem is not None else ""
                    updated = entry.findtext("atom:updated", "", ns)
                    
                    if title:
                        items.append({
                            "title": title.strip(),
                            "content": content.strip() if content else "",
                            "link": link.strip(),
                            "pub_date": updated.strip(),
                            "source": url
                        })
            
            return items
            
    except ET.ParseError as e:
        logger.error(f"XML parse error for {url}: {e}")
        return []
    except Exception as e:
        logger.error(f"RSS fetch error for {url}: {e}")
        return []


def parse_rss_date(date_str: str) -> datetime:
    """RSS tarih formatlarını parse et"""
    formats = [
        "%a, %d %b %Y %H:%M:%S %z",  # RFC 822
        "%a, %d %b %Y %H:%M:%S GMT",
        "%Y-%m-%dT%H:%M:%S%z",  # ISO 8601
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d %H:%M:%S",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    # Fallback to now
    return datetime.utcnow()


# =============================================================================
# KEYWORD-BASED ANALYSIS (Free, Fast)
# =============================================================================

def analyze_headline_keywords(title: str, content: str = "") -> Dict[str, Any]:
    """
    Keyword-based hızlı analiz (ücretsiz, <1ms)
    """
    text = (title + " " + content).lower()
    
    sentiment = 0.0
    matched_keywords = []
    is_high_impact = False
    
    # Bearish keywords
    for keyword, score in BEARISH_KEYWORDS.items():
        if keyword in text:
            sentiment += score
            matched_keywords.append(f"bearish: {keyword}")
    
    # Bullish keywords
    for keyword, score in BULLISH_KEYWORDS.items():
        if keyword in text:
            sentiment += score
            matched_keywords.append(f"bullish: {keyword}")
    
    # High impact check
    for keyword in HIGH_IMPACT_KEYWORDS:
        if keyword in text:
            is_high_impact = True
            break
    
    # Normalize sentiment to -1 to +1
    sentiment = max(-1.0, min(1.0, sentiment))
    
    # Direction
    if sentiment > 0.15:
        direction = "bullish"
    elif sentiment < -0.15:
        direction = "bearish"
    else:
        direction = "neutral"
    
    # Impact score (0-100)
    impact_score = int(abs(sentiment) * 100)
    if is_high_impact:
        impact_score = min(100, impact_score + 30)
    
    # Confidence based on keyword matches
    confidence = min(85, 40 + len(matched_keywords) * 15)
    
    return {
        "sentiment": sentiment,
        "direction": direction,
        "impact_score": impact_score,
        "confidence": confidence,
        "matched_keywords": matched_keywords,
        "is_high_impact": is_high_impact,
        "is_margin_related": "margin" in text,
        "is_rate_related": any(k in text for k in ["rate", "fed", "fomc", "powell"]),
        "is_fed_related": any(k in text for k in ["fed", "fomc", "powell", "federal reserve"]),
        "is_comex_official": "cme" in text or "comex" in text,
    }


# =============================================================================
# GROQ ANALYSIS (Free Tier - 30 req/min)
# =============================================================================

async def analyze_with_groq(title: str, content: str = "") -> Optional[Dict[str, Any]]:
    """
    Groq ile ücretsiz AI analizi (Llama 3.1 70B)
    Rate limit: 30 requests/minute (free tier)
    """
    if not settings.groq_api_key:
        return None
    
    prompt = f"""Analyze this COMEX/commodities news for gold trading impact.

NEWS: "{title}"
{f'DETAILS: "{content[:500]}"' if content else ''}

Return JSON only:
{{
    "impact_score": 0-100 (how significant for gold price),
    "direction": "bullish" | "bearish" | "neutral" (for GOLD),
    "direction_numeric": -1.0 to +1.0,
    "confidence": 0-100,
    "symbols_affected": ["XAUUSD", "SILVER", etc],
    "reasoning": "brief explanation",
    "is_margin_related": true/false,
    "is_rate_related": true/false,
    "time_sensitivity": "immediate" | "short_term" | "medium_term"
}}

Rules:
- Margin INCREASE = bearish for gold (higher costs, less longs)
- Rate HIKE = bearish for gold (opportunity cost)
- Rate CUT = bullish for gold
- Safe haven demand = bullish for gold
- Dollar strength = bearish for gold"""

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.groq_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.1-70b-versatile",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                    "max_tokens": 300,
                    "response_format": {"type": "json_object"}
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                import json
                return json.loads(content)
            else:
                logger.warning(f"Groq API error: {response.status_code}")
                return None
                
    except Exception as e:
        logger.error(f"Groq analysis error: {e}")
        return None


# =============================================================================
# COMEX NEWS SERVICE
# =============================================================================

class COMEXNewsService:
    """
    COMEX/CME haber servisi
    
    Kullanım:
        service = COMEXNewsService()
        impact = await service.get_comex_impact()
    """
    
    def __init__(self):
        self._cache: Dict[str, COMEXNewsItem] = {}
        self._last_fetch: Optional[datetime] = None
        self._cache_duration = timedelta(minutes=2)
        self._seen_hashes: set = set()
    
    def _generate_news_id(self, title: str, source: str) -> str:
        """Unique ID for deduplication"""
        content = f"{title}:{source}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    async def fetch_all_feeds(self) -> List[COMEXNewsItem]:
        """Tüm RSS feed'lerden haberleri çek"""
        
        # Cache check
        if (self._last_fetch and 
            datetime.utcnow() - self._last_fetch < self._cache_duration and
            self._cache):
            return list(self._cache.values())
        
        all_news = []
        
        # CME feeds (primary)
        cme_tasks = [
            fetch_rss_feed(url) 
            for url in CME_RSS_FEEDS.values()
        ]
        
        # Alternative feeds (backup)
        alt_tasks = [
            fetch_rss_feed(url)
            for url in ALTERNATIVE_RSS_FEEDS.values()
        ]
        
        # Fetch all in parallel
        results = await asyncio.gather(*cme_tasks, *alt_tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Feed fetch error: {result}")
                continue
            if isinstance(result, list):
                for item in result:
                    # Deduplicate
                    news_id = self._generate_news_id(item["title"], item["source"])
                    if news_id in self._seen_hashes:
                        continue
                    self._seen_hashes.add(news_id)
                    
                    # Parse date
                    pub_date = parse_rss_date(item.get("pub_date", ""))
                    
                    # Filter old news (>24h)
                    if datetime.utcnow() - pub_date.replace(tzinfo=None) > timedelta(hours=24):
                        continue
                    
                    # Create news item
                    news_item = COMEXNewsItem(
                        id=news_id,
                        title=item["title"],
                        content=item.get("content", ""),
                        source=item["source"],
                        published_at=pub_date,
                        link=item.get("link", ""),
                        symbols_affected=["XAUUSD", "GOLD"]
                    )
                    
                    all_news.append(news_item)
        
        # Sort by date (newest first)
        all_news.sort(key=lambda x: x.published_at, reverse=True)
        
        # Update cache
        self._cache = {n.id: n for n in all_news[:50]}  # Keep last 50
        self._last_fetch = datetime.utcnow()
        
        return all_news[:50]
    
    async def analyze_news_item(self, news: COMEXNewsItem, use_ai: bool = True) -> COMEXNewsItem:
        """Tek bir haberi analiz et"""
        
        # 1. Keyword-based analysis (always)
        keyword_analysis = analyze_headline_keywords(news.title, news.content)
        
        # 2. AI analysis (if enabled and high impact)
        ai_analysis = None
        if use_ai and keyword_analysis["is_high_impact"]:
            ai_analysis = await analyze_with_groq(news.title, news.content)
        
        # 3. Merge results
        if ai_analysis:
            news.impact_score = ai_analysis.get("impact_score", keyword_analysis["impact_score"])
            news.direction = ai_analysis.get("direction", keyword_analysis["direction"])
            news.direction_numeric = ai_analysis.get("direction_numeric", keyword_analysis["sentiment"])
            news.confidence = ai_analysis.get("confidence", keyword_analysis["confidence"])
            news.reasoning = ai_analysis.get("reasoning", "")
            news.symbols_affected = ai_analysis.get("symbols_affected", ["XAUUSD"])
        else:
            news.impact_score = keyword_analysis["impact_score"]
            news.direction = keyword_analysis["direction"]
            news.direction_numeric = keyword_analysis["sentiment"]
            news.confidence = keyword_analysis["confidence"]
            news.reasoning = ", ".join(keyword_analysis["matched_keywords"][:3])
        
        # 4. Set flags
        news.is_margin_related = keyword_analysis["is_margin_related"]
        news.is_rate_related = keyword_analysis["is_rate_related"]
        news.is_fed_related = keyword_analysis["is_fed_related"]
        news.is_comex_official = keyword_analysis["is_comex_official"]
        
        return news
    
    async def get_comex_impact(self, use_ai: bool = True) -> COMEXNewsImpact:
        """
        Birleştirilmiş COMEX haber etkisi
        
        Returns:
            COMEXNewsImpact with overall impact and ML features
        """
        
        # Fetch all news
        all_news = await self.fetch_all_feeds()
        
        if not all_news:
            return COMEXNewsImpact(
                overall_impact=0.0,
                impact_score=0,
                confidence=20,
                direction="HOLD",
                recent_news=[],
                high_impact_news=[],
                ml_features=self._get_empty_features(),
                last_update=datetime.utcnow(),
                news_count=0
            )
        
        # Analyze each news item
        analyzed_news = []
        for news in all_news[:20]:  # Analyze top 20
            analyzed = await self.analyze_news_item(news, use_ai=use_ai)
            analyzed_news.append(analyzed)
        
        # Calculate time-weighted impact
        now = datetime.utcnow()
        total_impact = 0.0
        total_weight = 0.0
        high_impact_news = []
        
        for news in analyzed_news:
            # Time decay (half-life = 30 minutes)
            age_minutes = (now - news.published_at.replace(tzinfo=None)).total_seconds() / 60
            decay = max(0.1, 1.0 - (age_minutes / 60))  # 1h = 0% decay
            
            # Weight by impact score
            weight = (news.impact_score / 100) * decay
            total_impact += news.direction_numeric * weight
            total_weight += weight
            
            # Track high impact
            if news.impact_score >= 70:
                high_impact_news.append(news)
        
        # Normalize
        overall_impact = total_impact / max(total_weight, 0.1)
        overall_impact = max(-1.0, min(1.0, overall_impact))
        
        # Direction
        if overall_impact > 0.15:
            direction = "BUY"
        elif overall_impact < -0.15:
            direction = "SELL"
        else:
            direction = "HOLD"
        
        # Impact score (0-100)
        impact_score = int(abs(overall_impact) * 100)
        
        # Confidence
        confidence = min(90, 30 + len(analyzed_news) * 3 + len(high_impact_news) * 10)
        
        # Should block trading?
        should_block = any(n.impact_score >= 85 for n in high_impact_news)
        block_reason = ""
        if should_block:
            critical_news = [n for n in high_impact_news if n.impact_score >= 85]
            block_reason = f"Critical news: {critical_news[0].title[:50]}..."
        
        # ML Features
        ml_features = self._calculate_ml_features(analyzed_news, overall_impact)
        
        return COMEXNewsImpact(
            overall_impact=overall_impact,
            impact_score=impact_score,
            confidence=confidence,
            direction=direction,
            recent_news=analyzed_news[:10],
            high_impact_news=high_impact_news,
            ml_features=ml_features,
            last_update=now,
            news_count=len(analyzed_news),
            should_block_trading=should_block,
            block_reason=block_reason
        )
    
    def _calculate_ml_features(self, news: List[COMEXNewsItem], overall_impact: float) -> Dict[str, float]:
        """ML modeli için feature'lar"""
        
        margin_news = [n for n in news if n.is_margin_related]
        rate_news = [n for n in news if n.is_rate_related]
        fed_news = [n for n in news if n.is_fed_related]
        high_impact = [n for n in news if n.impact_score >= 70]
        
        return {
            # Ana sentiment
            "comex_news_impact": overall_impact,
            "comex_impact_score": max((n.impact_score for n in news), default=0) / 100,
            
            # Kategori bazlı
            "comex_margin_sentiment": sum(n.direction_numeric for n in margin_news) / max(len(margin_news), 1),
            "comex_rate_sentiment": sum(n.direction_numeric for n in rate_news) / max(len(rate_news), 1),
            "comex_fed_sentiment": sum(n.direction_numeric for n in fed_news) / max(len(fed_news), 1),
            
            # Counts
            "comex_news_count": len(news) / 20,  # Normalized
            "comex_high_impact_count": len(high_impact) / 5,  # Normalized
            "comex_margin_news_count": len(margin_news) / 5,
            
            # Flags
            "comex_has_critical_news": 1.0 if any(n.impact_score >= 85 for n in news) else 0.0,
            "comex_has_margin_news": 1.0 if margin_news else 0.0,
            "comex_has_fed_news": 1.0 if fed_news else 0.0,
        }
    
    def _get_empty_features(self) -> Dict[str, float]:
        """Boş feature seti"""
        return {
            "comex_news_impact": 0.0,
            "comex_impact_score": 0.0,
            "comex_margin_sentiment": 0.0,
            "comex_rate_sentiment": 0.0,
            "comex_fed_sentiment": 0.0,
            "comex_news_count": 0.0,
            "comex_high_impact_count": 0.0,
            "comex_margin_news_count": 0.0,
            "comex_has_critical_news": 0.0,
            "comex_has_margin_news": 0.0,
            "comex_has_fed_news": 0.0,
        }


# =============================================================================
# GLOBAL INSTANCE & HELPER FUNCTIONS
# =============================================================================

_service_instance: Optional[COMEXNewsService] = None


def get_comex_service() -> COMEXNewsService:
    """Singleton service instance"""
    global _service_instance
    if _service_instance is None:
        _service_instance = COMEXNewsService()
    return _service_instance


async def get_comex_news_for_ml(symbol: str = "XAUUSD") -> Dict[str, float]:
    """
    ML modeli için COMEX haber feature'larını getir
    
    Returns:
        Dict with COMEX news features for ML model
    """
    if "XAU" not in symbol.upper() and "GOLD" not in symbol.upper():
        return get_comex_service()._get_empty_features()
    
    service = get_comex_service()
    impact = await service.get_comex_impact(use_ai=False)  # Fast mode
    return impact.ml_features


async def check_trading_block(symbol: str = "XAUUSD") -> Dict[str, Any]:
    """
    Kritik haber nedeniyle trading bloklanmalı mı?
    
    Returns:
        {"blocked": bool, "reason": str, "duration_minutes": int}
    """
    if "XAU" not in symbol.upper():
        return {"blocked": False, "reason": "", "duration_minutes": 0}
    
    service = get_comex_service()
    impact = await service.get_comex_impact(use_ai=True)
    
    return {
        "blocked": impact.should_block_trading,
        "reason": impact.block_reason,
        "duration_minutes": 30 if impact.should_block_trading else 0
    }
