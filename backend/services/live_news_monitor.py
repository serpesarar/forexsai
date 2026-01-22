"""
CANLI HABER TRANSKRİPT SİSTEMİ
CNN/Fox/CNBC canlı yayınlarını dinler, kritik kelimeleri tespit eder
Groq Whisper (ücretsiz) kullanır

XAUUSD ve NASDAQ için kritik haberleri anlık yakalar:
- Trump konuşmaları, tariff haberleri
- Fed kararları, faiz açıklamaları
- Ekonomik veriler, enflasyon
"""

from __future__ import annotations

import asyncio
import logging
import subprocess
import tempfile
import os
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from pathlib import Path
import httpx

from config import settings

logger = logging.getLogger(__name__)


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class TranscriptAlert:
    """Tespit edilen kritik haber"""
    keyword: str
    full_text: str
    channel: str
    timestamp: datetime
    sentiment: str = "neutral"  # bullish, bearish, neutral
    impact_level: str = "medium"  # high, medium, low
    confidence: float = 0.5
    

@dataclass
class LiveNewsImpact:
    """Canlı haber etkisi"""
    sentiment_score: float  # -1 to +1
    confidence: float  # 0-100
    direction_bias: str  # BUY, SELL, NEUTRAL
    alerts: List[TranscriptAlert]
    last_update: datetime
    channels_active: List[str]


# =============================================================================
# STREAM URLS - Ücretsiz ve Yasal Kaynaklar
# =============================================================================

STREAM_URLS = {
    'cnn': 'https://cnngo1.akamaized.net/hls/live/598782/PROD-cnnlive1/master.m3u8',
    'cnn_2': 'https://cnngo1.akamaized.net/hls/live/599236/PROD-cnnlive2/master.m3u8',
    'cnn_int': 'https://cnn-i.akamaihd.net/hls/224534/cnndebates_1/v2/master.m3u8',
    'fox': 'http://foxnewsuni-f.akamaihd.net/i/FNCGOPREV_40220@40220/master.m3u8',
    'fox_radio': 'https://fnurtmp-f.akamaihd.net/i/FNRADIO_1@92241/master.m3u8',
    'cnbc': 'https://service-stitcher.clusters.pluto.tv/stitch/hls/channel/5421f71da6af422839419cb3/master.m3u8',
    'bloomberg': 'https://www.bloomberg.com/media-manifest/streams/us.m3u8',
}


# =============================================================================
# KEYWORDS - Trading İçin Kritik Kelimeler
# =============================================================================

# XAUUSD (Gold) için kritik kelimeler
GOLD_KEYWORDS = {
    # Trump & Politics
    'trump': {'impact': 'high', 'base_sentiment': 0.1},
    'donald trump': {'impact': 'high', 'base_sentiment': 0.1},
    'president trump': {'impact': 'high', 'base_sentiment': 0.1},
    'tariff': {'impact': 'high', 'base_sentiment': 0.25},
    'tariffs': {'impact': 'high', 'base_sentiment': 0.25},
    'trade war': {'impact': 'high', 'base_sentiment': 0.3},
    'sanctions': {'impact': 'high', 'base_sentiment': 0.2},
    'executive order': {'impact': 'medium', 'base_sentiment': 0.1},
    
    # Fed & Interest Rates
    'federal reserve': {'impact': 'high', 'base_sentiment': 0.0},
    'fed': {'impact': 'high', 'base_sentiment': 0.0},
    'jerome powell': {'impact': 'high', 'base_sentiment': 0.0},
    'interest rate': {'impact': 'high', 'base_sentiment': 0.0},
    'rate cut': {'impact': 'high', 'base_sentiment': 0.3},
    'rate hike': {'impact': 'high', 'base_sentiment': -0.3},
    'fomc': {'impact': 'high', 'base_sentiment': 0.0},
    'monetary policy': {'impact': 'medium', 'base_sentiment': 0.0},
    
    # Inflation & Economy
    'inflation': {'impact': 'high', 'base_sentiment': 0.2},
    'cpi': {'impact': 'high', 'base_sentiment': 0.0},
    'consumer price': {'impact': 'high', 'base_sentiment': 0.0},
    'recession': {'impact': 'high', 'base_sentiment': 0.25},
    'employment': {'impact': 'medium', 'base_sentiment': 0.0},
    'jobs report': {'impact': 'high', 'base_sentiment': 0.0},
    'unemployment': {'impact': 'medium', 'base_sentiment': 0.0},
    'gdp': {'impact': 'medium', 'base_sentiment': 0.0},
    
    # Gold Specific
    'gold': {'impact': 'medium', 'base_sentiment': 0.0},
    'gold price': {'impact': 'high', 'base_sentiment': 0.0},
    'safe haven': {'impact': 'high', 'base_sentiment': 0.2},
    'central bank': {'impact': 'medium', 'base_sentiment': 0.1},
    'dollar': {'impact': 'medium', 'base_sentiment': 0.0},
    'treasury': {'impact': 'medium', 'base_sentiment': 0.0},
    
    # Geopolitical
    'war': {'impact': 'high', 'base_sentiment': 0.3},
    'military': {'impact': 'medium', 'base_sentiment': 0.15},
    'conflict': {'impact': 'high', 'base_sentiment': 0.2},
    'crisis': {'impact': 'high', 'base_sentiment': 0.2},
    'geopolitical': {'impact': 'medium', 'base_sentiment': 0.15},
}

