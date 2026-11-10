"""Tur 2: sıkışma günü (yükseliş + yüksek hacim) ertesi gün. Ön kayıt: PROTOCOL.md EK-1."""
import json
import numpy as np, pandas as pd, yfinance as yf
from scipy.stats import spearmanr
from ortak import tablo, ay_blok, OUT, D
def hazirla(t):
    t = t.copy(); t["vr"] = t.vol / t.vol.shift(1).rolling(60).median(); t["sma50"] = t.ac.rolling(50).mean(); t["y"] = t.y_gun
    t["S1"] = (t.r > 0) & (t.vr >= 1.5); return t
PER = [("KESIF", "2001-03-01", "2011-01-01"), ("TEST", "2011-01-01", "2018-05-01"), ("KOR", "2018-05-01", "2026-11-10")]
def ozet(v: pd.Series) -> dict:
    if len(v) < 5: return {"n": int(len(v))}
    b = ay_blok(v.index, lambda ix: v.to_numpy()[ix].mean())
    return {"n": int(len(v)), "ort": round(float(v.mean()), 1), "med": round(float(v.median()), 1), "isabet_eksi": round(float((v < 0).mean()), 3), "P_ort<0": round(float((b < 0).mean()), 3), "ss": round(float(v.std()), 0)}
t = hazirla(tablo()); res = {"S1": {}, "O1": {}, "O2": {}}
ana = t[(t.index >= "2001-03-01") & t.y.notna() & t.vr.notna()]
for nm, a, b in PER:
    seg = ana[(ana.index >= a) & (ana.index < b)]; s1 = seg[seg.S1]; up = seg[seg.r > 0]
    res["S1"][nm] = ozet(s1.y)
    alt, ust = s1[s1.ac < s1.sma50].y, s1[s1.ac >= s1.sma50].y
    res["O1"][nm] = {"alt_sma50": ozet(alt), "ust_sma50": ozet(ust), "fark": round(float(alt.mean() - ust.mean()), 1) if len(alt) and len(ust) else None}
    rho, p = spearmanr(up.vr, up.y); res["O2"][nm] = {"n_yukselis": int(len(up)), "rho": round(float(rho), 4), "p": round(float(p), 4)}
    print(nm, "S1", res["S1"][nm], "| Ö1", res["O1"][nm]["alt_sma50"].get("ort"), res["O1"][nm]["ust_sma50"].get("ort"), "n", len(alt), len(ust), "| Ö2", res["O2"][nm])
s1 = ana[ana.S1]; up = ana[ana.r > 0]
alt = (s1.ac < s1.sma50).to_numpy(); Y = s1.y.to_numpy()
bo = ay_blok(s1.index, lambda ix: Y[ix][alt[ix]].mean() - Y[ix][~alt[ix]].mean() if alt[ix].any() and (~alt[ix]).any() else np.nan)
rho, p = spearmanr(up.vr, up.y); big = s1[s1.r >= 0.01].y; small = s1[s1.r < 0.01].y
yr = s1.groupby(s1.index.year).y.agg(["size", "mean"]); yr3 = yr[yr["size"] >= 3]
res["havuz"] = {"S1": ozet(s1.y), "O1_fark": round(float(Y[alt].mean() - Y[~alt].mean()), 1), "O1_P_fark<0": round(float(np.nanmean(bo < 0)), 3), "O2_rho": round(float(rho), 4), "O2_p": round(float(p), 4),
                "r>=1%": ozet(big), "r<1%": ozet(small), "en_eksi5_haric_ort": round(float(s1.y.sort_values().iloc[5:].mean()), 1), "en_arti5_haric_ort": round(float(s1.y.sort_values().iloc[:-5].mean()), 1),
                "yil_eksi_orani": round(float((yr3["mean"] < 0).mean()), 2), "yil": {int(k): [int(v["size"]), round(float(v["mean"]), 0)] for k, v in yr.iterrows()},
                "yukselis_normal_hacim": ozet(up[up.vr < 1.5].y), "sonraki_gece": ozet(s1.y_gece.dropna())}
print("HAVUZ", json.dumps(res["havuz"], ensure_ascii=False))
old = t[(t.index >= "1999-06-01") & (t.index < "2001-03-01") & t.S1 & t.y.notna()]; res["eski_1999_2001"] = ozet(old.y); print("eski", res["eski_1999_2001"])
for tk in ("SPY", "IWM"):
    f = D / f"{tk}.parquet"
    if not f.exists():
        x = yf.Ticker(tk).history(start="1999-01-01", end="2026-11-10", auto_adjust=False); x.index = pd.DatetimeIndex(x.index).tz_localize(None).normalize(); x.to_parquet(f)
    x = pd.read_parquet(f); k = pd.DataFrame({"r": np.log(x["Adj Close"] / x["Adj Close"].shift(1)), "vr": x.Volume / x.Volume.shift(1).rolling(60).median(), "y": (x.Close.shift(-1) / x.Open.shift(-1) - 1) * 1e4})
    k = k[(k.index >= "2001-03-01")].dropna(); s = k[(k.r > 0) & (k.vr >= 1.5)]; res[tk] = {"hepsi": ozet(s.y), **{nm: ozet(s[(s.index >= a) & (s.index < b)].y) for nm, a, b in PER}}; print(tk, res[tk])
(OUT / "tur2.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
