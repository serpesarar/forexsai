"""
TWITTER/X TAKİP SİSTEMİ - GROK API
Trump ve diğer kritik hesapların tweet'lerini takip eder
xAI Grok API ile anlık analiz yapar

Takip edilen hesaplar:
- @realDonaldTrump (Trump)
- @WhiteHouse (Beyaz Saray)
- @federalreserve (Fed)
- @business (Bloomberg)
- @Reuters (Reuters)
"""

from __future__ import annotations

import asyncio
import logging
import os
import json
import hashlib
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
class TweetAlert:
    """Kritik tweet"""
    author: str
    text: str
    timestamp: datetime
    sentiment: str = "neutral"  # bullish, bearish, neutral
    impact_level: str = "medium"  # high, medium, low
    confidence: float = 0.5
    keywords_found: List[str] = field(default_factory=list)
    grok_analysis: Optional[str] = None


@dataclass
class TwitterImpact:
    """Twitter sentiment özeti"""
    sentiment_score: float  # -1 to +1
    confidence: float  # 0-100
    direction_bias: str  # BUY, SELL, NEUTRAL
    recent_tweets: List[TweetAlert]
    trump_sentiment: float
    fed_sentiment: float
    last_update: datetime


# =============================================================================
# CRITICAL ACCOUNTS TO MONITOR
# =============================================================================

CRITICAL_ACCOUNTS = {
    # Politicians & Government
    'realDonaldTrump': {'impact': 'very_high', 'category': 'trump'},
    'POTUS': {'impact': 'very_high', 'category': 'government'},
    'WhiteHouse': {'impact': 'high', 'category': 'government'},
    'USTreasury': {'impact': 'high', 'category': 'government'},
    
    # Federal Reserve
    'federalreserve': {'impact': 'very_high', 'category': 'fed'},
    'NewYorkFed': {'impact': 'high', 'category': 'fed'},
    
    # Financial News
    'business': {'impact': 'medium', 'category': 'news'},  # Bloomberg
    'Reuters': {'impact': 'medium', 'category': 'news'},
    'ABORAT': {'impact': 'medium', 'category': 'news'},  # Bloomberg Economics
    'markets': {'impact': 'medium', 'category': 'news'},
    'FT': {'impact': 'medium', 'category': 'news'},  # Financial Times
    'WSJ': {'impact': 'medium', 'category': 'news'},
    'CNBC': {'impact': 'medium', 'category': 'news'},
    
    # Market Analysts
    'zaborohes': {'impact': 'low', 'category': 'analyst'},
    'NorthmanTrader': {'impact': 'low', 'category': 'analyst'},
}

# Keywords for gold trading
GOLD_TWEET_KEYWORDS = {
    # Trump specific
    'tariff': 0.3,
    'tariffs': 0.3,
    'china': 0.2,
    'trade': 0.15,
    'trade war': 0.35,
    'trade deal': -0.2,
    'sanctions': 0.25,
    'executive order': 0.15,
    
    # Fed specific
    'rate cut': 0.3,
    'rate hike': -0.3,
    'interest rate': 0.1,
    'inflation': 0.2,
    'monetary policy': 0.1,
    'quantitative': 0.15,
    'tightening': -0.2,
    'easing': 0.2,
    
    # Market keywords
    'gold': 0.1,
    'dollar': 0.0,
    'treasury': 0.1,
    'bond': 0.05,
    'recession': 0.25,
    'crisis': 0.3,
    'market crash': 0.35,
    'uncertainty': 0.2,
    
    # Geopolitical
    'war': 0.3,
    'military': 0.2,
    'nuclear': 0.35,
    'attack': 0.25,
    'conflict': 0.25,
    'peace': -0.15,
    'deal': -0.1,
}


# =============================================================================
# GROK API CLIENT
# =============================================================================

