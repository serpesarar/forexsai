"""Alternatif benzerlik algoritmaları — NDX yön tahmini, sızıntısız ileri yürüme (2026-10-13).

Ön-kayıt: PROTOKOL.md (aynı klasör). Aileler: zED (MASS eşdeğeri) · zED_amp · DTW (Sakoe–Chiba + LB_Keogh) · retcorr ·
SAXyol · ngram · NW (Nadaraya–Watson) · cokolcek (çok-ölçekli özet) · refR7 (ME-02 referansı).
HOLDOUT: bar bitişi ≥ 2025-12-01 00:00 UTC olan hiçbir bar yüklenmez (assert).

Çalıştır (proje kökünden):
  nice -n 10 python3 research/mum_derin_tarama_20261013/algoritmalar/alg_tarama.py            # 2 süreç: [1m] ve [5m,15m,1h]
  ALG_SMOKE=1 ... (her sette en çok 150 sorgu, 10 kaydırma)  ·  ALG_TFS=5m,1h  (yalnız bu TF'ler)
Çıktı: results/<tf>_<h>_cfg.parquet (yapılandırma satırları), results/<tf>_<h>_null.npz (kaydırılmış t/fark), results/<tf>_<h>_q.npz
"""
from __future__ import annotations

import os

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("VECLIB_MAXIMUM_THREADS", "1")
os.environ.setdefault("NUMBA_NUM_THREADS", "1")

import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numba as nb
import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view
from scipy.stats import norm

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = HERE / "results"
CUTOFF = pd.Timestamp("2025-12-01", tz="UTC")                      # HOLDOUT sınırı
SRC = {"1m": ROOT / "research/ndx_pattern_motifs/data/bars_1m.parquet",
       "5m": ROOT / "research/ndx_pattern_motifs/data/bars_5m.parquet",
       "15m": ROOT / "research/ndx_pattern_motifs/data/bars_15m.parquet",
       "1h": ROOT / "research/ndx_gate_forge/data/long_1h_utc.parquet"}
TF_MIN = {"1m": 1, "5m": 5, "15m": 15, "1h": 60}
HZ = {"15m": 15, "1h": 60, "1d": 1440}
SHORT_SPACING = {"1m": 60, "5m": 60, "15m": 120, "1h": 480}       # dakika (≥ kısa ufuklar)
DAY_SPACING = 1500                                                  # 25 saat → saat döner
WARM_DAYS = {"1m": 60, "5m": 60, "15m": 90, "1h": 365}
SHIFT_GROUP = {"1m": "duka", "5m": "duka", "15m": "p15", "1h": "p1h"}
WS = (10, 20, 30, 50)
KS = np.array([20, 50, 100], np.int64)
KMAX = 100
LIB_NS = np.int64(int(365.25 * 5) * 86400 * 10**9)
SEG_GAP_NS = np.int64(4 * 86400 * 10**9)
WEEK_NS = np.int64(7 * 86400 * 10**9)
MIN_NS = np.int64(60 * 10**9)
N_SHIFT = 200
R_PLC = 20
B_BOOT = 2000
L_TOP = 2000
L_DTW = 1000
L_DTW_MAX = 16000
NW_CAND = 300
SAX_CAP = 200
PMAX = 200
MIN_VOTE = 15
STRONG = 0.20
SAX_PATH = ((3, 4), (3, 8), (5, 4), (5, 8))
NGRAM = tuple((a, w) for a in (3, 4, 5) for w in (4, 6, 8))
SIG_WIN = 100
MS_SPANS = (1, 2, 4, 8, 16, 32)
CH = 32
SMOKE = os.environ.get("ALG_SMOKE") == "1"
if SMOKE:
    N_SHIFT = 10


# ═══════════════════════════ numba çekirdekleri ═══════════════════════════
@nb.njit(cache=True)
def top_l(dist, lo, hi, mask, L, rng_arr, rq, use_amp):
    """[lo, hi] içinde mask'li en küçük L mesafe (eşitlikler dahil), artan sıralı. trunc = havuz L'den büyüktü."""
    m = hi - lo + 1
    if m <= 0:
        return np.empty(0, np.int64), np.empty(0, np.float32), False
    idx = np.empty(m, np.int64); val = np.empty(m, np.float32); cnt = 0
    for j in range(lo, hi + 1):
        if mask[j]:
            if use_amp:
                rr = rng_arr[j] / rq
                if rr < 0.5 or rr > 2.0:
                    continue
            idx[cnt] = j; val[cnt] = dist[j]; cnt += 1
    idx = idx[:cnt]; val = val[:cnt]
    trunc = False
    if cnt > L:
        thr = np.partition(val.copy(), L - 1)[L - 1]
        keep = val <= thr
        idx = idx[keep]; val = val[keep]; trunc = True
    o = np.argsort(val, kind="mergesort")
    return idx[o], val[o], trunc


@nb.njit(cache=True)
def dedup_pos(cand, okh, hi0, gap, kmax):
    """Mesafe sırasıyla: hi0'dan sonrasını ve sonucu geçersizleri at, seçilenler arası ≥ gap bar. Dönen: cand içi konumlar."""
    kept = np.empty(kmax, np.int64); pos = np.empty(kmax, np.int64); k = 0
    for p in range(cand.shape[0]):
        c = cand[p]
        if c > hi0 or not okh[c]:
            continue
        good = True
        for t in range(k):
            if abs(c - kept[t]) < gap:
                good = False
                break
        if good:
            kept[k] = c; pos[k] = p; k += 1
            if k == kmax:
                break
    return pos[:k]


@nb.njit(cache=True)
def bsearch_right(a, v):
    lo, hi = 0, a.shape[0]
    while lo < hi:
        mid = (lo + hi) // 2
        if a[mid] <= v:
            lo = mid + 1
        else:
            hi = mid
    return lo


