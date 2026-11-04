"""Literal mum eşleştirme — ortak veri + numba çekirdeği (ön-kayıt: PROTOCOL.md).

Dokunulmaz dönem: ts + TF < 2025-12-01 olmayan bar YÜKLENMEZ (assert).
"""
from __future__ import annotations

import os

os.environ.setdefault("NUMBA_NUM_THREADS", "2")
os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "2")
os.environ.setdefault("VECLIB_MAXIMUM_THREADS", "2")

from pathlib import Path

import numba as nb
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RES = HERE / "results"
HOLDOUT = pd.Timestamp("2025-12-01", tz="UTC")
PM, GF = ROOT / "research/ndx_pattern_motifs/data", ROOT / "research/ndx_gate_forge/data"
PATHS = {"1m": PM / "bars_1m.parquet", "5m": PM / "bars_5m.parquet", "15m": PM / "bars_15m.parquet",
         "1h": GF / "long_1h_utc.parquet"}
TF_MIN = {"1m": 1, "5m": 5, "15m": 15, "1h": 60}
HZ = {"1m": ["15m", "1h", "1d"], "5m": ["15m", "1h", "1d"], "15m": ["15m", "1h", "1d"], "1h": ["1h", "1d"]}
HZ_MIN = {"15m": 15, "1h": 60, "1d": 1440}
XS = np.array([10, 15, 20, 25, 30, 40, 50], dtype=np.int64)
TOLS = [("pct", 0.005), ("pct", 0.01), ("pct", 0.015), ("pct", 0.02), ("pct", 0.03), ("pct", 0.05),
        ("atr", 0.1), ("atr", 0.2), ("atr", 0.3)]
RULES = [("birebir", 1.0, 0)] + [(f"%{int(f * 100)}_son{m}", f, m) for f in (0.9, 0.8, 0.7) for m in (1, 2, 3)]
NR, NC, NX = len(RULES), 4, len(XS)          # combo c: bit0 = uygunluk, bit1 = seans
QSTEP = {"1m": 50, "5m": 10, "15m": 8, "1h": 8}
QSTART = {"1m": "2025-02-01", "5m": "2025-02-01", "15m": "2023-12-01", "1h": "2017-06-01"}
LIB_YEARS = 5
SEG_GAP_NS = 3 * 86_400 * 10**9
NS_MIN = 60 * 10**9
BIG = np.iinfo(np.int64).max