class GrokAPIClient:
    """
    xAI Grok API Client
    
    Grok API:
    - Real-time X/Twitter access
    - Powerful analysis capabilities
    - Fast inference
    
    API Key: https://console.x.ai/
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("XAI_API_KEY") or os.environ.get("GROK_API_KEY")
        self.base_url = "https://api.x.ai/v1"
        
    async def analyze_tweet(self, tweet_text: str, author: str) -> Dict[str, Any]:
        """
        Grok ile tweet analizi yap
        
        Returns:
            {
                'sentiment': 'bullish' | 'bearish' | 'neutral',
                'impact': 'high' | 'medium' | 'low',
                'gold_impact': float (-1 to 1),
                'nasdaq_impact': float (-1 to 1),
                'analysis': str
            }
        """
        if not self.api_key:
            logger.warning("Grok API key not set, using keyword-based analysis")
            return self._keyword_based_analysis(tweet_text, author)
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                prompt = f"""Analyze this tweet for financial market impact:

Author: @{author}
Tweet: {tweet_text}

Provide analysis in JSON format:
{{
    "sentiment": "bullish" or "bearish" or "neutral",
    "impact_level": "high" or "medium" or "low",
    "gold_impact": number from -1 (bearish) to 1 (bullish),
    "nasdaq_impact": number from -1 to 1,
    "key_points": ["point1", "point2"],
    "confidence": number from 0 to 100
}}

