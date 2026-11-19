"""kural.py — KEŞİF'te aday kurallar (eşikler yalnız KEŞİF'ten, piyasa başına dondurulur). python kural.py kesif | test"""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parents[1]
D = pd.read_parquet(HERE / "results/islemler.parquet")
MARK = {"DUKA_NDX": "NDX", "MT5_NAS100": "NDX", "MT5_US500": "US500", "MT5_US30": "US30", "MT5_US2000": "US2000"}
D["piyasa"] = D.besleme.map(MARK)

def thresholds(K):
    th = {}
    for pz, g in K.groupby("piyasa"):
        th[pz] = {"son_saat_p80": float(g.son_saat.quantile(0.8)), "vix_p20": float(g.vix.quantile(0.2))}
    return th

def exit_value(r, cap):
    """XP çıkışı en geç `cap` gün: tutuş > cap ise cap. günün 16:00 değeri (g{cap}), finansman yaklaşık düşülür."""
    if r.tutus_gun <= cap or not np.isfinite(r.get(f"g{cap}", np.nan)):
        return r.net
    return r[f"g{cap}"] - 1.756 * cap * 1.4

def apply(z, th, rule):
    z = z.copy()
    keep = np.ones(len(z), bool)
    val = z.net.values.copy()
    if "V_saat" in rule:
        keep &= ~(z.son_saat.values > z.piyasa.map(lambda p: th[p]["son_saat_p80"]).values)
    if "V_vix" in rule:
        keep &= ~(z.vix.values < z.piyasa.map(lambda p: th[p]["vix_p20"]).values)
    if "V_olay" in rule:
        keep &= ~(z.olay.values == 1)
    if "V_opex" in rule:
        keep &= ~np.isin(z.opex_k.values, [0, 1, 2])
    for cap in (1, 2, 3):
        if f"T{cap}" in rule:
            val = np.array([exit_value(r, cap) for r in z.itertuples(index=False)._asdict() and [] or []]) if False else \
                  np.array([r.net if (r.tutus_gun <= cap or not np.isfinite(getattr(r, f"g{cap}"))) else getattr(r, f"g{cap}") - 1.756 * cap * 1.4 for r in z.itertuples()])
    if "S0930" in rule:  # ertesi 09:30'da ≤ −eşik ise çık
        s = 100.0
        val = np.where(np.isfinite(z.c0930.values) & (z.c0930.values <= -s) & (z.tutus_gun.values >= 1), z.c0930.values, val)
    if "S04" in rule:
        s = 75.0
        val = np.where(np.isfinite(z.c04.values) & (z.c04.values <= -s), z.c04.values, val)
    return val, keep

def metr(v, keep, d):
    w = np.where(keep, v, 0.0)
    eq = pd.Series(w, index=pd.to_datetime(d)).sort_index().cumsum()
    vv = v[keep]
    return {"islem": int(keep.sum()), "toplam": round(float(w.sum()), 0), "brut_zarar": round(float(vv[vv < 0].sum()), 0),
            "isabet_%": round(float((vv > 0).mean() * 100), 1), "ort": round(float(vv.mean()), 1),
            "en_kotu": round(float(vv.min()), 1), "kotu10": round(float(np.sort(vv)[:max(1, len(vv) // 10)].mean()), 1),
            "maksDD": round(float((eq - eq.cummax()).min()), 0)}

RULES = ["TABAN", "T1", "T2", "T3", "S0930", "S04", "V_saat", "V_vix", "V_olay", "V_opex", "V_saat+V_vix", "V_saat+V_olay", "V_saat+V_vix+V_olay",
         "V_saat+T2", "V_saat+V_vix+T2", "V_saat+V_vix+V_olay+T2", "V_saat+V_vix+V_olay+V_opex+T2", "V_saat+V_vix+V_olay+V_opex+T3",
         "V_saat+V_vix+V_olay+V_opex", "V_opex+T2", "V_saat+V_opex+T2", "V_saat+V_vix+V_opex+T2", "V_saat+V_vix+V_opex"]

def table(Z, th, feeds):
    res = {}
    for f in feeds:
        z = Z[Z.besleme == f]
        base = None
        rec = {}
        for r in RULES:
            v, k = apply(z, th, r)
            m = metr(v, k, z.d.values)
            if r == "TABAN":
                base = m
            m["kar_orani"] = round(m["toplam"] / base["toplam"], 2)
            m["zarar_orani"] = round(m["brut_zarar"] / base["brut_zarar"], 2)
            m["kotu10_orani"] = round(m["kotu10"] / base["kotu10"], 2)
            m["DD_orani"] = round(m["maksDD"] / base["maksDD"], 2) if base["maksDD"] else None
            rec[r] = m
        res[f] = rec
    return res

if __name__ == "__main__":
    mode = sys.argv[1]
    K = D[D.donem == "KESIF"]
    th = thresholds(K[K.besleme.isin(["DUKA_NDX", "MT5_US500", "MT5_US30", "MT5_US2000"])])
    (HERE / "results/esikler_kesif.json").write_text(json.dumps(th, indent=1))
    Z = K if mode == "kesif" else D[D.donem == "TEST"]
    feeds = ["DUKA_NDX", "MT5_NAS100", "MT5_US500", "MT5_US30", "MT5_US2000"]
    res = table(Z, th, feeds)
    (HERE / f"results/kural_{mode}.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    print("eşikler:", th)
    for f in feeds:
        print(f"\n== {f} ({mode})")
        for r, m in res[f].items():
            print(f"  {r:34s} n {m['islem']:3d} kâr× {m['kar_orani']:5.2f} zarar× {m['zarar_orani']:5.2f} kötü10× {m['kotu10_orani']:5.2f} DD× {m['DD_orani']} | isabet {m['isabet_%']} ort {m['ort']} en kötü {m['en_kotu']}")
