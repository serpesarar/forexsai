import json, itertools
from pathlib import Path
import numpy as np, pandas as pd
import kural as KR
HERE = Path(__file__).resolve().parents[1]
D = KR.D
F0, FA, CK, E = (0.33, 0.5), (0.5, 1.0, 1.5), ("c04", "c0930", "c1200"), (0.0, 25.0)
def pkg(z, f0, fa, ck, e):
    c = z[ck].values; v = z.net.values
    add = np.isfinite(c) & (c > e)
    val = f0 * v + np.where(add, fa * (v - c - 1.0), 0.0)
    return val
def m(v, d):
    eq = pd.Series(v, index=pd.to_datetime(d)).sort_index().cumsum()
    return {"toplam": float(v.sum()), "zarar": float(v[v < 0].sum()), "kotu10": float(np.sort(v)[:max(1, len(v) // 10)].mean()),
            "DD": float((eq - eq.cummax()).min()), "en_kotu": float(v.min())}
def rel(p, b):
    return {"kar×": round(p["toplam"] / b["toplam"], 3), "zarar×": round(p["zarar"] / b["zarar"], 3), "kotu10×": round(p["kotu10"] / b["kotu10"], 2),
            "DD×": round(p["DD"] / b["DD"], 2), "en_kotu": [round(b["en_kotu"]), round(p["en_kotu"])]}
K = D[(D.donem == "KESIF") & D.besleme.isin(["DUKA_NDX", "MT5_US500", "MT5_US30", "MT5_US2000"])]
grid = []
for f0, fa, ck, e in itertools.product(F0, FA, CK, E):
    # piyasa başına oran, sonra ortalama (her piyasa eşit ağırlık)
    rs = []
    for f, z in K.groupby("besleme"):
        rs.append(rel(m(pkg(z, f0, fa, ck, e), z.d.values), m(z.net.values, z.d.values)))
    grid.append({"f0": f0, "fa": fa, "ck": ck, "e": e, "kar×": round(np.mean([r["kar×"] for r in rs]), 3),
                 "zarar×": round(np.mean([r["zarar×"] for r in rs]), 3), "kar_min": round(min(r["kar×"] for r in rs), 3)})
G = pd.DataFrame(grid)
a = G[G["kar×"] >= 1.0].sort_values("zarar×").head(1)
b = G[G["zarar×"] <= 0.5].sort_values("kar×", ascending=False).head(1)
frozen = pd.concat([a.assign(sec="A_kar>=1_min_zarar"), b.assign(sec="B_zarar<=0,5_max_kar")]).to_dict("records")
print(G.sort_values("zarar×").head(12).to_string(index=False))
print("DONDURULAN:", frozen)
out = {"izgara_kesif": grid, "dondurulan": frozen, "TEST": {}}
for fr in frozen:
    rec = {}
    for f in ["DUKA_NDX", "MT5_NAS100", "MT5_US500", "MT5_US30", "MT5_US2000"]:
        for e_ in ("KESIF", "TEST"):
            z = D[(D.besleme == f) & (D.donem == e_)]
            p = pkg(z, fr["f0"], fr["fa"], fr["ck"], fr["e"])
            rec[f"{f}_{e_}"] = rel(m(p, z.d.values), m(z.net.values, z.d.values))
    out["TEST"][fr["sec"]] = rec
    print("\n", fr["sec"], fr)
    for k, v in rec.items(): print("  ", k, v)
(HERE / "results/ek3_kademe.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))
