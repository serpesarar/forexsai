"""FX-YI aileleri (PROTOCOL.md'de dondurulmuş ızgara). Her hücre → işlem tablosu."""
from __future__ import annotations

import itertools

import numpy as np
import pandas as pd

import core

F1_WIN = {"A": range(1, 4), "B": range(1, 9), "C": range(9, 22)}
F1_GRID = list(itertools.product(F1_WIN, [2.0, 2.5, 3.0], ["MID", 0.5, 1.0], [1.5, 2.5, 4.0], [8, 24]))
F2_GRID = list(itertools.product([0.7, 1.0, 1.3], [0.15, 0.30], [0.5, 1.0]))
F3_GRID = list(itertools.product([0.25, 0.5], ["EDGE", "MID"], [0.5, 1.0], [16, 40]))


def f1(x: pd.DataFrame, cell: tuple, cost_mult: float = 1.0) -> pd.DataFrame:
    w, k, tpk, slk, tm = cell
    up = x.sma + k * x.sd
    dn = x.sma - k * x.sd
    ok = x.hr.isin(list(F1_WIN[w])) & x.atr.gt(0) & x.sd.gt(0)
    s_sell = ok & (x.c > up)
    s_buy = ok & (x.c < dn)
    idx = np.where(s_sell | s_buy)[0]
    if len(idx) == 0:
        return pd.DataFrame()
    side = np.where(s_buy.values[idx], 1, -1)
    atr = x.atr.values[idx]
    tp = np.abs(x.c.values[idx] - x.sma.values[idx]) if tpk == "MID" else tpk * atr
    sl = slk * atr
    return core.run(x, idx, side, tp, sl, np.full(len(idx), tm), cost_mult)


def f2(x: pd.DataFrame, cell: tuple, cost_mult: float = 1.0) -> pd.DataFrame:
    m, tpk, slk = cell
    disp = x.c - x.dopen
    ok = x.hr.between(2, 20) & x.atrd.gt(0)
    trig = ok & (disp.abs() >= m * x.atrd)
    first = trig & ~trig.groupby(x.day).cumsum().gt(1)
    idx = np.where(first)[0]
    if len(idx) == 0:
        return pd.DataFrame()
    side = -np.sign(disp.values[idx]).astype(int)
    ad = x.atrd.values[idx]
    return core.run(x, idx, side, tpk * ad, slk * ad, np.full(len(idx), 400), cost_mult)


def _asia(x: pd.DataFrame) -> pd.DataFrame:
    a = x[x.hr.between(2, 8)].groupby("day").agg(ah=("h", "max"), al=("l", "min"), an=("h", "size"))
    a = a[a.an >= 24]
    return a


def f3(x: pd.DataFrame, cell: tuple, cost_mult: float = 1.0) -> pd.DataFrame:
    b, tpm, slk, tm = cell
    a = _asia(x)
    ah = x.day.map(a.ah)
    al = x.day.map(a.al)
    rng = ah - al
    ok = x.hr.between(9, 12) & rng.gt(0)
    s_sell = ok & (x.c >= ah + b * rng)
    s_buy = ok & (x.c <= al - b * rng)
    trig = s_sell | s_buy
    first = trig & ~trig.groupby(x.day).cumsum().gt(1)
    idx = np.where(first)[0]
    if len(idx) == 0:
        return pd.DataFrame()
    side = np.where(s_buy.values[idx], 1, -1)
    c = x.c.values[idx]
    r = rng.values[idx]
    edge = np.where(side < 0, ah.values[idx], al.values[idx])
    mid = (ah.values[idx] + al.values[idx]) / 2
    target = edge if tpm == "EDGE" else mid
    tp = np.abs(c - target)
    return core.run(x, idx, side, tp, slk * r, np.full(len(idx), tm), cost_mult)


FAMS = {"F1": (f1, F1_GRID), "F2": (f2, F2_GRID), "F3": (f3, F3_GRID)}
