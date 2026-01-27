"""
Live News & Twitter Monitoring API Endpoints
Groq Whisper + Grok API entegrasyonu
"""

from fastapi import APIRouter, Query, BackgroundTasks
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import asyncio
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/live-news", tags=["Live News"])


# =============================================================================
# RESPONSE MODELS
# =============================================================================

class TweetAnalysisRequest(BaseModel):
    text: str
    author: str = "unknown"


class TweetAnalysisResponse(BaseModel):
    sentiment: str
    impact_level: str
    gold_impact: float
    nasdaq_impact: float
    key_points: List[str]
    confidence: float


class TwitterImpactResponse(BaseModel):
    sentiment_score: float
    confidence: float
    direction_bias: str
    trump_sentiment: float
    fed_sentiment: float
    recent_tweets_count: int
    last_update: str


class LiveNewsImpactResponse(BaseModel):
    sentiment_score: float
    confidence: float
    direction_bias: str
    alerts_count: int
    channels_active: List[str]
    last_update: str


class SystemStatusResponse(BaseModel):
    twitter_configured: bool
    groq_configured: bool
    xai_configured: bool
    twitter_monitor_running: bool
    live_news_monitor_running: bool
    recent_twitter_alerts: int
    recent_news_alerts: int


# =============================================================================
# TWITTER ENDPOINTS
# =============================================================================

@router.post("/analyze-tweet", response_model=TweetAnalysisResponse)
async def analyze_tweet(request: TweetAnalysisRequest):
    """
    Tek bir tweet'i Grok API ile analiz et.
    Gold ve NASDAQ için sentiment ve impact döndürür.
    """
    from services.twitter_monitor import analyze_tweet_for_gold
    
    result = await analyze_tweet_for_gold(request.text, request.author)
    
    return TweetAnalysisResponse(
        sentiment=result.get("sentiment", "neutral"),
        impact_level=result.get("impact_level", "medium"),
        gold_impact=result.get("gold_impact", 0.0),
        nasdaq_impact=result.get("nasdaq_impact", 0.0),
        key_points=result.get("key_points", []),
        confidence=result.get("confidence", 50)
    )


@router.get("/twitter-impact", response_model=TwitterImpactResponse)
async def get_twitter_impact():
    """
    Twitter/X sentiment özetini getir.
    Trump, Fed ve diğer kritik hesapların etkisini gösterir.
    """
    from services.twitter_monitor import get_twitter_impact as _get_impact
    
    impact = await _get_impact()
    
    return TwitterImpactResponse(
        sentiment_score=impact.sentiment_score,
        confidence=impact.confidence,
        direction_bias=impact.direction_bias,
        trump_sentiment=impact.trump_sentiment,
        fed_sentiment=impact.fed_sentiment,
        recent_tweets_count=len(impact.recent_tweets),
        last_update=impact.last_update.isoformat()
    )


@router.get("/twitter-alerts")
async def get_twitter_alerts(minutes: int = Query(60, ge=1, le=1440)):
    """Son X dakikadaki Twitter alert'lerini getir."""
    from services.twitter_monitor import get_twitter_monitor
    
    monitor = get_twitter_monitor()
    alerts = monitor.get_recent_alerts(minutes)
    
    return {
        "count": len(alerts),
        "alerts": [
            {
                "author": a.author,
                "text": a.text[:200],
                "sentiment": a.sentiment,
                "impact_level": a.impact_level,
                "confidence": a.confidence,
                "keywords": a.keywords_found,
                "timestamp": a.timestamp.isoformat()
            }
            for a in alerts
        ]
    }


@router.post("/twitter-check-account")
async def check_twitter_account(username: str = Query(..., description="Twitter username without @")):
    """
    Belirli bir hesabın son tweet'lerini kontrol et ve analiz et.
    """
    from services.twitter_monitor import get_twitter_monitor
    
    monitor = get_twitter_monitor()
    alerts = await monitor.check_account(username)
    
    return {
        "username": username,
        "new_alerts": len(alerts),
        "alerts": [
            {
                "text": a.text[:200],
                "sentiment": a.sentiment,
                "impact_level": a.impact_level,
                "confidence": a.confidence,
                "keywords": a.keywords_found
            }
            for a in alerts
        ]
    }


# =============================================================================
# LIVE NEWS ENDPOINTS
# =============================================================================

@router.get("/live-impact", response_model=LiveNewsImpactResponse)
async def get_live_news_impact():
    """
    Canlı haber sentiment özetini getir.
    CNN, Fox, CNBC gibi kaynaklardan gelen haberlerin etkisi.
    """
    from services.live_news_monitor import get_live_news_impact as _get_impact
    
    impact = await _get_impact()
    
    return LiveNewsImpactResponse(
        sentiment_score=impact.sentiment_score,
        confidence=impact.confidence,
        direction_bias=impact.direction_bias,
        alerts_count=len(impact.alerts),
        channels_active=impact.channels_active,
        last_update=impact.last_update.isoformat()
    )


@router.get("/live-alerts")
async def get_live_news_alerts(minutes: int = Query(60, ge=1, le=1440)):
    """Son X dakikadaki canlı haber alert'lerini getir."""
    from services.live_news_monitor import get_live_monitor
    
    monitor = get_live_monitor()
    alerts = monitor.get_recent_alerts(minutes)
    
    return {
        "count": len(alerts),
        "alerts": [
            {
                "keyword": a.keyword,
                "channel": a.channel,
                "sentiment": a.sentiment,
                "impact_level": a.impact_level,
                "confidence": a.confidence,
                "text": a.full_text[:200],
                "timestamp": a.timestamp.isoformat()
            }
            for a in alerts
        ]
    }


