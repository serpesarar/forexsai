#!/usr/bin/env python3
"""confirm_entry_lab.py — GİRİŞ ZAMANLAMASI: kırılım mumunda mı, İKİNCİ mumda mı?

Kullanıcı düzeltmesi (2026-07-28): "bir mum kırılınca, İKİNCİ bundan sonra işlem
açılınca oranlar ne kadar?" — yani giriş, büyük kırmızı mumun kapanışında değil,
ONDAN SONRAKİ (teyit) mumun kapanışında.

Aynı sızıntısız kurallar: göstergeler yalnız kapanmış barlardan, giriş bir bar
kapanışı, sonuç yalnız SONRAKİ barların high/low'u, aynı barda TP+SL → KAYIP.
Veri: sell_after_red_lab.py'ın --dump ile bıraktığı CSV (kutuda nas100_m5.csv).
"""
from __future__ import annotations

import argparse
import csv
from bisect import bisect_left

import numpy as np

ATR_PERIOD = 14
PIVOT_L = PIVOT_R = 2
LEVEL_WINDOW = 400
LEVEL_TOL_ATR = 0.35
MIN_TOUCH = 2
SPREAD = 1.5
BOT_TP, BOT_SL = 80.0, 110.0
LOT = 5.0
HORIZON = 72


def load_csv(path):
    t, o, h, l, c, v = [], [], [], [], [], []
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            t.append(int(float(row["time"]))); o.append(float(row["open"]))
            h.append(float(row["high"])); l.append(float(row["low"]))
            c.append(float(row["close"])); v.append(float(row["vol"]))
    return (np.asarray(t), np.asarray(o), np.asarray(h),
            np.asarray(l), np.asarray(c), np.asarray(v))


def wilder_atr(high, low, close, period=ATR_PERIOD):
    n = len(close)
    tr = np.empty(n)
    tr[0] = high[0] - low[0]
    prev = close[:-1]
    tr[1:] = np.maximum(high[1:] - low[1:],
                        np.maximum(np.abs(high[1:] - prev), np.abs(low[1:] - prev)))
    atr = np.full(n, np.nan)
    atr[period] = tr[1:period + 1].mean()
    for i in range(period + 1, n):
        atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period
    return atr


def pivot_lows(low, left=PIVOT_L, right=PIVOT_R):
    out = []
    for i in range(left, len(low) - right):
        if low[i] <= low[i - left:i].min() and low[i] <= low[i + 1:i + right + 1].min():
            out.append((i + right, i, float(low[i])))
    return out


def cluster(values, tol, min_touch=MIN_TOUCH):
    if not values:
        return []
    vals = sorted(values)
    groups, cur = [], [vals[0]]
    for x in vals[1:]:
        if x - cur[-1] <= tol:
            cur.append(x)
        else:
            groups.append(cur); cur = [x]
    groups.append(cur)
    return [float(np.mean(g)) for g in groups if len(g) >= min_touch]


def sim_sell(idx, entry, tp, sl, h, l, c, horizon=HORIZON, spread=SPREAD):
    end = min(idx + horizon, len(c) - 1)
    for j in range(idx + 1, end + 1):
        hit_sl = h[j] >= sl - spread
        hit_tp = l[j] <= tp - spread
        if hit_sl and hit_tp:
            return "LOSS", entry - sl
        if hit_sl:
            return "LOSS", entry - sl
        if hit_tp:
            return "WIN", entry - tp
    return "TIME", entry - c[end] - spread


