"""p1_ek1.py — PROTOCOL EK-1: ORB anatomi dozu kitap düzeyinde + yoklama mekanizması. Çıktı results/p1_ek1.json"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ndx_10y_1m_20261116/src"))
import c_new as C  # noqa: E402
import lib  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "results"
UW_HI, UW_LO = 0.2525146457389285, 0.18149161820047924


def probes(m1, d, t_in, or_hi) -> int:
    a, b = int(np.searchsorted(m1.t, lib.utc(d, 585))), int(np.searchsorted(m1.t, t_in))
    return int((m1.h[a:b] >= or_hi).sum())


def main() -> None:
    m1 = lib.load_m1()
    o = pd.read_parquet(OUT / "p1_orb_feats.parquet")
    o["probe"] = [probes(m1, r.d, r.t_in, r.or_hi) for r in o.itertuples()]
    res = {"EK1-b": {"spearman_uw5_probe": float(o[["f_uw5", "probe"]].corr("spearman").iloc[0, 1])}}
    for e in ("YENI", "ESKI"):
        g = o[o.era == e]
        q = g.probe.clip(upper=6)
        res["EK1-b"][e] = {"yoklama_0_1": {"n": int((q <= 1).sum()), "R": float(g[q <= 1].R.mean())},
                           "yoklama_2_5": {"n": int(((q >= 2) & (q <= 5)).sum()), "R": float(g[(q >= 2) & (q <= 5)].R.mean())},
                           "yoklama_6+": {"n": int((q >= 6).sum()), "R": float(g[q >= 6].R.mean())}}
    worst = (o.f_run <= 1) & (o.f_uw5 <= UW_LO)
    res["EK1-c"] = {e: {"n": int((worst & (o.era == e)).sum()), "R": float(o[worst & (o.era == e)].R.mean()),
                        "geri_kalan_R": float(o[~worst & (o.era == e)].R.mean())} for e in ("YENI", "ESKI")}
    # kitap dozu
    A = pd.read_parquet(lib.RESULTS / "a_trades.parquet")
    book = pd.concat([A[A.rule.isin(C.LOTS) & (A.rule != "ORBVIX")], o[A.columns.intersection(o.columns)]], ignore_index=True)
    base = C.sharpe_m(C.book_daily(m1, book))
    is_orb = book.rule == "ORBVIX"
    key = book.t_in.where(is_orb)
    feat = o.set_index("t_in")
    run = key.map(feat.f_run); uw = key.map(feat.f_uw5)
    doses = {"run>=3": run >= 3, "uw5_ust": uw > UW_HI, "biri": (run >= 3) | (uw > UW_HI)}
    eski = base.index.to_timestamp().date <= lib.ESKI_END
    res["EK1-a"] = {}
    for k, good in doses.items():
        f = pd.Series(1.0, index=book.index)
        f[is_orb] = np.where(good[is_orb], 1.5, 0.5)
        f[is_orb] = f[is_orb] / f[is_orb].mean()
        mo = C.sharpe_m(C.book_daily(m1, book, f))
        row = {e: {"sabit": C.sh(base[s]), "dozlu": C.sh(mo[s]), "P": C.boot_sharpe_diff(mo[s], base[s])}
               for e, s in (("ESKI", eski), ("YENI", ~eski), ("TUM", np.ones(len(base), bool)))}
        row["iyi_pay"] = float(good[is_orb].mean())
        row["gecti"] = bool(row["ESKI"]["dozlu"] > row["ESKI"]["sabit"] and row["YENI"]["dozlu"] > row["YENI"]["sabit"]
                            and row["TUM"]["P"] >= 0.90)
        res["EK1-a"][k] = row
    (OUT / "p1_ek1.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(res, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
