"""
INTELLIGENT NEWS-CANDLE MATCHING SERVICE
Büyük mum hareketlerini gerçekten açıklayan haberleri tespit eder

Algoritma:
1. Mum hareketinin büyüklüğünü ve volatilitesini analiz et
2. Mum zaman aralığına denk düşen haberleri getir
3. Haberlerin impact score'unu ve urgency'sini değerlendir
4. Sadece anlamlı eşleşmeleri döndür (max 5 haber)
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
import statistics

from database.supabase_client import get_supabase_client


@dataclass
class CandleInfo:
    """Mum verisi"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    
    @property
    def change_pct(self) -> float:
        """Yüzdelik değişim"""
        if self.open == 0:
            return 0
        return ((self.close - self.open) / self.open) * 100
    
    @property
    def range_pct(self) -> float:
        """Mum range'i (high-low) yüzdesi"""
        if self.open == 0:
            return 0
        return ((self.high - self.low) / self.open) * 100
    
    @property
    def is_bullish(self) -> bool:
        return self.close > self.open
    
    @property
    def is_bearish(self) -> bool:
        return self.close < self.open
    
    @property
    def body_size_pct(self) -> float:
        """Mum gövdesi yüzdesi"""
        if self.open == 0:
            return 0
        return abs(self.close - self.open) / self.open * 100


@dataclass
class MatchedNews:
    """Eşleşen haber"""
    id: str
    headline: str
    headline_tr: str
    timestamp: datetime
    urgency: str
    score: int
    direction: str
    confidence: float
    reasoning_tr: str
    relevance_score: float  # 0-1 arası eşleşme kalitesi
    time_diff_minutes: float
    url: str


