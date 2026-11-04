"""Sızıntı (prefix) testi: veriyi bir tarihte kesip olay listelerini yeniden üret; kesimden önceki olaylar aynı olmalı."""
import sys; sys.path.insert(0, "/Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_trend")
import numpy as np, pandas as pd, lib_trend as lt, run_trend as rt
m1 = lt.M1()
full = {c["name"]: c["ev"] for c in rt.cells(rt.frames(m1), m1)}
orig = lt.load_tf
for cut in ("2023-06-15 07:00", "2025-02-03 13:00"):
    cm = lt.m(cut)
    def trunc(name, tf, _o=orig, cm=cm):
        d = _o(name, tf)
        return d[d["dec"] <= cm].reset_index(drop=True)
    lt.load_tf = trunc; rt.lt.load_tf = trunc
    part = {c["name"]: c["ev"] for c in rt.cells(rt.frames(m1), m1)}
    lt.load_tf = orig; rt.lt.load_tf = orig
    bad = []
    for k, ev in part.items():
        if k.startswith("H3"):  # H3 1m'den, kesimden etkilenmez
            continue
        a = ev[ev["dec"] <= cm - 2880][["dec", "dir", "sl", "tp"]].round(6).reset_index(drop=True)
        b = full[k]; b = b[b["dec"] <= cm - 2880][["dec", "dir", "sl", "tp"]].round(6).reset_index(drop=True)
        if not a.equals(b):
            bad.append((k, len(a), len(b)))
    print(cut, "uyuşmayan:", bad)
