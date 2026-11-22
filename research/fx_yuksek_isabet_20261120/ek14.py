"""EK-14a: tüm işlem tabloları S70 ölçütüyle yeniden (PROTOCOL.md EK-14)."""
import json, sys
import numpy as np, pandas as pd
import core

SEEN = {("F1", "53"), ("SPIKE", "51"), ("SPIKE", "35"), ("EK11", "B|D1|tp0.25|sl4.0"), ("EK11", "B|D1|tp0.25|sl100.0")}


def tables():
    for f in ("F1", "F2", "F3"):
        T = pd.read_parquet(core.RES / f"trades_{f}.parquet")
        T["per"] = np.where(T.time < core.SPLIT, "KESIF", "KOR")
        yield f, T, ["KOR"]
    G = pd.read_parquet(core.RES / "trades_G.parquet")
    G["cell"] = G.sig + "|" + G["mode"] + "|" + G.g.astype(str)
    yield "G", G, ["TEST", "KOR"]
    for f, key, val in (("EK2", "grp", None), ("SPIKE", "grp", "OLAY"), ("SPIKE7", "grp", "PLANLI"), ("EK11", "ev", True), ("EK13", "grp", "ANA")):
        T = pd.read_parquet(core.RES / f"trades_{f}.parquet")
        if f == "EK2":
            print("EK2 grp", T.grp.unique(), T.per.unique())
            val = T.grp.unique()[0] if len(T.grp.unique()) == 1 else [g for g in T.grp.unique() if "OLAY" in str(g).upper() or "ANA" in str(g).upper()][0]
        T = T[T[key] == val]
        pers = [p for p in ("TEST", "KOR") if p in set(T.per)]
        yield f, T, pers


def freq(g):
    d = pd.to_datetime(g.day)
    months = max(1.0, (d.max() - d.min()).days / 30.44) if len(d) else 1.0
    return round(g.day.nunique() / months, 2)


def main():
    out, sel_all = [], []
    for f, T, pers in tables():
        T = T.copy(); T["cell"] = T.cell.astype(str)
        K = T[T.per == "KESIF"]
        rows = []
        for c, g in K.groupby("cell"):
            rows.append({"tab": f, "cell": c, "pair": "HAVUZ", "frq": freq(g), **core.summ(g)})
        for (c, p), g in K.groupby(["cell", "pair"]):
            rows.append({"tab": f, "cell": c, "pair": p, "frq": freq(g), **core.summ(g)})
        H = pd.DataFrame(rows)
        H["t"] = H.t.astype(float)
        S = H[(H.wr >= 70) & (H.ort > 0) & (H.t >= 2) & (H.n >= 100) & (H.frq >= 3)].sort_values("t", ascending=False).head(5)
        print(f, "KEŞİF aday sayısı", int(((H.wr >= 70) & (H.ort > 0) & (H.t >= 2) & (H.n >= 100) & (H.frq >= 3)).sum()), "/", len(H), flush=True)
        for r in S.itertuples():
            g = T[T.cell == r.cell] if r.pair == "HAVUZ" else T[(T.cell == r.cell) & (T.pair == r.pair)]
            d = {"tab": f, "cell": r.cell, "pair": r.pair, "gorulmus": (f, r.cell) in SEEN,
                 "KESIF": {"n": r.n, "wr": r.wr, "ort": r.ort, "t": r.t, "frq": r.frq}}
            ok = True
            for pnm in pers:
                gg = g[g.per == pnm]
                s = core.summ(gg, boot=True) if len(gg) else {"n": 0}
                s["frq"] = freq(gg) if len(gg) else 0
                d[pnm] = s
                ok &= bool(s.get("n", 0) >= 60 and s["wr"] >= 70 and s["ort"] > 0 and s.get("P", 0) >= 0.90
                           and min(s["yari"]) >= 0 and s["frq"] >= 3 and (f in ("G", "EK2") or s["stres15"] > 0))
            d["S70_1_6"] = ok
            sel_all.append(d)
            print(json.dumps({k: v for k, v in d.items()}, ensure_ascii=False, default=str), flush=True)
    (core.RES / "ek14_secim.json").write_text(json.dumps(sel_all, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