# NASDAQ için kritik kelimeler
NASDAQ_KEYWORDS = {
    'tech': {'impact': 'medium', 'base_sentiment': 0.0},
    'technology': {'impact': 'medium', 'base_sentiment': 0.0},
    'nvidia': {'impact': 'high', 'base_sentiment': 0.0},
    'apple': {'impact': 'high', 'base_sentiment': 0.0},
    'microsoft': {'impact': 'high', 'base_sentiment': 0.0},
    'amazon': {'impact': 'high', 'base_sentiment': 0.0},
    'google': {'impact': 'high', 'base_sentiment': 0.0},
    'meta': {'impact': 'high', 'base_sentiment': 0.0},
    'ai': {'impact': 'high', 'base_sentiment': 0.1},
    'artificial intelligence': {'impact': 'high', 'base_sentiment': 0.1},
    'earnings': {'impact': 'high', 'base_sentiment': 0.0},
    'revenue': {'impact': 'medium', 'base_sentiment': 0.0},
    'chip': {'impact': 'medium', 'base_sentiment': 0.0},
    'semiconductor': {'impact': 'high', 'base_sentiment': 0.0},
}

# Sentiment modifiers
BULLISH_MODIFIERS = [
    'surge', 'soar', 'rally', 'jump', 'gain', 'rise', 'climb', 'boost',
    'bullish', 'positive', 'strong', 'beat', 'exceed', 'record high',
    'optimism', 'confidence', 'growth', 'recovery', 'support'
]

BEARISH_MODIFIERS = [
    'plunge', 'crash', 'tumble', 'fall', 'drop', 'decline', 'sink', 'slump',
    'bearish', 'negative', 'weak', 'miss', 'disappoint', 'record low',
    'fear', 'concern', 'risk', 'slowdown', 'cut', 'layoff'
]


# =============================================================================
# GROQ WHISPER CLIENT (Ücretsiz Speech-to-Text)
# =============================================================================

