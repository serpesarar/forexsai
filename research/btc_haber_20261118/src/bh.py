"""bh.py — BTC: NDX korku gecesi dilimleri (H1), habersiz ABD gün içi düşüş (H2), olay günü devam (H3). python bh.py"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
for p in ("research/btc_korku_20261118/src", "research/korku_genislik_20261118/src"):
    sys.path.insert(0, str(ROOT / p))
import bk  # noqa: E402
import gn  # noqa: E402

G = gn.kk.G
RES = ROOT / "research/btc_haber_20261118/results"
NY = "America/New_York"
RT, SW = 4.0, 3.84
P_B = 1 - 0.05 / 7
ESKI_END = gn.kk.ESKI_END


def u(d, hh, mm) -> int:
    return int(pd.Timestamp(datetime(d.year, d.month, d.day, hh, mm), tz=NY).timestamp())


def main() -> None:
    RES.mkdir(exist_ok=True)
    b = bk.btc()
    t, o, c = b.t.values, b.o.values, b.c.values

    def px(v: int) -> float:
        i = int(np.searchsorted(t, v))
        return o[i] if i < len(t) and t[i] - v <= 300 else np.nan

    cal = pd.read_csv(ROOT / "research/xau_best_days_20261015/makro/out/calendar.csv")
    ev = set(pd.to_datetime(cal.date).dt.date)
    n = gn.nts(G.ndx_bars(), 60)
    k1 = dict(zip(n.d, n.K1))
    days = sorted(k1)
    out = {}

    # H1
    rows = []
    for i in range(len(days) - 1):
        d, e = days[i], days[i + 1]
        p16, p930, p16n = px(u(d, 16, 0)), px(u(e, 9, 30)), px(u(e, 16, 0))
        if not np.isfinite(p16 * p930 * p16n):
            continue
        ng = (e - d).days
        rows.append({"d": d, "K1": k1[d], "gece": (p930 / p16 - 1) * 1e4 - RT - SW * ng, "seans": (p16n / p930 - 1) * 1e4 - RT,
                     "tam": (p16n / p16 - 1) * 1e4 - RT - SW * ng})
    h1 = pd.DataFrame(rows)
    h1["era"] = np.where(h1.d <= ESKI_END, "ESKI", "YENI")
    for col in ("gece", "seans", "tam"):
        rec = {}
        for er in ("ESKI", "YENI"):
            z = h1[h1.era == er]
            rec[er] = {"n": int(z.K1.sum()), "ort": round(float(z[col][z.K1].mean()), 1), "taban": round(float(z[col][~z.K1].mean()), 1)}
        a, z = h1[h1.K1], h1[~h1.K1]
        rec["P"] = round(G.KS.diff_p(a[col].values, a.d.astype(str).values, z[col].values, z.d.astype(str).values), 4)
        ok = all(rec[er]["ort"] > 0 and rec[er]["ort"] > rec[er]["taban"] for er in ("ESKI", "YENI"))
        rec["hukum"] = "B" if ok and rec["P"] >= P_B else ("C+" if ok else "X")
        out[f"H1_{col}"] = rec
        print("H1", col, rec, flush=True)

    # H2 + H3 için gün başı yapılar
    x = G._local(b, NY)
    bars = []
    for d, g in x[(x.mn >= 570) & (x.mn < 960)].groupby("day"):
        if d not in k1:
            continue
        key = (g.mn.values - 570) // 30
        st = np.flatnonzero(np.r_[True, key[1:] != key[:-1]])
        en = np.r_[st[1:], len(key)] - 1
        bars.append(pd.DataFrame({"d": d, "k": key[st], "r": g.c.values[en] / g.o.values[st] - 1, "tend": g.t.values[en] + 300}))
    B = pd.concat(bars)
    B = B[B.k >= 1]
    sd = B.groupby("d").r.apply(lambda v: float(np.sqrt((v ** 2).mean())))
    sig = sd.shift(1).rolling(30, min_periods=20).mean()
    dl = list(sig.index)
    nxt = {dl[i]: dl[i + 1] for i in range(len(dl) - 1)}
    rng = np.random.default_rng(13)
    rows = []
    for d, g in B.groupby("d"):
        s = sig.get(d, np.nan)
        if not np.isfinite(s) or d not in nxt:
            continue
        e = nxt[d]
        x16 = px(u(e, 16, 0))
        ng = (e - d).days
        picks = [("rnd", g.tend.values[rng.integers(len(g))])]
        for kk_ in (3, 4):
            h = g[g.r <= -kk_ * s]
            picks.append((f"k{kk_}", h.tend.values[0] if len(h) else None))
        for tag, te in picks:
            if te is None:
                continue
            p0 = px(int(te))
            if np.isfinite(p0 * x16):
                rows.append({"d": d, "tag": tag, "olay": d in ev, "net": (x16 / p0 - 1) * 1e4 - RT - SW * ng})
    h2 = pd.DataFrame(rows)
    h2 = h2[h2.d <= pd.Timestamp("2026-10-02").date()]
    h2["era"] = np.where(h2.d <= ESKI_END, "ESKI", "YENI")
    for kk_ in (3, 4):
        rec = {}
        for grp, gm in (("habersiz", ~h2.olay), ("olay", h2.olay)):
            a, z = h2[gm & (h2.tag == f"k{kk_}")], h2[gm & (h2.tag == "rnd")]
            rec[grp] = {er: {"n": int((a.era == er).sum()), "ort": round(float(a[a.era == er].net.mean()), 1),
                             "taban": round(float(z[z.era == er].net.mean()), 1)} for er in ("ESKI", "YENI")}
            if grp == "habersiz":
                rec["P"] = round(G.KS.diff_p(a.net.values, a.d.astype(str).values, z.net.values, z.d.astype(str).values), 4)
        H = rec["habersiz"]
        ok = all(H[er]["ort"] > 0 and H[er]["ort"] > H[er]["taban"] for er in ("ESKI", "YENI"))
        rec["hukum"] = "B" if ok and rec["P"] >= P_B else ("C+" if ok else "X")
        out[f"H2_k{kk_}"] = rec
        print("H2", kk_, rec, flush=True)

    # H3
    rows = []
    for i in range(len(days) - 1):
        d, e = days[i], days[i + 1]
        p8, p16, p16n = px(u(d, 8, 0)), px(u(d, 16, 0)), px(u(e, 16, 0))
        if np.isfinite(p8 * p16 * p16n):
            rows.append({"d": d, "r": p16 / p8 - 1, "nx": (p16n / p16 - 1) * 1e4, "ng": (e - d).days})
    h3 = pd.DataFrame(rows)
    h3["sig"] = h3.r.shift(1).rolling(30, min_periods=20).std()
    h3 = h3[h3.d <= pd.Timestamp("2026-10-02").date()].dropna()
    h3["dev"] = np.sign(h3.r) * h3.nx - RT - SW * h3.ng
    h3["olay"] = h3.d.isin(ev)
    h3["era"] = np.where(h3.d <= ESKI_END, "ESKI", "YENI")
    for kk_ in (1.5, 2.0):
        bg = h3[h3.r.abs() >= kk_ * h3.sig]
        a, z = bg[bg.olay], bg[~bg.olay]
        rec = {er: {"n": int((a.era == er).sum()), "olay": round(float(a[a.era == er].dev.mean()), 1),
                    "kontrol": round(float(z[z.era == er].dev.mean()), 1)} for er in ("ESKI", "YENI")}
        rec["P"] = round(G.KS.diff_p(a.dev.values, a.d.astype(str).values, z.dev.values, z.d.astype(str).values), 4)
        ok = all(rec[er]["olay"] > 0 and rec[er]["olay"] > rec[er]["kontrol"] for er in ("ESKI", "YENI"))
        rec["hukum"] = "B" if ok and rec["P"] >= P_B else ("C+" if ok else "X")
        out[f"H3_k{kk_}"] = rec
        print("H3", kk_, rec, flush=True)
    (RES / "btc_haber.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
