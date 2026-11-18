"""kart.py — B çıkan "geniş fitilli KSG" (2h fitil %0,50, W 12 sa, 15:00→15:30 aşağı, 15:30 AL, ertesi 16:00 çık) 2. KURAL kartı + risk."""
from __future__ import annotations

import json
from datetime import datetime

import numpy as np
import pandas as pd

import gece as G
import gece_run as R

OUT = G.ROOT / "backend/data/evolution/go_live_cards/ndx_ksg_fitil_genis.json"


def trades(d, entry_min: int, exit_min: int, tz="America/New_York", step=60):
    dp = G.day_prices(d, tz, sorted({entry_min, exit_min, G.KSG_REF, entry_min + 1}), step)
    nt = G.nights(dp, entry_min, exit_min, G.KSG_REF, G.nyse_ok)
    e = G.wick_ends(d, tz, 7200, 0.50, step)
    m = G.tag(nt.t_in.values, e, 12 * 3600) & (nt.ksg_ret < 0).values
    return nt, nt[m].reset_index(drop=True)


def main() -> None:
    d = G.ndx_bars()
    nt, x = trades(d, 930, 960)
    _, xd = trades(d, 931, 960)                               # icra: 15:31 açılışı
    # tek pozisyon: önceki çıkış (ertesi 16:00) sonraki girişten (15:30) sonra → çakışanı atla
    keep, busy = [], -1
    for r in x.itertuples():
        if r.t_in >= busy:
            keep.append(r.Index)
            busy = r.t_in + 25 * 3600
    xs = x.loc[keep]
    h = len(x) // 2
    P = G.lib.block_boot_p(x.net_bp.values, pd.to_datetime(x.d).dt.to_period("M").astype(str).values)
    checks = {"1_hacim": {"deger": len(x), "gecti": len(x) >= 150},
              "2_beklenti": {"deger": f"{x.net_bp.mean():+.1f} bp, ay-blok P {P:.3f}", "gecti": bool(x.net_bp.mean() > 0 and P >= 0.9)},
              "3_kararlilik": {"deger": f"{x.net_bp.iloc[:h].mean():+.1f} / {x.net_bp.iloc[h:].mean():+.1f}",
                               "gecti": bool(x.net_bp.iloc[:h].mean() >= 0 and x.net_bp.iloc[h:].mean() >= 0)},
              "4_surtunme": {"deger": f"spread×1,5 {x.net_bp_s15.mean():+.1f}", "gecti": bool(x.net_bp_s15.mean() > 0)},
              "5_icra": {"deger": f"15:30 {x.net_bp.mean():+.1f} vs 15:31 {xd.net_bp.mean():+.1f}",
                         "gecti": bool(x.net_bp.mean() - xd.net_bp.mean() < 0.5 * abs(xd.net_bp.mean()) and xd.net_bp.mean() > 0)},
              "6_sira_bagimli": {"deger": f"tek pozisyon {xs.net_bp.mean():+.1f} (n {len(xs)})", "gecti": bool(xs.net_bp.mean() > 0)}}
    v = x.net_bp.values
    risk = {"std_bp": round(float(v.std()), 1), "en_kotu_bp": round(float(v.min()), 1), "en_iyi_bp": round(float(v.max()), 1),
            "medyan_bp": round(float(np.median(v)), 1), "isabet": round(float((v > 0).mean()), 3),
            "en_iyi_5_haric_bp": round(float((v.sum() - np.sort(v)[-5:].sum()) / (len(v) - 5)), 1),
            "kotu_yuzde5_bp": round(float(np.percentile(v, 5)), 1),
            "kumulatif_maxDD_bp": round(float((np.cumsum(v) - np.maximum.accumulate(np.cumsum(v))).min()), 1)}
    yil = {int(y): {"n": int(len(g)), "bp": round(float(g.net_bp.mean()), 1)} for y, g in x.groupby(pd.to_datetime(x.d).dt.year)}
    val = json.loads((R.RES / "dogrulama.json").read_text())
    vrow = next(r for r in val if r["hucre"]["tf"] == "2h" and r["hucre"]["w"] == "12h" and r["hucre"]["exit"] == "16:00")
    card = {"scope": "ndx_ksg_fitil_genis",
            "aciklama": "Geniş fitilli KSG: son 12 sa içinde kapanmış bir NY-hizalı 2h mumda alt fitil ≥ fiyatın %0,50'si ∧ üst ≤ alt/2, "
                        "ve 15:00→15:30 getirisi < 0 → 15:30'da AL (ask), ertesi işlem günü 16:00 açılışında çık. Stopsuz zaman işlemi.",
            "tarih": datetime.now().isoformat(timespec="seconds"),
            "ana_olcum": "Dukascopy NDX 1m 2018-01 → 2026-11 (lib.load_m1), giriş 15:30 açılışı + spread, çıkış ertesi 16:00 açılışı, gecelik finansman",
            "olay": len(x), "ort_bp": round(float(x.net_bp.mean()), 1), "fitilsiz_taban_bp": vrow["TUM"].get("taban"), "yillar": yil, "risk": risk,
            "checks": checks, "kart_6_6": all(c["gecti"] for c in checks.values()),
            "secim": "ESKİ 2018-21'de 324 hücrelik ızgaradan (plasebo üstü) seçildi; YENİ 2021-26 kör +41,1 vs −0,6 bp P 0,988 (Bonferroni 0,98 geçti)",
            "bagimsiz": vrow["beslemeler"], "verdict": "SHADOW", "sinif": "B",
            "verdict_gerekce": "Ön kayıtlı genişletme ölçütlerinin hepsi geçti (YENİ Bonferroni, MT5+EET30+NQ her biri fitilli>0 ve >taban, s×1,5, n≥150). "
                               "DAX'a taşınmıyor (G7 −22,7 bp) → ABD/NDX'e özgü. Stopsuz ~24 sa tutuş: risk bölümüne bak. Canlı kararı kullanıcıda.",
            "kanit": "research/fitil_gece_20261118/RAPOR.md"}
    OUT.write_text(json.dumps(card, indent=1, ensure_ascii=False, default=str))
    print(json.dumps({k: card[k] for k in ("olay", "ort_bp", "kart_6_6", "risk")}, ensure_ascii=False))
    print({k: (c["deger"], c["gecti"]) for k, c in checks.items()})
    print(yil)


if __name__ == "__main__":
    main()
