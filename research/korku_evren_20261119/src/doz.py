"""doz.py — EK-1 betimleyici: TWAP uzaklığı kovalarına göre korku gecesi paket (OPEX + XP) ortalaması. python doz.py"""
import json, warnings
import numpy as np, pandas as pd
import esik as E
warnings.filterwarnings("ignore")
EDGES = [-1e9, -50, -40, -30, -20, -10, 0]

def main():
    F = E.feeds()
    rows = []
    for nm, (b, st) in F.items():
        t = E.build_cell(b, st, nm, lambda f: (f.twap_uz <= 0) & (f.son_saat < 0))
        _, f, _ = E.VR.entry_features(b, st)
        t["twap_uz"] = f.twap_uz.reindex(pd.DatetimeIndex(t.d)).values
        rows.append(t)
    A = pd.concat(rows, ignore_index=True)
    A["kova"] = pd.cut(A.twap_uz, EDGES, labels=["<=-50", "-50..-40", "-40..-30", "-30..-20", "-20..-10", "-10..0"])
    out = {}
    for era in ("KESIF", "TEST"):
        for grp, sel in (("MT5", A.besleme.isin(E.MT5)), ("DUKA", A.besleme == "DUKA_NDX")):
            z = A[sel & (A.donem == era)]
            g = z.groupby("kova").net.agg(["size", "mean", lambda x: (x > 0).mean() * 100]).round(1)
            g.columns = ["n", "ort", "isabet_%"]
            out[f"{grp}_{era}"] = g.to_dict("index")
            print(grp, era); print(g.to_string())
    json.dump(out, open(E.RES / "doz.json", "w"), indent=1, ensure_ascii=False, default=str)

if __name__ == "__main__":
    main()
