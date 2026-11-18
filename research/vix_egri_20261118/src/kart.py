"""kart.py — ters VIX eğrisi (d−1 VIX/VIX3M ≥ 1) → d 09:30 AL, d+4 16:00 çık: tek pozisyon, epizotlar, risk, 2. KURAL kartı."""
from __future__ import annotations

import json
from datetime import datetime

import numpy as np
import pandas as pd

import ve

OUT = ve.ROOT / "backend/data/evolution/go_live_cards/ndx_vix_ters_egri_5g.json"


def summarize(x: pd.DataFrame) -> dict:
    v = x.net_bp.values
    cs = np.cumsum(v)
    return {"n": int(len(v)), "ort_bp": round(float(v.mean()), 1), "medyan_bp": round(float(np.median(v)), 1),
            "isabet": round(float((v > 0).mean()), 3), "en_kotu_bp": round(float(v.min()), 1), "std_bp": round(float(v.std()), 1),
            "en_iyi_5_haric_bp": round(float((v.sum() - np.sort(v)[-5:].sum()) / max(1, len(v) - 5)), 1),
            "maxDD_bp": round(float((cs - np.maximum.accumulate(cs)).min()), 1),
            "yillar": {int(y): {"n": int(len(g)), "bp": round(float(g.net_bp.mean()), 1)} for y, g in x.groupby(pd.to_datetime(x.d).dt.year)}}


def main():
    d = ve.G.ndx_bars()
    T = ve.trades(d, 60)
    df, ms = T["+4_16:00"]
    m = ms[("S2", 1.00)]
    x = df[m].sort_values("t_in").reset_index(drop=True)
    # tek pozisyon: 5 işlem günü tutuş → sonraki giriş önceki çıkıştan sonra
    days = sorted(df.d.unique())
    pos = {dd: i for i, dd in enumerate(days)}
    keep, busy = [], -1
    for r in x.itertuples():
        if pos[r.d] > busy:
            keep.append(r.Index)
            busy = pos[r.d] + 4
    xs = x.loc[keep].reset_index(drop=True)
    # epizot: ardışık (≤ 3 işlem günü arayla) sinyal günleri
    ep, last = 0, -99
    for dd in x.d:
        if pos[dd] - last > 3:
            ep += 1
        last = pos[dd]
    # icra: 09:31 açılışı
    dp = ve.G.day_prices(d, ve.TZ, [960], 60)
    tt = d.t.values
    xd = []
    for r in xs.itertuples():
        i, j = pos[r.d], int(np.searchsorted(tt, r.t_in + 60))      # 09:31 (girişten 1 dk sonra) açılışı
        if i + 4 < len(days) and j < len(tt) and tt[j] - r.t_in <= 360 and days[i + 4] in dp.index and np.isfinite(dp.loc[days[i + 4]].o960):
            pin = d.o.values[j] + d.sp.values[j]
            xd.append((dp.loc[days[i + 4]].o960 / pin - 1) * 1e4 - ve.G.lib.FIN_BP_PER_DAY * (days[i + 4] - r.d).days)
    xd = np.array(xd)
    s_all, s_one = summarize(x), summarize(xs)
    h = len(xs) // 2
    P = ve.G.lib.block_boot_p(xs.net_bp.values, pd.to_datetime(xs.d).dt.to_period("M").astype(str).values)
    checks = {"1_hacim": {"deger": f"{len(x)} işlem / {len(xs)} tek pozisyon / {ep} epizot", "gecti": len(x) >= 150},
              "2_beklenti": {"deger": f"tek poz {xs.net_bp.mean():+.1f} bp P {P:.3f}", "gecti": bool(xs.net_bp.mean() > 0 and P >= 0.9)},
              "3_kararlilik": {"deger": f"{xs.net_bp.iloc[:h].mean():+.1f} / {xs.net_bp.iloc[h:].mean():+.1f}",
                               "gecti": bool(xs.net_bp.iloc[:h].mean() >= 0 and xs.net_bp.iloc[h:].mean() >= 0)},
              "4_surtunme": {"deger": f"{xs.net_bp_s15.mean():+.1f}", "gecti": bool(xs.net_bp_s15.mean() > 0)},
              "5_icra": {"deger": f"09:30 {xs.net_bp.mean():+.1f} vs 09:31 {xd.mean():+.1f}",
                         "gecti": bool(xs.net_bp.mean() - xd.mean() < 0.5 * abs(xd.mean()) and xd.mean() > 0)},
              "6_sira_bagimli": {"deger": f"tek pozisyon {xs.net_bp.mean():+.1f} (n {len(xs)})", "gecti": bool(xs.net_bp.mean() > 0)}}
    val = json.loads((ve.RES / "dogrulama.json").read_text())
    v = next(r for r in val if r["hucre"]["S"] == "S2" and r["hucre"]["cikis"] == "+4_16:00")
    card = {"scope": "ndx_vix_ters_egri_5g", "tarih": datetime.now().isoformat(timespec="seconds"),
            "aciklama": "Dünkü kapanışta VIX ≥ VIX3M (ters vade eğrisi) → bugün NDX 09:30 AL, 5. işlem günü (d+4) 16:00 çık. Stopsuz 5 günlük tutuş.",
            "ana_olcum": "Dukascopy NDX 1m 2018-01 → 2026-11, giriş 09:30 açılışı + spread, çıkış d+4 16:00 açılışı, finansman",
            "tum_sinyaller": s_all, "tek_pozisyon": s_one, "epizot": ep, "checks": checks,
            "kart_6_6": all(c["gecti"] for c in checks.values()), "YENI": v["YENI"], "beslemeler": v["beslemeler"],
            "K1_ortusme": v["K1_ortusme"], "K1_disi": v["K1_disi"], "verdict": "SHADOW", "sinif": "C+",
            "verdict_gerekce": "Ön kayıt ölçütleri (YENİ kör +137,9 vs +6,3 bp P 0,995, MT5/EET30/NQ, n 163) B diyor; ama tek pozisyonda yalnız 55 işlem / 37 bağımsız epizot, en iyi 5 hariç +13,9 bp, en kötü −1.578 bp, birikimli maxDD −2.982 bp (−%30), 2018/2020/2025 eksi → kuyruk riski kabul edilemez; sınıf C+'ya indirildi. Canlıya uygun değil; ancak felaket stoplu / küçük lotlu bir sürüm ön kayıtla ayrıca sınanabilir.",
            "kanit": "research/vix_egri_20261118/RAPOR.md"}
    OUT.write_text(json.dumps(card, indent=1, ensure_ascii=False, default=str))
    print("tüm", s_all, "\ntek poz", s_one, "\nepizot", ep, "\n", {k: (c["deger"], c["gecti"]) for k, c in checks.items()})


if __name__ == "__main__":
    main()
