"""kart.py — 2. KURAL kartı: ORB × VIX, TP 3R (canlı geometri 2026-11-16). Çıktı backend/data/evolution/go_live_cards/ndx_orb_vix_tp3.json"""
from __future__ import annotations

import json
from datetime import datetime

import numpy as np

import lib
import rules

OUT = lib.ROOT / "backend/data/evolution/go_live_cards/ndx_orb_vix_tp3.json"


def ci95(v: np.ndarray, months: np.ndarray, n: int = 4000, seed: int = 9) -> list[float]:
    um = np.unique(months)
    groups = [v[months == u] for u in um]
    sums, cnts = np.array([g.sum() for g in groups]), np.array([len(g) for g in groups])
    pick = np.random.default_rng(seed).integers(0, len(um), (n, len(um)))
    m = sums[pick].sum(1) / cnts[pick].sum(1)
    return [round(float(np.percentile(m, 2.5)), 3), round(float(np.percentile(m, 97.5)), 3)]


def main() -> None:
    m1 = lib.load_m1()
    D = lib.daily_table(m1)
    vixp = lib.vix_prev_map(D.d.tolist())
    df = lib.to_frame(rules.orb(m1, D, vixp, tp_r=3.0)).sort_values("t_in").reset_index(drop=True)
    opt = lib.to_frame(rules.orb(m1, D, vixp, tp_r=3.0, optimistic=True))
    two = lib.to_frame(rules.orb(m1, D, vixp, tp_r=2.0))
    lo = lib.to_frame(rules.orb(m1, D, vixp, tp_r=3.0, arm="lo"))
    s = lib.summarize(df, "R")
    h = len(df) // 2
    y1, y2 = float(df.R.iloc[:h].mean()), float(df.R.iloc[h:].mean())
    mo = df.d.astype(str).str[:7].values
    yil = {int(y): round(float(g.R.mean()), 3) for y, g in df.groupby("year")}
    card = {
        "scope": "ndx_orb_vix_tp3",
        "aciklama": "NDX 09:30 ET ilk 15 dk aralığı; önceki gün VIX ≥ 18,4; 5m kapanış aralık tepesinin üstünde (bar bitişi ≤ 15:30) → "
                    "sonraki 5m açılışında BUY (ask); stop aralık ortası, hedef **3R**, 15:55 ET zaman çıkışı, günde ≤1. "
                    "ndx_orb_vix.json'dan tek fark hedef 2R → 3R.",
        "tarih": datetime.now().isoformat(timespec="seconds"),
        "sembol": "NAS100 (ölçüm Dukascopy USATECHIDXUSD)",
        "ana_olcum": "Dukascopy BID 1m 2018-01-02 → 2026-11-13, spread = NY-saati bp modeli (2025 gözlenen), stop/TP 1m'de, aynı bar → stop",
        "olay": s["n"], "aralik": [str(df.d.min()), str(df.d.max())], "wr": round(100 * s["hit"], 1),
        "ort_R": round(s["mean"], 3), "toplam_R": round(s["sum"], 1), "en_iyi_5_haric_ort": round(s["ex_top5"], 3),
        "bootstrap_%95": ci95(df.R.values, mo), "yillar": yil, "yillar_pozitif": f"{sum(v > 0 for v in yil.values())}/{len(yil)}",
        "checks": {
            "1_hacim": {"deger": s["n"], "esik": "≥150", "gecti": s["n"] >= 150},
            "2_beklenti": {"deger": f"ortR=+{s['mean']:.3f} P(EV>0)=%{100 * s['P']:.1f}", "esik": "ortR>0 ve P≥%90",
                           "gecti": bool(s["mean"] > 0 and s["P"] >= 0.90)},
            "3_kararlilik": {"deger": f"ilk={y1:+.3f} son={y2:+.3f}", "esik": "ikisi de ≥0", "gecti": bool(y1 >= 0 and y2 >= 0)},
            "4_surtunme": {"deger": f"spread×1,5 {s['mean_s15']:+.3f}", "esik": ">0", "gecti": bool(s["mean_s15"] > 0)},
            "5_icra": {"deger": f"tetik barı kapanışı (spreadsiz) {opt.R.mean():+.3f} vs gerçek {s['mean']:+.3f}",
                       "esik": "fark < 0,5×|gerçek ortR|", "gecti": bool(opt.R.mean() - s["mean"] < 0.5 * abs(s["mean"]))},
            "6_sira_bagimli": {"deger": f"günde ≤1, gün içi, tek pozisyon yapısal: {s['mean']:+.3f}", "esik": ">0", "gecti": bool(s["mean"] > 0)},
        },
        "donemler": {e: {k: round(v, 3) if isinstance(v, float) else v for k, v in lib.summarize(df[df.era == e], "R").items()
                         if k in ("n", "mean", "P", "hit")} for e in ("ESKI", "YENI")},
        "kiyas": {"TP2R_ayni_motor": round(float(two.R.mean()), 3), "VIX_alti_kol_TP3R": round(float(lo.R.mean()), 3),
                  "TP2R_yillar": {int(y): round(float(g.R.mean()), 3) for y, g in two.groupby("year")}},
        "uyarilar": [
            "Hedef seçimi sonradan: B1 komşuluk haritasında (72 hücre) 3R iki dönemde de 2R'yi geçti (fark P 0,999/0,995), EK1-a çıkış "
            "eğrisinde 2R en kötü nokta, 3R/4R/5R/TP'siz hepsi üstün — tek hücre değil plato. Yine de seçim örneklem içinde.",
            "2026 zayıf (+0,108R, n 62); 2022 ayı piyasası +0,053R.",
            "Eski 10 yıl iddiası (+0,185R, 2R) 2016-21'de 1h geometrisindendi; gerçek 5m geometrisiyle 2R 2018-26 +0,101R.",
            "Dukascopy fiyatı broker NAS100'den sabit olmayan düzey farkı taşır (FAZ_0); R ölçüsü düzeyden bağımsızdır.",
        ],
        "verdikt": "LIVE",
        "not": "Kullanıcı isteği 2026-11-16 'uygulamaya geç'; orb_vix_live.TP_R_LIVE = 3.0, eski davranış config.ORB_VIX_LIVE_TP_R = 2.0. "
               "Durdurma ölçütü (önceden yazılı): canlı n=60 işlemde ort R < 0 → 2R'ye dön ve yeniden değerlendir.",
    }
    ok = all(c["gecti"] for c in card["checks"].values())
    card["verdikt"] = "LIVE" if ok else "SHADOW"
    OUT.write_text(json.dumps(card, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(card, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
