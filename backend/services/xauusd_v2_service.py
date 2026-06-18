"""
XAUUSD v2/v3 ML Prediction Service.

Replaces the legacy 150-feature LightGBM Pipeline for XAUUSD with a two-headed
calibrated ensemble:

  * BUY model:  P(long trade profitable within 12h with TP=1.5×ATR / SL=1.0×ATR)
  * SELL model: P(short trade profitable within same window)
  * Isotonic calibrators on each head
  * Feature set (v3, 133 cols): ATR-normalized M30/H1/H4 OHLC + M15 anti-chase,
    swing-high/low distance, parabolic SAR position, linreg trend channel,
    consecutive-bar streaks, upper/lower wick clusters, sessions, DXY/VIX/US10Y
    correlations + returns. v3 specifically targets the "BUY at resistance /
    SELL at support" failure mode observed in early v2 production trades.

Fixed risk profile (Test A from hold-out backtest):
    TP = $10 (10 pips for XAUUSD)
    SL = $15
Hold-out 60d backtest (v3): 82.3% win-rate, +$3296 net, -$0 max drawdown,
1.2% BUY-at-resistance rate (vs ~15-20% in v2).

Public entry point:
    await predict_xauusd_v2(strategy="balanced") -> PredictionResult
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Model bundle loader (lazy, single load per process)
# ---------------------------------------------------------------------------

_MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "model_xauusd_v2.joblib"
_bundle: dict | None = None


def _load_bundle() -> Optional[dict]:
    global _bundle
    if _bundle is not None:
        return _bundle
    try:
        import joblib
        if not _MODEL_PATH.exists():
            logger.error(f"[xauusd_v2] model file not found: {_MODEL_PATH}")
            return None
        _bundle = joblib.load(_MODEL_PATH)
        logger.info(f"[xauusd_v2] loaded bundle ({len(_bundle.get('feature_columns', []))} features, "
                    f"config={_bundle.get('config', {})})")
        return _bundle
    except Exception as e:
        logger.exception(f"[xauusd_v2] bundle load failed: {e}")
        return None


# ---------------------------------------------------------------------------
# Indicators (same math as training-time features.py — kept pure-pandas)
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
    line = _ema(c, 12) - _ema(c, 26)
    sig = _ema(line, 9)
    return line, sig, line - sig


def _bbands(c: pd.Series, n: int = 20, k: float = 2.0):
    m = c.rolling(n).mean()
    sd = c.rolling(n).std()
    return m - k * sd, m, m + k * sd


def _parabolic_sar(high: pd.Series, low: pd.Series, af_init: float = 0.02,
                    af_step: float = 0.02, af_max: float = 0.2) -> pd.Series:
    """Wilder's Parabolic SAR — must mirror xauusdegitim/features.py exactly."""
    n = len(high)
    sar = np.full(n, np.nan)
    if n < 3:
        return pd.Series(sar, index=high.index)
    h = high.values
    l = low.values
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
                is_long = False
                sar_i = ep
                ep = l[i]
                af = af_init
            else:
                if h[i] > ep:
                    ep = h[i]
                    af = min(af + af_step, af_max)
        else:
            sar_i = prev_sar + af * (ep - prev_sar)
            sar_i = max(sar_i, h[i - 1], h[i - 2] if i >= 2 else h[i - 1])
            if h[i] > sar_i:
                is_long = True
                sar_i = ep
                ep = h[i]
                af = af_init
            else:
                if l[i] < ep:
                    ep = l[i]
                    af = min(af + af_step, af_max)
        sar[i] = sar_i
    return pd.Series(sar, index=high.index)


def _linreg_channel(close: pd.Series, n: int = 50) -> pd.DataFrame:
    """Rolling linreg channel: slope, residual sigma, %position within ±2σ band."""
    x = np.arange(n)
    out = pd.DataFrame(index=close.index, columns=["slope", "sigma", "pct_in_channel"], dtype=float)
    vals = close.values
    for i in range(n - 1, len(close)):
        y = vals[i - n + 1:i + 1]
        if np.any(np.isnan(y)):
            continue
        slope, intercept = np.polyfit(x, y, 1)
        pred = slope * x + intercept
        residuals = y - pred
        sigma = float(np.std(residuals))
        if sigma <= 0:
            continue
        upper = pred[-1] + 2 * sigma
        lower = pred[-1] - 2 * sigma
        pct = (y[-1] - lower) / (upper - lower) if upper > lower else 0.5
        out.iloc[i] = [slope, sigma, pct]
    return out


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


