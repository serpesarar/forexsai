"""ek_kapilar.py — sohbetin ilk yarısındaki onaylanabilir kapılar aynı düzenekte: K3, geniş fitilli KSG, referans fitilli KSG,
K1 × ters VIX eğrisi dozu, K1 × C3b dozu; + Avrupa taşıması (na.py yeniden koşu). python ek_kapilar.py"""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
import rapor as R
G, V = R.G, R.V
NY = R.NY
sys.path.insert(0, str(R.ROOT / "research/fitil_gece_20261118/src"))
import gece as GC  # noqa: E402

def vix_ratio():
    v = pd.read_parquet(R.ROOT / "research/qs03_akis_takvim_20261111/data/VIX.parquet")
    if isinstance(v.columns, pd.MultiIndex): v.columns = v.columns.get_level_values(0)
    v.index = pd.to_datetime(v.index).tz_localize(None).normalize()
    w = pd.read_parquet(R.ROOT / "research/son_rapor_20261118/VIX3M.parquet"); w.index = pd.to_datetime(w.index).tz_localize(None).normalize()
    r = (v.Close / w.Close.reindex(v.index)).dropna()
    return r.shift(1)  # d−1 kapanışı: d 16:00'da bilinir

def rsi2(s):
    d = s.diff(); up, dn = d.clip(lower=0), (-d).clip(lower=0)
    rs = up.ewm(alpha=0.5, adjust=False).mean() / dn.ewm(alpha=0.5, adjust=False).mean()
    return 100 - 100 / (1 + rs)

def dose(t, m, col="gece"):
    a, b = t[col].values[m], t[col].values[~m]
    if len(a) < 5: return {"n": int(len(a))}
    return {"n_doz": int(len(a)), "doz_ort": round(float(a.mean()), 1), "diger_ort": round(float(b.mean()), 1),
            "P_doz_iyi": round(1 - R.gate_p(t[col].values, m, 9), 4)}

def feed(b, st):
    out = {}
    dp = G.day_prices(b, NY, [570, 900, 930, 960], st)
    t = R.k1_table(b, st)
    # K3: 15:00→16:00 ≤ −%0,3
    k3 = []
    for d, g in zip(t.d, t.gece):
        r = dp.loc[d.date()] if d.date() in dp.index else None
        k3.append(bool(r is not None and np.isfinite(r.o900) and r.o960 / r.o900 - 1 <= -0.003))
    t["K3"] = k3
    one = lambda n: np.ones(n)
    k3t = t[t.K3].reset_index(drop=True)
    out["K3_son_saat"] = R.metrics(k3t.d, k3t.gece.values, one(len(k3t)))
    # fitilli KSG: geniş (2h, %0,5, 12 sa, 15:30→ertesi 16:00) ve referans (1h, %0,5, 6 sa, 16:00→09:30)
    for nm, (sec, w, en, ex) in {"fitilli_KSG_genis": (7200, 12 * 3600, 930, 960), "fitilli_KSG_referans": (3600, 6 * 3600, 960, 570)}.items():
        ends = GC.wick_ends(b, NY, sec, 0.50, st)
        nts = GC.nights(dp, en, ex, 900, GC.nyse_ok)
        m = GC.tag(nts.t_in.values, ends, w) & (nts.ksg_ret < 0).values
        z = nts[m].reset_index(drop=True); z["d"] = pd.to_datetime(z.d)
        out[nm] = R.metrics(z.d, z.net_bp.values, one(len(z)))
        out[nm + "_taban_ort"] = round(float(nts[~m].net_bp.mean()), 1)
    # K1 dozları
    kk = t[t.K1].reset_index(drop=True)
    vr = vix_ratio()
    inv = (vr.reindex(kk.d).values >= 1.0)
    out["K1_x_ters_VIX_egrisi_doz"] = dose(kk, np.nan_to_num(inv, nan=0).astype(bool) & (kk.d >= "2007-01-01").values)
    p16 = pd.Series(dp.o960.values, index=pd.to_datetime(dp.index)).dropna()
    r2 = rsi2(p16)
    out["K1_x_C3b_ayni_gun_doz"] = dose(kk, (r2.reindex(kk.d).values < 10))
    return out

def main():
    feeds = {"DUKA_NDX": (G.ndx_bars(), 60), "MT5_NAS100": (R.KD.mt5_m30("NAS100"), 1800), "MT5_US500": (R.KD.mt5_m30("US500", "2018-06-01"), 1800),
             "MT5_US30": (R.KD.mt5_m30("US30"), 1800), "MT5_US2000": (R.KD.mt5_m30("US2000"), 1800)}
    res = {nm: feed(b, st) for nm, (b, st) in feeds.items()}
    sys.path.insert(0, str(R.ROOT / "research/ndx_korku_avrupa_20261118/src"))
    import na  # noqa: E402
    na.main()
    res["Avrupa_tasima_na_py"] = json.loads((R.ROOT / "research/ndx_korku_avrupa_20261118/results").joinpath(
        sorted(p.name for p in (R.ROOT / "research/ndx_korku_avrupa_20261118/results").glob("*.json"))[0]).read_text())
    d = json.load(open(R.RES / "son_rapor.json")); d["ek_kapilar"] = res
    json.dump(d, open(R.RES / "son_rapor.json", "w"), ensure_ascii=False, indent=1, default=str)
    keys = ["islem", "yilda", "isabet_%", "ort_bp", "en_kotu_bp", "en_kotu_%10_ort_bp", "maks_dusus_bp", "arti_yil"]
    for f, r in res.items():
        print("==", f)
        for k, v in r.items():
            print(f"  {k:28s}", [v.get(x) for x in keys] if isinstance(v, dict) and "islem" in v else v)

if __name__ == "__main__": main()
