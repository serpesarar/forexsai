"""e_ek2.py — PROTOCOL EK-2: yeni strateji aileleri S1–S4 (dondurulmuş, taramasız). Çıktı results/e_ek2.json"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

import lib
import rules
from lib import Trade, utc


def s1_gap(m1, D, vixp, arm: str) -> list[Trade]:
    ctx = rules.caprev_ctx(D, vixp)
    full = D[D.full].reset_index(drop=True)
    out = []
    for i in range(1, len(full)):
        r, p = full.iloc[i], full.iloc[i - 1]
        c, v = ctx.get(r.d), vixp.get(r.d)
        if c is None or v is None or not np.isfinite(r.open930) or (arm == "hi") != (v >= 18.4):
            continue
        if r.open930 < p.close * (1 - 0.5 * c["dvol"]):
            x = lib.time_trade(m1, f"S1_{arm}", r.d, utc(r.d, 570), utc(r.d, 955), +1, gap_bp=(r.open930 / p.close - 1) * 1e4)
            if x:
                out.append(x)
    return out


def range_break(m1, D, vixp, side: int, or_s: int, or_e: int, last_trig: int, exit_min: int, rule: str) -> list[Trade]:
    out = []
    for row in D[D.full].itertuples():
        d, v = row.d, vixp.get(row.d)
        if v is None or v < 18.4:
            continue
        a, b = int(np.searchsorted(m1.t, utc(d, or_s))), int(np.searchsorted(m1.t, utc(d, or_e)))
        if b - a < (or_e - or_s) * 0.8:
            continue
        hi, lo = m1.h[a:b].max(), m1.l[a:b].min()
        mid = (hi + lo) / 2
        trig = next((x for x in rules.bars_tf(m1, d, or_e, last_trig, 5)
                     if (x["c"] > hi if side > 0 else x["c"] < lo)), None)
        if trig is None:
            continue
        i0 = m1.idx_from(trig["t_end"])
        if i0 is None:
            continue
        px = m1.o[i0] + m1.spr[i0] if side > 0 else m1.o[i0]
        risk = (px - mid) if side > 0 else (mid - px)
        if risk <= 0.0005 * px:
            continue
        tp = px + side * 3 * risk
        k, pout, why, mae = lib.walk(m1, i0, utc(d, exit_min), side, mid if side > 0 else mid, tp)
        out.append(Trade(rule, d, int(m1.t[i0]), int(m1.t[k]), side, px, pout, risk=risk, spr_in=m1.spr[i0],
                         spr_out=m1.spr[k], mae=mae, why=why))
    return out


def s4_pm(m1, D, vixp, arm: str) -> list[Trade]:
    out = []
    for row in D[D.full].itertuples():
        v = vixp.get(row.d)
        if v is None or (arm == "hi") != (v >= 18.4):
            continue
        k = m1.idx_from(utc(row.d, 720))
        if k is None or not np.isfinite(row.open930) or m1.o[k] <= row.open930:
            continue
        x = lib.time_trade(m1, f"S4_{arm}", row.d, utc(row.d, 720), utc(row.d, 955), +1)
        if x:
            out.append(x)
    return out


def judge(df: pd.DataFrame, col: str) -> dict:
    st = {e: lib.summarize(df[df.era == e], col) for e in ("ESKI", "YENI")}
    st["TUM"] = lib.summarize(df, col)
    keep = ("n", "mean", "median", "hit", "P", "mean_s15", "ex_top5", "worst")
    st = {e: {k: st[e].get(k) for k in keep} for e in st}
    st["yil"] = {int(y): round(float(g[col].mean()), 3) for y, g in df.groupby("year")}
    st["gecti_cekirdek"] = bool(all(st[e]["n"] and st[e]["mean"] > 0 and st[e]["P"] >= 0.90 for e in ("ESKI", "YENI"))
                               and st["TUM"]["mean_s15"] > 0)
    return st


def main() -> None:
    m1 = lib.load_m1()
    D = lib.daily_table(m1)
    vixp = lib.vix_prev_map(D.d.tolist())
    out = {}
    s1h, s1l = lib.to_frame(s1_gap(m1, D, vixp, "hi")), lib.to_frame(s1_gap(m1, D, vixp, "lo"))
    out["S1 korku açılış boşluğu"] = {"korku": judge(s1h, "net_bp"), "kontrol": judge(s1l, "net_bp")}
    out["S1 korku açılış boşluğu"]["gecti"] = bool(out["S1 korku açılış boşluğu"]["korku"]["gecti_cekirdek"]
                                                  and s1h.net_bp.mean() > s1l.net_bp.mean())
    s2 = lib.to_frame(range_break(m1, D, vixp, -1, 570, 585, 930, 955, "S2"))
    out["S2 ORB kısa aynası"] = judge(s2, "R")
    out["S2 ORB kısa aynası"]["gecti"] = out["S2 ORB kısa aynası"]["gecti_cekirdek"]
    s3 = lib.to_frame(range_break(m1, D, vixp, +1, 180, 195, 480, 565, "S3"))
    out["S3 Avrupa açılışı kırılımı"] = judge(s3, "R")
    out["S3 Avrupa açılışı kırılımı"]["gecti"] = out["S3 Avrupa açılışı kırılımı"]["gecti_cekirdek"]
    s4h, s4l = lib.to_frame(s4_pm(m1, D, vixp, "hi")), lib.to_frame(s4_pm(m1, D, vixp, "lo"))
    out["S4 korku günü öğleden sonra"] = {"korku": judge(s4h, "net_bp"), "kontrol": judge(s4l, "net_bp")}
    out["S4 korku günü öğleden sonra"]["gecti"] = bool(out["S4 korku günü öğleden sonra"]["korku"]["gecti_cekirdek"]
                                                      and s4h.net_bp.mean() > s4l.net_bp.mean())
    (lib.RESULTS / "e_ek2.json").write_text(json.dumps(out, indent=1, default=str, ensure_ascii=False), encoding="utf-8")
    for k, v in out.items():
        arms = {"korku": v["korku"], "kontrol": v["kontrol"]} if "korku" in v else {"": v}
        for a, s in arms.items():
            print(k, a, {e: (s[e]["n"], round(s[e]["mean"], 3) if s[e]["mean"] is not None else None,
                             round(s[e]["P"], 3) if s[e]["P"] == s[e]["P"] else None) for e in ("ESKI", "YENI")},
                  "s15", round(s["TUM"]["mean_s15"], 3), "yıl", s["yil"])
        print("   GEÇTİ:", v["gecti"])


if __name__ == "__main__":
    main()
