"""FX-01 EK-6 H8c-D: 4 JPY çifti eşit ağırlık havuz (çift seçimi yok) + nedensel doz eşiği — kart. Çalıştır: ../../.venv/bin/python -I h8cd_kart.py"""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fx_core as f
from ek6 import tokyo_table
PAIRS = ["USDJPY", "EURJPY", "GBPJPY", "AUDJPY"]
CARD = f.ROOT / "backend/data/evolution/go_live_cards/jpy_gotobi_doz_havuz.json"
T = {p: tokyo_table(p).assign(p=p) for p in PAIRS}
a = pd.concat(T.values()); a = a[a.index >= "2010-10-12"]
leg = a[a.got & (a.pre > 0) & (a.pre > a.thr)].dropna(subset=["net"])
ctl = a[~a.got & (a.pre > 0) & (a.pre > a.thr)].dropna(subset=["net"])
ev = leg.groupby(level=0).agg(net=("net", "mean"), gross=("gross", "mean"), k=("p", "size"))
ev["cost"] = ev.gross - ev.net
cev = ctl.groupby(level=0).net.mean()
h = len(ev) // 2; P = f.boot_p(ev.net.values)
k, b = ev[ev.index < f.SPLIT].net, ev[ev.index >= f.SPLIT].net
stress = (ev.gross - 1.5 * ev.cost).mean()
rng = np.random.default_rng(8)
dd = np.array([rng.choice(ev.net.values, len(ev)).mean() - rng.choice(cev.values, len(cev)).mean() for _ in range(3000)])
# yıl içi dairesel kaydırmalı gotobi etiketi plasebosu (tüm tasarım tekrar)
days = a.index.unique().sort_values(); gotd = set(a[a.got].index)
lab = np.array([d in gotd for d in days]); yrs = days.year.values
cand = a[(a.pre > 0) & (a.pre > a.thr)].dropna(subset=["net"]).groupby(level=0).net.mean()
pl = []
for _ in range(1000):
    pm = lab.copy()
    for y in np.unique(yrs):
        i = np.where(yrs == y)[0]; pm[i] = np.roll(lab[i], rng.integers(3, len(i) - 3))
    sel = set(days[pm]); v = cand[cand.index.isin(sel)]
    pl.append(v.mean())
pl = np.array(pl)
checks = {
 "1_hacim": {"deger": int(len(ev)), "esik": "≥150", "gecti": len(ev) >= 150},
 "2_beklenti": {"deger": f"net {ev.net.mean():+.2f} bp, P(EV>0)=%{P*100:.1f}", "esik": "ort>0 ve P≥%90", "gecti": bool(ev.net.mean() > 0 and P >= 0.9)},
 "3_kararlilik": {"deger": f"ilk yarı {ev.net[:h].mean():+.2f} son yarı {ev.net[h:].mean():+.2f}; KEŞİF {k.mean():+.2f} KÖR {b.mean():+.2f}", "esik": "ikisi de ≥0", "gecti": bool(ev.net[:h].mean() >= 0 and ev.net[h:].mean() >= 0)},
 "4_surtunme": {"deger": f"maliyet×1,5: {stress:+.2f} bp", "esik": ">0", "gecti": bool(stress > 0)},
 "5_icra": {"deger": f"iyimser (maliyetsiz) {ev.gross.mean():+.2f} vs gerçek {ev.net.mean():+.2f} (fark {ev.cost.mean():.2f})", "esik": "fark < 0,5×gerçek", "gecti": bool(ev.cost.mean() < 0.5 * ev.net.mean())},
 "6_sira_bagimli": {"deger": f"gün başına çift başına tek pozisyon (01→06 UTC), ort {ev.net.mean():+.2f}", "esik": ">0", "gecti": bool(ev.net.mean() > 0)},
}
n_ok = sum(c["gecti"] for c in checks.values())
card = {"scope": "jpy_gotobi_doz_havuz", "tarih": "2026-11-13", "sembol": "USDJPY, EURJPY, GBPJPY, AUDJPY (eşit ağırlık, çift seçimi yok)",
 "kural": "Gotobi günü (5/10/15/20/25/30; hafta sonu/JP tatili → önceki JP iş günü; ay sonu JP iş günü) her JPY çifti için r = open(01:00 UTC) / open(önceki gün 23:00 UTC) − 1. r > 0 VE r > aynı çiftin önceki 250 iş günü 23→01 UTC getirilerinin 67. yüzdeliği ise 01:00 UTC açılışında SAT, 06:00 UTC açılışında kapat. Stop yok (acil SL önerisi 60 bp).",
 "mekanizma": "Tokyo 09:55 gotobi fiksinde zorunlu ithalatçı USD (JPY satışı) alımı fiyatı fiksten önce iter, geçici etki fiks sonrası geri döner; itme büyükse dönüş büyür (ön-kayıtlı EK-6 doz eşiği, nedensel).",
 "ana_olcum": "Pepperstone MT5 H1 2010-10→2026-11; maliyet = max(bar spread, tick spread) + Razor komisyonu ($7/lot RT)",
 "olay_gunu": int(len(ev)), "bacak": int(len(leg)), "isabet": round(float((ev.net > 0).mean() * 100), 1),
 "ort_net_bp": round(float(ev.net.mean()), 2), "ort_brut_bp": round(float(ev.gross.mean()), 2), "ort_maliyet_bp": round(float(ev.cost.mean()), 2),
 "medyan_bp": round(float(ev.net.median()), 2), "en_iyi5_haric_bp": round(float(ev.net.drop(ev.net.abs().nlargest(5).index).mean()), 2),
 "en_kotu_bp": round(float(ev.net.min()), 1), "kontrol_gunleri_bp": round(float(cev.mean()), 2), "P_kontrol_farki": round(float((dd > 0).mean()), 3),
 "plasebo_kaydirma_ort": round(float(pl.mean()), 2), "plasebo_yuzdelik": round(float((pl < ev.net.mean()).mean()), 3),
 "cift_bazinda_bp": leg.groupby("p").net.mean().round(2).to_dict(),
 "yil": {int(y): round(float(v), 2) for y, v in ev.net.groupby(ev.index.year).mean().items()},
 "checks": checks, "gecen": f"{n_ok}/6", "verdikt_kod": "LIVE" if n_ok == 6 else ("SHADOW" if n_ok >= 4 else "RED"),
 "kanit": "research/fx_secim_20261113/ (PROTOCOL.md EK-6, ek6.py, h8cd_kart.py)"}
CARD.write_text(json.dumps(card, ensure_ascii=False, indent=1, default=float))
print(json.dumps({k_: v for k_, v in card.items() if k_ not in ("checks", "kural", "mekanizma", "ana_olcum", "kanit")}, ensure_ascii=False, indent=1))
for kk, c in checks.items(): print(kk, c["gecti"], c["deger"])
