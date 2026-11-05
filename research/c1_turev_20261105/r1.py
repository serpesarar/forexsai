"""NDX tur 1: C0 tabanlı filtre, çıkış, OR, kısa, söndürme, başarısız kırılım, geri test, ikinci şans, çapalar."""
from __future__ import annotations
import itertools, sys, time
import numpy as np, pandas as pd
from lab import *

T0 = time.time()
D5 = build_days("5m"); D30 = build_days("30m"); D60 = build_days("1h")
print("gün", len(D5), len(D30), len(D60), round(time.time() - T0, 1), flush=True)
LAST = 930; END = 955
def rule_break(day, bar, orlen, side, stopk, tgt, a0, last, end, sp=SPREAD, fade=False):
    """İlk kapanış aralık dışında → sonraki bar. stopk: 'mid'|'opp'. fade: kırılım yönünün TERSİ."""
    z = or_of(day, a0, orlen, bar)
    if not z: return None
    oh, ol, ie = z
    for i in range(ie + 1, len(day.o)):
        if day.m[i] + bar > last: return None
        if (day.c[i] > oh) if side > 0 else (day.c[i] < ol):
            if not fade:
                st = (oh + ol) / 2 if stopk == "mid" else (ol if side > 0 else oh)
                return sim(day, i + 1, side, st, tgt, end, sp)
            s2 = -side; w = (oh - ol) / 2 if stopk == "mid" else (oh - ol)
            st = (day.c[i] + w) if s2 < 0 else (day.c[i] - w)
            return sim(day, i + 1, s2, st, tgt, end, sp)
    return None
def rule_reclaim(day, bar, orlen, side, tgt, within, a0=570, last=LAST, end=END, sp=SPREAD):
    """Başarısız kırılımdan dönüş. side=+1: kapanış OR dibi altı, sonra within bar içinde dibin üstünde kapanış → BUY, stop dönemin dibi."""
    z = or_of(day, a0, orlen, bar)
    if not z: return None
    oh, ol, ie = z; n = len(day.o)
    for i in range(ie + 1, n):
        if day.m[i] + bar > last: return None
        if (day.c[i] < ol) if side > 0 else (day.c[i] > oh):
            for k in range(i + 1, min(i + 1 + within, n)):
                if day.m[k] + bar > last: return None
                if (day.c[k] > ol) if side > 0 else (day.c[k] < oh):
                    st = day.l[i:k + 1].min() if side > 0 else day.h[i:k + 1].max()
                    return sim(day, k + 1, side, st, tgt, end, sp)
            return None
    return None
def rule_retest(day, bar, orlen, tgt, within, a0=570, last=LAST, end=END, sp=SPREAD):
    """Kırılımdan sonra OR tepesine limit geri test: bar dibi tepenin 1 pt altına inerse dolum. Dolum barında stop kontrolü dahil."""
    z = or_of(day, a0, orlen, bar)
    if not z: return None
    oh, ol, ie = z; n = len(day.o); st = (oh + ol) / 2
    for i in range(ie + 1, n):
        if day.m[i] + bar > last: return None
        if day.c[i] > oh:
            for k in range(i + 1, min(i + 1 + within, n)):
                if day.l[k] <= oh - 1:
                    e = oh + sp; risk = e - st
                    if risk <= MIN_RISK * e: return None
                    tp = e + tgt * risk; lastb = None
                    if day.l[k] <= st: return -1.0, -risk / e * 1e4, risk / e * 1e4
                    for j in range(k + 1, n):
                        if day.m[j] >= end: break
                        lastb = j
                        if day.l[j] <= st: return -1.0, -risk / e * 1e4, risk / e * 1e4
                        if day.h[j] >= tp: return tgt, tgt * risk / e * 1e4, risk / e * 1e4
                    if lastb is None: return None
                    r = (day.c[lastb] - e) / risk; return r, r * risk / e * 1e4, risk / e * 1e4
            return None
    return None
def rule_second(day, bar, orlen, tgt, a0=570, last=LAST, end=END, sp=SPREAD):
    """İlk kırılım stopla bittiyse ikinci tepe üstü kapanışta yeniden gir."""
    z = or_of(day, a0, orlen, bar)
    if not z: return None
    oh, ol, ie = z; st = (oh + ol) / 2; n = len(day.o); stopped = False; first = False
    for i in range(ie + 1, n):
        if day.m[i] + bar > last: return None
        if not first:
            if day.c[i] > oh: first = True
            continue
        if not stopped:
            if day.l[i] <= st: stopped = True
            continue
        if day.c[i] > oh: return sim(day, i + 1, 1, st, tgt, end, sp)
    return None
def rule_reverse(day, bar, orlen, tgt, a0=570, last=LAST, end=END, sp=SPREAD):
    """Karşıt: yukarı kırılım stopla bitti → stop anı sonrası kısa; stop OR tepesi."""
    z = or_of(day, a0, orlen, bar)
    if not z: return None
    oh, ol, ie = z; st = (oh + ol) / 2; n = len(day.o); first = False
    for i in range(ie + 1, n):
        if day.m[i] + bar > last: return None
        if not first:
            if day.c[i] > oh: first = True
            continue
        if day.l[i] <= st:
            return sim(day, i + 1, -1, oh, tgt, end, sp)
        if day.h[i] >= oh + 2 * (oh - st): return None
    return None