def load(tf: str) -> dict:
    d = pd.read_parquet(PATHS[tf])
    d = d.sort_values("ts").drop_duplicates("ts").reset_index(drop=True)
    d = d[d.ts + pd.Timedelta(minutes=TF_MIN[tf]) < HOLDOUT].reset_index(drop=True)      # DOKUNULMAZ
    assert (d.ts + pd.Timedelta(minutes=TF_MIN[tf])).max() < HOLDOUT
    ts = d.ts.dt.tz_convert("UTC").dt.tz_localize(None).to_numpy().astype("datetime64[ns]").astype(np.int64)
    o, h, l, c = (d[k].to_numpy(np.float64) for k in ("open", "high", "low", "close"))
    n = len(d)
    brk = np.r_[True, np.diff(ts) > SEG_GAP_NS]
    if "seg" in d.columns:
        brk |= np.r_[True, d.seg.to_numpy()[1:] != d.seg.to_numpy()[:-1]]
    seg = np.cumsum(brk) - 1
    seg_start = np.zeros(n, np.int64)
    starts = np.flatnonzero(brk)
    seg_start[:] = starts[seg]
    close = ts + TF_MIN[tf] * NS_MIN
    pc = np.r_[c[0], c[:-1]]
    tr = np.maximum(h - l, np.maximum(np.abs(h - pc), np.abs(l - pc)))
    A = pd.Series(tr).rolling(14).mean().shift(1).to_numpy()
    A[seg_start > np.arange(n) - 15] = np.nan                                                 # ATR segment içinde
    pct = np.stack([100 * (h / o - 1), 100 * (l / o - 1), 100 * (c / o - 1)], 1)
    raw = np.stack([h - o, l - o, c - o], 1)
    hour = ((close // (3600 * 10**9)) % 24).astype(np.int8)
    hz = HZ[tf]
    endT = np.full((len(hz), n), BIG, np.int64); yv = np.full((len(hz), n), np.nan)
    for hi, hn in enumerate(hz):
        e, y = outcome(close, seg, c, HZ_MIN[hn])
        endT[hi], yv[hi] = e, y
    rng_pct = pct[:, 0] - pct[:, 1]
    rng_raw = h - l
    medR = {"pct": np.zeros((NX, n), np.float32), "atr": np.zeros((NX, n), np.float32)}
    for xi, X in enumerate(XS):
        medR["pct"][xi] = pd.Series(rng_pct).rolling(int(X)).median().to_numpy()
        medR["atr"][xi] = pd.Series(rng_raw).rolling(int(X)).median().to_numpy()
    return dict(tf=tf, n=n, ts=ts, close=close, o=o, h=h, l=l, c=c, seg=seg, seg_start=seg_start, A=A, pct=pct,
                raw=raw, hour=hour, endT=endT, yv=yv, medR=medR, hz=hz)


def outcome(close: np.ndarray, seg: np.ndarray, c: np.ndarray, hmin: int) -> tuple:
    n = len(close)
    T = close + hmin * NS_MIN
    if hmin >= 1440:
        wd = ((T // (86_400 * 10**9)) + 3) % 7                    # 0 = Pazartesi (1970-01-01 Perşembe)
        T = T + np.where(wd == 5, 2, np.where(wd == 6, 1, 0)) * 86_400 * 10**9
    j = np.searchsorted(close, T, side="right") - 1
    jj = np.clip(j, 0, n - 1)
    if hmin >= 1440:
        ok = (j > np.arange(n)) & (T - close[jj] <= 60 * NS_MIN)
    else:
        ok = (j > np.arange(n)) & (close[jj] == T)
    ok &= seg[jj] == seg
    endT = np.where(ok, close[jj], BIG)
    y = np.where(ok, c[jj] - c, np.nan)
    return endT, y


def query_grid(D: dict) -> np.ndarray:
    tf = D["tf"]
    t0 = pd.Timestamp(QSTART[tf]).value
    idx = np.arange(D["n"])
    ok = (D["ts"] >= t0) & (idx % QSTEP[tf] == 0) & (D["seg_start"] <= idx - 63) & np.isfinite(D["A"])
    return np.flatnonzero(ok)


def lib_lo(D: dict, qs: np.ndarray) -> np.ndarray:
    lo_t = D["close"][qs] - int(365.25 * LIB_YEARS * 86_400) * 10**9
    return np.maximum(np.searchsorted(D["ts"], lo_t), 64).astype(np.int64)


def rep_arrays(D: dict, rep: str) -> tuple:
    if rep == "pct":
        return D["pct"], np.ones(D["n"]), D["medR"]["pct"]
    A = D["A"]
    inv = np.where(np.isfinite(A) & (A > 0), 1.0 / np.where(A > 0, A, 1.0), np.nan)
    return D["raw"], inv, D["medR"]["atr"]


# ─────────────────────────── çekirdek ───────────────────────────
@nb.njit(parallel=True, fastmath=False, cache=True)
def scan(qs, lo_q, close, ts, F, invA, medR, seg_start, hour, endT, yv, tol, thin, XS,
         nraw, nind, upc, dnc, qelig, qvalid):
    """Sorgu başına: her yuva (h, xi, r, c) için ham eşleşme sayısı, bağımsız sayı, bağımsızlarda yukarı/aşağı sayısı.

    r = 0 birebir (tüm kütüphane); r = 1..9 kısmi (yalnız thin[e] konumları). c bit0 uygunluk, bit1 seans.
    """
    nq = qs.shape[0]; nh = endT.shape[0]; nx = XS.shape[0]
    c07 = np.empty(nx, np.int64); c08 = np.empty(nx, np.int64); c09 = np.empty(nx, np.int64)
    for xi in range(nx):
        c07[xi] = int(np.ceil(0.7 * XS[xi] - 1e-9)); c08[xi] = int(np.ceil(0.8 * XS[xi] - 1e-9))
        c09[xi] = int(np.ceil(0.9 * XS[xi] - 1e-9))
    xmax = XS[nx - 1]
    for qi in nb.prange(nq):
        q = qs[qi]; lo = lo_q[qi]; cq = close[q]; hq = hour[q]; sq = invA[q]
        if not np.isfinite(sq):
            continue
        Qf = np.empty((xmax, 3))
        for k in range(xmax):
            for f in range(3):
                Qf[k, f] = F[q - k, f] * sq
        qmaxk = q - seg_start[q] + 1
        for xi in range(nx):
            qvalid[qi, xi] = XS[xi] <= qmaxk
            qelig[qi, xi] = medR[xi, q] * sq >= 3.0 * tol
        lastEnd = np.full((nh, nx, 10, 4), -1, np.int64)
        cnt = np.empty(nx, np.int64)
        for e in range(lo, q):
            s = invA[e]
            if not np.isfinite(s):
                continue
            if abs(F[e, 0] * s - Qf[0, 0]) > tol or abs(F[e, 1] * s - Qf[0, 1]) > tol or abs(F[e, 2] * s - Qf[0, 2]) > tol:
                continue
            maxk = e - seg_start[e] + 1
            if qmaxk < maxk:
                maxk = qmaxk
            # birebir koşu uzunluğu
            L = 1
            while L < xmax and L < maxk:
                k = L
                if abs(F[e - k, 0] * s - Qf[k, 0]) > tol or abs(F[e - k, 1] * s - Qf[k, 1]) > tol or \
                        abs(F[e - k, 2] * s - Qf[k, 2]) > tol:
                    break
                L += 1
            deep = thin[e]
            if L < XS[0] and not deep:
                continue
            for xi in range(nx):
                cnt[xi] = -1
            if deep:
                mism = 0; xi = 0
                for k in range(xmax):
                    if k >= maxk:
                        break
                    if k < L:
                        m = True
                    elif k == L:
                        m = False
                    else:
                        m = not (abs(F[e - k, 0] * s - Qf[k, 0]) > tol or abs(F[e - k, 1] * s - Qf[k, 1]) > tol or
                                 abs(F[e - k, 2] * s - Qf[k, 2]) > tol)
                    if not m:
                        mism += 1
                    if k + 1 == XS[xi]:
                        cnt[xi] = k + 1 - mism
                        xi += 1
                        if xi == nx:
                            break
                    if mism > 15:
                        break
            dh = abs(int(hour[e]) - int(hq))
            if dh > 12:
                dh = 24 - dh
            sess = dh <= 1
            Lc = L if L < 3 else 3
            for xi in range(nx):
                X = XS[xi]
                if X > maxk:
                    break
                isex = L >= X
                cx = cnt[xi]
                p70 = deep and cx >= c07[xi]
                if not isex and not p70:
                    continue
                p80 = deep and cx >= c08[xi]
                p90 = deep and cx >= c09[xi]
                el = medR[xi, e] * s >= 3.0 * tol
                wstart = ts[e - X + 1]
                for h in range(nh):
                    et = endT[h, e]
                    if et > cq:
                        continue
                    y = yv[h, e]
                    for c in range(4):
                        if (c & 1) and not el:
                            continue
                        if (c & 2) and not sess:
                            continue
                        for r in range(10):
                            if r == 0:
                                ok = isex
                            else:
                                lev = (r - 1) // 3; mm = (r - 1) % 3 + 1
                                ok = (p90 if lev == 0 else (p80 if lev == 1 else p70)) and Lc >= mm
                            if not ok:
                                continue
                            slot = ((h * nx + xi) * 10 + r) * 4 + c
                            nraw[qi, slot] += 1
                            if wstart >= lastEnd[h, xi, r, c]:
                                lastEnd[h, xi, r, c] = et
                                nind[qi, slot] += 1
                                if y > 0:
                                    upc[qi, slot] += 1
                                elif y < 0:
                                    dnc[qi, slot] += 1


def run_scan(D: dict, qs: np.ndarray, rep: str, tol: float, phi: float, seed: int = 1) -> dict:
    F, invA, medR = rep_arrays(D, rep)
    n = D["n"]; nh = len(D["hz"])
    rng = np.random.default_rng(seed)
    thin = rng.random(n) < phi if phi < 1 else np.ones(n, bool)
    lo = lib_lo(D, qs)
    ns = nh * NX * NR * NC
    nraw = np.zeros((len(qs), ns), np.int32); nind = np.zeros_like(nraw); upc = np.zeros_like(nraw); dnc = np.zeros_like(nraw)
    qelig = np.zeros((len(qs), NX), np.bool_); qvalid = np.zeros((len(qs), NX), np.bool_)
    scan(qs.astype(np.int64), lo, D["close"], D["ts"], np.ascontiguousarray(F), invA, medR, D["seg_start"], D["hour"],
         D["endT"], D["yv"], float(tol), thin, XS, nraw, nind, upc, dnc, qelig, qvalid)
    shp = (len(qs), nh, NX, NR, NC)
    return dict(nraw=nraw.reshape(shp), nind=nind.reshape(shp), up=upc.reshape(shp), dn=dnc.reshape(shp),
                qelig=qelig, qvalid=qvalid, phi=phi)


@nb.njit(parallel=True, cache=True)
def k0_rate(qs, lo_q, F, invA, tol):
    """Son mumu tutan aday oranı (inceltme oranı seçimi için; sonuçlara bakmaz)."""
    out = np.zeros(qs.shape[0])
    for qi in nb.prange(qs.shape[0]):
        q = qs[qi]; sq = invA[q]; m = 0; tot = 0
        if not np.isfinite(sq):
            continue
        for e in range(lo_q[qi], q):
            s = invA[e]
            if not np.isfinite(s):
                continue
            tot += 1
            if abs(F[e, 0] * s - F[q, 0] * sq) <= tol and abs(F[e, 1] * s - F[q, 1] * sq) <= tol and \
                    abs(F[e, 2] * s - F[q, 2] * sq) <= tol:
                m += 1
        out[qi] = m
    return out
