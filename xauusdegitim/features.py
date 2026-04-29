"""
Feature engineering for XAUUSD retraining.

Design decisions (vs. current 150-feature model):
  - Replace raw OHLC features with ATR-NORMALIZED returns / distances
    (current model leaks price-level information → BUY-bias when XAU is at all-time-highs)
  - Add session flags (Asia / London / NY) — XAU sessions trade very differently
  - Add DXY/US10Y/VIX correlations as features (currently absent)
  - Add COT positioning lag (commercials_net change) — currently external, not in model
  - Add multi-TF momentum stacking (M30 / H1 / H4 alignment scores)
  - Triple-barrier labeling (TP / SL / timeout) instead of "1h close direction"

This file produces a single feature DataFrame at M30 cadence (the same as the legacy model
so we can A/B compare cleanly), plus a separate label DataFrame.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Indicators (no TA-Lib dependency — explicit pandas/numpy)
# ---------------------------------------------------------------------------

def ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=n, adjust=False).mean()


def rsi(close: pd.Series, n: int = 14) -> pd.Series:
    diff = close.diff()
    up = diff.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-diff.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    rs = up / dn.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def atr(high: pd.Series, low: pd.Series, close: pd.Series, n: int = 14) -> pd.Series:
    pc = close.shift(1)
    tr = pd.concat([(high - low), (high - pc).abs(), (low - pc).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / n, adjust=False).mean()


def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    line = ema(close, fast) - ema(close, slow)
    sig = ema(line, signal)
    return line, sig, line - sig


def bbands(close: pd.Series, n: int = 20, k: float = 2.0):
    m = close.rolling(n).mean()
    sd = close.rolling(n).std()
    return m - k * sd, m, m + k * sd


def adx(high: pd.Series, low: pd.Series, close: pd.Series, n: int = 14) -> pd.Series:
    up = high.diff()
    dn = -low.diff()
    plus_dm = ((up > dn) & (up > 0)).astype(float) * up
    minus_dm = ((dn > up) & (dn > 0)).astype(float) * dn
    a = atr(high, low, close, n)
    plus_di = 100 * plus_dm.ewm(alpha=1 / n, adjust=False).mean() / a
    minus_di = 100 * minus_dm.ewm(alpha=1 / n, adjust=False).mean() / a
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    return dx.ewm(alpha=1 / n, adjust=False).mean()


# ---------------------------------------------------------------------------
# Single-TF feature pack (suffix per timeframe)
# ---------------------------------------------------------------------------

def build_tf_features(df: pd.DataFrame, suffix: str) -> pd.DataFrame:
    o, h, l, c = df["open"], df["high"], df["low"], df["close"]
    a = atr(h, l, c, 14)

    out = pd.DataFrame(index=df.index)
    # ATR-normalized returns (price-level invariant — KEY FIX for XAU at ATH)
    out[f"ret1_atr_{suffix}"] = (c - c.shift(1)) / a
    out[f"ret5_atr_{suffix}"] = (c - c.shift(5)) / a
    out[f"ret20_atr_{suffix}"] = (c - c.shift(20)) / a

    # Range / body / wick (ATR-normalized — no absolute price)
    out[f"body_atr_{suffix}"] = (c - o) / a
    out[f"upper_wick_atr_{suffix}"] = (h - c.where(c >= o, o)) / a
    out[f"lower_wick_atr_{suffix}"] = (c.where(c <= o, o) - l) / a

    # EMAs as ATR-distance from price (not raw price)
    for n in (20, 50, 200):
        e = ema(c, n)
        out[f"dist_ema{n}_atr_{suffix}"] = (c - e) / a
        out[f"slope_ema{n}_{suffix}"] = (e - e.shift(5)) / a

    # Oscillators
    out[f"rsi_{suffix}"] = rsi(c, 14)
    out[f"rsi_slope_{suffix}"] = out[f"rsi_{suffix}"] - out[f"rsi_{suffix}"].shift(3)
    macd_line, macd_sig, macd_hist = macd(c)
    out[f"macd_hist_atr_{suffix}"] = macd_hist / a
    out[f"macd_hist_slope_{suffix}"] = (macd_hist - macd_hist.shift(2)) / a

    # Bollinger %B (already normalized 0–1ish)
    bl, bm, bu = bbands(c, 20)
    out[f"bb_pctb_{suffix}"] = (c - bl) / (bu - bl).replace(0, np.nan)
    out[f"bb_width_atr_{suffix}"] = (bu - bl) / a

    # Trend strength
    out[f"adx_{suffix}"] = adx(h, l, c, 14)

    # Volume (z-score) — guard against missing volume
    vol = df.get("tick_volume")
    if vol is not None:
        vmu = vol.rolling(50).mean()
        vsd = vol.rolling(50).std()
        out[f"vol_z_{suffix}"] = (vol - vmu) / vsd.replace(0, np.nan)

    return out


# ---------------------------------------------------------------------------
# Session / time features
# ---------------------------------------------------------------------------

def session_features(idx: pd.DatetimeIndex) -> pd.DataFrame:
    """UTC-based session flags. London=07-16, NY=12-21, Asia=00-09 (overlapping = liquidity)."""
    h = idx.hour
    out = pd.DataFrame(index=idx)
    out["sess_asia"] = ((h >= 0) & (h < 9)).astype(int)
    out["sess_london"] = ((h >= 7) & (h < 16)).astype(int)
    out["sess_ny"] = ((h >= 12) & (h < 21)).astype(int)
    out["sess_overlap_lon_ny"] = ((h >= 12) & (h < 16)).astype(int)
    out["dow"] = idx.dayofweek  # 0=Mon
    out["hour"] = h
    out["is_friday"] = (idx.dayofweek == 4).astype(int)
    out["is_sunday_open"] = ((idx.dayofweek == 6) & (h >= 22)).astype(int)
    return out


# ---------------------------------------------------------------------------
# Macro features (DXY / US10Y / VIX — XAUUSD's 3 strongest external drivers)
# ---------------------------------------------------------------------------

def macro_features(base: pd.DataFrame, dxy: pd.DataFrame | None,
                   us10y: pd.DataFrame | None, vix: pd.DataFrame | None) -> pd.DataFrame:
    out = pd.DataFrame(index=base.index)
    base_close = base["close"]

    def _add(name: str, df: pd.DataFrame | None):
        if df is None or df.empty:
            return
        c = df["close"].reindex(base.index, method="ffill")
        a = atr(df["high"], df["low"], df["close"], 14).reindex(base.index, method="ffill")
        out[f"{name}_ret1_atr"] = (c - c.shift(1)) / a
        out[f"{name}_ret20_atr"] = (c - c.shift(20)) / a
        # 60-bar rolling correlation of XAU returns vs macro returns
        x_ret = base_close.pct_change()
        m_ret = c.pct_change()
        out[f"{name}_corr60"] = x_ret.rolling(60).corr(m_ret)

    _add("dxy", dxy)
    _add("us10y", us10y)
    _add("vix", vix)
    return out


# ---------------------------------------------------------------------------
# Triple-barrier labeling (replaces "1h direction" label)
# ---------------------------------------------------------------------------

def triple_barrier_label(
    base: pd.DataFrame, *,
    horizon_bars: int = 24,         # 24 × M30 = 12h
    tp_atr_mult: float = 1.5,
    sl_atr_mult: float = 1.0,
) -> pd.DataFrame:
    """
    For each bar t, simulate a long entry at close[t]:
      label = +1 if TP hit before SL within horizon
      label = -1 if SL hit before TP
      label =  0 if neither (timeout)
    A symmetric short-side simulation produces meta_label (whether the *direction*
    inferred from sign is profitable). Use for CLASSIFICATION:
      class 1 ("BUY good") = long_label == +1
      class 0 = otherwise
    Train a MIRROR model with reversed P/L for SELL — or use sign(label) as 3-class.
    """
    h, l, c = base["high"], base["low"], base["close"]
    a = atr(h, l, c, 14)

    n = len(base)
    long_lbl = np.zeros(n, dtype=np.int8)
    short_lbl = np.zeros(n, dtype=np.int8)
    long_pl_atr = np.full(n, np.nan)   # realized P/L in ATR units (for sample weighting)
    short_pl_atr = np.full(n, np.nan)
    bars_to_event = np.full(n, np.nan)

    h_arr = h.to_numpy()
    l_arr = l.to_numpy()
    c_arr = c.to_numpy()
    a_arr = a.to_numpy()

    for i in range(n - 1):
        atr_i = a_arr[i]
        if not np.isfinite(atr_i) or atr_i <= 0:
            continue
        entry = c_arr[i]
        long_tp = entry + tp_atr_mult * atr_i
        long_sl = entry - sl_atr_mult * atr_i
        short_tp = entry - tp_atr_mult * atr_i
        short_sl = entry + sl_atr_mult * atr_i

        end = min(n, i + 1 + horizon_bars)
        long_done = short_done = False
        for j in range(i + 1, end):
            hj, lj = h_arr[j], l_arr[j]
            if not long_done:
                if hj >= long_tp:
                    long_lbl[i] = 1; long_pl_atr[i] = tp_atr_mult; bars_to_event[i] = j - i
                    long_done = True
                elif lj <= long_sl:
                    long_lbl[i] = -1; long_pl_atr[i] = -sl_atr_mult
                    long_done = True
            if not short_done:
                if lj <= short_tp:
                    short_lbl[i] = 1; short_pl_atr[i] = tp_atr_mult
                    short_done = True
                elif hj >= short_sl:
                    short_lbl[i] = -1; short_pl_atr[i] = -sl_atr_mult
                    short_done = True
            if long_done and short_done:
                break
        # Timeout: realized P/L = (close[end-1] - entry) / atr
        if not long_done:
            long_pl_atr[i] = (c_arr[end - 1] - entry) / atr_i
        if not short_done:
            short_pl_atr[i] = (entry - c_arr[end - 1]) / atr_i

    return pd.DataFrame({
        "long_label": long_lbl,
        "short_label": short_lbl,
        "long_pl_atr": long_pl_atr,
        "short_pl_atr": short_pl_atr,
        "bars_to_event": bars_to_event,
    }, index=base.index)


# ---------------------------------------------------------------------------
# Top-level builder
# ---------------------------------------------------------------------------

def build_dataset(
    base_m30: pd.DataFrame,
    h1: pd.DataFrame,
    h4: pd.DataFrame,
    macros: dict | None = None,
    horizon_bars: int = 24,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Returns (X, y) aligned to base_m30 index.
      X: feature DataFrame
      y: label DataFrame from triple_barrier_label
    """
    feats = [
        build_tf_features(base_m30, "M30"),
        # Higher TF features forward-filled onto M30 grid
        build_tf_features(h1, "H1").reindex(base_m30.index, method="ffill"),
        build_tf_features(h4, "H4").reindex(base_m30.index, method="ffill"),
        session_features(base_m30.index),
    ]
    if macros:
        feats.append(macro_features(base_m30,
                                    macros.get("DXY", {}).get("H1") if isinstance(macros.get("DXY"), dict) else None,
                                    macros.get("US10Y", {}).get("H1") if isinstance(macros.get("US10Y"), dict) else None,
                                    macros.get("VIX", {}).get("H1") if isinstance(macros.get("VIX"), dict) else None))
    X = pd.concat(feats, axis=1)
    y = triple_barrier_label(base_m30, horizon_bars=horizon_bars)
    return X, y
