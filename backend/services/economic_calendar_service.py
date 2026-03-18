"""
Economic Calendar & Earnings Service
=====================================
Fetches and tracks high-impact economic events and earnings reports.
Integrates with news correlation to mark important events on charts.
"""

import json
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import aiohttp
from services.redis_client import cache_get, cache_set

# High-impact economic events (always affect markets)
HIGH_IMPACT_EVENTS = {
    # US Economic Data
    "nfp", "non-farm payrolls", "employment", "unemployment rate",
    "cpi", "inflation rate", "core cpi", "ppi", "core ppi",
    "gdp", "gdp growth", "advance gdp", "final gdp",
    "fomc", "fed decision", "interest rate decision", "federal funds rate",
    "retail sales", "consumer spending", "durable goods",
    "ism manufacturing", "ism services", "pmi", "industrial production",
    "housing starts", "building permits", "existing home sales", "new home sales",
    "initial jobless claims", "continuing claims", "jobless claims",
    "consumer confidence", "consumer sentiment", "umich sentiment",
    "trade balance", "current account",
    "treasury", "bond yields", "10-year", "2-year", "yield curve",
    
    # European Economic Data
    "ecb", "european central bank", "refinancing rate", "deposit facility rate",
    "eurozone cpi", "eu inflation", "eur inflation",
    "eurozone gdp", "eu gdp", "german gdp", "german cpi",
    "german ifo", "german zew", "german manufacturing",
    
    # UK Economic Data
    "boe", "bank of england", "bank rate", "official bank rate",
    "uk cpi", "uk inflation", "uk gdp",
    
    # Asian Economic Data
    "boj", "bank of japan", "japan interest rate", "yield curve control",
    "china gdp", "china cpi", "china pmi", "pboc", "people's bank of china",
    
    # Critical events (always high urgency)
    "emergency meeting", "emergency rate cut", "intervention", "currency intervention",
}

@dataclass
class EconomicEvent:
    id: str
    timestamp: datetime
    currency: str  # USD, EUR, GBP, etc.
    event_name: str
    impact: str  # high, medium, low
    actual: Optional[str]
    forecast: Optional[str]
    previous: Optional[str]
    affected_symbols: List[str]
    is_earnings: bool = False
    company: Optional[str] = None


