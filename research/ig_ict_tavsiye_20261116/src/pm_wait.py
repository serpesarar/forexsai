"""IG-02 — "AM öncesi 400 puandan fazla düştüyse PM'i bekle", Dukascopy NDX 1m (PROTOCOL.md T2)."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT.parent / "nom_20261113" / "data" / "ndx_1m_v3_duka.parquet"
OUT = ROOT / "results"
SESS = {"AM": (9 * 60 + 30, 12 * 60), "PM": (13 * 60 + 30, 16 * 60)}
OR_MIN = 15
TGT_R = 2.0
DROP_PTS, DROP_PCT = -400.0, -0.016
RACE_FRAC, RANGE_LOOKBACK = 0.25, 20
SPLIT = pd.Timestamp("2022-01-01")
N_BOOT = 4000
RNG = np.random.default_rng(20261116)


def load() -> pd.DataFrame:
    d = pd.read_parquet(DATA)
    et = pd.to_datetime(d.t, unit="s", utc=True).dt.tz_convert("America/New_York").dt.tz_localize(None)
    d["mins"] = et.dt.hour * 60 + et.dt.minute
    d["date"] = et.dt.normalize()
    return d[["date", "mins", "open", "high", "low", "close", "spr"]]


def orb(s: pd.DataFrame) -> float | None:
    """İlk 15 dk aralığı kırılımı, ilk kırılım yönünde, stop karşı uç, 2R, seans sonu."""
    rng, rest = s.iloc[:OR_MIN], s.iloc[OR_MIN:]
    if len(rng) < OR_MIN - 2 or len(rest) < 10:
        return None
    hi, lo = rng.high.max(), rng.low.min()
    c = rest.close.to_numpy()
    brk = np.flatnonzero((c > hi) | (c < lo))
    if len(brk) == 0 or brk[0] + 1 >= len(rest):
        return None
    k = brk[0] + 1
    side = 1 if c[brk[0]] > hi else -1
    e = rest.open.iat[k]
    stop = lo if side > 0 else hi
    risk = (e - stop) * side
    if risk <= 0:
        return None
    cost = rest.spr.iat[k] / risk
    h, l = rest.high.to_numpy()[k:], rest.low.to_numpy()[k:]
    for hh, ll in zip(h, l):
        if (side > 0 and ll <= stop) or (side < 0 and hh >= stop):
            return -1 - cost
        if (side > 0 and hh >= e + TGT_R * risk) or (side < 0 and ll <= e - TGT_R * risk):
            return TGT_R - cost
    return side * (rest.close.iat[-1] - e) / risk - cost


def race_whipsaw(s: pd.DataFrame, x: float) -> float | None:
    """Açılıştan ±x yarışı: önce bir tarafa vurup sonra öbürüne de vurdu mu (1/0)."""
    o = s.open.iat[0]
    up = np.flatnonzero(s.high.to_numpy() >= o + x)
    dn = np.flatnonzero(s.low.to_numpy() <= o - x)
    if len(up) == 0 and len(dn) == 0:
        return None
    return float(len(up) > 0 and len(dn) > 0)


def per_day(d: pd.DataFrame) -> pd.DataFrame:
    rows, prev_close = [], None
    ranges = {k: [] for k in SESS}
    for day, g in d.groupby("date"):
        if day.weekday() >= 5:
            continue
        rth = g[(g.mins >= SESS["AM"][0]) & (g.mins < SESS["PM"][1])]
        if len(rth) < 300:
            prev_close = None
            continue
        row: dict = {"date": day}
        if prev_close is not None:
            o = rth.open.iat[0]
            row["drop_pts"], row["drop_pct"] = o - prev_close, o / prev_close - 1
        for name, (a, b) in SESS.items():
            s = g[(g.mins >= a) & (g.mins < b)]
            if len(s) < 0.9 * (b - a):
                continue
            rg = s.high.max() - s.low.min()
            o = s.open.iat[0]
            row[f"{name}_ret_bp"] = (s.close.iat[-1] / o - 1) * 1e4
            row[f"{name}_eff"] = abs(s.close.iat[-1] - o) / rg if rg > 0 else np.nan
            row[f"{name}_orb"] = orb(s)
            hist = ranges[name][-RANGE_LOOKBACK:]
            if len(hist) == RANGE_LOOKBACK:
                row[f"{name}_whip"] = race_whipsaw(s, RACE_FRAC * float(np.median(hist)))
            ranges[name].append(rg)
        rows.append(row)
        prev_close = rth.close.iat[-1]
    return pd.DataFrame(rows)


def boot_mean_p(x: np.ndarray) -> float:
    x = x[~np.isnan(x)]
    if len(x) < 3:
        return float("nan")
    sel = RNG.integers(0, len(x), size=(N_BOOT, len(x)))
    return round(float((x[sel].mean(1) > 0).mean()), 3)


def block(t: pd.DataFrame) -> dict:
    out = {"n_days": len(t)}
    for col in ("AM_ret_bp", "PM_ret_bp", "AM_eff", "PM_eff", "AM_whip", "PM_whip", "AM_orb", "PM_orb"):
        x = t[col].astype(float).to_numpy()
        out[col] = round(float(np.nanmean(x)), 4) if np.isfinite(x).any() else None
    out["AM_orb_n"] = int(t.AM_orb.notna().sum())
    out["PM_orb_n"] = int(t.PM_orb.notna().sum())
    pair = t[["AM_orb", "PM_orb"]].dropna().astype(float)
    dd = (pair.PM_orb - pair.AM_orb).to_numpy()
    out["PM_minus_AM_orb"] = round(float(dd.mean()), 4) if len(dd) else None
    out["P_PM_better"] = boot_mean_p(dd)
    out["P_AM_long_pos"] = boot_mean_p(t.AM_ret_bp.astype(float).to_numpy())
    out["P_PM_long_pos"] = boot_mean_p(t.PM_ret_bp.astype(float).to_numpy())
    return out


def interaction(t: pd.DataFrame, mask: pd.Series) -> dict:
    def diffs(x: pd.DataFrame) -> np.ndarray:
        p = x[["AM_orb", "PM_orb"]].dropna().astype(float)
        return (p.PM_orb - p.AM_orb).to_numpy()
    a, b = diffs(t[mask]), diffs(t[~mask])
    sa = RNG.integers(0, len(a), size=(N_BOOT, len(a)))
    sb = RNG.integers(0, len(b), size=(N_BOOT, len(b)))
    dd = a[sa].mean(1) - b[sb].mean(1)
    return {"interaction": round(float(a.mean() - b.mean()), 4), "P": round(float((dd > 0).mean()), 3)}


def main() -> None:
    OUT.mkdir(exist_ok=True)
    t = per_day(load())
    t = t.dropna(subset=["drop_pts"])
    t.to_csv(OUT / "pm_gunler.csv", index=False)
    res: dict = {"span": [str(t.date.min().date()), str(t.date.max().date())]}
    defs = {"P400": t.drop_pts <= DROP_PTS, "R16": t.drop_pct <= DROP_PCT}
    for name, m in defs.items():
        res[name] = {"all": block(t[m]), "control": block(t[~m]), **interaction(t, m)}
        for per, pm in (("2018-21", t.date < SPLIT), ("2022-26", t.date >= SPLIT)):
            if (m & pm).sum() >= 5:
                res[name][per] = {"drop": block(t[m & pm]), "control": block(t[~m & pm]),
                                  **interaction(t[pm], m[pm])}
    (OUT / "pm_ozet.json").write_text(json.dumps(res, indent=1, default=str, ensure_ascii=False))
    print(json.dumps(res, indent=1, default=str, ensure_ascii=False))


if __name__ == "__main__":
    main()
