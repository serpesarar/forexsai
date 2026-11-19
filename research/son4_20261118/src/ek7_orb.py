"""EK-7: ORB×VIX OPEX vetosu bağımsız beslemelerde (NQ 5m 2019–24, MT5 NAS100 M15 2022–26) + Duka 5m kopya sağlaması."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import ek3_veto as E3
import ox

R = ox.ROOT
sys.path.insert(0, str(R / "research/ndx_10y_1m_20261116/src"))
sys.path.insert(0, str(R / "research/ndx_tf_yapilandirma_20261117/src"))
import lib  # noqa: E402
import kaynak  # noqa: E402
import ksg_ek2 as KE  # noqa: E402

G, V = ox.G, ox.V
NY = "America/New_York"


def agg(b: pd.DataFrame, step: int, to: int) -> pd.DataFrame:
    k = (b.t // to) * to
    g = b.assign(k=k).groupby("k")
    return pd.DataFrame({"t": g.t.first().index.values, "o": g.o.first().values, "h": g.h.max().values, "l": g.l.min().values,
                         "c": g.c.last().values, "sp": g.sp.first().values})


def orb_generic(b: pd.DataFrame, step: int, vixp: dict) -> pd.DataFrame:
    x = G._local(b, NY)
    rows = []
    for d, g in x.groupby("day"):
        v = vixp.get(d)
        if v is None or v < 18.4 or pd.Timestamp(d).dayofweek >= 5 or not G.nyse_ok(d):
            continue
        mn, o, h, l, c, sp = (g[k].values for k in ("mn", "o", "h", "l", "c", "sp"))
        orm = (mn >= 570) & (mn + step // 60 <= 585)
        if orm.sum() < 1:
            continue
        hi, lo = h[orm].max(), l[orm].min()
        mid = (hi + lo) / 2
        cand = np.flatnonzero((mn >= 585) & (mn + step // 60 <= 930) & (c > hi))
        if not cand.size or cand[0] + 1 >= len(mn):
            continue
        e = cand[0] + 1
        ask = o[e] + sp[e]
        risk = ask - mid
        if risk <= 0.0005 * ask:
            continue
        tp = ask + 2 * risk
        px = None
        for j in range(e, len(mn)):
            if mn[j] >= 955:
                px = o[j]
                break
            if l[j] <= mid:
                px = min(mid, o[j])
                break
            if h[j] >= tp:
                px = max(tp, o[j])
                break
        if px is None:
            px = c[-1]
        rows.append({"d": pd.Timestamp(d), "R": (px - ask) / risk})
    return pd.DataFrame(rows)


def mt5_m15() -> pd.DataFrame:
    x = pd.read_csv(R / "research/c1_turev_20261105/data/mt5/NAS100_M15.csv.gz")
    t = kaynak.server_to_utc(x["t"].to_numpy())
    d = pd.DataFrame({"t": t.astype(np.int64), "o": x.o, "h": x.h, "l": x.l, "c": x.c, "sp": np.where(x.sp > 0, x.sp * 0.1, 1.3)})
    return d.dropna().drop_duplicates("t").sort_values("t").reset_index(drop=True)


def cmp(t: pd.DataFrame, win: set) -> dict:
    wd = t.d.dt.dayofweek.isin([2, 3, 4]).values
    ic = t.d.isin(win).values
    a, b = t[ic].R.values, t[wd & ~ic].R.values
    if len(a) < 5:
        return {"n": int(len(a))}
    r = np.random.default_rng(51)
    bs = r.choice(a, (5000, len(a))).mean(1) - r.choice(b, (5000, len(b))).mean(1)
    return {"n_ic": int(len(a)), "n_dis": int(len(b)), "ic_R": round(float(a.mean()), 3), "dis_R": round(float(b.mean()), 3),
            "fark": round(float(a.mean() - b.mean()), 3), "P_fark_eksi": round(float((bs < 0).mean()), 4), "tum_R": round(float(t.R.mean()), 3)}


def main() -> None:
    idx = pd.DatetimeIndex(sorted(set(V.ndx_frame().index)))
    win = E3.pre_days(idx, (0, 1, 2))
    out = {}
    duka = G.ndx_bars()
    days = sorted(set(pd.to_datetime(duka.t, unit="s", utc=True).dt.tz_convert(NY).dt.date))
    vixp = lib.vix_prev_map(days + [pd.Timestamp("2026-12-31").date()])
    d5 = agg(duka, 60, 300)
    td = orb_generic(d5, 300, vixp)
    out["sağlama_DUKA_5m_genel"] = cmp(td, win)
    nq, st = KE.bars("NQ")
    out["NQ_5m_2019_2024"] = cmp(orb_generic(nq, st, lib.vix_prev_map(sorted(set(pd.to_datetime(nq.t, unit="s", utc=True).dt.tz_convert(NY).dt.date)))), win)
    m15 = mt5_m15()
    out["MT5_NAS100_M15_2022_2026"] = cmp(orb_generic(m15, 900, lib.vix_prev_map(sorted(set(pd.to_datetime(m15.t, unit="s", utc=True).dt.tz_convert(NY).dt.date)))), win)
    for k, v in out.items():
        print(k, v)
    Path(__file__).resolve().parents[1].joinpath("results/ek7_orb.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
