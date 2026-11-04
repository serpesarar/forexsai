"""capali_veri.py — çapalı eşleştirme için ortak veri katmanı (PROTOCOL.md §0–§1).

HOLDOUT: ts ≥ 2025-12-01 00:00 UTC olan hiçbir bar / gün YÜKLENMEZ (yükleme anında kesilir).
Saatler: bar BAŞLANGICI UTC; NY yerel saati zoneinfo(America/New_York) ile, günün öğlen ofsetiyle (DST doğru;
geçişler Pazar 02:00'de olduğundan işlem günlerinde kullandığımız saatlerde tek ofset geçerli).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
HOLDOUT = pd.Timestamp("2025-12-01", tz="UTC")
HOLD_NS = int(HOLDOUT.value)
NSMIN = 60_000_000_000
SRC = {
    "5m": ROOT / "research/ndx_pattern_motifs/data/bars_5m.parquet",
    "15m": ROOT / "research/ndx_pattern_motifs/data/bars_15m.parquet",
    "30m": ROOT / "research/ndx_gate_forge/data/long_30m_utc.parquet",
    "1h": ROOT / "research/ndx_gate_forge/data/long_1h_utc.parquet",
}
DAILY = ROOT / "research/ndx_gate_forge/data/macro_daily_patched.csv"
TFMIN = {"5m": 5, "15m": 15, "30m": 30, "1h": 60}

# ── NY ofset tablosu (dakika; ör. yaz −240) ──
_D0 = int(np.datetime64("2014-01-01", "D").astype(np.int64))
_dates = pd.date_range("2014-01-01", "2026-03-01", freq="D")
_noon = (_dates + pd.Timedelta(hours=12)).tz_localize("America/New_York")
OFF = np.array([int(t.utcoffset().total_seconds() // 60) for t in _noon], dtype=np.int64)


def utc_ns(dn: np.ndarray, minute: np.ndarray | int) -> np.ndarray:
    """dn = 1970'ten gün sayısı (NY takvim günü), minute = NY yerel dakika → UTC ns."""
    dn = np.asarray(dn, dtype=np.int64)
    off = OFF[dn - _D0]
    return (dn * 1440 + np.asarray(minute, dtype=np.int64) - off) * NSMIN


