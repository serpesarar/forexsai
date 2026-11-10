"""Tur 5: ayı rallisi vetosu — ORB × VIX işlemleri + günlük 27 yıl. Ön kayıt: PROTOCOL.md EK-4."""
import json
from pathlib import Path
import numpy as np, pandas as pd
from ortak import ld, tablo, ay_blok, OUT
T = pd.read_csv(Path(__file__).resolve().parents[1] / "haber_derin_20261105/results_havuz_10yil.csv"); T["d"] = pd.to_datetime(T.d).dt.tz_localize(None).dt.normalize()
nd = ld("NDX").Close; up = (nd > nd.shift(1)); alt = nd < nd.rolling(50).mean()
T["up"] = up.shift(1).reindex(T.d).to_numpy(); T["alt"] = alt.shift(1).reindex(T.d).to_numpy(); T = T.dropna(subset=["up", "alt"]).sort_values("d").reset_index(drop=True)
T["v"] = T.up.astype(bool) & T.alt.astype(bool); T["y"] = T.d.dt.year
def sr_m(x, lo, hi):
    m = x.set_index("d").R.resample("ME").sum().reindex(pd.date_range(lo, hi, freq="ME")).fillna(0); return m
def kiyas(x):
    V, R = x.v.to_numpy(), x.R.to_numpy(); xi = x.set_index("d")
    if V.sum() < 8: return {"n": int(len(x)), "n_veto": int(V.sum())}
    d = float(R[~V].mean() - R[V].mean()); b = ay_blok(xi.index, lambda ix: R[ix][~V[ix]].mean() - R[ix][V[ix]].mean() if V[ix].any() and (~V[ix]).any() else np.nan)
    bv = ay_blok(xi.index, lambda ix: R[ix][V[ix]].mean() if V[ix].any() else np.nan)
    rng = np.random.default_rng(17); n = len(R); pm = np.array([(lambda s: R[~s].mean() - R[s].mean())(np.roll(V, int(rng.integers(10, n - 10)))) for _ in range(5000)])
    return {"n": int(n), "n_veto": int(V.sum()), "R_veto": round(float(R[V].mean()), 3), "R_kalan": round(float(R[~V].mean()), 3), "delta": round(d, 3), "P_delta>0": round(float(np.nanmean(b > 0)), 3), "p_perm": round(float((pm >= d).mean()), 4),
            "P_Rveto<=0": round(float(np.nanmean(bv <= 0)), 3), "isabet_veto": round(float((R[V] > 0).mean()), 3), "toplamR_veto": round(float(R[V].sum()), 1), "toplamR_kalan": round(float(R[~V].sum()), 1)}
