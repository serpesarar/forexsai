"""fam_stres — prereg.md'deki tüm hücreleri koşar. Çıktı: results/*.json, results/cells.csv, results/summary.md.

Kullanım: .venv/bin/python -I run_stres.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from engine import (M1, OUT, SEGS, block_boot, daily, seg_of, single_pos, stats, to_min)  # noqa: E402

N_PLACEBO = 200
CONF = ("OOS", "KOR")
RNG = np.random.default_rng(20261021)

m1 = M1()
D = daily(m1)
DAYS = D.index.to_numpy()
SIG = D.sig20.to_numpy()

# 1h barlar + ATR14 (bitiş zamanına göre)
h1 = pd.read_parquet(m1_path := (OUT.parent.parent / "data" / "btc_1h.parquet"),
                     columns=["ts", "open", "high", "low", "close"])
H1S = to_min(h1.ts)
H1E = H1S + 60
pc = h1.close.shift(1)
tr = np.maximum(h1.high - h1.low, np.maximum((h1.high - pc).abs(), (h1.low - pc).abs()))
ATR = tr.rolling(14).mean().to_numpy()
H1C = h1.close.to_numpy()


def atr_at(t: np.ndarray) -> np.ndarray:
    j = np.searchsorted(H1E, t, "right") - 1
    out = ATR[np.maximum(j, 0)]
    return np.where(j >= 0, out, np.nan)


def sig_at(day: np.ndarray) -> np.ndarray:
    j = day - DAYS[0]
    ok = (j >= 0) & (j < len(DAYS))
    return np.where(ok, SIG[np.clip(j, 0, len(DAYS) - 1)], np.nan)


# ---------------------------------------------------------------- geometri
def geom(t_dec: np.ndarray, exit_kind: str, hold: int, stop_kind: str, fac: float, side: int):
    day = t_dec // 1440
    n = len(t_dec)
    if exit_kind == "D0":
        T, hm = (day + 1) * 1440, np.zeros(n, np.int64)
    elif exit_kind == "D1":
        T, hm = (day + 2) * 1440, np.zeros(n, np.int64)
    else:
        T, hm = np.zeros(n, np.int64), np.full(n, hold * 60, np.int64)
    if stop_kind == "sig":
        sp, sa = fac * sig_at(day), np.zeros(n)
    else:
        sp, sa = np.zeros(n), fac * atr_at(t_dec)
    return dict(t_dec=t_dec, side=np.full(n, side), T_abs=T, hold_min=hm, stop_pct=sp, stop_abs=sa)


def run_events(t_dec, sig_close, spec) -> pd.DataFrame:
    g = geom(np.asarray(t_dec, np.int64), spec["exit"], spec.get("hold", 0), spec["stop"], spec["fac"],
             spec["side"])
    res = {}
    for mode in ("base", "stress", "fix", "opt"):
        res[mode] = m1.simulate(**g, mode=mode, sig_close=np.asarray(sig_close, np.float64)).set_index("k")
    df = res["base"].copy()
    for mode, col in (("stress", "R_st"), ("fix", "R_fix"), ("opt", "R_opt")):
        df[col] = res[mode].R.reindex(df.index)
    df["seg"] = seg_of(df.t_in.to_numpy())
    df["mod"] = (np.asarray(t_dec, np.int64)[df.index.to_numpy()] % 1440)
    df["t_dec"] = np.asarray(t_dec, np.int64)[df.index.to_numpy()]
    df["year"] = pd.to_datetime(df.t_in.to_numpy() * 60, unit="s").year
    return df.reset_index(drop=True)


# ---------------------------------------------------------------- plasebo P1
CAND = {}
for s, (a, b) in SEGS.items():
    dd = DAYS[(DAYS * 1440 >= a) & (DAYS * 1440 < b) & np.isfinite(SIG)]
    yrs = pd.to_datetime(dd * 86400, unit="s").year
    for y in np.unique(yrs):
        CAND[(s, int(y))] = dd[yrs == y]


def placebo_means(df: pd.DataFrame, spec) -> np.ndarray:
    """Her işlem: aynı segment × yıl × UTC saat:dakika, rastgele gün; aynı yön/geometri. Tekrar başına ort R."""
    if len(df) == 0:
        return np.full(N_PLACEBO, np.nan)
    n = len(df)
    tds = np.empty((N_PLACEBO, n), np.int64)
    for i, r in enumerate(df[["seg", "year", "mod"]].itertuples(index=False)):
        c = CAND[(r.seg, int(r.year))]
        tds[:, i] = RNG.choice(c, N_PLACEBO) * 1440 + r.mod
    flat = tds.ravel()
    g = geom(flat, spec["exit"], spec.get("hold", 0), spec["stop"], spec["fac"], spec["side"])
    res = m1.simulate(**g, mode="base")
    b = res.k.to_numpy() // n
    s = np.bincount(b, weights=res.R.to_numpy(), minlength=N_PLACEBO)
    c = np.bincount(b, minlength=N_PLACEBO)
    return s / np.maximum(c, 1)


# ---------------------------------------------------------------- olay üreticileri
def day_flags(k: float, fear: str, stress_mode: str = "sigma") -> pd.Series:
    if stress_mode == "sigma":
        st = (D.r1 <= -k * D.sig20) | (D.r5 <= -k * D.sig20 * np.sqrt(5))
    elif stress_mode == "literal":
        st = (D.r1 <= -0.015) | (D.r5 <= -0.04)
    elif stress_mode == "euph":
        st = (D.r1 >= k * D.sig20) | (D.r5 >= k * D.sig20 * np.sqrt(5))
    st = st & D.sig20.notna()
    return st


def fear_flag(fear: str) -> pd.Series:
    if fear == "VIX":
        return (D.vix >= 18.4) & D.vix.notna()
    if fear == "RV":
        return D.rvhi == 1.0
    if fear == "notVIX":
        return (D.vix < 18.4) & D.vix.notna()
    if fear == "notRV":
        return D.rvhi == 0.0
    return pd.Series(True, index=D.index)


# tetik adayları: gün başına ilk "kapanış < pdl" (UTC 1h ve US 30m) ve "kapanış > pdh" (UTC 1h)
_h = pd.DataFrame({"s": H1S, "c": H1C})
_h["day"] = _h.s // 1440
_h["mod"] = _h.s % 1440
_h = _h[_h["mod"] <= 19 * 60].join(D[["pdl", "pdh"]], on="day")
TRIG_UTC = _h[_h.c < _h.pdl].groupby("day").head(1).set_index("day")
TRIG_UTC_UP = _h[_h.c > _h.pdh].groupby("day").head(1).set_index("day")
_g = pd.DataFrame({"g": m1.ts // 30, "c": m1.c}).groupby("g").c.last()
_m = pd.DataFrame({"s": _g.index.to_numpy() * 30, "c": _g.to_numpy()})
_m["day"] = _m.s // 1440
_m["mod"] = _m.s % 1440
_m = _m[(_m["mod"] >= 810) & (_m["mod"] <= 1170)].join(D[["pdl"]], on="day")
TRIG_US = _m[_m.c < _m.pdl].groupby("day").head(1).set_index("day")


def caprev_events(daymask: pd.Series, window: str, up: bool = False):
    trig = TRIG_UTC_UP if up else (TRIG_UTC if window == "UTC" else TRIG_US)
    step = 60 if window == "UTC" else 30
    days = daymask[daymask].index
    t = trig.loc[trig.index.intersection(days)]
    return (t.s + step).to_numpy(np.int64), t.c.to_numpy()


def daily_events(daymask: pd.Series):
    days = daymask[daymask].index.to_numpy()
    return days * 1440, D.close.shift(1).loc[days].to_numpy()


# 1 saatlik şok (5m ızgara)
b5 = pd.read_parquet(OUT.parent.parent / "data" / "btc_5m.parquet", columns=["ts", "close"])
S5 = to_min(b5.ts)
C5 = b5.close.to_numpy()
_j = np.searchsorted(S5, S5 - 60)
_ok = (_j < len(S5)) & (S5[np.minimum(_j, len(S5) - 1)] == S5 - 60)
RET60 = np.where(_ok, C5 / C5[np.minimum(_j, len(S5) - 1)] - 1, np.nan)
SIG60 = pd.Series(RET60).rolling(8640, min_periods=4000).std().shift(1).to_numpy()


def shock_events(z: float, side: int):
    with np.errstate(invalid="ignore"):
        cond = (RET60 <= -z * SIG60) if side > 0 else (RET60 >= z * SIG60)
    idx = np.flatnonzero(cond)
    keep, last = [], -10 ** 12
    for i in idx:
        e = S5[i] + 5
        if e - last >= 240:
            keep.append(i)
            last = e
    keep = np.array(keep, np.int64)
    return S5[keep] + 5, C5[keep]


# ---------------------------------------------------------------- hücreler
CELLS: list[dict] = []


def add(name, group, t_dec, sclose, **spec):
    spec.setdefault("hold", 0)
    CELLS.append({"name": name, "group": group, "t": t_dec, "c": sclose, "spec": spec})


for fear, grp in (("VIX", "G1"), ("RV", "G2")):
    for k in (1.0, 1.5):
        mask = day_flags(k, fear) & fear_flag(fear)
        for w in ("UTC", "US"):
            t, c = caprev_events(mask, w)
            for x in ("D0", "H4", "D1"):
                ex, hold = ("H", 4) if x == "H4" else (x, 0)
                add(f"{grp}_k{k}_{w}_{x}", grp, t, c, exit=ex, hold=hold, stop="sig", fac=1.0, side=1)
for k in (0.0, 1.0, 2.0):
    mask = ((D.r1 < 0) if k == 0 else (D.r1 <= -k * D.sig20)) & D.sig20.notna()
    t, c = daily_events(mask)
    for x in ("D0", "D1"):
        add(f"G3_k{k}_{x}", "G3", t, c, exit=x, stop="sig", fac=2.0, side=1)
    mask = ((D.r1 > 0) if k == 0 else (D.r1 >= k * D.sig20)) & D.sig20.notna()
    t, c = daily_events(mask)
    for x in ("D0", "D1"):
        add(f"N1a_k{k}_{x}", "N1a", t, c, exit=x, stop="sig", fac=2.0, side=-1)
for z in (2.5, 3.5):
    for side, grp in ((1, "G4"), (-1, "G5")):
        t, c = shock_events(z, side)
        for s in (1.0, 2.0):
            for hold in (1, 4):
                add(f"{grp}_z{z}_s{s}_h{hold}", grp, t, c, exit="H", hold=hold, stop="atr", fac=s, side=side)
for k in (1.0, 1.5):
    t, c = caprev_events(day_flags(k, "", "euph"), "UTC", up=True)
    add(f"N1b_k{k}_UTC_D0", "N1b", t, c, exit="D0", stop="sig", fac=1.0, side=-1)
# kontrol / bilgi hücreleri (UTC × D0)
for k in (1.0, 1.5):
    st = day_flags(k, "")
    for fear in ("VIX", "RV"):
        nf = "notVIX" if fear == "VIX" else "notRV"
        for lab, mask in ((f"stres_ve_not{fear}", st & fear_flag(nf)),
                          (f"notstres_ve_{fear}", ~st & D.sig20.notna() & fear_flag(fear)),
                          (f"stres_ve_{fear}_SELL", st & fear_flag(fear))):
            t, c = caprev_events(mask, "UTC")
            add(f"K_k{k}_{lab}_UTC_D0", "K", t, c, exit="D0", stop="sig", fac=1.0,
                side=-1 if lab.endswith("SELL") else 1)
    t, c = caprev_events(st, "UTC")
    add(f"K_k{k}_stres_korkusuz_UTC_D0", "K", t, c, exit="D0", stop="sig", fac=1.0, side=1)
for fear in ("VIX", "RV"):
    t, c = caprev_events(day_flags(0, "", "literal") & fear_flag(fear), "UTC")
    add(f"K_literal_{fear}_UTC_D0", "K", t, c, exit="D0", stop="sig", fac=1.0, side=1)
t, c = caprev_events(D.sig20.notna(), "UTC")
add("K_tetik_hergun_UTC_D0", "K", t, c, exit="D0", stop="sig", fac=1.0, side=1)
t, c = caprev_events(D.sig20.notna(), "US")
add("K_tetik_hergun_US_D0", "K", t, c, exit="D0", stop="sig", fac=1.0, side=1)
t, c = daily_events(D.sig20.notna())
add("K_hergun_0000_BUY_1sig_D0", "K", t, c, exit="D0", stop="sig", fac=1.0, side=1)
for x in ("D0", "D1"):
    add(f"K_hergun_0000_BUY_2sig_{x}", "K", t, c, exit=x, stop="sig", fac=2.0, side=1)

PRIMARY = ("G1", "G2", "G3", "G4")


def main() -> None:
    rows, trades, plc = [], {}, {}
    for cell in CELLS:
        df = run_events(cell["t"], cell["c"], cell["spec"])
        trades[cell["name"]] = df
        r = {"cell": cell["name"], "group": cell["group"]}
        for s in ("KESIF", "OOS", "KOR"):
            st = stats(df[df.seg == s])
            for kk in ("n", "wr", "ortR", "P_EV", "ort_ret_bp"):
                r[f"{s}_{kk}"] = st.get(kk)
        cf = df[df.seg.isin(CONF)]
        st = stats(cf)
        for kk in ("n", "wr", "basabas_wr", "ortR", "ci95", "P_EV", "p_tek", "yari1", "yari2", "ort_ret_bp"):
            r[f"ONAY_{kk}"] = st.get(kk)
        r["TUM_ortR"] = stats(df).get("ortR")
        r["TUM_n"] = len(df)
        if cell["group"] in PRIMARY + ("G5", "N1a", "N1b") or cell["name"].startswith("K_tetik") \
                or cell["name"].startswith("K_hergun"):
            pk = placebo_means(df[df.seg == "KESIF"], cell["spec"])
            pc = placebo_means(cf, cell["spec"])
            plc[cell["name"]] = {"KESIF": pk, "ONAY": pc}
            if len(cf):
                r["ONAY_plasebo_ort"] = round(float(np.nanmean(pc)), 4)
                r["ONAY_plasebo_yuzdelik"] = round(float(np.mean(pc < cf.R.mean())), 3)
            kd = df[df.seg == "KESIF"]
            if len(kd):
                r["KESIF_plasebo_ort"] = round(float(np.nanmean(pk)), 4)
                r["KESIF_plasebo_yuzdelik"] = round(float(np.mean(pk < kd.R.mean())), 3)
        rows.append(r)
        print(f"{cell['name']:32} n={r['TUM_n']:5}  KEŞİF {r['KESIF_ortR']}  OOS {r['OOS_ortR']}  KÖR {r['KOR_ortR']}",
              flush=True)
    cells = pd.DataFrame(rows)
    cells.to_csv(OUT / "cells.csv", index=False)
    pd.to_pickle({"trades": trades, "placebo": plc}, OUT / "trades_placebo.pkl")
    print("hücreler yazıldı:", len(cells))


if __name__ == "__main__":
    main()
