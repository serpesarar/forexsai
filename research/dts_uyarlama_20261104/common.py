"""DTS ortak: arşiv yükleyici (npz), 1d türetme, ay-blok bootstrap. Ön-kayıt: PROTOCOL.md."""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
ARCH = ROOT / "backend/data/candle_history"
SYMS = ("NDX", "GDAXI", "XAUUSD", "USOIL")
SPREAD = {"NDX": 1.3, "GDAXI": 1.5, "XAUUSD": 0.25, "USOIL": 0.028}
B = 5000


def load(sym: str, tf: str) -> pd.DataFrame:
    if tf == "1d":
        return to_daily(load(sym, "1h"))
    z = np.load(ARCH / f"{sym}_{tf}.npz")
    d = pd.DataFrame({"ts": pd.to_datetime(z["ts"], unit="s", utc=True), "open": z["open"], "high": z["high"],
                      "low": z["low"], "close": z["close"]})
    return d.sort_values("ts").drop_duplicates("ts").reset_index(drop=True)


def to_daily(h: pd.DataFrame) -> pd.DataFrame:
    ny = h.ts.dt.tz_convert("America/New_York").dt.tz_localize(None) - pd.Timedelta(hours=17)
    g = h.assign(k=ny.dt.floor("1D").to_numpy()).groupby("k", sort=True)
    d = g.agg(ts=("ts", "first"), open=("open", "first"), high=("high", "max"), low=("low", "min"),
              close=("close", "last"), n=("close", "size"))
    return d[d.n >= 15].drop(columns="n").reset_index(drop=True)


def month_boot(x: np.ndarray, months: np.ndarray, seed: int = 0) -> float:
    """P(ortalama > 0), takvim-ayı blok bootstrap."""
    ok = np.isfinite(x)
    x, months = x[ok], months[ok]
    if len(x) < 10:
        return float("nan")
    u, inv = np.unique(months, return_inverse=True)
    s, n = np.bincount(inv, x), np.bincount(inv)
    i = np.random.default_rng(seed).integers(0, len(u), size=(B, len(u)))
    return float(((s[i].sum(1) / n[i].sum(1)) > 0).mean())


def clusters(idx: np.ndarray, gap: int) -> np.ndarray:
    """Sıralı olay indeksleri → küme etiketi (arada ≥ gap bar boşluk yeni küme)."""
    if len(idx) == 0:
        return np.array([], dtype=int)
    return np.r_[0, np.cumsum(np.diff(idx) >= gap)]