C = T[T.vix >= 18.4].reset_index(drop=True); L = T[T.vix < 18.4].reset_index(drop=True); res = {"A_havuz": kiyas(C)}; print("A HAVUZ", res["A_havuz"])
for tf in ("1h", "30m", "5m"): res["A_" + tf] = kiyas(C[C.tf == tf].reset_index(drop=True)); print(" ", tf, res["A_" + tf])
yr = {int(y): [int(x.v.sum()), round(float(x[x.v].R.mean()), 3) if x.v.any() else None, int((~x.v).sum()), round(float(x[~x.v].R.mean()), 3)] for y, x in C.groupby("y")}
ok = [v[1] < v[3] for v in yr.values() if v[0] >= 8]; res["A_yil"] = yr; res["A_yil_veto_kotu"] = [int(sum(ok)), len(ok)]; print("  yıl [n_veto, R, n_kalan, R]:", yr, res["A_yil_veto_kotu"])
lo, hi = T.d.min(), T.d.max(); m0, m1 = sr_m(C, lo, hi), sr_m(C[~C.v], lo, hi); sr = lambda m: float(m.mean() / m.std() * np.sqrt(12))
rng = np.random.default_rng(19); k = len(m0); bs = [(lambda ix: sr(m1.iloc[ix]) - sr(m0.iloc[ix]))(rng.integers(0, k, k)) for _ in range(4000)]
res["A_portfoy"] = {"toplamR_once": round(float(C.R.sum()), 1), "toplamR_sonra": round(float(C[~C.v].R.sum()), 1), "SR_once": round(sr(m0), 2), "SR_sonra": round(sr(m1), 2), "P_SR_artis": round(float(np.mean(np.array(bs) > 0)), 3)}; print("  portföy", res["A_portfoy"])
res["A_plasebo_dusukVIX"] = kiyas(L); print("  plasebo VIX<18,4", res["A_plasebo_dusukVIX"])
# dün düşüş kolu ayrıca (bilgi): veto dışı kalanın bileşimi
res["A_kollar"] = {k_: [int(len(x)), round(float(x.R.mean()), 3)] for k_, x in {"dun_dusus": C[~C.up.astype(bool)], "dun_yukselis_SMA50_ustu": C[C.up.astype(bool) & ~C.alt.astype(bool)], "dun_yukselis_SMA50_alti": C[C.v]}.items()}; print("  kollar", res["A_kollar"])
# B: günlük 27 yıl
t = tablo(); t["sma50"] = t.ac.rolling(50).mean(); t["vixp"] = t.vix.shift(1); t["y"] = t.y_gun; B = {}
for nm, a, b in [("KESIF", "2001-03-01", "2011-01-01"), ("TEST", "2011-01-01", "2018-05-01"), ("KOR", "2018-05-01", "2026-11-10")]:
    s = t[(t.index >= a) & (t.index < b) & (t.r > 0) & (t.vixp >= 18.4)].dropna(subset=["y", "sma50"]); lo_, hi_ = s[s.ac < s.sma50].y, s[s.ac >= s.sma50].y
    B[nm] = {"n_alt": int(len(lo_)), "ort_alt": round(float(lo_.mean()), 1), "med_alt": round(float(lo_.median()), 1), "n_ust": int(len(hi_)), "ort_ust": round(float(hi_.mean()), 1), "fark": round(float(lo_.mean() - hi_.mean()), 1)}; print("B", nm, B[nm])
s = t[(t.index >= "2001-03-01") & (t.r > 0) & (t.vixp >= 18.4)].dropna(subset=["y", "sma50"]); A_ = (s.ac < s.sma50).to_numpy(); Y = s.y.to_numpy()
bb = ay_blok(s.index, lambda ix: Y[ix][A_[ix]].mean() - Y[ix][~A_[ix]].mean() if A_[ix].any() and (~A_[ix]).any() else np.nan)
B["havuz"] = {"n_alt": int(A_.sum()), "ort_alt": round(float(Y[A_].mean()), 1), "ort_ust": round(float(Y[~A_].mean()), 1), "P_fark<0": round(float(np.nanmean(bb < 0)), 3)}; print("B havuz", B["havuz"]); res["B"] = B
h = res["A_havuz"]
res["olcut"] = {"A1": bool(h["R_veto"] <= 0), "A2": bool(h["P_delta>0"] >= .95 and h["p_perm"] <= .05), "A3": bool(all(res["A_" + tf].get("delta", -1) > 0 for tf in ("1h", "30m", "5m"))), "A4": bool(len(ok) > 0 and sum(ok) / len(ok) >= .7),
                "A5": bool(res["A_portfoy"]["toplamR_sonra"] >= res["A_portfoy"]["toplamR_once"] and res["A_portfoy"]["P_SR_artis"] >= .9), "A6": bool(h["n_veto"] >= 60),
                "B": bool(all(B[k]["ort_alt"] <= 0 and B[k]["fark"] < 0 for k in ("KESIF", "TEST", "KOR")) and B["havuz"]["P_fark<0"] >= .95)}
print(res["olcut"]); (OUT / "tur5.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
