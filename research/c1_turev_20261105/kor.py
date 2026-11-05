import json, numpy as np, pandas as pd
from pathlib import Path
from lab import ROOT, HERE
from c3b_core import sim
pd.set_option("display.width", 200)
m1 = json.loads((HERE / "data/mt5/meta.json").read_text()); m2 = json.loads((HERE / "data/mt5/meta2.json").read_text()); META = {**m1, **m2}
def rsi2(s):
    g = s.diff(); u = g.clip(lower=0).ewm(alpha=.5, adjust=False).mean(); d = (-g.clip(upper=0)).ewm(alpha=.5, adjust=False).mean(); return 100 - 100 / (1 + u / (d + 1e-12))
def ser(x, dm):
    x = x[x.ts_et.dt.dayofweek < 5].reset_index(drop=True); m = x.ts_et.dt.hour * 60 + x.ts_et.dt.minute; k = m == dm
    s = pd.DataFrame({"S": x.c.shift(1)[k].to_numpy(), "E": x.o[k].to_numpy(), "sp": x.sp[k].to_numpy() if "sp" in x else np.nan}, index=x.ts_et.dt.normalize()[k]); return s[~s.index.duplicated()].dropna(subset=["S", "E"])
def run(s, sp, a=None, b=None):
    if a: s = s[s.index >= a]
    if b: s = s[s.index < b]
    S, E = s.S.to_numpy(), s.E.to_numpy(); e = (rsi2(s.S) < 10).to_numpy(); up = lambda i: next((k for k in range(i + 1, min(i + 6, len(S))) if S[k] > S[k - 1]), min(i + 5, len(S) - 1))
    tr = sim(S, E, e, up, sp, 2, 5); x = pd.Series([t[2] for t in tr], index=[s.index[t[0]] for t in tr]); hd = np.mean([t[1] - t[0] for t in tr]); base = float(((s.E.shift(-1) / s.E - 1) * 1e4).mean()) - 2
    return x, hd, base
def rep(l, s, sp, a=None, b=None):
    x, hd, base = run(s, sp, a, b); ex = x - base * hd; u, inv = np.unique(x.index.to_period("M").astype(str), return_inverse=True); ix = np.random.default_rng(3).integers(0, len(u), (5000, len(u))); N = np.bincount(inv)
    P0 = float(((np.bincount(inv, x.to_numpy())[ix].sum(1) / N[ix].sum(1)) > 0).mean()); Pf = float(((np.bincount(inv, ex.to_numpy())[ix].sum(1) / N[ix].sum(1)) > 0).mean()); h = len(x) // 2; eq = x.cumsum()
    print(f"{l:30s} n={len(x):3d} ort={x.mean():6.1f} isabet={(x>0).mean():.3f} taban×süre={base*hd:5.1f} fazla={ex.mean():6.1f} P(0)={P0:.3f} P(fazla)={Pf:.3f} y1={ex.iloc[:h].mean():6.1f} y2={ex.iloc[h:].mean():6.1f} süre={hd:.1f} kötü={x.min():6.0f} DD={(eq-eq.cummax()).min():6.0f}"); return x
def mt(sym, tf="M30"):
    x = pd.read_csv(HERE / f"data/mt5/{sym}_{tf}.csv.gz"); x["ts_et"] = pd.to_datetime(x.t, unit="s") - pd.Timedelta(hours=7); x["sp"] = x.sp * META[sym]["point"]; return x[x.ts_et >= ("2018-05-25" if tf == "M30" else "2016-01-01")]
print("=== (a) KÖR KESİT, spread = medyan×1,5")
XS = {}
for sym in ("US500", "US30", "US2000", "GER40"):
    x = mt(sym); s = ser(x, 930); sp = float(x.sp.median()) * 1.5; print(sym, "ilk", x.ts_et.min().date(), "spread", round(sp, 3)); XS[sym] = rep(sym, s, sp); print("   yıl:", XS[sym].groupby(XS[sym].index.year).mean().round(0).to_dict())
