"""
Signal Feature Snapshot — comprehensive indicator state at signal time.

Purpose: every entry written to prediction_logs.factors must carry a rich,
queryable snapshot of WHAT THE MARKET LOOKED LIKE when the signal fired, so
that an AI-ops loop can later cluster failures, find patterns, and propose
improvements.

This module is the single source of truth for that snapshot. Models can call
build_signal_feature_snapshot(symbol) to get a flat dict of ~60 features
covering momentum, trend, volatility, S/R proximity, exhaustion, macro,
session, and pre-computed anti-chase warnings.

Design notes:
  - Self-contained — does not depend on the v2 model bundle.
  - Reads candles from DataHub (zero external API calls).
  - 30-second per-symbol cache so multiple model log calls in the same minute
    share work.
  - Failsafe: on any exception, returns {} — never blocks signal logging.
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

CACHE_TTL_SECONDS = 30
_cache: dict[str, tuple[float, dict]] = {}
_lock = asyncio.Lock()

SYMBOL_TIMEFRAMES = {
    "XAUUSD":      [("30m", "M30"), ("1h", "H1"), ("4h", "H4")],
    "NDX.INDX":    [("15m", "M15"), ("1h", "H1"), ("4h", "H4")],
    "GDAXI.INDX":  [("15m", "M15"), ("1h", "H1"), ("4h", "H4")],
    "USOIL.FOREX": [("30m", "M30"), ("1h", "H1"), ("4h", "H4")],
}
DEFAULT_TFS = [("30m", "M30"), ("1h", "H1"), ("4h", "H4")]


# ---------------------------------------------------------------------------
# Indicator math (pure pandas, no TA-Lib dep)
# ---------------------------------------------------------------------------

def _ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=n, adjust=False).mean()


def _rsi(c: pd.Series, n: int = 14) -> pd.Series:
    d = c.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    rs = up / dn.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def _atr(h: pd.Series, l: pd.Series, c: pd.Series, n: int = 14) -> pd.Series:
    pc = c.shift(1)
    tr = pd.concat([(h - l), (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / n, adjust=False).mean()


def _macd(c: pd.Series):
    fast = _ema(c, 12)
    slow = _ema(c, 26)
    line = fast - slow
    sig = _ema(line, 9)
    return line, sig, line - sig


def _bbands(c: pd.Series, n: int = 20, k: float = 2.0):
    m = c.rolling(n).mean()
    sd = c.rolling(n).std()
    return m - k * sd, m, m + k * sd


def _adx(h: pd.Series, l: pd.Series, c: pd.Series, n: int = 14) -> pd.Series:
    up = h.diff()
    dn = -l.diff()
    plus_dm = ((up > dn) & (up > 0)).astype(float) * up
    minus_dm = ((dn > up) & (dn > 0)).astype(float) * dn
    a = _atr(h, l, c, n)
    plus_di = 100 * plus_dm.ewm(alpha=1 / n, adjust=False).mean() / a
    minus_di = 100 * minus_dm.ewm(alpha=1 / n, adjust=False).mean() / a
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    return dx.ewm(alpha=1 / n, adjust=False).mean()


def _stoch(h: pd.Series, l: pd.Series, c: pd.Series, n: int = 14, d_n: int = 3):
    ll = l.rolling(n).min()
    hh = h.rolling(n).max()
    k = 100 * (c - ll) / (hh - ll).replace(0, np.nan)
    d = k.rolling(d_n).mean()
    return k, d


def _parabolic_sar(high: pd.Series, low: pd.Series) -> pd.Series:
    n = len(high)
    sar = np.full(n, np.nan)
    if n < 3:
        return pd.Series(sar, index=high.index)
    h = high.values
    l = low.values
    af_init, af_step, af_max = 0.02, 0.02, 0.2
    is_long = True
    sar[0] = l[0]
    ep = h[0]
    af = af_init
    for i in range(1, n):
        prev_sar = sar[i - 1] if not np.isnan(sar[i - 1]) else l[i - 1]
        if is_long:
            sar_i = prev_sar + af * (ep - prev_sar)
            sar_i = min(sar_i, l[i - 1], l[i - 2] if i >= 2 else l[i - 1])
            if l[i] < sar_i:
                is_long = False; sar_i = ep; ep = l[i]; af = af_init
            else:
                if h[i] > ep: ep = h[i]; af = min(af + af_step, af_max)
        else:
            sar_i = prev_sar + af * (ep - prev_sar)
            sar_i = max(sar_i, h[i - 1], h[i - 2] if i >= 2 else h[i - 1])
            if h[i] > sar_i:
                is_long = True; sar_i = ep; ep = h[i]; af = af_init
            else:
                if l[i] < ep: ep = l[i]; af = min(af + af_step, af_max)
        sar[i] = sar_i
    return pd.Series(sar, index=high.index)


def _linreg_channel_last(close: pd.Series, n: int = 50) -> tuple[float, float]:
    """Returns (slope, pct_in_channel) using only the LAST n bars. None if insufficient."""
    if len(close) < n:
        return float("nan"), float("nan")
    y = close.iloc[-n:].values
    if np.any(np.isnan(y)):
        return float("nan"), float("nan")
    x = np.arange(n)
    slope, intercept = np.polyfit(x, y, 1)
    pred = slope * x + intercept
    sigma = float(np.std(y - pred))
    if sigma <= 0:
        return float(slope), 0.5
    upper = pred[-1] + 2 * sigma
    lower = pred[-1] - 2 * sigma
    pct = float((y[-1] - lower) / (upper - lower)) if upper > lower else 0.5
    return float(slope), pct


# ---------------------------------------------------------------------------
# DataHub plumbing
# ---------------------------------------------------------------------------

def _candles_to_df(candles: list[dict]) -> pd.DataFrame:
    if not candles:
        return pd.DataFrame()
    df = pd.DataFrame(candles)
    ts_col = next((c for c in ("timestamp", "datetime", "date", "time", "t") if c in df.columns), None)
    if ts_col is None:
        return pd.DataFrame()
    if df[ts_col].dtype.kind in "iu":
        ts = pd.to_datetime(df[ts_col], utc=True, errors="coerce", unit="ms")
    else:
        ts = pd.to_datetime(df[ts_col], utc=True, errors="coerce")
    df.index = ts
    df = df[~df.index.isna()].sort_index()
    df = df[~df.index.duplicated(keep="last")]
    rename = {}
    for col in df.columns:
        lc = col.lower()
        if lc in ("open", "o"): rename[col] = "open"
        elif lc in ("high", "h"): rename[col] = "high"
        elif lc in ("low", "l"): rename[col] = "low"
        elif lc in ("close", "c"): rename[col] = "close"
        elif lc in ("volume", "v", "tick_volume"): rename[col] = "volume"
    df = df.rename(columns=rename)
    for col in ("open", "high", "low", "close"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.dropna(subset=["open", "high", "low", "close"])


async def _fetch_tf(symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
    try:
        from services.data_fetcher import fetch_ohlc_data
        candles = await fetch_ohlc_data(symbol, timeframe=timeframe, limit=limit)
        return _candles_to_df(candles)
    except Exception as e:
        logger.debug(f"[snapshot] fetch failed {symbol}/{timeframe}: {e}")
        return pd.DataFrame()


# ---------------------------------------------------------------------------
# Per-timeframe indicator snapshot
# ---------------------------------------------------------------------------

def _round(v: Any, n: int = 4) -> Any:
    """JSON-safe rounding. Returns None on NaN/inf or non-numeric."""
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    if not np.isfinite(f):
        return None
    return round(f, n)


def _compute_tf_snapshot(df: pd.DataFrame, suffix: str) -> dict:
    """One-bar-back-looking snapshot for a single timeframe. Returns 25–30 fields."""
    if df.empty or len(df) < 60:
        return {f"{suffix}_insufficient_bars": True}
    o, h, l, c = df["open"], df["high"], df["low"], df["close"]
    a = _atr(h, l, c, 14)
    out: dict = {}

    # Price + volatility
    last_close = float(c.iloc[-1])
    last_atr = float(a.iloc[-1])
    out[f"{suffix}_close"] = _round(last_close, 4)
    out[f"{suffix}_atr_14"] = _round(last_atr, 4)
    if last_close > 0 and np.isfinite(last_atr):
        out[f"{suffix}_atr_pct"] = _round(last_atr / last_close * 100, 3)
        atr_50_median = float(a.iloc[-50:].median()) if len(a) >= 50 else last_atr
        if atr_50_median > 0:
            out[f"{suffix}_atr_ratio_50"] = _round(last_atr / atr_50_median, 3)

    # RSI
    rsi_series = _rsi(c, 14)
    last_rsi = _round(rsi_series.iloc[-1], 2)
    out[f"{suffix}_rsi_14"] = last_rsi
    if len(rsi_series) >= 4:
        out[f"{suffix}_rsi_slope_3"] = _round(rsi_series.iloc[-1] - rsi_series.iloc[-4], 2)

    # MACD
    macd_line, macd_sig, macd_hist = _macd(c)
    last_hist = float(macd_hist.iloc[-1])
    out[f"{suffix}_macd_hist"] = _round(last_hist, 6)
    out[f"{suffix}_macd_hist_sign"] = int(np.sign(last_hist)) if np.isfinite(last_hist) else 0
    if last_atr > 0:
        out[f"{suffix}_macd_hist_atr"] = _round(last_hist / last_atr, 4)
    if len(macd_hist) >= 3:
        out[f"{suffix}_macd_hist_slope"] = _round(last_hist - float(macd_hist.iloc[-3]), 6)

    # ADX + label
    adx_series = _adx(h, l, c, 14)
    last_adx = _round(adx_series.iloc[-1], 2)
    out[f"{suffix}_adx_14"] = last_adx
    if last_adx is not None:
        if last_adx >= 25:
            out[f"{suffix}_adx_label"] = "trending"
        elif last_adx >= 18:
            out[f"{suffix}_adx_label"] = "weak_trend"
        else:
            out[f"{suffix}_adx_label"] = "ranging"

    # EMAs + alignment
    ema20 = _ema(c, 20)
    ema50 = _ema(c, 50)
    ema200 = _ema(c, 200) if len(c) >= 200 else None
    if last_atr > 0:
        out[f"{suffix}_dist_ema20_atr"] = _round((last_close - float(ema20.iloc[-1])) / last_atr, 3)
        out[f"{suffix}_dist_ema50_atr"] = _round((last_close - float(ema50.iloc[-1])) / last_atr, 3)
        if ema200 is not None and not pd.isna(ema200.iloc[-1]):
            out[f"{suffix}_dist_ema200_atr"] = _round((last_close - float(ema200.iloc[-1])) / last_atr, 3)
    # EMA stack: 20 > 50 > 200 = up; 20 < 50 < 200 = down
    if ema200 is not None and not pd.isna(ema200.iloc[-1]):
        e20 = float(ema20.iloc[-1])
        e50 = float(ema50.iloc[-1])
        e200 = float(ema200.iloc[-1])
        if e20 > e50 > e200:
            out[f"{suffix}_ema_stack"] = "up"
        elif e20 < e50 < e200:
            out[f"{suffix}_ema_stack"] = "down"
        else:
            out[f"{suffix}_ema_stack"] = "mixed"

    # Bollinger
    bl, bm, bu = _bbands(c, 20)
    if not pd.isna(bu.iloc[-1]) and not pd.isna(bl.iloc[-1]):
        denom = float(bu.iloc[-1]) - float(bl.iloc[-1])
        if denom > 0:
            out[f"{suffix}_bb_pctb"] = _round((last_close - float(bl.iloc[-1])) / denom, 3)
        if last_atr > 0:
            out[f"{suffix}_bb_width_atr"] = _round(denom / last_atr, 3)

    # Stochastic
    stk, std = _stoch(h, l, c, 14, 3)
    out[f"{suffix}_stoch_k"] = _round(stk.iloc[-1], 2)
    out[f"{suffix}_stoch_d"] = _round(std.iloc[-1], 2)

    # S/R proximity (anti-chase critical) — 30 + 100 bar swing extremes
    for lb in (30, 100):
        if len(df) < lb:
            continue
        sw_high = float(h.iloc[-lb:].max())
        sw_low = float(l.iloc[-lb:].min())
        if last_atr > 0:
            out[f"{suffix}_dist_swing_high_{lb}_atr"] = _round((sw_high - last_close) / last_atr, 3)
            out[f"{suffix}_dist_swing_low_{lb}_atr"] = _round((last_close - sw_low) / last_atr, 3)
        out[f"{suffix}_swing_high_{lb}"] = _round(sw_high, 4)
        out[f"{suffix}_swing_low_{lb}"] = _round(sw_low, 4)

    # Bars since extreme (timing exhaustion)
    if len(df) >= 30:
        h_last30 = h.iloc[-30:].values
        l_last30 = l.iloc[-30:].values
        out[f"{suffix}_bars_since_high_30"] = int(30 - 1 - int(np.argmax(h_last30)))
        out[f"{suffix}_bars_since_low_30"] = int(30 - 1 - int(np.argmin(l_last30)))

    # Bar streak (consecutive same-direction)
    direction = np.sign(c - o)
    streak = 1
    for i in range(len(direction) - 2, -1, -1):
        if direction.iloc[i] == direction.iloc[-1] and direction.iloc[i] != 0:
            streak += 1
        else:
            break
    last_dir = int(direction.iloc[-1]) if len(direction) else 0
    out[f"{suffix}_consec_green"] = streak if last_dir > 0 else 0
    out[f"{suffix}_consec_red"] = streak if last_dir < 0 else 0

    # Wick clusters (last 5)
    if len(df) >= 5 and last_atr > 0:
        c_eff = c.where(c >= o, o)
        upper_wick = (h - c_eff) / last_atr
        c_eff2 = c.where(c <= o, o)
        lower_wick = (c_eff2 - l) / last_atr
        out[f"{suffix}_upper_wick_5_atr"] = _round(upper_wick.iloc[-5:].sum(), 3)
        out[f"{suffix}_lower_wick_5_atr"] = _round(lower_wick.iloc[-5:].sum(), 3)

    # Parabolic SAR
    if len(df) >= 20:
        try:
            sar = _parabolic_sar(h, l)
            last_sar = float(sar.iloc[-1])
            if np.isfinite(last_sar):
                out[f"{suffix}_sar_above_price"] = bool(last_sar > last_close)
                if last_atr > 0:
                    out[f"{suffix}_sar_dist_atr"] = _round((last_close - last_sar) / last_atr, 3)
        except Exception:
            pass

    # Linear regression channel (50-bar)
    if len(df) >= 50:
        slope, pct = _linreg_channel_last(c, n=50)
        if last_atr > 0:
            out[f"{suffix}_chan_slope_atr"] = _round(slope / last_atr, 5)
        out[f"{suffix}_chan_pct"] = _round(pct, 3)

    # Volume z-score (if available)
    if "volume" in df.columns:
        vol = pd.to_numeric(df["volume"], errors="coerce")
        if vol.notna().any() and len(vol) >= 50:
            vmu = float(vol.iloc[-50:].mean())
            vsd = float(vol.iloc[-50:].std())
            if vsd > 0:
                out[f"{suffix}_vol_z"] = _round((float(vol.iloc[-1]) - vmu) / vsd, 3)

    return out


# ---------------------------------------------------------------------------
# Cross-TF aggregates + warning flags
# ---------------------------------------------------------------------------

def _compute_aggregates(snap: dict) -> dict:
    """Combine per-TF fields into MTF labels + boolean warning flags."""
    out: dict = {}

    # MTF EMA-stack agreement
    stacks = [snap.get(f"{tf}_ema_stack") for tf in ("M30", "M15", "H1", "H4") if snap.get(f"{tf}_ema_stack")]
    if stacks:
        if all(s == "up" for s in stacks):
            out["mtf_trend"] = "all_up"
        elif all(s == "down" for s in stacks):
            out["mtf_trend"] = "all_down"
        else:
            out["mtf_trend"] = "mixed"

    # Regime label (uses H4 ADX + MTF trend)
    h4_adx = snap.get("H4_adx_14") or 0
    if out.get("mtf_trend") == "all_up" and h4_adx >= 25:
        out["regime_label"] = "strong_trend_up"
    elif out.get("mtf_trend") == "all_down" and h4_adx >= 25:
        out["regime_label"] = "strong_trend_down"
    elif h4_adx and h4_adx < 18:
        out["regime_label"] = "ranging"
    else:
        out["regime_label"] = "transition"

    # Volatility regime (M30 atr_ratio)
    m30_atr_ratio = snap.get("M30_atr_ratio_50") or snap.get("M15_atr_ratio_50")
    if m30_atr_ratio:
        if m30_atr_ratio >= 1.5:
            out["volatility_regime"] = "high"
        elif m30_atr_ratio <= 0.7:
            out["volatility_regime"] = "low"
        else:
            out["volatility_regime"] = "normal"

    # Anti-chase warning flags — these are gold for failure analysis
    base_tf = "M30" if snap.get("M30_close") else "M15"
    dist_high = snap.get(f"{base_tf}_dist_swing_high_30_atr")
    dist_low = snap.get(f"{base_tf}_dist_swing_low_30_atr")
    if dist_high is not None:
        out["near_resistance"] = bool(dist_high < 0.3)
    if dist_low is not None:
        out["near_support"] = bool(dist_low < 0.3)

    rsi = snap.get(f"{base_tf}_rsi_14")
    if rsi is not None:
        out["overbought"] = bool(rsi > 70)
        out["oversold"] = bool(rsi < 30)
        out["rsi_extreme"] = bool(rsi > 75 or rsi < 25)

    consec_g = snap.get(f"{base_tf}_consec_green") or 0
    consec_r = snap.get(f"{base_tf}_consec_red") or 0
    out["exhaustion_up"] = bool(consec_g >= 5)
    out["exhaustion_down"] = bool(consec_r >= 5)

    bb_pctb = snap.get(f"{base_tf}_bb_pctb")
    if bb_pctb is not None:
        out["bb_extreme_upper"] = bool(bb_pctb > 0.95)
        out["bb_extreme_lower"] = bool(bb_pctb < 0.05)

    sar_above = snap.get(f"{base_tf}_sar_above_price")
    if sar_above is not None:
        out["sar_bearish"] = bool(sar_above)
        out["sar_bullish"] = bool(not sar_above)

    return out


# ---------------------------------------------------------------------------
# Macro + session
# ---------------------------------------------------------------------------

def _macro_block() -> dict:
    out: dict = {}
    try:
        from services import macro_data_service as macro
        snap = macro.get_snapshot()
        for name in ("DXY", "VIX", "US10Y"):
            s = snap.get(name)
            if s is None:
                continue
            n = name.lower()
            out[f"macro_{n}_price"] = _round(s.price, 4)
            if s.change_1h_pct is not None:
                out[f"macro_{n}_chg1h_pct"] = _round(s.change_1h_pct, 3)
            if s.change_1d_pct is not None:
                out[f"macro_{n}_chg1d_pct"] = _round(s.change_1d_pct, 3)
    except Exception as e:
        logger.debug(f"[snapshot] macro unavailable: {e}")
    return out


def _session_block() -> dict:
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    h = now.hour
    if 13 <= h < 17:
        sess = "overlap"
    elif 8 <= h < 13:
        sess = "europe"
    elif 13 <= h < 22:
        sess = "us"
    elif 0 <= h < 8:
        sess = "asia"
    else:
        sess = "closed"
    return {
        "session": sess,
        "hour_utc": h,
        "dow": now.weekday(),
        "is_friday": now.weekday() == 4,
        "is_sunday_open": now.weekday() == 6 and h >= 22,
    }


# ---------------------------------------------------------------------------
# Public entry
# ---------------------------------------------------------------------------

async def build_signal_feature_snapshot(symbol: str) -> dict:
    """Comprehensive indicator snapshot for failure analysis. Cached 30s.
    Never raises — returns {} if anything fails."""
    if not symbol:
        return {}
    cache_key = symbol.upper()
    now = time.monotonic()

    # Fast path: hit cache
    cached = _cache.get(cache_key)
    if cached and (now - cached[0]) < CACHE_TTL_SECONDS:
        return dict(cached[1])

    async with _lock:
        # Re-check after acquiring lock (another coroutine may have populated)
        cached = _cache.get(cache_key)
        if cached and (time.monotonic() - cached[0]) < CACHE_TTL_SECONDS:
            return dict(cached[1])
        try:
            tfs = SYMBOL_TIMEFRAMES.get(symbol.upper(), DEFAULT_TFS)
            tasks = [_fetch_tf(symbol, fetch_tf, 300) for fetch_tf, _ in tfs]
            dataframes = await asyncio.gather(*tasks, return_exceptions=True)

            snap: dict = {}
            for (fetch_tf, suffix), df in zip(tfs, dataframes):
                if isinstance(df, Exception) or df is None or (hasattr(df, 'empty') and df.empty):
                    snap[f"{suffix}_insufficient_bars"] = True
                    continue
                snap.update(_compute_tf_snapshot(df, suffix))

            # Aggregates + warning flags
            snap.update(_compute_aggregates(snap))

            # Macro + session
            snap.update(_macro_block())
            snap.update(_session_block())

            # Snapshot meta
            snap["snapshot_v"] = 1
            snap["snapshot_ts"] = pd.Timestamp.utcnow().isoformat()

            _cache[cache_key] = (now, snap)
            return dict(snap)
        except Exception as e:
            logger.warning(f"[snapshot] build failed for {symbol}: {e}", exc_info=False)
            return {}
