"""NDX Gate Forge — ortak veri katmanı + sızıntısız TP/SL simülatörü.

Tüm bar zaman damgaları bar BAŞLANGICI (gerçek UTC). Karar = bar i kapanışı,
giriş = bar i+1 açılışı. Özellikler yalnız bar <= i kullanır.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from numba import njit

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
OUT = HERE / "results"

DUKA = DATA / "duka_1m_2025.parquet"
CACHE = ROOT / "nasdaq_1m_candle_cache_2026-02-10_2026-08-29/nasdaq_1m_candle_cache_TAM_2026-02-10_2026-08-29.csv"
MT5 = ROOT / "nasdaq_tam_veri_2026-08-29/1m_veri/NAS100_1m_2026-05-19_2026-08-28.csv"
LONG = ROOT / "research/ndx_buy_lab/data"

CACHE_SPREAD = 1.3          # MT5 medyan spread (puan) — cache'te spread yok
SLIP = 0.2                  # dolum başına ek kayma (puan)
CACHE_FIX_BEFORE = pd.Timestamp("2026-03-08", tz="UTC")   # öncesi +60 dk
PERIODS = {
    "D25a": ("2025-01-01", "2025-07-01"),
    "D25b": ("2025-07-01", "2026-01-01"),
    "C26": ("2026-02-10", "2026-05-19 19:20"),
    "M26": ("2026-05-19 19:20", "2026-08-29"),
    "S26": ("2026-08-29", "2026-10-01"),   # indicator_snapshots (MT5 NAS100, UTC) — ileri dönem
}
SNAP = DATA / "snap_ndx_1m.parquet"


def _std(d: pd.DataFrame, seg: str) -> pd.DataFrame:
    d = d.sort_values("ts").drop_duplicates("ts").reset_index(drop=True)
    d["t"] = d.ts.astype("int64") // 10**9
    d["seg"] = seg
    return d


def load_1m() -> pd.DataFrame:
    """D25 + C26 + M26 birleşik 1m bid/ask barları."""
    p = DATA / "bars_1m_all.parquet"
    if p.exists():
        return pd.read_parquet(p)
    a = pd.read_parquet(DUKA)
    a = a.rename(columns={"ask_open": "ao", "ask_high": "ah", "ask_low": "al", "ask_close": "ac"})
    a = _std(a[["ts", "open", "high", "low", "close", "ao", "ah", "al", "ac", "volume", "spread_px"]], "D25")

    c = pd.read_csv(CACHE)
    c["ts"] = pd.to_datetime(c.time_utc, utc=True, format="ISO8601")
    c.loc[c.ts < CACHE_FIX_BEFORE, "ts"] += pd.Timedelta(minutes=60)
    m = pd.read_csv(MT5)
    m["ts"] = pd.to_datetime(m.time_utc, utc=True, format="ISO8601")
    c = c[c.ts < m.ts.iloc[0]].copy()
    c["spread_px"] = CACHE_SPREAD
    m["spread_px"] = m.spread * 0.1
    m["volume"] = m.tick_volume
    sn = pd.read_parquet(SNAP)
    sn = sn[sn.ts > m.ts.iloc[-1]].copy()
    sn["spread_px"] = CACHE_SPREAD
    parts = [a]
    for d, seg in [(c, "C26"), (m, "M26"), (sn, "S26")]:
        d = d[["ts", "open", "high", "low", "close", "volume", "spread_px"]].copy()
        for k, s in [("ao", "open"), ("ah", "high"), ("al", "low"), ("ac", "close")]:
            d[k] = d[s] + d.spread_px
        parts.append(_std(d, seg))
    b = pd.concat(parts, ignore_index=True).sort_values("ts").reset_index(drop=True)
    b["period"] = ""
    for k, (lo, hi) in PERIODS.items():
        b.loc[(b.ts >= pd.Timestamp(lo, tz="UTC")) & (b.ts < pd.Timestamp(hi, tz="UTC")), "period"] = k
    add_clock(b)
    b.to_parquet(p)
    return b


def add_clock(b: pd.DataFrame, col: str = "ts", close_offset_s: int = 60) -> None:
    """NY saat alanları KARAR anına göre (bar kapanışı)."""
    dec = b[col] + pd.Timedelta(seconds=close_offset_s)
    ny = dec.dt.tz_convert("America/New_York")
    b["ny_min"] = (ny.dt.hour * 60 + ny.dt.minute).astype("int32")
    # İşlem günü: NY 18:00'da başlar (vadeli/CFD oturumu)
    b["tday"] = (ny + pd.Timedelta(hours=6)).dt.strftime("%Y-%m-%d")
    b["ny_date"] = ny.dt.strftime("%Y-%m-%d")
    b["wd"] = (ny + pd.Timedelta(hours=6)).dt.weekday.astype("int8")   # işlem günü haftanın günü
    b["utc_h"] = dec.dt.hour.astype("int8")
    b["utc_min"] = (dec.dt.hour * 60 + dec.dt.minute).astype("int16")


def atr(h: np.ndarray, l: np.ndarray, c: np.ndarray, n: int) -> np.ndarray:
    pc = np.r_[np.nan, c[:-1]]
    tr = np.nanmax(np.c_[h - l, np.abs(h - pc), np.abs(l - pc)], axis=1)
    return pd.Series(tr).ewm(alpha=1 / n, adjust=False, min_periods=n).mean().to_numpy()


@njit(cache=True)
def _walk(t, o, h, l, c, ao, ah, al, ac, idx, side, tp, sl, maxhold, gapmax, slip):
    n = idx.shape[0]
    R = np.full(n, np.nan)
    dur = np.full(n, -1.0)
    why = np.full(n, -1, np.int8)   # 1 TP, 2 SL, 0 süre, 3 boşluk
    N = t.shape[0]
    for k in range(n):
        i = idx[k]
        j = i + 1
        if j >= N or t[j] - t[i] > 120 or not (sl[k] > 0):
            continue
        s = side[k]
        if s == 1:
            entry = ao[j] + slip
            tpp = entry + tp[k]
            slp = entry - sl[k]
        else:
            entry = o[j] - slip
            tpp = entry - tp[k]
            slp = entry + sl[k]
        tend = t[j] + maxhold
        ex = np.nan
        w = -1
        jj = j
        while jj < N:
            if jj > j and t[jj] - t[jj - 1] > gapmax:
                ex = c[jj - 1] if s == 1 else ac[jj - 1]
                w = 3
                jj -= 1
                break
            if s == 1:
                if jj > j and o[jj] <= slp:
                    ex = o[jj] - slip
                    w = 2
                    break
                if l[jj] <= slp:
                    ex = slp - slip
                    w = 2
                    break
                if h[jj] >= tpp:
                    ex = tpp
                    w = 1
                    break
            else:
                if jj > j and ao[jj] >= slp:
                    ex = ao[jj] + slip
                    w = 2
                    break
                if ah[jj] >= slp:
                    ex = slp + slip
                    w = 2
                    break
                if al[jj] <= tpp:
                    ex = tpp
                    w = 1
                    break
            if t[jj] + 60 >= tend:
                ex = c[jj] if s == 1 else ac[jj]
                w = 0
                break
            jj += 1
        if w == -1:
            continue
        R[k] = (ex - entry) * s / sl[k]
        dur[k] = (t[min(jj, N - 1)] + 60 - t[j]) / 60.0
        why[k] = w
    return R, dur, why


def simulate(b: pd.DataFrame, idx: np.ndarray, side: np.ndarray, tp: np.ndarray, sl: np.ndarray,
             maxhold_min: int = 720, gapmax_min: int = 120) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    a = [b[k].to_numpy(np.float64) for k in ["open", "high", "low", "close", "ao", "ah", "al", "ac"]]
    return _walk(b.t.to_numpy(np.int64), *a, idx.astype(np.int64), side.astype(np.int64),
                 tp.astype(np.float64), sl.astype(np.float64), maxhold_min * 60, gapmax_min * 60, SLIP)


@njit(cache=True)
def _fwd(t, o, c, ao, ac, idx, side, H, gapmax, slip):
    n = idx.shape[0]
    out = np.full(n, np.nan)
    N = t.shape[0]
    for k in range(n):
        i = idx[k]
        j = i + 1
        if j >= N or t[j] - t[i] > 120:
            continue
        s = side[k]
        entry = ao[j] + slip if s == 1 else o[j] - slip
        tend = t[j] + H * 60
        jj = j
        while jj + 1 < N and t[jj + 1] < tend and t[jj + 1] - t[jj] <= gapmax:
            jj += 1
        ex = c[jj] if s == 1 else ac[jj]
        out[k] = (ex - entry) * s
    return out


def fwd_points(b: pd.DataFrame, idx: np.ndarray, side: np.ndarray, H: int, gapmax_min: int = 120) -> np.ndarray:
    return _fwd(b.t.to_numpy(np.int64), b.open.to_numpy(float), b.close.to_numpy(float), b.ao.to_numpy(float),
                b.ac.to_numpy(float), idx.astype(np.int64), side.astype(np.int64), H, gapmax_min * 60, SLIP)


def block_boot(values: np.ndarray, groups: np.ndarray, n: int = 2000, seed: int = 7) -> np.ndarray:
    """Gün-bloklu bootstrap: grup ortalamalarının ağırlıklı yeniden örneklemesi → ortalama dağılımı."""
    if len(values) == 0:
        return np.array([np.nan])
    g, inv = np.unique(groups, return_inverse=True)
    s = np.bincount(inv, weights=values)
    cnt = np.bincount(inv)
    rng = np.random.default_rng(seed)
    pick = rng.integers(0, len(g), size=(n, len(g)))
    return s[pick].sum(1) / np.maximum(cnt[pick].sum(1), 1)


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (np.nan, np.nan)
    p = k / n
    d = 1 + z * z / n
    m = p + z * z / (2 * n)
    r = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((m - r) / d, (m + r) / d)