@nb.njit(cache=True)
def match_recent(group, lo, hi, okh, gap, cap):
    """Aynı kelimeye sahip pencereler (group: artan indeks), hi'den geriye, ≥ gap aralıkla, en çok cap."""
    out = np.empty(cap, np.int64); k = 0
    p = bsearch_right(group, hi) - 1
    last = np.int64(1) << 62
    while p >= 0 and k < cap:
        j = group[p]
        if j < lo:
            break
        if okh[j] and (last - j) >= gap:
            out[k] = j; k += 1; last = j
        p -= 1
    return out[:k]


@nb.njit(cache=True)
def lb_keogh_all(Z, U, Lw, lo, hi, mask, out):
    W = U.shape[0]
    for j in range(lo, hi + 1):
        if not mask[j]:
            out[j] = np.inf
            continue
        s = 0.0
        for i in range(W):
            x = Z[j, i]
            if x > U[i]:
                d = x - U[i]; s += d * d
            elif x < Lw[i]:
                d = Lw[i] - x; s += d * d
        out[j] = s


@nb.njit(cache=True)
def envelope(q, r):
    W = q.shape[0]; U = np.empty(W, np.float32); Lw = np.empty(W, np.float32)
    for i in range(W):
        a = max(0, i - r); b = min(W, i + r + 1)
        mx = q[a]; mn = q[a]
        for t in range(a, b):
            if q[t] > mx:
                mx = q[t]
            if q[t] < mn:
                mn = q[t]
        U[i] = mx; Lw[i] = mn
    return U, Lw


@nb.njit(cache=True)
def dtw_band(a, b, r):
    n = a.shape[0]; INF = 1e30
    prev = np.full(n + 1, INF); cur = np.full(n + 1, INF)
    prev[0] = 0.0
    for i in range(1, n + 1):
        r0 = max(0, i - r - 1); r1 = min(n, i + r + 1)
        for j in range(r0, r1 + 1):
            cur[j] = INF
        jlo = max(1, i - r); jhi = min(n, i + r)
        for j in range(jlo, jhi + 1):
            d = a[i - 1] - b[j - 1]
            m = prev[j - 1]
            if prev[j] < m:
                m = prev[j]
            if cur[j - 1] < m:
                m = cur[j - 1]
            cur[j] = d * d + m
        tmp = prev; prev = cur; cur = tmp
    return prev[n]


@nb.njit(cache=True)
def dtw_many(Z, qz, cand, r, out, start):
    for p in range(start, cand.shape[0]):
        out[p] = dtw_band(qz, Z[cand[p]], r)


@nb.njit(cache=True)
def _finish(n, cm, cmaj, chour, Sm, Sh, Nb):
    ncfg = n.shape[0]
    acc = np.full(ncfg, np.nan); am = np.full(ncfg, np.nan); ah = np.full(ncfg, np.nan)
    exc = np.full(ncfg, np.nan); tst = np.full(ncfg, np.nan); useh = np.zeros(ncfg, np.int8)
    nblk = Sm.shape[1]
    for c in range(ncfg):
        if n[c] < 2:
            continue
        acc[c] = cm[c] / n[c]; am[c] = cmaj[c] / n[c]; ah[c] = chour[c] / n[c]
        if ah[c] > am[c]:
            useh[c] = 1; cb = chour[c]
        else:
            cb = cmaj[c]
        d = (cm[c] - cb) / n[c]
        exc[c] = d
        v = 0.0; nb_used = 0
        for b in range(nblk):
            if Nb[c, b] > 0:
                nb_used += 1
                S = Sh[c, b] if useh[c] == 1 else Sm[c, b]
                e = S - d * Nb[c, b]
                v += e * e
        if nb_used > 1 and v > 0:
            v = v / (n[c] * n[c]) * nb_used / (nb_used - 1)
            tst[c] = d / np.sqrt(v)
    return acc, am, ah, exc, tst, useh


@nb.njit(cache=True)
def _accum(cfg, call, t, bm, bh, b, n, cm, cmaj, chour, Sm, Sh, Nb):
    c = 1.0 if call == t else 0.0
    m = 1.0 if bm == t else 0.0
    h = 1.0 if bh == t else 0.0
    n[cfg] += 1; cm[cfg] += c; cmaj[cfg] += m; chour[cfg] += h
    Sm[cfg, b] += c - m; Sh[cfg, b] += c - h; Nb[cfg, b] += 1


@nb.njit(cache=True)
def eval_knn(nbm, nn, ysg, qt, bmaj, bhour, blk, nblk, Ks, strong, min_vote, calls, write):
    """Komşu oyu. cfg = iK*2 + kural (0 tüm, 1 güçlü)."""
    Q = nbm.shape[0]; nK = Ks.shape[0]; ncfg = nK * 2
    n = np.zeros(ncfg); cm = np.zeros(ncfg); cmaj = np.zeros(ncfg); chour = np.zeros(ncfg)
    Sm = np.zeros((ncfg, nblk)); Sh = np.zeros((ncfg, nblk)); Nb = np.zeros((ncfg, nblk))
    for q in range(Q):
        t = qt[q]
        if t != 1 and t != -1:
            continue
        m = nn[q]
        up = 0; tot = 0
        for r in range(m):
            v = ysg[nbm[q, r]]
            if v != -9:
                tot += 1
                if v == 1:
                    up += 1
            for ik in range(nK):
                K = Ks[ik]
                if (r + 1 == K) or (r == m - 1 and m < K):
                    if tot >= min_vote:
                        vote = up / tot
                        call = 1 if vote > 0.5 else (-1 if vote < 0.5 else 0)
                        if call != 0:
                            _accum(ik * 2, call, t, bmaj[q], bhour[q], blk[q], n, cm, cmaj, chour, Sm, Sh, Nb)
                            if write:
                                calls[q, ik * 2] = call
                            if abs(vote - 0.5) >= strong:
                                _accum(ik * 2 + 1, call, t, bmaj[q], bhour[q], blk[q], n, cm, cmaj, chour, Sm, Sh, Nb)
                                if write:
                                    calls[q, ik * 2 + 1] = call
    acc, am, ah, exc, tst, useh = _finish(n, cm, cmaj, chour, Sm, Sh, Nb)
    return n, acc, am, ah, exc, tst, useh


