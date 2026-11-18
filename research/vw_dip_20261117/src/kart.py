"""kart.py — en güçlü aday (W1b ∧ düşüş ≥ %1,5 ∧ VIX ≥ 18,4, TP 2R, ertesi gün 16:00) için 2. KURAL kartı.

Hüküm ön kayıttan: Bonferroni TEST eşiği geçilmediği için LIVE olamaz → SHADOW. Kart tüm Dukascopy 2018-26 üzerinde hesaplanır
(proje kart standardı); KEŞİF'te seçildiği için tam-örneklem değerleri iyimserdir, TEST ve MT5 satırları ayrıca yazılır.
"""
from __future__ import annotations

import json
from datetime import datetime

import numpy as np
import pandas as pd

import vw  # noqa: I001
import kesif as KS
import dogrulama as DG

CELL = {"typ": "W1b", "drop": "d1.5", "vix": "v18.4", "tp": 2.0, "time": "D1_16"}
OUT = vw.ROOT / "backend/data/evolution/go_live_cards/ndx_vw_w1b_vix.json"


def main() -> None:
    e = pd.read_parquet(KS.CACHE / "girisler.parquet")
    e = e[e.typ == "W1b"].reset_index(drop=True)
    p = vw.duka_path_stable()
    x = DG.cell_rows(vw.evaluate_all(p, e), e, CELL)
    xo = DG.cell_rows(vw.evaluate_all(p, e, optimistic=True), e, CELL)
    xs = DG.single(x)
    s = DG.summ(x)
    era = e.era.values[x.e.values]
    val = json.loads((KS.RES / "dogrulama.json").read_text())
    v = next(a for a in val["adaylar"] if a["aday"]["typ"] == "W1b" and a["aday"]["vix"] == "v18.4")
    checks = {
        "1_hacim": {"deger": s["n"], "esik": "≥150", "gecti": s["n"] >= 150},
        "2_beklenti": {"deger": f"ortR {s['mean']:+.3f} P {s['P_kume']}", "esik": "ortR>0 ve P≥%90", "gecti": bool(s["mean"] > 0 and s["P_kume"] >= 0.9)},
        "3_kararlilik": {"deger": f"ilk {s['h1']:+.3f} son {s['h2']:+.3f}", "esik": "ikisi ≥0", "gecti": bool(s["h1"] >= 0 and s["h2"] >= 0)},
        "4_surtunme": {"deger": f"spread×1,5 {s['mean15']:+.3f}", "esik": ">0", "gecti": bool(s["mean15"] > 0)},
        "5_icra": {"deger": f"iyimser {xo.R.mean():+.3f} vs gerçek {s['mean']:+.3f}", "esik": "fark < 0,5×|gerçek|",
                   "gecti": bool(xo.R.mean() - s["mean"] < 0.5 * abs(s["mean"]))},
        "6_sira_bagimli": {"deger": f"tek pozisyon {xs.R.mean():+.3f} (n {len(xs)})", "esik": ">0", "gecti": bool(xs.R.mean() > 0)},
    }
    card = {
        "scope": "ndx_vw_w1b_vix",
        "aciklama": "NDX 3,5 sa alt fitil ≥ %0,50 ∧ üst ≤ alt/2 (NY 17:00 ızgarası) → mum kapanışından sonra 96 adet 15m içinde ikinci dip "
                    "(fraktal, L1'in −%0,25…+%0,40'ı, boyun ≥ L1+%0,30) teyidinde AL; 2 günlük tepeden düşüş ≥ %1,5; dünkü VIX ≥ 18,4; "
                    "stop min(L1,L2)−%0,10, TP 2R, çıkış ertesi işlem günü NY 16:00.",
        "tarih": datetime.now().isoformat(timespec="seconds"),
        "ana_olcum": "Dukascopy NDX 1m 2018-01 → 2026-11, giriş sonraki 1m açılışı + spread, TP/SL 1m'de, aynı bar → stop",
        "olay": s["n"], "gun": s["gun"], "wr": round(100 * s["hit"], 1), "ort_R": s["mean"], "en_iyi_5_haric": s["ex_top5"],
        "yillar": s["yil"], "KESIF": {"n": int((era == "KESIF").sum()), "ort_R": round(float(x.R[era == "KESIF"].mean()), 3)},
        "TEST": v["TEST"], "MT5_bagimsiz": v["MT5"], "plasebo_fark_P": v["P_plasebo_fark"],
        "checks": checks, "kart_6_6": all(c["gecti"] for c in checks.values()),
        "verdict": "SHADOW",
        "verdict_gerekce": ("KEŞİF'te 720 hücrelik şans düzeyindeki ızgaradan seçildi (plasebo yüzdeliği %80); kör TEST +0,192R ama "
                            "küme P %94,9 < Bonferroni %98; MT5 +0,121R; 2025–26 iki beslemede eksi; başka endekslere taşınmadı (1/4). "
                            "Tam-örneklem kart seçim yanlılığı taşır. Canlıya alma yok; ileri gölge kaydı önerilir."),
        "kanit": "research/vw_dip_20261117/RAPOR.md",
    }
    OUT.write_text(json.dumps(card, indent=1, ensure_ascii=False, default=str))
    print(json.dumps({k: card[k] for k in ("olay", "ort_R", "kart_6_6", "verdict")}, ensure_ascii=False),
          {k: c["gecti"] for k, c in checks.items()})


if __name__ == "__main__":
    main()
