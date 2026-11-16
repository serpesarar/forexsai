"""d_ek1.py — PROTOCOL EK-1 (a–d). Çıktı results/d_ek1.json"""
from __future__ import annotations

import json
from datetime import timedelta

import numpy as np
import pandas as pd

import c_new as C
import lib
import rules
from lib import utc

MONTHS = pd.period_range("2018-01", "2026-11", freq="M")


def mo_mean(df: pd.DataFrame, col: str, era: str) -> float:
    g = df[df.era == era]
    mm = pd.to_datetime(g.d).dt.to_period("M")
    sel = MONTHS[(MONTHS.to_timestamp().date <= lib.ESKI_END) == (era == "ESKI")]
    return float(g.groupby(mm)[col].sum().reindex(sel, fill_value=0).mean())


def ek1a(m1, D, vixp) -> dict:
    out = {}
    for tp in (2.0, 3.0, 4.0, 5.0, None):
        df = lib.to_frame(rules.orb(m1, D, vixp, tp_r=tp))
        key = "yok" if tp is None else f"{tp:g}R"
        out[key] = {e: {"n": int((df.era == e).sum()), "R": float(df[df.era == e].R.mean()),
                        "bp": float(df[df.era == e].net_bp.mean()), "R_ay": mo_mean(df, "R", e)} for e in ("ESKI", "YENI")}
        out[key]["tp_orani"] = float((df.why == "tp").mean())
    # 2. KURAL kartı, TP 3R
    df = lib.to_frame(rules.orb(m1, D, vixp, tp_r=3.0)).sort_values("t_in")
    opt = lib.to_frame(rules.orb(m1, D, vixp, tp_r=3.0, optimistic=True))
    s = lib.summarize(df, "R")
    h = len(df) // 2
    card = {"1_hacim": {"n": s["n"], "gecti": s["n"] >= 150},
            "2_beklenti": {"ortR": s["mean"], "P": s["P"], "gecti": s["mean"] > 0 and s["P"] >= 0.90},
            "3_kararlilik": {"yari1": float(df.R.iloc[:h].mean()), "yari2": float(df.R.iloc[h:].mean()),
                             "gecti": bool(df.R.iloc[:h].mean() >= 0 and df.R.iloc[h:].mean() >= 0)},
            "4_surtunme": {"ortR_s15": s["mean_s15"], "gecti": s["mean_s15"] > 0},
            "5_icra": {"iyimser_ortR": float(opt.R.mean()), "gercek_ortR": s["mean"],
                       "fark": float(opt.R.mean() - s["mean"]), "gecti": bool(opt.R.mean() - s["mean"] <= s["mean"] / 2)},
            "6_tek_pozisyon": {"gecti": True, "not": "kural günde ≤1 işlem, gün içi; aynı anda tek pozisyon zaten"}}
    card["gecen"] = int(sum(v["gecti"] for v in card.values() if isinstance(v, dict) and "gecti" in v))
    card["yil"] = {int(y): float(g.R.mean()) for y, g in df.groupby("year")}
    card["ex_top5"] = s["ex_top5"]
    out["kart_TP3R"] = card
    # 2R kartını da aynı motorla (kıyas)
    df2 = lib.to_frame(rules.orb(m1, D, vixp, tp_r=2.0))
    opt2 = lib.to_frame(rules.orb(m1, D, vixp, tp_r=2.0, optimistic=True))
    out["kart_TP2R_icra_farki"] = float(opt2.R.mean() - df2.R.mean())
    return out


def ek1b(A: pd.DataFrame, D: pd.DataFrame) -> dict:
    full = D[D.full].copy()
    full["rng"] = full.high930 - full.low930
    prev20 = full.set_index("d").rng.shift(1).rolling(20).mean()
    o = A[A.rule == "ORBVIX"].copy()
    o["g"] = o.or_w / o.d.map(prev20)
    o = o[o.g.notna()]
    o["T"] = pd.qcut(o.g, 3, labels=["dar", "orta", "genis"])
    out = {}
    for e in ("ESKI", "YENI"):
        g = o[o.era == e]
        out[e] = {t: {"n": int((g["T"] == t).sum()), "bp": float(g[g["T"] == t].net_bp.mean())} for t in ("dar", "orta", "genis")}
        out[e]["P_dar_gt_genis_bp"] = C.boot_diff(g[g["T"] == "dar"].net_bp, g[g["T"] == "genis"].net_bp)
    out["bp_iki_donemde_dar_ustun"] = bool(all(out[e]["dar"]["bp"] > out[e]["genis"]["bp"] for e in ("ESKI", "YENI")))
    return out