Consider: Trump tweets affect gold through uncertainty/tariffs. Fed tweets affect through rate expectations.
Only respond with valid JSON."""

                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "grok-beta",
                        "messages": [
                            {"role": "system", "content": "You are a financial analyst. Respond only with valid JSON."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.3
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = result['choices'][0]['message']['content']
                    
                    # Parse JSON
                    try:
                        analysis = json.loads(content)
                        return analysis
                    except json.JSONDecodeError:
                        logger.warning("Failed to parse Grok response, using keyword analysis")
                        return self._keyword_based_analysis(tweet_text, author)
                else:
                    logger.error(f"Grok API error: {response.status_code}")
                    return self._keyword_based_analysis(tweet_text, author)
                    
        except Exception as e:
            logger.error(f"Grok API exception: {e}")
            return self._keyword_based_analysis(tweet_text, author)
    
    def _keyword_based_analysis(self, tweet_text: str, author: str) -> Dict[str, Any]:
        """Fallback keyword-based analysis"""
        text_lower = tweet_text.lower()
        
        # Calculate sentiment score
        sentiment_score = 0.0
        keywords_found = []
        
        for keyword, impact in GOLD_TWEET_KEYWORDS.items():
            if keyword in text_lower:
                sentiment_score += impact
                keywords_found.append(keyword)
        
        # Author weight
        author_config = CRITICAL_ACCOUNTS.get(author, {})
        impact_multiplier = {
            'very_high': 2.0,
            'high': 1.5,
            'medium': 1.0,
            'low': 0.5
        }.get(author_config.get('impact', 'medium'), 1.0)
        
        sentiment_score *= impact_multiplier
        
        # Clamp
        sentiment_score = max(-1.0, min(1.0, sentiment_score))
        
        # Determine sentiment
        if sentiment_score > 0.15:
            sentiment = "bullish"
        elif sentiment_score < -0.15:
            sentiment = "bearish"
        else:
            sentiment = "neutral"
        
        # Impact level
        if abs(sentiment_score) > 0.4 or author_config.get('impact') == 'very_high':
            impact_level = "high"
        elif abs(sentiment_score) > 0.2:
            impact_level = "medium"
        else:
            impact_level = "low"
        
        return {
            'sentiment': sentiment,
            'impact_level': impact_level,
            'gold_impact': sentiment_score,
            'nasdaq_impact': sentiment_score * 0.5,  # Gold ve NASDAQ farklı etkilenir
            'key_points': keywords_found[:5],
            'confidence': min(90, 40 + len(keywords_found) * 10)
        }


# =============================================================================
# TWITTER MONITOR (Simulated - Real implementation needs X API access)
# =============================================================================

class TwitterMonitor:
    """
    Twitter/X takip sistemi
    
    NOT: Gerçek Twitter API erişimi için X Developer Account gerekli.
    Bu sınıf hem gerçek API hem de simülasyon modunu destekler.
    
    Gerçek API için:
    1. https://developer.twitter.com/ - Developer account
    2. https://console.x.ai/ - Grok API key
    """
    
    def __init__(self, grok_api_key: Optional[str] = None, x_bearer_token: Optional[str] = None):
        self.grok = GrokAPIClient(grok_api_key)
        self.x_bearer_token = x_bearer_token or os.environ.get("X_BEARER_TOKEN")
        self.alerts: List[TweetAlert] = []
        self.is_running = False
        self._seen_tweet_ids: set = set()
        
    async def _fetch_recent_tweets(self, username: str, count: int = 10) -> List[Dict]:
        """
        Kullanıcının son tweet'lerini çek
        
        Gerçek implementation için X API v2 gerekli
        """
        if not self.x_bearer_token:
            # Simülasyon modu - gerçek API yoksa
            return []
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                # X API v2 - User tweets timeline
                # https://developer.twitter.com/en/docs/twitter-api/tweets/timelines/api-reference/get-users-id-tweets
                
                # Önce user ID al
                user_response = await client.get(
                    f"https://api.twitter.com/2/users/by/username/{username}",
                    headers={"Authorization": f"Bearer {self.x_bearer_token}"}
                )
                
                if user_response.status_code != 200:
                    return []
                
                user_id = user_response.json().get('data', {}).get('id')
                if not user_id:
                    return []
                
                # Tweet'leri çek
                tweets_response = await client.get(
                    f"https://api.twitter.com/2/users/{user_id}/tweets",
                    headers={"Authorization": f"Bearer {self.x_bearer_token}"},
                    params={
                        "max_results": count,
                        "tweet.fields": "created_at,text,public_metrics"
                    }
                )
                
                if tweets_response.status_code == 200:
                    return tweets_response.json().get('data', [])
                    
                return []
                
        except Exception as e:
            logger.error(f"Twitter API error for {username}: {e}")
            return []
    
    async def check_account(self, username: str) -> List[TweetAlert]:
        """Bir hesabın son tweet'lerini kontrol et"""
        tweets = await self._fetch_recent_tweets(username, count=5)
        new_alerts = []
        
        for tweet in tweets:
            tweet_id = tweet.get('id')
            
            # Daha önce gördüysek atla
            if tweet_id in self._seen_tweet_ids:
                continue
            
            self._seen_tweet_ids.add(tweet_id)
            
            # Son 1000 tweet ID'yi tut
            if len(self._seen_tweet_ids) > 1000:
                self._seen_tweet_ids = set(list(self._seen_tweet_ids)[-500:])
            
            text = tweet.get('text', '')
            
            # Grok ile analiz
            analysis = await self.grok.analyze_tweet(text, username)
            
            # Alert oluştur
            alert = TweetAlert(
                author=username,
                text=text,
                timestamp=datetime.utcnow(),
                sentiment=analysis.get('sentiment', 'neutral'),
                impact_level=analysis.get('impact_level', 'medium'),
                confidence=analysis.get('confidence', 50) / 100,
                keywords_found=analysis.get('key_points', []),
                grok_analysis=json.dumps(analysis)
            )
            
            # Sadece önemli alert'leri kaydet
            if alert.impact_level != 'low' or alert.sentiment != 'neutral':
                new_alerts.append(alert)
                self.alerts.append(alert)
                
                logger.info(f"🐦 Tweet Alert: @{username} - {alert.sentiment} ({alert.impact_level})")
        
        # Son 100 alert'i tut
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]
        
        return new_alerts
    
    async def monitor_loop(self, interval_seconds: int = 60):
        """
        Sürekli monitoring döngüsü
        
        Args:
            interval_seconds: Kontrol aralığı (saniye)
        """
        self.is_running = True
        
        while self.is_running:
            for username in CRITICAL_ACCOUNTS.keys():
                if not self.is_running:
                    break
                    
                try:
                    await self.check_account(username)
                except Exception as e:
                    logger.error(f"Error checking @{username}: {e}")
                
                # Rate limiting
                await asyncio.sleep(2)
            
            # Ana bekleme
            await asyncio.sleep(interval_seconds)
    
    def stop(self):
        """Monitoring'i durdur"""
        self.is_running = False
    
    def get_recent_alerts(self, minutes: int = 60) -> List[TweetAlert]:
        """Son X dakikadaki alert'leri getir"""
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        return [a for a in self.alerts if a.timestamp > cutoff]
    
    def get_impact_summary(self) -> TwitterImpact:
        """Twitter sentiment özeti"""
        recent = self.get_recent_alerts(60)
        
        if not recent:
            return TwitterImpact(
                sentiment_score=0.0,
                confidence=20.0,
                direction_bias="NEUTRAL",
                recent_tweets=[],
                trump_sentiment=0.0,
                fed_sentiment=0.0,
                last_update=datetime.utcnow()
            )
        
        # Kategori bazlı sentiment
        trump_scores = []
        fed_scores = []
        all_scores = []
        
        for alert in recent:
            score = {
                'bullish': 0.3,
                'bearish': -0.3,
                'neutral': 0.0
            }.get(alert.sentiment, 0.0) * alert.confidence
            
            all_scores.append(score)
            
            author_config = CRITICAL_ACCOUNTS.get(alert.author, {})
            category = author_config.get('category', '')
            
            if category == 'trump' or alert.author == 'realDonaldTrump':
                trump_scores.append(score)
            elif category == 'fed':
                fed_scores.append(score)
        
        # Ortalamalar
        avg_sentiment = sum(all_scores) / len(all_scores) if all_scores else 0.0
        trump_sentiment = sum(trump_scores) / len(trump_scores) if trump_scores else 0.0
        fed_sentiment = sum(fed_scores) / len(fed_scores) if fed_scores else 0.0
        
        # Direction
        if avg_sentiment > 0.1:
            direction = "BUY"
        elif avg_sentiment < -0.1:
            direction = "SELL"
        else:
            direction = "NEUTRAL"
        
        # Confidence
        high_impact = len([a for a in recent if a.impact_level == 'high'])
        confidence = min(90, 30 + len(recent) * 5 + high_impact * 15)
        
        return TwitterImpact(
            sentiment_score=avg_sentiment,
            confidence=confidence,
            direction_bias=direction,
            recent_tweets=recent[-10:],
            trump_sentiment=trump_sentiment,
            fed_sentiment=fed_sentiment,
            last_update=datetime.utcnow()
        )


