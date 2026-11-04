"""Izgara hesaplayıcı: bir giriş kümesi (decider veya plasebo) için tüm geometri hücrelerinin işlem-bazlı
pnl matrislerini üretir. Giriş kümesi kolonları: direction, entry_price, spread_used, path_i0 (1m indeks),
atr_m5, orig_sl_usd, orig_tp_usd, day."""
from __future__ import annotations
import numpy as np
import pandas as pd
import core

SL_ATR = np.round(np.arange(0.5, 3.01, 0.25), 2)
TP_ATR = np.round(np.arange(0.5, 4.01, 0.25), 2)
SL_USD = np.array([2, 3, 4, 5, 6, 8, 10, 12, 15], float)
TP_USD = np.array([1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20], float)
TP_SCALE = np.array([0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0])
SL_SCALE = np.array([0.5, 0.75, 1.0, 1.5, 2.0])
TIME_H = (30, 60, 120, 240)
TIME_SL_ATR = np.array([1.0, 1.5, 2.0, 3.0])
BIG = 1e9


def cells_fixed(tr: pd.DataFrame, P: core.Paths) -> dict[str, np.ndarray]:
    """Dönüş: {aile: pnl[N, ...]} ($/ons) ve {aile+'_risk': risk[N, ...]} (R paydası, $)."""
    N = len(tr)
    out = {k: np.full((N, len(TP_ATR), len(SL_ATR)), np.nan) for k in ("atr",)}
    out["atr_code"] = np.zeros((N, len(TP_ATR), len(SL_ATR)), int)
    out["usd"] = np.full((N, len(TP_USD), len(SL_USD)), np.nan)
    out["scale"] = np.full((N, len(TP_SCALE), len(SL_SCALE)), np.nan)
    out["time_only"] = np.full((N, len(TIME_H)), np.nan)
    out["time_sl"] = np.full((N, len(TIME_H), len(TIME_SL_ATR)), np.nan)
    out["orig_cap"] = np.full((N, len(TIME_H)), np.nan)
    for n, x in enumerate(tr.itertuples(index=False)):
        w = P.window(int(x.path_i0), core.MAX_HOLD_MIN)
        h, l, c = P.h[w], P.l[w], P.c[w]
        a, e, s, dirn = x.atr_m5, x.entry_price, x.spread_used, x.direction
        pnl, code, _ = core.sim_grid(dirn, e, s, h, l, c, TP_ATR * a, SL_ATR * a)
        out["atr"][n], out["atr_code"][n] = pnl, code
        out["usd"][n] = core.sim_grid(dirn, e, s, h, l, c, TP_USD, SL_USD)[0]
        out["scale"][n] = core.sim_grid(dirn, e, s, h, l, c, TP_SCALE * x.orig_tp_usd, SL_SCALE * x.orig_sl_usd)[0]
        t = P.t[w]
        for k, H in enumerate(TIME_H):
            j = max(int(np.searchsorted(t, t[0] + np.timedelta64(H, "m"))), 1)
            _, _, cl = core.fav_adv(dirn, e, s, h[:j], l[:j], c[:j])
            out["time_only"][n, k] = cl[-1]
            out["time_sl"][n, k] = core.sim_grid(dirn, e, s, h[:j], l[:j], c[:j], np.array([BIG]), TIME_SL_ATR * a)[0][0]
            out["orig_cap"][n, k] = core.sim_grid(dirn, e, s, h[:j], l[:j], c[:j], np.array([x.orig_tp_usd]),
                                                  np.array([x.orig_sl_usd]))[0][0, 0]
    return out


def risk_arrays(tr: pd.DataFrame) -> dict[str, np.ndarray]:
    a = tr.atr_m5.values[:, None, None]
    return {"atr": np.broadcast_to(SL_ATR[None, None, :] * a, (len(tr), len(TP_ATR), len(SL_ATR))),
            "usd": np.broadcast_to(SL_USD[None, None, :], (len(tr), len(TP_USD), len(SL_USD))).astype(float),
            "scale": SL_SCALE[None, None, :] * tr.orig_sl_usd.values[:, None, None],
            "time_only": np.broadcast_to(tr.atr_m5.values[:, None], (len(tr), len(TIME_H))),   # R = 1×ATR5
            "time_sl": np.broadcast_to(TIME_SL_ATR[None, None, :] * a, (len(tr), len(TIME_H), len(TIME_SL_ATR))),
            "orig_cap": np.broadcast_to(tr.orig_sl_usd.values[:, None], (len(tr), len(TIME_H)))}


def day_boot(vals: np.ndarray, days: np.ndarray, B: int = 2000, seed: int = 7) -> np.ndarray:
    """Gün-kümeli bootstrap: vals[N, ...] → ortalama dağılımı [B, ...]. Aynı gün işlemleri birlikte örneklenir."""
    rng = np.random.default_rng(seed)
    u, inv = np.unique(days, return_inverse=True)
    flat = vals.reshape(len(vals), -1)
    S = np.zeros((len(u), flat.shape[1])); C = np.bincount(inv, minlength=len(u)).astype(float)
    np.add.at(S, inv, flat)
    W = rng.multinomial(len(u), np.ones(len(u)) / len(u), size=B).astype(float)
    m = (W @ S) / (W @ C)[:, None]
    return m.reshape((B,) + vals.shape[1:])


def summarize(pnl: np.ndarray, risk: np.ndarray, days: np.ndarray, B: int = 2000) -> dict[str, np.ndarray]:
    R = pnl / risk
    bR = day_boot(R, days, B)
    bU = day_boot(pnl, days, B)
    return {"n": np.full(pnl.shape[1:], len(pnl)), "WR": (pnl > 0).mean(0), "EV_R": R.mean(0),
            "EV_usd": pnl.mean(0), "R_lo": np.percentile(bR, 2.5, 0), "R_hi": np.percentile(bR, 97.5, 0),
            "P_R_gt0": (bR > 0).mean(0), "usd_lo": np.percentile(bU, 2.5, 0), "usd_hi": np.percentile(bU, 97.5, 0),
            "P_usd_gt0": (bU > 0).mean(0), "se_R": R.std(0, ddof=1) / np.sqrt(len(R))}
