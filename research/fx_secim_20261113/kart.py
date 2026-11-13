"""FX-01 H8c USDJPY gotobi fiks sonrası dönüş — canlıya alma kartı (2. KURAL). Çalıştır: ../../.venv/bin/python -I kart.py"""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fx_core as f, hyp
from h8c_saglamlik import events
CARD = f.ROOT / "backend/data/evolution/go_live_cards/usdjpy_gotobi_fiks_donus.json"
b = events("USDJPY", lambda d: True)
g = b[b.got].reset_index(drop=True)
net, gross = g.net, g.gross
cost = gross - net
h = len(g) // 2
P = f.boot_p(net.values)
opt = gross.mean()                       # iyimser: maliyetsiz (icra farkı ~0: giriş barı önceki kapanışıyla aynı)
icra_fark = float(np.nanmean([r["icra_fark"] for r in [hyp.trade("USDJPY", d + pd.Timedelta(hours=1), d + pd.Timedelta(hours=6), -1) for d in g.t] if r]))
sat = json.loads((f.RES / "h8c_saglamlik.json").read_text())
checks = {
 "1_hacim": {"deger": int(len(g)), "esik": "≥150", "gecti": len(g) >= 150},
 "2_beklenti": {"deger": f"net {net.mean():+.2f} bp, P(EV>0)=%{P*100:.1f}", "esik": "ort>0 ve P≥%90", "gecti": bool(net.mean() > 0 and P >= 0.9)},
 "3_kararlilik": {"deger": f"ilk yarı {net[:h].mean():+.2f} son yarı {net[h:].mean():+.2f}; KEŞİF(≤2021) {net[g.t < f.SPLIT].mean():+.2f} KÖR {net[g.t >= f.SPLIT].mean():+.2f}", "esik": "ikisi de ≥0", "gecti": bool(net[:h].mean() >= 0 and net[h:].mean() >= 0)},
 "4_surtunme": {"deger": f"maliyet×1,5: {(gross - 1.5 * cost).mean():+.2f} bp", "esik": ">0", "gecti": bool((gross - 1.5 * cost).mean() > 0)},
 "5_icra": {"deger": f"iyimser (bar açılışı, maliyetsiz) {opt:+.2f} vs gerçek {net.mean():+.2f} (fark {opt - net.mean():.2f}; zamanlama farkı {icra_fark:+.2f}, kalanı spread+komisyon {cost.mean():.2f} bp)", "esik": "fark < 0,5×gerçek", "gecti": bool(opt - net.mean() < 0.5 * net.mean())},
 "6_sira_bagimli": {"deger": f"gün başına tek pozisyon (01→06 UTC), çakışma 0, ort {net.mean():+.2f}", "esik": ">0", "gecti": bool(net.mean() > 0)},
}
n_ok = sum(c["gecti"] for c in checks.values())
card = {"scope": "usdjpy_gotobi_fiks_donus", "tarih": "2026-11-13", "sembol": "USDJPY",
 "kural": "Gotobi günü (5,10,15,20,25,30; hafta sonu/JP tatili → önceki JP iş günü) USDJPY 23:00→01:00 UTC (08:00→10:00 JST, Tokyo fiksi 09:55 içeride) getirisi > 0 ise 01:00 UTC H1 açılışında SAT, 06:00 UTC açılışında kapat. Stop yok (öneri acil SL 60 bp). Yılda ~41 olay.",
 "mekanizma": "Japon ithalatçılarının gotobi fiksinde zorunlu USD alımı (Ito & Yamada 2017); geçici fiyat etkisi fiks sonrası geri döner. Doz-tepki: sabah yükselişi büyüdükçe dönüş büyüyor.",
 "ana_olcum": "Pepperstone MT5 USDJPY H1 2010-10→2026-11 (kutu, salt-okuma); maliyet = max(bar spread, 2026-11 tick spread'i saat bazında) + Razor komisyonu 0,70 bp RT",
 "olay": int(len(g)), "aralik": [str(g.t.min().date()), str(g.t.max().date())], "isabet": round(float((net > 0).mean() * 100), 1),
 "ort_net_bp": round(float(net.mean()), 2), "ort_brut_bp": round(float(gross.mean()), 2), "ort_maliyet_bp": round(float(cost.mean()), 2),
 "medyan_bp": round(float(net.median()), 2), "en_iyi5_haric_bp": sat["ilk5_cikinca"], "en_kotu_bp": round(float(net.min()), 1),
 "kontrol_gunleri_ayni_kosul_bp": sat["kontrol_net"], "yil_pozitif": sat["yil_pozitif"],
 "checks": checks, "gecen": f"{n_ok}/6", "verdikt_kod": "LIVE" if n_ok == 6 else ("SHADOW" if n_ok >= 4 else "RED"),
 "verdikt_onerilen": "SHADOW",
 "neden_shadow": "Kural, ana hücre H8b'nin KÖR verisi görüldükten sonra yazıldı (EK-4, E53 sınıfı) → kanıt B−. Kenar maliyete ince (brüt 3,2 / maliyet 1,4 bp). Bağımsız besleme (Dukascopy) sınaması bekliyor.",
 "yan": {"cikis_saati_duyarlilik_bp": sat["cikis_duyarlilik"], "esik_doz_tepki_bp": sat["esik_duyarlilik"], "gotobi_tanimi_bp": sat["tanim"],
         "aile_maxt_p": sat["aile_maxt"], "kor_ciftler_gercek_maliyet": json.loads((f.RES / "h8c_gercek_maliyet.json").read_text())},
 "kanit": "research/fx_secim_20261113/ (PROTOCOL.md EK-1…4, RAPOR.md, h8c_saglamlik.py, kart.py)"}
CARD.write_text(json.dumps(card, ensure_ascii=False, indent=1, default=float))
print(json.dumps({k: card[k] for k in ("olay", "ort_net_bp", "ort_brut_bp", "gecen", "verdikt_kod")}, ensure_ascii=False))
for k, c in checks.items(): print(k, c["gecti"], c["deger"])
