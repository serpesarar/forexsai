"""EK-2: K1 × çekişme kopya kontrolü."""
import json
import numpy as np, pandas as pd
import vk as V
out = {}
for t in ("QQQ", "SPY"):
    x = V.ohlc(t); f = V.N.frame(t)
    c, o, h, l, idx = x.c.values, x.o.values, x.h.values, x.l.values, x.index
    k1 = (c <= (h + l) / 2 * 0.995) & (c < o)
    ii = np.flatnonzero(k1[:-1])
    tr = pd.DataFrame({"d": idx[ii], "net": (c[ii + 1] / c[ii] - 1) * 1e4 - 2 - V.FIN * (idx[ii + 1] - idx[ii]).days.values,
                       "ard": np.r_[False, k1[:-1]][ii]})
    on = np.log(f.o / f.c.shift(1)); idr = np.log(f.c / f.o)
    tug = V.N.pct(on.rolling(20).sum() - idr.rolling(20).sum()).reindex(tr.d).values
    pon = V.N.pct(on.rolling(20).sum()).reindex(tr.d).values
    pid = V.N.pct(-idr.rolling(20).sum()).reindex(tr.d).values
    vx = V.vix().reindex(tr.d).values >= 18.4
    ok = np.isfinite(tug)
    m = np.nan_to_num(tug) >= 0.8
    for nm, sub in (("VIXust", vx), ("VIXalt", ~vx), ("ardisik", tr.ard.values), ("tekil", ~tr.ard.values), ("tum", np.ones(len(tr), bool))):
        out[f"{t}_K1_cekisme_{nm}"] = V.diff_stat(tr, m & ok & sub, ok & sub)
    out[f"{t}_K1_yalniz_gece"] = V.diff_stat(tr, (np.nan_to_num(pon) >= 0.8) & np.isfinite(pon), np.isfinite(pon))
    out[f"{t}_K1_yalniz_gunici_satis"] = V.diff_stat(tr, (np.nan_to_num(pid) >= 0.8) & np.isfinite(pid), np.isfinite(pid))
    yrs = tr[m & ok].groupby(tr[m & ok].d.dt.year).net.mean()
    out[f"{t}_K1_cekisme_yil_arti"] = f"{int((yrs > 0).sum())}/{len(yrs)}"
for k, v in out.items(): print(k, v)
V.RES.joinpath("ek2.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
