"""XAU 1h 'yeni 20-mum tepesinde BUY, 20 mum tut' canlıya alma kartı (2026-10-10). Tek pozisyon, giriş sonraki 1h açılışı +
0,25 spread, çıkış 20 mum sonra kapanış. Veri 2016-05 → 2026-09-02 (Yahoo öncesi). Not: kural XAU'da POST-HOC seçildi (H1
genel sınavı geçmedi; altın alt kümesi) → kart geçse bile sınıf en fazla B."""
import sys, json, importlib.util as u
from pathlib import Path
from datetime import datetime
import numpy as np, pandas as pd
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[1]
sp = u.spec_from_file_location("mum_scan", ROOT / "research/mum_kural_20261009/scan.py"); S = u.module_from_spec(sp); sp.loader.exec_module(S)
sp2 = u.spec_from_file_location("deep", HERE / "deep.py"); D = u.module_from_spec(sp2); sp2.loader.exec_module(D)
SPR, H = 0.25, 20
d = pd.read_parquet(HERE / "data/XAUUSD_1h.parquet"); d = d[d.ts < "2026-09-03"].reset_index(drop=True); F = S.features(d)
o, c, seg, atr = F["o"], F["c"], F["seg"], F["atr"]; n = len(o)
idx = np.where(D.pin_mask(F, kind="hepsi"))[0]
def trades(ix, spr, optimistic=False):
    e = ix + 1; ok = e + H - 1 < n; e, ix = e[ok], ix[ok]; ok = (seg[e] == seg[ix]) & (seg[e + H - 1] == seg[ix]); e, ix = e[ok], ix[ok]
    ent = c[ix] if optimistic else o[e] + spr
    return (c[e + H - 1] - ent) / atr[ix] - (0 if optimistic else 0) , ix
R_all, ii = trades(idx, SPR)
no = D.nonoverlap(ii, H); R, ii1 = R_all[no], ii[no]
R15, _ = trades(idx, SPR * 1.5); R15 = R15[no]
Ro, _ = trades(idx, SPR, optimistic=True); Ro = Ro[no]
days = pd.to_datetime(F["ts"].to_numpy()[ii1], utc=True)
u_, inv = np.unique(days.strftime("%F"), return_inverse=True); s, k = np.bincount(inv, weights=R), np.bincount(inv)
pick = np.random.default_rng(3).integers(0, len(u_), (4000, len(u_))); bm = s[pick].sum(1) / k[pick].sum(1)
h = len(R) // 2
yrs = pd.Series(R).groupby(days.year).agg(["size", "mean"]).round(3)
B, _ = trades(np.where(F["ok"])[0][::3], SPR)
top5 = np.sort(pd.Series(R).groupby(days.date).sum().to_numpy())[::-1][:5].sum()
chk = {"1_hacim": (len(R), len(R) >= 150), "2_beklenti": (f"ortR {R.mean():+.3f} P %{100*(bm>0).mean():.1f}", R.mean() > 0 and (bm > 0).mean() >= .9),
       "3_kararlilik": (f"{R[:h].mean():+.3f}/{R[h:].mean():+.3f}", R[:h].mean() >= 0 and R[h:].mean() >= 0),
       "4_surtunme": (f"spread×1,5 {R15.mean():+.3f}", R15.mean() > 0),
       "5_icra": (f"kapanış-girişi {Ro.mean():+.3f} vs gerçek {R.mean():+.3f}", abs(Ro.mean() - R.mean()) < .5 * abs(R.mean())),
       "6_tek_poz": ("zaten tek pozisyon", R.mean() > 0)}
v = "RED" if not chk["1_hacim"][1] else ("LIVE" if all(x[1] for x in chk.values()) else "SHADOW")
print(f"XAU 1h yeni tepe BUY T20 — {days.min().date()}→{days.max().date()} n={len(R)} WR %{100*(R>0).mean():.1f} ortR {R.mean():+.3f} "
      f"(rastgele BUY taban {B.mean():+.3f}) toplam {R.sum():+.1f}R, en iyi 5 gün hariç {R.sum()-top5:+.1f}R")
for kk, (val, ok) in chk.items(): print(f"  {kk:14} {'✓' if ok else '✗'} {val}")
print("  yıllar:", {int(y): (int(r['size']), r['mean']) for y, r in yrs.iterrows()}, "→", v)
card = {"scope": "xau_1h_yeni_tepe_buy", "tarih": datetime.now().isoformat(timespec="seconds"), "olay": int(len(R)), "ort_R": round(float(R.mean()), 3),
        "taban_rastgele_buy": round(float(B.mean()), 3), "toplam_R": round(float(R.sum()), 1), "en_iyi_5_gun_haric": round(float(R.sum() - top5), 1),
        "bootstrap_P": round(float((bm > 0).mean()), 3), "checks": {kk: {"deger": str(val), "gecti": bool(ok)} for kk, (val, ok) in chk.items()},
        "yillar": {int(y): float(r["mean"]) for y, r in yrs.iterrows()}, "verdikt": v,
        "uyari": "kural XAU'da post-hoc seçildi (MOM-H genel sınavı geçmedi); XAU intraday botta kapalı (BLOCKED_SYMBOLS)"}
(ROOT / "backend/data/evolution/go_live_cards/xau_1h_yeni_tepe_buy.json").write_text(json.dumps(card, ensure_ascii=False, indent=1))
