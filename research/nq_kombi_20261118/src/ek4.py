import json, sys, numpy as np, pandas as pd
import vk as V
R = V.ROOT
for p in ("research/korku_genislik_20261118/src", "research/fitil_kesisim_20261118/src"):
    sys.path.insert(0, str(R / p))
import gn, ksg_dogrulama as KD
G = gn.G
def tug(t, lag):
    f = V.N.frame(t); on = np.log(f.o / f.c.shift(1)); idr = np.log(f.c / f.o)
    return V.N.pct(on.rolling(20).sum() - idr.rolling(20).sum()).shift(lag)
out = {}
pool = {0: [], 1: []}
for feed, (b, st, t) in {"DUKA_NDX": (G.ndx_bars(), 60, "QQQ"), "MT5_NAS100": (KD.mt5_m30("NAS100"), 1800, "QQQ"),
                         "MT5_US500": (KD.mt5_m30("US500"), 1800, "SPY")}.items():
    n = gn.nts(b, st); n = n[n.K1].reset_index(drop=True)
    for lag in (1, 0):
        tg = tug(t, lag).reindex(pd.to_datetime(n.d)).values
        ok = np.isfinite(tg); m = np.nan_to_num(tg) >= 0.8
        for e in ("ESKI", "YENI"):
            em = (n.era == e).values
            out[f"{feed}_lag{lag}_{e}"] = V.diff_stat(n, m & ok & em, ok & em)
        pool[lag].append(n.assign(m=m, ok=ok))
for lag, L in pool.items():
    z = pd.concat(L, ignore_index=True)
    out[f"havuz_lag{lag}"] = V.diff_stat(z, z.m.values & z.ok.values, z.ok.values)
for k, v in out.items(): print(k, v)
V.RES.joinpath("ek4.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
