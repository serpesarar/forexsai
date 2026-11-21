"""kq_analiz.py — KQ-01 (PROTOCOL.md): kuyruk anatomisi (A) + tutuş koruması (G), KEŞİF'te seç, TEST'te sına.

python kq_analiz.py → results/analiz.json
"""
from __future__ import annotations

import itertools
import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu
from sklearn.metrics import roc_auc_score

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "research/caprev_derin_20261120/src"))
import cd_analiz as CA  # noqa: E402

TEST_MAIN, BLIND = CA.TEST_MAIN, CA.BLIND
MAXS = 5
PF = ["z", "dz", "vix", "vixchg", "term", "br", "clv", "ll", "nobounce"]


# ───────── koruma hücreleri ─────────
def single_cells() -> dict[str, tuple[str, callable]]:
    C: dict[str, tuple[str, callable]] = {}
    for a in (0.5, 1.0, 1.5, 2.0):
        C[f"G1_z{a}"] = ("G1", lambda f, a=a: f["z"] <= -a)
    for v in (0.10, 0.20, 0.30):
        C[f"G2_vixchg{v}"] = ("G2", lambda f, v=v: np.isfinite(f["vixchg"]) and f["vixchg"] >= v)
    for L in (30, 35, 40):
        C[f"G3_vix{L}"] = ("G3", lambda f, L=L: np.isfinite(f["vix"]) and f["vix"] >= L)
    C["G4_altdip"] = ("G4", lambda f: f["s"] >= 1 and f["ll"])
    for q in (0.15, 0.25):
        C[f"G5_clv{q}"] = ("G5", lambda f, q=q: np.isfinite(f["clv"]) and f["clv"] <= q)
    for k in (2, 3):
        C[f"G6_br{k}"] = ("G6", lambda f, k=k: f["br"] >= k)
    for t in (1.05, 1.10):
        C[f"G7_term{t}"] = ("G7", lambda f, t=t: np.isfinite(f["term"]) and f["term"] >= t)
    C["G8_sekmeme"] = ("G8", lambda f: f["s"] >= 1 and f["nobounce"])
    for m in (1, 2, 3):
        C[f"G9_M{m}"] = ("G9", lambda f, m=m: f["s"] >= m)
    return C


SINGLE = single_cells()


def all_cells() -> dict[str, list[str]]:
    cells = {k: [k] for k in SINGLE}
    for a, b in itertools.combinations(SINGLE, 2):
        if SINGLE[a][0] != SINGLE[b][0]:
            cells[f"{a}|{b}"] = [a, b]
    return cells


CELLS = all_cells()


def simulate(ev: dict, guards: list[str] | None) -> tuple[float, int, str]:
    """(net bp, çıkış kapanışı, neden). guards None → korumasız X_5_3.0_kar."""
    n = len(ev["cl"])
    for s in range(n):
        if ev["stop_s"] is not None and ev["stop_s"] <= s:
            return ev["stop_res"], s, "stop"
        if ev["cl"][s] >= ev["E"]:
            return ev["res"][s], s, "kar"
        if s == MAXS or s == n - 1:
            return ev["res"][s], s, "sure"
        if guards and any(SINGLE[g][1](ev["pf"][s]) for g in guards):
            return ev["res"][s], s, "koruma"
    return ev["res"][n - 1], n - 1, "sure"


def frame(P: list[dict], cells: dict[str, list[str]]) -> pd.DataFrame:
    rows = []
    for ev in P:
        r = {"set": ev["set"], "idx": ev["idx"], "feed": ev["feed"], "d": ev["d"], "base": ev["base"], "dvol": ev["dvol"]}
        r["kar"], r["kar_s"], r["kar_why"] = simulate(ev, None)
        for c, g in cells.items():
            r[c] = simulate(ev, g)[0]
        rows.append(r)
    T = pd.DataFrame(rows)
    T["d"] = pd.to_datetime(T.d)
    T["grp"] = np.where(T.set == "G2016", "G2016_" + T.idx, T.set)
    T["blk"] = T.grp + "|" + T.d.dt.to_period("M").astype(str)
    return T