class GroqWhisperClient:
    """Groq'un ücretsiz Whisper API'si ile speech-to-text"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        self.base_url = "https://api.groq.com/openai/v1/audio/transcriptions"
        
    async def transcribe(self, audio_file_path: str) -> Optional[str]:
        """Ses dosyasını metne çevir"""
        if not self.api_key:
            logger.warning("GROQ_API_KEY not set")
            return None
            
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                with open(audio_file_path, 'rb') as audio_file:
                    files = {'file': ('audio.wav', audio_file, 'audio/wav')}
                    data = {'model': 'whisper-large-v3'}
                    headers = {'Authorization': f'Bearer {self.api_key}'}
                    
                    response = await client.post(
                        self.base_url,
                        files=files,
                        data=data,
                        headers=headers
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        return result.get('text', '')
                    else:
                        logger.error(f"Groq Whisper error: {response.status_code} - {response.text}")
                        return None
        except Exception as e:
            logger.error(f"Groq Whisper exception: {e}")
            return None


# =============================================================================
# LIVE NEWS MONITOR
# =============================================================================

class LiveNewsMonitor:
    """
    Canlı TV yayınlarını dinler ve kritik haberleri tespit eder.
    
    Akış:
    1. Stream URL'den ses al (ffmpeg)
    2. Groq Whisper ile metne çevir (ücretsiz)
    3. Keyword detection
    4. Claude ile sentiment analizi
    5. ML Model'e gönder
    """
    
    def __init__(self, groq_api_key: Optional[str] = None):
        self.whisper = GroqWhisperClient(groq_api_key)
        self.alerts: List[TranscriptAlert] = []
        self.is_running = False
        self.active_channels: List[str] = []
        self._callbacks: List[Callable[[TranscriptAlert], None]] = []
        
    def add_callback(self, callback: Callable[[TranscriptAlert], None]):
        """Alert geldiğinde çağrılacak callback ekle"""
        self._callbacks.append(callback)
        
    def _notify_callbacks(self, alert: TranscriptAlert):
        """Tüm callback'leri bilgilendir"""
        for callback in self._callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Callback error: {e}")
    
    def _extract_audio_chunk(self, stream_url: str, duration: int = 30) -> Optional[str]:
        """
        Stream'den ses parçası çıkar (ffmpeg kullanarak)
        
        Args:
            stream_url: HLS/M3U8 stream URL
            duration: Saniye cinsinden süre
            
        Returns:
            Geçici ses dosyası yolu
        """
        try:
            # Geçici dosya oluştur
            temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            temp_path = temp_file.name
            temp_file.close()
            
            # ffmpeg komutu
            command = [
                'ffmpeg',
                '-y',  # Overwrite
                '-i', stream_url,
                '-t', str(duration),
                '-vn',  # No video
                '-acodec', 'pcm_s16le',
                '-ar', '16000',
                '-ac', '1',
                temp_path
            ]
            
            process = subprocess.run(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=duration + 30
            )
            
            if process.returncode == 0 and os.path.exists(temp_path):
                return temp_path
            else:
                return None
                
        except subprocess.TimeoutExpired:
            logger.warning(f"ffmpeg timeout for {stream_url}")
            return None
        except Exception as e:
            logger.error(f"Audio extraction error: {e}")
            return None
    
    def _analyze_text(self, text: str, channel: str) -> List[TranscriptAlert]:
        """
        Metni analiz et ve kritik kelimeleri tespit et
        
        Returns:
            Tespit edilen alert listesi
        """
        text_lower = text.lower()
        alerts = []
        
        # Tüm keyword'leri kontrol et
        all_keywords = {**GOLD_KEYWORDS, **NASDAQ_KEYWORDS}
        
        for keyword, config in all_keywords.items():
            if keyword in text_lower:
                # Sentiment analizi
                sentiment_score = config['base_sentiment']
                
                # Modifier'ları kontrol et
                for bullish in BULLISH_MODIFIERS:
                    if bullish in text_lower:
                        sentiment_score += 0.1
                        
                for bearish in BEARISH_MODIFIERS:
                    if bearish in text_lower:
                        sentiment_score -= 0.1
                
                # Sentiment sınıflandırma
                if sentiment_score > 0.1:
                    sentiment = "bullish"
                elif sentiment_score < -0.1:
                    sentiment = "bearish"
                else:
                    sentiment = "neutral"
                
                alert = TranscriptAlert(
                    keyword=keyword,
                    full_text=text[:500],
                    channel=channel,
                    timestamp=datetime.utcnow(),
                    sentiment=sentiment,
                    impact_level=config['impact'],
                    confidence=min(0.9, 0.5 + abs(sentiment_score))
                )
                alerts.append(alert)
                
                logger.info(f"🚨 ALERT: {keyword.upper()} on {channel} - {sentiment}")
        
        return alerts
    
    async def monitor_channel(self, channel: str, duration: int = 30):
        """
        Tek bir kanalı dinle
        
        Args:
            channel: Kanal adı (cnn, fox, cnbc, bloomberg)
            duration: Her döngüde dinlenecek süre (saniye)
        """
        stream_url = STREAM_URLS.get(channel)
        if not stream_url:
            logger.error(f"Unknown channel: {channel}")
            return
        
        logger.info(f"🎥 Starting monitor for {channel.upper()}")
        self.active_channels.append(channel)
        
        while self.is_running:
            try:
                # Ses çıkar
                audio_path = self._extract_audio_chunk(stream_url, duration)
                
                if audio_path:
                    # Transkript al
                    text = await self.whisper.transcribe(audio_path)
                    
                    # Geçici dosyayı sil
                    try:
                        os.unlink(audio_path)
                    except:
                        pass
                    
                    if text:
                        # Analiz et
                        new_alerts = self._analyze_text(text, channel)
                        
                        for alert in new_alerts:
                            self.alerts.append(alert)
                            self._notify_callbacks(alert)
                            
                            # Son 100 alert'i tut
                            if len(self.alerts) > 100:
                                self.alerts = self.alerts[-100:]
                
                # Kısa bekleme
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Monitor error for {channel}: {e}")
                await asyncio.sleep(10)
        
        self.active_channels.remove(channel)
    
    async def start(self, channels: List[str] = None):
        """
        Monitoring'i başlat
        
        Args:
            channels: İzlenecek kanallar. None ise tümü.
        """
        if channels is None:
            channels = ['cnn', 'fox', 'cnbc']
        
        self.is_running = True
        
        # Her kanal için ayrı task
        tasks = [
            asyncio.create_task(self.monitor_channel(ch))
            for ch in channels
        ]
        
        await asyncio.gather(*tasks)
    
    def stop(self):
        """Monitoring'i durdur"""
        self.is_running = False
        logger.info("Live news monitor stopped")
    
    def get_recent_alerts(self, minutes: int = 60) -> List[TranscriptAlert]:
        """Son X dakikadaki alert'leri getir"""
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        return [a for a in self.alerts if a.timestamp > cutoff]
    
    def get_impact_summary(self) -> LiveNewsImpact:
        """Son alert'lerin özetini getir"""
        recent = self.get_recent_alerts(60)
        
        if not recent:
            return LiveNewsImpact(
                sentiment_score=0.0,
                confidence=20.0,
                direction_bias="NEUTRAL",
                alerts=[],
                last_update=datetime.utcnow(),
                channels_active=self.active_channels.copy()
            )
        
        # Ağırlıklı sentiment hesapla
        total_weight = 0
        weighted_sentiment = 0
        
        for alert in recent:
            weight = 1.0 if alert.impact_level == 'high' else 0.5
            sentiment_value = {
                'bullish': 0.3,
                'bearish': -0.3,
                'neutral': 0.0
            }.get(alert.sentiment, 0.0)
            
            weighted_sentiment += sentiment_value * weight * alert.confidence
            total_weight += weight
        
        avg_sentiment = weighted_sentiment / max(total_weight, 1)
        
        # Direction bias
        if avg_sentiment > 0.1:
            direction = "BUY"
        elif avg_sentiment < -0.1:
            direction = "SELL"
        else:
            direction = "NEUTRAL"
        
        # Confidence
        high_impact = len([a for a in recent if a.impact_level == 'high'])
        confidence = min(90, 40 + high_impact * 15)
        
        return LiveNewsImpact(
            sentiment_score=avg_sentiment,
            confidence=confidence,
            direction_bias=direction,
            alerts=recent[-10:],  # Son 10 alert
            last_update=datetime.utcnow(),
            channels_active=self.active_channels.copy()
        )