def bars_of(name): return {"5m": 5, "30m": 30, "1h": 60}[name]
def anchor_of(name, a0=570): return a0 if name != "1h" else (a0 if a0 % 60 == 0 else a0 + 30)
def eval_cell(fam, label, fn, fl_name, or5, indep=True):
    """fn(day, bar, orlen, a0) → sonuç. Keşif 5m 2024-25, bağımsız 30m,1h, son 2026."""
    fl = FILTERS[fl_name]; res = {}
    sets = [("k", [d for d in D5 if d.f["y"] <= 2025], 5, or5), ("s26", [d for d in D5 if d.f["y"] == 2026], 5, or5)]
    if indep: sets += [("b30", D30, 30, max(30, or5)), ("b60", D60, 60, 60)]
    for key, days, bar, orl in sets:
        rows = []
        for d in days:
            try:
                ok = fl(d.f)
            except Exception:
                ok = False
            if ok is not True and ok is not np.True_: continue
            z = fn(d, bar, orl)
            if z: rows.append((str(d.d), z[0], z[1], z[2]))
        res[key] = metrics(rows); ledger("NDX", fam, f"{label}|{fl_name}", key, res[key]); res[key + "_days"] = {r[0] for r in rows}
    return res
OUT = []
def run(fam, label, fn, flts, or5=15, indep=True):
    for fl in flts:
        r = eval_cell(fam, label, fn, fl, or5, indep)
        row = {"aile": fam, "hücre": label, "filtre": fl}
        for k in ("k", "b30", "b60", "s26"):
            for f_ in ("n", "R", "bp", "P"):
                if k in r: row[f"{k}_{f_}"] = r[k].get(f_)
            if k == "k": row["k_y1"], row["k_y2"] = r[k].get("y1"), r[k].get("y2")
        OUT.append(row)
ALL = list(FILTERS)
HI = ["tümü", "vix≥18,4", "vix<18,4", "vix18-25", "vix≥25"]
print("F1 filtre", flush=True); run("F1 filtre", "uzun OR15 mid 2R", lambda d, b, o: rule_break(d, b, o, 1, "mid", 2.0, anchor_of("x" if b < 60 else "1h"), LAST, END), ALL)
print("F2 kısa", flush=True); run("F2 kısa", "kısa OR15 mid 2R", lambda d, b, o: rule_break(d, b, o, -1, "mid", 2.0, anchor_of("x" if b < 60 else "1h"), LAST, END), ALL)
print("F3 çıkış", flush=True)
for s, t in itertools.product(("mid", "opp"), (1.0, 1.5, 2.0, 3.0, 4.0, None)):
    run("F3 çıkış", f"uzun {s} {t}R", lambda d, b, o, s=s, t=t: rule_break(d, b, o, 1, s, t, anchor_of("x" if b < 60 else "1h"), LAST, END), ["vix≥18,4", "vix<18,4"])
print("F4 OR", flush=True)
for o_ in (5, 10, 15, 30, 60):
    run("F4 OR", f"uzun OR{o_}", lambda d, b, o, o_=o_: rule_break(d, b, o, 1, "mid", 2.0, anchor_of("x" if b < 60 else "1h"), LAST, END), ["vix≥18,4", "vix<18,4"], or5=o_)
print("F5 söndür", flush=True)
for sd, t in itertools.product((1, -1), (1.0, 2.0)):
    run("F5 söndür", f"{'tepe kırılımını sat' if sd > 0 else 'dip kırılımını al'} {t}R", lambda d, b, o, sd=sd, t=t: rule_break(d, b, o, sd, "mid", t, anchor_of("x" if b < 60 else "1h"), LAST, END, fade=True), HI + ["vix<15", "vix≥18,4∧dün−", "vix≥18,4∧boşluk−", "geri eğim(vix>vix3m)"])
print("F6 dönüş", flush=True)
for sd, t, w in itertools.product((1, -1), (1.0, 2.0, 3.0), (3, 6, 12)):
    run("F6 dönüş", f"{'dip geri alındı BUY' if sd > 0 else 'tepe geri alındı SELL'} {t}R w{w}", lambda d, b, o, sd=sd, t=t, w=w: rule_reclaim(d, b, o, sd, t, w if b == 5 else max(1, w // 3), anchor_of("x" if b < 60 else "1h")), HI)
print("F7 geri test", flush=True)
for t, w in itertools.product((1.0, 2.0, 3.0), (6, 12, 24)):
    run("F7 geri test", f"tepe limit {t}R w{w}", lambda d, b, o, t=t, w=w: rule_retest(d, b, o, t, w if b == 5 else max(1, w // 6), anchor_of("x" if b < 60 else "1h")), HI)
print("F8 ikinci şans + ters", flush=True)
run("F8 ikinci", "ikinci kırılım 2R", lambda d, b, o: rule_second(d, b, o, 2.0, anchor_of("x" if b < 60 else "1h")), HI)
for t in (1.0, 2.0):
    run("F8 ters", f"stop sonrası kısa {t}R", lambda d, b, o, t=t: rule_reverse(d, b, o, t, anchor_of("x" if b < 60 else "1h")), HI)
print("F9 çapalar", flush=True)
for a0, sd, t in itertools.product((180, 480, 600, 660, 780, 840), (1, -1), (2.0, None)):
    last_ = min(930, a0 + 180); end_ = 955 if a0 >= 570 else 570
    run("F9 çapa", f"{a0//60:02d}:{a0%60:02d} {'uzun' if sd>0 else 'kısa'} {t}R", lambda d, b, o, a0=a0, sd=sd, t=t, last_=last_, end_=end_: rule_break(d, b, o, sd, "mid", t, anchor_of("x" if b < 60 else "1h", a0), last_, end_), ["tümü", "vix≥18,4", "vix<18,4"], or5=30)
df = pd.DataFrame(OUT); df.to_csv(HERE / "results/r1.csv", index=False)
print("hücre", len(df), "süre", round(time.time() - T0))
