"""fam_volyapi ortak motor: veri ızgarası, geometri ön-hesabı, sonuç çözümü, plasebo, istatistik.

Kurallar prereg.md §1–§5. Giriş e = karar dakikası t + 1, fiyat open[e]. Aynı bar TP+SL → SL (ana).
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "/Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/feasibility")
import lib  # noqa: E402  (sparse_tables yeniden kullanımı)

BASE = "/Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021"
DATA = f"{BASE}/data/btc_scalp_1m.parquet"
FAM = f"{BASE}/fam_volyapi"
CACHE = f"{FAM}/cache"
RES = f"{FAM}/results"

T0 = pd.Timestamp("2021-06-01", tz="UTC")
SL_FLOOR_BP = 19.0
SL_ATR_MULT = 1.1
HMAX = 60
MIN_LEFT = 10
COSTS = {"PEP": 1.85, "STRESS": 2.78, "MAKER": 4.0, "TAKER": 10.0}  # FIX15 ayrı (fiyata bağlı)
GEOMS = {"G1": (1.0, 30), "G2": (1.0, 60), "G3": (2.0, 30), "G4": (2.0, 60)}
SPLITS = {
    "DISC": ("2021-06-01", "2024-01-01"),
    "OOS": ("2024-01-11", "2025-07-01"),
    "BLIND": ("2025-07-01", "2026-10-21"),
}
N_PLACEBO = 200
N_BOOT = 2000


def tm(ts: str) -> int:
    t = pd.Timestamp(ts)
    if t.tzinfo is None:
        t = t.tz_localize("UTC")
    return int((t - T0) / pd.Timedelta(minutes=1))


class Grid:
    """Tam dakika ızgarası (2021-06-01 → 2026-10-20 23:59)."""

    def __init__(self, prefix: str = "spot") -> None:
        cols = ["ts", f"{prefix}_open", f"{prefix}_high", f"{prefix}_low", f"{prefix}_close",
                "spot_volume", "spot_quote_volume", "spot_missing"]
        df = pd.read_parquet(DATA, columns=cols)
        idx = ((df["ts"] - T0) / pd.Timedelta(minutes=1)).to_numpy().astype(np.int64)
        assert np.all(idx == np.arange(len(idx))), "ızgara tam değil"
        self.N = n = len(idx)
        self.O = df[f"{prefix}_open"].to_numpy().astype(float)
        self.H = df[f"{prefix}_high"].to_numpy().astype(float)
        self.L = df[f"{prefix}_low"].to_numpy().astype(float)
        self.C = df[f"{prefix}_close"].to_numpy().astype(float)
        self.V = df["spot_volume"].to_numpy().astype(float)
        self.Q = df["spot_quote_volume"].to_numpy().astype(float)
        miss = (df["spot_missing"].to_numpy() == 1) | np.isnan(self.C)
        for a in (self.O, self.H, self.L, self.C):
            a[miss] = np.nan
        bad = np.zeros(n, dtype=bool)
        bad[tm("2023-03-24 11:28"):tm("2023-03-24 14:00")] = True
        d = np.diff(np.concatenate([[0], miss.astype(np.int8), [0]]))
        for a, b in zip(np.where(d == 1)[0], np.where(d == -1)[0]):
            if b - a >= 5:
                bad[a:b] = True
        for a in (self.O, self.H, self.L, self.C):
            a[bad] = np.nan
        self.V[np.isnan(self.C)] = np.nan
        self.Q[np.isnan(self.C)] = np.nan
        self.bad = bad
        self.CF = pd.Series(self.C).ffill().to_numpy()
        self._time()
        self._atr5()
        self._roll()
        self._slip()

    # ── zaman ─────────────────────────────────────────────────────────────
    def _time(self) -> None:
        n = self.N
        m = np.arange(n)
        self.utc_hour = (m // 60) % 24
        self.utc_day = m // 1440
        dt = pd.DatetimeIndex(T0 + pd.to_timedelta(m, unit="min"))
        self.year = dt.year.to_numpy()
        self.utc_wd = dt.weekday.to_numpy()
        ny = dt.tz_convert("America/New_York")
        self.ny_mod = (ny.hour * 60 + ny.minute).to_numpy()
        self.ny_day = (ny.normalize().tz_localize(None) - pd.Timestamp("2021-01-01")).days.to_numpy()
        self.ny_wd = ny.weekday.to_numpy()
        lo = dt.tz_convert("Europe/London")
        self.lo_mod = (lo.hour * 60 + lo.minute).to_numpy()
        self.lo_wd = lo.weekday.to_numpy()
        self.lo_day = (lo.normalize().tz_localize(None) - pd.Timestamp("2021-01-01")).days.to_numpy()
        self.split = np.full(n, "", dtype=object)
        for k, (a, b) in SPLITS.items():
            self.split[tm(a):tm(b)] = k

    def _atr5(self) -> None:
        n5 = self.N // 5
        h5 = np.nanmax(self.H.reshape(n5, 5), axis=1) if True else None
        l5 = np.nanmin(self.L.reshape(n5, 5), axis=1)
        c5 = pd.DataFrame(self.C.reshape(n5, 5)).ffill(axis=1).iloc[:, -1].to_numpy()
        self.h5, self.l5, self.c5 = h5, l5, c5
        o5 = pd.DataFrame(self.O.reshape(n5, 5)).bfill(axis=1).iloc[:, 0].to_numpy()
        self.o5 = o5
        pc = np.concatenate([[np.nan], c5[:-1]])
        tr = np.nanmax(np.vstack([h5 - l5, np.abs(h5 - pc), np.abs(l5 - pc)]), axis=0)
        a = pd.Series(tr).rolling(14, min_periods=10).mean().to_numpy()
        m = np.arange(self.N)
        last = m // 5 - 1
        atr = np.full(self.N, np.nan)
        ok = last >= 0
        atr[ok] = a[last[ok]]
        self.atr5 = atr  # fiyat birimi, e girişinde bilinen
        cprev = np.concatenate([[np.nan], self.CF[:-1]])
        self.atr5bp = atr / cprev * 1e4
        self.s_bp = np.maximum(SL_FLOOR_BP, SL_ATR_MULT * self.atr5bp)

    def _roll(self) -> None:
        """e'den NY 16:58'e kalan dakika (zorunlu kapanış). [16:55,17:05) girişleri yasak."""
        n = self.N
        is_cut = self.ny_mod == 16 * 60 + 58
        nxt = np.full(n + 1, n + 100000, dtype=np.int64)
        idx = np.where(is_cut)[0]
        nxt_arr = np.full(n, n + 100000, dtype=np.int64)
        nxt_arr[idx] = idx
        nxt_arr = np.minimum.accumulate(nxt_arr[::-1])[::-1]
        self.rollleft = np.minimum(nxt_arr - np.arange(n), 100000)
        self.noentry = (self.ny_mod >= 16 * 60 + 55) & (self.ny_mod < 17 * 60 + 5)
        del nxt

    def _slip(self) -> None:
        r = np.abs(np.diff(np.log(self.CF), prepend=np.nan))
        thr = np.full(self.N, np.inf)
        for y in np.unique(self.year):
            mk = self.year == y
            thr[mk] = np.nanpercentile(r[mk], 99)
        self.slip_bp = np.where(r > thr, 5.0, 1.0)

    # ── geçerlilik ve ön-hesap ────────────────────────────────────────────
    def valid_entries(self) -> np.ndarray:
        n = self.N
        e = np.arange(n)
        ok = np.isfinite(self.O) & np.isfinite(self.s_bp)
        ok[1:] &= np.isfinite(self.C[:-1])
        ok[0] = False
        ok &= ~self.noentry
        ok &= self.rollleft >= MIN_LEFT
        lw = np.minimum(HMAX, self.rollleft)
        hi = np.minimum(e + lw, n)
        bcs = np.concatenate([[0], np.cumsum(self.bad)])
        ok &= (bcs[hi] - bcs[e]) == 0
        ok &= e + lw <= n
        return ok

    def precompute(self, tag: str = "spot") -> None:
        path = f"{CACHE}/hits_{tag}.npz"
        self.valid = self.valid_entries()
        if os.path.exists(path):
            z = np.load(path)
            self.K = {k: z[k] for k in z.files}
            return
        MX, MN = lib.sparse_tables(self.H, self.L, klev=6)
        ev = np.where(self.valid)[0]
        Lw = np.minimum(HMAX, self.rollleft[ev]).astype(np.int64)
        ent = self.O[ev]
        s = self.s_bp[ev] / 1e4
        K = {}
        for d, nm in ((1, "L"), (-1, "S")):
            sl = ent * (1 - d * s)
            K[f"sl_{nm}"] = first_hit_var(MN if d == 1 else MX, ev, sl, Lw, up=(d == -1))
            for r in (1.0, 2.0):
                tp = ent * (1 + d * r * s)
                K[f"tp{int(r)}_{nm}"] = first_hit_var(MX if d == 1 else MN, ev, tp, Lw, up=(d == 1))
        full = {}
        for k, v in K.items():
            a = np.full(self.N, 127, dtype=np.int8)
            a[ev] = v
            full[k] = a
        np.savez_compressed(path, **full)
        self.K = full

    # ── sonuç çözümü ──────────────────────────────────────────────────────
    def resolve(self, e: np.ndarray, d: np.ndarray, r: float, H: int) -> dict:
        """e: giriş indeksleri (valid olmalı), d: ±1. Döner: brüt bp (kötümser/iyimser/sezgisel), s, çıkış, tür."""
        e = np.asarray(e, dtype=np.int64)
        d = np.asarray(d, dtype=np.int64)
        assert self.valid[e].all()
        Leff = np.minimum(H, self.rollleft[e]).astype(np.int64)
        isL = d == 1
        ksl = np.where(isL, self.K["sl_L"][e], self.K["sl_S"][e]).astype(np.int64)
        ktp = np.where(isL, self.K[f"tp{int(r)}_L"][e], self.K[f"tp{int(r)}_S"][e]).astype(np.int64)
        slh = ksl < Leff
        tph = ktp < Leff
        same = slh & tph & (ksl == ktp)
        tp_first = tph & (~slh | (ktp < ksl))
        sl_first = slh & (~tph | (ksl < ktp))
        tim = ~slh & ~tph
        ent = self.O[e]
        s = self.s_bp[e]
        # SL dolumu (boşluk-duyarlı) + kayma
        hit = e + np.where(slh, ksl, 0)
        oh = self.O[hit]
        slp = ent * (1 - d * s / 1e4)
        fill = np.where(isL, np.minimum(slp, oh), np.maximum(slp, oh))
        sl_bp = d * (fill / ent - 1) * 1e4 - self.slip_bp[hit]
        tp_bp = r * s
        xe = e + Leff - 1
        t_bp = d * (self.CF[xe] / ent - 1) * 1e4
        g_p = np.where(tp_first, tp_bp, np.where(sl_first | same, sl_bp, t_bp))
        g_o = np.where(tp_first | same, tp_bp, np.where(sl_first, sl_bp, t_bp))
        # sezgisel: aynı barda açılış hangi seviyeye yakınsa o önce (giriş barında SL)
        tpp = ent * (1 + d * r * s / 1e4)
        heur_tp = same & (ksl > 0) & (np.abs(oh - tpp) < np.abs(oh - slp))
        g_h = np.where(tp_first | heur_tp, tp_bp, np.where(sl_first | same, sl_bp, t_bp))
        xi = np.where(tp_first, e + ktp, np.where(sl_first | same, e + ksl, xe))
        typ = np.where(tp_first, 1, np.where(sl_first | same, -1, 0))
        return {"e": e, "d": d, "s": s, "g": g_p, "g_opt": g_o, "g_heur": g_h, "x": xi, "typ": typ,
                "same": same, "ent": ent}


def first_hit_var(T: np.ndarray, e: np.ndarray, thr: np.ndarray, Lw: np.ndarray, up: bool) -> np.ndarray:
    """[e, e+Lw) içinde ilk dokunuş göreli indeksi; yoksa Lw (lib.first_hit'in değişken pencereli hâli)."""
    n = T.shape[1]
    pos = e.copy()
    end = np.minimum(e + Lw, n)
    for k in range(T.shape[0] - 1, -1, -1):
        step = 1 << k
        ok = pos + step <= end
        idx = np.where(ok, pos, 0)
        v = T[k][idx]
        nohit = (v < thr) if up else (v > thr)
        pos = np.where(ok & nohit, pos + step, pos)
    inside = pos < end
    if inside.any():
        pi = np.where(inside, pos, 0)
        v = T[0][pi]
        okh = (v >= thr) if up else (v <= thr)
        assert np.all(okh[inside]), "first_hit_var tutarsız"
    k_rel = pos - e
    k_rel[~inside] = Lw[~inside]
    return k_rel.astype(np.int8)


# ── maliyet / R ───────────────────────────────────────────────────────────
def net_R(res: dict, cost: str = "PEP", which: str = "g") -> np.ndarray:
    if cost == "FIX15":
        c = 15.0 / res["ent"] * 1e4
    elif cost == "ZERO":
        c = 0.0
    else:
        c = COSTS[cost]
    return (res[which] - c) / res["s"]


def single_position(e: np.ndarray, x: np.ndarray) -> np.ndarray:
    """Önceki çıkıştan (x, çıkış barı) önce gelen giriş atlanır; çıkış barının ertesinden itibaren serbest."""
    o = np.argsort(e, kind="stable")
    keep = np.zeros(len(e), dtype=bool)
    busy = -1
    for i in o:
        if e[i] > busy:
            keep[i] = True
            busy = x[i]
    return keep


def day_boot(R: np.ndarray, day: np.ndarray, nb: int = N_BOOT, seed: int = 7):
    if len(R) == 0:
        return np.nan, np.nan, np.nan
    u, inv = np.unique(day, return_inverse=True)
    sums = np.bincount(inv, weights=R)
    cnt = np.bincount(inv).astype(float)
    rng = np.random.default_rng(seed)
    nd = len(u)
    W = rng.multinomial(nd, np.full(nd, 1.0 / nd), size=nb).astype(float)
    m = (W @ sums) / np.maximum(W @ cnt, 1)
    return float(np.mean(m > 0)), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def cluster_z(R: np.ndarray, day: np.ndarray) -> float:
    if len(R) < 3:
        return np.nan
    u, inv = np.unique(day, return_inverse=True)
    sums = np.bincount(inv, weights=R - R.mean())
    nd = len(u)
    if nd < 3:
        return np.nan
    var = (sums ** 2).sum() * nd / (nd - 1) / len(R) ** 2
    return float(R.mean() / np.sqrt(var)) if var > 0 else np.nan


class Placebo:
    """Aynı yıl × UTC saat havuzundan rastgele geçerli giriş, aynı yön, aynı geometri."""

    def __init__(self, g: Grid) -> None:
        ev = np.where(g.valid)[0]
        key = (g.year[ev] - 2021) * 24 + g.utc_hour[ev]
        o = np.argsort(key, kind="stable")
        self.pool = ev[o]
        ks = key[o]
        self.nk = 6 * 24
        self.start = np.searchsorted(ks, np.arange(self.nk))
        self.end = np.searchsorted(ks, np.arange(self.nk), side="right")
        self.g = g

    def draw(self, e: np.ndarray, nrep: int, seed: int) -> np.ndarray:
        g = self.g
        key = (g.year[e] - 2021) * 24 + g.utc_hour[e]
        st, en = self.start[key], self.end[key]
        rng = np.random.default_rng(seed)
        u = rng.random((nrep, len(e)))
        idx = st[None, :] + np.floor(u * (en - st)[None, :]).astype(np.int64)
        return self.pool[idx]
