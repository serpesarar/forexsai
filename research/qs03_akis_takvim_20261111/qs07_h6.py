"""QS-07 EK-2 H6: Avrupa son seansı — kör Euro bölgesi endeksleri + broker GER40."""
import json, sys
import numpy as np, pandas as pd
from r1_dengeleme import px, st, H
from qs04 import monthly, side
from qs07_h4h5 import eu_bond
sys.path.insert(0, str(H.parent / "kazanan_turev_20261111"))
from ortak import Mkt  # noqa: E402
FD = H.parent / "geri_cekilme_20261106/data"
RNG = np.random.default_rng(79)


def load_oc(nm):
    if nm == "STOXX50E":
        x = pd.read_parquet(H / "data/STOXX50E.parquet")
    else:
        x = pd.read_csv(FD / f"{nm}.csv"); x.index = pd.to_datetime(x.Date.str[:10])
    x = x[(x.Close > 0) & (x.Open > 0)]
    valid = ((x.Open - x.Close.shift(1)).abs() > 1e-9) & (x.High > x.Low)
    return x.Open, x.Close, valid


def son_seans(nm, bond):
    O, C, valid = load_oc(nm)
    M = monthly(C, bond, {"_": C}); M = M[(M.d_s >= "2004-10-01") & (M.d_s < "2026-11-01")].reset_index(drop=True)
    s = side(M.dm.to_numpy()); v = []
    for k, r in M.iterrows():
        if s[k] == 0 or not bool(valid.get(r.d_D, False)):
            continue
        v.append(s[k] * (C.loc[r.d_D] / O.loc[r.d_D] - 1) * 1e4 - 3.0)
    return np.array(v)


bond = eu_bond(); res = {}
for nm in ("FCHI", "AEX", "IBEX", "STOXX50E"):
    res[nm] = st(son_seans(nm, bond))
means = [res[n]["ort"] for n in res]
B = 5000; boots = []
arrs = [son_seans(n, bond) for n in ("FCHI", "AEX", "IBEX", "STOXX50E")]
for _ in range(B):
    boots.append(np.mean([a[RNG.integers(0, len(a), len(a))].mean() for a in arrs]))
res["havuz"] = {"ort": round(float(np.mean(means)), 1), "P": round(float((np.array(boots) > 0).mean()), 3), "arti": f"{sum(m > 0 for m in means)}/4"}
# broker GER40
dax = px("GDAXI", "Close"); M = monthly(dax, bond, {"_": dax}); M = M[M.d_s >= "2018-06-01"].reset_index(drop=True); s = side(M.dm.to_numpy())
mk = Mkt("GER40"); g = []
for k, r in M.iterrows():
    if s[k] == 0:
        continue
    i, j = mk.at(r.d_D + pd.Timedelta(hours=3)), mk.at(r.d_D + pd.Timedelta(hours=11, minutes=30))
    if i < 0 or j < 0:
        continue
    g.append(s[k] * (mk.o[j] - mk.o[i]) / mk.o[i] * 1e4 - mk.cost(i) / mk.o[i] * 1e4)
res["GER40_broker_son_seans"] = st(np.array(g))
c1 = sum(m > 0 for m in means) >= 3 and res["havuz"]["P"] >= .9
c2 = res["GER40_broker_son_seans"].get("ort", -1) > 0
res["sinif"] = "B-" if c1 and c2 else ("C+" if c1 else "X")
(H / "results/qs07_h6.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str))
print(json.dumps(res, indent=1, ensure_ascii=False, default=str))
