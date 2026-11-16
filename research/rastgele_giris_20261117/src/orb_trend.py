"""orb_trend.py — PROTOCOL EK-1: ORB × VIX girişlerinde rastgele-girişle eğitilmiş TREND olasılığı. Çıktı results/orb_trend.json"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ndx_10y_1m_20261116/src"))
import c_new as C  # noqa: E402
import lib  # noqa: E402
from analyze import FEATS  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "results"


def feats_at(m1, j, d, m0, U, a60, a1440, vix, pc):
    o, h, l, c, t = m1.o, m1.h, m1.l, m1.c, m1.t
    rg = h - l
    clv = np.where(rg > 0, (c - l) / np.where(rg > 0, rg, 1), 0.5)
    up = c > o
    sl = lambda n: slice(j - n, j)
    ss = int(np.searchsorted(t, lib.utc(d, m0)))
    run, col = 0, up[j - 1]
    while run < 30 and up[j - 1 - run] == col:
        run += 1
    s_hi, s_lo = (h[ss:j].max(), l[ss:j].min()) if j > ss else (np.nan, np.nan)
    wsh = lambda arr, n: arr[sl(n)].sum() / max(1e-9, rg[sl(n)].sum())
    return {"clv1": clv[j - 1], "clv5": clv[sl(5)].mean(), "clv15": clv[sl(15)].mean(), "clv60": clv[sl(60)].mean(),
            "uw5": wsh(h - np.maximum(o, c), 5), "lw5": wsh(np.minimum(o, c) - l, 5), "uw15": wsh(h - np.maximum(o, c), 15),
            "lw15": wsh(np.minimum(o, c) - l, 15), "run_signed": run * (1 if col else -1), "body5": wsh(np.abs(c - o), 5),
            "flip15": float(np.mean(up[j - 15:j] != up[j - 16:j - 1])), "r5": (c[j - 1] - c[j - 6]) / U, "r15": (c[j - 1] - c[j - 16]) / U,
            "r60b": (c[j - 1] - c[j - 61]) / U, "r240": (c[j - 1] - c[j - 241]) / U,
            "rng60": (h[sl(60)].max() - l[sl(60)].min()) / U, "volreg": a60[j] / a1440[j],
            "sess_pos": (c[j - 1] - s_lo) / (s_hi - s_lo) if j > ss and s_hi > s_lo else 0.5,
            "dist_pc": (c[j - 1] - pc) / U if pc and np.isfinite(pc) else 0.0, "min_sess": int((t[j] - t[ss]) // 60),
            "seans_kod": 2, "dow": d.weekday(), "vix": vix}


def main() -> None:
    df = pd.read_parquet(OUT / "entries.parquet")
    df["vix"] = df.vix.fillna(df.vix.median())
    tr = df[df.per == "KESIF"]
    m = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, max_leaf_nodes=15, min_samples_leaf=200,
                                       random_state=0).fit(tr[FEATS], (tr.yapi == "TREND").astype(int))
    nyk = tr[tr.seans == "NY"]
    q = list(pd.Series(m.predict_proba(nyk[FEATS])[:, 1]).quantile([1 / 3, 2 / 3]))
    m1 = lib.load_m1(); D = lib.daily_table(m1)
    rg = m1.h - m1.l
    a60 = pd.Series(rg).rolling(60).mean().shift(1).values
    a1440 = pd.Series(rg).rolling(1440, min_periods=600).mean().shift(1).values
    pc = dict(zip(D.d, D.close.shift(1)))
    orb = pd.read_parquet(lib.RESULTS / "orb_tp3_trades.parquet").reset_index(drop=True)
    F = []
    for r in orb.itertuples():
        j = int(np.searchsorted(m1.t, r.t_in))
        F.append(feats_at(m1, j, r.d, 570, 4 * a60[j], a60, a1440, r.vix, pc.get(r.d)))
    orb["p_trend"] = m.predict_proba(pd.DataFrame(F)[FEATS])[:, 1]
    orb["T"] = np.where(orb.p_trend <= q[0], "dusuk", np.where(orb.p_trend > q[1], "yuksek", "orta"))
    res = {"esik": q}
    for e in ("ESKI", "YENI"):
        g = orb[orb.era == e]
        res[e] = {t: {"n": int((g["T"] == t).sum()), "R": float(g[g["T"] == t].R.mean())} for t in ("dusuk", "orta", "yuksek")}
    res["P_yuksek_gt_dusuk"] = C.boot_diff(orb[orb["T"] == "yuksek"].R, orb[orb["T"] == "dusuk"].R)
    # kitap dozu
    A = pd.read_parquet(lib.RESULTS / "a_trades.parquet")
    book = pd.concat([A[A.rule.isin(C.LOTS) & (A.rule != "ORBVIX")], orb[A.columns.intersection(orb.columns)]], ignore_index=True)
    base = C.sharpe_m(C.book_daily(m1, book))
    is_orb = book.rule == "ORBVIX"
    pt = book.t_in.where(is_orb).map(orb.set_index("t_in")["T"])
    f = pd.Series(1.0, index=book.index)
    f[is_orb] = np.where(pt[is_orb] == "yuksek", 1.5, np.where(pt[is_orb] == "dusuk", 0.5, 1.0))
    f[is_orb] = f[is_orb] / f[is_orb].mean()
    mo = C.sharpe_m(C.book_daily(m1, book, f))
    eski = base.index.to_timestamp().date <= lib.ESKI_END
    res["kitap"] = {k: {"sabit": C.sh(base[s]), "dozlu": C.sh(mo[s]), "P": C.boot_sharpe_diff(mo[s], base[s])}
                    for k, s in (("ESKI", eski), ("YENI", ~eski), ("TUM", np.ones(len(base), bool)))}
    res["gecti"] = bool(all(res[e]["yuksek"]["R"] > res[e]["dusuk"]["R"] for e in ("ESKI", "YENI")) and res["P_yuksek_gt_dusuk"] >= 0.9
                        and res["kitap"]["ESKI"]["dozlu"] > res["kitap"]["ESKI"]["sabit"] and res["kitap"]["YENI"]["dozlu"] > res["kitap"]["YENI"]["sabit"])
    (OUT / "orb_trend.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(res, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
