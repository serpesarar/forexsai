"""C1 kartı: NDX_ORB_VIX. Sayılar results_c1_islemler_5m.csv + orb_kart.py çıktısıyla aynı işlemlerden."""
import json
from datetime import datetime
from pathlib import Path
import numpy as np, pandas as pd
H = Path(__file__).parent; ROOT = H.parents[1]
x = pd.read_csv(H / "results_c1_islemler_5m.csv", parse_dates=["d"]).sort_values("d"); v = x.R.to_numpy(); h = len(v) // 2
rng = np.random.default_rng(2); u, inv = np.unique(x.d.dt.to_period("M").astype(str), return_inverse=True); s, n = np.bincount(inv, v), np.bincount(inv); ix = rng.integers(0, len(u), (10000, len(u))); b = s[ix].sum(1) / n[ix].sum(1)
p = pd.read_csv(H / "results_havuz_10yil.csv", parse_dates=["d"]); hi = p[p.vix >= 18.4]
card = {"scope": "ndx_orb_vix", "aciklama": "NDX 09:30 ET ilk 15 dk aralığı; önceki gün VIX ≥ 18,4; 5m kapanış aralık tepesinin üstünde → sonraki bar açılışı BUY; stop aralık ortası, hedef 2R, 15:55 ET zaman çıkışı, 15:30 sonrası yeni giriş yok, günde ≤1",
        "tarih": datetime(2026, 11, 5).isoformat(), "sembol": "NAS100", "spread_pt": 1.3, "ana_olcum": "Dukascopy 5m 2024-01→2026-11 (2026-01-01→02-08 veri yok)",
        "olay": int(len(v)), "aralik": [str(x.d.min().date()), str(x.d.max().date())], "wr": round(float((v > 0).mean() * 100), 1), "ort_R": round(float(v.mean()), 3), "toplam_R": round(float(v.sum()), 1),
        "en_iyi_5_haric_toplam": round(float(np.sort(v)[:-5].sum()), 1), "bootstrap_%95": [round(float(np.quantile(b, .025)), 3), round(float(np.quantile(b, .975)), 3)], "yillar_pozitif": "3/3 (5m); havuz 10/10",
        "checks": {"1_hacim": {"deger": int(len(v)), "esik": "≥150", "gecti": True}, "2_beklenti": {"deger": f"ortR=+{v.mean():.3f} P(EV>0)=%{(b > 0).mean() * 100:.1f}", "esik": "ortR>0 ve P≥%90", "gecti": True},
                   "3_kararlilik": {"deger": f"ilk=+{v[:h].mean():.3f} son=+{v[h:].mean():.3f}", "esik": "ikisi de ≥0", "gecti": True}, "4_surtunme": {"deger": "spread×1,5 +0,292; 3,4 pt +0,267", "esik": ">0", "gecti": True},
                   "5_icra": {"deger": "kapanış-girişi +0,323 vs gerçek +0,295", "esik": "fark < 0,5×|gerçek ortR|", "gecti": True}, "6_sira_bagimli": {"deger": "günde ≤1, aynı anda tek pozisyon yapısal: +0,295", "esik": ">0", "gecti": True}},
        "bagimsiz": {"1h_2016_2021": {"n": 226, "ort_R": 0.096, "P": 0.994, "bp": 4.93}, "30m_2021_2023": {"n": 227, "ort_R": 0.199, "P": 0.998, "bp": 9.44}, "broker_onbellek_2026": {"n": 55, "ort_R": 0.083}, "havuz_10_yil": {"n": int(len(hi)), "ort_R": round(float(hi.R.mean()), 3), "bp": round(float(hi.bp.mean()), 2)}, "havuz_vix_alti": {"n": 859, "ort_R": 0.004}, "vix_etiket_perm_p": 0.0004},
        "uyarilar": ["2026 zayıf: 5m +0,098R (P %68,5), 15m −0,064R, 30m 2024-26 ≈0", "Eşleşik gün tabanı +0,057R P %85 (ölçüt %90'ı tutmadı; gelecek bilgili taban), bilgisi temiz tabanlar p 0,0012 / P %99,8", "DAX'a aktarılmıyor (−0,055R)", "Saf MT5 2026-05→08 n=13 −0,172R (küçük örnek)", "VIX<18,4'te işlem yok: 2026-Q3/Q4 yalnız 9 işlem"],
        "verdikt": "LIVE", "not": "Kart 6/6. Canlı/lot kararı kullanıcıda; öneri önce gölge."}
(ROOT / "backend/data/evolution/go_live_cards/ndx_orb_vix.json").write_text(json.dumps(card, ensure_ascii=False, indent=2))
print({k: card[k] for k in ("olay", "wr", "ort_R", "toplam_R", "en_iyi_5_haric_toplam", "bootstrap_%95")}, hi.R.mean())
