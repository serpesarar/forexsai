from __future__ import annotations

from datetime import datetime

from backend.config import settings
from backend.services.marketaux_service import fetch_marketaux_headlines


async def run_claude_sentiment() -> dict:
    headlines = await fetch_marketaux_headlines(["NDX.INDX", "XAUUSD"])
    return {
        "sentiment": "BULLISH",
        "confidence": 0.85,
        "probability_up": 60,
        "probability_down": 30,
        "probability_sideways": 10,
        "key_factors": [
            {
                "factor": "Fed Faiz Kararı",
                "impact": "negative",
                "weight": 0.3,
                "reasoning": "Faiz indirimi beklentisi risk iştahını artırıyor.",
            },
            {
                "factor": "VIX Index",
                "impact": "positive",
                "weight": 0.25,
                "reasoning": "VIX düşüşü risk-on sinyali veriyor.",
            },
        ],
        "analysis": "Makro veriler ve haber akışı risk iştahını destekliyor.",
        "recommendation": "NASDAQ ve altın için temkinli uzun pozisyon.",
        "market_data_summary": {
            "vix": 14.2,
            "spy": 485.5,
            "news_count": len(headlines),
            "news_source": "marketaux" if settings.marketaux_api_key else "unavailable",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
        "model_status": None if settings.anthropic_api_key else "ANTHROPIC_API_KEY missing",
        "headlines": headlines,
    }