# =============================================================================
# SYSTEM STATUS & CONTROL
# =============================================================================

@router.get("/status", response_model=SystemStatusResponse)
async def get_system_status():
    """
    Canlı haber ve Twitter sistemlerinin durumunu kontrol et.
    API key'lerin set edilip edilmediğini ve monitor'ların çalışıp çalışmadığını gösterir.
    """
    import os
    from services.twitter_monitor import get_twitter_monitor
    from services.live_news_monitor import get_live_monitor
    
    twitter_monitor = get_twitter_monitor()
    live_monitor = get_live_monitor()
    
    return SystemStatusResponse(
        twitter_configured=bool(os.environ.get("X_BEARER_TOKEN")),
        groq_configured=bool(os.environ.get("GROQ_API_KEY")),
        xai_configured=bool(os.environ.get("XAI_API_KEY")),
        twitter_monitor_running=twitter_monitor.is_running,
        live_news_monitor_running=live_monitor.is_running,
        recent_twitter_alerts=len(twitter_monitor.get_recent_alerts(60)),
        recent_news_alerts=len(live_monitor.get_recent_alerts(60))
    )


@router.post("/start-twitter-monitor")
async def start_twitter_monitor(background_tasks: BackgroundTasks, interval: int = Query(60, ge=30, le=300)):
    """
    Twitter monitoring'i arka planda başlat.
    Kritik hesapları belirli aralıklarla kontrol eder.
    """
    from services.twitter_monitor import get_twitter_monitor
    
    monitor = get_twitter_monitor()
    
    if monitor.is_running:
        return {"status": "already_running", "message": "Twitter monitor is already running"}
    
    async def run_monitor():
        await monitor.monitor_loop(interval)
    
    background_tasks.add_task(asyncio.create_task, run_monitor())
    
    return {
        "status": "started",
        "message": f"Twitter monitor started with {interval}s interval",
        "interval_seconds": interval
    }


@router.post("/stop-twitter-monitor")
async def stop_twitter_monitor():
    """Twitter monitoring'i durdur."""
    from services.twitter_monitor import get_twitter_monitor
    
    monitor = get_twitter_monitor()
    monitor.stop()
    
    return {"status": "stopped", "message": "Twitter monitor stopped"}


@router.post("/start-live-monitor")
async def start_live_monitor(
    background_tasks: BackgroundTasks,
    channels: List[str] = Query(default=["cnn", "cnbc"])
):
    """
    Canlı TV monitoring'i arka planda başlat.
    NOT: ffmpeg kurulu olmalı ve stream URL'leri erişilebilir olmalı.
    """
    from services.live_news_monitor import get_live_monitor
    
    monitor = get_live_monitor()
    
    if monitor.is_running:
        return {"status": "already_running", "message": "Live news monitor is already running"}
    
    async def run_monitor():
        await monitor.start(channels)
    
    background_tasks.add_task(asyncio.create_task, run_monitor())
    
    return {
        "status": "started",
        "message": f"Live news monitor started for channels: {channels}",
        "channels": channels
    }


@router.post("/stop-live-monitor")
async def stop_live_monitor():
    """Canlı TV monitoring'i durdur."""
    from services.live_news_monitor import stop_live_monitoring
    
    stop_live_monitoring()
    
    return {"status": "stopped", "message": "Live news monitor stopped"}


# =============================================================================
# COMBINED SENTIMENT
# =============================================================================

@router.get("/combined-sentiment")
async def get_combined_sentiment(symbol: str = Query("XAUUSD", description="XAUUSD or NDX.INDX")):
    """
    Twitter + Live News + EODHD haberlerinden birleşik sentiment.
    ML modeline input olarak kullanılabilir.
    """
    from services.twitter_monitor import get_twitter_impact as _get_twitter
    from services.live_news_monitor import get_live_news_impact as _get_live
    
    twitter = await _get_twitter()
    live = await _get_live()
    
    # Ağırlıklı sentiment
    weights = {
        "twitter": 0.4,  # Trump/Fed tweet'leri önemli
        "live_news": 0.3,  # Canlı haberler
        "base": 0.3  # Diğer kaynaklar
    }
    
    # Normalize scores to -1 to 1
    twitter_score = twitter.sentiment_score
    live_score = live.sentiment_score
    
    # Trump etkisi ekstra önemli
    trump_boost = twitter.trump_sentiment * 0.2
    
    combined_score = (
        twitter_score * weights["twitter"] +
        live_score * weights["live_news"] +
        trump_boost
    )
    
    # Clamp
    combined_score = max(-1.0, min(1.0, combined_score))
    
    # Direction
    if combined_score > 0.1:
        direction = "BUY"
    elif combined_score < -0.1:
        direction = "SELL"
    else:
        direction = "NEUTRAL"
    
    # Confidence
    avg_confidence = (twitter.confidence + live.confidence) / 2
    
    return {
        "symbol": symbol,
        "combined_score": round(combined_score, 3),
        "direction": direction,
        "confidence": round(avg_confidence, 1),
        "breakdown": {
            "twitter": {
                "score": round(twitter_score, 3),
                "trump": round(twitter.trump_sentiment, 3),
                "fed": round(twitter.fed_sentiment, 3),
                "confidence": twitter.confidence
            },
            "live_news": {
                "score": round(live_score, 3),
                "channels": live.channels_active,
                "alerts": len(live.alerts),
                "confidence": live.confidence
            }
        },
        "for_ml_model": {
            "news_sentiment": round(combined_score, 3),
            "news_confidence": round(avg_confidence / 100, 3),
            "trump_factor": round(twitter.trump_sentiment, 3),
            "fed_factor": round(twitter.fed_sentiment, 3)
        }
    }
