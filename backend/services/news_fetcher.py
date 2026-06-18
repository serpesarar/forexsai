from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

import httpx

from config import settings

async def fetch_economic_events(days: int = 7) -> List[Dict[str, str]]:
    # Vendor economic-events API retired. Returns sample data until a new
    # economic-calendar source is wired (see economic_calendar_service).
    return _sample_economic_events()


async def fetch_market_news(limit: int = 30) -> List[Dict[str, str]]:
    # Vendor news API retired. Live news now comes from the RSS aggregator /
    # Telegram news detector (coming later); this fallback returns sample data.
    return _sample_market_news()


def classify_sentiment(event: Dict[str, str]) -> str:
    event_name = (event.get("event") or event.get("title") or "").lower()
    actual = _to_float(event.get("actual"))
    expected = _to_float(event.get("estimate") or event.get("expected"))

    if "interest rate" in event_name or "fomc" in event_name:
        if actual is not None and expected is not None and actual > expected:
            return "bearish"
        return "neutral"

    if "cpi" in event_name or "inflation" in event_name:
        if actual is not None and expected is not None:
            if actual < expected:
                return "bullish"
            if actual > expected:
                return "bearish"

    if "unemployment" in event_name or "jobless" in event_name:
        if actual is not None and expected is not None and actual > expected:
            return "bearish"

    return "neutral"


def infer_category(event_name: str) -> Optional[str]:
    lowered = event_name.lower()
    if "fed" in lowered or "fomc" in lowered or "interest rate" in lowered:
        return "fed"
    if "cpi" in lowered or "inflation" in lowered:
        return "inflation"
    if "jobs" in lowered or "unemployment" in lowered or "nfp" in lowered:
        return "jobs"
    return None


def _to_float(value: Optional[str]) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(str(value).replace("%", "").strip())
    except ValueError:
        return None


def _sample_economic_events() -> List[Dict[str, str]]:
    now = datetime.now(timezone.utc)
    return [
        {
            "date": (now - timedelta(hours=2)).isoformat().replace("+00:00", "Z"),
            "event": "Fed Interest Rate Decision",
            "impact": "High",
            "actual": "5.50%",
            "estimate": "5.50%",
            "previous": "5.25%",
        },
        {
            "date": (now - timedelta(hours=4)).isoformat().replace("+00:00", "Z"),
            "event": "CPI (Core)",
            "impact": "Medium",
            "actual": "3.2%",
            "estimate": "3.3%",
            "previous": "3.4%",
        },
        {
            "date": (now - timedelta(days=1)).isoformat().replace("+00:00", "Z"),
            "event": "Housing Starts",
            "impact": "Low",
            "actual": "1.42M",
            "estimate": "1.40M",
            "previous": "1.38M",
        },
    ]


def _sample_market_news() -> List[Dict[str, str]]:
    now = datetime.now(timezone.utc)
    return [
        {
            "date": (now - timedelta(minutes=45)).isoformat().replace("+00:00", "Z"),
            "title": "Nasdaq rallies as mega-cap earnings beat expectations",
            "content": "Tech earnings sparked a broad market rally as investors rotated into growth.",
            "link": "https://example.com/market-news/nasdaq-rally",
            "symbols": ["NDX.INDX"],
        },
        {
            "date": (now - timedelta(hours=6)).isoformat().replace("+00:00", "Z"),
            "title": "Gold steadies ahead of CPI report",
            "content": "Traders positioned cautiously ahead of inflation data and Fed commentary.",
            "link": "https://example.com/market-news/gold-steadies",
            "symbols": ["XAUUSD"],
        },
    ]
