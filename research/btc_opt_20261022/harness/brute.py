"""Kaba-döngü (bar bar) referans çözücü — exits.ExitEngine'in bağımsız doğrulaması için.

Aynı belgelenmiş konvansiyonlar, tek olay × tek spec, saf Python döngüsü (yavaş; yalnız sınama).
"""
from __future__ import annotations

import math

import numpy as np

import config as K
from exits import MAX_HOLD_MIN, ExitSpec, _isnan

BIGT = 2 ** 62


def brute_one(P, RO, row: dict, s: ExitSpec, mode: str = "base", slip: bool | None = None):
    """row: ts_dec, dir, price_dec, atr_*, sl_orig, end_orig, end_opp. Dönüş (R, bp, ext) veya (nan, nan, nan)."""
    if slip is None:
        slip = mode != "opt"
    nanr = (math.nan, math.nan, math.nan)
    T, O, H, L, C = P.T, P.O, P.H, P.L, P.C
    ts, d = int(row["ts_dec"]), int(row["dir"])
    k = int(np.searchsorted(T, ts))
    if k >= P.N or T[k] - ts > K.MAX_DELAY:
        return nanr
    o0 = O[k]
    if mode == "opt":
        h, E = 0.0, float(row["price_dec"])
    else:
        h = K.SPREAD_ABS / 2 if mode == "abs" else o0 * K.SPREAD[mode] / 2
        E = o0 + d * h
    # SL mesafesi
    if s.sl_kind == "atr":
        sl = s.sl_mult * row[f"atr_{s.sl_tf}"]
        if s.sl_floor_bp:
            sl = max(sl, s.sl_floor_bp * 1e-4 * o0)
    elif s.sl_kind == "bp":
        sl = s.sl_bp * 1e-4 * o0
    else:
        sl = row["sl_orig"]
    if not (sl == sl and sl > 0):
        return nanr
    # bitiş
    nro = RO[np.searchsorted(RO, ts, side="right")]
    end = BIGT
    if s.time_min > 0:
        end = min(end, ts + s.time_min)
    if s.struct == "day":
        end = min(end, (ts // 1440 + 1) * 1440)
    elif s.struct == "ro":
        end = min(end, nro - 2)
    elif s.struct == "opp" and row.get("end_opp") == row.get("end_opp") and row.get("end_opp") is not None:
        end = min(end, int(row["end_opp"]))
    elif s.struct == "orig" and row.get("end_orig") == row.get("end_orig") and row.get("end_orig") is not None:
        end = min(end, int(row["end_orig"]))
    if s.force_ro:
        end = min(end, nro - 2)
    end = min(end, ts + MAX_HOLD_MIN)
    if end > T[-1] + 1:
        return nanr
    e1 = int(np.searchsorted(T, end)) - 1
    if e1 < k:
        return nanr
    SL0 = E - d * sl
    tp = s.tp_rr
    if _isnan(tp):
        TP = None
    elif tp == -1:
        TP = E + d * row["tp_orig"] if row.get("tp_orig") == row.get("tp_orig") and row.get("tp_orig") is not None else None
    else:
        TP = E + d * tp * sl
    kind = s.kind

    def adv_hit(j, lev):
        return (L[j] - h <= lev) if d == 1 else (H[j] + h >= lev)

    def fav_hit(j, lev):
        return (H[j] - h >= lev) if d == 1 else (L[j] + h <= lev)

    def fill(j, lev):
        g = min(lev, O[j] - h) if d == 1 else max(lev, O[j] + h)
        if slip:
            sp = (K.SLIP_HOT_BP if P.hot[j] else K.SLIP_BP) * 1e-4 * lev
            g -= d * sp
        return g

    legs = []  # (frac, price, exit_time)
    if kind == "bracket":
        for j in range(k, e1 + 1):
            if adv_hit(j, SL0):
                legs = [(1.0, fill(j, SL0), T[j] + 0.5)]
                break
            if TP is not None and fav_hit(j, TP):
                legs = [(1.0, TP, T[j] + 0.5)]
                break
    elif kind == "be":
        act_lev = E + d * s.be_R * sl
        active = False
        for j in range(k, e1 + 1):
            stop = E if active else SL0
            if adv_hit(j, stop):
                legs = [(1.0, fill(j, stop), T[j] + 0.5)]
                break
            if TP is not None and fav_hit(j, TP):
                legs = [(1.0, TP, T[j] + 0.5)]
                break
            if not active and fav_hit(j, act_lev):
                active = True
    elif kind == "partial":
        f, TP1 = s.part_frac, E + d * s.part_rr1 * sl
        stage = 0
        rstop = E if s.part_be else SL0
        for j in range(k, e1 + 1):
            if stage == 0:
                if adv_hit(j, SL0):
                    legs = [(1.0, fill(j, SL0), T[j] + 0.5)]
                    break
                if fav_hit(j, TP1):
                    legs = [(f, TP1, T[j] + 0.5)]
                    stage = 1
                    if TP is not None and fav_hit(j, TP):
                        legs.append((1 - f, TP, T[j] + 0.5))
                        stage = 2
                        break
                continue
            if adv_hit(j, rstop):
                legs.append((1 - f, fill(j, rstop), T[j] + 0.5))
                stage = 2
                break
            if TP is not None and fav_hit(j, TP):
                legs.append((1 - f, TP, T[j] + 0.5))
                stage = 2
                break
        if stage == 1:
            legs.append((1 - f, C[e1] - d * h, T[e1] + 1.0))
    else:  # trail
        A = s.trail_k * row[f"atr_{s.trail_tf}"]
        if not (A == A):
            return nanr
        act = s.trail_act_R
        always = _isnan(act) or act <= 0
        peak = (O[k] - h) if d == 1 else (O[k] + h)
        for j in range(k, e1 + 1):
            mfe = (peak - E) if d == 1 else (E - peak)
            if always or mfe >= act * sl:
                stop = max(SL0, peak - A) if d == 1 else min(SL0, peak + A)
            else:
                stop = SL0
            if adv_hit(j, stop):
                legs = [(1.0, fill(j, stop), T[j] + 0.5)]
                break
            if TP is not None and fav_hit(j, TP):
                legs = [(1.0, TP, T[j] + 0.5)]
                break
            peak = max(peak, H[j] - h) if d == 1 else min(peak, L[j] + h)
    if not legs or sum(x[0] for x in legs) < 1 - 1e-12:
        if not legs:
            legs = [(1.0, C[e1] - d * h, T[e1] + 1.0)]
    et = T[k]
    rate = (K.SWAP_LONG if d == 1 else K.SWAP_SHORT) * E
    pnl = 0.0
    for fr, px, xt in legs:
        nights = np.searchsorted(RO, xt, "left") - np.searchsorted(RO, et, "right")
        pnl += fr * (d * (px - E) + nights * rate)
    ext = legs[-1][2]
    if P.excl is not None and et < P.excl[1] and ext > P.excl[0]:
        return nanr
    return pnl / sl, pnl / E * 1e4, ext
