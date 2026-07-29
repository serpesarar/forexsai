#!/usr/bin/env python3
"""limit_deep_probe.py — BÜYÜK geri çekilme limitleri (+0.75/+1.00/+1.50 ATR) kör testi.
Küçük offsetler ters seçilimden ölüyordu; büyük offset farklı bir işlem (gerilmiş
tepkiye satış = mean-reversion). Bu dosya onu kırmaya çalışır."""
from datetime import datetime, timezone
import numpy as np
import lab_vol_tpsl_grid as G

H = 72
LOT = 5.0
SPREAD = 1.5

t, o, h, l, c, v = G.load_csv("nas100_m5.csv")
n = len(c)
atr = G.wilder_atr(h, l, c)
cut = t[int(n * 0.7)]

evs = []
for i in range(G.ATR_PERIOD + 5, n - H - 20):
    a = atr[i]
    if not np.isfinite(a) or a <= 0:
        continue
    body = o[i] - c[i]; rng_ = h[i] - l[i]
    if rng_ <= 0 or body <= 0 or body < a or body / rng_ < 0.55:
        continue
    if not (c[i + 1] < l[i]):                      # teyit = lowbreak
        continue
    evs.append((i, a))


def market(e, tp_d, sl_d, sp=SPREAD):
    px = c[e]; tp_px, sl_px = px - tp_d, px + sl_d
    end = min(e + H, n - 1)
    for j in range(e + 1, end + 1):
        if h[j] >= sl_px - sp:
            return "LOSS", px - sl_px
        if l[j] <= tp_px - sp:
            return "WIN", px - tp_px
    return "TIME", px - c[end] - sp


def limit(e, L, expiry, tp_d, sl_d, sp=SPREAD):
    fill = None
    for j in range(e + 1, min(e + expiry, n - 1) + 1):
        if h[j] >= L:
            fill = j; break
    if fill is None:
        return None
    tp_px, sl_px = L - tp_d, L + sl_d
    end = min(fill + H, n - 1)
    for j in range(fill, end + 1):
        if h[j] >= sl_px - sp:
            return "LOSS", L - sl_px
        if l[j] <= tp_px - sp:
            return "WIN", L - tp_px
    return "TIME", L - c[end] - sp


def show(rows, sig, label):
    if not rows or sig == 0:
        print(f"  {label:<34} —"); return
    net = np.asarray([r[1] for r in rows], float)
    print(f"  {label:<34}{len(rows):>6}{100.0 * len(rows) / sig:>8.1f}"
          f"{100.0 * sum(1 for r in rows if r[0] == 'WIN') / len(rows):>7.1f}"
          f"{net.mean():>+10.2f}{net.sum() / sig:>+11.2f}{net.sum() * LOT:>+11,.0f}")


print("=" * 104)
print(f"BÜYÜK GERİ ÇEKİLME LİMİTLERİ — teyit=lowbreak, n={len(evs):,}, TP80/SL30, spread {SPREAD}")
print("=" * 104)
print(f"  {'konfig':<34}{'n':>6}{'dolum%':>8}{'TP%':>7}{'EV/işlem':>10}{'EV/sinyal':>11}{'$':>11}")
for off in (0.75, 1.00, 1.50):
    for exp in (6, 12, 24):
        for tag, want in (("TÜMÜ  ", None), ("EĞİTİM", True), ("TEST  ", False)):
            sub = [(i, a) for i, a in evs
                   if want is None or (t[i] < cut) == want]
            rows = [r for r in (limit(i + 1, c[i + 1] + off * a, exp, 80.0, 30.0)
                                for i, a in sub) if r]
            show(rows, len(sub), f"{tag} +{off:.2f}×ATR / {exp} bar")
    print()

print("TERS SEÇİLİM — büyük offsetlerde ıskalananlar market'te ne yapardı?")
for off, exp in ((0.75, 12), (1.00, 12), (1.00, 24)):
    fl, ms = [], []
    for i, a in evs:
        e = i + 1
        r = limit(e, c[e] + off * a, exp, 80.0, 30.0)
        (fl if r else ms).append(market(e, 80.0, 30.0)[1])
    print(f"  +{off:.2f}×ATR/{exp}bar → DOLAN n={len(fl):>5} market EV={np.mean(fl):+7.2f} p | "
          f"IŞKALANAN n={len(ms):>5} market EV={np.mean(ms):+7.2f} p")

print("\nÇEYREKLİK — +1.00×ATR / 12 bar")
byq = {}
for i, a in evs:
    e = i + 1
    r = limit(e, c[e] + 1.00 * a, 12, 80.0, 30.0)
    d = datetime.fromtimestamp(int(t[i]), tz=timezone.utc)
    q = f"{d.year}Ç{(d.month - 1) // 3 + 1}"
    byq.setdefault(q, {"rows": [], "sig": 0})
    byq[q]["sig"] += 1
    if r:
        byq[q]["rows"].append(r)
print(f"  {'çeyrek':<34}{'n':>6}{'dolum%':>8}{'TP%':>7}{'EV/işlem':>10}{'EV/sinyal':>11}{'$':>11}")
for q in sorted(byq):
    show(byq[q]["rows"], byq[q]["sig"], q)

print("\nKAYMA — +1.00×ATR/12 bar (limit: girişte kayma YOK, çıkışta var) vs MARKET")
print(f"  {'spread':<34}{'n':>6}{'dolum%':>8}{'TP%':>7}{'EV/işlem':>10}{'EV/sinyal':>11}{'$':>11}")
for sp in (1.5, 3.0, 5.0):
    rows = [r for r in (limit(i + 1, c[i + 1] + 1.00 * a, 12, 80.0, 30.0, sp)
                        for i, a in evs) if r]
    show(rows, len(evs), f"LİMİT spread {sp}")
for sp in (1.5, 3.0, 5.0):
    rows = [market(i + 1, 80.0, 30.0, sp) for i, a in evs]
    show(rows, len(evs), f"MARKET spread {sp}")
