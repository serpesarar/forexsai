"""EK-2: ABD olay günü devamı × yüksek isabet geometrisi, 7 USD majör (PROTOCOL.md EK-2)."""
from __future__ import annotations

import datetime as dt
import itertools
import json

import numpy as np
import pandas as pd

import core
import d1

MAJ = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "NZDUSD", "USDCAD", "USDCHF"]
GRID = list(itertools.product([1.0, 1.5, 2.0], [0.15, 0.25, 0.35], [1.0, 1.5, 2.0], [1, 2]))
R = core.HERE.parent


def nfp_rule(y: int, m: int) -> dt.date:
    d12 = dt.date(y, m, 12)
    sat = d12 + dt.timedelta(days=(5 - d12.weekday()) % 7)
    r = sat + dt.timedelta(days=20)
    if r.month == 7 and r.day in (3, 4):
        r -= dt.timedelta(days=1)
    return r


def events() -> pd.DataFrame:
    c = pd.read_csv(R / "xau_best_days_20261015/makro/out/calendar.csv")[["event", "date"]]
    f = pd.read_csv(R / "kapi_genis_20261118/data/fomc_1994_2007.csv")[["event", "date"]]
    n = pd.DataFrame({"event": "NFP", "date": [nfp_rule(y, m).isoformat() for y in range(1994, 2008) for m in range(2, 13)]})
    e = pd.concat([c, f, n], ignore_index=True)
    e["date"] = pd.to_datetime(e.date).dt.normalize()
    return e[e.date < pd.Timestamp("2026-11-14")]


def load(pair: str) -> pd.DataFrame:
    x = d1.load_d1(pair)
    m15 = core.load(pair)
    base = float((m15.cost - core.comm_bp(pair)).median())
    sp = (x.sp.astype(float) * core.point(pair) / x.o * 1e4).fillna(0).values
    c = np.where(x.srv < pd.Timestamp("2008-01-01"), 1.5 * sp, 1.5 * np.fmax(sp, base)) + core.comm_bp(pair)
    x["cost"] = c
    return x[x.srv >= pd.Timestamp("1993-06-01")].reset_index(drop=True)


def cell_trades(x: pd.DataFrame, pair: str, mask: np.ndarray, cell: tuple, side_override: np.ndarray | None = None) -> pd.DataFrame:
    k, tpk, slk, hold = cell
    big = (x.r.abs() >= k * x.sig20).values & x.atr.gt(0).values
    idx = np.where(mask & big)[0]
    side = np.sign(x.r.values[idx]).astype(int) if side_override is None else side_override[idx]
    keep = side != 0
    idx, side = idx[keep], side[keep]
    if len(idx) == 0:
        return pd.DataFrame()
    return d1.trades(x, pair, idx, side, (tpk, slk, hold))


def per(t: pd.Series) -> np.ndarray:
    return np.select([t < pd.Timestamp("2008-01-01"), t < pd.Timestamp("2017-01-01")], ["ESKI", "KESIF"], "SON")


def main() -> None:
    ev = events()
    evd = set(ev.date)
    old_ok = set(ev[ev.event.isin(["NFP", "FOMC"])].date)
    rows = []
    for pair in MAJ:
        x = load(pair)
        day = x.srv.dt.normalize()
        is_ev = day.isin(evd).values & ((day >= "2008-01-01").values | day.isin(old_ok).values)
        not_ev = ~day.isin(evd).values
        for ci, cell in enumerate(GRID):
            for grp, m in (("OLAY", is_ev), ("HABERSIZ", not_ev)):
                t = cell_trades(x, pair, m, cell)
                if len(t):
                    t["pair"], t["cell"], t["grp"] = pair, ci, grp
                    rows.append(t)
        print(pair, int(is_ev.sum()), flush=True)
    T = pd.concat(rows, ignore_index=True)
    T["per"] = per(T.time)
    T.to_parquet(core.RES / "trades_EK2.parquet")


if __name__ == "__main__":
    main()
