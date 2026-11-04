"""DV04c-U b3.0 olay listesi + H60 giriş geçerlilik maskesi (bağımsız dönem).

Satırlar fam_turev/scripts/01_prep.py (main: BAD, rollover, atr5), 02_outcomes.py (s_bp, base_ok, H=60 `valid`) ve
03_events.py (DV04 bloğu: z5, db, DV04c-U, add/episode) dosyalarından BİREBİR alındı; yalnız DV04c-U b3.0 hücresi ve
yalnız `valid` (sonuç hesabı yok) üretilir. Sabitler port/common.py'den (T0 2017-08-17, N).
Çıktı: cache/base_dv.npz, cache/out_H60.npz (valid), cache/signals.pkl
Kullanım: python -I -B 04_dv04c.py
"""
from __future__ import annotations

import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent / "port"))
import common as C  # noqa: E402

COLS = ["ts", "spot_open", "spot_high", "spot_low", "spot_close", "spot_missing", "spot_zero_vol", "perp_zero_vol",
        "perp_close", "basis_perp_spot_bp"]


# ---- 01_prep.py (aynen) ----
def rollover_fc() -> np.ndarray:
    from zoneinfo import ZoneInfo
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
    return out


def add(sig: list, hid: str, par: str, d: int, kind: str, t: np.ndarray, Hset=(15, 60), ep: bool = True) -> None:
    t = np.asarray(t, dtype=np.int64)
    t = t[(t >= 1) & (t < C.N - 2)]
    if ep:
        t = C.episode(t)
    else:
        t = np.sort(np.unique(t))
    sig.append({"hid": hid, "par": par, "dir": d, "kind": kind, "Hset": Hset, "t": t})


def main() -> None:
    C.CACHE.mkdir(parents=True, exist_ok=True)
    g = pd.read_parquet(C.DATA / "btc_scalp_1m.parquet", columns=COLS)
    assert len(g) == C.N and g["ts"].iloc[0] == C.T0
    o, h, l, c = (g[f"spot_{x}"].to_numpy(np.float64) for x in ["open", "high", "low", "close"])
    bad = (g["spot_missing"].to_numpy() == 1) | (g["spot_zero_vol"].to_numpy() == 1) | (g["perp_zero_vol"].to_numpy() == 1)
    bad |= np.isnan(c) | np.isnan(o)
    bad[C.tmin("2023-03-24 11:28"):C.tmin("2023-03-24 14:00")] = True  # bu dönemde boş dilim (etkisiz)
    for arr in (o, h, l, c):
        arr[bad] = np.nan
    fc = rollover_fc()
    e = np.arange(C.N)
    j = np.searchsorted(fc, e, side="left")
    nxt = fc[j]
    prv = fc[np.maximum(j - 1, 0)]
    hroll = (nxt - e).astype(np.int32)
    blocked = ((e >= prv) & (e < prv + 4)) | (hroll <= 0)
    a5 = atr5(h, l, c)

    # ---- 02_outcomes.py (aynen; yalnız H=60 valid) ----
    N = C.N
    prev_c = np.concatenate([[np.nan], c[:-1]])
    s_bp = np.maximum(C.SL_MIN_BP, C.SL_ATR * a5 / prev_c * 1e4)
    p0 = o
    base_ok = ~np.isnan(p0) & ~np.isnan(prev_c) & ~np.isnan(s_bp) & ~blocked
    base_ok[0] = False
    cb = np.concatenate([[0], np.cumsum(bad)])
    H = 60
    heff = np.minimum(H, hroll).astype(np.int64)
    hi = np.minimum(e + np.maximum(heff, 0), N)
    valid = base_ok & (heff >= 1) & ((cb[hi] - cb[e]) == 0) & (e + heff <= N)
    valid[1:] &= ~bad[:-1]
    np.savez(C.CACHE / "out_H60.npz", valid=valid)

    # ---- 03_events.py DV04 bloğu (aynen; yalnız DV04c-U b3.0) ----
    tt = np.arange(C.N)
    lc = np.log(c)
    r5 = np.full(C.N, np.nan)
    r5[5:] = lc[5:] - lc[:-5]
    z5 = C.roll_z(pd.Series(r5), 43200, 10000, center=False).to_numpy()
    bas = g["basis_perp_spot_bp"].to_numpy(np.float64)
    db = np.full(C.N, np.nan)
    db[5:] = bas[5:] - bas[:-5]
    sig: list = []
    bb = 3.0
    add(sig, "DV04c-U", f"b{bb}", 1, "event", tt[(z5 >= 3) & (db <= -bb)])
    with open(C.CACHE / "signals.pkl", "wb") as f:
        pickle.dump(sig, f)
    t = sig[0]["t"]
    ts = C.T0 + pd.to_timedelta(t, unit="min")
    print("BAD", int(bad.sum()), "valid H60", int(valid.sum()), "DV04c-U b3.0 epizod", len(t),
          "ilk", ts.min() if len(t) else None, "geçerli giriş (t+1)", int(valid[np.clip(t + 1, 0, N - 1)].sum()))
    print("yıl:", pd.Series(ts.year).value_counts().sort_index().to_dict())


if __name__ == "__main__":
    main()
