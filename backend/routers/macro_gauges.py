"""
Macro Gauges — Hero-strip indicators for the dashboard.
========================================================
Aggregates four high-impact macro instruments into a single endpoint optimised
for the front-page speedometer strip:

    1. DXY Pulse           — USD strength z-score (90d)
    2. VIX Fear Gauge      — Volatility regime
    3. Yield-Curve Spread  — US10Y - US3M term spread
    4. Risk-On / Off Ratio — SPY / GLD ratio z-score (90d)

The values are computed from the in-memory `macro_data_service` cache so this
endpoint is essentially free (no extra Yahoo calls). Each gauge ships with
front-end-ready metadata: needle position (0–100), risk band, color, and a
human-readable tooltip explaining direction effects on EUR/USD, XAU, NDX, etc.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import numpy as np
from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/macro-gauges", tags=["macro-gauges"])


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _safe_zscore(series, window: int = 90) -> Optional[float]:
    try:
        s = series.dropna()
        if len(s) < 20:
            return None
        recent = s.iloc[-window:] if len(s) > window else s
        mu = float(recent.mean())
        sigma = float(recent.std(ddof=1))
        if sigma <= 0 or not np.isfinite(sigma):
            return None
        z = (float(s.iloc[-1]) - mu) / sigma
        return float(np.clip(z, -3.5, 3.5))
    except Exception:
        return None


def _z_to_score(z: float) -> float:
    """Map z-score in [-3, +3] → [0, 100], 50 = neutral."""
    return float(np.clip(50 + (z / 3.0) * 50, 0, 100))


def _band_for_z(z: Optional[float], reverse: bool = False) -> Dict[str, str]:
    """Color/level mapping for a z-score gauge."""
    if z is None:
        return {"level": "UNKNOWN", "color": "#6b7280"}
    az = abs(z)
    if az < 0.5:
        return {"level": "NEUTRAL", "color": "#16a34a"}
    if az < 1.0:
        return {"level": "ELEVATED", "color": "#eab308"}
    if az < 1.75:
        return {"level": "WARNING", "color": "#f59e0b"}
    if az < 2.5:
        return {"level": "HIGH", "color": "#ea580c"}
    return {"level": "EXTREME", "color": "#dc2626"}


# ─── Gauge builders ───────────────────────────────────────────────────────────

def _build_dxy() -> Dict[str, Any]:
    """USD Dollar Index — 90-day z-score. >+1σ = strong USD = bearish XAU/EUR/risk."""
    from services import macro_data_service as macro

    df = macro.get_history("DXY", "D1")
    out: Dict[str, Any] = {
        "key": "dxy",
        "label": "DXY Pulse",
        "subtitle": "USD Strength",
    }
    if df is None or df.empty:
        out.update({"status": "loading", "score": 50, "value": None, "z_score": None,
                    "level": "UNKNOWN", "color": "#6b7280",
                    "tooltip": _dxy_tooltip(None, None)})
        return out

    last = float(df["close"].iloc[-1])
    z = _safe_zscore(df["close"])
    band = _band_for_z(z)
    score = _z_to_score(z) if z is not None else 50

    out.update({
        "status": "live",
        "value": round(last, 2),
        "z_score": round(z, 2) if z is not None else None,
        "score": round(score, 1),
        "level": band["level"],
        "color": band["color"],
        "tooltip": _dxy_tooltip(last, z),
    })
    return out


def _dxy_tooltip(value: Optional[float], z: Optional[float]) -> Dict[str, Any]:
    if z is None:
        return {
            "title": "USD Dollar Index (DXY)",
            "summary": "USD strength versus a basket of major currencies.",
            "interpretation": "Loading historical baseline…",
            "thresholds": [],
        }
    if z > 1.5:
        bias = "USD strongly bid → EUR/USD short, XAU pressured, NDX growth-stocks under repricing risk."
    elif z > 0.5:
        bias = "USD firm → mild headwind for gold and risk currencies."
    elif z < -1.5:
        bias = "USD weakening sharply → tailwind for XAU, EUR/USD, NDX, EM."
    elif z < -0.5:
        bias = "USD soft → modest support for risk and commodities."
    else:
        bias = "USD near 90-day mean → low macro USD bias, trend-followers stand down."
    return {
        "title": "USD Dollar Index (DXY)",
        "summary": "Dollar strength — Forex regime filter #1. Inverse to gold, oil, EUR/USD.",
        "interpretation": bias,
        "thresholds": [
            {"range": "z < -1σ", "label": "USD WEAK",   "effect": "Risk-on, XAU/EUR long bias"},
            {"range": "|z| < 1σ", "label": "NEUTRAL",   "effect": "No macro USD bias"},
            {"range": "z > +1σ", "label": "USD STRONG", "effect": "XAU/EUR short bias, NDX caution"},
        ],
    }


def _build_vix() -> Dict[str, Any]:
    """VIX — fear gauge. Raw value bucketed into calm/normal/elevated/panic."""
    from services import macro_data_service as macro

    df = macro.get_history("VIX", "D1")
    out: Dict[str, Any] = {
        "key": "vix",
        "label": "VIX Fear Gauge",
        "subtitle": "Volatility Regime",
    }
    if df is None or df.empty:
        out.update({"status": "loading", "score": 0, "value": None,
                    "level": "UNKNOWN", "color": "#6b7280",
                    "tooltip": _vix_tooltip(None)})
        return out

    last = float(df["close"].iloc[-1])
    # Map VIX 10–50 → 0–100 (linearly clipped)
    score = float(np.clip((last - 10.0) / 40.0 * 100, 0, 100))
    if last < 15:
        level, color = "CALM", "#16a34a"
    elif last < 20:
        level, color = "NORMAL", "#84cc16"
    elif last < 25:
        level, color = "ELEVATED", "#eab308"
    elif last < 35:
        level, color = "WARNING", "#f59e0b"
    elif last < 45:
        level, color = "HIGH", "#ea580c"
    else:
        level, color = "PANIC", "#dc2626"

    out.update({
        "status": "live",
        "value": round(last, 2),
        "score": round(score, 1),
        "level": level,
        "color": color,
        "tooltip": _vix_tooltip(last),
    })
    return out


def _vix_tooltip(value: Optional[float]) -> Dict[str, Any]:
    if value is None:
        return {"title": "VIX (CBOE Volatility Index)",
                "summary": "30-day implied volatility on S&P 500 — the fear gauge.",
                "interpretation": "Loading…",
                "thresholds": []}
    if value < 15:
        bias = "Calm tape — trend strategies favored, stops can be tight, NDX/SPX upside bias."
    elif value < 20:
        bias = "Normal regime — standard position sizing, mean-reversion edges work."
    elif value < 25:
        bias = "Elevated — rallies fragile, widen stops on indices, XAU bid increasing."
    elif value < 35:
        bias = "Warning — risk-off probable, reduce leverage, XAU/USD long bias, EUR/USD volatile."
    elif value < 45:
        bias = "High stress — defensive only, indices short-bias, gold flight-to-quality."
    else:
        bias = "PANIC — full risk-off, cover shorts may be sharp, expect dollar strength + USD funding squeeze."
    return {
        "title": "VIX (CBOE Volatility Index)",
        "summary": "30-day implied volatility on S&P 500 — risk-on / risk-off master switch.",
        "interpretation": bias,
        "thresholds": [
            {"range": "< 15",  "label": "CALM",     "effect": "Trend long bias on indices"},
            {"range": "15-20", "label": "NORMAL",   "effect": "Standard sizing"},
            {"range": "20-25", "label": "ELEVATED", "effect": "Rallies fragile, widen stops"},
            {"range": "25-35", "label": "WARNING",  "effect": "De-risk; XAU long bias"},
            {"range": "> 35",  "label": "PANIC",    "effect": "Defensive only; gold/USD bid"},
        ],
    }


def _build_yield_curve() -> Dict[str, Any]:
    """US10Y - US3M term spread. Negative = inverted = recession warning + gold bias."""
    from services import macro_data_service as macro

    df10 = macro.get_history("US10Y", "D1")
    df3m = macro.get_history("US3M", "D1")
    out: Dict[str, Any] = {
        "key": "yield_curve",
        "label": "Yield Curve",
        "subtitle": "10Y - 3M Spread",
    }
    if df10 is None or df3m is None or df10.empty or df3m.empty:
        out.update({"status": "loading", "score": 50, "value": None, "spread": None,
                    "level": "UNKNOWN", "color": "#6b7280",
                    "tooltip": _yield_tooltip(None)})
        return out

    # ^TNX and ^IRX are quoted as percent × 10 by Yahoo (e.g. 4.5% = 45). Both are quoted the
    # same way so the spread is consistent regardless of scale.
    y10 = float(df10["close"].iloc[-1])
    y3m = float(df3m["close"].iloc[-1])
    spread = y10 - y3m
    # Normalise typical spread range -150bp..+300bp → 0..100, with 0bp = 33 (inversion zone red)
    score = float(np.clip((spread + 1.5) / 4.5 * 100, 0, 100))
    if spread < -0.75:
        level, color = "DEEP INVERT", "#dc2626"
    elif spread < -0.10:
        level, color = "INVERTED", "#ea580c"
    elif spread < 0.50:
        level, color = "FLAT", "#eab308"
    elif spread < 1.50:
        level, color = "NORMAL", "#16a34a"
    else:
        level, color = "STEEP", "#22c55e"

    out.update({
        "status": "live",
        "value": round(spread, 2),
        "spread": round(spread, 2),
        "score": round(score, 1),
        "level": level,
        "color": color,
        "tooltip": _yield_tooltip(spread),
    })
    return out


def _yield_tooltip(spread: Optional[float]) -> Dict[str, Any]:
    if spread is None:
        return {"title": "US Yield Curve (10Y - 3M)",
                "summary": "Treasury term spread — leading recession indicator.",
                "interpretation": "Loading curve…",
                "thresholds": []}
    if spread < -0.75:
        bias = "Deep inversion — recession risk extreme, XAU long bias, indices late-cycle, USD eventually peaks."
    elif spread < -0.10:
        bias = "Curve inverted — recession watch active. XAU bid, defensives over cyclicals, oil demand at risk."
    elif spread < 0.50:
        bias = "Curve flat — late-cycle. Trade rotations carefully; growth slowdown priced in."
    elif spread < 1.50:
        bias = "Healthy positive slope — growth regime, indices trend long-bias, XAU range-trade."
    else:
        bias = "Steep curve — early-cycle / reflation, equities long-bias, USD weakening, commodities tailwind."
    return {
        "title": "US Yield Curve (10Y - 3M)",
        "summary": "Treasury term spread (in pct points × 10 from Yahoo). Most reliable recession signal historically.",
        "interpretation": bias,
        "thresholds": [
            {"range": "> +1.5%", "label": "STEEP",       "effect": "Reflation, equities long, USD ↓"},
            {"range": "+0.5% to +1.5%", "label": "NORMAL", "effect": "Growth regime, trend strategies"},
            {"range": "0% to +0.5%",   "label": "FLAT",  "effect": "Late cycle, rotate to defensives"},
            {"range": "< 0%",         "label": "INVERTED", "effect": "Recession watch, XAU long bias"},
            {"range": "< -0.75%",     "label": "DEEP INVERT", "effect": "High recession probability"},
        ],
    }


def _build_risk_ratio() -> Dict[str, Any]:
    """SPY / GLD ratio — risk-on numerator over risk-off denominator. Z-score 90d."""
    from services import macro_data_service as macro

    spy = macro.get_history("SPY", "D1")
    gld = macro.get_history("GLD", "D1")
    out: Dict[str, Any] = {
        "key": "risk_ratio",
        "label": "Risk-On / Off",
        "subtitle": "SPY / GLD Ratio",
    }
    if spy is None or gld is None or spy.empty or gld.empty:
        out.update({"status": "loading", "score": 50, "value": None, "z_score": None,
                    "level": "UNKNOWN", "color": "#6b7280",
                    "tooltip": _risk_tooltip(None, None)})
        return out

    # Align by date intersection
    common = spy.index.intersection(gld.index)
    if len(common) < 30:
        out.update({"status": "loading", "score": 50, "value": None, "z_score": None,
                    "level": "UNKNOWN", "color": "#6b7280",
                    "tooltip": _risk_tooltip(None, None)})
        return out
    ratio = (spy["close"].loc[common] / gld["close"].loc[common]).dropna()
    last = float(ratio.iloc[-1])
    z = _safe_zscore(ratio)
    band = _band_for_z(z)
    score = _z_to_score(z) if z is not None else 50

    out.update({
        "status": "live",
        "value": round(last, 3),
        "z_score": round(z, 2) if z is not None else None,
        "score": round(score, 1),
        "level": band["level"],
        "color": band["color"],
        "tooltip": _risk_tooltip(last, z),
    })
    return out


def _risk_tooltip(value: Optional[float], z: Optional[float]) -> Dict[str, Any]:
    if z is None:
        return {"title": "Risk-On / Risk-Off Ratio (SPY / GLD)",
                "summary": "Equities-over-gold ratio — captures investor risk appetite.",
                "interpretation": "Loading…",
                "thresholds": []}
    if z > 1.5:
        bias = "Aggressive risk-on — equities outperform gold strongly, NDX/SPX trend-long bias, XAU pressured."
    elif z > 0.5:
        bias = "Risk-on tilt — equity upside, gold underperforms."
    elif z < -1.5:
        bias = "Aggressive risk-off — gold outperforms equities, defensive flow, NDX short-bias."
    elif z < -0.5:
        bias = "Risk-off tilt — gold/treasuries bid, equity rallies fragile."
    else:
        bias = "Neutral — no dominant risk regime, trade by symbol-specific signals."
    return {
        "title": "Risk-On / Risk-Off Ratio (SPY / GLD)",
        "summary": "Equity-vs-gold relative performance. Z-score over 90 days.",
        "interpretation": bias,
        "thresholds": [
            {"range": "z > +1σ",  "label": "RISK-ON",  "effect": "NDX/SPX long, XAU short bias"},
            {"range": "|z| < 1σ", "label": "NEUTRAL",  "effect": "No dominant regime"},
            {"range": "z < -1σ",  "label": "RISK-OFF", "effect": "XAU/USD long, indices defensive"},
        ],
    }


# ─── Endpoint ─────────────────────────────────────────────────────────────────

@router.get("")
async def get_macro_gauges() -> Dict[str, Any]:
    """Return the four hero-strip macro gauges in a single payload."""
    try:
        from services import macro_data_service as macro
        # Lazy-start so cold endpoints work; macro service is idempotent.
        if not macro.is_ready():
            await macro.ensure_started()
    except Exception as e:
        logger.warning("macro service start failed: %s", e)

    gauges: List[Dict[str, Any]] = []
    for builder in (_build_dxy, _build_vix, _build_yield_curve, _build_risk_ratio):
        try:
            gauges.append(builder())
        except Exception as e:
            logger.exception("macro gauge builder failed: %s", e)
            gauges.append({"key": builder.__name__, "status": "error", "error": str(e)})

    return {"success": True, "gauges": gauges}
