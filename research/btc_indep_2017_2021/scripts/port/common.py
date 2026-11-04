"""fam_turev ortak sabitler ve yardımcılar (prereg.md ile birebir)."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/Users/melihcanodacioglu/Desktop/panel/research/btc_indep_2017_2021")
DATA = ROOT / "data"
FAM = ROOT
CACHE = ROOT / "cache"
OUT = ROOT / "cache"

T0 = pd.Timestamp("2017-08-17", tz="UTC")
T_END = pd.Timestamp("2021-06-01", tz="UTC")
N = int((T_END - T0) / pd.Timedelta(minutes=1))  # 2.833.920

SEG = {
    "DISC": ("2017-08-17", "2020-01-11"),
    "OOS": ("2020-01-11", "2021-06-01"),
    "BLIND": ("2021-06-01", "2021-06-01"),
}  # etiket adları korunur (kod 0/1/2 kullanır); anlamı: A / PERP / boş
HS = (15, 35, 60)
RS = (1.0, 1.5, 2.0)
SL_MIN_BP = 19.0
SL_ATR = 1.1
COSTS = {"PEP": 1.85, "PEP_STRESS": 2.78, "BIN_MAKER": 4.0, "BIN_TAKER": 10.0}  # + PEP_FIX15 (15$/fiyat)
EPISODE_MIN = 60


def tmin(ts) -> int:
    t = pd.Timestamp(ts)
    if t.tzinfo is None:
        t = t.tz_localize("UTC")
    return int((t - T0) / pd.Timedelta(minutes=1))


def seg_bounds(name: str) -> tuple[int, int]:
    a, b = SEG[name]
    return tmin(a), tmin(b)


def seg_of(e: np.ndarray) -> np.ndarray:
    """0 = DISC, 1 = OOS, 2 = BLIND, -1 = hiçbiri."""
    out = np.full(len(e), -1, dtype=np.int8)
    for i, nm in enumerate(["DISC", "OOS", "BLIND"]):
        a, b = seg_bounds(nm)
        out[(e >= a) & (e < b)] = i
    return out


def year_of(e: np.ndarray) -> np.ndarray:
    ts = T0 + pd.to_timedelta(e, unit="min")
    return np.asarray(ts.year, dtype=np.int16)


def episode(t: np.ndarray, gap: int = EPISODE_MIN) -> np.ndarray:
    """Sıralı tetik dakikalarından epizod başlarını seç: önceki SEÇİLEN tetikten itibaren gap dk içinde olanlar atılır."""
    t = np.sort(np.unique(t))
    keep = []
    last = -10**12
    for x in t:
        if x - last > gap:
            keep.append(x)
            last = x
    return np.asarray(keep, dtype=np.int64)


def roll_z(x: pd.Series, n: int, minp: int, center: bool = True) -> pd.Series:
    m = x.rolling(n, min_periods=minp).mean().shift(1)
    s = x.rolling(n, min_periods=minp).std().shift(1)
    return (x - m) / s if center else x / s
