"""kart.py — B çıkan K1 (TWAP altı ∧ KSG, 16:00→ertesi 16:00) ve K3 (son saat ≤ −%0,3, 16:00→ertesi 16:00) için 2. KURAL kartları,
risk ve örtüşme (geniş fitilli KSG ile)."""
from __future__ import annotations

import json
from datetime import datetime

import numpy as np
import pandas as pd

import korku as K
import gece as G

CARDS = {"K1": ("ndx_korku_twap", ("K1", 0.5), True), "K3": ("ndx_korku_sonsaat", ("K3", 0.3), False)}


def stats(x: pd.DataFrame, xd: pd.DataFrame) -> tuple[dict, dict]:
    h = len(x) // 2
    v = x.net_bp.values
    P = G.lib.block_boot_p(v, pd.to_datetime(x.d).dt.to_period("M").astype(str).values)
    keep, busy = [], -1
    for r in x.itertuples():
        if r.t_in >= busy:
            keep.append(r.Index)
            busy = r.t_in + 24 * 3600 + 60
    xs = x.loc[keep]
    checks = {"1_hacim": {"deger": len(x), "gecti": len(x) >= 150},
              "2_beklenti": {"deger": f"{v.mean():+.1f} bp P {P:.3f}", "gecti": bool(v.mean() > 0 and P >= 0.9)},
              "3_kararlilik": {"deger": f"{x.net_bp.iloc[:h].mean():+.1f} / {x.net_bp.iloc[h:].mean():+.1f}",
                               "gecti": bool(x.net_bp.iloc[:h].mean() >= 0 and x.net_bp.iloc[h:].mean() >= 0)},
              "4_surtunme": {"deger": f"{x.net_bp_s15.mean():+.1f}", "gecti": bool(x.net_bp_s15.mean() > 0)},
              "5_icra": {"deger": f"16:00 {v.mean():+.1f} vs 16:01 {xd.net_bp.mean():+.1f}",
                         "gecti": bool(v.mean() - xd.net_bp.mean() < 0.5 * abs(xd.net_bp.mean()) and xd.net_bp.mean() > 0)},
              "6_sira_bagimli": {"deger": f"tek pozisyon {xs.net_bp.mean():+.1f} (n {len(xs)})", "gecti": bool(xs.net_bp.mean() > 0)}}
    cs = np.cumsum(v)
    risk = {"std_bp": round(float(v.std()), 1), "en_kotu_bp": round(float(v.min()), 1), "kotu_yuzde5_bp": round(float(np.percentile(v, 5)), 1),
            "medyan_bp": round(float(np.median(v)), 1), "isabet": round(float((v > 0).mean()), 3),
            "en_iyi_5_haric_bp": round(float((v.sum() - np.sort(v)[-5:].sum()) / (len(v) - 5)), 1),
            "maxDD_bp": round(float((cs - np.maximum.accumulate(cs)).min()), 1),
            "yillar": {int(y): round(float(g.net_bp.mean()), 1) for y, g in x.groupby(pd.to_datetime(x.d).dt.year)}}
    return checks, risk


def main() -> None:
    d = G.ndx_bars()
    dp = G.day_prices(d, K.TZ, [570, 870, 900, 960, 961], 60)
    f = K.features(d, 960, 60)
    nt = G.nights(dp, 960, 960, G.KSG_REF, G.nyse_ok)
    ntd = G.nights(dp, 961, 960, G.KSG_REF, G.nyse_ok)
    trig = K.triggers(nt, f, dp, 960)
    wide = G.wick_ends(d, K.TZ, 7200, 0.50, 60)
    val = {(r["hucre"]["K"], r["hucre"]["esik"], r["hucre"]["ksg"]): r for r in json.loads((K.RES / "dogrulama.json").read_text())}
    days = {}
    for nm, (scope, tk, ksg) in CARDS.items():
        m = trig[tk] & ((nt.ksg_ret < 0).values if ksg else True)
        x = nt[m].reset_index(drop=True)
        xd = ntd[ntd.d.isin(set(x.d))]
        checks, risk = stats(x, xd)
        days[nm] = set(x.d)
        v = val[(tk[0], tk[1], ksg)]
        card = {"scope": scope, "tarih": datetime.now().isoformat(timespec="seconds"),
                "aciklama": {"K1": "NDX 16:00 fiyatı 09:30'dan beri TWAP'ın ≥ %0,5 altında ∧ 15:00→16:00 aşağı → 16:00 AL, ertesi işlem günü 16:00 çık (stopsuz).",
                             "K3": "NDX son nakit saati (15:00→16:00) ≤ −%0,3 → 16:00 AL, ertesi işlem günü 16:00 çık (stopsuz)."}[nm],
                "ana_olcum": "Dukascopy NDX 1m 2018-01 → 2026-11, giriş 16:00 açılışı + spread, çıkış ertesi 16:00 açılışı, finansman",
                "olay": len(x), "ort_bp": round(float(x.net_bp.mean()), 1), "checks": checks, "kart_6_6": all(c["gecti"] for c in checks.values()),
                "risk": risk, "YENI": v["YENI"], "fitilsiz_geceler": v["fitilsiz_geceler"], "beslemeler": v["beslemeler"],
                "fitil_ortusme_%": round(100 * float(G.tag(x.t_in.values, wide, 12 * 3600).mean()), 1),
                "verdict": "SHADOW", "sinif": "B",
                "verdict_gerekce": "ESKİ 96 hücrelik şans-üstü ızgaradan seçildi; YENİ Bonferroni, üç bağımsız besleme, fitilden bağımsızlık, s×1,5 ve n geçti. Stopsuz ~24 sa tutuş. Canlı kararı kullanıcıda.",
                "kanit": "research/korku_gece_20261118/RAPOR.md"}
        (G.ROOT / f"backend/data/evolution/go_live_cards/{scope}.json").write_text(json.dumps(card, indent=1, ensure_ascii=False, default=str))
        print(nm, "n", len(x), "ort", card["ort_bp"], "kart", card["kart_6_6"], {k: c["gecti"] for k, c in checks.items()}, "\n  risk", risk,
              "\n  fitil örtüşmesi %", card["fitil_ortusme_%"])
    inter = days["K1"] & days["K3"]
    print("K1∩K3", len(inter), "K1", len(days["K1"]), "K3", len(days["K3"]))


if __name__ == "__main__":
    main()
