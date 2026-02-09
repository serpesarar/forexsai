from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import List

from config import settings


def _path_exists(path: str) -> bool:
    return Path(path).expanduser().exists()


def run_pattern_engine(last_n: int, select_top: float, output_selected_only: bool) -> dict:
    """
    Non-mock, deterministic "pattern engine" based on live EOD candles.
    Uses DataHub cached EOD data (0 API calls).
    """
    model_ok = _path_exists(settings.pattern_engine_path)
    status = None if model_ok else f"Runtime not found: {settings.pattern_engine_path}"

    # Pull recent daily candles from DataHub (0 API calls)
    symbol = "NDX.INDX"
    now = datetime.utcnow()

    closes: List[float] = []
    try:
        from services.data_hub import get_candles
        eod_data = get_candles(symbol, "eod", 400)
        for row in eod_data:
            if isinstance(row, dict) and row.get("close") is not None:
                closes.append(float(row["close"]))
    except Exception:
        closes = []

    def _ret(window: int) -> float:
        if len(closes) < window + 1:
            return 0.0
        return (closes[-1] - closes[-1 - window]) / max(1e-9, closes[-1 - window])

    def _vol(window: int) -> float:
        if len(closes) < window + 1:
            return 0.0
        series = closes[-window:]
        mean = sum(series) / len(series)
        var = sum((x - mean) ** 2 for x in series) / max(1, len(series) - 1)
        return var ** 0.5 / max(1e-9, mean)

    r5 = _ret(5)
    r20 = _ret(20)
    vol20 = _vol(20)
    direction = "UP" if r5 >= 0 else "DOWN"

    # Deterministic candidates derived from live series
    base_patterns = [
        ("momentum_5d", "BUY" if r5 > 0 else "SELL", min(0.95, 0.55 + abs(r5) * 5)),
        ("momentum_20d", "BUY" if r20 > 0 else "SELL", min(0.95, 0.55 + abs(r20) * 3)),
        ("volatility_break", "HOLD" if vol20 < 0.01 else ("BUY" if r5 > 0 else "SELL"), min(0.9, 0.55 + vol20 * 10)),
        ("mean_reversion", "BUY" if r5 < -0.01 else ("SELL" if r5 > 0.01 else "HOLD"), min(0.9, 0.55 + abs(r5) * 4)),
    ]

    patterns: List[dict] = []
    trade_thr = 0.65
    for idx, (pid, route, p_success) in enumerate(base_patterns[: min(10, last_n)]):
        timestamp = (now - timedelta(minutes=idx * 15)).isoformat() + "Z"
        patterns.append(
            {
                "timestamp": timestamp,
                "pattern_id": pid,
                "route": route,
                "p_success": round(float(p_success), 2),
                "trade_ok": float(p_success) >= trade_thr,
                "trade_thr": trade_thr,
                "expected_next": direction if route != "HOLD" else "SIDEWAYS",
                "stage": "DETECTED",
            }
        )

    selected_count = int(last_n * select_top)
    if output_selected_only:
        patterns = [p for p in patterns if p["trade_ok"]]

    return {
        "patterns": patterns,
        "total_candidates": last_n,
        "selected_count": selected_count,
        "selection_threshold": trade_thr,
        "model_status": status,
    }