# =============================================================================
# GLOBAL INSTANCE & HELPER FUNCTIONS
# =============================================================================

_monitor_instance: Optional[LiveNewsMonitor] = None


def get_live_monitor() -> LiveNewsMonitor:
    """Singleton monitor instance"""
    global _monitor_instance
    if _monitor_instance is None:
        groq_key = os.environ.get("GROQ_API_KEY")
        _monitor_instance = LiveNewsMonitor(groq_key)
    return _monitor_instance


async def get_live_news_impact() -> LiveNewsImpact:
    """ML modeli için canlı haber etkisini getir"""
    monitor = get_live_monitor()
    return monitor.get_impact_summary()


async def start_live_monitoring(channels: List[str] = None):
    """Background'da canlı haber takibini başlat"""
    monitor = get_live_monitor()
    await monitor.start(channels)


def stop_live_monitoring():
    """Canlı haber takibini durdur"""
    monitor = get_live_monitor()
    monitor.stop()


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    async def test():
        monitor = LiveNewsMonitor()
        
        # Test callback
        def on_alert(alert: TranscriptAlert):
            print(f"\n{'='*60}")
            print(f"🚨 {alert.keyword.upper()} detected!")
            print(f"📺 Channel: {alert.channel}")
            print(f"💬 Text: {alert.full_text[:200]}...")
            print(f"📊 Sentiment: {alert.sentiment}")
            print(f"⚡ Impact: {alert.impact_level}")
            print(f"{'='*60}\n")
        
        monitor.add_callback(on_alert)
        
        print("Starting live news monitor...")
        print("Press Ctrl+C to stop")
        
        try:
            await monitor.start(['cnn'])
        except KeyboardInterrupt:
            monitor.stop()
            print("\nStopped.")
    
    asyncio.run(test())