def report(rows, label):
    """rows = [(outcome, net, risk)]"""
    if len(rows) < 20:
        print(f"  {label:<46} n={len(rows)} (çok az, atlandı)")
        return
    nets = np.asarray([r[1] for r in rows], dtype=float)
    risks = np.asarray([r[2] for r in rows], dtype=float)
    rr = nets / risks
    wr = 100.0 * float((nets > 0).mean())
    tp_rate = 100.0 * sum(1 for r in rows if r[0] == "WIN") / len(rows)
    sl_rate = 100.0 * sum(1 for r in rows if r[0] == "LOSS") / len(rows)
    rng = np.random.default_rng(7)
    idx = rng.integers(0, len(rr), size=(2000, len(rr)))
    p = float((rr[idx].mean(axis=1) > 0).mean())
    print(f"  {label:<46} n={len(rows):>5}  kâr%={wr:>5.1f}  TP%={tp_rate:>5.1f}  "
          f"SL%={sl_rate:>5.1f}  EV={nets.mean():>+7.2f}p ({rr.mean():>+6.3f}R)  "
          f"{nets.sum() * LOT:>+11,.0f}$  P(EV>0)=%{100 * p:.0f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="nas100_m5.csv")
    ap.add_argument("--body-atr", type=float, default=1.0)
    ap.add_argument("--body-ratio", type=float, default=0.55)
    args = ap.parse_args()

    t, o, h, l, c, v = load_csv(args.csv)
    n = len(c)
    atr = wilder_atr(h, l, c)
    piv = pivot_lows(l)
    piv_conf = [p[0] for p in piv]
    piv_bar = [p[1] for p in piv]

    warm = LEVEL_WINDOW + 10
    events = []
    for i in range(warm, n - HORIZON - 4):
        a = atr[i]
        if not np.isfinite(a) or a <= 0:
            continue
        body = o[i] - c[i]
        rng_ = h[i] - l[i]
        if rng_ <= 0 or body <= 0:
            continue
        if body < args.body_atr * a or body / rng_ < args.body_ratio:
            continue
        hi_ = bisect_left(piv_conf, i + 1)
        lo_ = bisect_left(piv_bar, i - LEVEL_WINDOW)
        levels = cluster([p[2] for p in piv[lo_:hi_]], LEVEL_TOL_ATR * a)
        broke = any(c[i] < lv < c[i - 1] for lv in levels)     # kapanışla seviye deldi
        below = [lv for lv in levels if lv <= c[i]]
        d_below = (c[i] - max(below)) / a if below else float("inf")
        events.append({"i": i, "atr": a, "broke": broke, "d_below": d_below})

    print("=" * 118)
    print(f"GİRİŞ ZAMANLAMASI LAB — NAS100 5m, {n:,} bar, {len(events):,} büyük kırmızı mum")
    print(f"spread={SPREAD}p · lot={LOT} · zaman-stopu {HORIZON} bar · aynı barda TP+SL = KAYIP")
    print("  'kâr%' = net kârla kapanan işlem oranı (zaman-stopu dahil) · 'TP%' = hedefe ulaşan")
    print("=" * 118)

    GEOS = {
        "BOT 80/110": lambda px, a: (px - BOT_TP, px + BOT_SL, BOT_SL),
        "ATR 1.0:1.0": lambda px, a: (px - a, px + a, a),
        "ATR 0.75:1.0": lambda px, a: (px - 0.75 * a, px + a, a),
    }

    # giriş varyantları: (etiket, giriş barı ofseti, ek koşul)
    VARIANTS = [
        ("A) kırılım mumunun kapanışı (önceki test)", 0, lambda e: True),
        ("B) 2. mumun kapanışı — koşulsuz bekle", 1, lambda e: True),
        ("C) 2. mum da KIRMIZI ise (teyit)", 1, lambda e: c[e["i"] + 1] < o[e["i"] + 1]),
        ("D) 2. mum 1. mumun DİBİNİ kırdıysa", 1,
         lambda e: c[e["i"] + 1] < l[e["i"]]),
        ("E) 2. mum kırmızı VE dibi kırdı", 1,
         lambda e: c[e["i"] + 1] < o[e["i"] + 1] and c[e["i"] + 1] < l[e["i"]]),
        ("F) 2. mum YEŞİL çıktıysa (teyit yok)", 1, lambda e: c[e["i"] + 1] >= o[e["i"] + 1]),
        ("G) 3. mumun kapanışı", 2, lambda e: True),
        ("H) 2.+3. mum ikisi de kırmızı", 2,
         lambda e: c[e["i"] + 1] < o[e["i"] + 1] and c[e["i"] + 2] < o[e["i"] + 2]),
    ]

    for gname, geo in GEOS.items():
        print(f"\n▸ GEOMETRİ: {gname}")
        for label, off, cond in VARIANTS:
            rows = []
            for e in events:
                i = e["i"]
                if not cond(e):
                    continue
                idx = i + off
                px = c[idx]
                tp, sl, risk = geo(px, e["atr"])
                out, net = sim_sell(idx, px, tp, sl, h, l, c)
                rows.append((out, net, risk))
            report(rows, label)

    print("\n" + "=" * 118)
    print("YALNIZ 'SEVİYE KIRAN' MUMLAR (kapanışıyla bir desteği deldi) — kullanıcının 'kırılınca' tarifi")
    print("=" * 118)
    br = [e for e in events if e["broke"]]
    print(f"  bu alt küme: n={len(br):,} olay")
    for gname, geo in GEOS.items():
        print(f"\n▸ GEOMETRİ: {gname}")
        for label, off, cond in VARIANTS[:6]:
            rows = []
            for e in br:
                if not cond(e):
                    continue
                idx = e["i"] + off
                px = c[idx]
                tp, sl, risk = geo(px, e["atr"])
                out, net = sim_sell(idx, px, tp, sl, h, l, c)
                rows.append((out, net, risk))
            report(rows, label)

    # kronolojik kör test — en iyi varyantın gerçekten dayanıp dayanmadığı
    cut = t[int(n * 0.7)]
    print("\n" + "=" * 118)
    print("KÖR TEST (ilk %70 eğitim / son %30 test) — teyitli varyantlar, tüm olaylar")
    print("=" * 118)
    for gname, geo in GEOS.items():
        for label, off, cond in VARIANTS[2:5]:
            for tag, keep in (("EĞİTİM", True), ("TEST  ", False)):
                rows = []
                for e in events:
                    i = e["i"]
                    if not cond(e):
                        continue
                    if (t[i] < cut) != keep:
                        continue
                    idx = i + off
                    px = c[idx]
                    tp, sl, risk = geo(px, e["atr"])
                    out, net = sim_sell(idx, px, tp, sl, h, l, c)
                    rows.append((out, net, risk))
                report(rows, f"{tag} | {gname} | {label[:34]}")


if __name__ == "__main__":
    main()
