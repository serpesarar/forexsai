"""QS-02 Tur 3 (EK-2): H3 coşku ∧ boşluk ≤ −%1 → kısa; kontrol coşkusuz boşluk ≤ −%1 kısa."""
import json
from pathlib import Path
import numpy as np, pandas as pd
from scipy.stats import binomtest
from qs02b import FOREIGN, ND, END, load_yahoo_csv, clean, frame, st

H = Path(__file__).resolve().parent


def h3(t, cost):
    v = t.valid & t.valid.shift(1, fill_value=False)
    E = (t.r1 >= 0.015) & (t.k1 >= 0.75); G = t.gap <= -0.01
    s = -(t.C / t.O - 1) * 1e4 - cost
    return {"H3": s[v & E & G], "kontrol": s[v & ~E & G]}


res = {}
for nm in FOREIGN:
    t = frame(clean(load_yahoo_csv(nm)))
    if len(t) >= 500:
        res[nm] = {k: st(x) for k, x in h3(t, 3.0).items()}
for nm in ("SPY", "IWM", "QQQ"):
    x = pd.read_parquet(ND / f"{nm}.parquet"); x = x[(x.index >= "1999-03-10") & (x.index < END)].assign(valid=True)
    res[nm] = {k: st(y) for k, y in h3(frame(x, adj=True), 2.0).items()}
fm = [m for m in FOREIGN if m in res and res[m]["H3"].get("n", 0) >= 10 and res[m]["kontrol"].get("n", 0) >= 10]
hv = [res[m]["H3"]["ort"] for m in fm]; kv = [res[m]["kontrol"]["ort"] for m in fm]
pos = sum(v > 0 for v in hv); sp = binomtest(pos, len(hv), 0.5, alternative="greater").pvalue
fark = float(np.mean(np.array(hv) - np.array(kv)))
c1 = np.mean(hv) > 0 and pos >= 0.6 * len(hv) and sp <= 0.10
c2 = all(res[e]["H3"].get("ort", -1) > 0 for e in ("SPY", "IWM"))
hk = {"piyasa": len(hv), "arti": int(pos), "havuz": round(float(np.mean(hv)), 1), "kontrol_havuz": round(float(np.mean(kv)), 1),
      "fark": round(fark, 1), "isaret_p": round(float(sp), 3), "sinif": "B-" if (c1 and c2 and fark > 0) else "X"}
res["hukum"] = hk
(H / "results/qs02e.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str))
for m, r in res.items():
    if m != "hukum":
        print(f"{m:7s} H3 {r['H3'].get('ort', float('nan')):7.1f} ({r['H3'].get('n', 0):3d})  kontrol {r['kontrol'].get('ort', float('nan')):7.1f} ({r['kontrol'].get('n', 0):3d})")
print(hk)
