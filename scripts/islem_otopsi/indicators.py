"""Göstergeler + çok-zaman-dilimi erişimi (saf pandas/numpy, sızıntısız).

Nedensellik kuralı (defter E1/E16): bir karar anı ``t`` için yalnız BİTİŞİ ≤ t olan
barlar okunur. Yeniden örnekleme ``label/closed='left'`` ile yapılır ve erişim her
zaman bar BİTİŞ zamanı üzerinden (``last_closed``) — sol-etiket sızıntısı olmaz.
EMA/RSI/ATR/ADX özyinelemelidir (t'deki değer yalnız ≤t'ye bağlı).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import settings as S

TF_MINUTES = (5, 15, 60)
BARS_PER_DAY_5M = 288


def ema(x: pd.Series, n: int) -> pd.Series:
    return x.ewm(span=n, adjust=False).mean()


def rsi(close: pd.Series, n: int = S.RSI_N) -> pd.Series:
    d = close.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    rs = up / dn.replace(0, np.nan)
    return (100 - 100 / (1 + rs)).fillna(50.0)


def true_range(df: pd.DataFrame) -> pd.Series:
    pc = df["close"].shift(1)
    return pd.concat([df["high"] - df["low"], (df["high"] - pc).abs(), (df["low"] - pc).abs()], axis=1).max(axis=1)


def atr(df: pd.DataFrame, n: int = S.ATR_N) -> pd.Series:
    return true_range(df).ewm(alpha=1 / n, adjust=False).mean()


def adx(df: pd.DataFrame, n: int = S.ADX_N) -> pd.DataFrame:
    up = df["high"].diff()
    dn = -df["low"].diff()
    plus_dm = np.where((up > dn) & (up > 0), up, 0.0)
    minus_dm = np.where((dn > up) & (dn > 0), dn, 0.0)
    tr = true_range(df).ewm(alpha=1 / n, adjust=False).mean().replace(0, np.nan)
    pdi = 100 * pd.Series(plus_dm, index=df.index).ewm(alpha=1 / n, adjust=False).mean() / tr
    mdi = 100 * pd.Series(minus_dm, index=df.index).ewm(alpha=1 / n, adjust=False).mean() / tr
    dx = 100 * (pdi - mdi).abs() / (pdi + mdi).replace(0, np.nan)
    return pd.DataFrame({"plus_di": pdi, "minus_di": mdi, "adx": dx.ewm(alpha=1 / n, adjust=False).mean()})


def bollinger(close: pd.Series, n: int = S.BB_N, k: float = S.BB_K) -> pd.DataFrame:
    mid = close.rolling(n).mean()
    sd = close.rolling(n).std(ddof=0)
    up, lo = mid + k * sd, mid - k * sd
    width = (up - lo).replace(0, np.nan)
    return pd.DataFrame({"bb_pctb": (close - lo) / width, "bb_width": width / mid})


def resample(m1: pd.DataFrame, minutes: int) -> pd.DataFrame:
    agg = {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
    return m1.resample(f"{minutes}min", label="left", closed="left").agg(agg).dropna(subset=["close"])


def enrich(df: pd.DataFrame, full: bool = False) -> pd.DataFrame:
    out = df.copy()
    out["ema20"] = ema(out["close"], S.EMA_FAST)
    out["ema50"] = ema(out["close"], S.EMA_SLOW)
    out["rsi"] = rsi(out["close"])
    out["atr"] = atr(out)
    if full:
        out = out.join(adx(out)).join(bollinger(out["close"]))
        win = S.REGIME_DAYS * BARS_PER_DAY_5M
        out["atr_med"] = out["atr"].rolling(win, min_periods=win // 5).median()
        out["bbw_pct"] = out["bb_width"].rolling(win, min_periods=win // 5).rank(pct=True)
    return out


def seasonal_volume(m1: pd.DataFrame) -> pd.Series:
    """Hacim / (aynı 15-dk dilimi, önceki 10 işlem günü medyanı) — nedensel.

    Tick hacminin gün-içi mevsimselliği güçlüdür (ABD açılışında her gün sıçrar);
    ham oranla "hacim arttı" demek mevsimselliği keşfetmek olur.
    """
    bucket = m1.index.hour * (60 // S.SEASONAL_BUCKET_MIN) + m1.index.minute // S.SEASONAL_BUCKET_MIN
    day = m1.index.normalize()
    table = m1["volume"].groupby([day, bucket]).mean().unstack()
    base = table.shift(1).rolling(S.SEASONAL_DAYS, min_periods=S.SEASONAL_MIN_DAYS).median()
    stacked = base.stack()
    key = pd.MultiIndex.from_arrays([day, bucket])
    vals = stacked.reindex(key).to_numpy()
    return pd.Series(m1["volume"].to_numpy() / np.where(vals > 0, vals, np.nan), index=m1.index)


class SymbolBars:
    """Bir sembolün 1m + türetilmiş 5m/15m/1h çerçeveleri ve kapalı-bar erişimi."""

    def __init__(self, symbol: str, m1: pd.DataFrame) -> None:
        self.symbol = symbol
        m = enrich(m1)
        m["vol_seas"] = seasonal_volume(m1)
        day = m.index.normalize()
        daily_close = m["close"].groupby(day).last()
        m["prev_day_close"] = pd.Series(day, index=m.index).map(daily_close.shift(1))
        m["day_high"] = m["high"].groupby(day).cummax()
        m["day_low"] = m["low"].groupby(day).cummin()
        self.m1 = m
        self.tf = {k: enrich(resample(m1, k), full=(k == 5)) for k in TF_MINUTES}
        self.ends = {1: (m.index + pd.Timedelta(minutes=1)).values}
        for k, f in self.tf.items():
            self.ends[k] = (f.index + pd.Timedelta(minutes=k)).values
        self.idx_values = m.index.values
        self.a = {c: m[c].to_numpy(dtype=float) for c in m.columns}
        self.ta = {k: {c: f[c].to_numpy(dtype=float) for c in f.columns} for k, f in self.tf.items()}

    def frame(self, tf: int) -> pd.DataFrame:
        return self.m1 if tf == 1 else self.tf[tf]

    def last_closed(self, tf: int, t: pd.Timestamp) -> int:
        """Bitişi ≤ t olan son barın konumu (yoksa −1)."""
        return int(np.searchsorted(self.ends[tf], t.to_datetime64(), side="right")) - 1

    def pos_at(self, t: pd.Timestamp) -> int:
        """t'yi içeren (veya t'den sonraki ilk) 1m barın konumu."""
        return int(np.searchsorted(self.idx_values, t.floor("min").to_datetime64(), side="left"))