def dosed_book(m1, book: pd.DataFrame, factor: pd.Series) -> pd.Series:
    """factor: kitap indeksine göre lot çarpanı (yalnız ilgili kural satırları ≠ 1); kural içinde ortalama 1'e normalize edilir."""
    f = factor.copy()
    for r in book.rule.unique():
        sel = book.rule == r
        if (f[sel] != 1).any():
            f[sel] = f[sel] / f[sel].mean()
    return C.sharpe_m(C.book_daily(m1, book, f))


def ek1c(m1, D, vixp, book: pd.DataFrame) -> dict:
    cl = D[D.full].set_index("d").close
    prev_down = (cl.shift(1) < cl.shift(2))
    base = C.sharpe_m(C.book_daily(m1, book))
    one = pd.Series(1.0, index=book.index)
    doses = {
        "ORB_dun_dusus": one.where(book.rule != "ORBVIX", np.where(book.d.map(prev_down).fillna(False), 1.5, 0.5)),
        "KSG_VIX25": one.where(book.rule != "KSG", np.where(book.d.map(lambda d: vixp.get(d, 0) >= 25), 2.0, 1.0)),
        "C3B_vade_haftasi": one.where(book.rule != "C3B", np.where(book.d.map(C.opex_week), 0.5, 1.0)),
    }
    doses["UCU_BIRDEN"] = doses["ORB_dun_dusus"] * doses["KSG_VIX25"] * doses["C3B_vade_haftasi"]
    out = {}
    eski = base.index.to_timestamp().date <= lib.ESKI_END
    for k, f in doses.items():
        mo = dosed_book(m1, book, f.astype(float))
        row = {}
        for e, sel in (("ESKI", eski), ("YENI", ~eski), ("TUM", np.ones(len(base), bool))):
            row[e] = {"sabit": C.sh(base[sel]), "dozlu": C.sh(mo[sel]), "P": C.boot_sharpe_diff(mo[sel], base[sel])}
        row["gecti"] = bool(row["ESKI"]["dozlu"] > row["ESKI"]["sabit"] and row["YENI"]["dozlu"] > row["YENI"]["sabit"]
                            and row["TUM"]["P"] >= 0.90)
        out[k] = row
    return out


def ek1d(m1, D) -> dict:
    fd = lib.fomc_days()
    days = D.d.tolist()
    full = dict(zip(D.d, D.full))
    var = {"16:00→09:30 (canlı)": (960, 0, 570), "16:00→13:55": (960, 0, 835), "D−1 14:00→13:55": (840, 0, 835),
           "09:30→13:55 (gün içi)": (570, 1, 835)}
    out = {}
    for name, (m_in, same_day, m_out) in var.items():
        tr = []
        for j in range(1, len(days)):
            if days[j] in fd and full.get(days[j - 1], False):
                d_in = days[j] if same_day else days[j - 1]
                x = lib.time_trade(m1, "FOMC", d_in, utc(d_in, m_in), utc(days[j], m_out), +1)
                if x:
                    tr.append(x)
        df = lib.to_frame(tr)
        out[name] = {e: lib.summarize(df[df.era == e], "net_bp") for e in ("ESKI", "YENI")}
        out[name] = {e: {k: out[name][e][k] for k in ("n", "mean", "median", "hit", "P")} for e in ("ESKI", "YENI")}
    return out


def main() -> None:
    m1 = lib.load_m1()
    D = lib.daily_table(m1)
    vixp = lib.vix_prev_map(D.d.tolist())
    A = pd.read_parquet(lib.RESULTS / "a_trades.parquet")
    book = A[A.rule.isin(C.LOTS)].reset_index(drop=True)
    out = {"EK1-a": ek1a(m1, D, vixp), "EK1-b": ek1b(A, D), "EK1-c": ek1c(m1, D, vixp, book), "EK1-d": ek1d(m1, D)}
    (lib.RESULTS / "d_ek1.json").write_text(json.dumps(out, indent=1, default=str, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(out, indent=1, default=str, ensure_ascii=False))


if __name__ == "__main__":
    main()
