"""fam_ml etiket motoru (feasibility/lib.py'deki seyrek tablo + ikili sıçrama yönteminin kopyası; oraya dokunulmaz).

Giriş barı e = m+1, fiyat open[e]. Pencere [e, e+H). Aynı barda TP+SL → SL. SL dolumu boşluk-duyarlı.
"""
from __future__ import annotations

import numpy as np

KLEV = 7  # 2^6 = 64; toplam 127 ≥ 60


def sparse_tables(high: np.ndarray, low: np.ndarray, klev: int = KLEV):
    h = np.where(np.isnan(high), -np.inf, high)
    l = np.where(np.isnan(low), np.inf, low)
    n = len(h)
    MX = np.empty((klev, n))
    MN = np.empty((klev, n))
    MX[0], MN[0] = h, l
    for k in range(1, klev):
        s = 1 << (k - 1)
        MX[k] = MX[k - 1]
        MN[k] = MN[k - 1]
        MX[k, :n - s] = np.maximum(MX[k - 1, :n - s], MX[k - 1, s:])
        MN[k, :n - s] = np.minimum(MN[k - 1, :n - s], MN[k - 1, s:])
    return MX, MN


def first_hit(T: np.ndarray, e: np.ndarray, thr: np.ndarray, L: int, up: bool) -> np.ndarray:
    n = T.shape[1]
    pos = e.copy()
    end = np.minimum(e + L, n)
    for k in range(T.shape[0] - 1, -1, -1):
        step = 1 << k
        ok = pos + step <= end
        idx = np.where(ok, pos, 0)
        v = T[k][idx]
        nohit = (v < thr) if up else (v > thr)
        pos = np.where(ok & nohit, pos + step, pos)
    k_rel = pos - e
    inside = pos < end
    k_rel[~inside] = L
    return k_rel.astype(np.int32)


def simulate(o, h, l, c, MX, MN, e, p0, s_frac, tp_mult, H, direction, gap_aware=True):
    """Bir hücre için sonuç. Döner dict: gross_bp, exit_type (0 TP, 1 SL, 2 zaman), k_exit, samebar."""
    tp_frac = s_frac * tp_mult
    if direction == 1:
        tp_lvl, sl_lvl = p0 * (1 + tp_frac), p0 * (1 - s_frac)
        k_tp = first_hit(MX, e, tp_lvl, H, True)
        k_sl = first_hit(MN, e, sl_lvl, H, False)
    else:
        tp_lvl, sl_lvl = p0 * (1 - tp_frac), p0 * (1 + s_frac)
        k_tp = first_hit(MN, e, tp_lvl, H, False)
        k_sl = first_hit(MX, e, sl_lvl, H, True)
    is_sl = (k_sl < H) & (k_sl <= k_tp)
    is_tp = (k_tp < H) & ~is_sl
    samebar = (k_sl < H) & (k_sl == k_tp)
    k_exit = np.where(is_sl, k_sl, np.where(is_tp, k_tp, H - 1))
    idx = e + k_exit
    if gap_aware:
        ohit = o[idx]
        sl_fill = np.minimum(sl_lvl, ohit) if direction == 1 else np.maximum(sl_lvl, ohit)
        sl_fill = np.where(np.isnan(sl_fill), sl_lvl, sl_fill)
    else:
        sl_fill = sl_lvl
    px = np.where(is_sl, sl_fill, np.where(is_tp, tp_lvl, c[idx]))
    gross = direction * (px / p0 - 1) * 1e4
    et = np.where(is_tp, 0, np.where(is_sl, 1, 2)).astype(np.int8)
    return {"gross_bp": gross.astype(np.float32), "exit_type": et, "k_exit": k_exit.astype(np.int16),
            "samebar": samebar}


def simulate_loop(o, h, l, c, ei, p0, s_frac, tp_mult, H, direction):
    """Basit döngü referansı (öz-sınama T4)."""
    tp_frac = s_frac * tp_mult
    if direction == 1:
        tp_lvl, sl_lvl = p0 * (1 + tp_frac), p0 * (1 - s_frac)
    else:
        tp_lvl, sl_lvl = p0 * (1 - tp_frac), p0 * (1 + s_frac)
    for k in range(H):
        j = ei + k
        if direction == 1:
            hit_sl, hit_tp = l[j] <= sl_lvl, h[j] >= tp_lvl
        else:
            hit_sl, hit_tp = h[j] >= sl_lvl, l[j] <= tp_lvl
        if hit_sl:
            f = min(sl_lvl, o[j]) if direction == 1 else max(sl_lvl, o[j])
            return direction * (f / p0 - 1) * 1e4, 1, k
        if hit_tp:
            return direction * (tp_lvl / p0 - 1) * 1e4, 0, k
    return direction * (c[ei + H - 1] / p0 - 1) * 1e4, 2, H - 1
