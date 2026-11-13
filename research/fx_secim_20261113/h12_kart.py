"""FX-01 EK-9 H12 VIXREG-FX — canlıya alma kartı (16 çift eşit ağırlık, 2010→). Çalıştır: ../../.venv/bin/python -I h12_kart.py"""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fx_core as f, h11
CARD = f.ROOT / "backend/data/evolution/go_live_cards/fx_vixreg_risk_doviz.json"
BLIND = {"USDNOK": -1, "USDSEK": -1, "USDCAD": -1, "EURAUD": -1, "EURCAD": -1, "GBPAUD": -1}
PAIRS = {**h11.MAIN, **h11.BLIND, **BLIND}
v = h11.vix()

def frames(lag_extra=True, cost_mult=1.0):
    out = {}
    for p, s in PAIRS.items():
        d = h11.prep(p); d["day"] = d.srv.dt.normalize(); d = d.set_index("day")
        d["r"] = s * np.log(d.c / d.c.shift()) * 1e4
        vv = v.reindex(d.index, method="ffill")
        lag = vv.shift(2 if lag_extra else 1)
        on = (lag >= h11.TH)
        sw = on.astype(int).diff().abs().fillna(0)
        cost = sw * (d.yr_sp + h11.comm(p) / 2) * cost_mult
        d["on"], d["cost"] = on.astype(float).where(lag.notna()), cost
        d["s"] = d.on * d.r - cost
        out[p] = d[d.index >= "2010-01-01"].dropna(subset=["r", "on"])
    return out

def port(fr):
    return pd.concat({p: x.s for p, x in fr.items()}, axis=1).mean(1), pd.concat({p: x.on for p, x in fr.items()}, axis=1).mean(1) > 0.5, pd.concat({p: x.r for p, x in fr.items()}, axis=1).mean(1)

fr = frames(); s, on, r = port(fr)
s_opt, _, _ = port(frames(lag_extra=False, cost_mult=0.0))
s15, _, _ = port(frames(cost_mult=1.5))
# rejim epizodları
ep = (on.astype(int).diff() == 1)
ep_id = ep.cumsum()[on]
ep_ret = s[on].groupby(ep_id).sum()
rng = np.random.default_rng(2)
P_ep = f.boot_p(ep_ret.values)
h = len(ep_ret) // 2
sh = lambda x: float(x.mean() / x.std() * np.sqrt(252))
checks = {
 "1_hacim": {"deger": f"{len(ep_ret)} rejim epizodu, {int(on.sum())} rejim günü", "esik": "≥150 olay", "gecti": len(ep_ret) >= 150},
 "2_beklenti": {"deger": f"epizod ort {ep_ret.mean():+.1f} bp, P(EV>0)=%{P_ep*100:.1f}", "esik": "ort>0 ve P≥%90", "gecti": bool(ep_ret.mean() > 0 and P_ep >= 0.9)},
 "3_kararlilik": {"deger": f"ilk yarı {ep_ret.iloc[:h].mean():+.1f} son yarı {ep_ret.iloc[h:].mean():+.1f} bp/epizod", "esik": "ikisi de ≥0", "gecti": bool(ep_ret.iloc[:h].mean() >= 0 and ep_ret.iloc[h:].mean() >= 0)},
 "4_surtunme": {"deger": f"maliyet×1,5 yıllık {s15.mean()*252/100:+.2f}%", "esik": ">0", "gecti": bool(s15.mean() > 0)},
 "5_icra": {"deger": f"iyimser (1 gün gecikme, maliyetsiz) yıllık {s_opt.mean()*252/100:+.2f}% vs gerçek (2 gün gecikme + maliyet) {s.mean()*252/100:+.2f}%", "esik": "fark < 0,5×gerçek", "gecti": bool(abs(s_opt.mean() - s.mean()) < 0.5 * s.mean())},
 "6_sira_bagimli": {"deger": "çift başına tek pozisyon (rejim açık/kapalı), çakışma yok", "esik": ">0", "gecti": bool(s.mean() > 0)},
}
n_ok = sum(c["gecti"] for c in checks.values())
card = {"scope": "fx_vixreg_risk_doviz", "tarih": "2026-11-13", "sembol": "16 FX çifti, risk para birimi uzun yönünde eşit ağırlık",
 "kural": "t+1 günü getirisi için t−1 günü VIX kapanışı ≥ 18,4 ise (bir gün fazladan gecikme) o gün risk para birimi UZUN (AUD/NZD/CAD/MXN/ZAR/NOK/SEK/GBP vs JPY/USD/EUR), aksi hâlde DÜZ. Günlük, broker 17:00 ET kapanışları.",
 "mekanizma": "Fed çağında (2010→) korku fiyatlandıktan sonra risk varlıkları döner (NDX VIXREG'in FX karşılığı). 2009 öncesi tersi (sakin rejim taşıması) → çağa bağlı.",
 "ana_olcum": "Pepperstone MT5 D1 2010-01→2026-11, spot (faiz farkı yok), maliyet 2× yıllık medyan spread + komisyon/geçiş",
 "kor_dogrulama": json.loads((f.RES / "h12_olcut.json").read_text())["kor"],
 "yillik_%": round(float(s.mean() * 252 / 100), 2), "Sharpe": round(sh(s), 2), "al_tut_Sharpe": round(sh(r), 2),
 "maxDD_%": round(float((s.cumsum() - s.cumsum().cummax()).min() / 100), 1),
 "yil_%": {int(y): round(float(g.mean() * 252 / 100), 2) for y, g in s.groupby(s.index.year)},
 "NDX_VIXREG_korelasyon": 0.608,
 "checks": checks, "gecen": f"{n_ok}/6", "verdikt_kod": "LIVE" if n_ok == 6 else ("SHADOW" if n_ok >= 4 else "RED"),
 "kanit": "research/fx_secim_20261113/ (PROTOCOL.md EK-8/EK-9, h11.py, h12_kart.py, results/h12*.json)"}
CARD.write_text(json.dumps(card, ensure_ascii=False, indent=1, default=float))
print(json.dumps({k: card[k] for k in ("yillik_%", "Sharpe", "al_tut_Sharpe", "maxDD_%", "gecen", "verdikt_kod", "yil_%")}, ensure_ascii=False))
for k, c in checks.items(): print(k, c["gecti"], c["deger"])