@nb.njit(cache=True)
def eval_nw(cand, wts, nn, ysg, zz, qt, bmaj, bhour, blk, nblk, nK, strong, min_vote, calls, write):
    """Nadaraya–Watson: R1 = sign(Σw·z/Σw), R2 = ağırlıklı yukarı payı ≥ 0,5 ± strong."""
    Q = cand.shape[0]; ncfg = nK * 2
    n = np.zeros(ncfg); cm = np.zeros(ncfg); cmaj = np.zeros(ncfg); chour = np.zeros(ncfg)
    Sm = np.zeros((ncfg, nblk)); Sh = np.zeros((ncfg, nblk)); Nb = np.zeros((ncfg, nblk))
    for q in range(Q):
        t = qt[q]
        if t != 1 and t != -1:
            continue
        m = nn[q]
        if m < min_vote:
            continue
        for ik in range(nK):
            sw = 0.0; swz = 0.0; swu = 0.0; tot = 0
            for r in range(m):
                j = cand[q, r]
                v = ysg[j]
                if v == -9:
                    continue
                w = wts[q, r, ik]
                tot += 1; sw += w; swz += w * zz[j]
                if v == 1:
                    swu += w
            if tot < min_vote or sw <= 0:
                continue
            est = swz / sw
            call = 1 if est > 0 else (-1 if est < 0 else 0)
            if call != 0:
                _accum(ik * 2, call, t, bmaj[q], bhour[q], blk[q], n, cm, cmaj, chour, Sm, Sh, Nb)
                if write:
                    calls[q, ik * 2] = call
            uf = swu / sw
            if abs(uf - 0.5) >= strong:
                c2 = 1 if uf > 0.5 else -1
                _accum(ik * 2 + 1, c2, t, bmaj[q], bhour[q], blk[q], n, cm, cmaj, chour, Sm, Sh, Nb)
                if write:
                    calls[q, ik * 2 + 1] = c2
    acc, am, ah, exc, tst, useh = _finish(n, cm, cmaj, chour, Sm, Sh, Nb)
    return n, acc, am, ah, exc, tst, useh


# ═══════════════════════════ veri ═══════════════════════════
def load(tf: str) -> pd.DataFrame:
    d = pd.read_parquet(SRC[tf], columns=["ts", "open", "high", "low", "close"])
    d = d[d.ts + pd.Timedelta(minutes=TF_MIN[tf]) < CUTOFF]                       # HOLDOUT kesimi
    d = d.sort_values("ts").drop_duplicates("ts").reset_index(drop=True)
    assert (d.ts + pd.Timedelta(minutes=TF_MIN[tf])).max() < CUTOFF, "holdout ihlali"
    return d


