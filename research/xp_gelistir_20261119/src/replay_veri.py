"""replay_veri.py — K1 + XP işlemlerinin gerçek 30m mumları + işaretler (Duka NDX). python replay_veri.py"""
import json, sys
from datetime import datetime
from pathlib import Path
import numpy as np, pandas as pd
import veri as VR
G, NY = VR.G, VR.NY
HERE = Path(__file__).resolve().parents[1]
D = pd.read_parquet(HERE / "results/islemler.parquet")
T = D[D.besleme == "DUKA_NDX"].sort_values("d").reset_index(drop=True)
b = G.ndx_bars(); t, o, h, l, c, sp = (b[k].values for k in ("t", "o", "h", "l", "c", "sp"))
def ts(d, hh, mm): return int(pd.Timestamp(datetime(d.year, d.month, d.day, hh, mm), tz=NY).timestamp())
dp = VR.daily_frame(b, 60); p16 = dp.o960; days = list(dp.index)
out = []
for r in T.itertuples():
    d, ex = pd.Timestamp(r.d), pd.Timestamp(r.cikis)
    i = days.index(d); j = days.index(ex)
    start = ts(days[i - 1] if i > 0 else d, 9, 30)
    end = ts(days[min(j + 1, len(days) - 1)], 16, 0)
    a, z = int(np.searchsorted(t, start)), int(np.searchsorted(t, end))
    tt = t[a:z]; k = (tt // 1800) * 1800
    df = pd.DataFrame({"k": k, "o": o[a:z], "h": h[a:z], "l": l[a:z], "c": c[a:z]}).groupby("k").agg(o=("o", "first"), h=("h", "max"), l=("l", "min"), c=("c", "last"))
    u0 = ts(d, 16, 0); i0 = int(np.searchsorted(t, u0)); ux = ts(ex, 16, 0); ix = int(np.searchsorted(t, ux))
    seg = l[i0:ix]; jm = int(np.argmin(seg)) if len(seg) else 0
    chk = []
    prev = p16.iloc[i]
    for q in range(i + 1, j + 1):
        pq = p16.iloc[q]; chk.append({"t": ts(days[q], 16, 0), "p": round(float(pq), 1), "yukseldi": bool(pq > prev), "gun": q - i}); prev = pq
    out.append({
        "id": len(out), "d": str(d.date()), "ex": str(ex.date()), "net": round(float(r.net), 1), "tg": int(r.tutus_gun),
        "giris_t": u0, "giris_p": round(float(r.giris), 1), "giris_bid": round(float(o[i0]), 1), "cikis_t": ux, "cikis_p": round(float(o[ix]), 1),
        "twap": round(float(dp.tw.iloc[i]), 1), "p15": round(float(dp.o900.iloc[i]), 1), "p0930": round(float(dp.o570.iloc[i]), 1),
        "mae_t": int(t[i0 + jm]) if len(seg) else u0, "mae_p": round(float(seg.min()), 1) if len(seg) else None, "mae": round(float(r.mae), 1), "mfe": round(float(r.mfe), 1),
        "son_saat": round(float(r.son_saat), 1), "twap_uz": round(float(r.twap_uz), 1), "seans": round(float(r.seans_ret), 1), "gun_ret": round(float(r.gun_ret), 1),
        "vix": None if not np.isfinite(r.vix) else round(float(r.vix), 2), "opex_k": int(r.opex_k), "olay": int(r.olay), "rsi2": round(float(r.rsi2), 1),
        "sma200": round(float(r.sma200_uz), 0) if np.isfinite(r.sma200_uz) else None, "chk": chk,
        "bar": [[int(kk) // 60 - u0 // 60, round(float(x.o), 1), round(float(x.h), 1), round(float(x.l), 1), round(float(x.c), 1)] for kk, x in df.iterrows()],
    })
def _temiz(x):  # NaN/inf → null (tarayıcı JSON.parse NaN kabul etmez)
    if isinstance(x, float):
        return x if np.isfinite(x) else None
    if isinstance(x, dict):
        return {k: _temiz(v) for k, v in x.items()}
    if isinstance(x, list):
        return [_temiz(v) for v in x]
    return x
s = json.dumps(_temiz(out), separators=(",", ":"), ensure_ascii=False, allow_nan=False)
(HERE / "results/replay.json").write_text(s); print(len(out), "işlem", round(len(s) / 1e6, 2), "MB")
