"""Tur 4: ORB × VIX işlemlerine 'dün düşüş' kapısı. Ön kayıt: PROTOCOL.md EK-3."""
import json
from pathlib import Path
import numpy as np, pandas as pd
from ortak import ld, ay_blok, OUT
T = pd.read_csv(Path(__file__).resolve().parents[1] / "haber_derin_20261105/results_havuz_10yil.csv"); T["d"] = pd.to_datetime(T.d).dt.tz_localize(None).dt.normalize()
nd = ld("NDX").Close; dn = (nd < nd.shift(1)).shift(1)          # d−1 düşüş mü (d'ye hizalı)
T["g"] = dn.reindex(T.d).to_numpy(); T = T.dropna(subset=["g"]).sort_values("d").reset_index(drop=True); T["g"] = T.g.astype(bool); T["y"] = T.d.dt.year
def kiyas(x: pd.DataFrame, perm=True) -> dict:
    G, R = x.g.to_numpy(), x.R.to_numpy(); x = x.set_index("d")
    if G.sum() < 10 or (~G).sum() < 10: return {"n": int(len(x))}
    d = float(R[G].mean() - R[~G].mean()); b = ay_blok(x.index, lambda ix: R[ix][G[ix]].mean() - R[ix][~G[ix]].mean() if G[ix].any() and (~G[ix]).any() else np.nan)
    o = {"n": int(len(x)), "n_acik": int(G.sum()), "R_acik": round(float(R[G].mean()), 3), "R_kapali": round(float(R[~G].mean()), 3), "delta": round(d, 3), "P_delta>0": round(float(np.nanmean(b > 0)), 3),
         "isabet_acik": round(float((R[G] > 0).mean()), 3), "isabet_kapali": round(float((R[~G] > 0).mean()), 3), "toplamR_acik": round(float(R[G].sum()), 1), "toplamR_kapali": round(float(R[~G].sum()), 1)}
    if perm:
        rng = np.random.default_rng(13); n = len(R); pm = np.array([(lambda s: R[s].mean() - R[~s].mean())(np.roll(G, int(rng.integers(10, n - 10)))) for _ in range(5000)]); o["p_perm"] = round(float((pm >= d).mean()), 4)
    return o
C = T[T.vix >= 18.4]; L = T[T.vix < 18.4]; res = {"havuz_C1": kiyas(C)}
print("HAVUZ C1", res["havuz_C1"])
for tf in ("1h", "30m", "5m"):
    res["C1_" + tf] = kiyas(C[C.tf == tf], perm=False); print(tf, res["C1_" + tf])
yr = {}
for y, x in C.groupby("y"):
    a, b = x[x.g].R, x[~x.g].R
    yr[int(y)] = [int(len(a)), round(float(a.mean()), 3) if len(a) else None, int(len(b)), round(float(b.mean()), 3) if len(b) else None]
res["yil"] = yr; ok = [(v[1] - v[3]) > 0 for v in yr.values() if v[0] >= 10 and v[2] >= 10]; res["yil_delta_arti"] = [int(sum(ok)), len(ok)]; print("yıl [n_açık, R, n_kapalı, R]:", yr, "| Δ>0:", res["yil_delta_arti"])
res["plasebo_dusukVIX"] = kiyas(L); print("PLASEBO VIX<18,4", res["plasebo_dusukVIX"])
def aylik_sr(x):
    m = x.set_index("d").R.resample("ME").sum(); m = m.reindex(pd.date_range(T.d.min(), T.d.max(), freq="ME")).fillna(0); return round(float(m.mean() / m.std() * np.sqrt(12)), 2)
res["aylik_SR"] = {"C1": aylik_sr(C), "C1_kapili": aylik_sr(C[C.g]), "C1_kapali_kol": aylik_sr(C[~C.g])}; print("aylık SR", res["aylik_SR"])
h = res["havuz_C1"]
res["olcut"] = {"1_uc_sette": bool(all(res["C1_" + tf].get("delta", -1) > 0 for tf in ("1h", "30m", "5m"))), "2_P_ve_perm": bool(h["P_delta>0"] >= .95 and h["p_perm"] <= .05),
                "3_toplanma": bool(h["R_kapali"] <= .05 and h["R_acik"] >= .25), "4_yil": bool(sum(ok) >= 7), "5_plasebo": bool(res["plasebo_dusukVIX"]["P_delta>0"] < .90)}
print(res["olcut"]); (OUT / "tur4.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
