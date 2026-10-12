"""XAU 1h yeni tepe BUY, SL 1,5×ATR + 20 mum zaman çıkışı — kart (ön kayıt: SL 1,5 xau_stops.py'de en iyi pozitif-yıl
oranıyla seçildi → seçim etkisi var; taban: aynı stop/çıkışla rastgele BUY, tek pozisyon)."""
import importlib.util as u, json
from pathlib import Path
from datetime import datetime
import numpy as np, pandas as pd
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[1]
sp = u.spec_from_file_location("mum_scan", ROOT / "research/mum_kural_20261009/scan.py"); S = u.module_from_spec(sp); sp.loader.exec_module(S)
sp2 = u.spec_from_file_location("deep", HERE / "deep.py"); D = u.module_from_spec(sp2); sp2.loader.exec_module(D)
d = pd.read_parquet(HERE / "data/XAUUSD_1h.parquet"); d = d[d.ts < "2026-09-03"].reset_index(drop=True); F = S.features(d)
o, h, l, c, seg, atr = F["o"], F["h"], F["l"], F["c"], F["seg"], F["atr"]; n = len(o); H, K = 20, 1.5
def sim(idx, spr, optimistic=False):
    res, busy, t = [], -1, []
    for i in idx:
        e = i + 1
        if i <= busy or e + H - 1 >= n or seg[e] != seg[i] or seg[e + H - 1] != seg[i]: continue
        A = atr[i]; ent = (c[i] if optimistic else o[e] + spr); stop = ent - K * A; out = None
        for j in range(e, e + H):
            if l[j] <= stop: out = (min(o[j], stop) if j > e else stop); last = j; break
        if out is None: out, last = c[e + H - 1], e + H - 1
        res.append((out - ent) / (K * A)); busy = last; t.append(F["ts"].iat[i])
    return np.array(res), pd.to_datetime(pd.Series(t), utc=True)
sig = np.where(D.pin_mask(F, kind="hepsi"))[0]
R, T = sim(sig, 0.25); R15, _ = sim(sig, 0.375); Ro, _ = sim(sig, 0.25, True)
rng = np.random.default_rng(5); base = [sim(np.sort(rng.choice(np.where(F["ok"])[0], len(sig), replace=False)), 0.25)[0].mean() for _ in range(20)]
u_, inv = np.unique(T.dt.strftime("%F"), return_inverse=True); s, k = np.bincount(inv, weights=R), np.bincount(inv)
bm = s[np.random.default_rng(1).integers(0, len(u_), (4000, len(u_)))].sum(1) / k[np.random.default_rng(1).integers(0, len(u_), (4000, len(u_)))].sum(1)
h2 = len(R) // 2; yrs = pd.Series(R).groupby(T.dt.year.to_numpy()).mean().round(3)
top5 = np.sort(pd.Series(R).groupby(T.dt.date.to_numpy()).sum().to_numpy())[::-1][:5].sum()
chk = {"1_hacim": (len(R), len(R) >= 150), "2_beklenti": (f"ortR {R.mean():+.3f} P %{100*(bm>0).mean():.1f}", R.mean() > 0 and (bm > 0).mean() >= .9),
       "3_kararlilik": (f"{R[:h2].mean():+.3f}/{R[h2:].mean():+.3f}", R[:h2].mean() >= 0 and R[h2:].mean() >= 0),
       "4_surtunme": (f"spread×1,5 {R15.mean():+.3f}", R15.mean() > 0),
       "5_icra": (f"kapanış-girişi {Ro.mean():+.3f} vs gerçek {R.mean():+.3f}", abs(Ro.mean() - R.mean()) < .5 * abs(R.mean())),
       "6_tek_poz": ("tek pozisyon", R.mean() > 0)}
v = "LIVE" if all(x[1] for x in chk.values()) else "SHADOW"
print(f"XAU 1h yeni tepe BUY, SL 1,5×ATR, 20 mum: n={len(R)} WR %{100*(R>0).mean():.1f} ortR {R.mean():+.3f} | aynı stoplu RASTGELE BUY "
      f"(20 tekrar) ort {np.mean(base):+.3f} max {np.max(base):+.3f} | en iyi 5 gün hariç toplam {R.sum()-top5:+.1f}R / {R.sum():+.1f}R")
for kk, (val, ok) in chk.items(): print(f"  {kk:14} {'✓' if ok else '✗'} {val}")
print("  yıllar:", dict(yrs), "→", v)
card = {"scope": "xau_1h_yeni_tepe_buy_sl15", "tarih": datetime.now().isoformat(timespec="seconds"), "olay": int(len(R)), "ort_R": round(float(R.mean()), 3),
        "taban_rastgele_buy_ayni_stop": round(float(np.mean(base)), 3), "taban_max": round(float(np.max(base)), 3), "bootstrap_P": round(float((bm > 0).mean()), 3),
        "en_iyi_5_gun_haric": round(float(R.sum() - top5), 1), "checks": {kk: {"deger": str(val), "gecti": bool(ok)} for kk, (val, ok) in chk.items()},
        "yillar": {int(y): float(x) for y, x in yrs.items()}, "verdikt": v,
        "uyari": "XAU'da post-hoc (MOM-H genel sınavı geçmedi); SL 1,5 dört stoptan seçildi; XAU intraday botta kapalı; 2016-26 altın boğa piyasası"}
(ROOT / "backend/data/evolution/go_live_cards/xau_1h_yeni_tepe_buy_sl15.json").write_text(json.dumps(card, ensure_ascii=False, indent=1))
