"""ek1.py — PROTOCOL EK-1: A(18:00, −40) sağlamlık/mekanizma + R(−60, 16:00) E116 karşı kolu. python ek1.py"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

import motor as M

FEEDS = {"DUKA_NDX": ("18:00", "18:05", "18:15", "18:30"), "NQ": ("18:00", "18:05", "18:15", "18:30"),
         "MT5_NAS100": ("18:00", "18:30"), "EET30": ("18:00", "18:30"),
         "MT5_US500": ("18:00", "18:30"), "MT5_US30": ("18:00", "18:30"), "MT5_US2000": ("18:00", "18:30")}
KS = (30, 40, 50, 60)
ERN = {pd.Timestamp(k) for k in json.loads((M.ROOT / "research/ksg_derin_20261119/data/earnings.json").read_text())}


def add_rows(F: M.Feed, N: pd.DataFrame, times: tuple) -> pd.DataFrame:
    rows = []
    for r in N.itertuples():
        d, nd = r.d.date(), r.nd.date()
        i16, i930 = F.ix(M.ts(d, 16, 0)), F.ix(M.ts(nd, 9, 30))
        E = F.o[i16] + F.sp[i16]
        x = {"d": r.d, "ksg": r.ksg, "base": r.base, "sp16": F.sp[i16]}
        for t in times:
            j = F.ix(M.ts(d, *M.hm(t)))
            ok = j is not None and i16 < j < i930
            x[f"pnl_{t}"] = (F.o[j] / E - 1) * 1e4 if ok else np.nan
            x[f"inc_{t}"] = (F.o[i930] / (F.o[j] + F.sp[j]) - 1) * 1e4 - M.FIN * (r.nd - r.d).days if ok else np.nan
            x[f"sp_{t}"] = F.sp[j] if ok else np.nan
        rows.append(x)
    return pd.DataFrame(rows)


def dist(v: pd.Series) -> dict:
    v = v.dropna().sort_values()
    if not len(v):
        return {"n": 0}
    return {"n": len(v), "ort": round(float(v.mean()), 1), "medyan": round(float(v.median()), 1), "isabet": round(float((v > 0).mean()), 3),
            "en_iyi5_haric": round(float(v.iloc[:-5].mean()), 1) if len(v) > 5 else None, "en_kotu": round(float(v.min()), 1)}


def a_block(name: str, times: tuple) -> dict:
    b, st = M.load(name)
    F = M.Feed(b, st)
    N = M.table(name)
    if name == "MT5_US500":
        N = N[N.d >= "2018-06-01"]
    X = add_rows(F, N, times)
    K, C = X[X.ksg], X[~X.ksg]
    out = {"spread_16_vs_18": [round(float(K.sp16.median()), 3), round(float(K[f"sp_{times[0]}"].median()), 3)]}
    for t in times:
        for k in KS:
            a = K[K[f"pnl_{t}"] <= -k]
            out[f"{t}|{k}"] = dist(a[f"inc_{t}"]) | {"karsi_kol": dist(C.loc[C[f"pnl_{t}"] <= -k, f"inc_{t}"])}
    a = K[K["pnl_18:00"] <= -40]
    out["yillar_18_40"] = {int(y): [len(g), round(float(g["inc_18:00"].mean()), 1)] for y, g in a.groupby(a.d.dt.year)}
    out["bilanco_ortusme_18_40"] = {"n": int(a.d.isin(ERN).sum()), "bilanco_ort": dist(a[a.d.isin(ERN)]["inc_18:00"]),
                                    "bilancosuz": dist(a[~a.d.isin(ERN)]["inc_18:00"])}
    return out


def r_counter(name: str) -> dict:
    N = M.add_rescue(M.table(name))
    out = {}
    for lab, z in (("KSG", N[N.ksg]), ("KSG_degil", N[~N.ksg])):
        lose = z[(z.x930 <= -60) & z["hold_16:00"].notna()]
        out[lab] = dist(lose["hold_16:00"] - lose.base)
    return out


def main() -> None:
    res = {"A": {}, "R_karsi_kol": {}}
    for f, times in FEEDS.items():
        res["A"][f] = a_block(f, times)
        print(f, json.dumps({k: v for k, v in res["A"][f].items() if k.startswith(("18:00|40", "18:30|40", "spread", "yillar", "bilanco"))
                             or k.endswith("|40")}, ensure_ascii=False), flush=True)
    for f in ("DUKA_NDX", "MT5_NAS100", "EET30", "NQ", "MT5_US500", "MT5_US30", "MT5_US2000"):
        res["R_karsi_kol"][f] = r_counter(f)
        print("R", f, res["R_karsi_kol"][f], flush=True)
    (M.HERE / "results/ek1.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
