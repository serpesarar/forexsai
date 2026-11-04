"""CAPREV portföy kartının (caprev_pooled.py, GF-22) saat ekseni düzeltilmiş yeniden üretimi.

KURAL AYNEN (round4.events / cross_market.events / caprev_card.paths, hiçbir parametre değişmez);
yalnız bar zaman damgaları düzeltilir. Kart JSON'una YAZMAZ — sonuçlar results/ altına.

Senaryolar:
  ORJ   : orijinal veri (kartı birebir yeniden üretmeli: 161 / 134 / +0,217)
  DAXfix: DAX +60 dk (NY standart saatinde), NDX orijinal
  TAM_a : DAXfix + NDX long_1h 2017-11-05…2018-02-26 −60 dk
  TAM_b : DAXfix + NDX long_1h 2017-11-05…2018-03-02 −60 dk
  TAM_x : DAXfix + NDX 2017-11-05…2018-03-11 dışlanmış (diğer araştırmacının yolu)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

GFDIR = Path("/Users/melihcanodacioglu/Desktop/panel/research/ndx_gate_forge")
sys.path.insert(0, str(GFDIR))
import cross_market as cm  # noqa: E402
from caprev_card import SPR, SPREAD_STRESS, paths  # noqa: E402
from common import block_boot  # noqa: E402
from long_data import load_long  # noqa: E402
from round4 import build, events  # noqa: E402

HERE = Path(__file__).resolve().parent
FIX = HERE / "data_fixed"
OUT = HERE / "results"
ORIG_DATA = cm.DATA
HOUR = pd.Timedelta(minutes=60)


def dax_build(fixed: bool) -> pd.DataFrame:
    cm.DATA = FIX if fixed else ORIG_DATA
    try:
        return cm.build_dax("1h")
    finally:
        cm.DATA = ORIG_DATA


def ndx_bars(variant: str) -> pd.DataFrame:
    if variant == "orj":
        return load_long("1h")
    if variant in ("a", "b"):
        return pd.read_parquet(FIX / f"ndx_long_1h_fix{variant}.parquet")
    if variant == "x":
        d = load_long("1h")
        bad = (d.ts >= pd.Timestamp("2017-11-05", tz="UTC")) & (d.ts < pd.Timestamp("2018-03-12", tz="UTC"))
        return d[~bad].reset_index(drop=True)
    raise ValueError(variant)


def leg(name: str, d: pd.DataFrame, E: pd.DataFrame, ce: int) -> pd.DataFrame:
    real = paths(d, E, SPR, close_end=ce).assign(m=name)
    real["R15"] = paths(d, E, SPR * SPREAD_STRESS, close_end=ce).R_d0.to_numpy()
    real["Ropt"] = paths(d, E, SPR, optimistic=True, close_end=ce).R_d0.to_numpy()
    # olay ayrıntısı (tetik barı UTC, pdl, r1/r5/dvol) — karşılaştırma için
    ev = E.set_index("nyd")
    real["trig_ts"] = [d.ts.iat[int(t) - 1] for t in real.t_in]
    real["entry_ts"] = [d.ts.iat[int(t)] for t in real.t_in]
    real["exit_ts"] = [d.ts.iat[int(t)] for t in real.t_out]
    for c in ("pdl", "r1", "r5", "dvol", "vix"):
        real[c] = ev.loc[real.nyd, c].to_numpy()
    return real


def card(parts: list[pd.DataFrame]) -> dict:
    x = pd.concat(parts).sort_values("nyd").reset_index(drop=True)
    v = x.R_d0.to_numpy(); days = x.nyd.astype(str).to_numpy()
    bs = block_boot(v, days, 4000); h = len(v) // 2
    ndays = int(x.nyd.nunique()); both = int((x.groupby("nyd").m.nunique() == 2).sum())
    top5 = float(np.sort(x.groupby("nyd").R_d0.sum().to_numpy())[::-1][:5].sum())
    sp = x.sort_values(["nyd", "m"], ascending=[True, True]).groupby("nyd").head(1)
    yrs = x.assign(y=x.nyd.dt.year).groupby("y").R_d0.sum()
    chk = {
        "1_hacim": {"deger": f"{len(v)} işlem / {ndays} bağımsız gün", "gecti": bool(len(v) >= 150 and ndays >= 100)},
        "2_beklenti": {"deger": f"ortR={v.mean():+.3f} P(EV>0)=%{100*np.mean(bs>0):.1f}",
                       "gecti": bool(v.mean() > 0 and np.mean(bs > 0) >= .9)},
        "3_kararlilik": {"deger": f"ilk={v[:h].mean():+.3f} son={v[h:].mean():+.3f}",
                         "gecti": bool(v[:h].mean() >= 0 and v[h:].mean() >= 0)},
        "4_surtunme": {"deger": f"spread×1.5: ortR={x.R15.mean():+.3f}", "gecti": bool(x.R15.mean() > 0)},
        "5_icra": {"deger": f"kapanış-girişi {x.Ropt.mean():+.3f} vs gerçek {v.mean():+.3f} "
                            f"(fark {abs(x.Ropt.mean()-v.mean()):.3f}, eşik {.5*abs(v.mean()):.3f})",
                   "gecti": bool(abs(x.Ropt.mean() - v.mean()) < .5 * abs(v.mean()))},
        "6_sira_bagimli": {"deger": f"gün başına tek pozisyon n={len(sp)} ortR={sp.R_d0.mean():+.3f}",
                           "gecti": bool(sp.R_d0.mean() > 0)},
    }
    per = {m: {"n": int((x.m == m).sum()), "ortR": round(float(x.R_d0[x.m == m].mean()), 3),
               "toplam": round(float(x.R_d0[x.m == m].sum()), 2),
               "WR": round(100 * float((x.R_d0[x.m == m] > 0).mean()), 1)} for m in sorted(x.m.unique())}
    for m in per:   # bacak başına bootstrap (bilgi; kart portföyde)
        xm = x[x.m == m]
        bm = block_boot(xm.R_d0.to_numpy(), xm.nyd.astype(str).to_numpy(), 4000)
        per[m]["P(EV>0)"] = round(float(np.mean(bm > 0)), 3)
        per[m]["CI95"] = [round(float(np.percentile(bm, 2.5)), 3), round(float(np.percentile(bm, 97.5)), 3)]
        hm = len(xm) // 2
        per[m]["yarilar"] = [round(float(xm.R_d0.iloc[:hm].mean()), 3), round(float(xm.R_d0.iloc[hm:].mean()), 3)]
        per[m]["yil+"] = f"{int((xm.groupby(xm.nyd.dt.year).R_d0.sum() > 0).sum())}/{xm.nyd.dt.year.nunique()}"
    return {"islem": len(v), "bagimsiz_gun": ndays, "iki_piyasa_ayni_gun": both,
            "wr": round(100 * float((v > 0).mean()), 1), "ort_R": round(float(v.mean()), 3),
            "toplam_R": round(float(v.sum()), 2), "en_iyi_5_gun_haric": round(float(v.sum() - top5), 2),
            "en_iyi_5_gun_payi": round(top5 / float(v.sum()), 2) if v.sum() > 0 else None,
            "P(EV>0)": round(float(np.mean(bs > 0)), 3),
            "CI95": [round(float(np.percentile(bs, 2.5)), 3), round(float(np.percentile(bs, 97.5)), 3)],
            "pozitif_yil": f"{int((yrs > 0).sum())}/{len(yrs)}", "bacaklar": per, "checks": chk,
            "verdikt": "LIVE" if all(c["gecti"] for c in chk.values()) else "SHADOW"}, x


def run(dax_fixed: bool, ndx_var: str) -> tuple[dict, pd.DataFrame]:
    d_n = build(ndx_bars(ndx_var), 60, 540)
    d_d = dax_build(dax_fixed)
    ce_d = int(d_d.close_end.iat[0])
    parts = [leg("NDX", d_n, events(d_n, "stress", "hi"), 960), leg("DAX", d_d, cm.events(d_d, "stress", "hi"), ce_d)]
    return card(parts)


if __name__ == "__main__":
    sc = {"ORJ": (False, "orj"), "DAXfix": (True, "orj"), "TAM_a": (True, "a"), "TAM_b": (True, "b"), "TAM_x": (True, "x")}
    res, trades = {}, {}
    for k, (fx, nv) in sc.items():
        c, x = run(fx, nv)
        res[k], trades[k] = c, x
        x.to_csv(OUT / f"trades_{k}.csv", index=False)
        print(f"\n===== {k} =====  verdikt {c['verdikt']}")
        print({kk: c[kk] for kk in ("islem", "bagimsiz_gun", "wr", "ort_R", "toplam_R", "P(EV>0)", "CI95",
                                    "en_iyi_5_gun_haric", "en_iyi_5_gun_payi", "pozitif_yil")})
        for m, p in c["bacaklar"].items():
            print(f"   {m}: {p}")
        for ck, v in c["checks"].items():
            print(f"   {ck:15} {'✓' if v['gecti'] else '✗'} {v['deger']}")
    (OUT / "recheck_card.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str))
