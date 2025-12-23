from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict
import sys

import numpy as np

from backend.models.rtyhiim import RtyhiimPrediction, RtyhiimResponse, RtyhiimState
from backend.config import settings


def run_rtyhiim_detector(symbol: str, timeframe: str) -> Dict[str, object]:
    """Run the RTYHIIM detector using the shared rhythm detector logic."""

    state = _run_rhythm_engine()
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "state": state,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


def _run_rhythm_engine() -> Dict[str, object]:
    detector = _build_detector()
    prices = _generate_prices(600)
    for idx, price in enumerate(prices):
        detector.add_tick(float(price), timestamp=float(idx))
    rhythm_state = detector.detect_wave_pattern()
    decision = detector.should_trade()

    predictions = []
    for horizon in ("30s", "60s", "120s"):
        value = rhythm_state.get("predictions", {}).get(horizon)
        if value is None:
            continue
        predictions.append(
            {
                "horizon": horizon,
                "value": float(value),
                "confidence": float(rhythm_state.get("confidence", 0.0)),
            }
        )

    return RtyhiimState(
        pattern_type=str(rhythm_state.get("pattern_type")),
        dominant_period_s=float(rhythm_state.get("dominant_period_s", 0.0)),
        confidence=float(rhythm_state.get("confidence", 0.0)),
        regularity=float(rhythm_state.get("regularity", 0.0)),
        phase=float(rhythm_state.get("phase", 0.0)),
        amplitude=float(rhythm_state.get("amplitude", 0.0)),
        should_trade=bool(decision.get("should_trade")),
        direction=str(decision.get("direction")),
        predictions=[RtyhiimPrediction(**item) for item in predictions],
    ).dict()


def _build_detector():
    repo_root = Path(__file__).resolve().parents[2]
    if str(repo_root) not in sys.path:
        sys.path.append(str(repo_root))
    try:
        from rhythm_detector_v2 import RhythmDetector, RhythmConfig

        return RhythmDetector(
            RhythmConfig(
                window_seconds=settings.rtyhiim_window_seconds,
                tick_rate_hz=settings.rtyhiim_tick_rate_hz,
                min_period_s=settings.rtyhiim_min_period_s,
                max_period_s=settings.rtyhiim_max_period_s,
            )
        )
    except Exception:
        from rhythm_detector import RhythmDetector, RhythmConfig

        return RhythmDetector(
            RhythmConfig(
                window_seconds=settings.rtyhiim_window_seconds,
                tick_rate_hz=settings.rtyhiim_tick_rate_hz,
                min_period_s=settings.rtyhiim_min_period_s,
                max_period_s=settings.rtyhiim_max_period_s,
            )
        )


def _generate_prices(length: int) -> np.ndarray:
    t = np.arange(length)
    return 100 + np.sin(2 * np.pi * (1 / 60) * t) + np.random.normal(scale=0.3, size=length)
