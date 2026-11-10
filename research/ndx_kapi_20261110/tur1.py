"""Tur 1: düşüş günü sonrası uzun tabanına K-A / K-B / K-C kapıları. Ön kayıt: PROTOCOL.md."""
import json
import numpy as np, pandas as pd
from ortak import tablo, korku_asimi, degerlendir, OUT
t = tablo()
t["kA"] = korku_asimi(t, "vxn") > 0; t.loc[korku_asimi(t, "vxn").isna(), "kA"] = np.nan
vr = t.vol / t.vol.shift(1).rolling(60).median(); t["kB"] = (vr >= 1.5).where(vr.notna())
dq = t.r_qqew - t.r; t["kC"] = (dq < 0).where(dq.notna())
t["kREF"] = (t.vix >= 18.4).where(t.vix.notna()); t["y"] = t.y_gun
# önek testi: son 500 günü silince önceki kapı değerleri değişmemeli
t2 = tablo().iloc[:-500]; a2 = korku_asimi(t2, "vxn") > 0; assert (a2.iloc[300:] == (korku_asimi(t, "vxn") > 0).reindex(a2.index).iloc[300:]).all()
PER = {"kA": [("KESIF", "2001-03-01", "2011-01-01"), ("TEST", "2011-01-01", "2018-05-01"), ("KOR", "2018-05-01", "2026-11-10")]}
PER["kB"] = PER["kA"]; PER["kREF"] = PER["kA"]; PER["kC"] = [("KESIF", "2006-06-01", "2013-01-01"), ("TEST", "2013-01-01", "2018-05-01"), ("KOR", "2018-05-01", "2026-11-10")]
res = {}
for g, pers in PER.items():
    res[g] = {}
    for nm, a, b in pers:
        seg = t[(t.index >= a) & (t.index < b)]; dn = seg[seg.r < 0]; up = seg[seg.r > 0]
        res[g][nm] = degerlendir(dn, g); res[g][nm + "_plasebo_yukselis"] = {k: v for k, v in degerlendir(up, g).items() if k in ("n", "n_acik", "ort_acik", "ort_kapali", "delta", "p_perm")}
        if nm == "KOR" and g != "kREF":
            for lab, m in (("vix_yuksek", dn.vix >= 18.4), ("vix_dusuk", dn.vix < 18.4)):
                res[g][nm + "_" + lab] = {k: v for k, v in degerlendir(dn[m], g).items() if k in ("n", "n_acik", "ort_acik", "ort_kapali", "delta", "P_delta>0")}
        print(g, nm, res[g][nm])
    for k in list(res[g]):
        if "plasebo" in k or "vix_" in k: print("   ", k, res[g][k])
ps = sorted(((res[g]["KESIF"]["p_perm"], g) for g in ("kA", "kB", "kC")))
res["holm"] = {g: round(min(1.0, p * (3 - i)), 4) for i, (p, g) in enumerate(ps)}; print("Holm (KEŞİF):", res["holm"])
(OUT / "tur1.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
