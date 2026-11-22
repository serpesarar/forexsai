"""EK-7: ABD dışı planlı veri anı (:00/:30) sıçrama devamı — Dukascopy 1m BID + Çarşamba ASK spread modeli (PROTOCOL.md EK-7)."""
from __future__ import annotations

import itertools
import json
import sys

import numpy as np
import pandas as pd

import core
import d1
import spike

PAIRS = ["AUDUSD", "GBPUSD", "EURUSD", "USDCAD"]
GRID = list(itertools.product([0.15, 0.25], ["DEVAM", "GERI"], [0.25, 0.5], [1.0, 2.0], [15, 60]))
NEWS_MULT = 3.0


def load(pair: str) -> pd.DataFrame:
    x = pd.read_parquet(core.HERE / "data" / f"duka_{pair}_1m.parquet")
    x["ts"] = pd.to_datetime(x.t, unit="s")
    x["yr"], x["hr"] = x.ts.dt.year, x.ts.dt.hour
    w = x.dropna(subset=["a_o"])
    sp = ((w.a_o - w.o) / w.o * 1e4).groupby([w.yr, w.hr]).median()
    x["spr"] = [sp.get((y, h), np.nan) for y, h in zip(x.yr, x.hr)] if len(x) < 0 else x.set_index(["yr", "hr"]).index.map(sp).values
    x["spr"] = x.spr.fillna(x.spr.median())
    return x.reset_index(drop=True)


def candidates(x: pd.DataFrame, minutes: tuple[int, int], us_T: set[int]) -> np.ndarray:
    t = x.t.values
    mnt = x.ts.dt.minute.values
    wd = x.ts.dt.weekday.values
    i = np.where(np.isin(mnt, minutes) & (wd < 5))[0]
    i = i[i + 3 < len(x)]
    ok = (t[i + 2] == t[i] + 120) & (t[i + 3] == t[i] + 180)
    i = i[ok]
    return i[~np.isin(t[i], list(us_T))]


def run(pair: str, minutes: tuple[int, int], us_T: set[int]) -> pd.DataFrame:
    x = load(pair)
    atr = spike.atr_prev(pair)
    day = x.ts.dt.normalize()
    a_idx = atr.index.searchsorted(day.values, side="left") - 1
    av = np.where(a_idx >= 0, atr.values[np.clip(a_idx, 0, None)], np.nan)
    o, h, l, c = x.o.values, x.h.values, x.l.values, x.c.values
    i = candidates(x, minutes, us_T)
    s = c[i + 2] - o[i]
    comm = core.comm_bp(pair)
    out = []
    for ci, (q, mode, tpk, slk, tmin) in enumerate(GRID):
        m = np.abs(s) >= q * av[i]
        ii, ss = i[m], s[m]
        if len(ii) == 0:
            continue
        side = np.sign(ss).astype(np.int64) * (1 if mode == "DEVAM" else -1)
        ei, xi, ep, xp, why = core.race(o, h, l, c, (ii + 2).astype(np.int64), side, tpk * np.abs(ss), slk * np.abs(ss),
                                         np.full(len(ii), tmin, np.int64), np.full(len(o), len(o) - 1, np.int64))
        k = ei >= 0
        t = pd.DataFrame({"side": side[k], "ep": ep[k], "xp": xp[k], "why": why[k], "ei": ei[k], "xi": xi[k],
                          "sl_bp": slk * np.abs(ss[k]) / ep[k] * 1e4, "spike_bp": np.abs(ss[k]) / ep[k] * 1e4})
        t["gross"] = t.side * (t.xp - t.ep) / t.ep * 1e4
        t["cost"] = (NEWS_MULT * x.spr.values[t.ei.values] + x.spr.values[t.xi.values]) / 2 + comm
        t["net"] = t.gross - t.cost
        t["R"] = t.net / t.sl_bp
        t["time"] = x.ts.values[t.ei.values]
        t["hr"] = x.hr.values[t.ei.values]
        t["cell"], t["pair"] = ci, pair
        out.append(t)
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame()


def main() -> None:
    us_T = set(spike.events()["T"].astype(int))
    allt = []
    for p in PAIRS:
        for grp, mins in (("PLANLI", (0, 30)), ("PLASEBO", (13, 43))):
            t = run(p, mins, us_T)
            t["grp"] = grp
            allt.append(t)
        print(p, flush=True)
    T = pd.concat(allt, ignore_index=True)
    T["day"] = pd.to_datetime(T.time).dt.normalize()
    y = pd.to_datetime(T.time).dt.year
    T["per"] = np.select([y <= 2020, y <= 2022], ["KESIF", "TEST"], "KOR")
    T.to_parquet(core.RES / "trades_SPIKE7.parquet")
    P = T[T.grp == "PLANLI"]
    K = P[P.per == "KESIF"]
    H = pd.DataFrame([{"cell": ci, "def": GRID[ci], **core.summ(g)} for ci, g in K.groupby("cell")])
    pd.set_option("display.width", 250)
    print(H.sort_values("ort", ascending=False).head(12).to_string(index=False))
    S = H[(H.wr >= 80) & (H.ort > 0) & (H.n >= 150)].sort_values("t", ascending=False).head(3)
    print("SEÇİLEN", S.cell.tolist())
    res = {}
    for ci in S.cell:
        d = {"def": str(GRID[ci])}
        for nm in ("KESIF", "TEST", "KOR"):
            d[nm] = core.summ(P[(P.cell == ci) & (P.per == nm)], boot=True)
        d["plasebo_KOR"] = core.summ(T[(T.grp == "PLASEBO") & (T.cell == ci) & (T.per == "KOR")])
        res[int(ci)] = d
    print(json.dumps(res, indent=1, ensure_ascii=False, default=str))
    (core.RES / "spike7.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
