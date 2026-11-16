"""f_s4.py — EK-2 S4 geçti: ORB ile çakışma, kitaba katkı (aylık Sharpe, E110) ve 2. KURAL kartı. Çıktı results/f_s4.json"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

import c_new as C
import e_ek2 as E
import lib
import rules


def main() -> None:
    m1 = lib.load_m1(); D = lib.daily_table(m1); vixp = lib.vix_prev_map(D.d.tolist())
    s4 = lib.to_frame(E.s4_pm(m1, D, vixp, "hi")).sort_values("t_in").reset_index(drop=True)
    orb3 = lib.to_frame(rules.orb(m1, D, vixp, tp_r=3.0))
    t12 = s4.t_in.values
    open_at = {r.d: (r.t_in <= t <= r.t_out) for r in orb3.itertuples() for t in [lib.utc(r.d, 720)]}
    s4["orb_acik"] = s4.d.map(open_at).fillna(False).astype(bool)
    out = {"ORB 12:00'de açık": {e: lib.summarize(s4[(s4.era == e) & s4.orb_acik], "net_bp") for e in ("ESKI", "YENI")},
           "ORB 12:00'de açık değil": {e: lib.summarize(s4[(s4.era == e) & ~s4.orb_acik], "net_bp") for e in ("ESKI", "YENI")}}
    out = {k: {e: {kk: v[e][kk] for kk in ("n", "mean", "P")} for e in v} for k, v in out.items()}
    # kitaba katkı: canlı kitap (ORB 3R ile) + S4 0,5 lot
    A = pd.read_parquet(lib.RESULTS / "a_trades.parquet")
    book = A[A.rule.isin(C.LOTS) & (A.rule != "ORBVIX")]
    book = pd.concat([book, orb3], ignore_index=True)
    base = C.sharpe_m(C.book_daily(m1, book))
    C.LOTS["S4_hi"] = 0.5
    s4_only = s4[~s4.orb_acik]
    res = {}
    for name, extra in (("S4 tümü", s4), ("S4 yalnız ORB açık değilken", s4_only)):
        bk = pd.concat([book, extra.drop(columns=["orb_acik"])], ignore_index=True)
        mo = C.sharpe_m(C.book_daily(m1, bk))
        eski = base.index.to_timestamp().date <= lib.ESKI_END
        res[name] = {e: {"kitap": C.sh(base[s]), "kitap+S4": C.sh(mo[s]), "P": C.boot_sharpe_diff(mo[s], base[s])}
                     for e, s in (("ESKI", eski), ("YENI", ~eski), ("TUM", np.ones(len(base), bool)))}
    out["kitaba_katki"] = res
    # kart (S4 tümü)
    s = lib.summarize(s4, "net_bp"); h = len(s4) // 2
    late = lib.to_frame([x for x in (lib.time_trade(m1, "S4L", r.d, lib.utc(r.d, 721), lib.utc(r.d, 955), +1)
                                    for r in s4.itertuples()) if x])
    out["kart"] = {"1_hacim": [s["n"], s["n"] >= 150], "2_beklenti": [round(s["mean"], 2), round(s["P"], 3), s["mean"] > 0 and s["P"] >= 0.9],
                   "3_kararlilik": [round(s4.net_bp.iloc[:h].mean(), 2), round(s4.net_bp.iloc[h:].mean(), 2),
                                    bool(s4.net_bp.iloc[:h].mean() >= 0 and s4.net_bp.iloc[h:].mean() >= 0)],
                   "4_surtunme": [round(s["mean_s15"], 2), s["mean_s15"] > 0],
                   "5_icra_1dk_gec": [round(float(late.net_bp.mean()), 2), bool(s["mean"] - late.net_bp.mean() <= s["mean"] / 2)],
                   "6_tek_pozisyon": [True, True], "en_iyi_5_haric": round(s["ex_top5"], 2), "isabet": round(s["hit"], 3)}
    out["kart"]["gecen"] = int(sum(bool(v[-1]) for k, v in out["kart"].items() if k[0].isdigit()))
    (lib.RESULTS / "f_s4.json").write_text(json.dumps(out, indent=1, default=str, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(out, indent=1, default=str, ensure_ascii=False))


if __name__ == "__main__":
    main()
