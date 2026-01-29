"""
NASDAQ Earnings Calendar & Scenario Analysis Service
Yahoo Finance API'den earnings verisi çeker ve senaryo analizi yapar
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

import yfinance as yf

class ImportanceLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class ScenarioType(str, Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    MIXED = "mixed"
    NEUTRAL = "neutral"

@dataclass
class EarningsEvent:
    symbol: str
    company_name: str
    date: str
    time: str  # BMO, AMC, TNS
    expected_eps: Optional[float]
    expected_revenue: Optional[float]
    actual_eps: Optional[float] = None
    actual_revenue: Optional[float] = None
    guidance: Optional[str] = None
    importance: ImportanceLevel = ImportanceLevel.MEDIUM
    nasdaq_weight: float = 0.0

@dataclass
class ScenarioResult:
    scenario_type: ScenarioType
    confidence: float
    nasdaq_direction: str
    color: str
    expected_move_pips: int
    timeframe: str
    risk_level: str
    reasoning: str

# NASDAQ-100 ağırlıkları (top 20)
NASDAQ_WEIGHTS = {
    "AAPL": 12.45, "MSFT": 11.23, "AMZN": 7.85, "NVDA": 6.92,
    "GOOGL": 6.12, "META": 4.78, "TSLA": 4.52, "AVGO": 3.21,
    "COST": 2.89, "NFLX": 2.45, "AMD": 2.34, "ADBE": 2.12,
    "PEP": 1.98, "CSCO": 1.87, "INTC": 1.76, "QCOM": 1.65,
    "CMCSA": 1.54, "TXN": 1.43, "INTU": 1.32, "AMGN": 1.21
}

def get_importance_level(symbol: str) -> ImportanceLevel:
    """Şirketin NASDAQ'taki ağırlığına göre önem seviyesi"""
    weight = NASDAQ_WEIGHTS.get(symbol, 0)
    if weight >= 5.0:
        return ImportanceLevel.CRITICAL
    elif weight >= 2.0:
        return ImportanceLevel.HIGH
    elif weight >= 1.0:
        return ImportanceLevel.MEDIUM
    return ImportanceLevel.LOW