class NewsCandleMatcher:
    """Akıllı haber-mum eşleştirme servisi"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
    
    def calculate_candle_significance(self, candle: CandleInfo, 
                                     avg_range: float, 
                                     atr: float) -> Dict[str, Any]:
        """
        Mumun ne kadar önemli olduğunu hesapla
        
        Returns:
            {
                "is_significant": bool,
                "significance_score": float,  # 0-10 arası
                "movement_type": "major" | "moderate" | "minor",
                "expected_news_urgency": ["breaking", "high"] | ["high", "medium"] | ["medium"],
                "min_impact_score": int
            }
        """
        change_pct = abs(candle.change_pct)
        range_pct = candle.range_pct
        
        # ATR'e göre normalize et
        atr_multiple = range_pct / atr if atr > 0 else 0
        
        # Volatilite skoru (0-10)
        significance_score = min(10, atr_multiple * 2 + change_pct * 2)
        
        # Mum önem derecesi
        if significance_score >= 7 or atr_multiple >= 2.5:
            return {
                "is_significant": True,
                "significance_score": significance_score,
                "movement_type": "major",
                "expected_news_urgency": ["breaking", "high"],
                "min_impact_score": 7,
                "time_window_minutes": 30  # Dar zaman penceresi
            }
        elif significance_score >= 4 or atr_multiple >= 1.5:
            return {
                "is_significant": True,
                "significance_score": significance_score,
                "movement_type": "moderate",
                "expected_news_urgency": ["high", "medium"],
                "min_impact_score": 5,
                "time_window_minutes": 60
            }
        else:
            return {
                "is_significant": False,
                "significance_score": significance_score,
                "movement_type": "minor",
                "expected_news_urgency": ["medium"],
                "min_impact_score": 4,
                "time_window_minutes": 120
            }
    
    def fetch_relevant_news(self, 
                           symbol: str, 
                           candle_time: datetime,
                           time_window_minutes: int,
                           min_impact_score: int,
                           expected_urgency: List[str]) -> List[Dict]:
        """
        Muma yakın zamanda etkili haberleri getir
        """
        start_time = candle_time - timedelta(minutes=time_window_minutes)
        end_time = candle_time + timedelta(minutes=time_window_minutes//2)
        
        try:
            # Önce yüksek urgency haberleri dene
            result = (
                self.supabase.table("enriched_news")
                .select("*")
                .gte("timestamp", start_time.isoformat())
                .lte("timestamp", end_time.isoformat())
                .in_("urgency", expected_urgency)
                .order("timestamp", desc=False)
                .limit(20)
                .execute()
            )
            
            items = result.data if hasattr(result, 'data') else result.get('data', [])
            
            # Eğer yeterli haber yoksa, tüm haberleri dene ama skor filtresi uygula
            if len(items) < 3:
                result_all = (
                    self.supabase.table("enriched_news")
                    .select("*")
                    .gte("timestamp", start_time.isoformat())
                    .lte("timestamp", end_time.isoformat())
                    .order("ai_confidence", desc=True)
                    .limit(10)
                    .execute()
                )
                items_all = result_all.data if hasattr(result_all, 'data') else result_all.get('data', [])
                
                # Skor filtresi uygula
                filtered = []
                for item in items_all:
                    impacts = item.get("impacts", [])
                    symbol_impact = next(
                        (imp for imp in impacts if imp.get("symbol") == symbol),
                        None
                    )
                    if symbol_impact and symbol_impact.get("score", 0) >= min_impact_score:
                        filtered.append(item)
                
                items = filtered
            
            return items or []
            
        except Exception as e:
            print(f"[NewsCandleMatcher] Error fetching news: {e}")
            return []
    
    def calculate_relevance(self, 
                           news: Dict,
                           candle: CandleInfo,
                           symbol: str) -> float:
        """
        Haberin mumla ne kadar alakalı olduğunu hesapla (0-1 arası)
        
        Faktörler:
        - Zaman yakınlığı (haber mumdan önce mi sonra mı)
        - Yön uyumu (haber bullish, mum bullish mi)
        - Impact score
        - Urgency seviyesi
        - Confidence
        """
        impacts = news.get("impacts", [])
        symbol_impact = next(
            (imp for imp in impacts if imp.get("symbol") == symbol),
            None
        )
        
        if not symbol_impact:
            return 0
        
        relevance = 0.0
        
        # 1. Impact score ağırlığı (0-0.3)
        impact_score = symbol_impact.get("score", 5)
        relevance += (impact_score / 10) * 0.3
        
        # 2. Urgency ağırlığı (0-0.25)
        urgency_weights = {
            "breaking": 1.0,
            "high": 0.8,
            "medium": 0.4,
            "low": 0.1
        }
        urgency = news.get("urgency", "medium")
        relevance += urgency_weights.get(urgency, 0.4) * 0.25
        
        # 3. Yön uyumu (0-0.25)
        news_direction = symbol_impact.get("direction", "neutral")
        if news_direction == "bullish" and candle.is_bullish:
            relevance += 0.25
        elif news_direction == "bearish" and candle.is_bearish:
            relevance += 0.25
        elif news_direction == "neutral":
            relevance += 0.1
        
        # 4. AI confidence (0-0.1)
        ai_confidence = news.get("ai_confidence", 50) / 100
        relevance += ai_confidence * 0.1
        
        # 5. Zaman faktörü (0-0.1)
        # Haber mumdan hemen önceyse daha iyi
        news_time = datetime.fromisoformat(news.get("timestamp", "").replace('Z', '+00:00'))
        time_diff = abs((news_time - candle.timestamp).total_seconds() / 60)
        if time_diff < 15:
            relevance += 0.1
        elif time_diff < 30:
            relevance += 0.05
        
        return min(1.0, relevance)
    
    def match_news_to_candle(self,
                            symbol: str,
                            candle: CandleInfo,
                            historical_candles: List[CandleInfo]) -> List[MatchedNews]:
        """
        Ana eşleştirme fonksiyonu
        
        Returns:
            Önem sırasına göre sıralanmış en fazla 5 haber
        """
        # ATR hesapla (son 20 mum)
        if len(historical_candles) >= 20:
            recent_ranges = [c.range_pct for c in historical_candles[-20:]]
            atr = statistics.mean(recent_ranges)
            avg_range = atr
        else:
            atr = 0.5  # Default
            avg_range = 0.5
        
        # Mum önemini analiz et
        significance = self.calculate_candle_significance(candle, avg_range, atr)
        
        print(f"[NewsCandleMatcher] Candle significance: {significance['movement_type']}, "
              f"score: {significance['significance_score']:.1f}, "
              f"expected urgency: {significance['expected_news_urgency']}")
        
        # Önemsiz mumlar için az haber döndür
        if not significance["is_significant"]:
            print(f"[NewsCandleMatcher] Insignificant candle, returning empty")
            return []
        
        # Haberleri getir
        news_items = self.fetch_relevant_news(
            symbol=symbol,
            candle_time=candle.timestamp,
            time_window_minutes=significance["time_window_minutes"],
            min_impact_score=significance["min_impact_score"],
            expected_urgency=significance["expected_news_urgency"]
        )
        
        if not news_items:
            print(f"[NewsCandleMatcher] No news found for this candle")
            return []
        
        # Her haber için relevance hesapla
        matched = []
        for news in news_items:
            relevance = self.calculate_relevance(news, candle, symbol)
            
            # Minimum relevance threshold
            if relevance < 0.3:
                continue
            
            impacts = news.get("impacts", [])
            symbol_impact = next(
                (imp for imp in impacts if imp.get("symbol") == symbol),
                None
            )
            
            if not symbol_impact:
                continue
            
            news_time = datetime.fromisoformat(news.get("timestamp", "").replace('Z', '+00:00'))
            time_diff = (news_time - candle.timestamp).total_seconds() / 60
            
            matched.append(MatchedNews(
                id=news.get("id", ""),
                headline=news.get("headline", ""),
                headline_tr=news.get("headline_tr", news.get("headline", "")),
                timestamp=news_time,
                urgency=news.get("urgency", "medium"),
                score=symbol_impact.get("score", 5),
                direction=symbol_impact.get("direction", "neutral"),
                confidence=symbol_impact.get("confidence", 0.5),
                reasoning_tr=symbol_impact.get("reasoning_tr", ""),
                relevance_score=relevance,
                time_diff_minutes=time_diff,
                url=news.get("url", "")
            ))
        
        # Relevance'a göre sırala ve en iyi 5'i al
        matched.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Eğer çok fazla "medium" varsa ve "high" azsa, filtrele
        high_news = [n for n in matched if n.urgency in ["breaking", "high"]]
        
        if len(high_news) >= 2:
            # Sadece high urgency haberleri göster
            result = high_news[:5]
        else:
            # High + en iyi medium haberleri
            result = matched[:5]
        
        print(f"[NewsCandleMatcher] Found {len(result)} relevant news items "
              f"(filtered from {len(matched)} matches)")
        
        return result
    
    def match_news_to_candle_simple(self,
                                   symbol: str,
                                   candle_timestamp: str,
                                   candle_open: float,
                                   candle_close: float,
                                   candle_high: float,
                                   candle_low: float) -> List[Dict]:
        """
        Basit API versiyonu - direkt değerlerle çalışır
        """
        try:
            candle = CandleInfo(
                timestamp=datetime.fromisoformat(candle_timestamp.replace('Z', '+00:00')),
                open=candle_open,
                high=candle_high,
                low=candle_low,
                close=candle_close,
                volume=0
            )
            
            # Basit ATR hesapla (tek mum için)
            atr = candle.range_pct * 0.5
            
            significance = self.calculate_candle_significance(candle, atr, atr)
            
            if not significance["is_significant"]:
                return []
            
            # Haberleri getir
            news_items = self.fetch_relevant_news(
                symbol=symbol,
                candle_time=candle.timestamp,
                time_window_minutes=significance["time_window_minutes"],
                min_impact_score=significance["min_impact_score"],
                expected_urgency=significance["expected_news_urgency"]
            )
            
            # Relevance hesapla ve sırala
            matched = []
            for news in news_items:
                relevance = self.calculate_relevance(news, candle, symbol)
                if relevance >= 0.3:
                    impacts = news.get("impacts", [])
                    symbol_impact = next(
                        (imp for imp in impacts if imp.get("symbol") == symbol),
                        None
                    )
                    if symbol_impact:
                        matched.append({
                            **news,
                            "relevance_score": relevance,
                            "symbol_impact": symbol_impact
                        })
            
            matched.sort(key=lambda x: x["relevance_score"], reverse=True)
            return matched[:5]
            
        except Exception as e:
            print(f"[NewsCandleMatcher] Error in simple match: {e}")
            return []


# Singleton instance
_matcher: Optional[NewsCandleMatcher] = None


def get_news_candle_matcher() -> NewsCandleMatcher:
    """Get or create matcher singleton"""
    global _matcher
    if _matcher is None:
        _matcher = NewsCandleMatcher()
    return _matcher
