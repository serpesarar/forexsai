"""CAPREV portföyü NDX + DAX — ön kayıt research/canli_kart_20261009/PROTOCOL.md §C (2026-10-09).

Kural aynen (round4.events / cross_market.events, stres ∧ VIX≥18,4), 1h, çıkış o piyasanın seans kapanışı,
stop 1×gvol, giriş sonraki bar açılışı + spread. Kart birleşik işlem listesinde; gün-bloklu bootstrap.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import cross_market as cm
from caprev_card import SPR, SPREAD_STRESS, paths
from common import block_boot
from long_data import load_long
from round4 import build, events

d_n = build(load_long("1h"), 60, 540)
d_d = cm.build_dax("1h")
ce_d = int(d_d.close_end.iat[0])
parts = []
for name, d, E, ce in [("NDX", d_n, events(d_n, "stress", "hi"), 960), ("DAX", d_d, cm.events(d_d, "stress", "hi"), ce_d)]:
    real = paths(d, E, SPR, close_end=ce).assign(m=name)
    real["R15"] = paths(d, E, SPR * SPREAD_STRESS, close_end=ce).R_d0.to_numpy()
    real["Ropt"] = paths(d, E, SPR, optimistic=True, close_end=ce).R_d0.to_numpy()
    parts.append(real)
    print(f"{name}: n={len(real)} ortR {real.R_d0.mean():+.3f} toplam {real.R_d0.sum():+.1f}R {real.nyd.min().date()}→{real.nyd.max().date()}")
x = pd.concat(parts).sort_values("nyd").reset_index(drop=True)
v = x.R_d0.to_numpy(); days = x.nyd.astype(str).to_numpy()
bs = block_boot(v, days, 4000); h = len(v) // 2
ndays = x.nyd.nunique(); both = (x.groupby("nyd").m.nunique() == 2).sum()
top5 = np.sort(x.groupby("nyd").R_d0.sum().to_numpy())[::-1][:5].sum()
# tek pozisyon (aynı gün NDX ve DAX çakışırsa önce açılanı tut — DAX seansı önce)
sp = x.sort_values(["nyd", "m"], ascending=[True, True]).groupby("nyd").head(1)
yrs = x.assign(y=x.nyd.dt.year).groupby("y").R_d0.sum()
print(f"\nPORTFÖY: işlem={len(v)} bağımsız gün={ndays} (iki piyasa aynı gün: {both}) WR %{100*(v>0).mean():.1f} "
      f"ortR {v.mean():+.3f} toplam {v.sum():+.1f}R")
print(f"  P(EV>0) %{100*np.mean(bs>0):.1f} CI[{np.percentile(bs,2.5):+.3f},{np.percentile(bs,97.5):+.3f}] "
      f"yarılar {v[:h].mean():+.3f}/{v[h:].mean():+.3f} ×1,5 spread {x.R15.mean():+.3f} "
      f"kapanış-girişi {x.Ropt.mean():+.3f} tek-poz(gün başına 1) n={len(sp)} ortR {sp.R_d0.mean():+.3f}")
print(f"  en iyi 5 gün hariç toplam {v.sum()-top5:+.1f}R · pozitif yıl {int((yrs>0).sum())}/{len(yrs)}")

import json
from datetime import datetime
from caprev_card import CARD
chk = {
    "1_hacim": {"deger": f"{len(v)} işlem / {ndays} bağımsız gün", "esik": "≥150 işlem (+ön kayıt: ≥100 bağımsız gün)",
                "gecti": bool(len(v) >= 150 and ndays >= 100)},
    "2_beklenti": {"deger": f"ortR={v.mean():+.3f} P(EV>0)=%{100*np.mean(bs>0):.1f}", "esik": "ortR>0 ve P≥%90",
                   "gecti": bool(v.mean() > 0 and np.mean(bs > 0) >= .9)},
    "3_kararlilik": {"deger": f"ilk={v[:h].mean():+.3f} son={v[h:].mean():+.3f}", "esik": "ikisi de ≥0",
                     "gecti": bool(v[:h].mean() >= 0 and v[h:].mean() >= 0)},
    "4_surtunme": {"deger": f"spread×1.5: ortR={x.R15.mean():+.3f}", "esik": ">0", "gecti": bool(x.R15.mean() > 0)},
    "5_icra": {"deger": f"kapanış-girişi {x.Ropt.mean():+.3f} vs gerçek {v.mean():+.3f}", "esik": "fark < 0,5×|ortR|",
               "gecti": bool(abs(x.Ropt.mean() - v.mean()) < .5 * abs(v.mean()))},
    "6_sira_bagimli": {"deger": f"gün başına tek pozisyon n={len(sp)} ortR={sp.R_d0.mean():+.3f}", "esik": ">0",
                       "gecti": bool(sp.R_d0.mean() > 0)},
}
card = {"scope": "caprev_portfoy", "aciklama": "CAPREV (stres∧VIX≥18,4, önceki RTH dibi altı ilk kapanış → BUY, stop 1×gvol, "
        "seans kapanışında çık) NDX + DAX birlikte", "tarih": datetime.now().isoformat(timespec="seconds"),
        "semboller": ["NAS100", "GER40"], "olay": int(len(v)), "bagimsiz_gun": int(ndays), "wr": round(100 * float((v > 0).mean()), 1),
        "ort_R": round(float(v.mean()), 3), "toplam_R": round(float(v.sum()), 2),
        "en_iyi_5_gun_haric_toplam": round(float(v.sum() - top5), 2), "pozitif_yil": f"{int((yrs > 0).sum())}/{len(yrs)}",
        "bootstrap_%95": [round(float(np.percentile(bs, 2.5)), 3), round(float(np.percentile(bs, 97.5)), 3)],
        "checks": chk, "verdikt": "LIVE" if all(c["gecti"] for c in chk.values()) else "SHADOW",
        "uyarilar": ["toplamın %64'ü en iyi 5 günden", "ilk yarı zayıf (+0,064)", "NDX geçmişine 4+ turda bakıldı (E23); DAX kural "
                     "değiştirilmeden sınanan bağımsız piyasa", "M1 katı icra yalnız NDX 11 işlem", "canlı/gölge ileri kanıt yok (gölge 0 olay)"],
        "not": "research/ndx_gate_forge/caprev_pooled.py; ön kayıt research/canli_kart_20261009/PROTOCOL.md §C"}
(CARD.parent / "caprev_portfoy.json").write_text(json.dumps(card, ensure_ascii=False, indent=1))
print("kart:", card["verdikt"], {k: c["gecti"] for k, c in chk.items()})