def prep(tf: str) -> dict:
    d = load(tf)
    ts = d.ts.dt.tz_convert("UTC").dt.tz_localize(None).to_numpy().astype("datetime64[ns]").astype(np.int64)
    o, h, l, c = (d[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    n = len(c)
    te = ts + np.int64(TF_MIN[tf]) * MIN_NS
    gap_after = np.r_[np.diff(ts) > SEG_GAP_NS, False]
    seg = np.r_[0, np.cumsum(gap_after)][:n]
    pc = np.r_[c[0], c[:-1]]
    tr = np.maximum(h - l, np.maximum(np.abs(h - pc), np.abs(l - pc)))
    A = pd.Series(tr).rolling(14).mean().shift(1).to_numpy()
    hour = ((te // (3600 * 10**9)) % 24).astype(np.int64)                         # karar (bitiş) saati UTC
    lab = {}
    tol = np.int64(4) * MIN_NS if tf == "1m" else np.int64(0)
    idx = np.arange(n)
    for hz, hm in HZ.items():
        if hm < TF_MIN[tf]:
            continue
        target = te + np.int64(hm) * MIN_NS
        oi = np.searchsorted(te, target, side="right") - 1
        oi = np.clip(oi, 0, n - 1)
        ok = (oi > idx) & (te[oi] >= target - tol) & (seg[oi] == seg) & np.isfinite(A) & (A > 0)
        y = np.where(ok, c[oi] - c, np.nan)
        ysg = np.where(ok, np.sign(np.nan_to_num(y)), -9).astype(np.int8)
        z = np.where(ok, y / np.where(A > 0, A, np.nan), np.nan).astype(np.float32)
        hi0 = np.searchsorted(te + np.int64(hm) * MIN_NS, te, side="right") - 1      # j ≤ hi0 ⇔ te_j + h ≤ te_q
        lab[hz] = dict(ok=ok, y=y, ysg=ysg, z=z, hi0=hi0.astype(np.int64), gap=max(1, hm // TF_MIN[tf]))
    lo = np.searchsorted(ts, ts - LIB_NS, side="left").astype(np.int64)
    return dict(tf=tf, ts=ts, te=te, o=o, h=h, l=l, c=c, n=n, seg=seg, A=A, hour=hour, lab=lab, lo=lo)


def valid_cov(P: dict, cov: int) -> np.ndarray:
    n = P["n"]; e = np.arange(n); s = np.maximum(e - cov - 14, 0)
    return (e >= cov + 14) & (P["seg"][e] == P["seg"][s]) & np.isfinite(P["A"]) & (P["A"] > 0)


def pick_queries(P: dict, hzs: list[str], spacing_min: int) -> np.ndarray:
    tf = P["tf"]; te = P["te"]
    elig = valid_cov(P, max(max(WS) + 1, SIG_WIN + 8, 32)) & (te >= P["ts"][0] + np.int64(WARM_DAYS[tf]) * 86400 * 10**9)
    for hz in hzs:
        L = P["lab"][hz]
        elig &= L["ok"] & (L["ysg"] != 0)
    cand = np.flatnonzero(elig)
    out = []; last = -np.inf; sp = spacing_min * 60 * 10**9
    for i in cand:
        if te[i] >= last + sp:
            out.append(i); last = te[i]
    q = np.array(out, np.int64)
    if SMOKE:
        q = q[:: max(1, len(q) // 150)][:150]
    return q


# ═══════════════════════════ özellikler ═══════════════════════════
def zrows(sw: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    mu = sw.mean(1, keepdims=True); sd = sw.std(1, keepdims=True)
    good = (sd[:, 0] > 1e-12) & np.isfinite(sd[:, 0])
    Z = np.zeros(sw.shape, np.float32)
    Z[good] = ((sw[good] - mu[good]) / sd[good]).astype(np.float32)
    return Z, good


def w_feats(P: dict, W: int) -> dict:
    n, c, h, l, A = P["n"], P["c"], P["h"], P["l"], P["A"]
    Zp = np.zeros((n, W), np.float32); gp = np.zeros(n, bool)
    Z, g = zrows(sliding_window_view(c, W)); Zp[W - 1:] = Z; gp[W - 1:] = g
    lr = np.r_[np.nan, np.diff(np.log(c))]
    Zr = np.zeros((n, W), np.float32); gr = np.zeros(n, bool)
    swr = sliding_window_view(lr, W); fin = np.isfinite(swr).all(1)
    Z, g = zrows(np.where(fin[:, None], swr, 0.0)); Zr[W - 1:] = Z; gr[W - 1:] = g & fin
    dc = np.r_[np.nan, np.diff(c)]
    Xn = np.zeros((n, W), np.float32)
    swd = sliding_window_view(dc, W)
    with np.errstate(invalid="ignore", divide="ignore"):
        X = swd / A[W - 1:, None]
    gx = np.isfinite(X).all(1)
    Xn[W - 1:][gx] = X[gx].astype(np.float32)
    gn = np.zeros(n, bool); gn[W - 1:] = gx
    rng = (pd.Series(h).rolling(W).max() - pd.Series(l).rolling(W).min()).to_numpy()
    valid = valid_cov(P, W + 1) & gp & gr & gn & np.isfinite(rng) & (rng > 0)
    sax = {}
    for a, w in SAX_PATH:
        segs = np.array_split(np.arange(W), w)
        paa = np.stack([Zp[:, s].mean(1) for s in segs], 1)
        bp = norm.ppf(np.arange(1, a) / a)
        sym = np.digitize(paa, bp).astype(np.int64)
        code = (sym * (a ** np.arange(w))[None, :]).sum(1)
        sax[(a, w)] = np.where(valid, code, -1)
    return dict(Zp=Zp, Zr=Zr, Xn=Xn, sqn=(Xn.astype(np.float64) ** 2).sum(1).astype(np.float32),
                rng=np.nan_to_num(rng).astype(np.float64), valid=valid, sax=sax)


def global_feats(P: dict) -> dict:
    n, c, h, l, o, A = P["n"], P["c"], P["h"], P["l"], P["o"], P["A"]
    cols = []
    hs, ls = pd.Series(h), pd.Series(l)
    for s in MS_SPANS:
        cs = np.r_[np.full(s, np.nan), c[s:] - c[:-s]]
        rg = (hs.rolling(s).max() - ls.rolling(s).min()).to_numpy()
        cols += [cs / A / np.sqrt(s), rg / A / np.sqrt(s)]
    M = np.stack(cols, 1)
    vm = valid_cov(P, 33) & np.isfinite(M).all(1)
    M = np.nan_to_num(M).astype(np.float32)
    raw = np.stack([h - o, l - o, c - o], 1)
    R7 = np.full((n, 21), np.nan)
    for k in range(7):
        R7[k:, 3 * k:3 * k + 3] = raw[:n - k] / A[k:, None]
    v7 = valid_cov(P, 7) & np.isfinite(R7).all(1)
    R7 = np.nan_to_num(R7).astype(np.float32)
    lr = np.r_[np.nan, np.diff(np.log(c))]
    sig = pd.Series(lr).rolling(SIG_WIN).std().shift(1).to_numpy()
    with np.errstate(invalid="ignore", divide="ignore"):
        u = lr / sig
    vng = valid_cov(P, SIG_WIN + 9)
    ng = {}
    for a, w in NGRAM:
        bp = norm.ppf(np.arange(1, a) / a)
        sym = np.digitize(np.nan_to_num(u), bp).astype(np.int64)
        fin = np.isfinite(u)
        code = np.zeros(n, np.int64); okw = np.ones(n, bool)
        for k in range(w):
            sk = np.r_[np.zeros(k, np.int64), sym[:n - k]]
            fk = np.r_[np.zeros(k, bool), fin[:n - k]]
            code += sk * a ** k; okw &= fk
        ng[(a, w)] = np.where(vng & okw, code, -1)
    return dict(M=M, sqm=(M.astype(np.float64) ** 2).sum(1).astype(np.float32), vm=vm,
                R7=R7, sq7=(R7.astype(np.float64) ** 2).sum(1).astype(np.float32), v7=v7, ng=ng)


def code_groups(codes: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    order = np.argsort(codes, kind="stable")
    return order.astype(np.int64), codes[order]


# ═══════════════════════════ komşu setleri ═══════════════════════════
class SetStore:
    """sets[hz][key] = dict(kind, nbm|cand, nn, [d2], exact)"""

    def __init__(self, hzs, Q):
        self.hzs, self.Q = hzs, Q
        self.sets = {hz: {} for hz in hzs}

    def knn(self, key):
        for hz in self.hzs:
            if key not in self.sets[hz]:
                self.sets[hz][key] = dict(kind="knn", nbm=np.full((self.Q, KMAX), -1, np.int32),
                                          nn=np.zeros(self.Q, np.int64), exact=np.ones(self.Q, bool))
        return [self.sets[hz][key] for hz in self.hzs]

    def nw(self, key):
        for hz in self.hzs:
            if key not in self.sets[hz]:
                self.sets[hz][key] = dict(kind="nw", cand=np.full((self.Q, NW_CAND), -1, np.int32),
                                          d2=np.full((self.Q, NW_CAND), np.inf, np.float32), nn=np.zeros(self.Q, np.int64))
        return [self.sets[hz][key] for hz in self.hzs]

    def sax(self, key):
        for hz in self.hzs:
            if key not in self.sets[hz]:
                self.sets[hz][key] = dict(kind="sax", nbm=np.full((self.Q, SAX_CAP), -1, np.int32),
                                          nn=np.zeros(self.Q, np.int64))
        return [self.sets[hz][key] for hz in self.hzs]


def knn_fill(dist, lo, hi, mask, L, labs, slots, qi, rng_arr=None, rq=1.0, use_amp=False, kmax=KMAX, keep_d=False):
    """En yakın L adayı → her ufuk için tekilleştir; KMAX'a (NW: KMAX'a) ulaşılamazsa adayı ×8 büyüt (sonra tümü)."""
    ra = rng_arr if rng_arr is not None else np.zeros(1)
    cand, val, tr = top_l(dist, lo, hi, mask, L, ra, rq, use_amp)
    kneed = min(kmax, KMAX)
    for L_, slot in zip(labs, slots):
        pos = dedup_pos(cand, L_["ok"], L_["hi0_q"], L_["gap"], kmax)
        c_sel, v_sel = cand[pos], val[pos]
        L2, tr2 = L, tr
        while len(c_sel) < kneed and tr2:
            L2 = L2 * 8 if L2 < 100_000 else 10**9
            cand2, val2, tr2 = top_l(dist, lo, hi, mask, L2, ra, rq, use_amp)
            pos2 = dedup_pos(cand2, L_["ok"], L_["hi0_q"], L_["gap"], kmax)
            c_sel, v_sel = cand2[pos2], val2[pos2]
        k = len(c_sel)
        if keep_d:
            slot["cand"][qi, :k] = c_sel; slot["d2"][qi, :k] = v_sel
        else:
            slot["nbm"][qi, :k] = c_sel
        slot["nn"][qi] = k


def dtw_fill(P, F, W, q, lo, hi, labs, slots, qi, lbbuf, L0):
    r = max(1, int(round(0.1 * W)))
    qz = F["Zp"][q]
    U, Lw = envelope(qz, r)
    lb_keogh_all(F["Zp"], U, Lw, lo, hi, F["valid"], lbbuf)
    L = L0
    cand, lbv, tr = top_l(lbbuf, lo, hi, F["valid"], L, np.zeros(1), 1.0, False)
    dv = np.empty(len(cand)); dtw_many(F["Zp"], qz, cand, r, dv, 0)
    while True:
        need_more = False
        res = []
        for L_ in labs:
            okm = (cand <= L_["hi0_q"]) & L_["ok"][cand]
            cc, dd = cand[okm], dv[okm]
            o = np.argsort(dd, kind="stable")
            pos = dedup_pos(cc[o], L_["ok"], L_["hi0_q"], L_["gap"], KMAX)
            sel = cc[o][pos]; sd = dd[o][pos]
            exact = (not tr) or (len(sel) == KMAX and sd[-1] <= lbv[-1])
            if tr and not exact:
                need_more = True
            res.append((sel, exact))
        if not need_more or L >= L_DTW_MAX:
            break
        L *= 4
        cand2, lbv2, tr = top_l(lbbuf, lo, hi, F["valid"], L, np.zeros(1), 1.0, False)
        known = dict(zip(cand.tolist(), dv.tolist()))
        dv2 = np.empty(len(cand2))
        new = np.array([c not in known for c in cand2.tolist()], bool)
        for p in np.flatnonzero(~new):
            dv2[p] = known[int(cand2[p])]
        if new.any():
            tmp = np.empty(new.sum()); dtw_many(F["Zp"], qz, cand2[new], r, tmp, 0); dv2[new] = tmp
        cand, lbv, dv = cand2, lbv2, dv2
    for (sel, exact), slot in zip(res, slots):
        k = len(sel); slot["nbm"][qi, :k] = sel; slot["nn"][qi] = k; slot["exact"][qi] = exact


def build_sets(P: dict, Qi: np.ndarray, hzs: list[str]) -> SetStore:
    Q = len(Qi); S = SetStore(hzs, Q)
    labs_all = []
    for hz in hzs:
        L_ = dict(P["lab"][hz]); labs_all.append(L_)
    full = "1d" in hzs
    Ltop = 10**9 if full else L_TOP
    lbbuf = np.full(P["n"], np.inf, np.float32)
    t0 = time.time()
    for W in WS:
        F = w_feats(P, W)
        grp = {k: code_groups(v) for k, v in F["sax"].items()}
        s_z = S.knn(("zED", W, "")); s_a = S.knn(("zED_amp", W, "")); s_r = S.knn(("retcorr", W, ""))
        s_d = S.knn(("DTW", W, "")); s_n = S.nw(("NW", W, ""))
        s_x = {k: S.sax(("SAXyol", W, f"a{k[0]}w{k[1]}")) for k in SAX_PATH}
        for c0 in range(0, Q, CH):
            qs = Qi[c0:c0 + CH]
            Dp = -(F["Zp"][qs] @ F["Zp"].T)
            Dr = -(F["Zr"][qs] @ F["Zr"].T)
            Dn = F["sqn"][None, :] + F["sqn"][qs][:, None] - 2.0 * (F["Xn"][qs] @ F["Xn"].T)
            for ci, q in enumerate(qs):
                qi = c0 + ci; lo = int(P["lo"][q]); hi = int(q - W - 1)
                for L_ in labs_all:
                    L_["hi0_q"] = int(L_["hi0"][q])
                knn_fill(Dp[ci], lo, hi, F["valid"], Ltop, labs_all, s_z, qi)
                knn_fill(Dp[ci], lo, hi, F["valid"], Ltop, labs_all, s_a, qi, F["rng"], float(F["rng"][q]), True)
                knn_fill(Dr[ci], lo, hi, F["valid"], Ltop, labs_all, s_r, qi)
                knn_fill(Dn[ci], lo, hi, F["valid"], Ltop, labs_all, s_n, qi, kmax=NW_CAND, keep_d=True)
                dtw_fill(P, F, W, q, lo, hi, labs_all, s_d, qi, lbbuf, L_DTW * (4 if full else 1))
                for k in SAX_PATH:
                    cq = F["sax"][k][q]
                    if cq < 0:
                        continue
                    order, sc = grp[k]
                    gs, ge = np.searchsorted(sc, cq, "left"), np.searchsorted(sc, cq, "right")
                    g = order[gs:ge]
                    for L_, slot in zip(labs_all, s_x[k]):
                        m = match_recent(g, lo, min(hi, L_["hi0_q"]), L_["ok"], L_["gap"], SAX_CAP)
                        slot["nbm"][qi, :len(m)] = m; slot["nn"][qi] = len(m)
        print(f"  {P['tf']} {hzs} W={W} Q={Q} {time.time() - t0:.0f}s", flush=True)
        del F, Dp, Dr, Dn
    G = global_feats(P)
    grp = {k: code_groups(v) for k, v in G["ng"].items()}
    s_m = S.knn(("cokolcek", 32, "")); s_7 = S.knn(("refR7", 7, ""))
    s_g = {k: S.sax(("ngram", k[1], f"a{k[0]}w{k[1]}")) for k in NGRAM}
    for c0 in range(0, Q, CH):
        qs = Qi[c0:c0 + CH]
        Dm = G["sqm"][None, :] - 2.0 * (G["M"][qs] @ G["M"].T)
        D7 = G["sq7"][None, :] - 2.0 * (G["R7"][qs] @ G["R7"].T)
        for ci, q in enumerate(qs):
            qi = c0 + ci; lo = int(P["lo"][q])
            for L_ in labs_all:
                L_["hi0_q"] = int(L_["hi0"][q])
            knn_fill(Dm[ci], lo, int(q - 33), G["vm"], Ltop, labs_all, s_m, qi)
            knn_fill(D7[ci], lo, int(q - 8), G["v7"], Ltop, labs_all, s_7, qi)
            for k in NGRAM:
                cq = G["ng"][k][q]
                if cq < 0:
                    continue
                order, sc = grp[k]
                gs, ge = np.searchsorted(sc, cq, "left"), np.searchsorted(sc, cq, "right")
                g = order[gs:ge]
                for L_, slot in zip(labs_all, s_g[k]):
                    m = match_recent(g, lo, min(int(q - 9), L_["hi0_q"]), L_["ok"], L_["gap"], SAX_CAP)
                    slot["nbm"][qi, :len(m)] = m; slot["nn"][qi] = len(m)
    print(f"  {P['tf']} {hzs} global {time.time() - t0:.0f}s", flush=True)
    return S


def nw_weights(slot: dict) -> np.ndarray:
    d2 = slot["d2"].astype(np.float64); nn = slot["nn"]; Q = d2.shape[0]
    w = np.zeros((Q, NW_CAND, len(KS)), np.float32)
    for ik, K in enumerate(KS):
        kk = np.clip(np.minimum(K, nn) - 1, 0, NW_CAND - 1)
        h2 = np.maximum(d2[np.arange(Q), kk], 1e-9)
        with np.errstate(invalid="ignore", over="ignore"):
            ww = np.exp(-np.maximum(d2, 0) / (2.0 * h2[:, None]))
        ww[~np.isfinite(d2)] = 0.0
        w[:, :, ik] = ww
    return w


# ═══════════════════════════ değerlendirme ═══════════════════════════
def shift_map(ts: np.ndarray, k: int) -> np.ndarray:
    T0 = ts[0]; span_w = int((ts[-1] - T0) // WEEK_NS); span = np.int64(span_w) * WEEK_NS
    tsh = T0 + ((ts - T0 + np.int64(k) * WEEK_NS) % span)
    m = np.clip(np.searchsorted(ts, tsh), 0, len(ts) - 1)
    return np.where(ts[m] == tsh, m, -1)


def shift_ks(group: str, ts: np.ndarray) -> np.ndarray:
    span_w = int((ts[-1] - ts[0]) // WEEK_NS)
    rng = np.random.default_rng({"duka": 11, "p15": 12, "p1h": 13}[group])
    return rng.integers(2, span_w - 1, size=N_SHIFT)


class Bases:
    def __init__(self, P, Qi, lab):
        self.Qi = Qi; self.lo = P["lo"][Qi]; self.hi0 = lab["hi0"][Qi]
        hour = P["hour"]; self.order = np.argsort(hour, kind="stable"); hs = hour[self.order]
        gstart = np.searchsorted(hs, np.arange(25))
        self.qa = np.empty(len(Qi), np.int64); self.qb = np.empty(len(Qi), np.int64)
        idx_by_h = {b: self.order[gstart[b]:gstart[b + 1]] for b in range(24)}
        for i, q in enumerate(Qi):
            b = hour[q]; g = idx_by_h[b]
            self.qa[i] = gstart[b] + np.searchsorted(g, self.lo[i], "left")
            self.qb[i] = gstart[b] + np.searchsorted(g, self.hi0[i], "right")

    def calls(self, ysg: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        up = np.r_[0, np.cumsum(ysg == 1)]; va = np.r_[0, np.cumsum(ysg != -9)]
        nv = va[self.hi0 + 1] - va[self.lo]
        with np.errstate(invalid="ignore", divide="ignore"):
            p0 = (up[self.hi0 + 1] - up[self.lo]) / nv
        v = ysg[self.order]
        uph = np.r_[0, np.cumsum(v == 1)]; vah = np.r_[0, np.cumsum(v != -9)]
        nvh = vah[self.qb] - vah[self.qa]
        with np.errstate(invalid="ignore", divide="ignore"):
            p0h = (uph[self.qb] - uph[self.qa]) / nvh
        p0h = np.where(nvh > 20, p0h, p0)
        bm = np.where(p0 >= 0.5, 1, -1).astype(np.int8); bh = np.where(p0h >= 0.5, 1, -1).astype(np.int8)
        return bm, bh, p0, p0h


def cfg_names(key, kind):
    fam, W, par = key
    if kind == "sax":
        return [(fam, W, par, 0, "tum"), (fam, W, par, 0, "guclu")]
    return [(fam, W, par, int(K), r) for K in KS for r in ("tum", "guclu")]


def run_eval(P: dict, S: SetStore, hz: str, Qi: np.ndarray, rng: np.random.Generator) -> str:
    tf = P["tf"]; lab = P["lab"][hz]; Q = len(Qi); t0 = time.time()
    te_q = P["te"][Qi]
    bdays = 7 if hz == "1d" else 1
    blk_raw = (te_q // (86400 * 10**9 * bdays)).astype(np.int64)
    _, blk = np.unique(blk_raw, return_inverse=True); blk = blk.astype(np.int64); nblk = int(blk.max()) + 1
    half = (te_q >= np.median(te_q))
    B_ = Bases(P, Qi, lab)
    sets = S.sets[hz]
    keys = list(sets.keys())
    for k in keys:
        if sets[k]["kind"] == "nw":
            sets[k]["w"] = nw_weights(sets[k])
    names = []
    for k in keys:
        names += cfg_names(k, sets[k]["kind"])
    ncfg = len(names)

    def eval_all(ysg, zz, qt, bm, bh, write):
        out = []; calls = []
        for k in keys:
            s = sets[k]
            if s["kind"] == "nw":
                cl = np.zeros((Q, len(KS) * 2), np.int8)
                r = eval_nw(s["cand"], s["w"], s["nn"], ysg, zz, qt, bm, bh, blk, nblk, len(KS), STRONG, MIN_VOTE, cl, write)
            elif s["kind"] == "knn":
                cl = np.zeros((Q, len(KS) * 2), np.int8)
                r = eval_knn(s["nbm"], s["nn"], ysg, qt, bm, bh, blk, nblk, KS, STRONG, MIN_VOTE, cl, write)
            else:
                cl = np.zeros((Q, 2), np.int8)
                r = eval_knn(s["nbm"], s["nn"], ysg, qt, bm, bh, blk, nblk, np.array([SAX_CAP], np.int64), STRONG,
                             MIN_VOTE, cl, write)
            out.append(np.stack(r, 1)); calls.append(cl)
        return np.concatenate(out, 0), (np.concatenate(calls, 1) if write else None)

    # ── gerçek ──
    ysg = lab["ysg"]; zz = lab["z"]
    qt = ysg[Qi]; bm, bh, p0, p0h = B_.calls(ysg)
    real, calls = eval_all(ysg, zz, qt, bm, bh, True)
    ypts = lab["y"][Qi]
    # plasebo (aynı havuzdan rastgele komşu, R_PLC tekrar), kapsam grubuna göre
    covs = {"zED": None, "zED_amp": None, "retcorr": None, "DTW": None, "NW": None, "SAXyol": None}
    def cov_of(key):
        fam, W, par = key
        if fam in covs:
            return W + 1
        return {"cokolcek": 33, "refR7": 8, "ngram": 9}[fam]
    nn_used = []
    for k in keys:
        s = sets[k]; kind = s["kind"]; nn = s["nn"]
        if kind == "sax":
            nn_used += [nn, nn]
        else:
            for K in KS:
                nn_used += [np.minimum(nn, K)] * 2
    cov_per_cfg = []
    for k in keys:
        cov_per_cfg += [cov_of(k)] * (2 if sets[k]["kind"] == "sax" else 2 * len(KS))
    def placebo_table(cov):
        valid = valid_cov(P, cov)
        okidx = np.flatnonzero(lab["ok"] & valid)
        a = np.searchsorted(okidx, P["lo"][Qi], "left")
        b = np.searchsorted(okidx, np.minimum(lab["hi0"][Qi], Qi - cov), "right")
        span = np.maximum(b - a, 0)
        cu = np.zeros((R_PLC, Q, PMAX), np.int16)
        for r in range(R_PLC):
            u = rng.random((Q, PMAX), dtype=np.float32)
            pick = okidx[np.minimum(a[:, None] + (u * span[:, None]).astype(np.int64), len(okidx) - 1)]
            cu[r] = np.cumsum(ysg[pick] == 1, axis=1)
        return cu
    rows = []
    yb_true = (qt == 1)
    M = rng.multinomial(nblk, np.full(nblk, 1.0 / nblk), size=B_BOOT).astype(np.float64)
    for ci, name in enumerate(names):
        n_, acc, am, ah, exc, tst, useh = real[ci]
        cl = calls[:, ci]; called = cl != 0
        row = dict(tf=tf, hz=hz, fam=name[0], W=name[1], par=name[2], K=name[3], rule=name[4], n=int(n_),
                   acc=acc, acc_maj=am, acc_hour=ah, base="saat" if useh else "cogunluk", exc=exc, t=tst)
        if n_ >= 30:
            corr = (cl[called] == qt[called]).astype(float)
            bc = (bh if useh else bm)[called]
            d = corr - (bc == qt[called]).astype(float)
            Sb = np.bincount(blk[called], d, minlength=nblk); Nb_ = np.bincount(blk[called], minlength=nblk).astype(float)
            bmn = (M @ Sb) / np.maximum(M @ Nb_, 1)
            row["P_boot"] = float((bmn > 0).mean())
            h1 = called & ~half; h2 = called & half
            for nm, hm in (("y1", h1), ("y2", h2)):
                if hm.sum() >= 10:
                    c_ = (cl[hm] == qt[hm]).astype(float).mean(); b_ = ((bh if useh else bm)[hm] == qt[hm]).astype(float).mean()
                    row[f"exc_{nm}"] = c_ - b_; row[f"n_{nm}"] = int(hm.sum())
            mv = cl[called] * ypts[called]
            row["mv_pts"] = float(mv.mean()); row["mv_base_pts"] = float(((bh if useh else bm)[called] * ypts[called]).mean())
            row["abs_y_pts"] = float(np.abs(ypts[called]).mean())
            row["n_days"] = int(len(np.unique(te_q[called] // (86400 * 10**9))))
            row["nn_mean"] = float(nn_used[ci][called].mean())
            if name[0] == "DTW":
                row["dtw_exact"] = float(sets[(name[0], name[1], name[2])]["exact"][called].mean())
        rows.append(row)
    for cov in sorted(set(cov_per_cfg)):                     # plasebo: kapsam grubu başına bir tablo (bellek)
        cu = placebo_table(cov)
        for ci in [i for i, cv in enumerate(cov_per_cfg) if cv == cov]:
            cl = calls[:, ci]; called = cl != 0
            if called.sum() < 30:
                continue
            nu = np.clip(nn_used[ci][called], 1, PMAX)
            qq = np.flatnonzero(called)
            vote = cu[:, qq, nu - 1] / nu[None, :]
            pa = np.where(vote == 0.5, 0.5, ((vote > 0.5) == yb_true[qq][None, :]).astype(float)).mean(1)
            rows[ci]["plc_mean"] = float(pa.mean()); rows[ci]["plc_max"] = float(pa.max())
            rows[ci]["plc_beat"] = bool(rows[ci]["acc"] > pa.max())
        del cu
    cfg = pd.DataFrame(rows)
    # ── seçim düzeltmesi: tam hafta kaydırma ──
    ks = shift_ks(SHIFT_GROUP[tf], P["ts"])
    tnull = np.full((N_SHIFT, ncfg), np.nan, np.float32); enull = np.full((N_SHIFT, ncfg), np.nan, np.float32)
    nnull = np.zeros((N_SHIFT, ncfg), np.int32)
    for si, k in enumerate(ks):
        mp = shift_map(P["ts"], int(k))
        ys = np.where(mp >= 0, ysg[np.maximum(mp, 0)], -9).astype(np.int8)
        zs = np.where(mp >= 0, zz[np.maximum(mp, 0)], np.nan).astype(np.float32)
        qts = ys[Qi]; bms, bhs, _, _ = B_.calls(ys)
        res, _ = eval_all(ys, zs, qts, bms, bhs, False)
        nnull[si] = res[:, 0]; enull[si] = res[:, 4]; tnull[si] = res[:, 5]
    OUT.mkdir(parents=True, exist_ok=True)
    tag = f"{tf}_{hz}" + ("_smoke" if SMOKE else "")
    cfg.to_parquet(OUT / f"{tag}_cfg.parquet")
    np.savez_compressed(OUT / f"{tag}_null.npz", t=tnull, e=enull, n=nnull, ks=ks)
    np.savez_compressed(OUT / f"{tag}_q.npz", qi=Qi, te=te_q, y=ypts, qt=qt, bm=bm, bh=bh, p0=p0, p0h=p0h, calls=calls,
                        names=np.array(["|".join(map(str, x)) for x in names]))
    best = cfg[cfg.n >= 200].sort_values("t", ascending=False).head(1)
    bs = best[["fam", "W", "K", "rule", "n", "exc", "t"]].to_dict("records") if len(best) else []
    return f"{tf} {hz}: Q={Q} cfg={ncfg} eval {time.time() - t0:.0f}s en iyi={bs}"


def run_tf(tf: str) -> list[str]:
    msgs = []; t0 = time.time()
    P = prep(tf)
    rng = np.random.default_rng({"1m": 101, "5m": 105, "15m": 115, "1h": 160}[tf])
    hzs = [h for h in HZ if HZ[h] >= TF_MIN[tf]]
    short = [h for h in hzs if h != "1d"]
    for group, sp in ((short, SHORT_SPACING[tf]), (["1d"], DAY_SPACING)):
        Qi = pick_queries(P, group, sp)
        print(f"{tf} {group}: sorgu={len(Qi)} {pd.Timestamp(P['te'][Qi[0]])}→{pd.Timestamp(P['te'][Qi[-1]])}", flush=True)
        S = build_sets(P, Qi, group)
        for hz in group:
            m = run_eval(P, S, hz, Qi, rng); print(m, flush=True); msgs.append(m)
        del S
    msgs.append(f"{tf} toplam {time.time() - t0:.0f}s")
    return msgs


def run_list(tfs: list[str]) -> list[str]:
    out = []
    for tf in tfs:
        out += run_tf(tf)
    return out


def main() -> None:
    only = os.environ.get("ALG_TFS")
    tfs = only.split(",") if only else ["1m", "5m", "15m", "1h"]
    jobs = [[t for t in tfs if t == "1m"], [t for t in tfs if t != "1m"]]
    jobs = [j for j in jobs if j]
    if len(jobs) == 1:
        for m in run_list(jobs[0]):
            print(m, flush=True)
        return
    with ProcessPoolExecutor(max_workers=2) as ex:
        futs = {ex.submit(run_list, j): j for j in jobs}
        for f in as_completed(futs):
            try:
                for m in f.result():
                    print(m, flush=True)
            except Exception as e:  # noqa: BLE001
                import traceback
                print("HATA", futs[f], repr(e), traceback.format_exc(), flush=True)


if __name__ == "__main__":
    main()
