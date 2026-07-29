#!/usr/bin/env python3
"""break_confirm_split.py — 'seviyeyi KIRAN mum + 2. mum teyidi' kurgusunun
kronolojik kör testi ve çeyreklik dağılımı. lab_confirm_entry.py'ı kütüphane
olarak kullanır (aynı sızıntısız kurallar)."""
from bisect import bisect_left
from datetime import datetime, timezone
import numpy as np
import lab_confirm_entry as L

t, o, h, l, c, v = L.load_csv("nas100_m5.csv")
n = len(c)
atr = L.wilder_atr(h, l, c)
piv = L.pivot_lows(l)
pc = [p[0] for p in piv]; pb = [p[1] for p in piv]

events = []
for i in range(L.LEVEL_WINDOW + 10, n - L.HORIZON - 4):
    a = atr[i]
    if not np.isfinite(a) or a <= 0:
        continue
    body = o[i] - c[i]; rng_ = h[i] - l[i]
    if rng_ <= 0 or body <= 0 or body < a or body / rng_ < 0.55:
        continue
    hi_ = bisect_left(pc, i + 1); lo_ = bisect_left(pb, i - L.LEVEL_WINDOW)
    lv = L.cluster([p[2] for p in piv[lo_:hi_]], L.LEVEL_TOL_ATR * a)
    if not any(c[i] < x < c[i - 1] for x in lv):        # yalnız SEVİYE KIRANLAR
        continue
    events.append((i, a))
cut = t[int(n * 0.7)]
print(f"seviye kıran büyük kırmızı mum: n={len(events):,}  "
      f"kesim tarihi={datetime.fromtimestamp(int(cut), tz=timezone.utc):%Y-%m-%d}")

VAR = {"A) kırılım mumunun kapanışı": (0, lambda i: True),
       "C) 2. mum da kırmızı": (1, lambda i: c[i + 1] < o[i + 1]),
       "D) 2. mum 1.'in dibini kırdı": (1, lambda i: c[i + 1] < l[i])}
GEO = {"BOT 80/110": lambda px, a: (px - L.BOT_TP, px + L.BOT_SL, L.BOT_SL),
       "ATR 1.0:1.0": lambda px, a: (px - a, px + a, a)}

for gname, geo in GEO.items():
    print(f"\n▸ {gname}")
    for vname, (off, cond) in VAR.items():
        for tag, want_train in (("EĞİTİM", True), ("TEST  ", False)):
            rows = []
            for i, a in events:
                if not cond(i) or ((t[i] < cut) != want_train):
                    continue
                px = c[i + off]; tp, sl, risk = geo(px, a)
                rows.append(L.sim_sell(i + off, px, tp, sl, h, l, c) + (risk,))
            L.report([(r[0], r[1], r[2]) for r in rows], f"{tag} | {vname}")

print("\n▸ ÇEYREKLİK — seviye kıran + D varyantı + BOT 80/110")
byq = {}
for i, a in events:
    if not (c[i + 1] < l[i]):
        continue
    px = c[i + 1]
    out, net = L.sim_sell(i + 1, px, px - L.BOT_TP, px + L.BOT_SL, h, l, c)
    d = datetime.fromtimestamp(int(t[i]), tz=timezone.utc)
    byq.setdefault(f"{d.year}Ç{(d.month - 1) // 3 + 1}", []).append((out, net, L.BOT_SL))
for k in sorted(byq):
    L.report(byq[k], k)