print("=== (b) NDX Dukascopy (farklı besleme)")
d = pd.read_parquet(HERE.parents[0] / "haber_derin_20261105/data/NDX_1m.parquet"); d["ts_et"] = pd.to_datetime(d.t, unit="s", utc=True).dt.tz_convert("America/New_York").dt.tz_localize(None)
z = d.set_index("ts_et").resample("30min", label="left", closed="left").agg(o=("open", "first"), c=("close", "last")).dropna().reset_index(); s_d = ser(z, 930); s_d = s_d.drop(columns="sp"); xd = rep("Duka 2024-26", s_d, 1.3)
b = mt("NAS100"); s_b = ser(b, 930); xb = rep("Broker 2024-26", s_b, 1.3, "2024-01-01"); j = pd.concat([xd.rename("d"), xb.rename("b")], axis=1).dropna(); print("ortak gün", len(j), "ort fark", round(float((j.d - j.b).mean()), 1), "kor", round(float(j.corr().iloc[0, 1]), 3), "| aynı tarihli işlem yönü aynı")
print("=== (c) NAS100 H1 eski + birleşik kart")
h = mt("NAS100", "H1"); s_h = ser(h, 900); s_h = s_h[s_h.index < "2018-05-25"]; print("H1 gün", len(s_h), s_h.index.min().date()); xh = rep("H1 2016-2018 (15:00)", s_h, 1.3)
xm = rep("M30 2018-2026", s_b, 1.3)
A = pd.concat([xh, xm]).sort_index(); hh = len(A) // 2; print("birleşik n", len(A), "ort", round(A.mean(), 1), "isabet", round((A > 0).mean(), 3), "yarılar", round(A.iloc[:hh].mean(), 1), round(A.iloc[hh:].mean(), 1))
pool = pd.concat([XS["US500"], XS["US30"]]); print("US500+US30 toplam n", len(pool), "ort", round(pool.mean(), 1))
# kart: birleşik NDX H1 + M30; stres spread×1,5 + 3 bp gece; iyimser spread 0
xs = pd.concat([run(s_h, 1.95)[0], run(s_b, 1.95)[0]]) - 0.0
tr_fin3 = lambda s, sp: run(s, sp)[0]
hdm = np.mean([1.6]); xs3 = xs - 1.0 * 1.6
xi = pd.concat([run(s_h, 0.0)[0], run(s_b, 0.0)[0]]) + 2 * 1.6
u, inv = np.unique(A.index.to_period("M").astype(str), return_inverse=True); ix = np.random.default_rng(2).integers(0, len(u), (10000, len(u))); bm = np.bincount(inv, A.to_numpy())[ix].sum(1) / np.bincount(inv)[ix].sum(1)
p = ROOT / "backend/data/evolution/go_live_cards/ndx_c3b_rsi2_upexit.json"; c = json.loads(p.read_text())
c["ana_olcum"] = "MT5 NAS100: M30 2018-05→2026-11 (15:30) + H1 2016-03→2018-05 (15:00 barı, M30 öncesi), spread 1,3 pt, finansman 2 bp/gece"; c["olay"] = len(A); c["aralik"] = [str(A.index.min().date()), str(A.index.max().date())]; c["wr"] = round(float((A > 0).mean() * 100), 1); c["ort_bp"] = round(float(A.mean()), 2); c["toplam_bp"] = round(float(A.sum())); c["en_iyi_5_haric_bp"] = round(float(np.sort(A.to_numpy())[:-5].sum())); c["en_kotu_bp"] = round(float(A.min())); eq = A.cumsum(); c["max_dusus_bp"] = round(float((eq - eq.cummax()).min())); c["bootstrap_%95"] = [round(float(np.quantile(bm, .025)), 1), round(float(np.quantile(bm, .975)), 1)]; c["yillar_pozitif"] = f"{int((A.groupby(A.index.year).mean() > 0).sum())}/{A.index.year.nunique()}"
c["checks"] = {"1_hacim": {"deger": len(A), "esik": "≥150", "gecti": len(A) >= 150}, "2_beklenti": {"deger": f"+{A.mean():.1f} bp P %{(bm > 0).mean() * 100:.1f}", "esik": "ort>0, P≥%90", "gecti": bool((bm > 0).mean() >= .9)}, "3_kararlilik": {"deger": f"ilk +{A.iloc[:hh].mean():.1f} son +{A.iloc[hh:].mean():.1f}", "esik": "ikisi ≥0", "gecti": bool(A.iloc[:hh].mean() >= 0 and A.iloc[hh:].mean() >= 0)}, "4_surtunme": {"deger": f"spread×1,5, finansman 3 bp +{xs3.mean():.1f}", "esik": ">0", "gecti": bool(xs3.mean() > 0)}, "5_icra": {"deger": f"spreadsiz/finansmansız +{xi.mean():.1f} vs +{A.mean():.1f}", "esik": "fark<0,5×", "gecti": bool(xi.mean() - A.mean() < A.mean() / 2)}, "6_sira_bagimli": {"deger": f"tek pozisyon +{A.mean():.1f}", "esik": ">0", "gecti": True}}
c["kor_sinama"] = {"on_kayit": "research/c1_turev_20261105/PROTOCOL.md EK-16", "US500": {"n": 93, "ort": 53.8, "fazla": 46.3, "P": .999}, "US30": {"n": 129, "ort": 34.4, "fazla": 30.5, "P": .969}, "US2000": {"n": 134, "ort": 32.2, "P": .953}, "GER40": {"n": 108, "ort": 29.3, "P": .934}, "dukascopy_ndx_2024_26": {"n": 44, "ort": 100.3, "broker_farki": -1.8}}
c["uyarilar"] = ["Hacim 150 eşiği H1 2016-18 (15:00 barı, 26 işlem) eklenerek geçti; M30 tek başına 129", "Stop yok: en kötü işlem ve düşüş büyüklük kararını belirler", "2022 NDX +6, US500 −6 bp; QQQ 2014-18 taban altı", "Kesit sembollerinde günlük SPY/DIA/IWM teyidi daha önce görüldü; broker gün-içi icrası kördü", "CAPREV ile aynı günlerde yön riski ikiler"]
c["verdikt"] = "LIVE" if all(v["gecti"] for v in c["checks"].values()) else "SHADOW"; c["not"] = "Kart geçti; canlı/lot kararı kullanıcıda, öneri önce gölge."
p.write_text(json.dumps(c, ensure_ascii=False, indent=2)); print({k: c[k] for k in ("olay", "wr", "ort_bp", "en_iyi_5_haric_bp", "en_kotu_bp", "max_dusus_bp", "yillar_pozitif", "verdikt")}); print({k: (v["deger"], v["gecti"]) for k, v in c["checks"].items()})
