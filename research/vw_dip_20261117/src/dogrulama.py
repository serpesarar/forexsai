"""dogrulama.py — PROTOCOL §6: dondurulmuş adaylar TEST (Dukascopy 2021-11 → 2026-11), MT5 bağımsız, plasebo, tek pozisyon,
icra farkı, kart. Adaylar results/donmus_adaylar.json'dan okunur; burada hiçbir parametre seçilmez.
"""
from __future__ import annotations

import json
from datetime import datetime

import numpy as np
import pandas as pd

import kesif as KS
import vw  # noqa: I001  (sys.path: lib, veri)
import lib
import veri

CARD_DIR = vw.ROOT / "backend/data/evolution/go_live_cards"


def cell_rows(ev: pd.DataFrame, e: pd.DataFrame, c: dict) -> pd.DataFrame:
    x = ev.merge(e[["typ", "drop", "vix", "d"]], left_on="e", right_index=True)
    x = x[(x.typ == c["typ"]) & (x["drop"] >= KS.DROPS[c["drop"]]) & (x.tp == c["tp"]) & (x.time == c["time"])]
    if KS.VIXS[c["vix"]] > 0:
        x = x[x.vix >= KS.VIXS[c["vix"]]]
    return x.sort_values("t_in").reset_index(drop=True)


def single(x: pd.DataFrame) -> pd.DataFrame:
    keep, busy = [], -1
    for r in x.itertuples():
        if r.t_in >= busy:
            keep.append(r.Index)
            busy = r.t_out
    return x.loc[keep]


def summ(x: pd.DataFrame) -> dict:
    if len(x) == 0:
        return {"n": 0}
    h = len(x) // 2
    return {"n": int(len(x)), "gun": int(x.d.nunique()), "mean": round(float(x.R.mean()), 4), "median": round(float(x.R.median()), 3),
            "hit": round(float((x.R > 0).mean()), 3), "P_kume": round(KS.cluster_p(x.R.values, x.d.astype(str).values), 4),
            "mean15": round(float(x.R15.mean()), 4), "h1": round(float(x.R.iloc[:h].mean()), 4) if h else None,
            "h2": round(float(x.R.iloc[h:].mean()), 4) if h else None, "bp": round(float(x.bp.mean()), 2),
            "ex_top5": round(float((x.R.sum() - np.sort(x.R.values)[-5:].sum()) / max(1, len(x) - 5)), 4) if len(x) > 5 else None,
            "yil": {int(y): round(float(g.R.mean()), 3) for y, g in x.groupby(pd.to_datetime(x.d).dt.year)}}


def mt5_entries() -> tuple[veri.PathBars, pd.DataFrame]:
    veri.KUTU = vw.ROOT / "research/fitil210_15m_20261117/data/kutu_1117"
    p = veri.mt5_path("M15")
    q = veri.build_15m(p)
    b = veri.build_210m(q)
    anc = pd.concat([vw.a210_anchors(q, b, set()), vw.ag_anchors(q)], ignore_index=True)
    e = vw.entries(q, anc)
    e["d"] = [pd.Timestamp(int(t), unit="s", tz="UTC").tz_convert(vw.NY).date() for t in e.t_sig]
    e["vix"] = e.d.map(lib.vix_prev_map(sorted(set(e.d))))
    return p, e


def main(tag: str = "", k_total: int = 5) -> None:
    """tag: "" (tur 1) | "_tur2" …; k_total: birikimli TEST aday sayısı (EK-1 Bonferroni: P ≥ 1 − 0,10/K)."""
    p_test = 1 - 0.10 / k_total
    frozen = json.loads((KS.RES / f"donmus_adaylar{tag}.json").read_text())
    if not frozen:
        print("dondurulmuş aday yok — doğrulanacak bir şey yok")
        (KS.RES / f"dogrulama{tag}.json").write_text(json.dumps({"adaylar": []}, indent=1))
        return
    f_eval = {"_tur2": vw.evaluate_hold_all, "_tur3": vw.evaluate_r3_all}.get(tag, vw.evaluate_all)
    e = pd.read_parquet(KS.CACHE / ("girisler_tur3.parquet" if tag == "_tur3" else "girisler.parquet"))
    if tag == "_tur3":
        e = e[e.typ.isin({c["typ"] for c in frozen})].reset_index(drop=True)
    p = vw.duka_path_stable()
    et = e[e.era == "TEST"].reset_index(drop=True)
    ev = f_eval(p, et)
    evo = f_eval(p, et, optimistic=True)
    pls = [f_eval(p, et, shift=KS.placebo_shifts(et, 50 + r)) for r in range(10)]
    pm, em = mt5_entries()
    if tag == "_tur3":
        em = em[em.typ.isin({c["typ"] for c in frozen})].reset_index(drop=True)
    evm = f_eval(pm, em)
    out = []
    for c in frozen:
        x = cell_rows(ev, et, c)
        xo = cell_rows(evo, et, c)
        xs = single(x)
        xp = pd.concat([cell_rows(z, et, c) for z in pls], ignore_index=True)
        xm = cell_rows(evm, em, c)
        s, sm = summ(x), summ(xm)
        dp = float(np.mean([x.R.mean() - xp.sample(len(x), replace=True, random_state=k).R.mean() > 0 for k in range(2000)])) if len(x) and len(xp) else np.nan
        icra = (float(xo.R.mean()) - s.get("mean", np.nan)) if len(xo) else np.nan
        checks = {
            "1_test": bool(s.get("mean", -1) > 0 and s.get("P_kume", 0) >= p_test),
            "2_mt5": bool(sm.get("mean", -1) > 0),
            "3_surtunme": bool(s.get("mean15", -1) > 0),
            "4_tek_pozisyon": bool(len(xs) and xs.R.mean() > 0),
            "5_plasebo": bool(dp >= 0.90),
            "6_icra": bool(np.isfinite(icra) and icra < 0.5 * abs(s.get("mean", 0))),
            "7_hacim": bool(c["n"] + s.get("n", 0) >= 150),
        }
        out.append({"aday": c, "TEST": s, "TEST_tek_poz": summ(xs), "TEST_iyimser": round(float(xo.R.mean()), 4) if len(xo) else None,
                    "plasebo_mean": round(float(xp.R.mean()), 4) if len(xp) else None, "P_plasebo_fark": round(dp, 4),
                    "MT5": sm, "olcutler": checks, "gecti": all(checks.values())})
        print(f"{c['typ']} {c['drop']} {c['vix']} TP{c['tp']} {c['time']}: KEŞİF {c['mean']:+.3f} (n {c['n']}) → "
              f"TEST {s.get('mean', float('nan')):+.3f} (n {s.get('n')}, P {s.get('P_kume')}) MT5 {sm.get('mean', float('nan')):+.3f} "
              f"(n {sm.get('n')}) plasebo {out[-1]['plasebo_mean']} P_fark {dp:.2f} → {sum(checks.values())}/7 {'GEÇTİ' if out[-1]['gecti'] else ''}",
              flush=True)
    (KS.RES / f"dogrulama{tag}.json").write_text(json.dumps({"tarih": datetime.now().isoformat(timespec="seconds"), "P_test_esik": p_test, "adaylar": out},
                                                      indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    import sys
    main(sys.argv[1] if len(sys.argv) > 1 else "", int(sys.argv[2]) if len(sys.argv) > 2 else 5)
