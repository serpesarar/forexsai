"""ME-09 ortak tanımlar — kullanıcı tanımlı 'dalgalı tepe aralığı' şablonları (NAS100 1h).

Benzerlik ölçüsü ME-08 ile aynı (research/benzerlik_ornek_20261019/merdiven_test.py):
pencere → 64 noktaya zaman-esnek doğrusal yeniden örnekleme (log kapanış) → z-normalize → Öklid.
z-normalize (ddof=0) iki vektör için d² = 2·64·(1 − r) → d ile Pearson r birebir: r = 1 − d²/128.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = HERE / "results"
OUT.mkdir(exist_ok=True)

P = 64
# Şablon sınırları: kullanıcının yanıtındaki GÜNLER, UTC gün sınırıyla (başlangıç günü 00:00 → bitiş günü son barı 23:00).
# Görsellerden ölçülen alternatif sınırlar (TEMPL_ALT) yalnız duyarlılık için (PROTOCOL.md §1).
TEMPL = {
    "T1": ("2026-07-06 00:00", "2026-07-21 23:00"),
    "T2": ("2026-07-17 00:00", "2026-07-29 23:00"),
    "T3": ("2026-08-13 00:00", "2026-08-20 23:00"),
}
TEMPL_ALT = {  # elips kenarlarının piksel→zaman dönüşümü (görsel 6: T1; görsel 7: T2 kırmızı, T3 sağ pembe)
    "T1": ("2026-07-07 07:00", "2026-07-21 15:00"),
    "T2": ("2026-07-16 12:00", "2026-07-29 23:00"),
    "T3": ("2026-08-11 08:00", "2026-08-20 06:00"),
}
FS = (1 / 3, 1 / 2, 2 / 3, 1.0)
DEV_END = pd.Timestamp("2025-11-30 23:00", tz="UTC")
HO_START = pd.Timestamp("2025-12-01", tz="UTC")
SPLIT = pd.Timestamp("2021-01-01", tz="UTC")
DAX_START = pd.Timestamp("2020-01-01", tz="UTC")
QUERY_HOUR = 20


def load_ndx() -> pd.DataFrame:
    """NDX CFD 1h: long_1h_utc (2016-05 → 2026-07-14) + bars_15m'den 1h'e toplanmış uzatma (ME-08 load() ile aynı)."""
    a = pd.read_parquet(ROOT / "research/ndx_gate_forge/data/long_1h_utc.parquet")[["ts", "open", "high", "low", "close"]]
    b = pd.read_parquet(ROOT / "research/ndx_pattern_motifs/data/bars_15m.parquet")[["ts", "open", "high", "low", "close"]]
    b = (b[b.ts > a.ts.max()].set_index("ts").resample("1h")
         .agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna().reset_index())
    return pd.concat([a, b]).sort_values("ts").drop_duplicates("ts").reset_index(drop=True)


def load_dax() -> pd.DataFrame:
    x = pd.read_parquet(ROOT / "research/ndx_gate_forge/data/dax_1h.parquet")[["ts", "open", "high", "low", "close"]]
    return x[x.ts >= DAX_START].sort_values("ts").drop_duplicates("ts").reset_index(drop=True)


def tpl_index(ts: pd.Series, templ: dict[str, tuple[str, str]] = TEMPL) -> dict[str, tuple[int, int]]:
    """Şablon → (ilk bar indeksi, son bar indeksi) (ikisi dahil)."""
    out = {}
    for k, (a, b) in templ.items():
        i0 = int(ts.searchsorted(pd.Timestamp(a, tz="UTC")))
        i1 = int(ts.searchsorted(pd.Timestamp(b, tz="UTC"), side="right")) - 1
        out[k] = (i0, i1)
    return out


def shapes(c: np.ndarray, starts: np.ndarray, length: int) -> np.ndarray:
    """starts[i]'den başlayan length barlık log-kapanış penceresini 64 noktaya örnekle + z-normalize."""
    pos = starts[:, None] + np.linspace(0, length - 1, P)[None, :]
    lo = np.floor(pos).astype(int)
    w = pos - lo
    hi = np.minimum(lo + 1, len(c) - 1)
    x = c[lo] * (1 - w) + c[hi] * w
    sd = x.std(1, keepdims=True)
    sd[sd == 0] = np.nan
    return (x - x.mean(1, keepdims=True)) / sd


def tpl_shape(c: np.ndarray, a: int, b: int, f: float = 1.0) -> np.ndarray:
    tl = int(round(f * (b - a + 1)))
    return shapes(c, np.array([a]), tl)[0]


def window_lengths(tpl: dict[str, tuple[int, int]]) -> tuple[int, int, int]:
    med = float(np.median([b - a + 1 for a, b in tpl.values()]))
    return (int(round(0.8 * med)), int(round(med)), int(round(1.2 * med)))


def dist_matrix(c: np.ndarray, Q: np.ndarray, LS: tuple[int, ...], tvecs: list[np.ndarray], f: float) -> np.ndarray:
    """Her sorgu için min_{şablon, L} mesafe; pencere = sorgu barında biten son round(f·L) bar (sorgu barı dahil)."""
    D = np.full(len(Q), np.inf)
    for L in LS:
        Lf = int(round(f * L))
        st = Q - Lf + 1
        ok = st >= 0
        S = shapes(c, np.clip(st, 0, None), Lf)
        for tv in tvecs:
            dist = np.sqrt(((S - tv) ** 2).sum(1))
            dist[~ok | ~np.isfinite(dist)] = np.inf
            D = np.minimum(D, dist)
    return D


def r_from_d(d: np.ndarray | float) -> np.ndarray | float:
    return 1 - np.asarray(d) ** 2 / (2 * P)
