"""Tur 3: kapanış baskısı gecesi (QQQ aşaması). Ön kayıt: PROTOCOL.md EK-2."""
import json
import numpy as np, pandas as pd
from ortak import tablo, ld, degerlendir, ay_blok, OUT
t = tablo(); q = ld("QQQ"); div = q["Dividends"].reindex(t.index).fillna(0.0)
t["y"] = ((t.o.shift(-1) + div.shift(-1)) / t.c - 1) * 1e4
t["ibs"] = (t.c - t.l) / (t.h - t.l); t["g"] = (t.ibs < 0.2).where(t.ibs.notna()); t["vixp"] = t.vix.shift(1)
PER = [("KESIF", "1999-06-01", "2011-01-01"), ("TEST", "2011-01-01", "2018-05-01"), ("KOR", "2018-05-01", "2026-11-10")]
res = {}
def ek(ev):
    a = ev[ev.g == True].y  # noqa: E712
    b = ay_blok(a.index, lambda ix: a.to_numpy()[ix].mean())
    return {"P_ort>4bp": round(float((b > 4).mean()), 3), "med_acik": round(float(a.median()), 1), "ss_acik": round(float(a.std()), 0)}
for nm, a, b in PER:
    seg = t[(t.index >= a) & (t.index < b)].dropna(subset=["y", "vixp", "r", "g"])
    T = seg[(seg.r < 0) & (seg.vixp >= 18.4)]; res[nm] = {**degerlendir(T, "g", cost=4.0), **ek(T)}
    res[nm + "_plasebo_dusukVIX_dusus"] = {k: v for k, v in degerlendir(seg[(seg.r < 0) & (seg.vixp < 18.4)], "g", cost=4.0).items() if k in ("n", "n_acik", "ort_acik", "ort_kapali", "delta", "p_perm")}
    res[nm + "_plasebo_yukselis"] = {k: v for k, v in degerlendir(seg[(seg.r > 0)], "g", cost=4.0).items() if k in ("n", "n_acik", "ort_acik", "ort_kapali", "delta", "p_perm")}
    res[nm + "_tumgun_gece"] = round(float(seg.y.mean()), 2)
    print(nm, res[nm]); print("   düşükVIX", res[nm + "_plasebo_dusukVIX_dusus"]); print("   yükseliş", res[nm + "_plasebo_yukselis"], "| tüm gün gece", res[nm + "_tumgun_gece"])
allT = t[(t.index >= "1999-06-01")].dropna(subset=["y", "vixp", "r", "g"]); allT = allT[(allT.r < 0) & (allT.vixp >= 18.4)]; on = allT[allT.g == True]  # noqa: E712
res["yil_acik"] = {int(k): [int(v["size"]), round(float(v["mean"]), 1)] for k, v in on.groupby(on.index.year).y.agg(["size", "mean"]).iterrows()}
res["havuz_acik"] = {"n": int(len(on)), "ort": round(float(on.y.mean()), 2), "isabet": round(float((on.y > 0).mean()), 3), "en_iyi5_haric": round(float(on.y.sort_values().iloc[:-5].mean()), 2), "enkotu": round(float(on.y.min()), 0)}
print("yıl (kapı açık):", res["yil_acik"]); print("havuz:", res["havuz_acik"])
(OUT / "tur3.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