def _build_tf_features(df: pd.DataFrame, suffix: str) -> pd.DataFrame:
    o, h, l, c = df["open"], df["high"], df["low"], df["close"]
    a = _atr(h, l, c, 14)
    out = pd.DataFrame(index=df.index)
    out[f"ret1_atr_{suffix}"] = (c - c.shift(1)) / a
    out[f"ret5_atr_{suffix}"] = (c - c.shift(5)) / a
    out[f"ret20_atr_{suffix}"] = (c - c.shift(20)) / a
    out[f"body_atr_{suffix}"] = (c - o) / a
    out[f"upper_wick_atr_{suffix}"] = (h - c.where(c >= o, o)) / a
    out[f"lower_wick_atr_{suffix}"] = (c.where(c <= o, o) - l) / a
    for n in (20, 50, 200):
        e = _ema(c, n)
        out[f"dist_ema{n}_atr_{suffix}"] = (c - e) / a
        out[f"slope_ema{n}_{suffix}"] = (e - e.shift(5)) / a
    out[f"rsi_{suffix}"] = _rsi(c, 14)
    out[f"rsi_slope_{suffix}"] = out[f"rsi_{suffix}"] - out[f"rsi_{suffix}"].shift(3)
    macd_line, macd_sig, macd_hist = _macd(c)
    out[f"macd_hist_atr_{suffix}"] = macd_hist / a
    out[f"macd_hist_slope_{suffix}"] = (macd_hist - macd_hist.shift(2)) / a
    bl, bm, bu = _bbands(c, 20)
    out[f"bb_pctb_{suffix}"] = (c - bl) / (bu - bl).replace(0, np.nan)
    out[f"bb_width_atr_{suffix}"] = (bu - bl) / a
    out[f"adx_{suffix}"] = _adx(h, l, c, 14)
    vol = df.get("tick_volume")
    if vol is None:
        vol = df.get("volume")
    if vol is not None:
        vmu = vol.rolling(50).mean()
        vsd = vol.rolling(50).std()
        out[f"vol_z_{suffix}"] = (vol - vmu) / vsd.replace(0, np.nan)

    # ── v3 anti-chase features (must match xauusdegitim/features.py) ──
    for lb in (30, 100):
        sw_high = h.rolling(lb).max()
        sw_low = l.rolling(lb).min()
        out[f"dist_swing_high_{lb}_atr_{suffix}"] = (sw_high - c) / a
        out[f"dist_swing_low_{lb}_atr_{suffix}"] = (c - sw_low) / a

    out[f"bars_since_high_30_{suffix}"] = h.rolling(30).apply(
        lambda x: 30 - 1 - int(np.argmax(x)), raw=True)
    out[f"bars_since_low_30_{suffix}"] = l.rolling(30).apply(
        lambda x: 30 - 1 - int(np.argmin(x)), raw=True)

    direction = np.sign(c - o)
    streak = direction.groupby((direction != direction.shift()).cumsum()).cumcount() + 1
    out[f"consec_green_{suffix}"] = (streak * (direction > 0)).astype(float)
    out[f"consec_red_{suffix}"] = (streak * (direction < 0)).astype(float)

    sar = _parabolic_sar(h, l)
    out[f"sar_above_{suffix}"] = (sar > c).astype(float) - (sar < c).astype(float)
    out[f"sar_dist_atr_{suffix}"] = (c - sar) / a

    chan = _linreg_channel(c, n=50)
    out[f"chan_slope_atr_{suffix}"] = chan["slope"] / a
    out[f"chan_pct_{suffix}"] = chan["pct_in_channel"]

    upper_wick = (h - c.where(c >= o, o)) / a
    lower_wick = (c.where(c <= o, o) - l) / a
    out[f"upper_wick_5_{suffix}"] = upper_wick.rolling(5).sum()
    out[f"lower_wick_5_{suffix}"] = lower_wick.rolling(5).sum()
    return out


