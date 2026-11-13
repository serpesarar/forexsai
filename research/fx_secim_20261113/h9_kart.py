"""FX-01 EK-5 H9 ay sonu Londra fiksi dönüş sepeti — sonuçlar + kart. Çalıştır: ../../.venv/bin/python -I h9_kart.py"""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fx_core as f, hyp
TS = json.loads((f.DATA / "tick_spread.json").read_text())["sp"]
COMM = {"EURUSD": 0.60, "GBPUSD": 0.53, "USDJPY": 0.70, "USDCHF": 0.70, "USDCAD": 0.70, "AUDUSD": 1.07}
CARD = f.ROOT / "backend/data/evolution/go_live_cards/fx_aysonu_fiks_donus.json"

def table() -> pd.DataFrame:
    me = set(hyp.last_bdays("2010-11-01", "2026-10-31"))
    rows = []
    for d in hyp.bdays("2010-11-01", "2026-11-12"):
        for p in COMM:
            pre = hyp.trade(p, hyp.london(d, 10), hyp.london(d, 16), +1)
            if pre is None or pre["gross"] == 0:
                continue
            side = -1 if pre["gross"] > 0 else 1
            r = hyp.trade(p, hyp.london(d, 16), hyp.london(d, 20), side)
            if r is None:
                continue
            sh = (TS.get(p) or {}).get("saat", {})
            tc = np.mean([sh.get(str(h), [0])[0] for h in (15, 16, 19, 20)]) if sh else 0.0
            c = max(r["gross"] - r["net"], tc) + COMM[p]
            rows.append({"d": d, "p": p, "me": d in me, "pre": abs(pre["gross"]), "gross": r["gross"], "net": r["gross"] - c, "cost": c, "icra": r["icra_fark"]})
    return pd.DataFrame(rows)

if __name__ == "__main__":
    x = table(); x.to_parquet(f.RES / "h9_tablo.parquet")
    m = x[x.me]
    ev = m.groupby("d").agg(net=("net", "mean"), gross=("gross", "mean"), cost=("cost", "mean"), icra=("icra", "mean"))
    ctl = x[~x.me].groupby("d").net.mean()
    h = len(ev) // 2; P = f.boot_p(ev.net.values)
    k, b = ev[ev.index < f.SPLIT].net, ev[ev.index >= f.SPLIT].net
    stress = (ev.gross - 1.5 * ev.cost).mean()
    checks = {
     "1_hacim": {"deger": int(len(ev)), "esik": "≥150", "gecti": len(ev) >= 150},
     "2_beklenti": {"deger": f"net {ev.net.mean():+.2f} bp, P(EV>0)=%{P*100:.1f}", "esik": "ort>0 ve P≥%90", "gecti": bool(ev.net.mean() > 0 and P >= 0.9)},
     "3_kararlilik": {"deger": f"ilk yarı {ev.net[:h].mean():+.2f} son yarı {ev.net[h:].mean():+.2f}; KEŞİF {k.mean():+.2f} KÖR {b.mean():+.2f}", "esik": "ikisi de ≥0", "gecti": bool(ev.net[:h].mean() >= 0 and ev.net[h:].mean() >= 0)},
     "4_surtunme": {"deger": f"maliyet×1,5: {stress:+.2f} bp", "esik": ">0", "gecti": bool(stress > 0)},
     "5_icra": {"deger": f"iyimser (maliyetsiz) {ev.gross.mean():+.2f} vs gerçek {ev.net.mean():+.2f} (fark {ev.gross.mean() - ev.net.mean():.2f}; zamanlama {ev.icra.mean():+.2f})", "esik": "fark < 0,5×gerçek", "gecti": bool(ev.gross.mean() - ev.net.mean() < 0.5 * ev.net.mean())},
     "6_sira_bagimli": {"deger": f"ay sonu başına çift başına tek pozisyon (16→20 Londra), ort {ev.net.mean():+.2f}", "esik": ">0", "gecti": bool(ev.net.mean() > 0)},
    }
    n_ok = sum(c["gecti"] for c in checks.values())
    rng = np.random.default_rng(3)
    dd = np.array([rng.choice(ev.net.values, len(ev)).mean() - rng.choice(ctl.values, len(ctl)).mean() for _ in range(3000)])
    x["q"] = x.groupby("p").pre.transform(lambda v: pd.qcut(v, 3, labels=False))
    card = {"scope": "fx_aysonu_fiks_donus", "tarih": "2026-11-13", "sembol": "EURUSD,GBPUSD,USDJPY,USDCHF,USDCAD,AUDUSD (eşit ağırlık sepet)",
     "kural": "Ayın son iş günü her çift için 10:00→16:00 Londra getirisi r; 16:00 Londra H1 açılışında −sign(r) yönünde gir, 20:00 Londra açılışında çık. Stop yok. Yılda 12 olay × 6 bacak.",
     "mekanizma": "Ay sonu WM/R 16:00 fiksinde zorunlu dengeleme akışı (hedge/endeks/portföy) fiyatı fiks öncesi iter; geçici etki fiks sonrası geri döner (Melvin-Prins 2015, Evans 2018). Normal günlerde aynı kural eksi (devam) → ayrım ay sonuna özgü.",
     "ana_olcum": "Pepperstone MT5 H1 2010-11→2026-10 (kutu, salt-okuma); maliyet = max(bar spread, 2026-11 tick spread'i) + Razor komisyonu",
     "olay": int(len(ev)), "aralik": [str(ev.index.min().date()), str(ev.index.max().date())], "isabet": round(float((ev.net > 0).mean() * 100), 1),
     "ort_net_bp": round(float(ev.net.mean()), 2), "ort_brut_bp": round(float(ev.gross.mean()), 2), "medyan_bp": round(float(ev.net.median()), 2),
     "en_iyi5_haric_bp": round(float(ev.net.drop(ev.net.abs().nlargest(5).index).mean()), 2), "en_kotu_bp": round(float(ev.net.min()), 1),
     "kontrol_gunleri_bp": round(float(ctl.mean()), 2), "kontrol_farki": round(float(ev.net.mean() - ctl.mean()), 2), "P_fark": round(float((dd > 0).mean()), 3),
     "cift_bazinda_bp": m.groupby("p").net.mean().round(2).to_dict(), "doz_tepki_ay_sonu": x[x.me].groupby("q").net.mean().round(2).to_dict(),
     "doz_tepki_kontrol": x[~x.me].groupby("q").net.mean().round(2).to_dict(),
     "yil": {int(y): round(float(v), 1) for y, v in ev.net.groupby(ev.index.year).mean().items()},
     "checks": checks, "gecen": f"{n_ok}/6", "verdikt_kod": "LIVE" if n_ok == 6 else ("SHADOW" if n_ok >= 4 else "RED"), "verdikt_onerilen": "SHADOW",
     "neden_shadow": "Ön-kayıtlı (EK-5) ve mekanizmalı, ama kenar maliyete ince (5. ölçüt) ve yılda yalnız 12 karar günü; ileri gölge + Dukascopy teyidi bekliyor.",
     "kanit": "research/fx_secim_20261113/ (PROTOCOL.md EK-5, h9_kart.py, RAPOR.md)"}
    CARD.write_text(json.dumps(card, ensure_ascii=False, indent=1, default=float))
    print(json.dumps({k: card[k] for k in ("olay", "ort_net_bp", "ort_brut_bp", "isabet", "medyan_bp", "en_iyi5_haric_bp", "kontrol_farki", "P_fark", "gecen", "verdikt_kod", "yil")}, ensure_ascii=False))
    for kk, c in checks.items(): print(kk, c["gecti"], c["deger"])