# =============================================================================
# GLOBAL INSTANCE & HELPER FUNCTIONS
# =============================================================================

_twitter_monitor: Optional[TwitterMonitor] = None


def get_twitter_monitor() -> TwitterMonitor:
    """Singleton Twitter monitor instance"""
    global _twitter_monitor
    if _twitter_monitor is None:
        grok_key = os.environ.get("XAI_API_KEY") or os.environ.get("GROK_API_KEY")
        x_token = os.environ.get("X_BEARER_TOKEN")
        _twitter_monitor = TwitterMonitor(grok_key, x_token)
    return _twitter_monitor


async def get_twitter_impact() -> TwitterImpact:
    """ML modeli için Twitter etkisini getir"""
    monitor = get_twitter_monitor()
    return monitor.get_impact_summary()


async def analyze_tweet_for_gold(tweet_text: str, author: str = "unknown") -> Dict[str, Any]:
    """Tek bir tweet'i gold trading için analiz et"""
    monitor = get_twitter_monitor()
    return await monitor.grok.analyze_tweet(tweet_text, author)


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    async def test():
        # Test keyword analysis
        monitor = TwitterMonitor()
        
        test_tweets = [
            ("I am imposing 25% TARIFFS on all imports from China starting next week!", "realDonaldTrump"),
            ("The Federal Reserve will cut interest rates by 50 basis points.", "federalreserve"),
            ("Gold prices surge as uncertainty increases in global markets.", "Reuters"),
            ("Great meeting with President Xi. Trade deal is very close!", "realDonaldTrump"),
        ]
        
        print("Testing tweet analysis...\n")
        
        for tweet, author in test_tweets:
            result = await monitor.grok.analyze_tweet(tweet, author)
            print(f"Author: @{author}")
            print(f"Tweet: {tweet[:80]}...")
            print(f"Analysis: {json.dumps(result, indent=2)}")
            print("-" * 60)
    
    asyncio.run(test())
