"""Tur 6 sağlamlık. Ön kayıt: PROTOCOL.md EK-6."""
import json
from pathlib import Path
import numpy as np, pandas as pd
from ortak import ld, ay_blok, OUT
from broker import gun_tablosu
ROOT = Path(__file__).resolve().parents[2]; res = {}
def P(v):
    v = v.dropna(); a = v.to_numpy(); return round(float((ay_blok(v.index, lambda ix: a[ix].mean()) > 0).mean()), 3)
dk = pd.read_parquet(ROOT / "research/tp_sonrasi_ters_20261109/data/duka_1m.parquet"); et = dk.index.tz_convert("America/New_York").tz_localize(None); dk = dk.assign(d=et.normalize(), m=et.hour * 60 + et.minute); dk = dk[et.dayofweek < 5]
od = lambda mm: dk[dk.m == mm].drop_duplicates("d").set_index("d").open
f = pd.DataFrame({"o15": od(900), "o1555": od(955), "o16": od(960), "o1601": od(961), "o1605": od(965), "o1614": od(974), "o930": od(570)}).dropna(subset=["o15", "o16", "o930"])
gp = (pd.Series(f.index, index=f.index).shift(-1) - pd.Series(f.index, index=f.index)).dt.days; f["n"] = gp.clip(upper=3); f["ex"] = f.o930.shift(-1); f = f[gp <= 4].dropna(subset=["ex"])
sig = f.o16 / f.o15 - 1 < 0; net = lambda e: ((f.ex / (e + 1.5) - 1) * 1e4 - 1.8 * f.n)
s1 = {}
for nm, col in (("16:00", "o16"), ("16:01", "o1601"), ("16:05", "o1605"), ("16:14", "o1614")):
    v = net(f[col])[sig].dropna(); s1[nm] = {"n": int(len(v)), "net": round(float(v.mean()), 2), "P": P(v)}
res["S1"] = s1; print("S1", s1)
sig2 = f.o1555 / f.o15 - 1 < 0; v = net(f.o16)[sig2].dropna(); res["S2"] = {"n": int(len(v)), "net": round(float(v.mean()), 2), "P": P(v), "uyum": round(float((sig2 == sig).mean()), 3)}; print("S2", res["S2"])
t = gun_tablosu("NAS100"); vix = ld("VIX").Close; t["vixp"] = vix.shift(1).reindex(t.index, method="ffill"); t = t.dropna(subset=["y_net", "son_saat"])
q = pd.qcut(t.son_saat, 5, labels=False); res["S3"] = {int(k): [round(float(x.son_saat.mean()), 1), round(float(x.y_brut.mean()), 1), int(len(x))] for k, x in t.groupby(q)}; print("S3 dilim [son saat bp, gece brüt bp, n]", res["S3"])
K = t[t.son_saat < 0]
res["S4_gun"] = {["Pzt", "Sal", "Çrş", "Prş", "Cum"][int(k)]: [int(len(x)), round(float(x.y_net.mean()), 1), round(float(x.y_brut.mean()), 1)] for k, x in K.groupby(K.index.dayofweek)}; print("S4 gün [n, net, brüt]", res["S4_gun"])
vb = pd.cut(K.vixp, [0, 15, 18.4, 25, 100]); res["S4_vix"] = {str(k): [int(len(x)), round(float(x.y_net.mean()), 1)] for k, x in K.groupby(vb, observed=True)}; print("S4 VIX [n, net]", res["S4_vix"])
S = (t.son_saat < 0).to_numpy(); Y = t.y_brut.to_numpy(); d = Y[S].mean() - Y[~S].mean(); rng = np.random.default_rng(29); pm = np.array([(lambda s: Y[s].mean() - Y[~s].mean())(np.roll(S, int(rng.integers(20, len(S) - 20)))) for _ in range(10000)])
res["S4_perm_p"] = round(float((pm >= d).mean()), 5); print("S4 dairesel kaydırma p", res["S4_perm_p"], "Δ", round(float(d), 2))
for nm, x in (("2018-05→2019-12", K[K.index < "2020-01-01"]), ("2020-01→2026-11", K[K.index >= "2020-01-01"])):
    o = t[(t.son_saat >= 0) & (t.index >= x.index.min()) & (t.index <= x.index.max())]
    res["S5_" + nm] = {"n": int(len(x)), "net": round(float(x.y_net.mean()), 2), "P": P(x.y_net), "delta_brut": round(float(x.y_brut.mean() - o.y_brut.mean()), 2)}; print("S5", nm, res["S5_" + nm])
(OUT / "tur6b.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
