import json, numpy as np, pandas as pd
import vk as V
out = {}
for t in ("QQQ", "SPY"):
    x = V.ohlc(t); f = V.N.frame(t)
    c, o, h, l, idx = x.c.values, x.o.values, x.h.values, x.l.values, x.index
    k1 = (c <= (h + l) / 2 * 0.995) & (c < o); ii = np.flatnonzero(k1[:-1])
    tr = pd.DataFrame({"d": idx[ii], "net": (c[ii + 1] / c[ii] - 1) * 1e4 - 2 - V.FIN * (idx[ii + 1] - idx[ii]).days.values})
    on = np.log(f.o / f.c.shift(1)); idr = np.log(f.c / f.o)
    tug = V.N.pct(on.rolling(20).sum() - idr.rolling(20).sum()).reindex(tr.d).values
    r20 = (x.c / x.c.shift(20) - 1).reindex(tr.d).values
    s200 = (x.c > x.c.rolling(200).mean()).reindex(tr.d).values
    ok = np.isfinite(tug) & np.isfinite(r20); m = np.nan_to_num(tug) >= 0.8
    for nm, sub in (("r20_eksi", r20 < 0), ("r20_arti", r20 >= 0), ("SMA200_alti", ~s200), ("SMA200_ustu", s200)):
        out[f"{t}_{nm}"] = V.diff_stat(tr, m & ok & sub, ok & sub)
for k, v in out.items(): print(k, v)
V.RES.joinpath("ek3.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
