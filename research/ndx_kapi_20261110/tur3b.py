"""Tur 3 broker aşaması (ön kayıtta 'raporlanır'): NAS100 gece primi, G-IBS ve G-SON. PROTOCOL.md EK-2."""
import json
import numpy as np, pandas as pd
from ortak import ld, ay_blok, OUT
from broker import gun_tablosu
t = gun_tablosu("NAS100"); vix = ld("VIX").Close; t["vixp"] = vix.shift(1).reindex(t.index, method="ffill"); t = t.dropna(subset=["y_net", "r", "vixp"])
def oz(x, col="y_net"):
    v = x[col]
    if len(v) < 8: return {"n": int(len(v))}
    b = ay_blok(v.index, lambda ix: v.to_numpy()[ix].mean()); h = len(v) // 2
    return {"n": int(len(v)), "brut": round(float(x.y_brut.mean()), 1), "net": round(float(v.mean()), 1), "med": round(float(v.median()), 1), "isabet": round(float((v > 0).mean()), 3), "P_net>0": round(float((b > 0).mean()), 3),
            "yari": [round(float(v.iloc[:h].mean()), 1), round(float(v.iloc[h:].mean()), 1)], "ss": round(float(v.std()), 0), "enkotu": round(float(v.min()), 0), "eniyi5haric": round(float(v.sort_values().iloc[:-5].mean()), 1)}
print("dönem", t.index[0].date(), t.index[-1].date(), "gün", len(t), "ort maliyet", round(float(t.maliyet.mean()), 2))
T = t[(t.r < 0) & (t.vixp >= 18.4)]; res = {"tum_geceler": oz(t), "taban_T": oz(T)}
hucre = {"T ∧ IBS<0,2": T[T.ibs < .2], "T ∧ IBS≥0,2": T[T.ibs >= .2], "T ∧ son saat<0": T[T.son_saat < 0], "T ∧ son saat≥0": T[T.son_saat >= 0], "T ∧ IBS<0,2 ∧ son saat<0": T[(T.ibs < .2) & (T.son_saat < 0)],
         "düşüş ∧ VIX<18,4": t[(t.r < 0) & (t.vixp < 18.4)], "yükseliş ∧ VIX≥18,4": t[(t.r > 0) & (t.vixp >= 18.4)], "yükseliş ∧ VIX<18,4": t[(t.r > 0) & (t.vixp < 18.4)],
         "tüm ∧ son saat<0": t[t.son_saat < 0], "tüm ∧ son saat≥0": t[t.son_saat >= 0], "VIX≥18,4 ∧ son saat<0": t[(t.vixp >= 18.4) & (t.son_saat < 0)], "VIX≥18,4 ∧ son saat≥0": t[(t.vixp >= 18.4) & (t.son_saat >= 0)]}
for k, x in hucre.items(): res[k] = oz(x); print(f"{k:28s}", res[k])
print("taban", res["taban_T"]); print("tüm", res["tum_geceler"])
res["yil_T"] = {int(y): [int(len(x)), round(float(x.y_net.mean()), 1), round(float(x.y_gunduz.mean()), 1)] for y, x in T.groupby(T.index.year)}; print("yıl taban [n, gece net, ertesi gündüz]:", res["yil_T"])
(OUT / "tur3b.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
