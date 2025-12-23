from __future__ import annotations

from datetime import datetime
from typing import Dict

from backend.config import settings


def run_claude_pattern_analysis(symbol: str, timeframes: list[str]) -> dict:
    analyses: Dict[str, dict] = {}
    for timeframe in timeframes:
        analyses[timeframe] = {
            "detected_patterns": [
                {
                    "pattern_name": "Double Bottom",
                    "pattern_source": "instagram",
                    "completion_percentage": 85,
                    "signal": "bullish",
                    "entry": 21500.0,
                    "stop_loss": 21300.0,
                    "target": 21800.0,
                    "confidence": 0.85,
                    "reasoning": "Son 100 mum içinde çift dip tamamlanma aşamasında.",
                }
            ],
            "summary": f"{timeframe} timeframe için güçlü yükseliş paterni.",
            "recommendation": "BUY",
        }
    return {
        "analyses": analyses,
        "current_price": 21547.35,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "model_status": None if settings.anthropic_api_key else "ANTHROPIC_API_KEY missing",
    }
