"""cd_analiz.py — PROTOCOL.md: F (günlük bağlam filtresi), M (çok değişkenli), X (yüksek isabetli çıkış), SL/TP profili. python cd_analiz.py"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

from cd_veri import CATS, FEATS, HERE, X_CELLS

NB = 3000
RNG = np.random.default_rng(83)
TEST_MAIN = ["DUKA_NDX", "DUKA_DAX"]
BLIND = ["MT5_US500", "MT5_US30", "MT5_US2000"]
ALLF = FEATS + CATS


def load() -> pd.DataFrame:
    T = pd.read_parquet(HERE / "cache/olaylar.parquet")
    T["d"] = pd.to_datetime(T.d)
    T["grp"] = np.where(T.set == "G2016", "G2016_" + T.idx, T.set)
    T["blk"] = T.grp + "|" + T.d.dt.to_period("M").astype(str)
    return T


def sharpe(d: pd.Series, pnl: pd.Series) -> float:
    days = pd.bdate_range(d.min(), d.max())
    s = pnl.groupby(d.values).sum().reindex(days).fillna(0)
    return round(float(s.mean() / s.std() * np.sqrt(252)), 3) if s.std() > 0 else np.nan


def boot(v: np.ndarray, blk: np.ndarray) -> float:
    ub = np.unique(blk)
    idx = {u: np.flatnonzero(blk == u) for u in ub}
    return round(float(np.mean([v[np.concatenate([idx[u] for u in RNG.choice(ub, len(ub))])].mean() > 0 for _ in range(NB)])), 4)


def cvar5(v: pd.Series) -> float:
    s = np.sort(v.values)
    return float(s[:max(1, int(len(s) * 0.05))].mean())


# ───────── F ─────────
def mask(x: pd.DataFrame, r: dict) -> pd.Series:
    """Hücreye (tertil/kategori) üyelik; eksik değer üye değil."""
    v = x[r["f"]]
    m = (v == r["val"]) if r["f"] in CATS else ((v >= r["lo"]) & (v < r["hi"]))
    return m & v.notna()


def candidates(K: pd.DataFrame) -> list[dict]:
    out = []
    mu = K.base.mean()
    for f in ALLF:
        z = K.dropna(subset=[f])
        if len(z) < 150:
            continue
        if f in CATS:
            bins = [{"f": f, "val": v} for v in sorted(z[f].unique())]
        else:
            q = z[f].quantile([1 / 3, 2 / 3]).values
            bins = [{"f": f, "lo": a, "hi": b, "ter": t} for t, (a, b) in
                    enumerate([(-np.inf, q[0]), (q[0], q[1]), (q[1], np.inf)])]
        stats = []
        for b in bins:
            mm = mask(z, b)
            stats.append((b, float(z[mm].base.mean()) if mm.sum() else np.nan, int(mm.sum())))
        stats = [s for s in stats if s[2] >= 30]
        if len(stats) < 2:
            continue
        worst = min(stats, key=lambda s: s[1])[0]
        best = max(stats, key=lambda s: s[1])[0]
        for form, b in (("D", worst), ("K", best)):
            r = b | {"form": form}
            keep = keep_mask(K, r)
            kept = K[keep].base
            t = (kept.mean() - mu) / (kept.std(ddof=1) / np.sqrt(len(kept)))
            out.append(r | {"t": float(t), "kesif_fark": float(kept.mean() - mu), "kesif_kalan": int(keep.sum()),
                            "kesif_isabet": [round(float((K.base > 0).mean()), 3), round(float((kept > 0).mean()), 3)]})
    return out


def keep_mask(x: pd.DataFrame, r: dict) -> pd.Series:
    """D: hücreyi at (eksik değer tutulur). K: yalnız hücreyi tut."""
    m = mask(x, r)
    return ~m if r["form"] == "D" else m


def judge_filter(T: pd.DataFrame, keep_fn, P_need: float) -> dict:
    res, diffs, blks = {}, [], []
    for g in TEST_MAIN + ["MT5_NAS100"] + BLIND + sorted(T[T.set == "G2016"].grp.unique()):
        x = T[T.grp == g]
        if not len(x):
            continue
        k = keep_fn(x)
        kept = x[k]
        res[g] = {"n": len(x), "kalan": int(k.sum()), "ort": round(float(x.base.mean()), 1),
                  "ort_kalan": round(float(kept.base.mean()), 1) if k.any() else None,
                  "fark": round(float(kept.base.mean() - x.base.mean()), 1) if k.any() else None,
                  "isabet": [round(float((x.base > 0).mean()), 3), round(float((kept.base > 0).mean()), 3) if k.any() else None],
                  "sharpe": [sharpe(x.d, x.base), sharpe(x.d, x.base.where(k, 0.0))],
                  "atilan_ort": round(float(x[~k].base.mean()), 1) if (~k).any() else None}
        if g in TEST_MAIN or g.startswith("G2016"):
            diffs.append((kept.base - x.base.mean()).values)
            blks.append(kept.blk.values)
    P = boot(np.concatenate(diffs), np.concatenate(blks)) if diffs else np.nan
    ok = {"ndx_dax": all(res[g]["fark"] is not None and res[g]["fark"] > 0 and res[g]["isabet"][1] > res[g]["isabet"][0] for g in TEST_MAIN),
          "havuz_P": P >= P_need, "kor_2_3": sum((res[g]["fark"] or -1) > 0 for g in BLIND) >= 2,
          "sharpe": res["DUKA_NDX"]["sharpe"][1] > res["DUKA_NDX"]["sharpe"][0]}
    neg = any(res[g]["fark"] is None or res[g]["fark"] <= 0 for g in TEST_MAIN)
    return {"olcum": res, "havuz_P": P, "olcut": ok, "hukum": "B" if all(ok.values()) else ("X" if neg else "C")}


# ───────── M ─────────
def m_family(T: pd.DataFrame) -> dict:
    K = T[T.set == "KESIF"]
    med = K[ALLF].median()
    mu, sd = K[ALLF].fillna(med).mean(), K[ALLF].fillna(med).std().replace(0, 1)
    Z = lambda x: ((x[ALLF].fillna(med) - mu) / sd).values  # noqa: E731
    y = (K.base > 0).astype(int).values
    out = {}
    for nm, mdl in (("lojistik", LogisticRegression(C=0.5, max_iter=2000)),
                    ("gbm", GradientBoostingClassifier(n_estimators=200, max_depth=2, learning_rate=0.05, subsample=0.8, random_state=0))):
        mdl.fit(Z(K), y)
        pk = mdl.predict_proba(Z(K))[:, 1]
        thr = float(np.quantile(pk, 1 / 3))
        T[f"p_{nm}"] = mdl.predict_proba(Z(T))[:, 1]
        j = judge_filter(T, lambda x, c=f"p_{nm}": x[c] >= thr, 0.983)
        j["auc"] = {g: round(float(roc_auc_score(T[T.grp == g].base > 0, T[T.grp == g][f"p_{nm}"])), 3)
                    for g in TEST_MAIN + ["MT5_NAS100"] + BLIND if T[T.grp == g].base.gt(0).nunique() == 2}
        j["auc_kesif_ici"] = round(float(roc_auc_score(y, pk)), 3)
        j["esik"] = thr
        out[nm] = j
    return out


# ───────── X ─────────
def x_stats(x: pd.DataFrame, c: str) -> dict:
    return {"n": len(x), "ort": round(float(x[c].mean()), 1), "fark": round(float((x[c] - x.base).mean()), 1),
            "isabet": [round(float((x.base > 0).mean()), 3), round(float((x[c] > 0).mean()), 3)],
            "sharpe": [sharpe(x.d, x.base), sharpe(x.d, x[c])], "cvar5": [round(cvar5(x.base), 0), round(cvar5(x[c]), 0)]}


def x_family(T: pd.DataFrame) -> dict:
    K = T[T.set == "KESIF"]
    h0 = (K.base > 0).mean()
    tab = {c: x_stats(K, c) for c in X_CELLS}
    elig = [c for c in X_CELLS if tab[c]["isabet"][1] >= h0 + 0.10]
    sel = sorted(elig, key=lambda c: tab[c]["fark"], reverse=True)[:2]
    out = {"kesif_tablo": tab, "uygun": len(elig), "secilen": sel, "hucre": {}}
    for c in sel:
        res, diffs, blks = {}, [], []
        for g in TEST_MAIN + ["MT5_NAS100"] + BLIND + sorted(T[T.set == "G2016"].grp.unique()):
            x = T[T.grp == g]
            res[g] = x_stats(x, c)
            if g in TEST_MAIN or g.startswith("G2016"):
                diffs.append((x[c] - x.base).values)
                blks.append(x.blk.values)
        P = boot(np.concatenate(diffs), np.concatenate(blks))
        ok = {"ndx_dax": all(res[g]["fark"] > 0 and res[g]["isabet"][1] > res[g]["isabet"][0] for g in TEST_MAIN),
              "havuz_P": P >= 0.975, "kor_2_3": sum(res[g]["fark"] > 0 for g in BLIND) >= 2,
              "sharpe": res["DUKA_NDX"]["sharpe"][1] > res["DUKA_NDX"]["sharpe"][0],
              "cvar5": all(res[g]["cvar5"][1] >= 2 * res[g]["cvar5"][0] for g in TEST_MAIN)}
        neg = any(res[g]["fark"] <= 0 for g in TEST_MAIN)
        out["hucre"][c] = {"olcum": res, "havuz_P": P, "olcut": ok, "hukum": "B" if all(ok.values()) else ("X" if neg else "C")}
    out["test_tablo"] = {g: {c: x_stats(T[T.grp == g], c) for c in X_CELLS} for g in TEST_MAIN + ["MT5_NAS100"]}
    return out


def profile(T: pd.DataFrame) -> dict:
    out = {}
    for nm, x in (("KESIF", T[T.set == "KESIF"]), ("TEST_NDX_DAX", T[T.grp.isin(TEST_MAIN)])):
        o = {"sinif": x.cls.value_counts().to_dict()}
        for f in ALLF:
            a, b = x[x.cls == "SL"][f].dropna(), x[x.cls == "TP"][f].dropna()
            if len(a) < 8 or len(b) < 8:
                continue
            obs = a.mean() - b.mean()
            pool = np.concatenate([a, b])
            perm = [(lambda p: p[:len(a)].mean() - p[len(a):].mean())(RNG.permutation(pool)) for _ in range(2000)]
            o[f] = {"SL": round(float(a.mean()), 4), "TP": round(float(b.mean()), 4), "p": round(float(np.mean(np.abs(perm) >= abs(obs))), 3)}
        out[nm] = o
    return out


def main() -> None:
    T = load()
    K = T[T.set == "KESIF"]
    res = {"taban": T.groupby("grp").agg(n=("base", "size"), ort=("base", "mean"), isabet=("base", lambda s: (s > 0).mean()))
           .round(3).to_dict("index")}
    cands = candidates(K)
    seen, sel = set(), []
    for c in sorted(cands, key=lambda r: r["t"], reverse=True):
        if c["f"] not in seen:
            sel.append(c)
            seen.add(c["f"])
        if len(sel) == 3:
            break
    res["F"] = {"aday": len(cands), "en_iyi10": sorted(cands, key=lambda r: r["t"], reverse=True)[:10], "hucre": []}
    for r in sel:
        j = judge_filter(T, lambda x, r=r: keep_mask(x, r), 0.983)
        res["F"]["hucre"].append({"kural": r} | j)
        print("F", r["form"], r["f"], {k: v for k, v in r.items() if k in ("lo", "hi", "val", "t", "kesif_fark", "kesif_isabet")},
              j["hukum"], j["olcut"], "P", j["havuz_P"],
              {g: (j["olcum"][g]["fark"], j["olcum"][g]["isabet"]) for g in TEST_MAIN + BLIND + ["MT5_NAS100"]}, flush=True)
    res["M"] = m_family(T)
    for nm, j in res["M"].items():
        print("M", nm, j["hukum"], j["olcut"], "P", j["havuz_P"], "AUC", j["auc"], "kesif", j["auc_kesif_ici"],
              {g: (j["olcum"][g]["fark"], j["olcum"][g]["isabet"]) for g in TEST_MAIN}, flush=True)
    res["X"] = x_family(T)
    print("X uygun", res["X"]["uygun"], "secilen", res["X"]["secilen"])
    for c, j in res["X"]["hucre"].items():
        print("X", c, j["hukum"], j["olcut"], "P", j["havuz_P"],
              {g: (j["olcum"][g]["fark"], j["olcum"][g]["isabet"], j["olcum"][g]["cvar5"]) for g in TEST_MAIN + BLIND + ["MT5_NAS100"]}, flush=True)
    res["profil"] = profile(T)
    (HERE / "results").mkdir(exist_ok=True)
    (HERE / "results/analiz.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
