"""SC — nedensel özellikler (yalnız k ve öncesi barlar). Her dizi tüm bar uzunluğunda; k indeksindeki değer k kapanışında bilinir.
Nedensellik testi: tests/test_ozellik.py (k sonrası barlar bozulunca k'daki değer değişmemeli).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

import sc_veri as V


def ema(x: np.ndarray, n: int) -> np.ndarray:
    return pd.Series(x).ewm(span=n, adjust=False).mean().to_numpy()


def atr(bar: V.Bar, n: int = 14) -> np.ndarray:
    onceki = np.r_[bar.c[0], bar.c[:-1]]
    tr = np.maximum(bar.h, onceki) - np.minimum(bar.l, onceki)
    return pd.Series(tr).ewm(span=n, adjust=False).mean().to_numpy()


@dataclass
class Ozellik:
    ema240: np.ndarray
    ema1440: np.ndarray
    atr14: np.ndarray
    atr_oran: np.ndarray
    ust60: np.ndarray
    alt60: np.ndarray
    c60: np.ndarray       # c_{k−60}
    dt60: np.ndarray      # t_k − t_{k−60}


def hesapla(bar: V.Bar) -> Ozellik:
    a = atr(bar)
    med = pd.Series(a).rolling(1440, min_periods=720).median().to_numpy()
    c60 = np.r_[np.full(60, np.nan), bar.c[:-60]]
    t60 = np.r_[np.full(60, -10**12), bar.t[:-60]]
    return Ozellik(ema(bar.c, 240), ema(bar.c, 1440), a, a / med,
                   pd.Series(bar.h).rolling(60).max().to_numpy(), pd.Series(bar.l).rolling(60).min().to_numpy(),
                   c60, bar.t - t60)


def itki_sinyal(bar: V.Bar, oz: Ozellik, a: float, konum_min: float = 0.90, atr_oran_min: float = 1.2,
                sogu_bar: int = 60, maks_dt: int = 90 * 60) -> tuple[np.ndarray, np.ndarray]:
    """SC-03 IT(a). Dönüş (k indeksleri, yön). Soğuma: aynı yönde son sinyalden sonra sogu_bar dakika (zamanla)."""
    c = bar.c
    y = np.where(c > oz.ema1440, 1, -1)
    ayni = np.sign(c - oz.ema240) == y
    r60 = y * (c - oz.c60) / oz.atr14
    genis = oz.ust60 - oz.alt60
    konum = np.where(y > 0, (c - oz.alt60) / genis, (oz.ust60 - c) / genis)
    with np.errstate(invalid="ignore"):
        aday = ayni & (r60 >= a) & (konum >= konum_min) & (oz.atr_oran >= atr_oran_min) & (oz.dt60 <= maks_dt) & (genis > 0)
    k_all = np.flatnonzero(aday)
    secilen, yonler = [], []
    son = {1: -10**12, -1: -10**12}
    for k in k_all:
        yy = int(y[k])
        if bar.t[k] - son[yy] >= sogu_bar * 60:
            secilen.append(k)
            yonler.append(yy)
            son[yy] = bar.t[k]
    return np.array(secilen, dtype=np.int64), np.array(yonler, dtype=np.int32)
