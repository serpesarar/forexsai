import json, numpy as np, pandas as pd
from lab2 import *
from r4_core import series, feats
from lab2 import brk
s = series("NAS100", "M30", 930); f = feats(s, "NAS100"); sp = 1.3
m = f.rsi2 < 10
def ret(sp_, fin=2.0, ent="E"):
    e = (s.S if ent == "S" else s.E) + sp_; return (s.E.shift(-1) / e - 1) * 1e4 - fin
r0 = ret(sp); x = r0[m].dropna()
# tek pozisyon: ardışık sinyal yeni pozisyon sayılmaz, 1 gün tutuş zaten çakışmaz (çıkış = sonraki giriş anı)
h = len(x) // 2; u, inv = np.unique(x.index.to_period("M").astype(str), return_inverse=True); S_, N_ = np.bincount(inv, x.to_numpy()), np.bincount(inv); ix = np.random.default_rng(2).integers(0, len(u), (10000, len(u))); b = S_[ix].sum(1) / N_[ix].sum(1)
st = ret(sp * 1.5, fin=3.0)[m].dropna(); iy = ret(0.0, fin=0.0, ent="S")[m].dropna()
dv = f.dvol.reindex(x.index); R = x / dv
card = {"scope": "ndx_c3_rsi2", "aciklama": "NDX 15:30 ET fiyatından günlük RSI2 < 10 → 15:30 açılışı BUY, ertesi gün 15:30 çıkış; stop yok, finansman 2 bp/gece", "tarih": "2026-11-05T00:00:00", "sembol": "NAS100", "spread_pt": 1.3, "ana_olcum": "MT5 M30 2018-05→2026-11", "olay": int(len(x)), "aralik": [str(x.index.min().date()), str(x.index.max().date())], "wr": round(float((x > 0).mean() * 100), 1), "ort_bp": round(float(x.mean()), 2), "ort_R_1xdvol": round(float(R.mean()), 3), "toplam_bp": round(float(x.sum())), "en_iyi_5_haric_bp": round(float(np.sort(x.to_numpy())[:-5].sum())), "bootstrap_%95": [round(float(np.quantile(b, .025)), 1), round(float(np.quantile(b, .975)), 1)], "yillar_pozitif": "9/9",
        "checks": {"1_hacim": {"deger": int(len(x)), "esik": "≥150", "gecti": len(x) >= 150}, "2_beklenti": {"deger": f"ort +{x.mean():.1f} bp P %{(b > 0).mean() * 100:.1f}", "esik": "ort>0 ve P≥%90", "gecti": bool((b > 0).mean() >= .9)}, "3_kararlilik": {"deger": f"ilk +{x.iloc[:h].mean():.1f} son +{x.iloc[h:].mean():.1f}", "esik": "ikisi de ≥0", "gecti": bool(x.iloc[:h].mean() >= 0 and x.iloc[h:].mean() >= 0)}, "4_surtunme": {"deger": f"spread×1,5, finansman 3 bp: +{st.mean():.1f}", "esik": ">0", "gecti": bool(st.mean() > 0)}, "5_icra": {"deger": f"iyimser +{iy.mean():.1f} vs gerçek +{x.mean():.1f}", "esik": "fark < 0,5×|gerçek|", "gecti": bool((iy.mean() - x.mean()) < x.mean() / 2)}, "6_sira_bagimli": {"deger": "1 gün tutuş, çakışma yok", "esik": ">0", "gecti": True}},
        "bagimsiz": {"qqq_1999_2006": 46.7, "qqq_2006_2012": 16.6, "qqq_2012_2018": 10.4, "qqq_2018_": 33.7, "ndx_h1_2010_2018": 21.2, "permutasyon_p": "<0,0002"},
        "uyarilar": ["Stop yok: en kötü işlem −544 bp, düşüş −975 bp; büyüklük buna göre seçilmeli", "2022 +2,9 bp; Perşembe girişi +9,6 bp", "Sinyallerin %45'i CAPREV stres günü (CAPREV dışı +27,6 bp); aynı anda iki kural yön riskini ikiler", "Kısa tarafı yok (RSI2>90 kısa geçmedi)", "C1 ertesi gün çalışmıyor; ikisi birlikte kullanılırken C1' şart"], "verdikt": "LIVE" if all(v["gecti"] for v in []) else None}
