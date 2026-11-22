"""EK-6: ABD veri anı sıçraması, Dukascopy 1m BID+ASK (PROTOCOL.md EK-6)."""
from __future__ import annotations

import itertools
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

import core
import d1
import duka_olay as du

ET = ZoneInfo("America/New_York")
GRID = list(itertools.product([1, 3], [0.15, 0.30], ["DEVAM", "GERI"], [0.25, 0.5], [1.0, 2.0], [15, 60]))
PER = [("KESIF", 2012, 2018), ("TEST", 2019, 2022), ("KOR", 2023, 2026)]


def events() -> pd.DataFrame:
    c = pd.read_csv(core.HERE.parent / "xau_best_days_20261015/makro/out/calendar.csv")
    c = c[c.event.isin(["NFP", "CPI", "FOMC"])].copy()
    c["date"] = pd.to_datetime(c.date)
    c = c[(c.date >= "2012-01-01") & (c.date <= "2026-11-13")]
    hm = {"NFP": (8, 30), "CPI": (8, 30), "FOMC": (14, 0)}
    c["T"] = [int(pd.Timestamp(d.year, d.month, d.day, *hm[e], tz=ET).timestamp()) for d, e in zip(c.date, c.event)]
    return c.drop_duplicates("T").reset_index(drop=True)


def atr_prev(pair: str) -> pd.Series:
    x = d1.load_d1(pair)
    return pd.Series(x.atr.values, index=x.srv.dt.normalize()).dropna()


def pair_trades(pair: str, ev: pd.DataFrame, shift_min: int = 0) -> pd.DataFrame:
    x = pd.read_parquet(core.HERE / "data" / f"duka_{pair}_olay_1m.parquet").dropna(subset=["a_o"]).reset_index(drop=True)
    mo = (x.o + x.a_o).values / 2
    mh = (x.h + x.a_h).values / 2
    ml = (x.l + x.a_l).values / 2
    mc = (x.c + x.a_c).values / 2
    spr = ((x.a_o - x.o) / mo * 1e4).values
    pos = pd.Series(np.arange(len(x)), index=x.t.values)
    atr = atr_prev(pair)
    comm = core.comm_bp(pair)
    rows = []
    for _, e in ev.iterrows():
        T = int(e["T"]) + shift_min * 60
        a_ = atr[atr.index < e["date"].normalize()]
        if len(a_) == 0 or T not in pos.index:
            continue
        i0 = int(pos[T])
        rows.append((e["date"], e["event"], T, i0, float(a_.iloc[-1])))
    out = []
    for cell_i, (k, q, mode, tpk, slk, tmin) in enumerate(GRID):
        sig, side, tp, sl, meta = [], [], [], [], []
        for date, evn, T, i0, a in rows:
            ik = i0 + k - 1
            if ik + 1 >= len(x) or x.t.values[ik] != T + (k - 1) * 60 or x.t.values[ik + 1] != T + k * 60:
                continue
            s = mc[ik] - mo[i0]
            if abs(s) < q * a:
                continue
            sd = int(np.sign(s)) * (1 if mode == "DEVAM" else -1)
            sig.append(ik); side.append(sd); tp.append(tpk * abs(s)); sl.append(slk * abs(s)); meta.append((date, evn, abs(s) / mo[i0] * 1e4))
        if not sig:
            continue
        sig = np.array(sig)
        ei, xi, ep, xp, why = core.race(mo, mh, ml, mc, sig.astype(np.int64), np.array(side, np.int64), np.array(tp), np.array(sl),
                                         np.full(len(sig), tmin, np.int64), np.full(len(mo), len(mo) - 1, np.int64))
        m = ei >= 0
        t = pd.DataFrame({"side": np.array(side)[m], "ep": ep[m], "xp": xp[m], "why": why[m], "ei": ei[m], "xi": xi[m],
                          "sl_bp": np.array(sl)[m] / ep[m] * 1e4})
        md = [meta[j] for j in np.where(m)[0]]
        t["date"] = [z[0] for z in md]; t["event"] = [z[1] for z in md]; t["spike_bp"] = [z[2] for z in md]
        t["gross"] = t.side * (t.xp - t.ep) / t.ep * 1e4
        t["cost"] = (spr[t.ei.values] + spr[t.xi.values]) / 2 + comm
        t["net"] = t.gross - t.cost
        t["R"] = t.net / t.sl_bp
        t["cell"] = cell_i
        t["pair"] = pair
        out.append(t)
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame()


def main() -> None:
    ev = events()
    allt = []
    for p in du.PAIRS:
        for sh, nm in ((0, "OLAY"), (-60, "PLASEBO")):
            t = pair_trades(p, ev, sh)
            if len(t):
                t["grp"] = nm
                allt.append(t)
        print(p, flush=True)
    T = pd.concat(allt, ignore_index=True)
    T["time"] = pd.to_datetime(T.date)
    T["day"] = T.time
    T["per"] = np.select([T.time.dt.year <= 2018, T.time.dt.year <= 2022], ["KESIF", "TEST"], "KOR")
    T.to_parquet(core.RES / "trades_SPIKE.parquet")


if __name__ == "__main__":
    main()
