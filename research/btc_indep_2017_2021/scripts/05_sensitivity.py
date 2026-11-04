"""EK-2 (sonuç SONRASI; verdikti DEĞİŞTİRMEZ): ön-kayıtlı sağlamlık raporları + maliyet taraması.

(1) maliyet taraması: % modeli RT {1.85, 2.775, 5, 7.5, 10, 15, 20} bp → P-PRE ortR/bp/P (kol zinciri her maliyette yeniden kurulur)
(2) sıcak-dakika eşiği = bağımsız dönemin kendi p99'u (ön-kayıtlı duyarlılık)
(3) >%5 fitil işaretli günlerde giren/çıkan işlemler hariç (ön-kayıtlı duyarlılık)
(4) swap −%22,5 varyantı (05_extras.py formülü), sabit 15 $ yıl bazında, QB'siz P-PRE, BTC al-tut yıl getirisi (bağlam)
Kullanım: python -I -B 05_sensitivity.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ME / "scripts" / "port"))
import lib_st as L  # noqa: E402
import sleeves as SV  # noqa: E402

DAYM = 1440
PRE = ["S1_CORE", "S2_MAX10", "S3_QB", "S4_X04"]
E = SV.engine()
EV = {k: SV.SLEEVES[k][0]().sort_values("ent").reset_index(drop=True) for k in SV.SLEEVES}
out: dict = {}


def chain_mode(k: str, mode: str) -> pd.DataFrame:
    ev = EV[k]
    s = E.simulate(ev.ent, ev.dir, ev.sl_d, ev.tp_d, ev.end, ev.sig, mode=mode, slip=True)
    df = ev.copy()
    df["R"] = s.R.to_numpy() * (df.sl_d.to_numpy() / df.R_den.to_numpy())
    for c in ("bp", "ent_t", "ext_t", "nights", "typ"):
        df[c] = s[c].to_numpy()
    df = df[np.isfinite(df.R)].reset_index(drop=True)
    df["split"] = L.split_of(df.ent_t.to_numpy())
    df = df[df.split != ""].reset_index(drop=True)
    keep = L.single_position(df.ent_t.to_numpy().astype(float), df.ext_t.to_numpy())
    return df.iloc[np.sort(keep)].reset_index(drop=True)


def pool(dfs: list[pd.DataFrame]) -> dict:
    d = pd.concat(dfs, ignore_index=True)
    P, lo, hi = L.day_boot(d.R.to_numpy(), (d.ent_t.to_numpy() // DAYM))
    return {"n": len(d), "ortR": round(float(d.R.mean()), 4), "bp": round(float(d.bp.mean()), 2), "P": round(P, 4),
            "GA": [round(lo, 4), round(hi, 4)]}


# (1) maliyet taraması
rows = []
for c in (1.85, 2.775, 5.0, 7.5, 10.0, 15.0, 20.0):
    key = f"c{c}"
    L.SPREAD[key] = c / 1e4
    sets = {k: chain_mode(k, key) for k in SV.SLEEVES}
    r = {"RT_bp": c, **{f"P-PRE_{a}": b for a, b in pool([sets[k] for k in PRE]).items()}}
    for k in SV.SLEEVES:
        r[k] = round(float(sets[k].R.mean()), 4) if len(sets[k]) else np.nan
    r["P-ALL-DV_ortR"] = pool([sets[k] for k in list(SV.SLEEVES)[:6]])["ortR"]
    rows.append(r)
    print(r, flush=True)
cost = pd.DataFrame(rows)
cost.to_csv(L.RES / "cost_sweep.csv", index=False)
out["cost_sweep"] = rows

# (2) sıcak eşik = bağımsız dönemin p99'u
lc = np.log(E.C)
ar = np.abs(np.diff(lc, prepend=np.nan)) * 1e4
thr_ind = float(np.nanpercentile(ar, 99))
hot_frozen = E.hot.copy()
E.hot = ar > thr_ind
sets_h = {k: chain_mode(k, "base") for k in SV.SLEEVES}
E.hot = hot_frozen
out["hot_thr"] = {"frozen_bp": L.HOT_THR, "ind_p99_bp": round(thr_ind, 3),
                  "share_hot_minutes_frozen": round(float(np.mean(hot_frozen)), 4),
                  "P-PRE_ind_thr": pool([sets_h[k] for k in PRE])}
print("sıcak eşik:", out["hot_thr"], flush=True)

# (3) fitil günleri hariç + (4) diğerleri — taban setler (portfolio.py çıktısı)
SETS = pd.read_pickle(L.RES / "portfolio_trades.pkl")
q = json.load(open(ME / "data" / "btc_quality_report.json"))
wd = sorted({pd.Timestamp(x["ts"]).floor("D") for x in q["wick_gt5pct_from_rolling_median"]})
wdays = np.array([int(t.value // 60_000_000_000) // DAYM for t in wd])
dfs = []
for k in PRE:
    d = SETS[k]
    a = d.ent_t.to_numpy() // DAYM
    b = (d.ext_t.to_numpy() // DAYM).astype(np.int64)
    hit = np.array([np.any((wdays >= x) & (wdays <= y)) for x, y in zip(a, b)])
    dfs.append(d[~hit])
out["wick_days"] = {"n_days": len(wdays), "days": [str(x.date()) for x in wd],
                    "P-PRE_excl": pool(dfs), "removed": int(sum(len(SETS[k]) for k in PRE) - sum(len(x) for x in dfs))}
print("fitil günleri hariç:", out["wick_days"]["P-PRE_excl"], "silinen", out["wick_days"]["removed"], flush=True)

swap = {}
for k in SV.SLEEVES:
    p = SETS[k]
    extra = np.where(p.dir == 1, -(0.225 - 0.14) / 365, 0.0) * p.nights * p.sig / p.R_den
    swap[k] = [round(float(p.R.mean()), 4), round(float((p.R + extra).mean()), 4), round(float(p.nights.mean()), 2)]
out["swap22.5"] = swap
dpre = pd.concat([SETS[k] for k in PRE], ignore_index=True)
yrs = pd.to_datetime(dpre.ent_t * 60, unit="s").dt.year
out["abs15_by_year"] = {int(y): [int((yrs == y).sum()), round(float(dpre.R_abs[yrs == y].mean()), 4),
                                 round(float(dpre.R[yrs == y].mean()), 4)] for y in sorted(yrs.unique())}
out["P-PRE_without_QB"] = pool([SETS[k] for k in PRE if k != "S3_QB"])
out["P-PRE_bp_by_sleeve"] = {k: round(float(SETS[k].bp.mean()), 2) for k in PRE}
P_by_sleeve = {}
for k in SV.SLEEVES:
    d = SETS[k]
    if len(d) > 1:
        P_by_sleeve[k] = pool([d])
out["sleeve_pool"] = P_by_sleeve
d1 = pd.read_parquet(ME / "data" / "btc_1d.parquet", columns=["ts", "close"])
d1["y"] = d1.ts.dt.year
yr = d1.groupby("y").close.agg(["first", "last"])
out["btc_buy_hold_by_year"] = {int(y): round(float(r["last"] / r["first"] - 1), 3) for y, r in yr.iterrows()}
out["long_share_P-PRE"] = round(float((dpre.dir == 1).mean()), 3)
(L.RES / "sensitivity.json").write_text(json.dumps(out, indent=1, default=float))
for k, v in out.items():
    if k not in ("cost_sweep", "wick_days"):
        print(k, v)
