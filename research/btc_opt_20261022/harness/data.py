"""Veri katmanı: 1m yol + seyrek min/max tabloları, UTC barlar + ATR bağlamı, rollover anları.

- `Path1m(data)`: lib_trend.M1 ile aynı yol (2023-03-24 11:28–14:00 satırları atılır), binary-lifting `_first`.
- `bars(data, tf)`: Binance UTC-hizalı barlar (left-closed/left-label), Wilder ATR14, karar anı = açılış + TF.
- `atr_asof(data, tf, t)`: karar anı t'de KAPANMIŞ son barın ATR14'ü (sızıntısız; bar kapanışı ≤ t).
- `rollovers(data)`: NY 17:00 (DST'ye duyarlı) → UTC epoch dakika.
Önbellek: cache/m1_<data>.npz (yalnız OHLC). Seyrek tablolar bellekte (ana ≈ 0,75 GB).
"""
from __future__ import annotations

from functools import lru_cache

import numpy as np
import pandas as pd

import config as K


def tmin(s) -> np.ndarray:
    return (pd.to_datetime(s).astype("int64") // 60_000_000_000).to_numpy(np.int64)


def _require(data: str) -> None:
    if data not in K.DATA_DIRS:
        raise ValueError(data)


class Path1m:
    """1m yol. `T` epoch dk (artan, boşluklu olabilir); O/H/L/C float64; `mn`/`mx` seyrek tablolar."""

    LEVELS = 16  # azami tutuş 2^16−1 = 65.535 dk ≈ 45,5 gün

    def __init__(self, data: str = "main") -> None:
        _require(data)
        self.data = data
        f = K.CACHE / f"m1_{data}.npz"
        if f.exists():
            z = np.load(f)
            T, O, H, L, C = z["T"], z["O"], z["H"], z["L"], z["C"]
        else:
            d = pd.read_parquet(K.DATA_DIRS[data] / "btc_1m.parquet", columns=["ts", "open", "high", "low", "close"])
            T = tmin(d["ts"])
            keep = ~((T >= K.EX0) & (T < K.EX1)) if data == "main" else np.ones(len(T), bool)
            T, O, H, L, C = (T[keep], d["open"].to_numpy(np.float64)[keep], d["high"].to_numpy(np.float64)[keep],
                             d["low"].to_numpy(np.float64)[keep], d["close"].to_numpy(np.float64)[keep])
            assert np.all(np.diff(T) > 0)
            np.savez(f, T=T, O=O, H=H, L=L, C=C)
        self.T, self.O, self.H, self.L, self.C = T, O, H, L, C
        self.N = len(T)
        pad = (1 << self.LEVELS) + 2
        lo = np.concatenate([L, np.full(pad, np.inf)])
        hi = np.concatenate([H, np.full(pad, -np.inf)])
        self.mn, self.mx = [lo], [hi]
        for lv in range(1, self.LEVELS):
            s = 1 << (lv - 1)
            a, b = self.mn[-1], self.mx[-1]
            self.mn.append(np.minimum(a, np.concatenate([a[s:], np.full(s, np.inf)])))
            self.mx.append(np.maximum(b, np.concatenate([b[s:], np.full(s, -np.inf)])))
        lc = np.log(C)
        ar = np.abs(np.diff(lc, prepend=np.nan)) * 1e4
        self.hot = ar > K.HOT_THR_BP
        self.RO = rollovers(data)
        self.excl = (K.EX0, K.EX1) if data == "main" else None

    # lib_trend.M1._first ile birebir
    def first(self, k: np.ndarray, e: np.ndarray, thr: np.ndarray, below: bool) -> np.ndarray:
        """[k,e] içinde ilk j: low[j] ≤ thr (below) / high[j] ≥ thr. Yoksa e+1. k>e ise k döner (çağıran eler)."""
        pos = np.asarray(k, np.int64).copy()
        if len(pos) == 0:
            return pos
        e = np.asarray(e, np.int64)
        maxlen = int(np.max(e - pos + 1))
        Lv = max(0, int(np.ceil(np.log2(max(maxlen, 1) + 1))))
        if Lv >= self.LEVELS:
            raise ValueError("tutuş seyrek tablodan uzun")
        tab = self.mn if below else self.mx
        for lv in range(Lv, -1, -1):
            step = 1 << lv
            okb = pos + step - 1 <= e
            v = tab[lv][pos]
            adv = okb & ((v > thr) if below else (v < thr))
            pos = pos + step * adv
        return pos

    def row_at_or_after(self, t) -> np.ndarray:
        return np.searchsorted(self.T, np.asarray(t, np.int64), "left")

    def last_row_before(self, t) -> np.ndarray:
        return np.searchsorted(self.T, np.asarray(t, np.int64), "left") - 1

    def close_before(self, t) -> np.ndarray:
        j = self.last_row_before(t)
        return np.where(j >= 0, self.C[np.maximum(j, 0)], np.nan)


@lru_cache(None)
def path(data: str = "main") -> Path1m:
    if data == "indep" and not K.holdout_unlocked():
        raise K.HoldoutError("bağımsız dönem 1m yolu (sonuç simülasyonu) yalnız holdout.evaluate_frozen_on_holdout "
                             "içinden açılır. Olay üretimi için data.raw_m1('indep') kullan.")
    return Path1m(data)


def raw_m1(data: str) -> pd.DataFrame:
    """Olay üreticileri için ham 1m (sonuç hesaplamaz); holdout kilidine tabi değil."""
    _require(data)
    return pd.read_parquet(K.DATA_DIRS[data] / "btc_1m.parquet")


@lru_cache(None)
def rollovers(data: str = "main") -> np.ndarray:
    a, b = ("2021-05-20", "2026-12-01") if data == "main" else ("2017-08-01", "2021-07-01")
    days = pd.date_range(a, b, freq="D")
    ro = pd.DatetimeIndex([pd.Timestamp(f"{x.date()} 17:00", tz="America/New_York") for x in days])
    return tmin(pd.Series(ro.tz_convert("UTC")))


def atr_wilder(h, l, c, n: int = 14) -> np.ndarray:
    pc = np.concatenate([[np.nan], c[:-1]])
    tr = np.nanmax(np.vstack([h - l, np.abs(h - pc), np.abs(l - pc)]), axis=0)
    a = pd.Series(tr).ewm(alpha=1.0 / n, adjust=False).mean().to_numpy()
    a[: n - 1] = np.nan
    return a


@lru_cache(None)
def bars(data: str, tf: str) -> pd.DataFrame:
    _require(data)
    d = pd.read_parquet(K.DATA_DIRS[data] / f"btc_{tf}.parquet")
    d["om"] = tmin(d["ts"])
    d["dec"] = d["om"] + K.TF_MIN[tf]
    d["atr"] = atr_wilder(d["high"].to_numpy(), d["low"].to_numpy(), d["close"].to_numpy())
    if data == "main":
        d["excl"] = (d["om"] < K.EX1) & (d["dec"] > K.EX0)
    else:
        d["excl"] = False
    return d.reset_index(drop=True)


def atr_asof(data: str, tf: str, t) -> np.ndarray:
    """Karar anı t (dk) için kapanışı ≤ t olan son barın ATR14'ü (Wilder)."""
    b = bars(data, tf)
    dec = b["dec"].to_numpy(np.int64)
    j = np.searchsorted(dec, np.asarray(t, np.int64), "right") - 1
    a = b["atr"].to_numpy()
    return np.where(j >= 0, a[np.maximum(j, 0)], np.nan)


@lru_cache(None)
def dvol20_series(data: str) -> pd.Series:
    d = bars(data, "1d")
    r = np.log(d["close"]).diff()
    return pd.Series(r.rolling(20).std().to_numpy(), index=d["om"].to_numpy() // 1440)


def dvol20_asof(data: str, t) -> np.ndarray:
    """Karar günü − 1'e kadar tamamlanmış UTC günlerinin 20 g log getiri std'si (sleeves.dvol_known ile aynı)."""
    t = np.asarray(t, np.int64)
    return dvol20_series(data).reindex(t // 1440 - 1).to_numpy()


def next_ro(data: str, t) -> np.ndarray:
    ro = rollovers(data)
    return ro[np.searchsorted(ro, np.asarray(t, np.int64), side="right")]


@lru_cache(None)
def _raw_tc(data: str):
    f = K.CACHE / f"m1_{data}.npz"
    if f.exists():
        z = np.load(f)
        return z["T"], z["C"]
    d = pd.read_parquet(K.DATA_DIRS[data] / "btc_1m.parquet", columns=["ts", "close"])
    T = tmin(d["ts"])
    keep = ~((T >= K.EX0) & (T < K.EX1)) if data == "main" else np.ones(len(T), bool)
    return T[keep], d["close"].to_numpy(np.float64)[keep]


def close_before_raw(data: str, t) -> np.ndarray:
    """Karar anından önce kapanan son 1m barın kapanışı (sinyal fiyatı; sonuç hesaplamaz)."""
    T, C = _raw_tc(data)
    j = np.searchsorted(T, np.asarray(t, np.int64), "left") - 1
    return np.where(j >= 0, C[np.maximum(j, 0)], np.nan)


def context(data: str, t) -> dict:
    """Olay kütüphanesi için karar-anı oynaklık bağlamı (hepsi t'de bilinen)."""
    t = np.asarray(t, np.int64)
    out = {f"atr_{tf}": atr_asof(data, tf, t) for tf in K.TF_MIN}
    out["dvol20"] = dvol20_asof(data, t)
    out["price_dec"] = close_before_raw(data, t)
    return out