class NASDAQScenarioEngine:
    """Earnings sonuçlarına göre NASDAQ senaryosu oluşturur"""
    
    def __init__(self):
        self.importance_multipliers = {
            ImportanceLevel.CRITICAL: 2.0,
            ImportanceLevel.HIGH: 1.5,
            ImportanceLevel.MEDIUM: 1.0,
            ImportanceLevel.LOW: 0.5
        }
    
    def analyze_scenario(
        self,
        symbol: str,
        actual_eps: float,
        expected_eps: float,
        actual_revenue: float,
        expected_revenue: float,
        guidance: Optional[str] = None
    ) -> ScenarioResult:
        """
        Kazanç sonucuna göre NASDAQ senaryosu oluştur
        """
        # 1. Surprise hesapla
        eps_surprise = (actual_eps - expected_eps) / expected_eps if expected_eps else 0
        revenue_surprise = (actual_revenue - expected_revenue) / expected_revenue if expected_revenue else 0
        
        # 2. Beat/Miss belirleme
        eps_beat = eps_surprise > 0.05  # %5+ beat
        revenue_beat = revenue_surprise > 0.03  # %3+ beat
        
        # 3. Guidance multiplier
        guidance_mult = {"up": 1.5, "maintain": 1.0, "down": 0.5}.get(guidance, 1.0)
        
        # 4. Önem seviyesi
        importance = get_importance_level(symbol)
        
        # 5. Senaryo oluştur
        scenario = self._build_scenario(eps_beat, revenue_beat, eps_surprise, revenue_surprise, guidance, guidance_mult)
        
        # 6. NASDAQ etkisi hesapla
        impact = self._calculate_nasdaq_impact(scenario, importance, symbol)
        
        return ScenarioResult(
            scenario_type=scenario["type"],
            confidence=scenario["confidence"],
            nasdaq_direction=scenario["direction"],
            color=scenario["color"],
            expected_move_pips=impact["move"],
            timeframe=impact["timeframe"],
            risk_level=impact["risk"],
            reasoning=scenario["reasoning"]
        )
    
    def _build_scenario(
        self,
        eps_beat: bool,
        revenue_beat: bool,
        eps_surprise: float,
        revenue_surprise: float,
        guidance: Optional[str],
        guidance_mult: float
    ) -> Dict:
        """Senaryo matrisi"""
        
        if eps_beat and revenue_beat:
            if guidance == "up":
                return {
                    "type": ScenarioType.BULLISH,
                    "confidence": min(95, 90 * guidance_mult),
                    "direction": "up",
                    "color": "#10b981",
                    "reasoning": f"EPS beat {eps_surprise:.1%} + Revenue beat {revenue_surprise:.1%} + Guidance UP → Strong bullish"
                }
            elif guidance == "down":
                return {
                    "type": ScenarioType.MIXED,
                    "confidence": 60,
                    "direction": "uncertain",
                    "color": "#f59e0b",
                    "reasoning": f"Beat but guidance cut → Initial rally then fade likely"
                }
            else:
                return {
                    "type": ScenarioType.BULLISH,
                    "confidence": 75,
                    "direction": "up",
                    "color": "#10b981",
                    "reasoning": f"Strong beat (EPS {eps_surprise:.1%}, Rev {revenue_surprise:.1%}) no guidance"
                }
        
        elif eps_beat and not revenue_beat:
            return {
                "type": ScenarioType.MIXED,
                "confidence": 50,
                "direction": "choppy",
                "color": "#f59e0b",
                "reasoning": "EPS beat but revenue miss → Margin expansion but demand weak"
            }
        
        elif not eps_beat and revenue_beat:
            return {
                "type": ScenarioType.MIXED,
                "confidence": 55,
                "direction": "volatile",
                "color": "#f59e0b",
                "reasoning": "Revenue beat but EPS miss → Cost pressure, margin squeeze"
            }
        
        else:  # Both miss
            if guidance == "down":
                return {
                    "type": ScenarioType.BEARISH,
                    "confidence": 95,
                    "direction": "down",
                    "color": "#ef4444",
                    "reasoning": f"EPS miss {eps_surprise:.1%} + Revenue miss {revenue_surprise:.1%} + Guidance cut → Strong bearish"
                }
            else:
                return {
                    "type": ScenarioType.BEARISH,
                    "confidence": 80,
                    "direction": "down",
                    "color": "#ef4444",
                    "reasoning": "Miss on both metrics → Bearish reaction expected"
                }
    
    def _calculate_nasdaq_impact(self, scenario: Dict, importance: ImportanceLevel, symbol: str) -> Dict:
        """NASDAQ'a etki skorunu hesapla"""
        
        base_confidence = scenario["confidence"]
        weight = NASDAQ_WEIGHTS.get(symbol, 0.5)
        importance_mult = self.importance_multipliers[importance]
        
        # Impact score (0-100)
        impact_score = min(base_confidence * (weight / 5) * importance_mult, 100)
        
        # Expected move (pips)
        direction_mult = 1 if scenario["direction"] in ["up", "bullish"] else -1
        expected_move = int((impact_score / 100) * 50 * (weight / 5)) * direction_mult
        
        # Timeframe
        if importance == ImportanceLevel.CRITICAL:
            timeframe = "pre-market → session"
        elif importance == ImportanceLevel.HIGH:
            timeframe = "pre-market → 1h"
        else:
            timeframe = "pre-market only"
        
        # Risk level
        if impact_score > 70:
            risk = "HIGH"
        elif impact_score > 40:
            risk = "MEDIUM"
        else:
            risk = "LOW"
        
        return {
            "score": round(impact_score, 1),
            "move": expected_move,
            "timeframe": timeframe,
            "risk": risk
        }
    
    def generate_pre_earnings_scenarios(self, symbol: str, expected_eps: float, expected_revenue: float) -> List[Dict]:
        """Earnings öncesi 3 olası senaryo üret"""
        
        importance = get_importance_level(symbol)
        weight = NASDAQ_WEIGHTS.get(symbol, 0.5)
        
        scenarios = []
        
        # Scenario 1: Strong Beat
        beat_result = self.analyze_scenario(
            symbol=symbol,
            actual_eps=expected_eps * 1.10,  # %10 beat
            expected_eps=expected_eps,
            actual_revenue=expected_revenue * 1.05,  # %5 beat
            expected_revenue=expected_revenue,
            guidance="up"
        )
        scenarios.append({
            "name": "Strong Beat + Guidance Up",
            "probability": 25,
            **vars(beat_result)
        })
        
        # Scenario 2: In-line
        inline_result = self.analyze_scenario(
            symbol=symbol,
            actual_eps=expected_eps * 1.02,
            expected_eps=expected_eps,
            actual_revenue=expected_revenue * 1.01,
            expected_revenue=expected_revenue,
            guidance="maintain"
        )
        scenarios.append({
            "name": "In-line Results",
            "probability": 50,
            **vars(inline_result)
        })
        
        # Scenario 3: Miss
        miss_result = self.analyze_scenario(
            symbol=symbol,
            actual_eps=expected_eps * 0.90,  # %10 miss
            expected_eps=expected_eps,
            actual_revenue=expected_revenue * 0.95,
            expected_revenue=expected_revenue,
            guidance="down"
        )
        scenarios.append({
            "name": "Miss + Guidance Cut",
            "probability": 25,
            **vars(miss_result)
        })
        
        return scenarios


