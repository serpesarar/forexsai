"""ek3.py — PROTOCOL EK-3: Pazartesi uzun kartı + gün plasebosu + kitap katkısı; 16:00 VIX ailesinde yeniden açılış kontrolü. Çıktı results/ek3.json"""
from __future__ import annotations

import json
import sys
import warnings
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import grid as G  # noqa: E402
import lib  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ndx_10y_1m_20261116/src"))
import c_new as C  # noqa: E402
import rules  # noqa: E402

OUT = G.OUT


def day_rule(m1, D, wd: int, mn: int, lag: int = 0, name: str = "P1"):
    days = D.d.tolist()
    tr = []
    for i, d in enumerate(days[:-1]):
        if d.weekday() != wd:
            continue
        nd = days[i + 1]
        x = lib.time_trade(m1, name, d, lib.utc(d, mn) + 60 * lag, lib.utc(nd, mn), +1)
        if x:
            tr.append(x)
    return lib.to_frame(tr)


def main() -> None:
    m1 = lib.load_m1(); D = lib.daily_table(m1); vixp = lib.vix_prev_map(D.d.tolist())
    res = {}
    # (1) Pazartesi kuralı ve gün plasebosu
    P = day_rule(m1, D, 0, 180)
    s = lib.summarize(P.sort_values("t_in"), "net_bp")
    late = day_rule(m1, D, 0, 180, lag=1)
    days_cmp = {nm: float(day_rule(m1, D, wd, 180).net_bp.mean()) for wd, nm in enumerate(("Pzt", "Sal", "Car", "Per", "Cum"))}
    yil = {int(y): (int(len(g)), round(float(g.net_bp.mean()), 1)) for y, g in P.groupby("year")}
    h = len(P) // 2
    Ps = P.sort_values("t_in")
    card = {"1_hacim": [s["n"], s["n"] >= 150], "2_beklenti": [round(s["mean"], 2), round(s["P"], 3), s["mean"] > 0 and s["P"] >= 0.9],
            "3_kararlilik": [round(Ps.net_bp.iloc[:h].mean(), 1), round(Ps.net_bp.iloc[h:].mean(), 1),
                             bool(Ps.net_bp.iloc[:h].mean() >= 0 and Ps.net_bp.iloc[h:].mean() >= 0)],
            "4_surtunme": [round(s["mean_s15"], 2), s["mean_s15"] > 0],
            "5_icra_1dk_gec": [round(float(late.net_bp.mean()), 2), bool(s["mean"] - late.net_bp.mean() <= s["mean"] / 2)],
            "6_tek_pozisyon": [True, True]}
    card["gecen"] = int(sum(bool(v[-1]) for v in card.values()))
    res["P1_pazartesi_0300"] = {"ozet": {k: s[k] for k in ("n", "mean", "median", "hit", "P", "mean_s15", "ex_top5", "worst")},
                                "kart": card, "yil": yil, "gun_plasebosu": days_cmp,
                                "yan_0830": float(day_rule(m1, D, 0, 510).net_bp.mean()), "yan_0930": float(day_rule(m1, D, 0, 570).net_bp.mean()),
                                "ESKI": lib.summarize(P[P.era == "ESKI"], "net_bp")["mean"], "YENI": lib.summarize(P[P.era == "YENI"], "net_bp")["mean"]}
    # gün plasebosu P: Pazartesi ortalaması diğer dört günün dağılımında
    others = [day_rule(m1, D, wd, 180).net_bp.values for wd in (1, 2, 3, 4)]
    pool = np.concatenate(others)
    rng = np.random.default_rng(5)
    boot = np.array([rng.choice(pool, size=len(P)).mean() for _ in range(4000)])
    res["P1_pazartesi_0300"]["P_diger_gunlerden_iyi"] = float((boot < P.net_bp.mean()).mean())
    # örtüşme: bilinen kuralların açık olduğu günler
    A = pd.read_parquet(lib.RESULTS / "a_trades.parquet")
    known = set()
    for r in A.itertuples():
        d0 = pd.Timestamp(r.t_in, unit="s").tz_localize("UTC").tz_convert(lib.NY).date()
        d1 = pd.Timestamp(r.t_out, unit="s").tz_localize("UTC").tz_convert(lib.NY).date()
        dd = d0
        while dd <= d1:
            known.add(dd); dd += timedelta(days=1)
    res["P1_pazartesi_0300"]["bilinen_kural_gun_ortusmesi"] = float(np.mean([d in known for d in P.d]))
    # kitap katkısı
    orb3 = lib.to_frame(rules.orb(m1, D, vixp, tp_r=3.0))
    book = pd.concat([A[A.rule.isin(C.LOTS) & (A.rule != "ORBVIX")], orb3], ignore_index=True)
    base = C.sharpe_m(C.book_daily(m1, book))
    C.LOTS["P1"] = 0.5
    mo = C.sharpe_m(C.book_daily(m1, pd.concat([book, P], ignore_index=True)))
    eski = base.index.to_timestamp().date <= lib.ESKI_END
    res["P1_pazartesi_0300"]["kitap"] = {k: {"kitap": C.sh(base[s_]), "kitap+P1": C.sh(mo[s_]), "P": C.boot_sharpe_diff(mo[s_], base[s_])}
                                         for k, s_ in (("ESKI", eski), ("YENI", ~eski), ("TUM", np.ones(len(base), bool)))}
    # (2) 16:00 VIX18–25 ∧ EMA20 üstü: çıkış 18:00 / 18:05 / 18:15 / 18:30
    Cd = G.conditions(D, vixp)
    days = D.d.tolist()
    out2 = {}
    for ex in (1080, 1085, 1095, 1110):
        vals = []
        for i, d in enumerate(days[:-1]):
            if not D.full.iloc[i] or not (Cd.loc[d, "VIX18-25"] and Cd.loc[d, "ust_EMA20"]):
                continue
            x = lib.time_trade(m1, "V16", d, lib.utc(d, 960), lib.utc(d, ex), +1, tol_s=120)
            if x:
                vals.append((d, x.net_bp()))
        v = pd.DataFrame(vals, columns=["d", "bp"])
        out2[f"cikis_{ex // 60}:{ex % 60:02d}"] = {"n": len(v), "bp": float(v.bp.mean()),
                                                     "KOR_2024+": float(v[v.d >= date(2024, 1, 1)].bp.mean())}
    res["V16_yeniden_acilis"] = out2
    (OUT / "ek3.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    print(json.dumps(res, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
