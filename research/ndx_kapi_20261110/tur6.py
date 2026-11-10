"""Tur 6: Kapanış saati gecesi (KSG). Ön kayıt: PROTOCOL.md EK-5."""
import json
from pathlib import Path
import numpy as np, pandas as pd
from ortak import ld, ay_blok, OUT
from broker import gun_tablosu, MT5, meta
ROOT = Path(__file__).resolve().parents[2]; res = {}
def P(v, f=lambda a: a.mean() > 0):
    v = v.dropna(); a = v.to_numpy(); b = ay_blok(v.index, lambda ix: a[ix].mean()); return round(float((b > 0).mean()), 3)
def dP(x, sig, col):
    x = x.dropna(subset=[sig, col]); S = (x[sig] < 0).to_numpy(); Y = x[col].to_numpy(); b = ay_blok(x.index, lambda ix: Y[ix][S[ix]].mean() - Y[ix][~S[ix]].mean() if S[ix].any() and (~S[ix]).any() else np.nan)
    return round(float(Y[S].mean() - Y[~S].mean()), 2), round(float(np.nanmean(b > 0)), 3)
t = gun_tablosu("NAS100"); vix = ld("VIX").Close; t["vixp"] = vix.shift(1).reindex(t.index, method="ffill"); t = t.dropna(subset=["y_net", "son_saat"]); K = t[t.son_saat < 0]
# D1
yr = {}
for y, x in t.groupby(t.index.year):
    a, b = x[x.son_saat < 0], x[x.son_saat >= 0]; yr[int(y)] = [int(len(a)), round(float(a.y_net.mean()), 1), round(float(a.y_brut.mean() - b.y_brut.mean()), 1)]
res["D1"] = {"yil[n,net,delta_brut]": yr, "net>0": int(sum(v[1] > 0 for v in yr.values())), "delta>0": int(sum(v[2] > 0 for v in yr.values())), "yil": len(yr)}; print("D1", res["D1"])
# D2: saat pencereleri (ham barlardan)
x = pd.read_csv(MT5 / "NAS100_M30.csv.gz"); x["et"] = pd.to_datetime(x.t, unit="s") - pd.Timedelta(hours=7); x["d"] = x.et.dt.normalize(); x["m"] = x.et.dt.hour * 60 + x.et.dt.minute
ob = lambda mm: x[x.m == mm].drop_duplicates("d").set_index("d").o.reindex(t.index)
d2 = {}
for h in range(10, 16):
    t[f"h{h}"] = (ob((h + 1) * 60) / ob(h * 60) - 1) * 1e4; d2[f"{h}→{h+1}"] = dP(t, f"h{h}", "y_brut")
d2["gun_yonu"] = dP(t.assign(rr=t.r), "rr", "y_brut"); d2["15→16 | düşüş günü"] = dP(t[t.r < 0], "son_saat", "y_brut"); d2["15→16 | yükseliş günü"] = dP(t[t.r > 0], "son_saat", "y_brut")
d2["15:30→16 (son yarım)"] = dP(t, "son_yarim", "y_brut"); res["D2"] = d2; print("D2 [Δ brüt, P(Δ>0)]", d2)
# D3: NDX 1h 2016-06 → 2018-05-14
z = np.load(ROOT / "backend/data/candle_history/NDX_1h.npz"); q = pd.DataFrame({k: z[k] for k in z.files}); q["ts"] = pd.to_datetime(q.ts.astype("int64"), unit="s", utc=True); q = q.sort_values("ts")
q["et"] = q.ts.dt.tz_convert("America/New_York").dt.tz_localize(None); q = q[(q.et < "2018-05-15") & (q.et.dt.dayofweek < 5)]; q["d"] = q.et.dt.normalize(); q["h"] = q.et.dt.hour
vol = ((q.high - q.low) / q.close).groupby([q.et.dt.to_period("M"), q.h]).mean(); res["D3_eksen"] = {int(k): int(v) for k, v in vol.groupby(level=0).idxmax().map(lambda k: k[1]).value_counts().items()}
b15 = q[q.h == 15].drop_duplicates("d").set_index("d"); o9 = q[q.h == 9].drop_duplicates("d").set_index("d").open
e = pd.DataFrame({"sig": (b15.close / b15.open - 1) * 1e4, "c16": b15.close}); e["o9n"] = o9.reindex(e.index).shift(-1); gap = (pd.Series(e.index, index=e.index).shift(-1) - pd.Series(e.index, index=e.index)).dt.days
e = e[gap <= 4].dropna(); e["y"] = (e.o9n / e.c16 - 1) * 1e4; ks = e[e.sig < 0]; dd, pp = dP(e, "sig", "y")
res["D3"] = {"donem": [str(e.index[0].date()), str(e.index[-1].date())], "gece": int(len(e)), "n_KSG": int(len(ks)), "KSG_brut": round(float(ks.y.mean()), 2), "KSG_net(−3,9)": round(float(ks.y.mean() - 3.9), 2), "diger_brut": round(float(e[e.sig >= 0].y.mean()), 2), "delta": dd, "P_delta>0": pp, "P_KSG_brut>0": P(ks.y)}
print("D3 eksen", res["D3_eksen"], res["D3"])
# D4: kör enstrümanlar
d4 = {}; ser = {}
for sym in ("US500", "US30", "US2000"):
    u = gun_tablosu(sym).dropna(subset=["y_net", "son_saat"]); k = u[u.son_saat < 0]; dd, pp = dP(u, "son_saat", "y_brut")
    d4[sym] = {"n": int(len(k)), "brut": round(float(k.y_brut.mean()), 1), "net": round(float(k.y_net.mean()), 1), "P_net>0": P(k.y_net), "delta": dd, "P_delta>0": pp, "maliyet": round(float(u.maliyet.mean()), 1)}; ser[sym] = u[["y_brut", "son_saat"]]; print("D4", sym, d4[sym])
