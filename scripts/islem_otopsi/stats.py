"""Saf numpy istatistik (kutuda scipy yok; burada da bağımlılık eklemiyoruz)."""
from __future__ import annotations

import numpy as np

from . import settings as S

Z95 = 1.959964


def ranks(x: np.ndarray) -> np.ndarray:
    """Ortalama-bağ sıralaması (1 tabanlı)."""
    order = np.argsort(x, kind="mergesort")
    r = np.empty(x.size, dtype=float)
    r[order] = np.arange(1, x.size + 1)
    sx = x[order]
    i = 0
    while i < sx.size:
        j = i
        while j + 1 < sx.size and sx[j + 1] == sx[i]:
            j += 1
        if j > i:
            r[order[i:j + 1]] = (i + j + 2) / 2.0
        i = j + 1
    return r


def auc(x_pos: np.ndarray, x_neg: np.ndarray) -> float:
    """P(pos > neg) + ½·P(eşit) — Mann-Whitney U / (n₁n₀)."""
    x_pos, x_neg = x_pos[np.isfinite(x_pos)], x_neg[np.isfinite(x_neg)]
    if not x_pos.size or not x_neg.size:
        return np.nan
    r = ranks(np.concatenate([x_pos, x_neg]))
    n1 = x_pos.size
    return float((r[:n1].sum() - n1 * (n1 + 1) / 2) / (n1 * x_neg.size))


def auc_perm(x_pos: np.ndarray, x_neg: np.ndarray, n_perm: int = S.PERMUTATIONS,
             seed: int = S.RNG_SEED) -> tuple[float, float]:
    """AUC ve iki yönlü permütasyon p-değeri (etiketler karıştırılır)."""
    x_pos, x_neg = x_pos[np.isfinite(x_pos)], x_neg[np.isfinite(x_neg)]
    n1, n0 = x_pos.size, x_neg.size
    if n1 < 2 or n0 < 2:
        return np.nan, np.nan
    r = ranks(np.concatenate([x_pos, x_neg]))
    base = n1 * (n1 + 1) / 2
    obs = (r[:n1].sum() - base) / (n1 * n0)
    rng = np.random.default_rng(seed)
    perm = np.argsort(rng.random((n_perm, n1 + n0)), axis=1)[:, :n1]
    null = (r[perm].sum(axis=1) - base) / (n1 * n0)
    p = (np.sum(np.abs(null - 0.5) >= abs(obs - 0.5) - 1e-12) + 1) / (n_perm + 1)
    return float(obs), float(p)


def bh_q(p: np.ndarray) -> np.ndarray:
    """Benjamini–Hochberg q-değerleri (NaN korunur)."""
    p = np.asarray(p, dtype=float)
    q = np.full(p.shape, np.nan)
    ok = np.isfinite(p)
    m = ok.sum()
    if not m:
        return q
    pv = p[ok]
    order = np.argsort(pv)
    adj = pv[order] * m / np.arange(1, m + 1)
    adj = np.minimum.accumulate(adj[::-1])[::-1]
    out = np.empty(m)
    out[order] = np.minimum(adj, 1.0)
    q[ok] = out
    return q


def wilson(k: int, n: int) -> tuple[float, float]:
    if n == 0:
        return np.nan, np.nan
    ph = k / n
    den = 1 + Z95 ** 2 / n
    mid = (ph + Z95 ** 2 / (2 * n)) / den
    half = Z95 * np.sqrt(ph * (1 - ph) / n + Z95 ** 2 / (4 * n * n)) / den
    return float(mid - half), float(mid + half)


def boot_mean_ci(x: np.ndarray, n_boot: int = S.PERMUTATIONS, seed: int = S.RNG_SEED) -> tuple[float, float, float]:
    """Ortalama, %95 bootstrap aralığı ve P(ortalama > 0)."""
    x = x[np.isfinite(x)]
    if x.size < 3:
        return np.nan, np.nan, np.nan
    rng = np.random.default_rng(seed)
    means = x[rng.integers(0, x.size, (n_boot, x.size))].mean(axis=1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5)), float((means > 0).mean())
