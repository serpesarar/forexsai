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

# BTC vs NDX correlation — when BTC underperforms while NDX rallies, that's
# a "risk-on internal divergence" warning (the speculative tail is leading
# the broader risk-on flow). For NDX longs this is bearish; for XAU longs
# this is slightly bullish (defensive flow).
_BIAS_BTC_NDX_DIVERGENCE: Dict[str, Tuple[float, float]] = {
    "NDX.INDX":    (-0.45, +0.25),
    "GDAXI.INDX":  (-0.20, +0.10),
    "XAUUSD":      (+0.30, -0.15),
    "USOIL.FOREX": (-0.15, +0.10),
}

# USD/JPY carry unwind — sharp DROP in USD/JPY usually triggers global
# risk-off (Aug 2024 reminded everyone). 3-day drop > 3% = warning state.
# Indices get hit, gold benefits, oil mildly bearish (demand fear).
_BIAS_CARRY_UNWIND: Dict[str, Tuple[float, float]] = {
    "NDX.INDX":    (-0.80, +0.45),
    "GDAXI.INDX":  (-0.70, +0.40),
    "XAUUSD":      (+0.65, -0.35),
    "USOIL.FOREX": (-0.45, +0.30),
}

# Copper/Gold — global growth proxy (China demand sensitive). Rising ratio
# = pro-growth / pro-cyclical. Useful especially for USOIL and DAX which
# are exposed to global industrial cycle.
_BIAS_COPPER_GOLD: Dict[str, Tuple[float, float]] = {
    "NDX.INDX":    (+0.25, -0.15),
    "GDAXI.INDX":  (+0.55, -0.30),
    "XAUUSD":      (-0.40, +0.25),
    "USOIL.FOREX": (+0.70, -0.35),
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
    """VIX overlay — dual-mode: own-history z-score + absolute thresholds.

    My market observation (2024-2026): the static VIX>25 "elevated" threshold
    is outdated. After 2020 the structural VIX baseline shifted lower
    (~15-18) thanks to 0DTE option flow compressing realized vol. A z-score
    against the same instrument's 252-day window catches "elevated FOR THIS
    REGIME" while the absolute >25 still fires for tail events. Both must
    agree before we issue a strong signal.

    Calm VIX is intentionally treated as a complacency signal for equities,
    not a tailwind — historically the lowest VIX prints precede corrections
    (Q4 2019, Dec 2017). Magnitude is small (-0.5 vs -1.0 for HOT) because
    the calm-precedes-storm timing is loose.
    """
    try:
        from services import macro_data_service as macro
        df = macro.get_history("VIX", "D1")
        if df is None or len(df) < 60:
            return None
        s = df["close"].dropna()
        vix = float(s.iloc[-1])
        window = s.iloc[-252:] if len(s) >= 252 else s.iloc[-90:]
        mu = float(window.mean())
        sigma = float(window.std(ddof=1))
        z = (vix - mu) / sigma if sigma > 0 else 0.0

        # Adaptive hot detection: BOTH z>+1 AND vix>=22 confirm "elevated for
        # this regime". A z-score alone in a calm year would spam false hot.
        hot = z >= 1.0 and vix >= 22
        very_hot = vix >= 30  # absolute backstop — always hot regardless of z

        if very_hot or hot:
            base_intensity = _scale_linear(vix, 22.0, 40.0)
            z_intensity = _scale_z(z, soft=1.0, hard=3.0)
            intensity = max(base_intensity, z_intensity)
            sign = 1.0
            state = f"VIX HOT (z={z:+.1f}σ)" if very_hot else f"VIX ELEVATED (z={z:+.1f}σ)"
        elif z <= -1.0 or vix <= 13:
            # Complacency mode — small opposite nudge (penalize equity longs
            # mildly, favour vol hedges/gold slightly). NEVER large because
            # the calm-before-storm signal is noisy.
            intensity = max(_scale_linear(-z, 1.0, 2.5), _scale_linear(13 - vix, 0.0, 4.0)) * 0.5
            sign = -1.0
            state = f"VIX CALM (complacency, z={z:+.1f}σ)"
        else:
            return None  # normal regime — no overlay

        if intensity <= 0:
            return None
        mult = _mult_for(_BIAS_VIX_HOT, symbol, direction) * sign
        delta = float(np.clip(intensity * mult * PER_GAUGE_MAX, -PER_GAUGE_MAX, PER_GAUGE_MAX))
        if abs(delta) < 0.25:
            return None
        direction_word = "desteği" if delta > 0 else "aleyhine"
        sign_str = "+" if delta > 0 else ""
        note = f"VIX {vix:.1f} ({state}) → {symbol} {direction} {direction_word} {sign_str}{delta:.1f}"
        return GaugeContribution("vix", state, intensity, delta, note)
    except Exception as e:
        logger.debug("vix contrib failed: %s", e)
        return None


def _contrib_yield(symbol: str, direction: str) -> Optional[GaugeContribution]:
    """Yield curve overlay — combines slope (10Y-3M) with absolute level (10Y).

    My market observation (2024-2026): the 2022-2023 inversion gave many
    false-positive recession warnings; just the slope isn't enough anymore.

    1) Use 10Y-3M (NY Fed's preferred — Estrella & Mishkin 1996) as slope.
       Fall back to 2Y-10Y if 3M series unavailable.

    2) Add ABSOLUTE-LEVEL gate: 10Y > 5% compresses equity multiples
       regardless of curve shape (Cost-of-Capital channel). Hits equity
       longs (NDX/DAX) most.

    3) Shrinkage: if slope+level both fire same sign, take stronger leg /
       √2 to avoid double-counting the same recession/disinflation theme.
    """
    try:
        from services import macro_data_service as macro
        df10 = macro.get_history("US10Y", "D1")
        if df10 is None or df10.empty:
            return None
        y10 = float(df10["close"].iloc[-1])

        # Slope: prefer 10Y-3M, fall back to 10Y-2Y
        df3m = macro.get_history("US3M", "D1")
        short = None
        short_label = ""
        if df3m is not None and not df3m.empty:
            short = float(df3m["close"].iloc[-1])
            short_label = "3M"
        else:
            df2y = macro.get_history("US2Y", "D1")
            if df2y is not None and not df2y.empty:
                short = float(df2y["close"].iloc[-1])
                short_label = "2Y"
        spread = (y10 - short) if short is not None else 0.0

        slope_intensity = 0.0
        slope_mult = 0.0
        slope_state = ""
        if short is not None:
            if spread < 0:
                slope_intensity = _scale_linear(-spread, 0.0, 1.5)
                slope_mult = _mult_for(_BIAS_YIELD_INVERTED, symbol, direction)
                slope_state = f"INVERTED ({short_label})"
            elif spread > 1.5:
                slope_intensity = _scale_linear(spread, 1.5, 3.0)
                slope_mult = _mult_for(_BIAS_YIELD_STEEP, symbol, direction)
                slope_state = f"STEEP ({short_label})"

        # Absolute-level component
        level_intensity = 0.0
        level_mult = 0.0
        level_state = ""
        if y10 >= 5.0:
            level_intensity = _scale_linear(y10, 5.0, 6.5)
            level_buy_pen = {"NDX.INDX": -0.55, "GDAXI.INDX": -0.45,
                              "XAUUSD": -0.15, "USOIL.FOREX": -0.20}
            level_sell_bonus = {"NDX.INDX": +0.30, "GDAXI.INDX": +0.30,
                                 "XAUUSD": +0.20, "USOIL.FOREX": +0.15}
            level_mult = (level_buy_pen if direction == "BUY"
                          else level_sell_bonus).get(symbol, 0.0)
            level_state = f"10Y HIGH ({y10:.2f}%)"

        if slope_intensity <= 0 and level_intensity <= 0:
            return None

        slope_delta = slope_intensity * slope_mult
        level_delta = level_intensity * level_mult
        # Shrinkage when same sign
        if slope_delta * level_delta > 0:
            combined_mag = max(abs(slope_delta), abs(level_delta)) / (2 ** 0.5)
            combined = combined_mag * (1.0 if slope_delta >= 0 else -1.0)
        else:
            combined = slope_delta + level_delta

        delta = float(np.clip(combined * PER_GAUGE_MAX, -PER_GAUGE_MAX, PER_GAUGE_MAX))
        if abs(delta) < 0.25:
            return None
        state = " + ".join(p for p in (slope_state, level_state) if p) or "yield"
        direction_word = "desteği" if delta > 0 else "aleyhine"
        sign_str = "+" if delta > 0 else ""
        note = (f"Yield {state} (10Y={y10:.2f}%, spread={spread:+.2f}%) → "
                f"{symbol} {direction} {direction_word} {sign_str}{delta:.1f}")
        return GaugeContribution("yield", state, max(slope_intensity, level_intensity), delta, note)
    except Exception as e:
        logger.debug("yield contrib failed: %s", e)
        return None


def _contrib_risk_ratio(symbol: str, direction: str) -> Optional[GaugeContribution]:
    """Risk-On/Off overlay — combines equity-vs-gold (SPY/GLD) with credit
    (HYG/IEF) when both available.

    My market observation (2024-2026): SPY/GLD captures equity-vs-safehaven
    sentiment but misses CREDIT-RISK appetite, which often turns first.
    Institutional risk-parity desks watch HYG/IEF (high-yield-credit vs
    treasuries) — when HYG underperforms IEF before equity sells off,
    that's the early-warning that retail-flow indicators miss.

    Combined Z: average of the two available z-scores (using the most
    extreme magnitude as the displayed state). Both fire same sign →
    high conviction. Disagree → reduced signal (likely policy-driven
    rather than risk-driven, so shrink).
    """
    try:
        from services import macro_data_service as macro

        def _zscore_pair(num_sym: str, den_sym: str) -> Optional[float]:
            num = macro.get_history(num_sym, "D1")
            den = macro.get_history(den_sym, "D1")
            if num is None or den is None or num.empty or den.empty:
                return None
            common = num.index.intersection(den.index)
            if len(common) < 30:
                return None
            r = (num["close"].loc[common] / den["close"].loc[common]).dropna()
            recent = r.iloc[-90:] if len(r) > 90 else r
            sigma = float(recent.std(ddof=1))
            mu = float(recent.mean())
            if sigma <= 0:
                return None
            return (float(r.iloc[-1]) - mu) / sigma

        z_spygld = _zscore_pair("SPY", "GLD")
        z_hygief = _zscore_pair("HYG", "IEF")  # credit risk appetite

        zs = [z for z in (z_spygld, z_hygief) if z is not None]
        if not zs:
            return None

        # Both available + same sign → average (high conviction)
        # Disagree → use the larger magnitude × 0.5 (low conviction)
        if len(zs) == 2:
            if zs[0] * zs[1] > 0:
                z = (zs[0] + zs[1]) / 2.0
                detail = f"SPY/GLD={z_spygld:+.1f}σ, HYG/IEF={z_hygief:+.1f}σ (aligned)"
            else:
                z = max(zs, key=abs) * 0.5
                detail = f"SPY/GLD={z_spygld:+.1f}σ vs HYG/IEF={z_hygief:+.1f}σ (split)"
        else:
            z = zs[0]
            detail = f"SPY/GLD={z:+.1f}σ" if z_spygld is not None else f"HYG/IEF={z:+.1f}σ"

        intensity = _scale_z(z)
        if intensity <= 0:
            return None
        sign = 1.0 if z > 0 else -1.0
        mult = _mult_for(_BIAS_RISK_ON, symbol, direction) * sign
        delta = float(np.clip(intensity * mult * PER_GAUGE_MAX, -PER_GAUGE_MAX, PER_GAUGE_MAX))
        if abs(delta) < 0.25:
            return None
        state = "RISK-ON" if z > 0 else "RISK-OFF"
        direction_word = "desteği" if delta > 0 else "aleyhine"
        sign_str = "+" if delta > 0 else ""
        note = (f"Risk regime {state} ({detail}) → {symbol} {direction} "
                f"{direction_word} {sign_str}{delta:.1f}")
        return GaugeContribution("risk_ratio", state, intensity, delta, note)
    except Exception as e:
        logger.debug("risk_ratio contrib failed: %s", e)
        return None


def _contrib_btc_ndx_divergence(symbol: str, direction: str) -> Optional[GaugeContribution]:
    """BTC vs NDX divergence — speculative-tail leading indicator.

    My market observation (2024-2026): post-2020 BTC became a high-beta
    proxy for tech/risk-on flows — when BTC and NDX move together, the
    risk-on tide is broad. When BTC sells off WHILE NDX rallies, the
    speculative edge is fading first — that's the canary. The reverse
    (BTC rallying while NDX flatlines) is usually less informative.

    Method: 5-day return spread (NDX_5d - BTC_5d). If NDX is up but BTC
    is down by 5%+, that's a divergence z-score >+1.5 → fire warning.
    """
    try:
        from services import macro_data_service as macro
        btc = macro.get_history("BTC", "D1")
        ndx = macro.get_history("NQ", "D1")  # Nasdaq Composite proxy
        if btc is None or ndx is None or len(btc) < 30 or len(ndx) < 30:
            return None
        common = btc.index.intersection(ndx.index)
        if len(common) < 30:
            return None
        btc_c = btc["close"].loc[common]
        ndx_c = ndx["close"].loc[common]
        # 5-day returns
        btc_ret = (btc_c.iloc[-1] / btc_c.iloc[-6] - 1) * 100 if len(btc_c) >= 6 else 0
        ndx_ret = (ndx_c.iloc[-1] / ndx_c.iloc[-6] - 1) * 100 if len(ndx_c) >= 6 else 0
        diverg = ndx_ret - btc_ret  # positive = NDX outperforming BTC
        # Need EITHER ABS(divergence) significant AND signs differ to flag
        if abs(diverg) < 4.0:
            return None
        # Only act when the SIGNS disagree (real divergence, not just lead/lag)
        if btc_ret * ndx_ret >= 0:
            return None

        intensity = float(np.clip((abs(diverg) - 4.0) / 6.0, 0.0, 1.0))
        # Direction of divergence: positive diverg = bullish-NDX/bearish-BTC
        # is the BEARISH warning (NDX leading without spec-tail support).
        sign = 1.0 if diverg > 0 else -1.0
        mult = _mult_for(_BIAS_BTC_NDX_DIVERGENCE, symbol, direction) * sign
        delta = float(np.clip(intensity * mult * PER_GAUGE_MAX, -PER_GAUGE_MAX, PER_GAUGE_MAX))
        if abs(delta) < 0.25:
            return None
        state = ("NDX↑/BTC↓ divergence" if diverg > 0
                 else "BTC↑/NDX↓ divergence")
        direction_word = "desteği" if delta > 0 else "aleyhine"
        sign_str = "+" if delta > 0 else ""
        note = (f"{state} (NDX 5d={ndx_ret:+.1f}%, BTC 5d={btc_ret:+.1f}%) → "
                f"{symbol} {direction} {direction_word} {sign_str}{delta:.1f}")
        return GaugeContribution("btc_ndx", state, intensity, delta, note)
    except Exception as e:
        logger.debug("btc_ndx contrib failed: %s", e)
        return None


def _contrib_carry_unwind(symbol: str, direction: str) -> Optional[GaugeContribution]:
    """USD/JPY carry-trade unwind detector.

    My market observation (Aug 2024 was the textbook example): rapid drops
    in USD/JPY trigger forced unwinds of yen-funded leveraged positions
    globally. The cascade hits indices/risk assets within 24-72h. This is
    asymmetric — a JPY rally (USDJPY drop) is risk-off; a steady carry
    grind (USDJPY drift up) is normal liquidity.

    Method: 3-day pct change. < -2% → moderate, < -3.5% → strong warning.
    Recovery (positive moves) ignored intentionally — only the unwind side
    matters for risk management.
    """
    try:
        from services import macro_data_service as macro
        df = macro.get_history("USDJPY", "D1")
        if df is None or len(df) < 10:
            return None
        c = df["close"].dropna()
        if len(c) < 4:
            return None
        chg3d = (float(c.iloc[-1]) / float(c.iloc[-4]) - 1) * 100
        # Asymmetric — only flag drops
        if chg3d > -2.0:
            return None
        intensity = float(np.clip((-chg3d - 2.0) / 2.5, 0.0, 1.0))
        # Always negative sign (unwind = risk-off direction in bias matrix)
        mult = _mult_for(_BIAS_CARRY_UNWIND, symbol, direction)
        delta = float(np.clip(intensity * mult * PER_GAUGE_MAX, -PER_GAUGE_MAX, PER_GAUGE_MAX))
        if abs(delta) < 0.25:
            return None
        state = f"USD/JPY unwind ({chg3d:+.2f}% 3d)"
        direction_word = "desteği" if delta > 0 else "aleyhine"
        sign_str = "+" if delta > 0 else ""
        note = (f"{state} → carry unwind risk on {symbol} {direction} "
                f"{direction_word} {sign_str}{delta:.1f}")
        return GaugeContribution("carry", state, intensity, delta, note)
    except Exception as e:
        logger.debug("carry_unwind contrib failed: %s", e)
        return None


def _contrib_copper_gold(symbol: str, direction: str) -> Optional[GaugeContribution]:
    """Copper/Gold ratio — global growth / China demand proxy.

    My market observation: copper is "Dr. Copper" — first to respond to
    industrial demand changes. Ratio to gold filters out USD effects.
    Rising ratio = pro-growth (favours equities + oil, hurts gold).
    Falling = disinflation/recession fear.

    Method: 30-day rolling z-score of copper/gold ratio. |z| > 1 triggers.
    """
    try:
        from services import macro_data_service as macro
        cop = macro.get_history("COPPER", "D1")
        gld = macro.get_history("GLD", "D1")
        if cop is None or gld is None or len(cop) < 60 or len(gld) < 60:
            return None
        common = cop.index.intersection(gld.index)
        if len(common) < 60:
            return None
        ratio = (cop["close"].loc[common] / gld["close"].loc[common]).dropna()
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
        mult = _mult_for(_BIAS_COPPER_GOLD, symbol, direction) * sign
        delta = float(np.clip(intensity * mult * PER_GAUGE_MAX, -PER_GAUGE_MAX, PER_GAUGE_MAX))
        if abs(delta) < 0.25:
            return None
        state = "GROWTH↑ (Cu/Au)" if z > 0 else "GROWTH↓ (Cu/Au)"
        direction_word = "desteği" if delta > 0 else "aleyhine"
        sign_str = "+" if delta > 0 else ""
        note = (f"Copper/Gold {state} (z={z:+.1f}σ) → {symbol} {direction} "
                f"{direction_word} {sign_str}{delta:.1f}")
        return GaugeContribution("copper_gold", state, intensity, delta, note)
    except Exception as e:
        logger.debug("copper_gold contrib failed: %s", e)
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

def compute_macro_context(symbol: str, direction: str,
                            regime: Optional[str] = None) -> Dict[str, Any]:
    """
    Build the full macro context for (symbol, direction).

    Improvements (2026-05-14) — beyond academic literature:
    - Multi-gauge dampening (√n): when 3+ gauges fire same sign, divide
      the redundant portion by √n to avoid triple-counting the same
      underlying theme (risk-off events make DXY+VIX+Yield all hostile
      simultaneously — they're correlated, not independent).
    - Regime-aware shrinkage: in STRONG_TREND_UP/DOWN, the trend itself
      already prices the macro consensus. Multiply final adjustment by
      0.5 so the overlay doesn't fight a clear technical trend.
    - Sign-conflict dampening: gauges pulling opposite directions get
      partially netted (signal quality is lower).
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
    for fn in (
        _contrib_dxy,
        _contrib_vix,
        _contrib_yield,
        _contrib_risk_ratio,
        _contrib_btc_ndx_divergence,
        _contrib_carry_unwind,
        _contrib_copper_gold,
        _contrib_psi,
    ):
        c = fn(symbol, direction)
        if c is not None:
            contribs.append(c)

    if not contribs:
        return stub

    # === Multi-gauge dampening (√n shrinkage for correlated agreement) ===
    pos = [c.delta for c in contribs if c.delta > 0]
    neg = [c.delta for c in contribs if c.delta < 0]
    # If ≥3 gauges agree (same sign), the overlap is likely a single
    # underlying theme — shrink the redundant magnitude.
    raw_total_pos = sum(pos)
    raw_total_neg = sum(neg)
    if len(pos) >= 3:
        raw_total_pos = raw_total_pos / (len(pos) ** 0.5) * 1.4  # √n correction
    if len(neg) >= 3:
        raw_total_neg = raw_total_neg / (len(neg) ** 0.5) * 1.4
    raw_total = raw_total_pos + raw_total_neg

    # === Regime-aware shrinkage ===
    # If we're already in a strong trend, the technical signal dominates;
    # the macro overlay should be a feathered nudge, not a full vote.
    if regime in ("STRONG_TREND_UP", "STRONG_TREND_DOWN"):
        raw_total *= 0.5
    elif regime in ("WEAK_TREND_UP", "WEAK_TREND_DOWN"):
        raw_total *= 0.75

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
