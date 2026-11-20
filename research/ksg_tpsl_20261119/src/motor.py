"""motor.py — KSG gece yolları: T braket, R sabah kurtarma, A ekleme, M kapanış emri payı (PROTOCOL.md). Gece başına tablo üretir."""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]
for p in ("research/korku_evren_20261119/src", "research/ndx_10y_1m_20261116/src", "research/ndx_tf_yapilandirma_20261117/src"):
    sys.path.insert(0, str(ROOT / p))
import lib  # noqa: E402

NY = "America/New_York"
FIN = lib.FIN_BP_PER_DAY
TP_K = (20, 30, 40, 60, 80, 120)
SL_S = (None, 50, 100, 150, 250)
R_K = (0, 30, 60, 100)
R_H = ("10:00", "10:30", "11:00", "12:00", "16:00", "BE")
A_T = ("18:00", "20:00", "00:00", "03:00", "06:00")
A_K = (40, 80, 120)


def ts(d, hh: int, mm: int) -> int:
    return int(pd.Timestamp(datetime(d.year, d.month, d.day, hh, mm), tz=NY).timestamp())


def hm(s: str) -> tuple[int, int]:
    h, m = s.split(":")
    return int(h), int(m)


# ---------------- besleme ----------------
def load(name: str) -> tuple[pd.DataFrame, int]:
    """Ortak biçim t,o,h,l,c,sp (sp fiyat birimi) + adım (s)."""
    if name.startswith("MT5_") or name == "DUKA_NDX":
        import esik as E
        b, st = E.feeds()[name]
        return b[["t", "o", "h", "l", "c", "sp"]].sort_values("t").reset_index(drop=True), st
    import kaynak
    if name == "DUKA_M30_2016_17":
        d, st, spr = kaynak.load_duka_m30_export(), 1800, 1.5
        d = d[d.t < int(pd.Timestamp("2018-01-01", tz="UTC").timestamp())]
    elif name == "EET30":
        d, st, spr = pd.read_parquet(ROOT / "research/ndx_tf_yapilandirma_20261117/out/ek/EET30_kalibre.parquet"), 1800, 1.5
    else:
        d, st, spr = pd.read_parquet(ROOT / "research/ndx_tf_yapilandirma_20261117/out/ek/NQ_kalibre.parquet"), 300, 0.25
    d = d.sort_values("t").drop_duplicates("t")
    return pd.DataFrame({"t": d.t.values.astype(np.int64), "o": d.open.values, "h": d.high.values, "l": d.low.values,
                         "c": d.close.values, "sp": np.full(len(d), spr)}), st


class Feed:
    def __init__(self, b: pd.DataFrame, step: int):
        self.t, self.o, self.h, self.l, self.sp = (b[c].values.astype(float) if c != "t" else b.t.values for c in ("t", "o", "h", "l", "sp"))
        self.step = step
        self.tol = max(step - 1, 299) if step < 1800 else 0

    def ix(self, u: int) -> int | None:
        """u'da açılan (ya da tol içinde ilk) mum."""
        i = int(np.searchsorted(self.t, u, side="left"))
        return i if i < len(self.t) and self.t[i] - u <= self.tol else None

    def days(self) -> list:
        ny = pd.to_datetime(self.t[:: max(1, 1800 // self.step)], unit="s", utc=True).tz_convert(NY)
        ds = sorted(set(ny.date))
        return [d for d in ds if d.weekday() < 5 and not lib.nyse.is_holiday(d)]


# ---------------- aileler ----------------
def bracket(F: Feed, i0: int, i1: int, E: float, k: int, s: int | None) -> float:
    """Brüt bp: [i0, i1) mumlarında TP limiti / stop; yoksa i1 açılışı."""
    hh, ll = F.h[i0:i1], F.l[i0:i1]
    tp = E * (1 + k / 1e4)
    jt = int(np.argmax(hh >= tp)) if (hh >= tp).any() else 10 ** 9
    js = 10 ** 9
    if s is not None:
        sl = E * (1 - s / 1e4)
        js = int(np.argmax(ll <= sl)) if (ll <= sl).any() else 10 ** 9
    if js <= jt and js < 10 ** 9:
        return (min(sl, F.o[i0 + js]) / E - 1) * 1e4
    if jt < 10 ** 9:
        return float(k)
    return (F.o[i1] / E - 1) * 1e4


def rescue(F: Feed, i930: int, d_nd, E: float, H: str) -> float | None:
    """09:30'dan sonra tutma; H saati açılışı ya da BE (giriş fiyatına limit, en geç 16:00)."""
    i16 = F.ix(ts(d_nd, 16, 0))
    if i16 is None:
        return None
    if H != "BE":
        j = F.ix(ts(d_nd, *hm(H)))
        return None if j is None else (F.o[j] / E - 1) * 1e4
    hh = F.h[i930:i16]
    return 0.0 if (hh >= E).any() else (F.o[i16] / E - 1) * 1e4


def night(F: Feed, d, nd) -> dict | None:
    i15, i16, i930 = F.ix(ts(d, 15, 0)), F.ix(ts(d, 16, 0)), F.ix(ts(nd, 9, 30))
    if i15 is None or i16 is None or i930 is None or i930 <= i16:
        return None
    E = F.o[i16] + F.sp[i16]
    fin = FIN * (nd - d).days
    base = (F.o[i930] / E - 1) * 1e4 - fin
    r = {"d": pd.Timestamp(d), "nd": pd.Timestamp(nd), "ksg": bool(F.o[i16] < F.o[i15]), "base": base,
         "isabet_base": base > 0, "x930": base + fin}
    for k in TP_K:
        for s in SL_S:
            r[f"T_{k}_{s}"] = bracket(F, i16, i930, E, k, s) - fin
    for H in R_H:
        v = rescue(F, i930, nd, E, H)
        r[f"hold_{H}"] = None if v is None else v - fin
    for t in A_T:
        dd = d if t in ("18:00", "20:00") else nd
        j = F.ix(ts(dd, *hm(t)))
        if j is None or not (i16 < j < i930):
            r[f"pnl_{t}"], r[f"inc_{t}"] = np.nan, np.nan
            continue
        r[f"pnl_{t}"] = (F.o[j] / E - 1) * 1e4
        r[f"inc_{t}"] = (F.o[i930] / (F.o[j] + F.sp[j]) - 1) * 1e4 - fin
    j50 = F.ix(ts(d, 15, 50)) if F.step < 1800 else None
    drop = F.o[i15] - F.o[i16]
    r["m"] = (F.o[j50] - F.o[i16]) / drop if (j50 is not None and drop > 0) else np.nan
    return r


def table(name: str) -> pd.DataFrame:
    b, st = load(name)
    F = Feed(b, st)
    ds = F.days()
    rows = []
    for i, d in enumerate(ds[:-1]):
        nd = ds[i + 1]
        if (nd - d).days > 5 or lib.nyse.is_early_close(d) or lib.nyse.is_early_close(nd):
            continue
        r = night(F, d, nd)
        if r is not None:
            rows.append(r)
    N = pd.DataFrame(rows)
    N["besleme"] = name
    N["blk"] = N.d.dt.to_period("M").astype(str)
    return N


def add_rescue(N: pd.DataFrame) -> pd.DataFrame:
    """R hücreleri: 09:30 net ≤ −k ise hold_H, değilse base."""
    for k in R_K:
        lose = N.x930 <= -k
        for H in R_H:
            h = N[f"hold_{H}"]
            N[f"R_{k}_{H}"] = np.where(lose & h.notna(), h, N.base)
    return N
