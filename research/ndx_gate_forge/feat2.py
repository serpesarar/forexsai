"""Geniş nedensel özellik seti — çok zaman dilimli (1m/5m/15m/60m tamamlanmış barlar).

Her özellik karar anında (1m bar i kapanışı) bilinen son TAMAMLANMIŞ tf-barından.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from common import atr, DATA
from features import _last_complete, map_asof


def rsi(c: np.ndarray, n: int = 14) -> np.ndarray:
    d = np.diff(c, prepend=np.nan)
    up = pd.Series(np.where(d > 0, d, 0.0)).ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    dn = pd.Series(np.where(d < 0, -d, 0.0)).ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    return (100 - 100 / (1 + up / dn.replace(0, np.nan))).to_numpy()


def tf_block(b: pd.DataFrame, tf: int) -> dict[str, np.ndarray]:
    if tf == 1:
        s = b[["t", "open", "high", "low", "close", "volume"]].copy()
        s["avail"] = s.t + 60
    else:
        s = _last_complete(b[["ts", "t", "open", "high", "low", "close", "volume"]], tf)
    o, h, l, c, v = (s[k].to_numpy(float) for k in ["open", "high", "low", "close", "volume"])
    a14 = atr(h, l, c, 14)
    e20 = pd.Series(c).ewm(span=20, adjust=False).mean().to_numpy()
    e50 = pd.Series(c).ewm(span=50, adjust=False).mean().to_numpy()
    e200 = pd.Series(c).ewm(span=200, adjust=False).mean().to_numpy()
    out = {
        "rsi": rsi(c, 14),
        "d_e20": (c - e20) / a14,
        "d_e50": (c - e50) / a14,
        "d_e200": (c - e200) / a14,
        "slope50": (e50 - np.r_[np.full(5, np.nan), e50[:-5]]) / a14,
        "ret3": (c - np.r_[np.full(3, np.nan), c[:-3]]) / a14,
        "ret12": (c - np.r_[np.full(12, np.nan), c[:-12]]) / a14,
        "pos20": (c - pd.Series(l).rolling(20).min().to_numpy()) / (pd.Series(h).rolling(20).max() - pd.Series(l).rolling(20).min()).replace(0, np.nan).to_numpy(),
        "body": (c - o) / np.where(h - l > 0, h - l, np.nan),
        "atr_ratio": a14 / pd.Series(a14).rolling(100, min_periods=50).mean().to_numpy(),
        "vol_ratio": v / pd.Series(v).rolling(50, min_periods=20).mean().to_numpy(),
        "eff12": np.abs(c - np.r_[np.full(12, np.nan), c[:-12]]) / pd.Series(np.abs(np.diff(c, prepend=np.nan))).rolling(12).sum().to_numpy(),
        "bbw": (pd.Series(c).rolling(20).std() / pd.Series(c).rolling(20).std().rolling(200, min_periods=50).median()).to_numpy(),
        "streak": _streak(c),
    }
    av = s.avail.to_numpy()
    return {k: map_asof(b.t.to_numpy() + 60, av, x, max_age_s=tf * 60 * 3) for k, x in out.items()}


def _streak(c: np.ndarray) -> np.ndarray:
    d = np.sign(np.diff(c, prepend=np.nan))
    out = np.zeros(len(c))
    for i in range(1, len(c)):
        if d[i] == 0 or np.isnan(d[i]):
            out[i] = 0
        elif d[i] == np.sign(out[i - 1]) or out[i - 1] == 0:
            out[i] = out[i - 1] + d[i]
        else:
            out[i] = d[i]
    return out


def build_all(b: pd.DataFrame) -> pd.DataFrame:
    f = {}
    for tf in (1, 5, 15, 60):
        for k, v in tf_block(b, tf).items():
            f[f"{k}_{tf}"] = v
    F = pd.DataFrame(f)
    base = pd.read_parquet(DATA / "feat_tf1.parquet")
    for k in ["vr15", "skew120", "rv30_rel", "v15_rel", "rng15_rel", "range_used", "day_pos", "pos4",
              "ret_prevclose", "prev_day_ret", "gap"]:
        F[k] = base[k].to_numpy()
    p = base.price.to_numpy()
    F["d_vwap"] = (p - base.vwap.to_numpy()) / base.vwap_sd.replace(0, np.nan).to_numpy()
    F["d_pdh"] = (base.pdh.to_numpy() - p) / base.atr70.to_numpy()
    F["d_pdl"] = (p - base.pdl.to_numpy()) / base.atr70.to_numpy()
    # günlük makro (önceki takvim günü kapanışı — nedensel)
    m = pd.read_csv(DATA / "macro_daily_patched.csv", parse_dates=["date"]).set_index("date")
    full = pd.date_range("2024-01-01", "2026-12-31")
    prevd = pd.to_datetime(base.ny_date) - pd.Timedelta(days=1)
    for col, name in [("VIX_close", "vix"), ("VIX3M_close", "vix3m")]:
        F[name] = m[col].reindex(full).ffill().reindex(prevd).to_numpy()
    F["vix_ts"] = F.vix / F.vix3m
    vx = m.VIX_close.dropna()
    F["vix_chg1"] = (vx.pct_change()).reindex(full).ffill().reindex(prevd).to_numpy()
    ndx = m.NDXCASH_close.dropna()
    F["ndx_ret5d"] = ndx.pct_change(5).reindex(full).ffill().reindex(prevd).to_numpy()
    F["ndx_d200"] = (ndx / ndx.rolling(200).mean() - 1).reindex(full).ffill().reindex(prevd).to_numpy()
    hyg = m.HYG_close.dropna()
    F["hyg_ret1"] = hyg.pct_change().reindex(full).ffill().reindex(prevd).to_numpy()
    tlt = m.TLT_close.dropna()
    F["tlt_ret1"] = tlt.pct_change().reindex(full).ffill().reindex(prevd).to_numpy()
    return F


if __name__ == "__main__":
    from common import load_1m
    b = load_1m()
    F = build_all(b)
    F.to_parquet(DATA / "feat2.parquet")
    print(F.shape)
    print(F.describe().T[["count", "mean", "50%"]].round(3).to_string())