def stats(x: pd.DataFrame, c: str) -> dict:
    return {"n": len(x), "ort": round(float(x[c].mean()), 1), "fark": round(float((x[c] - x.base).mean()), 1),
            "fark_kar": round(float((x[c] - x.kar).mean()), 1),
            "isabet": [round(float((x.base > 0).mean()), 3), round(float((x.kar > 0).mean()), 3), round(float((x[c] > 0).mean()), 3)],
            "sharpe": [CA.sharpe(x.d, x.base), CA.sharpe(x.d, x.kar), CA.sharpe(x.d, x[c])],
            "cvar5": [round(CA.cvar5(x.base), 0), round(CA.cvar5(x.kar), 0), round(CA.cvar5(x[c]), 0)]}


# ───────── seçim + sınama ─────────
def select(T: pd.DataFrame) -> dict:
    K = T[T.set == "KESIF"]
    h0, cv0 = (K.base > 0).mean(), CA.cvar5(K.base)
    tab = {}
    for c in CELLS:
        tab[c] = {"fark": float((K[c] - K.base).mean()), "isabet": float((K[c] > 0).mean()), "cvar5": CA.cvar5(K[c])}
    out = {"kesif_taban": {"isabet": round(h0, 3), "cvar5": round(cv0, 0), "ort": round(float(K.base.mean()), 1)},
           "kesif_kar": stats(K, "kar")}
    for lim in (1.5, 2.0):
        elig = [c for c in CELLS if tab[c]["isabet"] >= h0 + 0.10 and tab[c]["cvar5"] >= lim * cv0]
        if elig:
            break
    rank = sorted(elig, key=lambda c: tab[c]["fark"], reverse=True)
    sel = rank[:2]
    if not any("|" not in c for c in sel):
        singles = [c for c in rank if "|" not in c]
        if singles:
            sel = [rank[0], singles[0]]
    out.update({"cvar_esik": lim, "uygun": len(elig), "secilen": sel,
                "kesif_ilk15": {c: {k: round(v, 3) for k, v in tab[c].items()} for c in rank[:15]},
                "kesif_tek": {c: {k: round(v, 3) for k, v in tab[c].items()} for c in SINGLE}})
    return out


def judge(T: pd.DataFrame, c: str) -> dict:
    res, diffs, blks = {}, [], []
    for g in TEST_MAIN + ["MT5_NAS100"] + BLIND + sorted(T[T.set == "G2016"].grp.unique()):
        x = T[T.grp == g]
        res[g] = stats(x, c)
        if g in TEST_MAIN or g.startswith("G2016"):
            diffs.append((x[c] - x.base).values)
            blks.append(x.blk.values)
    P = CA.boot(np.concatenate(diffs), np.concatenate(blks))
    ok = {"ndx_dax": all(res[g]["fark"] > 0 and res[g]["isabet"][2] > res[g]["isabet"][0] for g in TEST_MAIN),
          "havuz_P": P >= 0.975, "kor_2_3": sum(res[g]["fark"] > 0 for g in BLIND) >= 2,
          "sharpe": res["DUKA_NDX"]["sharpe"][2] > res["DUKA_NDX"]["sharpe"][0],
          "cvar5_2x": all(res[g]["cvar5"][2] >= 2 * res[g]["cvar5"][0] for g in TEST_MAIN),
          "cvar5_kar": res["DUKA_NDX"]["cvar5"][2] > res["DUKA_NDX"]["cvar5"][1]}
    neg = any(res[g]["fark"] <= 0 for g in TEST_MAIN)
    return {"olcum": res, "havuz_P": P, "olcut": ok, "hukum": "B" if all(ok.values()) else ("X" if neg else "C")}


# ───────── anatomi ─────────
def classify(ev: dict) -> str | None:
    if ev["cl"][0] >= ev["E"] or (ev["stop_s"] is not None and ev["stop_s"] == 0):
        return None                                      # tutulmayan (D0'da kârda ya da D0'da stop)
    net, s, why = simulate(ev, None)
    if why == "stop" or net <= -2 * ev["dvol"] * 1e4:
        return "COKUS"
    return "DONUS" if why == "kar" else "SURUNME"


