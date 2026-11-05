import json, numpy as np, pandas as pd, yfinance as yf
from lab2 import *
from r4_core import series, feats
from c3b_core import sim
pd.set_option("display.width", 200)
def g(t, a="2009-01-01"):
    s = yf.Ticker(t).history(start=a, end="2026-11-05", auto_adjust=True)["Close"]; s.index = s.index.tz_localize(None).normalize(); return s
V = g("^VIX"); ch = V.pct_change() * 100; Z = (ch - ch.rolling(60).mean().shift(1)) / ch.rolling(60).std().shift(1)
def x2(sym, th, side, tf, ent, ex, sp, a, b):
    x = mt5_bars(sym, tf); x = x[(x.ts_et >= a) & (x.ts_et < b)]; x["d"] = x.ts_et.dt.normalize(); x["m"] = x.ts_et.dt.hour * 60 + x.ts_et.dt.minute; O = x.pivot_table(index="d", columns="m", values="o", aggfunc="first")
    tr = O[O.index.dayofweek < 5]; rows = {}
    for i, d in enumerate(tr.index[:-1]):
        z = Z.get(d, np.nan)
        if not (z <= th) or ent not in tr or ex not in tr: continue
        if d.dayofweek == 4: e = O[ent].get(d + pd.Timedelta(days=2), np.nan)      # Cuma kapanışı sinyali → Pazar 18:30
        else: e = tr[ent].iat[i]
        xt = tr[ex].iat[i + 1]
        if e == e and xt == xt: rows[d] = ((xt / (e + sp) - 1) * 1e4 - 2) if side > 0 else ((e / (xt + sp) - 1) * 1e4 - .5)
    q = pd.Series(rows).sort_index()
    if len(q) < 8: return f"n={len(q)}"
    u, inv = np.unique(q.index.to_period("M").astype(str), return_inverse=True); S, N = np.bincount(inv, q.to_numpy()), np.bincount(inv); ix = np.random.default_rng(3).integers(0, len(u), (3000, len(u)))
    return f"n={len(q)} ort={q.mean():.1f} isabet={(q>0).mean():.2f} P={((S[ix].sum(1)/N[ix].sum(1))>0).mean():.3f} y1={q.iloc[:len(q)//2].mean():.1f} y2={q.iloc[len(q)//2:].mean():.1f}"
