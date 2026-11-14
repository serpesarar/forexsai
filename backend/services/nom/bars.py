"""NOM — 1m barlardan üst zaman dilimi (HTF) barları ve göstergeler.

Kural (sızıntı kilidi): her HTF barı `end` (kapanış) zamanını taşır. Bir karar anı T'de yalnız
`end <= T` olan barlar kullanılır (`asof_map`). Devam eden bar ASLA görünmez.

Zaman: `t` = 1m bar AÇILIŞI (UTC epoch sn). 1m barın kapanışı t + 60.
TF anahtarları: 'M5','M15','H1' UTC'ye hizalı; 'H4','D1' NY 18:00 seansına hizalı (CME/CFD günü).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

NY = 'America/New_York'
TF_MIN = {'M5': 5, 'M15': 15, 'H1': 60, 'H4': 240, 'D1': 1440}


def _ny_session_key(t: np.ndarray, minutes: int) -> tuple[np.ndarray, np.ndarray]:
    """NY 18:00 seans hizalı anahtar ve kapanış zamanı (epoch sn). D1 kapanışı = seans başı + 23 s (17:00 ET)."""
    ts = pd.to_datetime(t, unit='s', utc=True).tz_convert(NY)
    naive = ts.tz_localize(None)
    shifted = naive - pd.Timedelta(hours=18)
    sess_day = shifted.floor('D')
    sess_start_naive = sess_day + pd.Timedelta(hours=18)
    start_utc = sess_start_naive.tz_localize(NY, ambiguous='NaT', nonexistent='shift_forward').tz_convert('UTC')
    start = np.asarray(start_utc.asi8 // 10**9, dtype='int64')
    if minutes == 1440:
        return start, start + 23 * 3600
    mins = np.asarray(((shifted - sess_day).total_seconds() // 60), dtype='int64')
    blk = mins // minutes
    key = start + blk * minutes * 60
    end = np.minimum(key + minutes * 60, start + 23 * 3600)
    return key, end


def resample(b1: pd.DataFrame, tf: str) -> pd.DataFrame:
    """1m → HTF OHLC. Dönen: key, end, o, h, l, c, n (alt-bar sayısı)."""
    mn = TF_MIN[tf]
    t = b1.t.to_numpy()
    if tf in ('M5', 'M15', 'H1'):
        key = (t // (mn * 60)) * (mn * 60)
        end = key + mn * 60
    else:
        key, end = _ny_session_key(t, mn)
    df = pd.DataFrame({'key': key, 'end': end, 'o': b1.open.to_numpy(), 'h': b1.high.to_numpy(),
                       'l': b1.low.to_numpy(), 'c': b1.close.to_numpy()})
    g = df.groupby('key', sort=True)
    out = pd.DataFrame({'end': g.end.max(), 'o': g.o.first(), 'h': g.h.max(), 'l': g.l.min(), 'c': g.c.last(),
                        'n': g.o.size()}).reset_index()
    return out


# ───────────────────────────── göstergeler (seri → seri, nedensel) ─────────────────────────────

def wilder(x: pd.Series, n: int) -> pd.Series:
    return x.ewm(alpha=1.0 / n, adjust=False).mean()


def atr(b: pd.DataFrame, n: int = 14) -> pd.Series:
    pc = b.c.shift(1).fillna(b.o)
    tr = np.maximum(b.h - b.l, np.maximum((b.h - pc).abs(), (b.l - pc).abs()))
    return wilder(pd.Series(tr, index=b.index), n)


def rsi(c: pd.Series, n: int = 14) -> pd.Series:
    d = c.diff()
    up = wilder(d.clip(lower=0).fillna(0), n)
    dn = wilder((-d).clip(lower=0).fillna(0), n)
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))


def ema(c: pd.Series, n: int) -> pd.Series:
    return c.ewm(span=n, adjust=False).mean()


def adx(b: pd.DataFrame, n: int = 14) -> pd.Series:
    up = b.h.diff()
    dn = -b.l.diff()
    pdm = np.where((up > dn) & (up > 0), up, 0.0)
    ndm = np.where((dn > up) & (dn > 0), dn, 0.0)
    a = atr(b, n).replace(0, np.nan)
    pdi = 100 * wilder(pd.Series(pdm, index=b.index), n) / a
    ndi = 100 * wilder(pd.Series(ndm, index=b.index), n) / a
    dx = 100 * (pdi - ndi).abs() / (pdi + ndi).replace(0, np.nan)
    return wilder(dx.fillna(0), n)


def psar(b: pd.DataFrame, step: float = 0.02, mx: float = 0.2) -> np.ndarray:
    """Parabolic SAR yönü (+1 yükseliş / −1 düşüş) ve SAR değeri; döngü (nedensel)."""
    h, l = b.h.to_numpy(), b.l.to_numpy()
    n = len(h)
    sar = np.full(n, np.nan)
    dirn = np.zeros(n)
    if n < 3:
        return np.c_[dirn, sar]
    up = True
    af = step
    ep = h[0]
    s = l[0]
    for i in range(1, n):
        s = s + af * (ep - s)
        if up:
            s = min(s, l[i - 1], l[i - 2] if i > 1 else l[i - 1])
            if l[i] < s:
                up, s, ep, af = False, ep, l[i], step
            elif h[i] > ep:
                ep, af = h[i], min(af + step, mx)
        else:
            s = max(s, h[i - 1], h[i - 2] if i > 1 else h[i - 1])
            if h[i] > s:
                up, s, ep, af = True, ep, h[i], step
            elif l[i] < ep:
                ep, af = l[i], min(af + step, mx)
        sar[i] = s
        dirn[i] = 1.0 if up else -1.0
    return np.c_[dirn, sar]


def asof_map(t_dec: np.ndarray, end: np.ndarray, values: pd.DataFrame) -> pd.DataFrame:
    """Her karar anı için `end <= t_dec` olan SON barın değerleri (yoksa NaN)."""
    idx = np.searchsorted(end, t_dec, side='right') - 1
    out = values.iloc[np.clip(idx, 0, None)].reset_index(drop=True)
    out.loc[idx < 0, :] = np.nan
    return out


def last_closed_1m(t_open: np.ndarray, t_dec: np.ndarray) -> np.ndarray:
    """Kapanışı (t+60) karar anına eşit/önce olan son 1m barın indeksi (−1 = yok)."""
    return np.searchsorted(t_open + 60, t_dec, side='right') - 1