j = pd.concat({s: v for s, v in ser.items()}, axis=1).dropna(); Yb = j.xs("y_brut", axis=1, level=1).mean(axis=1); Sg = j.xs("son_saat", axis=1, level=1).mean(axis=1); d4["ucu_ortalama"] = dP(pd.DataFrame({"s": Sg, "y": Yb}), "s", "y"); print("D4 üçü ort [Δ,P]", d4["ucu_ortalama"]); res["D4"] = d4
# D5: Dukascopy 1m
dk = pd.read_parquet(ROOT / "research/tp_sonrasi_ters_20261109/data/duka_1m.parquet"); et = dk.index.tz_convert("America/New_York").tz_localize(None); dk = dk.assign(d=et.normalize(), m=et.hour * 60 + et.minute); dk = dk[et.dayofweek < 5]
od = lambda mm: dk[dk.m == mm].drop_duplicates("d").set_index("d").open
f = pd.DataFrame({"o15": od(900), "o16": od(960), "o930": od(570)}).dropna(); gp = (pd.Series(f.index, index=f.index).shift(-1) - pd.Series(f.index, index=f.index)).dt.days
f["sig"] = (f.o16 / f.o15 - 1) * 1e4; f["y_brut"] = (f.o930.shift(-1) / f.o16 - 1) * 1e4; f["y_net"] = (f.o930.shift(-1) / (f.o16 + 1.5) - 1) * 1e4 - 1.8 * gp.clip(upper=3); f = f[gp <= 4].dropna()
kd = f[f.sig < 0]; cm = pd.concat([f.y_brut, t.y_brut], axis=1, keys=["d", "b"]).dropna(); dd, pp = dP(f, "sig", "y_brut")
res["D5"] = {"donem": [str(f.index[0].date()), str(f.index[-1].date())], "n": int(len(kd)), "net": round(float(kd.y_net.mean()), 1), "P_net>0": P(kd.y_net), "delta": dd, "P_delta>0": pp, "ortak_gece": int(len(cm)), "korelasyon": round(float(cm.corr().iloc[0, 1]), 3), "sinyal_uyumu": round(float(((f.sig < 0).reindex(t.index).dropna() == (t.son_saat < 0).reindex(f.index).dropna()).mean()), 3)}; print("D5", res["D5"])
# D6: kart
v = K.y_net; h = len(v) // 2; sp_bp = (t.sp_o1600.fillna(t.sp_o1600.median()) / t.c * 1e4).reindex(K.index); s3 = K.y_brut - 3 * sp_bp - 1.8 * K.gece_n
gec = ((t.shift(-1).o930 / (t.o1630 + t.sp_o1630.fillna(t.sp_o1630.median()) * 1.5) - 1) * 1e4 - 1.8 * t.gece_n).reindex(K.index).dropna()
m = v.resample("ME").sum(); mall = m.reindex(pd.date_range(t.index.min(), t.index.max(), freq="ME")).fillna(0); eq = v.cumsum()
res["D6"] = {"n": int(len(v)), "net": round(float(v.mean()), 2), "P": P(v), "isabet": round(float((v > 0).mean()), 3), "yari": [round(float(v.iloc[:h].mean()), 2), round(float(v.iloc[h:].mean()), 2)], "spread_x3": round(float(s3.mean()), 2), "P_spread_x3": P(s3),
             "gecikme_1630": round(float(gec.mean()), 2), "n_gecikme": int(len(gec)), "eniyi5_haric": round(float(v.sort_values().iloc[:-5].mean()), 2), "enkotu_gece": round(float(v.min()), 0), "yillik_bp": round(float(v.sum() / ((t.index[-1] - t.index[0]).days / 365.25)), 0),
             "yil_basi_islem": round(float(len(v) / ((t.index[-1] - t.index[0]).days / 365.25)), 0), "aylik_SR": round(float(mall.mean() / mall.std() * np.sqrt(12)), 2), "ay_arti": round(float((m > 0).mean()), 3), "maxDD_bp": round(float((eq - eq.cummax()).min()), 0), "ss": round(float(v.std()), 0)}
print("D6", res["D6"])
# raporlanır
KV = K[K.vixp >= 18.4]; KL = K[K.vixp < 18.4]
res["rapor"] = {"KSG-V": {"n": int(len(KV)), "net": round(float(KV.y_net.mean()), 2), "P": P(KV.y_net)}, "KSG ∧ VIX<18,4": {"n": int(len(KL)), "net": round(float(KL.y_net.mean()), 2), "P": P(KL.y_net)}}
for nm, mm in (("03:00", 180), ("08:00", 480)):
    oo = ob(mm); res["rapor"]["cikis_" + nm] = round(float((((oo.shift(-1) / t.c - 1) * 1e4) - t.maliyet).reindex(K.index).mean()), 2)
res["rapor"]["ertesi_gunduz_KSG"] = round(float(K.y_gunduz.mean()), 2); res["rapor"]["ertesi_gunduz_diger"] = round(float(t[t.son_saat >= 0].y_gunduz.mean()), 2)
print("rapor", res["rapor"])
(OUT / "tur6.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str))
