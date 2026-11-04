"""BTC scalp fizibilite ortak motoru.

- Dakika ızgarası (UTC, m = 2021-06-01 00:00'dan itibaren dakika), eksik dakika NaN.
- Dışlama: 2023-03-24 11:28–14:00 UTC + >=5 dk Binance kesintileri (BAD).
- Giriş: karar dakikası t'nin kapanışı → giriş barı e = t+1, fiyat open[e].
- İlk dokunuş: seyrek tablo (sparse table) + ikili sıçrama ile vektörel; pencere [e, e+L).
  Giriş barının kendi high/low'u (açılıştan sonra) dahildir.
- Aynı barda TP+SL → SL (kötümser). SL dolumu boşluk-duyarlı: long min(SL, open[hit]).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

DATA = "/Users/melihcanodacioglu/Desktop/panel/research/btc_indep_2017_2021/data"
OUT = "/Users/melihcanodacioglu/Desktop/panel/research/btc_indep_2017_2021/cache"

T0 = pd.Timestamp("2017-08-17", tz="UTC")
T_END = pd.Timestamp("2021-06-01", tz="UTC")
N = int((T_END - T0) / pd.Timedelta(minutes=1))
LMAX = 1440  # en uzun izleme ufku (dk)
KLEV = 11    # 2^10 = 1024; ikili sıçrama toplamı 2047 >= LMAX


def tmin(ts) -> int:
    t = pd.Timestamp(ts)
    if t.tzinfo is None:
        t = t.tz_localize("UTC")
    return int((t - T0) / pd.Timedelta(minutes=1))


def load_grid() -> dict:
    df = pd.read_parquet(f"{DATA}/btc_1m.parquet", columns=["ts", "open", "high", "low", "close"])
    idx = ((df["ts"] - T0) / pd.Timedelta(minutes=1)).to_numpy().astype(np.int64)
    g = {}
    for c in ["open", "high", "low", "close"]:
        a = np.full(N, np.nan)
        a[idx] = df[c].to_numpy()
        g[c] = a
    bad = np.zeros(N, dtype=bool)
    bad[tmin("2023-03-24 11:28"):tmin("2023-03-24 14:00")] = True
    miss = np.isnan(g["close"])
    d = np.diff(np.concatenate([[0], miss.astype(np.int8), [0]]))
    st, en = np.where(d == 1)[0], np.where(d == -1)[0]
    for a, b in zip(st, en):
        if b - a >= 5:
            bad[a:b] = True
    g["bad"] = bad
    # dışlanan dakikaları fiyat serisinden sil
    for c in ["open", "high", "low", "close"]:
        g[c][bad] = np.nan
    g["close_ff"] = pd.Series(g["close"]).ffill().to_numpy()
    return g


def sparse_tables(high: np.ndarray, low: np.ndarray, klev: int = KLEV):
    """MX[k][i] = max(high[i:i+2^k]), MN[k][i] = min(low[i:i+2^k]); NaN → -inf/+inf (dokunuş yok)."""
    h = np.where(np.isnan(high), -np.inf, high)
    l = np.where(np.isnan(low), np.inf, low)
    n = len(h)
    MX = np.empty((klev, n))
    MN = np.empty((klev, n))
    MX[0], MN[0] = h, l
    for k in range(1, klev):
        s = 1 << (k - 1)
        MX[k] = MX[k - 1]
        MN[k] = MN[k - 1]
        MX[k, :n - s] = np.maximum(MX[k - 1, :n - s], MX[k - 1, s:])
        MN[k, :n - s] = np.minimum(MN[k - 1, :n - s], MN[k - 1, s:])
    return MX, MN


def first_hit(T: np.ndarray, e: np.ndarray, thr: np.ndarray, L: int, up: bool) -> np.ndarray:
    """Pencere [e, e+L) içinde ilk dokunuşun göreli indeksi k (0..L-1); yoksa L.

    up=True: high >= thr (T=MX); up=False: low <= thr (T=MN).
    """
    n = T.shape[1]
    pos = e.copy()
    end = np.minimum(e + L, n)
    for k in range(T.shape[0] - 1, -1, -1):
        step = 1 << k
        ok = pos + step <= end
        idx = np.where(ok, pos, 0)
        v = T[k][idx]
        nohit = (v < thr) if up else (v > thr)
        pos = np.where(ok & nohit, pos + step, pos)
    k_rel = pos - e
    # pos<end ise pos'ta dokunuş var (maksimal dokunuşsuz önek); doğrulama
    inside = pos < end
    if inside.any():
        pi = np.where(inside, pos, 0)
        v = T[0][pi]
        okhit = (v >= thr) if up else (v <= thr)
        assert np.all(okhit[inside]), "first_hit tutarsız"
    k_rel[~inside] = L
    return k_rel.astype(np.int32)


def entries(g: dict, L: int = LMAX) -> np.ndarray:
    """Geçerli giriş barları: open var, karar barı t=e-1 var, [e, e+L) BAD ile kesişmiyor."""
    o = g["open"]
    ok = ~np.isnan(o)
    ok[1:] &= ~np.isnan(g["close"][:-1])
    ok[0] = False
    bcs = np.concatenate([[0], np.cumsum(g["bad"])])
    e = np.arange(N)
    hi = np.minimum(e + L, N)
    ok &= (bcs[hi] - bcs[e]) == 0
    ok &= e + L <= N  # tam pencere
    return np.where(ok)[0]


def atr_1m(g: dict, n: int = 14) -> np.ndarray:
    """ATR14(1m) karar anında bilinen: e girişi için bar e-1'de biten 14 barın TR ortalaması → index e."""
    h, l, c = g["high"], g["low"], g["close"]
    pc = np.concatenate([[np.nan], c[:-1]])
    tr = np.nanmax(np.vstack([h - l, np.abs(h - pc), np.abs(l - pc)]), axis=0)
    a = pd.Series(tr).rolling(n, min_periods=10).mean().to_numpy()
    return np.concatenate([[np.nan], a[:-1]])


def atr_5m(g: dict, n: int = 14) -> np.ndarray:
    """ATR14(5m): son 14 TAMAMLANMIŞ 5m bar (giriş dakikası e'den önce kapanmış)."""
    m = np.arange(N)
    b5 = m // 5
    df = pd.DataFrame({"b": b5, "h": g["high"], "l": g["low"], "c": g["close"]})
    agg = df.groupby("b").agg(h=("h", "max"), l=("l", "min"), c=("c", "last"))
    pc = agg["c"].shift(1)
    tr = pd.concat([agg["h"] - agg["l"], (agg["h"] - pc).abs(), (agg["l"] - pc).abs()], axis=1).max(axis=1)
    a = tr.rolling(n, min_periods=10).mean()
    # e girişinde bilinen son tamamlanmış 5m kova: (e//5)-1  (e kovanın ilk dakikası ise önceki kova bitmiştir)
    last_done = (m // 5) - 1
    arr = a.reindex(np.arange(b5.max() + 1)).to_numpy()
    out = np.full(N, np.nan)
    okk = last_done >= 0
    out[okk] = arr[last_done[okk]]
    return out


def rv_24h(g: dict) -> np.ndarray:
    """Önceki 1440 dakikanın 1m log getiri std'si, yıllıklandırılmış; index e (e-1'e kadar bilgi)."""
    c = g["close_ff"]
    r = np.diff(np.log(c), prepend=np.nan)
    s = pd.Series(r).rolling(1440, min_periods=1000).std().to_numpy() * np.sqrt(525600)
    return np.concatenate([[np.nan], s[:-1]])
