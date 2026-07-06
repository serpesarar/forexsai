"""Feature pack — one code path for research and live.

compute_feature_frame(bars_ctx) adds causal indicator columns to a 1m bar frame
(context = previous day + event day). event_features(feat_bars, events) then
extracts rows at event timestamps and appends event/family metadata.

Tier A  — reproducible from broker 1m candles alone (deployment floor).
Tier B  — needs per-minute tick microstructure (Dukascopy offline / tick_recorder live).
          Column names prefixed "b_" so the trainer can slice tiers cleanly.

All features are relative (z-scores, ATR-normalized, bucketed) — no absolute prices.
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config  # noqa: E402
from labels.triple_barrier import compute_atr  # noqa: E402
from triggers.detect import _rolling_linreg_z  # noqa: E402


def _rsi(close: pd.Series, period: int = 14) -> pd.Series:
    d = close.diff()
    up = d.clip(lower=0).ewm(alpha=1 / period, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / period, adjust=False).mean()
    rs = up / dn.replace(0, np.nan)
    return 100 - 100 / (1 + rs)


def _adx(bars: pd.DataFrame, period: int = 14) -> pd.Series:
    h, l, c = bars["mid_h"], bars["mid_l"], bars["mid_c"]
    up, dn = h.diff(), -l.diff()
    plus_dm = np.where((up > dn) & (up > 0), up, 0.0)
    minus_dm = np.where((dn > up) & (dn > 0), dn, 0.0)
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1 / period, adjust=False).mean()
    pdi = 100 * pd.Series(plus_dm, index=bars.index).ewm(alpha=1 / period, adjust=False).mean() / atr
    mdi = 100 * pd.Series(minus_dm, index=bars.index).ewm(alpha=1 / period, adjust=False).mean() / atr
    dx = 100 * (pdi - mdi).abs() / (pdi + mdi).replace(0, np.nan)
    return dx.ewm(alpha=1 / period, adjust=False).mean()


def compute_feature_frame(bars: pd.DataFrame) -> pd.DataFrame:
    """Add causal feature columns to a time-sorted 1m bar context frame."""
    f = bars.sort_values("ts").reset_index(drop=True).copy()
    c = f["mid_c"]
    atr = compute_atr(f)
    f["atr"] = atr

    # ── Tier A: trend / momentum / structure ────────────────────────────────
    for span in (5, 10, 20, 50, 200):
        f[f"ema{span}_d_atr"] = (c - c.ewm(span=span, adjust=False).mean()) / atr
    emas = [c.ewm(span=s, adjust=False).mean() for s in (5, 10, 20, 50)]
    f["ema_stack"] = sum((emas[i] > emas[i + 1]).astype(int) - (emas[i] < emas[i + 1]).astype(int)
                         for i in range(3))  # −3..+3
    f["rsi14"] = _rsi(c)
    f["adx14"] = _adx(f)
    f["adx_bucket"] = pd.cut(f["adx14"], [0, 18, 25, 35, 999], labels=False)
    f["chan_z"] = _rolling_linreg_z(c, config.CHAN_WINDOW)
    w = f["n_ticks"].clip(lower=1).astype(float)
    vwap = (c * w).rolling(config.CHAN_WINDOW).sum() / w.rolling(config.CHAN_WINDOW).sum()
    dev = c - vwap
    f["vwap_z"] = dev / dev.rolling(config.CHAN_WINDOW).std().replace(0, np.nan)
    f["atr_pctl"] = atr.rolling(1200, min_periods=200).rank(pct=True)
    f["range_atr_5"] = (f["mid_h"].rolling(5).max() - f["mid_l"].rolling(5).min()) / atr

    # 5m / 15m context — STRICTLY CAUSAL: a 1m bar at minute t may only see the most
    # recent higher-TF bar that has already CLOSED at/before t. resample(label/closed=
    # "right") labels each bin by its close time; ffill then picks the last bin whose
    # close ≤ t (the current, still-forming bin is excluded → no lookahead).
    for tf, mins in (("5m", 5), ("15m", 15)):
        r = (f.set_index("ts")["mid_c"]
             .resample(f"{mins}min", label="right", closed="right").last().dropna())
        ema20 = r.ewm(span=20, adjust=False).mean()
        d = ((r - ema20) / r.diff().abs().rolling(14).mean().replace(0, np.nan))
        rsi = _rsi(r)
        f[f"{tf}_stretch"] = d.reindex(f["ts"], method="ffill").to_numpy()
        f[f"{tf}_rsi"] = rsi.reindex(f["ts"], method="ffill").to_numpy()

    # candle behaviour
    body = (f["mid_c"] - f["mid_o"]).abs()
    rng = (f["mid_h"] - f["mid_l"]).replace(0, np.nan)
    f["body_ratio_3"] = (body / rng).rolling(3).mean()
    up_bar = (f["mid_c"] > f["mid_o"]).astype(int) * 2 - 1
    f["consec_dir"] = up_bar.groupby((up_bar != up_bar.shift()).cumsum()).cumcount() + 1
    f["consec_dir"] = f["consec_dir"] * up_bar
    f["upper_wick_atr"] = (f["mid_h"] - f[["mid_c", "mid_o"]].max(axis=1)) / atr
    f["lower_wick_atr"] = (f[["mid_c", "mid_o"]].min(axis=1) - f["mid_l"]) / atr

    # session / calendar
    f["utc_hour"] = f["ts"].dt.hour
    f["dow"] = f["ts"].dt.dayofweek
    day = f["ts"].dt.date
    day_open = f.groupby(day)["mid_o"].transform("first")
    prev_close = f.groupby(day)["mid_c"].transform("last").shift(1)  # approx via ffill below
    f["day_pos_atr"] = (c - day_open) / atr
    # prior-day levels (computed per day, shifted)
    daily = f.groupby(day).agg(d_h=("mid_h", "max"), d_l=("mid_l", "min"), d_c=("mid_c", "last"))
    daily_prev = daily.shift(1)
    f = f.merge(daily_prev, left_on=f["ts"].dt.date, right_index=True, how="left")
    f["pd_high_d_atr"] = (f["d_h"] - c) / atr
    f["pd_low_d_atr"] = (c - f["d_l"]) / atr
    f["gap_atr"] = (day_open - f["d_c"]) / atr
    f["pd_range_pos"] = (c - f["d_l"]) / (f["d_h"] - f["d_l"]).replace(0, np.nan)
    f["round100_d_atr"] = (c % 100).where(lambda s: s <= 50, 100 - (c % 100)) / atr
    f.drop(columns=["key_0", "d_h", "d_l", "d_c"], errors="ignore", inplace=True)

    # ── Tier B: per-minute microstructure (b_ prefix) ────────────────────────
    hour = f["utc_hour"]
    tick_base = f.groupby(hour)["n_ticks"].transform(lambda s: s.rolling(600, min_periods=60).median())
    f["b_tickrate_z"] = (f["n_ticks"] - tick_base) / tick_base.replace(0, np.nan)
    spread_base = f.groupby(hour)["spread_med"].transform(lambda s: s.rolling(600, min_periods=60).median())
    f["b_spread_state"] = f["spread_med"] / spread_base.replace(0, np.nan)
    f["b_flip_3"] = f["sign_flip_ratio"].rolling(3).mean()
    f["b_maxrun_3"] = f["max_run"].rolling(3).max()
    imb = (f["up_ticks"] - f["down_ticks"]) / (f["up_ticks"] + f["down_ticks"]).replace(0, np.nan)
    f["b_imb_1"] = imb
    f["b_imb_5"] = imb.rolling(5).mean()
    f["b_pathlen_eff"] = f["range_mid"] / f["path_len"].replace(0, np.nan)  # 1=clean sweep, →0 chop
    return f


TIER_A_COLS = [
    "ema5_d_atr", "ema10_d_atr", "ema20_d_atr", "ema50_d_atr", "ema200_d_atr",
    "ema_stack", "rsi14", "adx14", "adx_bucket", "chan_z", "vwap_z", "atr_pctl",
    "range_atr_5", "5m_stretch", "5m_rsi", "15m_stretch", "15m_rsi",
    "body_ratio_3", "consec_dir", "upper_wick_atr", "lower_wick_atr",
    "utc_hour", "dow", "day_pos_atr", "pd_high_d_atr", "pd_low_d_atr",
    "gap_atr", "pd_range_pos", "round100_d_atr",
]
TIER_B_COLS = ["b_tickrate_z", "b_spread_state", "b_flip_3", "b_maxrun_3",
               "b_imb_1", "b_imb_5", "b_pathlen_eff"]
META_COLS = ["meta_z", "meta_touches", "meta_dist_atr", "meta_pierce_atr",
             "meta_kind", "meta_or_width", "meta_stretch"]


def event_features(feat_bars: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    """Extract feature rows at event timestamps (confirm bar — fully closed, causal)."""
    idx = pd.DatetimeIndex(feat_bars["ts"])
    pos = pd.Series(np.arange(len(feat_bars)), index=idx)
    rows = []
    for _, ev in events.iterrows():
        p = pos.get(pd.Timestamp(ev["ts"]))
        if p is None or (isinstance(p, float) and np.isnan(p)):
            continue
        r = feat_bars.iloc[int(p)][TIER_A_COLS + TIER_B_COLS].to_dict()
        r["ts"] = ev["ts"]
        r["direction"] = ev["direction"]
        r["family"] = ev["family"]
        r["is_buy"] = 1 if ev["direction"] == "BUY" else 0
        for m in META_COLS:
            r[m] = ev.get(m, np.nan)
        rows.append(r)
    return pd.DataFrame(rows)