class EconomicCalendarService:
    """Service to fetch and cache economic calendar events"""
    
    def __init__(self):
        self.cache_ttl = 300  # 5 minutes for upcoming events
        
    @staticmethod
    def _deserialize_event(payload: Dict[str, Any]) -> EconomicEvent:
        event_payload = dict(payload)
        timestamp = event_payload.get("timestamp")
        if isinstance(timestamp, str):
            event_payload["timestamp"] = datetime.fromisoformat(timestamp.replace("Z", "+00:00")).replace(tzinfo=None)
        return EconomicEvent(**event_payload)
        
    def _get_cache_key(self, date_str: str) -> str:
        return f"economic_calendar:{date_str}"
    
    def _get_earnings_cache_key(self, date_str: str) -> str:
        return f"earnings_calendar:{date_str}"
    
    def _determine_affected_symbols(self, event_name: str, currency: str) -> List[str]:
        """Determine which symbols are affected by this event"""
        symbols = []
        event_lower = event_name.lower()
        
        # Currency-based mapping
        if currency == "USD":
            symbols.extend(["DXY", "XAUUSD", "NDX", "USOIL", "VIX"])
            if any(x in event_lower for x in ["fed", "fomc", "interest", "rate"]):
                symbols.extend(["DXY", "XAUUSD"])  # Major impact
        
        elif currency == "EUR":
            symbols.extend(["DAX", "XAUUSD"])  # DAX affected by Euro
            if any(x in event_lower for x in ["ecb", "eurozone"]):
                symbols.append("DAX")
        
        elif currency == "GBP":
            if "boe" in event_lower:
                symbols.append("DAX")  # FTSE/DAX correlation
        
        # Event-specific mapping
        if any(x in event_lower for x in ["oil", "petroleum", "eia", "crude", "opec"]):
            symbols.append("USOIL")
        
        if any(x in event_lower for x in ["gold", "precious metal", "xau"]):
            symbols.append("XAUUSD")
        
        if any(x in event_lower for x in ["nasdaq", "tech", "apple", "microsoft", "amazon", "nvidia", "tesla", "google", "meta"]):
            symbols.append("NDX")
        
        if any(x in event_lower for x in ["german", "dax", "eurozone manufacturing"]):
            symbols.append("DAX")
        
        if any(x in event_lower for x in ["volatility", "vix", "fear"]):
            symbols.append("VIX")
        
        # High impact events affect everything
        if self._is_high_impact(event_name):
            symbols.extend(["XAUUSD", "NDX", "DAX", "USOIL", "VIX", "DXY"])
        
        return list(set(symbols))  # Remove duplicates
    
    def _is_high_impact(self, event_name: str) -> bool:
        """Check if event is high impact"""
        event_lower = event_name.lower()
        return any(keyword in event_lower for keyword in HIGH_IMPACT_EVENTS)
    
    async def fetch_today_events(self) -> List[EconomicEvent]:
        """Fetch today's economic events from cache or API"""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        cache_key = self._get_cache_key(today)
        
        # Try cache first
        cached = cache_get(cache_key)
        if cached:
            return [self._deserialize_event(e) for e in cached]
        
        # In production, this would call an API like ForexFactory, Investing.com, or Bloomberg
        # For now, we'll create synthetic events based on known schedule
        events = self._generate_today_events()
        
        # Cache for 5 minutes
        cache_data = [{
            "id": e.id,
            "timestamp": e.timestamp.isoformat(),
            "currency": e.currency,
            "event_name": e.event_name,
            "impact": e.impact,
            "actual": e.actual,
            "forecast": e.forecast,
            "previous": e.previous,
            "affected_symbols": e.affected_symbols,
            "is_earnings": e.is_earnings,
            "company": e.company
        } for e in events]
        
        cache_set(cache_key, cache_data, ttl=self.cache_ttl)
        return events
    
    def _generate_today_events(self) -> List[EconomicEvent]:
        """Generate today's known economic events (simplified)"""
        events = []
        now = datetime.utcnow()
        weekday = now.weekday()
        
        # Weekly recurring events
        if weekday == 0:  # Monday
            events.append(EconomicEvent(
                id=f"event_{now.strftime('%Y%m%d')}_001",
                timestamp=now.replace(hour=14, minute=0),
                currency="USD",
                event_name="New Home Sales",
                impact="medium",
                actual=None,
                forecast=None,
                previous=None,
                affected_symbols=["DXY", "NDX"]
            ))
        
        if weekday == 1:  # Tuesday
            events.append(EconomicEvent(
                id=f"event_{now.strftime('%Y%m%d')}_002",
                timestamp=now.replace(hour=14, minute=0),
                currency="USD",
                event_name="Durable Goods Orders",
                impact="medium",
                actual=None,
                forecast=None,
                previous=None,
                affected_symbols=["DXY", "NDX", "DAX"]
            ))
        
        if weekday == 2:  # Wednesday
            # EIA Oil Inventory (always Wednesday)
            events.append(EconomicEvent(
                id=f"event_{now.strftime('%Y%m%d')}_eia",
                timestamp=now.replace(hour=14, minute=30),
                currency="USD",
                event_name="EIA Crude Oil Inventories",
                impact="high",
                actual=None,
                forecast=None,
                previous=None,
                affected_symbols=["USOIL", "XAUUSD"]
            ))
        
        if weekday == 3:  # Thursday
            events.append(EconomicEvent(
                id=f"event_{now.strftime('%Y%m%d')}_003",
                timestamp=now.replace(hour=12, minute=30),
                currency="USD",
                event_name="Initial Jobless Claims",
                impact="medium",
                actual=None,
                forecast=None,
                previous=None,
                affected_symbols=["DXY", "NDX"]
            ))
        
        if weekday == 4:  # Friday
            # NFP on first Friday of month
            if now.day <= 7:
                events.append(EconomicEvent(
                    id=f"event_{now.strftime('%Y%m%d')}_nfp",
                    timestamp=now.replace(hour=12, minute=30),
                    currency="USD",
                    event_name="Non-Farm Payrolls",
                    impact="high",
                    actual=None,
                    forecast=None,
                    previous=None,
                    affected_symbols=["XAUUSD", "NDX", "DAX", "USOIL", "VIX", "DXY"]
                ))
            events.append(EconomicEvent(
                id=f"event_{now.strftime('%Y%m%d')}_004",
                timestamp=now.replace(hour=14, minute=0),
                currency="USD",
                event_name="ISM Manufacturing PMI",
                impact="high",
                actual=None,
                forecast=None,
                previous=None,
                affected_symbols=["DXY", "NDX", "DAX"]
            ))
        
        # Daily events during market hours
        if 12 <= now.hour <= 16:  # US session
            events.append(EconomicEvent(
                id=f"event_{now.strftime('%Y%m%d')}_daily",
                timestamp=now,
                currency="USD",
                event_name="US Market Session Active",
                impact="low",
                actual=None,
                forecast=None,
                previous=None,
                affected_symbols=["NDX", "DAX", "XAUUSD", "USOIL"]
            ))
        
        return events
    
    async def fetch_earnings_today(self) -> List[EconomicEvent]:
        """Fetch today's earnings reports"""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        cache_key = self._get_earnings_cache_key(today)
        
        cached = cache_get(cache_key)
        if cached:
            return [EconomicEvent(**e) for e in cached]
        
        # Major earnings calendar (simplified)
        earnings = self._generate_today_earnings()
        
        cache_data = [{
            "id": e.id,
            "timestamp": e.timestamp.isoformat(),
            "currency": e.currency,
            "event_name": e.event_name,
            "impact": e.impact,
            "actual": e.actual,
            "forecast": e.forecast,
            "previous": e.previous,
            "affected_symbols": e.affected_symbols,
            "is_earnings": e.is_earnings,
            "company": e.company
        } for e in earnings]
        
        cache_set(cache_key, cache_data, ttl=3600)  # 1 hour cache
        return earnings
    
    def _generate_today_earnings(self) -> List[EconomicEvent]:
        """Generate today's major earnings (simplified - would come from API)"""
        # This would typically call an earnings API
        # For now return empty - real implementation would fetch from:
        # - Alpha Vantage
        # - Earnings Whispers
        # - Yahoo Finance
        return []
    
    async def get_upcoming_high_impact_events(self, minutes_ahead: int = 60) -> List[EconomicEvent]:
        """Get high-impact events happening in next X minutes"""
        all_events = await self.fetch_today_events()
        now = datetime.utcnow()
        cutoff = now + timedelta(minutes=minutes_ahead)
        
        upcoming = [
            e for e in all_events 
            if e.impact == "high" and now <= e.timestamp <= cutoff
        ]
        
        return sorted(upcoming, key=lambda x: x.timestamp)
    
    async def get_events_for_symbol(self, symbol: str, hours_back: int = 24) -> List[EconomicEvent]:
        """Get economic events affecting a specific symbol"""
        all_events = await self.fetch_today_events()
        now = datetime.utcnow()
        cutoff = now - timedelta(hours=hours_back)
        
        symbol_events = [
            e for e in all_events 
            if symbol in e.affected_symbols and e.timestamp >= cutoff
        ]
        
        return sorted(symbol_events, key=lambda x: x.timestamp, reverse=True)


