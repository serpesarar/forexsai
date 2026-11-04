"""fam_stres — ortak motor: veri, sızıntısız icra simülasyonu (1m), istatistik, plasebo.

Ön-kayıt: prereg.md. Tüm zamanlar UTC dakika (int, epoch'tan).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data"
OUT = HERE / "results"

SPR_BASE, SPR_STRESS, SPR_FIX = 0.000185, 0.00028, 15.0   # gidiş-dönüş
SWAP_L, SWAP_S = 0.14 / 365, 0.02 / 365                    # gece başına, giriş fiyatı oranı
MAX_LAG = 10                                                # giriş gecikmesi tavanı (dk)
LV = 13                                                     # seyrek tablo seviyesi (aralık ≤ 8191 dk)


def tmin(s: str) -> int:
    return int(pd.Timestamp(s, tz="UTC").value // 60_000_000_000)


SEGS = {"KESIF": (tmin("2021-06-01"), tmin("2024-01-01")),
        "OOS": (tmin("2024-01-11"), tmin("2025-07-01")),
        "KOR": (tmin("2025-07-01"), tmin("2026-10-21"))}
EXCL = (tmin("2023-03-24 11:28"), tmin("2023-03-24 14:00"))


def seg_of(tm: np.ndarray) -> np.ndarray:
    out = np.full(len(tm), "", dtype=object)
    for k, (a, b) in SEGS.items():
        out[(tm >= a) & (tm < b)] = k
    return out


def to_min(ts: pd.Series) -> np.ndarray:
    return ts.values.astype("datetime64[m]").astype(np.int64)


# ---------------------------------------------------------------- 1m veri + seyrek tablolar
class M1:
    def __init__(self) -> None:
        m = pd.read_parquet(DATA / "btc_1m.parquet", columns=["ts", "open", "high", "low", "close"])
        self.ts = to_min(m.ts)
        self.o, self.h, self.l, self.c = (m[c].to_numpy(np.float64) for c in ("open", "high", "low", "close"))
        self.n = len(self.ts)
        self.stl = self._st(self.l, np.minimum)
        self.sth = self._st(self.h, np.maximum)
        self.log2 = np.zeros(1 << LV, dtype=np.int64)
        for L in range(2, 1 << LV):
            self.log2[L] = self.log2[L // 2] + 1
        # rollover = 17:00 New York (sunucu 00:00)
        days = pd.date_range("2021-05-25", "2026-11-05", freq="D")
        ny = pd.DatetimeIndex([pd.Timestamp(f"{d.date()} 17:00", tz="America/New_York") for d in days])
        self.roll = to_min(pd.Series(ny.tz_convert("UTC")))

    def _st(self, a: np.ndarray, fn) -> np.ndarray:
        st = np.empty((LV, len(a)), dtype=np.float64)
        st[0] = a
        for k in range(1, LV):
            h = 1 << (k - 1)
            st[k] = st[k - 1]
            st[k, :-h] = fn(st[k - 1, :-h], st[k - 1, h:])
        return st

    def rq(self, st: np.ndarray, a: np.ndarray, b: np.ndarray, fn) -> np.ndarray:
        L = b - a + 1
        assert L.max(initial=1) < (1 << LV), "aralık seyrek tablodan uzun"
        k = self.log2[L]
        return fn(st[k, a], st[k, b - (1 << k) + 1])

    def cond(self, i0, b, thr, side):
        lo = self.rq(self.stl, i0, b, np.minimum)
        hi = self.rq(self.sth, i0, b, np.maximum)
        return np.where(side > 0, lo <= thr, hi >= thr)

    def first_hit(self, i0, i1, thr, side) -> np.ndarray:
        hit = self.cond(i0, i1, thr, side)
        lo, hi = i0.copy(), i1.copy()
        while True:
            act = hit & (lo < hi)
            if not act.any():
                break
            mid = (lo + hi) // 2
            c = self.cond(i0, mid, thr, side)
            hi = np.where(act & c, mid, hi)
            lo = np.where(act & ~c, mid + 1, lo)
        return np.where(hit, lo, -1)

    def last_close_before(self, t: np.ndarray) -> np.ndarray:
        j = np.searchsorted(self.ts, t, "left") - 1
        return self.c[np.maximum(j, 0)]

    def simulate(self, t_dec, side, T_abs, hold_min, stop_pct, stop_abs, mode: str = "base",
                 sig_close=None) -> pd.DataFrame:
        """Olay başına sonuç. stop_pct>0 → D = giriş×stop_pct; değilse D = stop_abs (fiyat).
        T_abs: mutlak zaman çıkışı (dk) — hold_min>0 ise T = giriş+hold_min.
        mode: base | stress | fix | opt (sinyal kapanışından giriş, spread 0)."""
        t_dec = np.asarray(t_dec, np.int64)
        side = np.asarray(side, np.int64)
        T_abs = np.asarray(T_abs, np.int64)
        hold_min = np.asarray(hold_min, np.int64)
        stop_pct = np.asarray(stop_pct, np.float64)
        stop_abs = np.asarray(stop_abs, np.float64)
        i0 = np.searchsorted(self.ts, t_dec, "left")
        ok = i0 < self.n
        i0c = np.minimum(i0, self.n - 1)
        ok &= (self.ts[i0c] - t_dec) <= MAX_LAG
        T = np.where(hold_min > 0, self.ts[i0c] + hold_min, T_abs)
        i1 = np.searchsorted(self.ts, T, "left") - 1
        ok &= i1 >= i0c
        i1c = np.maximum(i1, i0c)
        ok &= ~((self.ts[i0c] < EXCL[1]) & (self.ts[i1c] + 1 > EXCL[0]))
        ok &= np.isfinite(stop_pct) & np.isfinite(stop_abs)
        idx = np.flatnonzero(ok)
        a, b, sd = i0c[idx], i1c[idx], side[idx]
        px0 = self.o[a]
        if mode == "base":
            hs = 0.5 * SPR_BASE * px0
        elif mode == "stress":
            hs = 0.5 * SPR_STRESS * px0
        elif mode == "fix":
            hs = np.full(len(a), 0.5 * SPR_FIX)
        elif mode == "opt":
            hs = np.zeros(len(a))
        else:
            raise ValueError(mode)
        entry = (np.asarray(sig_close, np.float64)[idx] if mode == "opt" else px0 + sd * hs)
        D = np.where(stop_pct[idx] > 0, entry * stop_pct[idx], stop_abs[idx])
        stop = entry - sd * D
        thr = np.where(sd > 0, stop + hs, stop - hs)
        j = self.first_hit(a, b, thr, sd)
        hit = j >= 0
        jj = np.where(hit, j, b)
        gap_px = np.where(sd > 0, np.minimum(self.o[jj] - hs, stop), np.maximum(self.o[jj] + hs, stop))
        px_stop = np.where(jj > a, gap_px, stop)
        px = np.where(hit, px_stop, self.c[b] - sd * hs)
        nights = (np.searchsorted(self.roll, self.ts[jj], "right")
                  - np.searchsorted(self.roll, self.ts[a], "right"))
        swap = np.where(sd > 0, -entry * SWAP_L * nights, entry * SWAP_S * nights)
        pnl = sd * (px - entry) + swap
        return pd.DataFrame({"k": idx, "t_in": self.ts[a], "t_out": self.ts[jj] + 1, "side": sd,
                             "entry": entry, "D": D, "R": pnl / D, "ret": pnl / entry, "stopped": hit,
                             "nights": nights, "day": self.ts[a] // 1440})


# ---------------------------------------------------------------- günlük çerçeve
def daily(m1: M1) -> pd.DataFrame:
    d = pd.read_parquet(DATA / "btc_1d.parquet", columns=["ts", "open", "high", "low", "close"])
    d["day"] = to_min(d.ts) // 1440
    d = d.set_index("day")
    assert (np.diff(d.index) == 1).all(), "günlük seri boşluklu"
    r = d.close.pct_change()
    d["r"] = r
    d["sig20"] = r.shift(1).rolling(20).std()
    d["r1"] = r.shift(1)
    d["r5"] = d.close.shift(1) / d.close.shift(6) - 1
    d["pdl"] = d.low.shift(1)
    d["pdh"] = d.high.shift(1)
    s30 = r.shift(1).rolling(30).std()
    med = s30.rolling(365, min_periods=120).median()
    d["rvhi"] = np.where(med.isna() | s30.isna(), np.nan, (s30 > med).astype(float))
    mac = pd.read_parquet(DATA / "macro_daily.parquet")
    mac = mac[mac.vix_close.notna() & mac.qqq_close.notna()].sort_values("avail_utc")
    start = pd.DataFrame({"t": pd.to_datetime(d.index.to_numpy() * 1440 * 60, unit="s", utc=True)})
    vx = pd.merge_asof(start, mac[["avail_utc", "vix_close"]], left_on="t", right_on="avail_utc",
                       direction="backward", allow_exact_matches=True)
    d["vix"] = vx.vix_close.to_numpy()
    d["year"] = pd.to_datetime(d.index.to_numpy() * 86400, unit="s").year
    return d


# ---------------------------------------------------------------- istatistik
def block_boot(v: np.ndarray, g: np.ndarray, n: int = 5000, seed: int = 7) -> np.ndarray:
    if len(v) == 0:
        return np.array([np.nan])
    u, inv = np.unique(g, return_inverse=True)
    s = np.bincount(inv, weights=v)
    c = np.bincount(inv)
    rng = np.random.default_rng(seed)
    pick = rng.integers(0, len(u), size=(n, len(u)))
    return s[pick].sum(1) / np.maximum(c[pick].sum(1), 1)


def single_pos(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values("t_in")
    keep, last = [], -1
    for ti, to in zip(df.t_in.to_numpy(), df.t_out.to_numpy()):
        if ti >= last:
            keep.append(True)
            last = to
        else:
            keep.append(False)
    return df[np.array(keep, bool)]


def stats(df: pd.DataFrame) -> dict:
    if len(df) == 0:
        return {"n": 0}
    v = df.R.to_numpy()
    bs = block_boot(v, df.day.to_numpy())
    w, l = v[v > 0], v[v <= 0]
    be = (abs(l.mean()) / (w.mean() + abs(l.mean()))) if len(w) and len(l) else np.nan
    h = len(v) // 2
    o = df.sort_values("t_in").R.to_numpy()
    return {"n": int(len(v)), "gun": int(df.day.nunique()), "wr": round(100 * float((v > 0).mean()), 1),
            "basabas_wr": round(100 * float(be), 1) if np.isfinite(be) else None,
            "ortR": round(float(v.mean()), 4), "ci95": [round(float(np.percentile(bs, 2.5)), 4),
                                                       round(float(np.percentile(bs, 97.5)), 4)],
            "P_EV": round(float(np.mean(bs > 0)), 4), "p_tek": round(float(np.mean(bs <= 0)), 4),
            "yari1": round(float(o[:h].mean()), 4) if h else None, "yari2": round(float(o[h:].mean()), 4),
            "toplamR": round(float(v.sum()), 2), "ort_ret_bp": round(1e4 * float(df.ret.mean()), 2),
            "stop_orani": round(float(df.stopped.mean()), 3)}