def local_min(dn: np.ndarray, t_ns: np.ndarray) -> np.ndarray:
    """t_ns'in dn gününe göre NY yerel dakikası."""
    return ((np.asarray(t_ns) - utc_ns(dn, 0)) // NSMIN).astype(np.int64)


# ── günlük nakit takvim ──
def load_daily() -> pd.DataFrame:
    d = pd.read_csv(DAILY, parse_dates=["date"])
    d = d[d.date < HOLDOUT.tz_localize(None)]
    d = d.rename(columns={"NDXCASH_open": "O", "NDXCASH_high": "H", "NDXCASH_low": "L", "NDXCASH_close": "C",
                          "VIX_close": "VIX"})[["date", "O", "H", "L", "C", "VIX"]]
    d = d.dropna(subset=["O", "H", "L", "C"]).sort_values("date").reset_index(drop=True)
    pc = d.C.shift(1)
    tr = np.maximum(d.H, pc) - np.minimum(d.L, pc)
    d["ATR"] = tr.rolling(14).mean().shift(1)                 # D−1 dahil, D hariç
    d["dn"] = d.date.values.astype("datetime64[D]").astype(np.int64)
    s = set(d.dn.tolist())
    md, wd, dd = d.date.dt.month, d.date.dt.weekday, d.date.dt.day
    bf = (md == 11) & (wd == 4) & dd.between(23, 29) & ~(d.dn - 1).isin(s)    # Şükran sonrası Cuma
    d["early"] = bf | ((md == 12) & (dd == 24)) | ((md == 7) & (dd == 3))
    return d


class Grid:
    """Tek TF bar dizisi + kesin/toleranslı fiyat okuma + o TF'nin işlem günü listesi."""

    def __init__(self, tf: str, daily: pd.DataFrame):
        d = pd.read_parquet(SRC[tf])
        d = d[d.ts < HOLDOUT].sort_values("ts").drop_duplicates("ts").reset_index(drop=True)
        self.tf, self.m = tf, TFMIN[tf]
        self.st = d.ts.values.astype("datetime64[ns]").astype(np.int64)
        self.en = self.st + self.m * NSMIN
        self.o, self.h, self.l, self.c = (d[k].to_numpy(float) for k in ("open", "high", "low", "close"))
        assert self.en.max() <= HOLD_NS
        first = int(np.datetime64(d.ts.iloc[0].tz_convert("America/New_York").date(), "D").astype(np.int64)) + 1
        last = int(np.datetime64(d.ts.iloc[-1].tz_convert("America/New_York").date(), "D").astype(np.int64))
        dd = daily[(daily.dn >= first) & (daily.dn <= last)].reset_index(drop=True)
        self.days = dd.dn.to_numpy(np.int64)                      # TF gün listesi (tüm işlem günleri)
        self.early = dd.early.to_numpy(bool)
        self.atr = dd.ATR.to_numpy(float)
        self.vix = dd.VIX.to_numpy(float)
        # önceki işlem günü (master takvimden): ilk gün için de bulunur
        mdn = daily.dn.to_numpy(np.int64)
        pos = np.searchsorted(mdn, self.days)
        self.prev_dn = np.where(pos > 0, mdn[np.maximum(pos - 1, 0)], -1)
        self.prev_early = np.where(pos > 0, daily.early.to_numpy(bool)[np.maximum(pos - 1, 0)], True)
        self.prev_vix = np.where(pos > 0, daily.VIX.to_numpy(float)[np.maximum(pos - 1, 0)], np.nan)
        # bar ATR14 (önceki 14 bar)
        pc = np.r_[self.c[0], self.c[:-1]]
        tr = np.maximum(self.h, pc) - np.minimum(self.l, pc)
        self.batr = pd.Series(tr).rolling(14).mean().shift(1).to_numpy()

    # kesin: bitişi tam t olan barın kapanışı
    def px(self, t: np.ndarray) -> np.ndarray:
        t = np.asarray(t, dtype=np.int64)
        i = np.searchsorted(self.en, t)
        ic = np.minimum(i, len(self.en) - 1)
        ok = (i < len(self.en)) & (self.en[ic] == t)
        return np.where(ok, self.c[ic], np.nan)

    # toleranslı: t'de ya da önce biten son bar, en fazla tol dk eski
    def px_tol(self, t: np.ndarray, tol: int) -> np.ndarray:
        t = np.asarray(t, dtype=np.int64)
        i = np.searchsorted(self.en, t, side="right") - 1
        ic = np.maximum(i, 0)
        ok = (i >= 0) & (self.en[ic] >= t - tol * NSMIN)
        return np.where(ok, self.c[ic], np.nan)

    # başlangıcı tam t olan barın indeksi (yoksa −1)
    def at_start(self, t: np.ndarray) -> np.ndarray:
        t = np.asarray(t, dtype=np.int64)
        i = np.searchsorted(self.st, t)
        ic = np.minimum(i, len(self.st) - 1)
        return np.where((i < len(self.st)) & (self.st[ic] == t), ic, -1)

    def day_index_of(self, t_ns: np.ndarray) -> np.ndarray:
        """bar başlangıcının NY takvim günü → TF gün listesi indeksi (yoksa −1)."""
        t_ns = np.asarray(t_ns, dtype=np.int64)
        dn_guess = (t_ns // NSMIN // 1440).astype(np.int64)          # UTC günü
        # NY günü = UTC − ofset; ofset ≤ 5 s → UTC günü ya aynı ya bir sonraki
        loc = (t_ns // NSMIN + OFF[np.clip(dn_guess - _D0, 0, len(OFF) - 1)])
        dn = loc // 1440
        pos = np.searchsorted(self.days, dn)
        pc = np.minimum(pos, len(self.days) - 1)
        return np.where((pos < len(self.days)) & (self.days[pc] == dn), pc, -1)


def outcome(G: Grid, day: np.ndarray, refmin: np.ndarray, hz: tuple) -> tuple[np.ndarray, np.ndarray]:
    """y = px(bitiş) − px(referans) (puan) ve bitiş ns. hz: ('plus', dk) | ('next', NY dk) | ('nextsame', None)."""
    n = len(G.days)
    day = np.asarray(day, dtype=np.int64)
    ok = (day >= 0) & (day < n)
    dc = np.clip(day, 0, n - 1)
    t_ref = utc_ns(G.days[dc], refmin)
    kind, v = hz
    if kind == "plus":
        t_end = t_ref + int(v) * NSMIN
    else:
        d2 = day + 1
        ok &= d2 < n
        d2c = np.clip(d2, 0, n - 1)
        t_end = utc_ns(G.days[d2c], refmin if kind == "nextsame" else v)
    y = G.px(t_end) - G.px(t_ref)
    y = np.where(ok & (t_end < HOLD_NS), y, np.nan)
    return y, t_end