# Singleton
_calendar_service: Optional[EconomicCalendarService] = None

def get_calendar_service() -> EconomicCalendarService:
    """Get or create economic calendar service singleton"""
    global _calendar_service
    if _calendar_service is None:
        _calendar_service = EconomicCalendarService()
    return _calendar_service


# News integration helper
async def enrich_news_with_economic_context(news_item: Dict) -> Dict:
    """
    Enrich news item with economic calendar context.
    If news matches an economic event, mark it as high impact.
    """
    calendar = get_calendar_service()
    events = await calendar.fetch_today_events()
    
    news_title = news_item.get("title", "").lower()
    news_time = news_item.get("published_at") or news_item.get("timestamp")
    
    if news_time:
        if isinstance(news_time, str):
            news_time = datetime.fromisoformat(news_time.replace("Z", "+00:00"))
        
        # Check if news is near any economic event
        for event in events:
            time_diff = abs((news_time - event.timestamp).total_seconds())
            
            # If news is within 30 minutes of economic event
            if time_diff < 1800:
                # Check if event keywords match
                event_keywords = event.event_name.lower().split()
                if any(kw in news_title for kw in event_keywords):
                    news_item["economic_event"] = {
                        "name": event.event_name,
                        "impact": event.impact,
                        "affected_symbols": event.affected_symbols
                    }
                    news_item["urgency"] = "high"
                    break
    
    return news_item
