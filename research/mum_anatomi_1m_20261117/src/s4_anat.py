"""s4_anat.py — PROTOCOL EK-5: S4 × sabah 1m anatomisi + kitap katkısı. Çıktı results/s4_anat.json"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ndx_10y_1m_20261116/src"))
import c_new as C  # noqa: E402
import e_ek2 as E  # noqa: E402
import lib  # noqa: E402
import rules  # noqa: E402
from q_daily import PER, per  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "results"


def anat(m1, d):
    a, b = int(np.searchsorted(m1.t, lib.utc(d, 570))), int(np.searchsorted(m1.t, lib.utc(d, 720)))
    o, h, l, c = m1.o[a:b], m1.h[a:b], m1.l[a:b], m1.c[a:b]
    rg = h - l
    clv = np.where(rg > 0, (c - l) / np.where(rg > 0, rg, 1), np.nan)
    return float(np.nanmean(clv)), float(((np.minimum(o, c) - l).sum() - (h - np.maximum(o, c)).sum()) / max(1e-9, rg.sum()))


def main() -> None:
    m1 = lib.load_m1(); D = lib.daily_table(m1); vixp = lib.vix_prev_map(D.d.tolist())
    s4 = lib.to_frame(E.s4_pm(m1, D, vixp, "hi"))
    s4[["A_clv", "A_w"]] = [anat(m1, d) for d in s4.d]
    s4["per"] = s4.d.map(per)
    res = {}
    A = pd.read_parquet(lib.RESULTS / "a_trades.parquet")
    orb3 = lib.to_frame(rules.orb(m1, D, vixp, tp_r=3.0))
    book = pd.concat([A[A.rule.isin(C.LOTS) & (A.rule != "ORBVIX")], orb3], ignore_index=True)
    base = C.sharpe_m(C.book_daily(m1, book))
    eski = base.index.to_timestamp().date <= lib.ESKI_END
    C.LOTS["S4_hi"] = 0.5
    pvals = {}
    for f in ("A_clv", "A_w"):
        e = list(s4[s4.per == "KESIF"][f].quantile([1 / 3, 2 / 3]))
        cell = {"esik": e}
        for p in PER:
            g = s4[s4.per == p]
            top, bot = g[g[f] > e[1]], g[g[f] <= e[0]]
            mo = pd.to_datetime(top.d).dt.to_period("M").astype(str).values
            cell[p] = {"n_ust": len(top), "ust": float(top.net_bp.mean()), "alt": float(bot.net_bp.mean()), "tum": float(g.net_bp.mean()),
                       "P_ust": lib.block_boot_p(top.net_bp.values, mo), "P_ust_gt_alt": C.boot_diff(top.net_bp, bot.net_bp)}
        sub = s4[s4[f] > e[1]].drop(columns=["A_clv", "A_w", "per"])
        mo = C.sharpe_m(C.book_daily(m1, pd.concat([book, sub], ignore_index=True)))
        cell["kitap"] = {k: {"kitap": C.sh(base[s]), "kitap+S4+": C.sh(mo[s]), "P": C.boot_sharpe_diff(mo[s], base[s])}
                         for k, s in (("ESKI", eski), ("YENI", ~eski), ("TUM", np.ones(len(base), bool)))}
        cell["gecti_tek"] = bool(all(cell[p]["ust"] > 0 and cell[p]["ust"] > cell[p]["alt"] for p in PER)
                                 and cell["TEST"]["P_ust"] >= 0.9 and cell["BAGIMSIZ"]["P_ust"] >= 0.9)
        cell["gecti_kitap"] = bool(cell["kitap"]["ESKI"]["kitap+S4+"] > cell["kitap"]["ESKI"]["kitap"]
                                   and cell["kitap"]["YENI"]["kitap+S4+"] > cell["kitap"]["YENI"]["kitap"])
        pvals[f] = 1 - min(cell["TEST"]["P_ust_gt_alt"], cell["BAGIMSIZ"]["P_ust_gt_alt"])
        res[f] = cell
    srt = sorted(pvals.items(), key=lambda x: x[1])
    res["holm"] = {k: min(1.0, v * (len(srt) - i)) for i, (k, v) in enumerate(srt)}
    (OUT / "s4_anat.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    for f in ("A_clv", "A_w"):
        c = res[f]
        print(f, {p: (c[p]["n_ust"], round(c[p]["ust"], 1), round(c[p]["alt"], 1), round(c[p]["tum"], 1), round(c[p]["P_ust"], 2)) for p in PER})
        print("   kitap", {k: (round(v["kitap"], 2), round(v["kitap+S4+"], 2), round(v["P"], 2)) for k, v in c["kitap"].items()},
              "tek", c["gecti_tek"], "kitap", c["gecti_kitap"])
    print("holm", res["holm"])


if __name__ == "__main__":
    main()
