"""
UNIFIED NEWS ANALYZER
Tüm haber kaynaklarını birleştirir ve ML modeline sentiment sağlar

Kaynaklar:
1. EODHD News API - Yazılı haberler
2. Live TV Transcription - CNN/Fox/CNBC canlı yayın
3. Twitter/X Monitor - Trump ve Fed tweet'leri

Çıktı: Birleştirilmiş sentiment skoru ve ML modeli için feature'lar
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import httpx

from config import settings

logger = logging.getLogger(__name__)


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class UnifiedNewsImpact:
    """Birleştirilmiş haber etkisi - ML modeli için"""
    
    # Ana metrikler
    sentiment_score: float  # -1 (bearish) to +1 (bullish for gold)
    confidence: float  # 0-100
    direction_bias: str  # BUY, SELL, NEUTRAL
    
    # Kaynak bazlı sentiment
    eodhd_sentiment: float
    live_tv_sentiment: float
    twitter_sentiment: float
    trump_sentiment: float
    fed_sentiment: float
    
    # Ağırlıklar ve katkılar
    source_weights: Dict[str, float]
    source_contributions: Dict[str, float]
    
    # Detaylar
    key_factors: List[str]
    high_impact_events: List[Dict]
    conflicts: List[str]
    
    # Meta
    last_update: datetime
    data_freshness: Dict[str, int]  # Her kaynak için dakika cinsinden yaş
    
    # ML Feature'ları
    ml_features: Dict[str, float]


@dataclass 
class NewsSourceStatus:
    """Haber kaynağı durumu"""
    name: str
    is_active: bool
    last_data: Optional[datetime]
    data_count: int
    error: Optional[str] = None


# =============================================================================
# SOURCE WEIGHTS - Kaynak güvenilirlik ağırlıkları
# =============================================================================

SOURCE_WEIGHTS = {
    'eodhd': 0.25,      # Yazılı haberler - güvenilir ama gecikmeli
    'live_tv': 0.35,    # Canlı yayın - en hızlı
    'twitter': 0.25,    # Twitter - hızlı ama gürültülü
    'trump': 0.15,      # Trump özel - çok etkili ama volatil
}

# Impact multipliers by event type
EVENT_MULTIPLIERS = {
    'trump_tariff': 2.0,
    'fed_rate': 2.0,
    'trump_tweet': 1.8,
    'fomc': 1.7,
    'inflation_data': 1.5,
    'jobs_report': 1.4,
    'geopolitical': 1.6,
    'market_crash': 2.0,
    'default': 1.0,
}


# =============================================================================
# UNIFIED NEWS ANALYZER
# =============================================================================

class UnifiedNewsAnalyzer:
    """
    Tüm haber kaynaklarını birleştiren ana sınıf
    
    Kullanım:
        analyzer = UnifiedNewsAnalyzer()
        impact = await analyzer.get_unified_impact("XAUUSD")
    """
    
    def __init__(self):
        self._last_eodhd_data: List[Dict] = []
        self._last_eodhd_fetch: Optional[datetime] = None
        self._cache_duration = timedelta(minutes=5)
        
    async def _fetch_eodhd_news(self, symbol: str = "GOLD") -> List[Dict]:
        """EODHD News API'den haber çek"""
        
        # Cache kontrolü
        if (self._last_eodhd_fetch and 
            datetime.utcnow() - self._last_eodhd_fetch < self._cache_duration and
            self._last_eodhd_data):
            return self._last_eodhd_data
        
        if not settings.eodhd_api_key:
            return []
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                # Gold için en iyi semboller
                symbols = "GOLD,GC.CMX,DXY.INDX,SPY.US"
                
                response = await client.get(
                    "https://eodhistoricaldata.com/api/news",
                    params={
                        "api_token": settings.eodhd_api_key,
                        "s": symbols,
                        "limit": 30,
                        "fmt": "json"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list):
                        self._last_eodhd_data = data
                        self._last_eodhd_fetch = datetime.utcnow()
                        return data
                        
                return []
                
        except Exception as e:
            logger.error(f"EODHD news fetch error: {e}")
            return []
    
    def _analyze_eodhd_sentiment(self, news: List[Dict]) -> Dict[str, Any]:
        """EODHD haberlerinin sentiment analizi"""
        
        if not news:
            return {
                'sentiment': 0.0,
                'confidence': 20.0,
                'key_factors': [],
                'high_impact': []
            }
        
        total_sentiment = 0.0
        count = 0
        key_factors = []
        high_impact = []
        
        # Gold için kritik kelimeler
        bullish_keywords = [
            'gold surge', 'gold rally', 'safe haven', 'inflation rise',
            'rate cut', 'dollar weak', 'uncertainty', 'crisis', 'war',
            'tariff', 'trade war', 'sanctions', 'recession'
        ]
        
        bearish_keywords = [
            'gold fall', 'gold drop', 'risk on', 'dollar strong',
            'rate hike', 'inflation cool', 'deal', 'peace', 'growth'
        ]
        
        for article in news[:20]:  # Son 20 haber
            title = (article.get('title') or '').lower()
            
            # EODHD'nin kendi sentiment'i varsa kullan
            eodhd_sentiment = article.get('sentiment', {})
            if isinstance(eodhd_sentiment, dict):
                polarity = eodhd_sentiment.get('polarity', 0)
                # EODHD polarity'yi gold sentiment'e çevir
                # Pozitif market haberi gold için karışık olabilir
                article_sentiment = polarity * 0.3
            else:
                article_sentiment = 0.0
            
            # Keyword analizi
            for keyword in bullish_keywords:
                if keyword in title:
                    article_sentiment += 0.15
                    if article_sentiment > 0.3:
                        key_factors.append(f"📰 {title[:60]}...")
                        
            for keyword in bearish_keywords:
                if keyword in title:
                    article_sentiment -= 0.15
            
            # Trump/Fed haberleri yüksek etki
            if 'trump' in title or 'tariff' in title:
                article_sentiment *= 1.5
                high_impact.append({
                    'title': title[:80],
                    'source': 'eodhd',
                    'sentiment': 'bullish' if article_sentiment > 0 else 'bearish'
                })
            
            if 'fed' in title or 'rate' in title:
                high_impact.append({
                    'title': title[:80],
                    'source': 'eodhd',
                    'sentiment': 'bullish' if article_sentiment > 0 else 'bearish'
                })
            
            total_sentiment += max(-1, min(1, article_sentiment))
            count += 1
        
        avg_sentiment = total_sentiment / max(count, 1)
        confidence = min(80, 30 + count * 2 + len(high_impact) * 10)
        
        return {
            'sentiment': avg_sentiment,
            'confidence': confidence,
            'key_factors': key_factors[:5],
            'high_impact': high_impact[:5]
        }
    
    async def _get_live_tv_sentiment(self) -> Dict[str, Any]:
        """Canlı TV transkript sentiment'i"""
        try:
            from services.live_news_monitor import get_live_news_impact
            impact = await get_live_news_impact()
            
            return {
                'sentiment': impact.sentiment_score,
                'confidence': impact.confidence,
                'key_factors': [f"📺 {a.keyword}: {a.sentiment}" for a in impact.alerts[-3:]],
                'is_active': len(impact.channels_active) > 0
            }
        except Exception as e:
            logger.debug(f"Live TV not available: {e}")
            return {
                'sentiment': 0.0,
                'confidence': 0.0,
                'key_factors': [],
                'is_active': False
            }
    
    async def _get_twitter_sentiment(self) -> Dict[str, Any]:
        """Twitter/X sentiment'i"""
        try:
            from services.twitter_monitor import get_twitter_impact
            impact = await get_twitter_impact()
            
            return {
                'sentiment': impact.sentiment_score,
                'confidence': impact.confidence,
                'trump_sentiment': impact.trump_sentiment,
                'fed_sentiment': impact.fed_sentiment,
                'key_factors': [f"🐦 @{t.author}: {t.sentiment}" for t in impact.recent_tweets[-3:]],
                'is_active': len(impact.recent_tweets) > 0
            }
        except Exception as e:
            logger.debug(f"Twitter monitor not available: {e}")
            return {
                'sentiment': 0.0,
                'confidence': 0.0,
                'trump_sentiment': 0.0,
                'fed_sentiment': 0.0,
                'key_factors': [],
                'is_active': False
            }
    
    def _detect_conflicts(self, sentiments: Dict[str, float]) -> List[str]:
        """Çakışan sinyalleri tespit et"""
        conflicts = []
        
        # EODHD vs Live TV
        if abs(sentiments.get('eodhd', 0) - sentiments.get('live_tv', 0)) > 0.4:
            conflicts.append("⚠️ Written news vs Live TV conflict")
        
        # Trump vs Fed
        if abs(sentiments.get('trump', 0) - sentiments.get('fed', 0)) > 0.4:
            conflicts.append("⚠️ Trump vs Fed sentiment conflict")
        
        return conflicts
    
    def _calculate_ml_features(self, 
                               eodhd: Dict, 
                               live_tv: Dict, 
                               twitter: Dict) -> Dict[str, float]:
        """ML modeli için feature'lar hesapla"""
        
        return {
            # Ana sentiment
            'news_sentiment_combined': (
                eodhd['sentiment'] * 0.3 +
                live_tv['sentiment'] * 0.35 +
                twitter['sentiment'] * 0.35
            ),
            
            # Kaynak bazlı
            'news_sentiment_eodhd': eodhd['sentiment'],
            'news_sentiment_live': live_tv['sentiment'],
            'news_sentiment_twitter': twitter['sentiment'],
            'news_sentiment_trump': twitter.get('trump_sentiment', 0.0),
            'news_sentiment_fed': twitter.get('fed_sentiment', 0.0),
            
            # Confidence
            'news_confidence_avg': (
                eodhd['confidence'] + 
                live_tv['confidence'] + 
                twitter['confidence']
            ) / 3,
            
            # Activity flags
            'news_live_tv_active': 1.0 if live_tv.get('is_active') else 0.0,
            'news_twitter_active': 1.0 if twitter.get('is_active') else 0.0,
            
            # Volatility indicator (sentiment spread)
            'news_sentiment_spread': abs(
                max(eodhd['sentiment'], live_tv['sentiment'], twitter['sentiment']) -
                min(eodhd['sentiment'], live_tv['sentiment'], twitter['sentiment'])
            ),
        }
    
    async def get_unified_impact(self, symbol: str = "XAUUSD") -> UnifiedNewsImpact:
        """
        Tüm kaynaklardan birleştirilmiş haber etkisi
        
        Args:
            symbol: Trading sembolü (XAUUSD veya NASDAQ)
            
        Returns:
            UnifiedNewsImpact object with all metrics
        """
        
        # Paralel olarak tüm kaynakları çek
        eodhd_news, live_tv_result, twitter_result = await asyncio.gather(
            self._fetch_eodhd_news("GOLD" if "XAU" in symbol else "SPY"),
            self._get_live_tv_sentiment(),
            self._get_twitter_sentiment(),
            return_exceptions=True
        )
        
        # Hata kontrolü
        if isinstance(eodhd_news, Exception):
            logger.error(f"EODHD error: {eodhd_news}")
            eodhd_news = []
        if isinstance(live_tv_result, Exception):
            logger.error(f"Live TV error: {live_tv_result}")
            live_tv_result = {'sentiment': 0, 'confidence': 0, 'key_factors': [], 'is_active': False}
        if isinstance(twitter_result, Exception):
            logger.error(f"Twitter error: {twitter_result}")
            twitter_result = {'sentiment': 0, 'confidence': 0, 'trump_sentiment': 0, 'fed_sentiment': 0, 'key_factors': [], 'is_active': False}
        
        # EODHD analizi
        eodhd_analysis = self._analyze_eodhd_sentiment(eodhd_news)
        
        # Sentiment'leri topla
        sentiments = {
            'eodhd': eodhd_analysis['sentiment'],
            'live_tv': live_tv_result['sentiment'],
            'twitter': twitter_result['sentiment'],
            'trump': twitter_result.get('trump_sentiment', 0.0),
            'fed': twitter_result.get('fed_sentiment', 0.0),
        }
        
        # Ağırlıklı birleştirme
        weights = SOURCE_WEIGHTS.copy()
        
        # Aktif olmayan kaynakların ağırlığını azalt
        if not live_tv_result.get('is_active'):
            weights['live_tv'] = 0.1
        if not twitter_result.get('is_active'):
            weights['twitter'] = 0.1
            weights['trump'] = 0.05
        
        # Normalize weights
        total_weight = sum(weights.values())
        weights = {k: v / total_weight for k, v in weights.items()}
        
        # Birleşik sentiment
        combined_sentiment = (
            sentiments['eodhd'] * weights['eodhd'] +
            sentiments['live_tv'] * weights['live_tv'] +
            sentiments['twitter'] * weights['twitter'] +
            sentiments['trump'] * weights['trump']
        )
        
        # Contribution
        contributions = {
            'eodhd': sentiments['eodhd'] * weights['eodhd'],
            'live_tv': sentiments['live_tv'] * weights['live_tv'],
            'twitter': sentiments['twitter'] * weights['twitter'],
            'trump': sentiments['trump'] * weights['trump'],
        }
        
        # Conflicts
        conflicts = self._detect_conflicts(sentiments)
        
        # Confidence
        base_confidence = (
            eodhd_analysis['confidence'] * 0.3 +
            live_tv_result['confidence'] * 0.35 +
            twitter_result['confidence'] * 0.35
        )
        
        # Conflict penalty
        confidence = max(20, base_confidence - len(conflicts) * 10)
        
        # Direction bias
        if combined_sentiment > 0.1:
            direction = "BUY"
        elif combined_sentiment < -0.1:
            direction = "SELL"
        else:
            direction = "NEUTRAL"
        
        # Key factors birleştir
        key_factors = []
        key_factors.extend(eodhd_analysis.get('key_factors', [])[:2])
        key_factors.extend(live_tv_result.get('key_factors', [])[:2])
        key_factors.extend(twitter_result.get('key_factors', [])[:2])
        
        # High impact events
        high_impact = eodhd_analysis.get('high_impact', [])
        
        # ML features
        ml_features = self._calculate_ml_features(
            eodhd_analysis, live_tv_result, twitter_result
        )
        
        # Data freshness
        now = datetime.utcnow()
        freshness = {
            'eodhd': int((now - self._last_eodhd_fetch).total_seconds() / 60) if self._last_eodhd_fetch else 999,
            'live_tv': 0 if live_tv_result.get('is_active') else 999,
            'twitter': 0 if twitter_result.get('is_active') else 999,
        }
        
        return UnifiedNewsImpact(
            sentiment_score=combined_sentiment,
            confidence=confidence,
            direction_bias=direction,
            eodhd_sentiment=sentiments['eodhd'],
            live_tv_sentiment=sentiments['live_tv'],
            twitter_sentiment=sentiments['twitter'],
            trump_sentiment=sentiments['trump'],
            fed_sentiment=sentiments['fed'],
            source_weights=weights,
            source_contributions=contributions,
            key_factors=key_factors,
            high_impact_events=high_impact,
            conflicts=conflicts,
            last_update=now,
            data_freshness=freshness,
            ml_features=ml_features
        )
    
    async def get_source_status(self) -> List[NewsSourceStatus]:
        """Tüm haber kaynaklarının durumu"""
        statuses = []
        
        # EODHD
        try:
            news = await self._fetch_eodhd_news()
            statuses.append(NewsSourceStatus(
                name="EODHD News",
                is_active=len(news) > 0,
                last_data=self._last_eodhd_fetch,
                data_count=len(news)
            ))
        except Exception as e:
            statuses.append(NewsSourceStatus(
                name="EODHD News",
                is_active=False,
                last_data=None,
                data_count=0,
                error=str(e)
            ))
        
        # Live TV
        try:
            from services.live_news_monitor import get_live_monitor
            monitor = get_live_monitor()
            statuses.append(NewsSourceStatus(
                name="Live TV",
                is_active=monitor.is_running,
                last_data=datetime.utcnow() if monitor.is_running else None,
                data_count=len(monitor.alerts)
            ))
        except:
            statuses.append(NewsSourceStatus(
                name="Live TV",
                is_active=False,
                last_data=None,
                data_count=0,
                error="Not initialized"
            ))
        
        # Twitter
        try:
            from services.twitter_monitor import get_twitter_monitor
            monitor = get_twitter_monitor()
            statuses.append(NewsSourceStatus(
                name="Twitter/X",
                is_active=monitor.is_running,
                last_data=datetime.utcnow() if monitor.is_running else None,
                data_count=len(monitor.alerts)
            ))
        except:
            statuses.append(NewsSourceStatus(
                name="Twitter/X",
                is_active=False,
                last_data=None,
                data_count=0,
                error="Not initialized"
            ))
        
        return statuses


# =============================================================================
# GLOBAL INSTANCE & HELPER FUNCTIONS
# =============================================================================

_analyzer_instance: Optional[UnifiedNewsAnalyzer] = None


def get_unified_analyzer() -> UnifiedNewsAnalyzer:
    """Singleton analyzer instance"""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = UnifiedNewsAnalyzer()
    return _analyzer_instance


async def get_news_sentiment_for_ml(symbol: str = "XAUUSD") -> Dict[str, float]:
    """
    ML modeli için haber sentiment feature'larını getir
    
    Returns:
        Dict with sentiment features for ML model
    """
    analyzer = get_unified_analyzer()
    impact = await analyzer.get_unified_impact(symbol)
    return impact.ml_features


async def get_news_direction_bias(symbol: str = "XAUUSD") -> tuple[str, float, float]:
    """
    Haber bazlı yön önerisi
    
    Returns:
        (direction, sentiment_score, confidence)
    """
    analyzer = get_unified_analyzer()
    impact = await analyzer.get_unified_impact(symbol)
    return impact.direction_bias, impact.sentiment_score, impact.confidence


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    async def test():
        print("Testing Unified News Analyzer...\n")
        
        analyzer = UnifiedNewsAnalyzer()
        
        # Get unified impact
        impact = await analyzer.get_unified_impact("XAUUSD")
        
        print("=" * 60)
        print("UNIFIED NEWS IMPACT")
        print("=" * 60)
        print(f"Sentiment Score: {impact.sentiment_score:.3f}")
        print(f"Confidence: {impact.confidence:.1f}%")
        print(f"Direction Bias: {impact.direction_bias}")
        print()
        print("Source Sentiments:")
        print(f"  EODHD:   {impact.eodhd_sentiment:.3f}")
        print(f"  Live TV: {impact.live_tv_sentiment:.3f}")
        print(f"  Twitter: {impact.twitter_sentiment:.3f}")
        print(f"  Trump:   {impact.trump_sentiment:.3f}")
        print(f"  Fed:     {impact.fed_sentiment:.3f}")
        print()
        print("Key Factors:")
        for factor in impact.key_factors:
            print(f"  • {factor}")
        print()
        if impact.conflicts:
            print("Conflicts:")
            for conflict in impact.conflicts:
                print(f"  {conflict}")
        print()
        print("ML Features:")
        for k, v in impact.ml_features.items():
            print(f"  {k}: {v:.3f}")
        print("=" * 60)
        
        # Source status
        print("\nSource Status:")
        statuses = await analyzer.get_source_status()
        for status in statuses:
            icon = "✅" if status.is_active else "❌"
            print(f"  {icon} {status.name}: {status.data_count} items")
    
    asyncio.run(test())
