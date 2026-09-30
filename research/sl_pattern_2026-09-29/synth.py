"""Sentetik girişlerle yapısal test: kilit kuralı fiyat sürecinin kendisinden mi geliyor?

Her 15 dk'da bir (piyasa açıkken) varsayımsal BUY ve SELL; TP/SL = fiyatın %'si.
Martingale altında hiçbir çıkış kuralı beklentiyi değiştiremez → sentetik Δ>0 ise
bu ölçekte ortalamaya dönüş (TP yolunun %60'ından geri dönme eğilimi) yapısaldır.
"""
import sys
import numpy as np
import pandas as pd
from sim import simulate

SPREAD = {"USOIL.FOREX": 0.03, "NDX.INDX": 1.5, "GDAXI.INDX": 1.5}


def paths_for(sym: str, step: int = 15, horizon: int = 1440):
    m = pd.read_pickle(f"fx_{sym}_1m.pkl")[["open", "high", "low", "close"]].astype(float)
    t = m.index.values
    H, L, C = m.high.values, m.low.values, m.close.values
    out = []
    for i in range(300, len(m) - horizon, step):
        # piyasa kapalı/boşluk: sonraki 60 bar 90 dk'dan uzun sürüyorsa atla
        if (t[i + 60] - t[i]) / np.timedelta64(1, "m") > 90:
            continue
        out.append((i, t[i], C[i]))
    return m, out


def run(sym, sl_pct, tp_pct, rules, direction, step=15, horizon=1440):
    m, pts = paths_for(sym, step, horizon)
    H, L, C = m.high.values, m.low.values, m.close.values
    sp = SPREAD[sym]
    res = {k: [] for k in ["base"] + list(rules)}
    times = []
    for i, ti, c in pts:
        e = c + sp if direction == "BUY" else c          # BUY ask'tan, SELL bid'den
        risk = e * sl_pct / 100; rr = tp_pct / sl_pct
        seg = slice(i + 1, i + 1 + horizon)
        if direction == "BUY":
            fav = (H[seg] - e) / risk; adv = (L[seg] - e) / risk; cls = (C[seg] - e) / risk
        else:
            fav = (e - (L[seg] + sp)) / risk; adv = (e - (H[seg] + sp)) / risk; cls = (e - (C[seg] + sp)) / risk
        p = dict(fav=np.r_[0, fav], adv=np.r_[0, adv], cls=np.r_[0, cls])
        res["base"].append(simulate(p, rr)[0])
        for k, r in rules.items():
            rr_ = dict(r)
            if "be_trig_f" in rr_: rr_["be_trig"] = rr_.pop("be_trig_f") * rr
            if "be_lock_f" in rr_: rr_["be_lock"] = rr_.pop("be_lock_f") * rr
            if "trail_trig_f" in rr_: rr_["trail_trig"] = rr_.pop("trail_trig_f") * rr
            if "trail_dist_f" in rr_: rr_["trail_dist"] = rr_.pop("trail_dist_f") * rr
            tpm = rr_.pop("tp_mult", 1.0)
            res[k].append(simulate(p, rr * tpm, **rr_)[0])
        times.append(ti)
    return pd.DataFrame(res, index=pd.to_datetime(times))


if __name__ == "__main__":
    sym = sys.argv[1] if len(sys.argv) > 1 else "USOIL.FOREX"
    rules = {"lock60_50": dict(be_trig_f=0.6, be_lock_f=0.5),
             "lock60_30": dict(be_trig_f=0.6, be_lock_f=0.3),
             "be60_0": dict(be_trig_f=0.6, be_lock_f=0.0),
             "lock80_50": dict(be_trig_f=0.8, be_lock_f=0.5),
             "tp0.6": dict(tp_mult=0.6),
             "trail50_30": dict(trail_trig_f=0.5, trail_dist_f=0.3)}
    geos = [(0.77, 1.04), (1.49, 1.04), (3.1, 1.04), (1.0, 1.0)] if sym == "USOIL.FOREX" else \
           [(0.35, 0.26), (0.5, 0.5), (0.25, 0.25)]
    for d in ("BUY", "SELL"):
        for sl, tp in geos:
            R = run(sym, sl, tp, rules, d)
            half = R.index < pd.Timestamp("2026-08-01")
            line = f"{sym} {d} SL%{sl} TP%{tp} n={len(R)} base ΣR={R.base.sum():.1f} WR={(R.base>0).mean():.2f} |"
            for k in rules:
                dd = R[k] - R.base
                line += f" {k}: {dd.mean()*100:+.1f}cR/işlem (H1 {dd[half].mean()*100:+.1f} H2 {dd[~half].mean()*100:+.1f})"
            print(line, flush=True)
