from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from backend.config import settings


@dataclass
class SignalResult:
    signal: str
    confidence: float
    reasoning: List[str]
    metrics: dict
    timestamp: str
    model_status: str | None = None


def _path_exists(path: str) -> bool:
    return Path(path).expanduser().exists()


def _base_metrics(trend: str, current_price: Optional[float]) -> dict:
    return {
        "distance_to_ema": 50.0,
        "distance_to_support": -200.0,
        "support_strength": 0.8,
        "rsi": 45.0,
        "trend": trend,
        "current_price": current_price,
    }


def run_nasdaq_signal(current_price: Optional[float] = None) -> SignalResult:
    model_ok = _path_exists(settings.nasdaq_model_path)
    status = None if model_ok else f"Model path not found: {settings.nasdaq_model_path}"
    reasoning = [
        "EMA(20) 50 puan üzerinde",
        "RSI 45 (normal bölge)",
        "En güçlü destek 21,300 (sağlamlık: 8/10)",
    ]
    if current_price is not None:
        reasoning.append(f"Canlı fiyat: {current_price}")
    return SignalResult(
        signal="BUY",
        confidence=0.75,
        reasoning=reasoning,
        metrics=_base_metrics("BULLISH", current_price),
        timestamp=datetime.utcnow().isoformat() + "Z",
        model_status=status,
    )


def run_xauusd_signal(current_price: Optional[float] = None) -> SignalResult:
    model_ok = _path_exists(settings.xauusd_model_path)
    status = None if model_ok else f"Model path not found: {settings.xauusd_model_path}"
    reasoning = [
        "Momentum zayıf, fiyat kritik direnç altında",
        "RSI 52 (nötr)",
        "Destek seviyesi 2,050 (sağlamlık: 7/10)",
    ]
    if current_price is not None:
        reasoning.append(f"Canlı fiyat: {current_price}")
    return SignalResult(
        signal="HOLD",
        confidence=0.68,
        reasoning=reasoning,
        metrics={
            "distance_to_ema": 18.0,
            "distance_to_support": 120.0,
            "support_strength": 0.7,
            "rsi": 52.0,
            "trend": "NEUTRAL",
            "current_price": current_price,
        },
        timestamp=datetime.utcnow().isoformat() + "Z",
        model_status=status,
    )