class EarningsCalendarService:
    """Yahoo Finance API'den earnings takvimi çeker (ücretsiz)"""
    
    def __init__(self):
        self.scenario_engine = NASDAQScenarioEngine()
        self._executor = ThreadPoolExecutor(max_workers=5)
    
    def _fetch_single_ticker_earnings(self, symbol: str, days_ahead: int) -> Optional[EarningsEvent]:
        """Tek bir ticker için earnings verisi çek (sync)"""
        try:
            ticker = yf.Ticker(symbol)
            calendar = ticker.calendar
            
            if not calendar or "Earnings Date" not in calendar:
                return None
            
            earnings_dates = calendar.get("Earnings Date", [])
            if not earnings_dates:
                return None
            
            # İlk earnings date'i al
            next_earnings = earnings_dates[0] if isinstance(earnings_dates, list) else earnings_dates
            
            # Tarih kontrolü
            today = datetime.now().date()
            max_date = today + timedelta(days=days_ahead)
            
            if isinstance(next_earnings, datetime):
                earnings_date = next_earnings.date()
            else:
                earnings_date = next_earnings
            
            if earnings_date < today or earnings_date > max_date:
                return None
            
            # EPS ve Revenue tahminleri
            eps_avg = calendar.get("Earnings Average")
            rev_avg = calendar.get("Revenue Average")
            
            # Revenue milyar'a çevir
            if rev_avg and rev_avg > 1_000_000_000:
                rev_avg = rev_avg / 1_000_000_000
            
            return EarningsEvent(
                symbol=symbol,
                company_name=ticker.info.get("shortName", symbol),
                date=str(earnings_date),
                time="AMC",  # Yahoo bunu vermez, varsayılan
                expected_eps=float(eps_avg) if eps_avg else None,
                expected_revenue=float(rev_avg) if rev_avg else None,
                importance=get_importance_level(symbol),
                nasdaq_weight=NASDAQ_WEIGHTS.get(symbol, 0)
            )
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
            return None
    
    async def fetch_earnings_calendar(self, days_ahead: int = 7) -> List[EarningsEvent]:
        """Önümüzdeki X gün için earnings takvimi (Yahoo Finance)"""
        
        loop = asyncio.get_event_loop()
        events = []
        
        # NASDAQ-100 top 20 için paralel fetch
        symbols = list(NASDAQ_WEIGHTS.keys())
        
        # ThreadPoolExecutor ile paralel çalıştır
        futures = [
            loop.run_in_executor(
                self._executor, 
                self._fetch_single_ticker_earnings, 
                symbol, 
                days_ahead
            )
            for symbol in symbols
        ]
        
        results = await asyncio.gather(*futures, return_exceptions=True)
        
        for result in results:
            if isinstance(result, EarningsEvent):
                events.append(result)
        
        # Önem sırasına göre sırala
        events.sort(key=lambda x: (
            {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}[x.importance.value],
            x.date
        ))
        
        return events
    
    async def get_earnings_with_scenarios(self, days_ahead: int = 7) -> List[Dict]:
        """Earnings takvimi + senaryo analizleri"""
        
        events = await self.fetch_earnings_calendar(days_ahead)
        result = []
        
        for event in events:
            scenarios = []
            if event.expected_eps and event.expected_revenue:
                scenarios = self.scenario_engine.generate_pre_earnings_scenarios(
                    symbol=event.symbol,
                    expected_eps=event.expected_eps,
                    expected_revenue=event.expected_revenue
                )
            
            result.append({
                "symbol": event.symbol,
                "company_name": event.company_name,
                "date": event.date,
                "time": event.time,
                "expected_eps": event.expected_eps,
                "expected_revenue": event.expected_revenue,
                "importance": event.importance.value,
                "nasdaq_weight": f"{event.nasdaq_weight:.2f}%",
                "scenarios": scenarios,
                "color": self._get_importance_color(event.importance)
            })
        
        return result
    
    def _get_importance_color(self, importance: ImportanceLevel) -> str:
        """Önem seviyesine göre renk"""
        colors = {
            ImportanceLevel.CRITICAL: "#ef4444",  # Red
            ImportanceLevel.HIGH: "#f97316",      # Orange
            ImportanceLevel.MEDIUM: "#eab308",    # Yellow
            ImportanceLevel.LOW: "#22c55e"        # Green
        }
        return colors.get(importance, "#6b7280")


# Singleton instance
earnings_service = EarningsCalendarService()
scenario_engine = NASDAQScenarioEngine()