def _session_features(idx: pd.DatetimeIndex) -> pd.DataFrame:
    h = idx.hour
    out = pd.DataFrame(index=idx)
    out["sess_asia"] = ((h >= 0) & (h < 9)).astype(int)
    out["sess_london"] = ((h >= 7) & (h < 16)).astype(int)
    out["sess_ny"] = ((h >= 12) & (h < 21)).astype(int)
    out["sess_overlap_lon_ny"] = ((h >= 12) & (h < 16)).astype(int)
    out["dow"] = idx.dayofweek
    out["hour"] = h
    out["is_friday"] = (idx.dayofweek == 4).astype(int)
    out["is_sunday_open"] = ((idx.dayofweek == 6) & (h >= 22)).astype(int)
    return out


def _macro_features(base: pd.DataFrame) -> pd.DataFrame:
    """Pull macros from macro_data_service and align onto base index."""
    from services import macro_data_service as macro
    out = pd.DataFrame(index=base.index)
    base_close = base["close"]
    base_ret = base_close.pct_change()
    for name in ("DXY", "US10Y", "VIX"):
        df = macro.get_history(name, "H1")
        if df is None or df.empty:
            continue
        c = df["close"].reindex(base.index, method="ffill")
        a = _atr(df["high"], df["low"], df["close"], 14).reindex(base.index, method="ffill")
        n = name.lower()
        out[f"{n}_ret1_atr"] = (c - c.shift(1)) / a
        out[f"{n}_ret20_atr"] = (c - c.shift(20)) / a
        m_ret = c.pct_change()
        out[f"{n}_corr60"] = base_ret.rolling(60).corr(m_ret)
    return out


# ---------------------------------------------------------------------------
# DataHub → DataFrame helpers
# ---------------------------------------------------------------------------

