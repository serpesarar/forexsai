"""
Macro Context Service — single source of truth for macro overlays.
==================================================================
Aggregates the four hero-strip macro gauges (DXY, VIX, Yield Curve, Risk-On
ratio) plus the Pandemic Sensitivity Index into a unified per-symbol context:

    1. Per-symbol confidence adjustment (capped at ±15 absolute points)
    2. Commentary lines (Turkish-friendly, 1-3 entries) so any model can append
       them to its `decision_notes` for analyst-grade transparency
    3. Raw signals list for UI / debugging

Design rules (mirror the PSI overlay rules — never destabilise existing
fusion):
  - Macro never flips a signal direction (BUY/SELL/HOLD).
  - Each gauge contributes at most ±4 confidence points before symmetrisation,
    and the total is hard-capped at ±15.
  - Per-symbol/per-direction asymmetry — penalising risk-on longs in a
    risk-off regime is heavier than rewarding shorts, etc.
  - Any internal failure returns a zero-impact stub so callers never crash.

Public API
----------
    compute_macro_context(symbol, direction) -> Dict
    commentary_lines(symbol, direction)      -> List[str]   (informational only)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# ─── Hard caps ───────────────────────────────────────────────────────────────

PER_GAUGE_MAX = 4.0           # max absolute points contributed by ONE gauge
TOTAL_MAX = 15.0              # absolute hard cap on the sum (matches PSI rail)
SUPPORTED_SYMBOLS = ("NDX.INDX", "GDAXI.INDX", "XAUUSD", "USOIL.FOREX")


# ─── Per-symbol bias matrix ──────────────────────────────────────────────────
# Each entry is (buy_multiplier, sell_multiplier) ∈ [-1, +1].
# Multipliers are scaled by the gauge's intensity (0..1) and the per-gauge max.
# Negative buy_multiplier = penalise longs when this gauge is in its hot state.
#
# "Hot state" definitions per gauge:
#     DXY        — z-score |z| > 1   (strong/weak USD)
#     VIX        — value > 25         (elevated fear)
#     YIELD      — spread < 0 OR > 1.5% (inversion vs steep)
#     RISK_RATIO — z-score |z| > 1   (extreme risk-on/off)
#     PSI        — handled by pandemic_sensitivity_service.compute_meta_adjustment

# DXY: bias when USD STRONG (z > +1). Mirror sign for weak USD.
_BIAS_DXY_STRONG: Dict[str, Tuple[float, float]] = {
    "NDX.INDX":    (-0.55, +0.35),
    "GDAXI.INDX":  (-0.45, +0.30),
    "XAUUSD":      (-1.00, +0.70),
    "USOIL.FOREX": (-0.70, +0.45),
}

# VIX: bias when VIX ELEVATED (>25). Calm VIX (<15) gives a tiny opposite nudge.
_BIAS_VIX_HOT: Dict[str, Tuple[float, float]] = {
    "NDX.INDX":    (-1.00, +0.55),
    "GDAXI.INDX":  (-0.95, +0.55),
    "XAUUSD":      (+0.80, -0.50),
    "USOIL.FOREX": (-0.40, +0.25),
}

# Yield curve INVERTED (<0bp). Steep curve (> +1.5%) flips signs (less aggressively).
_BIAS_YIELD_INVERTED: Dict[str, Tuple[float, float]] = {
    "NDX.INDX":    (-0.70, +0.50),
    "GDAXI.INDX":  (-0.65, +0.45),
    "XAUUSD":      (+0.90, -0.50),
    "USOIL.FOREX": (-0.60, +0.40),
}
_BIAS_YIELD_STEEP: Dict[str, Tuple[float, float]] = {
    "NDX.INDX":    (+0.40, -0.20),
    "GDAXI.INDX":  (+0.40, -0.20),
    "XAUUSD":      (-0.30, +0.20),
    "USOIL.FOREX": (+0.50, -0.25),
}

# Risk-On (SPY/GLD z > +1). Risk-Off mirrors signs.
_BIAS_RISK_ON: Dict[str, Tuple[float, float]] = {
    "NDX.INDX":    (+0.55, -0.30),
    "GDAXI.INDX":  (+0.50, -0.30),
    "XAUUSD":      (-0.65, +0.40),
    "USOIL.FOREX": (+0.35, -0.20),
}


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _scale_z(z: float, soft: float = 1.0, hard: float = 2.5) -> float:
    """Map |z| in [soft..hard] to intensity in [0..1]. Below soft = 0."""
    az = abs(z)
    if az <= soft:
        return 0.0
    return float(min(1.0, (az - soft) / (hard - soft)))


def _scale_linear(value: float, lo: float, hi: float) -> float:
    """Clamp value into [lo..hi] then map to [0..1]."""
    if hi == lo:
        return 0.0
    t = (value - lo) / (hi - lo)
    return float(max(0.0, min(1.0, t)))


def _mult_for(bias_table: Dict[str, Tuple[float, float]], symbol: str, direction: str) -> float:
    pair = bias_table.get(symbol)
    if pair is None:
        return 0.0
    return pair[0] if direction == "BUY" else pair[1]


@dataclass
class GaugeContribution:
    gauge: str                 # "dxy" / "vix" / "yield" / "risk_ratio" / "psi"
    state: str                 # human-readable state (e.g. "USD STRONG", "INVERTED")
    intensity: float           # 0..1
    delta: float               # signed contribution to confidence (already scaled)
    note: str                  # short Turkish/English commentary line


# ─── Per-gauge contributions ─────────────────────────────────────────────────

def _contrib_dxy(symbol: str, direction: str) -> Optional[GaugeContribution]:
    try:
        from services import macro_data_service as macro
        df = macro.get_history("DXY", "D1")
        if df is None or len(df) < 30:
            return None
        s = df["close"].dropna()
        recent = s.iloc[-90:] if len(s) > 90 else s
        sigma = float(recent.std(ddof=1))
        mu = float(recent.mean())
        if sigma <= 0:
            return None
        z = (float(s.iloc[-1]) - mu) / sigma

        intensity = _scale_z(z)
        if intensity <= 0:
            return None
        # When USD weak, multiplier sign flips relative to STRONG table.
        sign = 1.0 if z > 0 else -1.0
        mult = sign * _mult_for(_BIAS_DXY_STRONG, symbol, direction)
        delta = float(np.clip(intensity * mult * PER_GAUGE_MAX, -PER_GAUGE_MAX, PER_GAUGE_MAX))
        if abs(delta) < 0.25:
            return None
        state = "USD STRONG" if z > 0 else "USD WEAK"
        if delta > 0:
            note = f"DXY {state} (z={z:+.1f}σ) → {symbol} {direction} desteği +{delta:.1f}"
        else:
            note = f"DXY {state} (z={z:+.1f}σ) → {symbol} {direction} aleyhine {delta:.1f}"
        return GaugeContribution("dxy", state, intensity, delta, note)
    except Exception as e:
        logger.debug("dxy contrib failed: %s", e)
        return None


def _contrib_vix(symbol: str, direction: str) -> Optional[GaugeContribution]:
    try:
        from services import macro_data_service as macro
        df = macro.get_history("VIX", "D1")
        if df is None or df.empty:
            return None
        vix = float(df["close"].iloc[-1])
        # Hot state: VIX > 25, scaled to 1.0 by VIX = 40
        if vix >= 15:
            intensity = _scale_linear(vix, 25.0, 40.0)
            sign = 1.0
            state = "VIX ELEVATED" if vix >= 25 else "VIX NORMAL"
            if vix < 25:
                # Calm regime gets a tiny opposite-direction nudge below 15
                if vix > 15:
                    return None
        else:
            intensity = _scale_linear(15.0 - vix, 0.0, 5.0)
            sign = -1.0
            state = "VIX CALM"

        if intensity <= 0:
            return None
        mult = _mult_for(_BIAS_VIX_HOT, symbol, direction) * sign
        delta = float(np.clip(intensity * mult * PER_GAUGE_MAX, -PER_GAUGE_MAX, PER_GAUGE_MAX))
        if abs(delta) < 0.25:
            return None
        if delta > 0:
            note = f"VIX {vix:.1f} ({state}) → {symbol} {direction} desteği +{delta:.1f}"
        else:
            note = f"VIX {vix:.1f} ({state}) → {symbol} {direction} aleyhine {delta:.1f}"
        return GaugeContribution("vix", state, intensity, delta, note)
    except Exception as e:
        logger.debug("vix contrib failed: %s", e)
        return None


def _contrib_yield(symbol: str, direction: str) -> Optional[GaugeContribution]:
    try:
        from services import macro_data_service as macro
        df10 = macro.get_history("US10Y", "D1")
        df3m = macro.get_history("US3M", "D1")
        if df10 is None or df3m is None or df10.empty or df3m.empty:
            return None
        y10 = float(df10["close"].iloc[-1])
        y3m = float(df3m["close"].iloc[-1])
        spread = y10 - y3m

        if spread < 0:
            intensity = _scale_linear(-spread, 0.0, 1.5)
            mult = _mult_for(_BIAS_YIELD_INVERTED, symbol, direction)
            state = "INVERTED"
        elif spread > 1.5:
            intensity = _scale_linear(spread, 1.5, 3.0)
            mult = _mult_for(_BIAS_YIELD_STEEP, symbol, direction)
            state = "STEEP"
        else:
            return None  # normal-flat = no overlay

        if intensity <= 0:
            return None
        delta = float(np.clip(intensity * mult * PER_GAUGE_MAX, -PER_GAUGE_MAX, PER_GAUGE_MAX))
        if abs(delta) < 0.25:
            return None
        if delta > 0:
            note = f"Yield curve {state} (spread {spread:+.2f}%) → {symbol} {direction} desteği +{delta:.1f}"
        else:
            note = f"Yield curve {state} (spread {spread:+.2f}%) → {symbol} {direction} aleyhine {delta:.1f}"
        return GaugeContribution("yield", state, intensity, delta, note)
    except Exception as e:
        logger.debug("yield contrib failed: %s", e)
        return None


def _contrib_risk_ratio(symbol: str, direction: str) -> Optional[GaugeContribution]:
    try:
        from services import macro_data_service as macro
        spy = macro.get_history("SPY", "D1")
        gld = macro.get_history("GLD", "D1")
        if spy is None or gld is None or spy.empty or gld.empty:
            return None
        common = spy.index.intersection(gld.index)
        if len(common) < 30:
            return None
        ratio = (spy["close"].loc[common] / gld["close"].loc[common]).dropna()
        recent = ratio.iloc[-90:] if len(ratio) > 90 else ratio
        sigma = float(recent.std(ddof=1))
        mu = float(recent.mean())
        if sigma <= 0:
            return None
        z = (float(ratio.iloc[-1]) - mu) / sigma

        intensity = _scale_z(z)
        if intensity <= 0:
            return None
        sign = 1.0 if z > 0 else -1.0
        mult = _mult_for(_BIAS_RISK_ON, symbol, direction) * sign
        delta = float(np.clip(intensity * mult * PER_GAUGE_MAX, -PER_GAUGE_MAX, PER_GAUGE_MAX))
        if abs(delta) < 0.25:
            return None
        state = "RISK-ON" if z > 0 else "RISK-OFF"
        if delta > 0:
            note = f"Risk-On/Off {state} (z={z:+.1f}σ) → {symbol} {direction} desteği +{delta:.1f}"
        else:
            note = f"Risk-On/Off {state} (z={z:+.1f}σ) → {symbol} {direction} aleyhine {delta:.1f}"
        return GaugeContribution("risk_ratio", state, intensity, delta, note)
    except Exception as e:
        logger.debug("risk_ratio contrib failed: %s", e)
        return None


def _contrib_psi(symbol: str, direction: str) -> Optional[GaugeContribution]:
    try:
        from services.pandemic_sensitivity_service import compute_meta_adjustment
        info = compute_meta_adjustment(symbol, direction)
        delta = float(info.get("adjustment", 0.0) or 0.0)
        if abs(delta) < 0.25 or not info.get("applied"):
            return None
        risk = str(info.get("risk_level", "NORMAL"))
        # Cap PSI contribution by per-gauge max (PSI internal cap is 15 → keep aligned)
        delta = float(np.clip(delta, -PER_GAUGE_MAX, PER_GAUGE_MAX))
        intensity = min(1.0, abs(delta) / PER_GAUGE_MAX)
        sign = "+" if delta > 0 else ""
        note = f"PSI {info.get('psi_score', 0):.0f} ({risk}) → {symbol} {direction} {sign}{delta:.1f}"
        return GaugeContribution("psi", risk, intensity, delta, note)
    except Exception as e:
        logger.debug("psi contrib failed: %s", e)
        return None


# ─── Public API ──────────────────────────────────────────────────────────────

def compute_macro_context(symbol: str, direction: str) -> Dict[str, Any]:
    """
    Build the full macro context for (symbol, direction).

    Returns dict with:
        adjustment   (float)   — total signed delta, capped at ±TOTAL_MAX
        signals      (list)    — per-gauge contributions (gauge, state, delta, note)
        commentary   (list)    — top 1-3 commentary lines (for decision_notes)
        rationale    (str)     — single-line summary suitable for logs
        applied      (bool)    — True if |adjustment| ≥ 0.5
    """
    stub = {
        "adjustment": 0.0,
        "signals": [],
        "commentary": [],
        "rationale": "Macro overlay inactive",
        "applied": False,
    }
    if direction not in ("BUY", "SELL"):
        return stub
    if symbol not in SUPPORTED_SYMBOLS:
        return stub

    contribs: List[GaugeContribution] = []
    for fn in (_contrib_dxy, _contrib_vix, _contrib_yield, _contrib_risk_ratio, _contrib_psi):
        c = fn(symbol, direction)
        if c is not None:
            contribs.append(c)

    if not contribs:
        return stub

    raw_total = sum(c.delta for c in contribs)
    total = float(np.clip(raw_total, -TOTAL_MAX, TOTAL_MAX))

    # Sort by absolute impact for commentary ordering
    contribs_sorted = sorted(contribs, key=lambda c: abs(c.delta), reverse=True)
    commentary = [c.note for c in contribs_sorted[:3]]

    sign = "+" if total > 0 else ""
    rationale = (
        f"Macro overlay {sign}{total:.1f} on {symbol} {direction} "
        f"({len(contribs)} gauges: " +
        ", ".join(f"{c.gauge}{'+' if c.delta > 0 else ''}{c.delta:.1f}" for c in contribs_sorted)
        + ")"
    )

    return {
        "adjustment": round(total, 2),
        "raw_adjustment": round(raw_total, 2),
        "signals": [
            {
                "gauge": c.gauge,
                "state": c.state,
                "intensity": round(c.intensity, 3),
                "delta": round(c.delta, 2),
                "note": c.note,
            }
            for c in contribs_sorted
        ],
        "commentary": commentary,
        "rationale": rationale,
        "applied": abs(total) >= 0.5,
    }


def commentary_lines(symbol: str, direction: str, max_lines: int = 2) -> List[str]:
    """
    Lightweight helper for the rule-based models (Pulse 1/2/3, EMEL).
    Returns the top-N commentary lines for the active macro context. Safe to
    call from anywhere — never raises, never blocks (uses cached snapshots).
    """
    try:
        ctx = compute_macro_context(symbol, direction)
        if not ctx.get("applied"):
            return []
        lines = list(ctx.get("commentary", []))[:max_lines]
        return lines
    except Exception as e:
        logger.debug("commentary_lines failed for %s/%s: %s", symbol, direction, e)
        return []