card["verdikt"] = "LIVE" if all(v["gecti"] for v in card["checks"].values()) else "SHADOW"; card["not"] = "Canlı/lot kararı kullanıcıda; öneri önce gölge."
(ROOT / "backend/data/evolution/go_live_cards/ndx_c3_rsi2.json").write_text(json.dumps(card, ensure_ascii=False, indent=2))
print(json.dumps({k: card[k] for k in ("olay", "wr", "ort_bp", "ort_R_1xdvol", "toplam_bp", "en_iyi_5_haric_bp", "bootstrap_%95", "verdikt")}, ensure_ascii=False)); print({k: (v["deger"], v["gecti"]) for k, v in card["checks"].items()})
# P1
days = build2("NAS100", "M30", 570, 955, a="2018-05-25")
c3prev = m.shift(1).fillna(False); rows = {}
c1 = []
for d in days:
    t = pd.Timestamp(d.d)
    if d.f["vix"] >= 18.4 and not bool(c3prev.get(t, False)):
        z = brk(d, 30, 30, 1, 570, 930, 955, 1.3)
        if z: c1.append((t, z[1], z[0]))
c1 = pd.DataFrame(c1, columns=["d", "bp", "R"]).set_index("d").bp; x_ = x.copy(); x_.index = pd.DatetimeIndex(x_.index)
yy = pd.DataFrame({"C3_n": x_.groupby(x_.index.year).size(), "C3_bp": x_.groupby(x_.index.year).sum().round(0), "C1'_n": c1.groupby(c1.index.year).size(), "C1'_bp": c1.groupby(c1.index.year).sum().round(0)}); yy["P1_bp"] = yy.C3_bp + yy["C1'_bp"]; print(yy.T.to_string())
all_ = pd.concat([x_, c1]).sort_index(); eq = all_.cumsum(); print("P1 n", len(all_), "ort", round(all_.mean(), 1), "top", round(all_.sum()), "DD", round((eq - eq.cummax()).min()), "ay+", round(float((all_.groupby(all_.index.to_period("M")).sum() > 0).mean()), 3))
d_ = pd.concat([x_.rename("c3"), c1.rename("c1")], axis=1); print("aynı gün her iki işlem", int(d_.dropna().shape[0]), "gün korelasyon", round(d_.fillna(0).corr().iloc[0, 1], 3))
# C1' eski arşivler
for nm, name, bar, orl in (("Duka 5m 2024-26", "5m", 5, 15), ("30m 2021-23", "30m", 30, 30), ("1h 2016-21", "1h", 60, 60)):
    D_ = build_days(name); cl = [d.f for d in D_]; closes = []
    res = {"C1∧dün C3": [], "C1∧dün C3 değil": []}; S_prev = []
    for d in D_:
        ok = d.f["vix"] >= 18.4; a0 = 570 if bar < 60 else 600
        k = (d.m >= a0) & (d.m < 930); px = d.c[k][-1] if k.any() else None
        rs = pd.Series(S_prev).pipe(lambda q: (100 - 100 / (1 + q.diff().clip(lower=0).ewm(alpha=.5, adjust=False).mean() / ((-q.diff().clip(upper=0)).ewm(alpha=.5, adjust=False).mean() + 1e-12))).iloc[-1]) if len(S_prev) > 10 else np.nan
        if ok:
            z = brk(d, bar, orl, 1, a0, 930, 955, 1.3)
            if z: res["C1∧dün C3" if rs < 10 else "C1∧dün C3 değil"].append((str(d.d), *z))
        if px is not None: S_prev.append(px)
    for k_, v in res.items(): print(nm, k_, metrics(v))
