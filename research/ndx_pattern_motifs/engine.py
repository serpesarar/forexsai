"""engine.py — kapanış YOLU (çizgi) düzeyinde şablon eşleştirme yardımcıları.

shape_template.py kullanır. Mum-mum motif taraması seq_engine.py'dedir.

Yol: p_k = 100·(C_k / ort(C) − 1). Şekil modunda aday en küçük kareler ölçeğiyle
(0.1 ≤ a ≤ 10) şablona oturtulur; pay dışında kalan mum sayısı (ihlal) döner.
"""
from __future__ import annotations

import numba as nb
import numpy as np


@nb.njit(parallel=True, fastmath=True, cache=True)
def template_scan(P, T, tol, maxv, shape_mode):
    """Şablona karşı tüm pencereler: ihlal sayısı, RMS, ölçek a, korelasyon.

    shape_mode=0 → mutlak (% yol, ölçek 1); 1 → en küçük kareler ölçeği a>0.
    """
    N, Lw = P.shape
    viol = np.full(N, Lw, np.int32)
    rms = np.full(N, np.inf, np.float32)
    scale = np.zeros(N, np.float32)
    corr = np.zeros(N, np.float32)
    tt = 0.0
    for k in range(Lw):
        tt += T[k] * T[k]
    for i in nb.prange(N):
        pt = 0.0
        pp = 0.0
        for k in range(Lw):
            pt += P[i, k] * T[k]
            pp += P[i, k] * P[i, k]
        if pp <= 0.0:
            continue
        corr[i] = pt / np.sqrt(pp * tt)
        a = 1.0
        if shape_mode == 1:
            a = pt / pp
            if a < 0.1 or a > 10.0:
                continue
        scale[i] = a
        v = 0
        ss = 0.0
        for k in range(Lw):
            x = T[k] - a * P[i, k]
            ss += x * x
            if x > tol or x < -tol:
                v += 1
        viol[i] = v
        rms[i] = np.sqrt(ss / Lw)
    return viol, rms, scale, corr


def greedy_nonoverlap(starts: np.ndarray, cand: np.ndarray, key: np.ndarray,
                      blocked: list[int], excl: int, center: int | None = None) -> list[int]:
    """En iyi skordan başlayarak çakışmasız örnek seç (blocked/merkez ile de çakışmasız)."""
    taken = list(blocked)
    if center is not None:
        taken.append(int(starts[center]))
    taken_arr = np.array(sorted(taken), dtype=np.int64) if taken else np.empty(0, np.int64)
    picked: list[int] = []
    for t in np.argsort(key, kind="stable"):
        j = int(cand[t])
        s = int(starts[j])
        if taken_arr.size:
            pos = np.searchsorted(taken_arr, s)
            lo = taken_arr[pos - 1] if pos > 0 else -10**12
            hi = taken_arr[pos] if pos < taken_arr.size else 10**12
            if s - lo < excl or hi - s < excl:
                continue
        picked.append(j)
        taken_arr = np.insert(taken_arr, np.searchsorted(taken_arr, s), s)
    return picked


def sign_surrogate(close: np.ndarray, seg: np.ndarray, seed: int = 7) -> np.ndarray:
    """Getiri büyüklükleri aynı, işaretleri rastgele → volatilite yapısı korunur,
    yön yapısı (trend/dönüş düzeni) yok edilir. Sıfır hipotezi: 'şekil tesadüf'."""
    rng = np.random.default_rng(seed)
    r = np.diff(np.log(close))
    r[np.diff(seg) != 0] = 0.0
    r = np.abs(r) * rng.choice([-1.0, 1.0], size=r.size)
    return close[0] * np.exp(np.concatenate([[0.0], np.cumsum(r)]))
