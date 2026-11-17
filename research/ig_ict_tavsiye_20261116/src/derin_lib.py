"""EK-1 ortak katman: Duka NDX 1m → gün × dakika matrisleri (NY saati), günlük tablo, istatistik."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT.parent
M1_CACHE = RES / "ndx_10y_1m_20261116" / "cache" / "m1_ny.parquet"
DAILY = RES / "ndx_10y_1m_20261116" / "cache" / "daily.parquet"
MACRO = RES / "nom_20261113" / "data" / "macro" / "macro_daily.parquet"
OUT = ROOT / "results"
CACHE = ROOT / "cache"
SPLIT = np.datetime64("2023-01-01")
VIX_TH = 18.4
OPEN, CLOSE = 570, 960  # 09:30, 16:00 NY
RNG = np.random.default_rng(20261116)
DOW_NAMES = ["Pzt", "Sal", "Car", "Per", "Cum"]


@dataclass
class Mat:
    days: np.ndarray      # datetime64[D], tam RTH günleri
    O: np.ndarray         # gün × 1440 (NaN = bar yok)
    H: np.ndarray
    L: np.ndarray
    C: np.ndarray
    S: np.ndarray         # spread (puan)
    prevO: np.ndarray     # bir önceki NY tarihinin matrisi (gece için), satır hizalı
    prevH: np.ndarray
    prevL: np.ndarray
    prevC: np.ndarray
    dow: np.ndarray
    vix_prev: np.ndarray  # önceki işlem gününün VIX kapanışı
    kesif: np.ndarray     # bool


def _pivot(df: pd.DataFrame, col: str, day_ix: np.ndarray, n_days: int) -> np.ndarray:
    m = np.full((n_days, 1440), np.nan, dtype=np.float64)
    m[day_ix, df.m.to_numpy()] = df[col].to_numpy()
    return m


def load_mat() -> Mat:
    CACHE.mkdir(exist_ok=True)
    cp = CACHE / "mat.npz"
    if cp.exists():
        z = np.load(cp, allow_pickle=False)
        return Mat(**{k: z[k] for k in z.files})
    df = pd.read_parquet(M1_CACHE)
    all_days = np.unique(df.d.to_numpy())
    pos = {d: i for i, d in enumerate(all_days)}
    di = np.array([pos[d] for d in df.d.to_numpy()])
    n = len(all_days)
    O, H, L, C, S = (_pivot(df, c, di, n) for c in ("open", "high", "low", "close", "spr"))
    rth_n = np.isfinite(C[:, OPEN:CLOSE]).sum(1)
    full = (rth_n >= 380) & (pd.to_datetime(all_days).dayofweek < 5)
    idx = np.flatnonzero(full)
    idx = idx[idx > 0]
    prev = idx - 1  # önceki NY takvim tarihi satırı (Pazartesi için Pazar akşamı)
    days = all_days[idx]
    mac = pd.read_parquet(MACRO)[["date", "VIX_close"]].dropna()
    mac["date"] = pd.to_datetime(mac.date).values.astype("datetime64[D]")
    vix = pd.Series(mac.VIX_close.to_numpy(), index=mac.date)
    vix_prev = np.array([vix[vix.index < d].iloc[-1] if (vix.index < d).any() else np.nan for d in days])
    m = Mat(days=days, O=O[idx], H=H[idx], L=L[idx], C=C[idx], S=S[idx], prevO=O[prev], prevH=H[prev],
            prevL=L[prev], prevC=C[prev], dow=pd.to_datetime(days).dayofweek.to_numpy(),
            vix_prev=vix_prev, kesif=days < SPLIT)
    np.savez_compressed(cp, **m.__dict__)
    return m


def first_valid(row_block: np.ndarray, axis: int = 1) -> np.ndarray:
    """Her satırda ilk sonlu değer (ör. dilimin ilk açılışı)."""
    ok = np.isfinite(row_block)
    j = ok.argmax(axis)
    out = row_block[np.arange(row_block.shape[0]), j]
    out[~ok.any(axis)] = np.nan
    return out


def last_valid(row_block: np.ndarray) -> np.ndarray:
    return first_valid(row_block[:, ::-1])


def price_open(m: Mat, minute: int) -> np.ndarray:
    return first_valid(m.O[:, minute:minute + 5])


def price_close_before(m: Mat, minute: int) -> np.ndarray:
    return last_valid(m.C[:, max(0, minute - 5):minute])


def prev_rth_close(m: Mat) -> np.ndarray:
    """Önceki işlem gününün 16:00 kapanışı (gün listesinde bir önceki satır)."""
    c = price_close_before(m, CLOSE)
    out = np.full_like(c, np.nan)
    out[1:] = c[:-1]
    return out


def tstat(x: np.ndarray) -> tuple[float, float, int]:
    x = x[np.isfinite(x)]
    n = len(x)
    if n < 3:
        return np.nan, np.nan, n
    sd = x.std(ddof=1)
    return float(x.mean()), float(x.mean() / sd * np.sqrt(n)) if sd > 0 else np.nan, n


def welch(a: np.ndarray, b: np.ndarray) -> tuple[float, float]:
    a, b = a[np.isfinite(a)], b[np.isfinite(b)]
    if len(a) < 3 or len(b) < 3:
        return np.nan, np.nan
    d = a.mean() - b.mean()
    se = np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
    return float(d), float(d / se) if se > 0 else np.nan


def passes(t_k: float, t_t: float, n_t: int, min_n: int = 30) -> bool:
    return bool(np.isfinite(t_k) and np.isfinite(t_t) and abs(t_k) >= 2.0 and n_t >= min_n
                and np.sign(t_t) == np.sign(t_k) and abs(t_t) >= 1.65)
