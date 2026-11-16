"""analyze.py — PROTOCOL §4 A1 (ortak özellik), A2 (model AUC), A3 (maliyetli kural). Çıktı results/analyze.json"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ndx_10y_1m_20261116/src"))
import lib  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "results"
FEATS = ["clv1", "clv5", "clv15", "clv60", "uw5", "lw5", "uw15", "lw15", "run_signed", "body5", "flip15", "r5", "r15", "r60b", "r240",
         "rng60", "volreg", "sess_pos", "dist_pc", "min_sess", "seans_kod", "dow", "vix"]
PERS = ("KESIF", "TEST", "BAGIMSIZ")
rng = np.random.default_rng(7)


def cohen(df, f, mask_a, mask_b):
    a, b = df.loc[mask_a, f].astype(float), df.loc[mask_b, f].astype(float)
    sp = np.sqrt((a.var() + b.var()) / 2)
    d = (a.mean() - b.mean()) / sp if sp > 0 else 0.0
    t = (a.mean() - b.mean()) / np.sqrt(a.var() / len(a) + b.var() / len(b)) if len(a) > 2 and len(b) > 2 else 0.0
    return float(d), float(t)


def a1(df) -> dict:
    out = {}
    for name, ma, mb in (("yon", lambda g: g.yon == 1, lambda g: g.yon == -1),
                         ("yapi", lambda g: g.yapi == "TREND", lambda g: g.yapi == "KARARSIZ")):
        res = {}
        for f in FEATS:
            row = {}
            for p in PERS:
                g = df[df.per == p]
                row[p] = cohen(g, f, ma(g), mb(g))
            ds = [row[p][0] for p in PERS]
            row["ortak"] = bool((all(x > 0 for x in ds) or all(x < 0 for x in ds)) and min(abs(x) for x in ds) >= 0.05
                                and min(abs(row[p][1]) for p in PERS) >= 3)
            res[f] = row
        # plasebo: gün içi etiket karıştırma → en büyük 'üç dönemde min |t|'
        mx = []
        for _ in range(100):
            sh = df.copy()
            sh["yon"] = sh.groupby("d").yon.transform(lambda s: rng.permutation(s.values))
            sh["yapi"] = sh.groupby("d").yapi.transform(lambda s: rng.permutation(s.values))
            best = 0
            for f in FEATS:
                ts = [cohen(sh[sh.per == p], f, ma(sh[sh.per == p]), mb(sh[sh.per == p]))[1] for p in PERS]
                if all(x > 0 for x in ts) or all(x < 0 for x in ts):
                    best = max(best, min(abs(x) for x in ts))
            mx.append(best)
        res["_plasebo_min_t_p95"] = float(np.percentile(mx, 95))
        out[name] = res
    return out


def a2(df) -> tuple[dict, dict]:
    out, models = {}, {}
    targets = {"yon": (df.yon != 0, lambda g: (g.yon == 1).astype(int)),
               "trend": (pd.Series(True, index=df.index), lambda g: (g.yapi == "TREND").astype(int))}
    for name, (keep, ylab) in targets.items():
        d = df[keep]
        tr = d[d.per == "KESIF"]
        m = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, max_leaf_nodes=15, min_samples_leaf=200,
                                           random_state=0).fit(tr[FEATS], ylab(tr))
        models[name] = m
        row = {}
        for p in ("TEST", "BAGIMSIZ"):
            g = d[d.per == p]
            y = ylab(g).values
            pr = m.predict_proba(g[FEATS])[:, 1]
            auc = roc_auc_score(y, pr)
            null = []
            for _ in range(200):
                yy = g.assign(_y=y).groupby("d")._y.transform(lambda s: rng.permutation(s.values)).values
                null.append(roc_auc_score(yy, pr))
            row[p] = {"auc": float(auc), "null_p95": float(np.percentile(null, 95)), "taban_oran": float(y.mean())}
        row["gecti"] = bool(all(row[p]["auc"] > row[p]["null_p95"] for p in ("TEST", "BAGIMSIZ")))
        # basit oynaklık-yalnız modeli (karşılaştırma): volreg + rng60 + seans
        vf = ["volreg", "rng60", "seans_kod", "min_sess"]
        mv = HistGradientBoostingClassifier(max_iter=200, learning_rate=0.05, max_leaf_nodes=15, min_samples_leaf=200,
                                            random_state=0).fit(tr[vf], ylab(tr))
        row["yalniz_oynaklik_auc"] = {p: float(roc_auc_score(ylab(d[d.per == p]), mv.predict_proba(d[d.per == p][vf])[:, 1]))
                                      for p in ("TEST", "BAGIMSIZ")}
        out[name] = row
    return out, models


def trade_R(m1, j, side, U) -> float:
    """j açılışında side yönünde gir (ask/bid), ±1U braket (BID yolu), 60 dk zaman çıkışı; R = net / U."""
    t0 = m1.t[j]
    entry_bid = m1.o[j]
    px_in = entry_bid + m1.spr[j] if side > 0 else entry_bid
    stop = px_in - U if side > 0 else px_in + U
    tp = px_in + U if side > 0 else px_in - U
    k, px, why, _ = lib.walk(m1, j, int(t0 + 3600), side, stop, tp)
    return side * (px - px_in) / U


def a3(df, models, m1) -> dict:
    out = {}
    d = df.copy()
    d["p_trend"] = models["trend"].predict_proba(d[FEATS])[:, 1]
    d["p_up"] = models["yon"].predict_proba(d[FEATS])[:, 1]
    kes = d[d.per == "KESIF"]
    thr_t = float(kes.p_trend.quantile(0.9))
    thr_u = float((kes.p_up - 0.5).abs().quantile(0.9))
    rules = {"trend_momentum": (d.p_trend >= thr_t, np.sign(d.r15)),
             "yon_model": ((d.p_up - 0.5).abs() >= thr_u, np.where(d.p_up >= 0.5, 1, -1)),
             "taban_tum_momentum": (pd.Series(True, index=d.index), np.sign(d.r15))}
    for name, (sel, side) in rules.items():
        side = pd.Series(side, index=d.index)
        g = d[sel & (side != 0)]
        if name == "taban_tum_momentum":
            g = g.sample(n=min(len(g), 6000), random_state=1)
        R = np.array([trade_R(m1, int(r.j), int(side[i]), r.U) for i, r in g.iterrows()])
        g = g.assign(R=R)
        row = {}
        for p in PERS:
            x = g[g.per == p]
            mo = pd.to_datetime(x.d).dt.to_period("M").astype(str).values
            row[p] = {"n": int(len(x)), "R": float(x.R.mean()), "P": lib.block_boot_p(x.R.values, mo),
                      "isabet": float((x.R > 0).mean()), "maliyet_R": float((x.spr_U).mean())}
        row["gecti"] = bool(all(row[p]["R"] > 0 for p in ("TEST", "BAGIMSIZ")) and all(row[p]["P"] >= 0.9 for p in ("TEST", "BAGIMSIZ")))
        out[name] = row
    out["esikler"] = {"p_trend_ust10": thr_t, "p_up_uc10": thr_u}
    return out


def main() -> None:
    df = pd.read_parquet(OUT / "entries.parquet")
    df["vix"] = df.vix.fillna(df.vix.median())
    res = {"A1": a1(df)}
    res["A2"], models = a2(df)
    m1 = lib.load_m1()
    res["A3"] = a3(df, models, m1)
    (OUT / "analyze.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    for name in ("yon", "yapi"):
        r = res["A1"][name]
        ort = {f: {p: round(r[f][p][0], 3) for p in PERS} for f in FEATS if r[f]["ortak"]}
        top = sorted(FEATS, key=lambda f: -min(abs(r[f][p][1]) for p in PERS) if all(np.sign(r[f][p][0]) == np.sign(r[f]["KESIF"][0]) for p in PERS) else 0)[:6]
        print("A1", name, "ortak:", ort, "| plasebo p95 min t", round(r["_plasebo_min_t_p95"], 2))
        print("   en güçlü tutarlı:", {f: {p: (round(r[f][p][0], 3), round(r[f][p][1], 1)) for p in PERS} for f in top})
    print("A2", json.dumps(res["A2"], ensure_ascii=False))
    print("A3", json.dumps(res["A3"], ensure_ascii=False))


if __name__ == "__main__":
    main()