def anatomy(P: list[dict], T0: pd.DataFrame) -> dict:
    ent = pd.read_parquet(ROOT / "research/caprev_derin_20261120/cache/olaylar.parquet")
    ent["d"] = pd.to_datetime(ent.d)
    ent = ent.set_index(["feed", "d"])
    rows = []
    for ev in P:
        c = classify(ev)
        if c is None:
            continue
        r = {"set": ev["set"], "feed": ev["feed"], "d": pd.Timestamp(ev["d"]), "cls": c}
        for s in (0, 1):
            if s < len(ev["pf"]) and not (ev["stop_s"] is not None and ev["stop_s"] <= s):
                for k in PF:
                    r[f"{k}_{s}"] = float(ev["pf"][s][k])
        key = (ev["feed"], pd.Timestamp(ev["d"]))
        if key in ent.index:
            e = ent.loc[key]
            e = e.iloc[0] if isinstance(e, pd.DataFrame) else e
            for k in CA.FEATS:
                r[f"giris_{k}"] = float(e[k]) if pd.notna(e[k]) else np.nan
        rows.append(r)
    A = pd.DataFrame(rows)
    feats = [c for c in A.columns if c.endswith("_0") or c.endswith("_1") or c.startswith("giris_")]
    out = {}
    for name, x in [("KESIF", A[A.set == "KESIF"]), ("TEST_2018_26", A[A.feed.isin(["DUKA_NDX", "DUKA_DAX", "MT5_NAS100"] + BLIND)]),
                    ("G2016", A[A.set == "G2016"])]:
        y = (x.cls == "COKUS").astype(int)
        tab = {"n": {k: int(v) for k, v in x.cls.value_counts().items()}}
        for f in feats:
            v = x[f]
            ok = v.notna()
            if ok.sum() < 20 or y[ok].sum() < 5 or (1 - y[ok]).sum() < 5:
                continue
            a, b = v[ok & (y == 1)], v[ok & (y == 0)]
            p = mannwhitneyu(a, b).pvalue
            auc = roc_auc_score(y[ok], v[ok])
            tab[f] = {"cokus": round(float(a.mean()), 3), "diger": round(float(b.mean()), 3), "p": round(float(p), 4),
                      "auc": round(float(auc), 3)}
        out[name] = tab
    return out


def tail_list(T: pd.DataFrame, cells: list[str]) -> dict:
    out = {}
    for g in ("DUKA_NDX", "DUKA_DAX"):
        x = T[T.grp == g].sort_values("kar").head(8)
        out[g] = [{"d": str(r.d.date()), "taban": round(r.base), "kar": round(r.kar), **{c: round(r[c]) for c in cells}}
                  for _, r in x.iterrows()]
    return out


def main() -> None:
    P = pickle.load(open(HERE / "cache/yollar.pkl", "rb"))
    T = frame(P, CELLS)
    old = CA.load()
    chk = {}
    for g in TEST_MAIN + ["MT5_NAS100"]:
        chk[g] = [round(float(T[T.grp == g].kar.mean()), 1), round(float(old[old.grp == g]["X_5_3.0_kar"].mean()), 1),
                  int((T.grp == g).sum()), int((old.grp == g).sum())]
    sel = select(T)
    out = {"tutarlilik_kar_yeni_eski_n": chk, "secim": sel, "anatomi": anatomy(P, T),
           "hucre": {c: judge(T, c) for c in sel["secilen"]}, "kuyruk_listesi": tail_list(T, sel["secilen"]),
           "tek_hucre_test": {c: {g: stats(T[T.grp == g], c) for g in TEST_MAIN} for c in SINGLE}}
    (HERE / "results").mkdir(exist_ok=True)
    json.dump(out, open(HERE / "results/analiz.json", "w"), ensure_ascii=False, indent=1, default=float)
    print(json.dumps({"chk": chk, "secilen": sel["secilen"], "esik": sel["cvar_esik"], "uygun": sel["uygun"],
                      "hukum": {c: (v["hukum"], v["olcut"], v["havuz_P"]) for c, v in out["hucre"].items()}}, ensure_ascii=False, indent=1))
    T.drop(columns=[c for c in CELLS if c not in sel["secilen"]]).to_pickle(HERE / "cache/sonuc.pkl")


if __name__ == "__main__":
    main()