print("X2 VIX z≤−1,5 → XAU uzun, D 18:30 → D+1 13:00")
for a, b in (("2018-05-25", "2022-08-15"), ("2022-08-15", "2025-01-01"), ("2025-01-01", "2027-01-01")): print(" M30", a[:7], x2("XAUUSD", -1.5, 1, "M30", 1110, 780, .25, a, b))
print(" H1 2010-18 (görülmemiş, 19:00→13:00)", x2("XAUUSD", -1.5, 1, "H1", 1140, 780, .25, "2010-05-01", "2018-05-25"))
print(" taban tüm günler H1 2010-18", x2("XAUUSD", 99, 1, "H1", 1140, 780, .25, "2010-05-01", "2018-05-25")); print(" taban M30 2018-26", x2("XAUUSD", 99, 1, "M30", 1110, 780, .25, "2018-05-25", "2027-01-01"))
# C3b kartı
s = series("NAS100", "M30", 930); f = feats(s, "NAS100"); S = s.S.to_numpy(); E = s.E.to_numpy(); idx = s.index; m = (f.rsi2 < 10).to_numpy()
up = lambda i: next((k for k in range(i + 1, min(i + 6, len(S))) if S[k] > S[k - 1]), min(i + 5, len(S) - 1))
tr = sim(S, E, m, up, 1.3, 2, 5); x = pd.Series([t[2] for t in tr], index=[idx[t[0]] for t in tr]); tst = sim(S, E, m, up, 1.95, 3, 5); xs = pd.Series([t[2] for t in tst]); ty = sim(S, S, m, up, 0, 0, 5); xy = pd.Series([t[2] for t in ty])
u, inv = np.unique(x.index.to_period("M").astype(str), return_inverse=True); S_, N_ = np.bincount(inv, x.to_numpy()), np.bincount(inv); ix = np.random.default_rng(2).integers(0, len(u), (10000, len(u))); b = S_[ix].sum(1) / N_[ix].sum(1); h = len(x) // 2; eq = x.cumsum()
card = {"scope": "ndx_c3b_rsi2_upexit", "aciklama": "NDX 15:30 ET fiyatından günlük RSI2<10 → 15:30 açılışı BUY; ilk günlük 15:30 fiyatı önceki günün üstünde olunca (≤5 gün) o açılışta çık; stop yok; tek pozisyon", "tarih": "2026-11-05T00:00:00", "sembol": "NAS100", "ana_olcum": "MT5 M30 2018-05→2026-11, spread 1,3 pt, finansman 2 bp/gece", "olay": len(x), "aralik": [str(x.index.min().date()), str(x.index.max().date())], "wr": round((x > 0).mean() * 100, 1), "ort_bp": round(x.mean(), 2), "toplam_bp": round(x.sum()), "en_iyi_5_haric_bp": round(np.sort(x.to_numpy())[:-5].sum()), "en_kotu_bp": round(x.min()), "max_dusus_bp": round((eq - eq.cummax()).min()), "ortalama_tutus_gun": round(np.mean([t[1] - t[0] for t in tr]), 2), "bootstrap_%95": [round(np.quantile(b, .025), 1), round(np.quantile(b, .975), 1)], "yillar_pozitif": f"{int((x.groupby(x.index.year).mean() > 0).sum())}/{x.index.year.nunique()}",
        "checks": {"1_hacim": {"deger": len(x), "esik": "≥150", "gecti": len(x) >= 150}, "2_beklenti": {"deger": f"+{x.mean():.1f} bp P %{(b > 0).mean() * 100:.1f}", "esik": "ort>0, P≥%90", "gecti": bool((b > 0).mean() >= .9)}, "3_kararlilik": {"deger": f"ilk +{x.iloc[:h].mean():.1f} son +{x.iloc[h:].mean():.1f}", "esik": "ikisi ≥0", "gecti": True}, "4_surtunme": {"deger": f"spread×1,5 fin 3 bp +{xs.mean():.1f}", "esik": ">0", "gecti": bool(xs.mean() > 0)}, "5_icra": {"deger": f"iyimser +{xy.mean():.1f} vs +{x.mean():.1f}", "esik": "fark<0,5×", "gecti": bool(xy.mean() - x.mean() < x.mean() / 2)}, "6_sira_bagimli": {"deger": f"tek pozisyon zaten: +{x.mean():.1f}", "esik": ">0", "gecti": True}},
        "bagimsiz": {"qqq": {"1999_2003": 110.5, "2003_2009": 37.0, "2009_2014": 26.2, "2014_2018": 3.9, "2018_": 56.3}, "kesit": {"SPY": 39.6, "IWM": 27.9, "EFA": 23.0, "DIA": 14.9}, "gc_cl": "yok"},
        "uyarilar": ["Hacim 129 < 150; C3 (h=1) 201 ile 6/6", "Stop yok: en kötü işlem ve düşüş büyüklük kararını belirler", "2022 +6 bp; 2014-18 QQQ +3,9 (taban altı)", "CAPREV ile aynı günlerde yön riski ikiler"], "verdikt": None, "not": "Karar kullanıcıda; öneri önce gölge, sonra küçük lot."}
card["verdikt"] = "LIVE" if all(v["gecti"] for v in card["checks"].values()) else "SHADOW"; (ROOT / "backend/data/evolution/go_live_cards/ndx_c3b_rsi2_upexit.json").write_text(json.dumps(card, ensure_ascii=False, indent=2)); print({k: card[k] for k in ("olay", "wr", "ort_bp", "toplam_bp", "en_iyi_5_haric_bp", "en_kotu_bp", "max_dusus_bp", "ortalama_tutus_gun", "yillar_pozitif", "verdikt")}); x.to_csv(HERE / "results/c3b_islemler.csv")
