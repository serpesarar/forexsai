"""Tur 2: üç sembol broker verisi: ORB × rejim, iki yön, çıkış, söndürme, dönüş."""
import itertools, time, pandas as pd, numpy as np
from lab2 import *
T = time.time()
CFG = {"NAS100": {"anchors": [(570, 955), (600, 955)]}, "XAUUSD": {"anchors": [(510, 805), (570, 805), (180, 510)]}, "SpotCrude": {"anchors": [(540, 865), (570, 865), (180, 510)]}}
FL = ["tümü", "vix≥18,4", "vix<18,4", "vix18-25", "vix≥25", "iv yüksek", "iv düşük", "dün−", "dün+", "iv yüksek∧dün−", "iv yüksek∧dün+", "iv düşük∧dün−", "iv düşük∧dün+", "vix≥18,4∧dün−", "vix≥18,4∧dün+", "rv_üst%33", "rv_alt%33", "boşluk+", "boşluk−", "5g−", "5g+", "sal-per", "cuma", "veri günü", "veri dışı"]
OUT = []
for sym, cfg in CFG.items():
    for o0, f0 in cfg["anchors"]:
        K = build2(sym, "M15", o0, f0, a="2022-08-15", b="2025-01-01"); Bg = build2(sym, "M30", o0, f0, a="2018-05-25", b="2022-08-15"); S = build2(sym, "M15", o0, f0, a="2025-01-01"); M5 = build2(sym, "M5", o0, f0, a="2025-06-15")
        sp = SP[sym]; last = f0 - 25
        print(sym, o0, len(K), len(Bg), len(S), len(M5), round(time.time() - T), flush=True)
        fams = {}
        for side in (1, -1):
            nm = "uzun" if side > 0 else "kısa"
            fams[f"ORB {nm} 2R"] = lambda bar, orl, d, side=side: brk(d, bar, orl, side, o0, last, f0, sp)
            fams[f"ORB {nm} 1R"] = lambda bar, orl, d, side=side: brk(d, bar, orl, side, o0, last, f0, sp, tgt=1.0)
            fams[f"ORB {nm} zaman"] = lambda bar, orl, d, side=side: brk(d, bar, orl, side, o0, last, f0, sp, tgt=None)
            fams[f"Kırılımı sön {nm} 1R"] = lambda bar, orl, d, side=side: brk(d, bar, orl, side, o0, last, f0, sp, tgt=1.0, fade=True)
            fams[f"Dönüş {nm} 2R"] = lambda bar, orl, d, side=side: reclaim(d, bar, orl, side, o0, last, f0, sp)
        for name, fn in fams.items():
            for fl_ in FL:
                fl = FLT2[fl_]; row = {"sym": sym, "çapa": f"{o0//60:02d}:{o0%60:02d}", "aile": name, "filtre": fl_}
                for key, days, bar, orl in (("k", K, 15, 30), ("b", Bg, 30, 30), ("s", S, 15, 30), ("m5", M5, 5, 15)):
                    m, _ = evalset(days, lambda d: fn(bar, orl, d), fl)
                    ledger(sym, f"T2 {name} {row['çapa']}", fl_, key, m)
                    for f_ in ("n", "R", "bp", "P", "y1", "y2"): row[f"{key}_{f_}"] = m.get(f_)
                OUT.append(row)
df = pd.DataFrame(OUT); df.to_csv(HERE / "results/r2.csv", index=False); print("hücre", len(df), round(time.time() - T))
