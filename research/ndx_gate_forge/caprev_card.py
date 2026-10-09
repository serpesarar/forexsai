"""CAPREV canlıya alma kartı (CLAUDE.md 2. Kural) — 2026-10-09.

ÖN KAYIT (sonuçlara bakmadan):
  Scope    : tek kademeli CAPREV (GF-20). CAPREV-2 GF-19'da geri çekildi → sınanmaz.
  Kural    : round4.events(stress, hi) — stres günü (dün ≤ −%1,5 veya 5g ≤ −%4) ∧ VIX ≥ 18,4,
             NY 03:00–15:00 arası önceki RTH dibinin altındaki İLK kapanış → BUY.
  Giriş    : sinyal barından SONRAKİ barın açılışı + spread (gerçek icra).
  Stop     : 1 × günlük oynaklık (dvol). Ana çıkış: aynı gün 16:00 ET kapanışı (R_d0).
  Ana veri : NDX 1h, broker uzun geçmiş (2016+). Yan: 30m, 15m, çıkış +1R/−1R (R_tp1).
  Ölçütler : go_live_gate.py ile aynı 6 ölçüt ve eşikler.
  Spread   : SPR = 0,00006 (≈1,7 puan / taraf; MT5 ölçümü 1,3–1,5 → muhafazakâr).
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from common import block_boot
from long_data import load_long
from round4 import build, events

ROOT = Path(__file__).resolve().parents[2]
CARD = ROOT / "backend/data/evolution/go_live_cards/caprev.json"
SPR = 0.00006
MIN_EVENTS, MIN_P_EV, SPREAD_STRESS = 150, 0.90, 1.5
CLOSE_END = 960          # 16:00 ET bar bitişi (dk)


def paths(d: pd.DataFrame, E: pd.DataFrame, spr: float, optimistic: bool = False,
          close_end: int = CLOSE_END) -> pd.DataFrame:
    """Olay başına R. optimistic=True → giriş sinyal barı kapanışı, spread yok (raporların varsayımı)."""
    idx = pd.Series(d.index[d.end == close_end], index=d.nyd[d.end == close_end]).groupby(level=0).last()
    lo, hi, op, cl = (d[c].to_numpy() for c in ["low", "high", "open", "close"])
    cost = 0.0 if optimistic else 2 * spr
    rows = []
    for r in E.itertuples():
        if r.nyd not in idx.index or int(idx[r.nyd]) < r.ei:
            continue
        j0 = int(idx[r.nyd])
        e = cl[r.ei - 1] if optimistic else op[r.ei]
        sd = e * r.dvol
        stop, tgt = e - sd, e + sd
        R_d0 = R_tp = None
        for j in range(r.ei, j0 + 1):
            if lo[j] <= stop:
                px = min(op[j], stop) if j > r.ei else stop
                R = (px - e) / sd - cost / r.dvol
                R_d0 = R if R_d0 is None else R_d0
                R_tp = R if R_tp is None else R_tp
                break
            if hi[j] >= tgt and R_tp is None:
                px = max(op[j], tgt) if j > r.ei else tgt
                R_tp = (px - e) / sd - cost / r.dvol
        if R_d0 is None:
            R_d0 = (cl[j0] - e) / sd - cost / r.dvol
        R_tp = R_d0 if R_tp is None else R_tp
        rows.append({"nyd": r.nyd, "t_in": r.ei, "t_out": j0, "R_d0": R_d0, "R_tp1": R_tp})
    return pd.DataFrame(rows).sort_values("nyd").reset_index(drop=True)


def card_for(d: pd.DataFrame, col: str) -> dict:
    E = events(d, "stress", "hi")
    real = paths(d, E, SPR)
    stress = paths(d, E, SPR * SPREAD_STRESS)
    opt = paths(d, E, SPR, optimistic=True)
    v = real[col].to_numpy()
    days = real.nyd.astype(str).to_numpy()
    bs = block_boot(v, days, 4000)
    h = len(v) // 2
    m, m_opt, m_st = float(v.mean()), float(opt[col].mean()), float(stress[col].mean())
    overlap = int((real.t_in.to_numpy()[1:] <= real.t_out.to_numpy()[:-1]).sum())
    top5 = float(np.sort(v)[::-1][:5].sum())
    chk = {
        "1_hacim": {"deger": len(v), "esik": f"≥{MIN_EVENTS}", "gecti": len(v) >= MIN_EVENTS},
        "2_beklenti": {"deger": f"ortR={m:+.3f} P(EV>0)=%{100 * np.mean(bs > 0):.1f}",
                       "esik": "ortR>0 ve P≥%90", "gecti": m > 0 and np.mean(bs > 0) >= MIN_P_EV},
        "3_kararlilik": {"deger": f"ilk={v[:h].mean():+.3f} son={v[h:].mean():+.3f}",
                         "esik": "ikisi de ≥0", "gecti": bool(v[:h].mean() >= 0 and v[h:].mean() >= 0)},
        "4_surtunme": {"deger": f"spread×{SPREAD_STRESS}: ortR={m_st:+.3f}", "esik": ">0", "gecti": m_st > 0},
        "5_icra": {"deger": f"kapanış-girişi ortR={m_opt:+.3f} vs gerçek {m:+.3f}",
                   "esik": "fark < 0,5×|gerçek ortR|", "gecti": abs(m_opt - m) < 0.5 * abs(m)},
        "6_sira_bagimli": {"deger": f"çakışan işlem={overlap}, n={len(v)} ortR={m:+.3f}",
                           "esik": ">0 (tek pozisyon)", "gecti": overlap == 0 and m > 0},
    }
    return {"olay": len(v), "aralik": [str(real.nyd.iat[0].date()), str(real.nyd.iat[-1].date())],
            "wr": round(100 * float((v > 0).mean()), 1), "ort_R": round(m, 3), "toplam_R": round(float(v.sum()), 2),
            "en_iyi_5_haric_toplam": round(float(v.sum()) - top5, 2),
            "bootstrap_%95": [round(float(np.percentile(bs, 2.5)), 3), round(float(np.percentile(bs, 97.5)), 3)],
            "yillar_pozitif": f"{int((real.assign(R=v).groupby(real.nyd.dt.year).R.sum() > 0).sum())}/"
                              f"{real.nyd.dt.year.nunique()}",
            "checks": chk}


def verdict(chk: dict) -> str:
    if not chk["1_hacim"]["gecti"]:
        return "RED"
    return "LIVE" if all(c["gecti"] for c in chk.values()) else "SHADOW"


def main() -> None:
    res = {}
    for tf, step in [("1h", 60), ("30m", 30), ("15m", 15)]:
        d = build(load_long(tf), step, 540 if step == 60 else 570)
        for col in ("R_d0", "R_tp1"):
            res[f"{tf} {col}"] = card_for(d, col)
    main_c = res["1h R_d0"]
    out = {
        "scope": "caprev", "aciklama": "NDX stres∧VIX≥18,4 günü, önceki RTH dibi altındaki ilk kapanış → BUY; "
                                      "stop 1×günlük vol, çıkış 16:00 ET",
        "tarih": datetime.now().isoformat(timespec="seconds"), "sembol": "NAS100",
        "spread_oran": SPR, "ana_olcum": "NDX 1h, çıkış 16:00 (R_d0)",
        **{k: main_c[k] for k in ("olay", "aralik", "wr", "ort_R", "toplam_R", "en_iyi_5_haric_toplam",
                                  "bootstrap_%95", "yillar_pozitif", "checks")},
        "verdikt": verdict(main_c["checks"]),
        "yan_olcumler": {k: {**{x: v[x] for x in ("olay", "aralik", "ort_R", "toplam_R", "en_iyi_5_haric_toplam",
                                                 "yillar_pozitif")},
                             "verdikt": verdict(v["checks"]),
                             "gecen": [c for c, x in v["checks"].items() if x["gecti"]]}
                         for k, v in res.items() if k != "1h R_d0"},
        "m1_kanit": "ndx_synthesis_20261002: M1 katı icra (sonraki M1 açılışı + gerçek spread) 11 işlem +11,12R, "
                    "en iyi 5 gün çıkınca −1,35R",
        "not": "Mac'te üretildi (research/ndx_gate_forge/caprev_card.py). CAPREV-2 GF-19'da geri çekildi; kart tek "
               "kademeli CAPREV içindir. Yılda ~10 olay: 1. ölçüt yapısal olarak geçilemez.",
    }
    CARD.write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str))
    print(json.dumps({k: out[k] for k in ("olay", "aralik", "wr", "ort_R", "toplam_R", "en_iyi_5_haric_toplam",
                                          "bootstrap_%95", "yillar_pozitif", "verdikt")}, ensure_ascii=False))
    for c, x in out["checks"].items():
        print(f"  {c:16} {'✓' if x['gecti'] else '✗'}  {x['deger']}   ({x['esik']})")
    for k, v in out["yan_olcumler"].items():
        print(f"  yan {k:10} n={v['olay']} ortR={v['ort_R']:+.3f} top={v['toplam_R']} 5hariç={v['en_iyi_5_haric_toplam']} "
              f"yıl={v['yillar_pozitif']} → {v['verdikt']} geçen={v['gecen']}")


if __name__ == "__main__":
    main()