def _candles_to_df(candles: list[dict]) -> pd.DataFrame:
    if not candles:
        return pd.DataFrame()
    df = pd.DataFrame(candles)
    # DataHub candle dicts vary across services — try common fields
    ts_col = next((c for c in ("timestamp", "datetime", "date", "time", "t") if c in df.columns), None)
    if ts_col is None:
        return pd.DataFrame()
    ts = pd.to_datetime(df[ts_col], utc=True, errors="coerce", unit="ms" if df[ts_col].dtype.kind in "iu" else None)
    if ts.isna().all():
        ts = pd.to_datetime(df[ts_col], utc=True, errors="coerce")
    df.index = ts
    df = df[~df.index.isna()].sort_index()
    df = df[~df.index.duplicated(keep="last")]
    rename_map = {}
    for c in df.columns:
        lc = c.lower()
        if lc in ("open", "o"):
            rename_map[c] = "open"
        elif lc in ("high", "h"):
            rename_map[c] = "high"
        elif lc in ("low", "l"):
            rename_map[c] = "low"
        elif lc in ("close", "c"):
            rename_map[c] = "close"
        elif lc in ("volume", "v", "tick_volume"):
            rename_map[c] = "tick_volume"
    df = df.rename(columns=rename_map)
    for col in ("open", "high", "low", "close"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "tick_volume" not in df.columns:
        df["tick_volume"] = 0
    return df.dropna(subset=["open", "high", "low", "close"])


async def _fetch_tf(timeframe: str, limit: int) -> pd.DataFrame:
    from services.data_fetcher import fetch_ohlc_data
    candles = await fetch_ohlc_data("XAUUSD", timeframe=timeframe, limit=limit)
    df = _candles_to_df(candles)
    return df


# ---------------------------------------------------------------------------
# Result builder
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hold_result(symbol: str, reason: str, current_price: float = 0.0):
    """Build a HOLD PredictionResult — must mirror PredictionResult dataclass."""
    from services.ml_prediction_service import PredictionResult
    return PredictionResult(
        symbol=symbol, direction="HOLD", confidence=0.0,
        probability_up=50.0, probability_down=50.0,  # 0-100 scale (see live return site)
        target_pips=0.0, stop_pips=0.0, risk_reward=0.0,
        entry_price=current_price, target_price=current_price, stop_price=current_price,
        technical_score=0.0, momentum_score=0.0, trend_score=0.0,
        volatility_regime="unknown",
        reasoning=[f"v2: {reason}"], key_levels=[],
        timestamp=_now_iso(), model_version="xauusd_v2",
    )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

# Inference parameters (match Test A backtest)
_THRESHOLD = 0.60      # min calibrated probability to enter
_MARGIN = 0.05         # min |P(BUY) - P(SELL)|
_TP_DOLLARS = 10.0     # 10 pips ($1/pip XAU)
_SL_DOLLARS = 15.0
_TP_PIPS = 10.0
_SL_PIPS = 15.0


async def predict_xauusd_v2(strategy: str = "balanced", **_ignored):
    """Generate a v2 XAUUSD prediction. Returns PredictionResult (HOLD/BUY/SELL)."""
    bundle = _load_bundle()
    if bundle is None:
        return _hold_result("XAUUSD", "model_unavailable")

    # Pull candles in parallel
    m15_task = asyncio.create_task(_fetch_tf("15m", 500))
    m30_task = asyncio.create_task(_fetch_tf("30m", 500))
    h1_task = asyncio.create_task(_fetch_tf("1h", 300))
    h4_task = asyncio.create_task(_fetch_tf("4h", 200))
    m15, m30, h1, h4 = await asyncio.gather(m15_task, m30_task, h1_task, h4_task)

    if m30.empty or len(m30) < 60:
        return _hold_result("XAUUSD", f"insufficient_m30_bars({len(m30)})")
    if h1.empty or len(h1) < 30:
        return _hold_result("XAUUSD", f"insufficient_h1_bars({len(h1)})")
    if h4.empty or len(h4) < 30:
        return _hold_result("XAUUSD", f"insufficient_h4_bars({len(h4)})")
    if m15.empty or len(m15) < 60:
        # M15 anti-chase features still useful but not strictly required;
        # downstream column-fill will impute missing M15 columns.
        logger.warning(f"[xauusd_v2] M15 unavailable ({len(m15)} bars) — anti-chase M15 features will be imputed")

    # Build feature matrix at M30 cadence
    feats = [
        _build_tf_features(m30, "M30"),
        _build_tf_features(h1, "H1").reindex(m30.index, method="ffill"),
        _build_tf_features(h4, "H4").reindex(m30.index, method="ffill"),
        _session_features(m30.index),
    ]
    if not m15.empty and len(m15) >= 60:
        m15_feat = _build_tf_features(m15, "M15")
        keep = [col for col in m15_feat.columns if any(k in col for k in (
            "swing_high", "swing_low", "bars_since_high", "bars_since_low",
            "consec_green", "consec_red", "sar_", "chan_", "wick_5",
        ))]
        feats.append(m15_feat[keep].reindex(m30.index, method="ffill"))
    try:
        feats.append(_macro_features(m30))
    except Exception as e:
        logger.warning(f"[xauusd_v2] macro features unavailable: {e}")

    X = pd.concat(feats, axis=1)
    feature_cols = bundle["feature_columns"]
    # Ensure columns exist (missing macros → zero-fill, sklearn pipeline imputes)
    for col in feature_cols:
        if col not in X.columns:
            X[col] = np.nan
    X = X[feature_cols]

    # Use the LATEST bar for live inference
    last_idx = X.index[-1]
    x_last = X.loc[[last_idx]]
    if x_last.isna().all(axis=1).item():
        return _hold_result("XAUUSD", "all_features_nan", float(m30["close"].iloc[-1]))

    try:
        p_buy_raw = float(bundle["buy_model"].predict_proba(x_last)[:, 1][0])
        p_sell_raw = float(bundle["sell_model"].predict_proba(x_last)[:, 1][0])
        p_buy = float(bundle["buy_calibrator"].transform([p_buy_raw])[0])
        p_sell = float(bundle["sell_calibrator"].transform([p_sell_raw])[0])
    except Exception as e:
        logger.exception(f"[xauusd_v2] predict failed: {e}")
        return _hold_result("XAUUSD", "predict_error", float(m30["close"].iloc[-1]))

    current_price = float(m30["close"].iloc[-1])
    # Use real-time price if newer
    try:
        from services.data_fetcher import fetch_latest_price
        live = await fetch_latest_price("XAUUSD")
        if live and 0.0 < live < 1e6:
            current_price = float(live)
    except Exception:
        pass

    # Threshold + margin gate (Test A inference logic)
    p_max = max(p_buy, p_sell)
    margin = abs(p_buy - p_sell)
    direction = "HOLD"
    confidence_pct = 0.0
    if p_max >= _THRESHOLD and margin >= _MARGIN:
        direction = "BUY" if p_buy > p_sell else "SELL"
        # Confidence: scale calibrated prob (0.50–1.00) → percent (50–100)
        confidence_pct = max(0.0, min(100.0, 100.0 * p_max))

    if direction == "HOLD":
        return _hold_result("XAUUSD",
                            f"below_gate(p_buy={p_buy:.3f},p_sell={p_sell:.3f},margin={margin:.3f})",
                            current_price)

    # Risk levels (Test A: TP $10 / SL $15)
    if direction == "BUY":
        target_price = current_price + _TP_DOLLARS
        stop_price = current_price - _SL_DOLLARS
    else:
        target_price = current_price - _TP_DOLLARS
        stop_price = current_price + _SL_DOLLARS

    # Macro snapshot for factors (also useful for downstream analysis)
    macro_snap_factors: dict = {}
    try:
        from services import macro_data_service as macro
        snap = macro.get_snapshot()
        for name, s in snap.items():
            macro_snap_factors[f"macro_{name.lower()}_price"] = round(s.price, 4)
            if s.change_1h_pct is not None:
                macro_snap_factors[f"macro_{name.lower()}_chg1h_pct"] = round(s.change_1h_pct, 3)
            if s.change_1d_pct is not None:
                macro_snap_factors[f"macro_{name.lower()}_chg1d_pct"] = round(s.change_1d_pct, 3)
    except Exception:
        pass

    reasoning = [
        f"v2 ML — calibrated P(BUY)={p_buy:.3f} P(SELL)={p_sell:.3f} margin={margin:.3f}",
        f"Threshold gate: ≥{_THRESHOLD:.2f} prob & ≥{_MARGIN:.2f} margin → {direction}",
        f"Risk: TP ${_TP_DOLLARS:.0f} / SL ${_SL_DOLLARS:.0f} (R:R {_TP_DOLLARS / _SL_DOLLARS:.2f})",
    ]
    if macro_snap_factors:
        ms = []
        for n in ("DXY", "VIX", "US10Y"):
            k = f"macro_{n.lower()}_chg1h_pct"
            if k in macro_snap_factors:
                ms.append(f"{n} 1h:{macro_snap_factors[k]:+.2f}%")
        if ms:
            reasoning.append("Macro: " + " | ".join(ms))

    from services.ml_prediction_service import PredictionResult
    return PredictionResult(
        symbol="XAUUSD",
        direction=direction,
        confidence=confidence_pct,
        # PredictionResult uses a 0-100 probability scale (see ml_prediction_service
        # which returns round(prob*100,1)). p_buy/p_sell are raw 0-1 probabilities,
        # so scale them here to stay consistent with the nasdaq/main model output.
        probability_up=round(p_buy * 100, 1),
        probability_down=round(p_sell * 100, 1),
        target_pips=_TP_PIPS,
        stop_pips=_SL_PIPS,
        risk_reward=_TP_DOLLARS / _SL_DOLLARS,
        entry_price=current_price,
        target_price=target_price,
        stop_price=stop_price,
        technical_score=confidence_pct,
        momentum_score=confidence_pct,
        trend_score=confidence_pct,
        volatility_regime="trend" if (p_max >= 0.70) else "neutral",
        reasoning=reasoning,
        key_levels=[
            {"label": "TP", "price": target_price, "type": "target"},
            {"label": "SL", "price": stop_price, "type": "stop"},
        ],
        timestamp=_now_iso(),
        model_version="xauusd_v2",
    )
