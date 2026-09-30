"""Aday kuralları C (sentetik, 15k, iki yön) + sembol kırılımlarında sına."""
import pickle
import numpy as np
import pandas as pd

A, B, C = pickle.load(open("zz_ds.pkl", "rb"))
O = pd.read_pickle("zz_grid.pkl")
FAM = {(1, 0): "K (klasik)", (1, -1): "Z→K", (2, 1): "K→Z→K", (2, -1): "Z→K→Z→K",
       (2, 0): "2.kâr", (3, 0): "3.kâr", (3, 1): "K→Z→K→Z→K", (3, -1): "Z→K→Z→K→Z→K"}
O["fam"] = [FAM.get((a, b), "?") for a, b in zip(O.n_p, O["first"])]
P4 = O[O.pass4].copy()
P4["score"] = np.minimum.reduce([P4.A_tr / 340, P4.A_te / 147, P4.B_h1 / 300, P4.B_h2 / 300])
cand = pd.concat([O[O.fam.isin(["K (klasik)", "Z→K"])],
                  P4.sort_values("score", ascending=False).groupby("fam").head(60)]).drop_duplicates(
    subset=["n_p", "first", "P", "Pa", "L", "age", "lock", "lock_tp", "action"])


def kw(r):
    return dict(n_p=int(r.n_p), first=int(r["first"]), P=float(r.P),
                Pa=None if pd.isna(r.Pa) else float(r.Pa), L=float(r.L), age=int(r.age),
                lock=float(r.lock), lock_tp=bool(r.lock_tp), action=int(r.action), delay=2)


Cs = C.meta.sym.values; Cd = C.meta.dir.values
Bs = B.meta.sym.values; As = A.meta.sym.values
rows = []
for _, r in cand.iterrows():
    Rc, _ = C.run(**kw(r)); d = Rc - C.base
    Rb, _ = B.run(**kw(r)); db = Rb - B.base
    Ra, _ = A.run(**kw(r)); da = Ra - A.base
    row = {**kw(r), "fam": r.fam, "A_dR": r.A_dR, "A_usd": r.A_usd, "B_dR": r.B_dR,
           "pass4": r.pass4, "A_saved": r.A_saved, "A_killed": r.A_killed,
           "B_saved": r.B_saved, "B_killed": r.B_killed,
           "C_dR": d.sum(), "C_per100": d.mean() * 100,
           "C_saved": int(((C.base < 0) & (Rc > C.base + 1e-9)).sum()),
           "C_killed": int(((C.base > 0) & (Rc < C.base - 1e-9)).sum())}
    for s in ("NDX.INDX", "GDAXI.INDX", "USOIL.FOREX"):
        k = s[:4]
        row[f"C_{k}"] = d[Cs == s].mean() * 100
        row[f"B_{k}"] = db[Bs == s].sum()
        row[f"A_{k}"] = da[As == s].sum()
    rows.append(row)
R = pd.DataFrame(rows)
R.to_pickle("zz_evalC.pkl")
pd.set_option("display.width", 260)
print("aday sayısı", len(R))
print(R.groupby("fam").agg(n=("C_dR", "size"), C_pos=("C_dR", lambda x: (x > 0).mean()),
                           C_med=("C_per100", "median"), C_best=("C_per100", "max")).round(3))
R["all_pos"] = (R.pass4) & (R.C_dR > 0)
print("A(tr,te)+B(h1,h2)+C hepsi pozitif:", R.all_pos.sum())
cols = ["fam", "action", "P", "Pa", "L", "age", "lock", "lock_tp", "A_dR", "A_usd", "A_saved", "A_killed",
        "B_dR", "B_saved", "B_killed", "C_per100", "C_saved", "C_killed", "C_NDX.", "C_GDAX", "C_USOI",
        "B_NDX.", "B_GDAX", "B_USOI"]
print(R[R.all_pos].sort_values("C_per100", ascending=False)[cols].head(30).round(2).to_string(index=False))
