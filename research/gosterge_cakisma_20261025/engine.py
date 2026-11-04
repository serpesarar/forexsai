"""Tetik/durum matrisleri, etiketler ve kombinasyon madenciliği (PROTOCOL §3–§7)."""
from __future__ import annotations

import numpy as np
import pandas as pd

import config as C

W_NAMES = ("n", "e", "ee", "up", "dn", "pu", "pd", "r")   # her bölme için toplanan ağırlıklar
CHUNK = 20000


# ── matrisler ────────────────────────────────────────────────────────────────
def matrices(book):
    names = sorted(book.states)
    Sm = np.column_stack([book.states[k] for k in names])
    prev = np.vstack([np.zeros((1, Sm.shape[1]), bool), Sm[:-1]])
    T = Sm & ~prev                                   # tetik = durumun başladığı bar
    Rm = T.copy()
    for k in range(1, C.RECENT_W):                   # yakın tetik: son w bar içinde
        Rm[k:] |= T[:-k]
    ind = np.array([book.meta[k][0] for k in names])
    return names, Sm, T, Rm, ind


def thin(T: np.ndarray, h: int) -> np.ndarray:
    """Her tetik sütunu ateşledikten sonra h bar susar (E6/E9)."""
    if h <= 1:
        return T
    out = np.zeros_like(T)
    for j in range(T.shape[1]):
        idx = np.flatnonzero(T[:, j])
        keep, last = [], -10 ** 9
        for i in idx:
            if i - last >= h:
                keep.append(i)
                last = i
        out[keep, j] = True
    return out


# ── etiketler ────────────────────────────────────────────────────────────────
def labels(d: pd.DataFrame, bucket: np.ndarray, h: int, cost_px: float):
    o, c, seg, sp = d.open.values, d.close.values, d.seg.values, d.split.values
    n = len(d)
    r = np.full(n, np.nan)
    i = np.arange(n - h)
    same = (seg[i + h] == seg[i]) & (seg[i + 1] == seg[i])
    r[i[same]] = np.log(c[i[same] + h] / o[i[same] + 1])
    valid = ~np.isnan(r) & (r != 0)
    pu, pdn, mu = np.zeros(n), np.zeros(n), np.zeros(n)
    for s in range(3):
        for b in np.unique(bucket):
            m = (sp == s) & (bucket == b)
            mv = m & valid
            if mv.sum() == 0:
                continue
            pu[m] = (r[mv] > 0).mean()
            pdn[m] = (r[mv] < 0).mean()
            mu[m] = r[mv].mean()
    e = np.where(valid, r - mu, 0.0)
    cost = np.array([cost_px / np.median(c[sp == s]) for s in range(3)])
    return dict(r=np.where(valid, r, 0.0), e=e, valid=valid, pu=pu, pd=pdn, split=sp, cost=cost)


def weights(L) -> np.ndarray:
    """n × (3 bölme × 8 ağırlık) — geçersiz etiketli satırlar sıfır."""
    v = L["valid"].astype(np.float64)
    base = [v, L["e"] * v, L["e"] ** 2 * v, (L["r"] > 0) * v, (L["r"] < 0) * v, L["pu"] * v, L["pd"] * v, L["r"] * v]
    cols = []
    for s in range(3):
        m = (L["split"] == s).astype(np.float64)
        cols += [w * m for w in base]
    return np.column_stack(cols)


def x_matrix(Sm, Rm) -> np.ndarray:
    return np.hstack([np.ones((Sm.shape[0], 1), bool), Sm, Rm])


def pair_sums(Th: np.ndarray, X: np.ndarray, W: np.ndarray) -> np.ndarray:
    """A[i, k, j] = Σ_t Th[t,i]·W[t,k]·X[t,j]  (bloklu matris çarpımı)."""
    nt, nk, nx = Th.shape[1], W.shape[1], X.shape[1]
    A = np.zeros((nt * nk, nx), np.float64)
    for a in range(0, Th.shape[0], CHUNK):
        b = a + CHUNK
        tw = (Th[a:b, :, None] * W[a:b, None, :].astype(np.float32)).reshape(-1, nt * nk)
        A += (tw.T @ X[a:b].astype(np.float32)).astype(np.float64)
    return A.reshape(nt, nk, nx)


# ── istatistikler ────────────────────────────────────────────────────────────
def split_stats(A: np.ndarray, s: int) -> dict:
    """A[..., (s*8 + k), ...] → n, z, ort. artık, hit/base sayıları."""
    g = {w: A[..., s * 8 + k] for k, w in enumerate(W_NAMES)}
    n = g["n"]
    with np.errstate(divide="ignore", invalid="ignore"):
        mean = g["e"] / n
        var = np.maximum(g["ee"] / n - mean ** 2, 1e-18)
        z = mean / np.sqrt(var / n)
    z = np.where(n >= 2, np.nan_to_num(z), 0.0)       # n<2'de varyans tabanı z'yi patlatır (EK-4)
    g["mean"], g["z"] = mean, z
    return g


def directional(g: dict, d: np.ndarray, cost: float) -> dict:
    n = np.maximum(g["n"], 1)
    hit = np.where(d > 0, g["up"], g["dn"]) / n
    base = np.where(d > 0, g["pu"], g["pd"]) / n
    ret = d * g["r"] / n
    return dict(n=g["n"], z=d * g["z"], hit=hit, base=base, lift=hit - base, ret_bp=ret * 1e4, cost_bp=cost * 1e4)


def _absz(n, se, see):
    with np.errstate(divide="ignore", invalid="ignore"):
        mean = se / n
        return np.abs(np.nan_to_num(mean / np.sqrt(np.maximum(see / n - mean ** 2, 1e-18) / n)))


def null_threshold(Th, X, L, excl, n_min, rng, ind) -> tuple[float, list]:
    """KEŞİF içinde etiket dairesel kaydırma → aramanın TAMAMININ (L1+L2+L3) max|z| dağılımı (E24/E48)."""
    disc = np.flatnonzero(L["split"] == 0)
    nd = len(disc)
    v, e = L["valid"][disc].astype(np.float64), L["e"][disc]
    Td, Xd = Th[disc], X[disc]
    ind_x = np.array([""] + list(ind) + list(ind), dtype=object)
    maxes = []
    for _ in range(C.NULL_SHIFTS):
        off = int(rng.integers(int(nd * C.NULL_MIN_OFFSET), nd - int(nd * C.NULL_MIN_OFFSET)))
        vs, es = np.roll(v, off), np.roll(e, off)
        W = np.column_stack([vs, es * vs, es ** 2 * vs])
        A = pair_sums(Td, Xd, W)
        z = _absz(A[:, 0], A[:, 1], A[:, 2])
        z[(A[:, 0] < n_min) | excl] = 0
        best = float(z.max())
        z2 = z.copy()
        z2[:, 0] = 0
        for flat in np.argsort(-z2, axis=None)[: C.L3_EXPAND]:
            i, j = np.unravel_index(flat, z2.shape)
            idx = np.flatnonzero(Td[:, i] & Xd[:, j])
            if len(idx) == 0:
                continue
            A3 = W[idx].T @ Xd[idx].astype(np.float64)
            z3 = _absz(A3[0], A3[1], A3[2])
            bad = (np.arange(len(ind_x)) == 0) | (ind_x == ind[i]) | (ind_x == ind_x[j]) | (A3[0] < n_min)
            best = max(best, float(np.where(bad, 0, z3).max()))
        maxes.append(best)
    if not maxes or max(maxes) == 0:
        return float("nan"), maxes                 # havuz boş → hücre ölçülemez
    return float(np.quantile(maxes, 0.95)), maxes
