from __future__ import annotations

from dataclasses import dataclass
from typing import List, Literal, Tuple

import numpy as np

from services.data_fetcher import fetch_eod_candles, fetch_latest_price
from services.technical_indicators import calculate_ema, calculate_rsi


Trend = Literal["BULLISH", "BEARISH", "NEUTRAL"]


@dataclass
class Level:
    price: float
    kind: Literal["support", "resistance"]
    hits: int
    strength: float  # 0..1


def _ema(values: np.ndarray, period: int) -> float:
    """
    Calculate EMA using TradingView standard.
    Delegates to technical_indicators.calculate_ema for accuracy.
    """
    result = calculate_ema(values, period)
    return float(result) if result is not None else (float(values[-1]) if len(values) else 0.0)


def _rsi(values: np.ndarray, period: int = 14) -> float:
    if len(values) < period + 1:
        return 50.0
    diffs = np.diff(values)
    gains = np.where(diffs > 0, diffs, 0.0)
    losses = np.where(diffs < 0, -diffs, 0.0)
    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:]) + 1e-9
    rs = avg_gain / avg_loss
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return float(np.clip(rsi, 0.0, 100.0))


def _swing_levels(closes: np.ndarray, current_price: float) -> Tuple[List[Level], List[Level]]:
    """
    Best-effort support/resistance from swing highs/lows on daily closes.
    """
    if len(closes) < 30:
        return [], []

    # Simple pivot detection (fractal-like)
    highs = []
    lows = []
    period = 2
    for i in range(period, len(closes) - period):
        window = closes[i - period : i + period + 1]
        if closes[i] == np.max(window):
            highs.append(float(closes[i]))
        if closes[i] == np.min(window):
            lows.append(float(closes[i]))

    # De-dupe by binning within tolerance
    tol = max(0.001, current_price * 0.002)  # ~0.2%

    def cluster(levels: List[float], kind: Literal["support", "resistance"]) -> List[Level]:
        levels_sorted = sorted(levels)
        clusters: List[List[float]] = []
        for lv in levels_sorted:
            if not clusters or abs(lv - np.mean(clusters[-1])) > tol:
                clusters.append([lv])
            else:
                clusters[-1].append(lv)
        out: List[Level] = []
        for c in clusters:
            price = float(np.mean(c))
            hits = len(c)
            strength = float(min(1.0, hits / 6.0))
            out.append(Level(price=price, kind=kind, hits=hits, strength=strength))
        return out

    supports = cluster(lows, "support")
    resistances = cluster(highs, "resistance")

    # pick nearest 3 below/above current
    supports = sorted([s for s in supports if s.price <= current_price], key=lambda x: current_price - x.price)[:3]
    resistances = sorted([r for r in resistances if r.price >= current_price], key=lambda x: x.price - current_price)[:3]
    return supports, resistances


async def compute_ta_snapshot(symbol: str, limit: int = 220) -> dict:
    """
    Compute TA snapshot from live (latest) price + EOD daily candles.
    """
    eod_rows = await fetch_eod_candles(symbol, limit=limit)
    closes = np.array([r["close"] for r in eod_rows], dtype=float) if eod_rows else np.array([], dtype=float)

    live = await fetch_latest_price(symbol)
    current_price = float(live) if live is not None else (float(closes[-1]) if len(closes) else 0.0)

    ema20 = _ema(closes[-60:], 20) if len(closes) else 0.0
    ema50 = _ema(closes[-120:], 50) if len(closes) else 0.0
    ema200 = _ema(closes[-260:], 200) if len(closes) else 0.0
    rsi14 = _rsi(closes, 14) if len(closes) else 50.0

    # Trend heuristic from 20d return
    trend: Trend = "NEUTRAL"
    if len(closes) >= 21:
        ret20 = (closes[-1] - closes[-21]) / max(1e-9, closes[-21])
        if ret20 > 0.02:
            trend = "BULLISH"
        elif ret20 < -0.02:
            trend = "BEARISH"

    supports, resistances = _swing_levels(closes, current_price)

    prev_close = float(closes[-2]) if len(closes) >= 2 else None
    last_close = float(closes[-1]) if len(closes) else None
    
    # TradingView-style % change: (current_price - previous_close) / previous_close * 100
    # This gives the real-time intraday change, not just yesterday's close vs day before
    change_pct = None
    if prev_close and current_price:
        change_pct = float(((current_price - prev_close) / prev_close) * 100.0)

    def _safe_float(v):
        if v is None:
            return None
        import math
        try:
            f = float(v)
            if math.isnan(f) or math.isinf(f):
                return None
            return f
        except (ValueError, TypeError):
            return None

    return {
        "symbol": symbol,
        "current_price": _safe_float(current_price),
        "last_close": _safe_float(last_close),
        "prev_close": _safe_float(prev_close),
        "change_pct": _safe_float(change_pct),
        "ema": {
            "ema20": _safe_float(ema20), 
            "ema50": _safe_float(ema50), 
            "ema200": _safe_float(ema200)
        },
        "rsi14": _safe_float(rsi14),
        "trend": trend,
        "supports": [{"price": _safe_float(s.price), "kind": s.kind, "hits": s.hits, "strength": _safe_float(s.strength)} for s in supports],
        "resistances": [{"price": _safe_float(r.price), "kind": r.kind, "hits": r.hits, "strength": _safe_float(r.strength)} for r in resistances],
    }



