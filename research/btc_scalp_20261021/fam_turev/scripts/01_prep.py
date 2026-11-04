"""Temel ızgara: spot OHLC, BAD maskesi, rollover sınırı, ATR, ve sinyal özellikleri → cache/base.npz

Kullanım: python -I 01_prep.py
"""
from __future__ import annotations

import sys
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

COLS = ["ts", "spot_open", "spot_high", "spot_low", "spot_close", "spot_missing", "spot_zero_vol", "perp_zero_vol",
        "perp_close", "prem_close_bp", "basis_perp_spot_bp", "funding_pred_running", "funding_rate_last",
        "funding_last_time", "funding_last_estimated", "min_to_next_funding", "metrics_eff_ts",
        "liq_flow_long_1m", "liq_flow_short_1m"]


def rollover_fc() -> np.ndarray:
    """Her UTC günü için zorla kapanış dakikası = NY 17:00 − 2 dk (UTC dakika indeksi)."""
    ny = ZoneInfo("America/New_York")
    days = pd.date_range(C.T0 - pd.Timedelta(days=2), C.T_END + pd.Timedelta(days=2), freq="D")
    fc = []
    for d in days:
        t = pd.Timestamp(d.year, d.month, d.day, 17, 0, tzinfo=ny).tz_convert("UTC")
        fc.append(C.tmin(t) - 2)
    return np.asarray(sorted(fc), dtype=np.int64)


def atr5(h, l, c) -> np.ndarray:
    m = np.arange(C.N)
    b5 = m // 5
    df = pd.DataFrame({"b": b5, "h": h, "l": l, "c": c})
    agg = df.groupby("b").agg(h=("h", "max"), l=("l", "min"), c=("c", "last"))
    pc = agg["c"].shift(1)
    tr = pd.concat([agg["h"] - agg["l"], (agg["h"] - pc).abs(), (agg["l"] - pc).abs()], axis=1).max(axis=1)
    a = tr.rolling(14, min_periods=10).mean()
    last_done = b5 - 1
    arr = a.reindex(np.arange(b5.max() + 1)).to_numpy()
    out = np.full(C.N, np.nan)
    ok = last_done >= 0
    out[ok] = arr[last_done[ok]]
    return out  # index e: girişten önce tamamlanmış kovalar


def atr1(h, l, c) -> np.ndarray:
    pc = np.concatenate([[np.nan], c[:-1]])
    tr = np.nanmax(np.vstack([h - l, np.abs(h - pc), np.abs(l - pc)]), axis=0)
    a = pd.Series(tr).rolling(14, min_periods=10).mean().to_numpy()
    return np.concatenate([[np.nan], a[:-1]])  # index t: t-1'e kadar bilgi


def main() -> None:
    C.CACHE.mkdir(parents=True, exist_ok=True)
    g = pd.read_parquet(C.DATA / "btc_scalp_1m.parquet", columns=COLS)
    assert len(g) == C.N and g["ts"].iloc[0] == C.T0
    o, h, l, c = (g[f"spot_{x}"].to_numpy(np.float64) for x in ["open", "high", "low", "close"])
    bad = (g["spot_missing"].to_numpy() == 1) | (g["spot_zero_vol"].to_numpy() == 1) | (g["perp_zero_vol"].to_numpy() == 1)
    bad |= np.isnan(c) | np.isnan(o)
    bad[C.tmin("2023-03-24 11:28"):C.tmin("2023-03-24 14:00")] = True
    for arr in (o, h, l, c):
        arr[bad] = np.nan

    fc = rollover_fc()
    e = np.arange(C.N)
    j = np.searchsorted(fc, e, side="left")  # fc[j] >= e
    nxt = fc[j]
    prv = fc[np.maximum(j - 1, 0)]
    hroll = (nxt - e).astype(np.int32)  # e+hroll = zorla kapanış dakikası (o barın açılışında kapanır)
    blocked = ((e >= prv) & (e < prv + 4)) | (hroll <= 0)

    a5 = atr5(h, l, c)
    a1 = atr1(h, l, c)
    lr = np.log(c / o)
    a, b = C.seg_bounds("DISC")
    p99 = float(np.nanpercentile(np.abs(lr[a:b]), 99))

    np.savez_compressed(
        C.CACHE / "base.npz", o=o, h=h, l=l, c=c, bad=bad, hroll=hroll, blocked=blocked, atr5=a5, atr1=a1,
        absr=np.abs(lr).astype(np.float32), p99_absr=p99,
        perp_close=g["perp_close"].to_numpy(np.float64),
        prem=g["prem_close_bp"].to_numpy(np.float64),
        basis=g["basis_perp_spot_bp"].to_numpy(np.float64),
        fp=(g["funding_pred_running"].to_numpy(np.float64) * 1e4),
        fl=(g["funding_rate_last"].to_numpy(np.float64) * 1e4),
        fl_time=C.tmin(C.T0) + ((g["funding_last_time"] - C.T0) / pd.Timedelta(minutes=1)).to_numpy(np.float64),
        fl_est=g["funding_last_estimated"].to_numpy(np.float32),
        mtnf=g["min_to_next_funding"].to_numpy(np.int32),
        m_eff=((g["metrics_eff_ts"] - C.T0) / pd.Timedelta(minutes=1)).to_numpy(np.float64),
        p1L=g["liq_flow_long_1m"].to_numpy(np.int8), p1S=g["liq_flow_short_1m"].to_numpy(np.int8),
    )
    print("N", C.N, "BAD", int(bad.sum()), "blocked", int(blocked.sum()), "p99|r1m| DISC (bp)", round(p99 * 1e4, 2))
    sl = np.maximum(C.SL_MIN_BP, C.SL_ATR * a5 / c * 1e4)
    yrs = C.year_of(e)
    for y in np.unique(yrs):
        s = sl[yrs == y]
        print(y, "SL bp medyan", round(float(np.nanmedian(s)), 1), "SL=19 tabanı payı", round(float(np.nanmean(s <= 19.0001)), 3))


if __name__ == "__main__":
    main()
