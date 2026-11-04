"""fam_ml ortak ML yardımcıları."""
from __future__ import annotations

import json
import os

import lightgbm as lgb
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
CELLS = [f"{d}_tp{tp:g}_h{H}" for d in ("L", "S") for tp in (1.0, 1.5) for H in (30, 60)]
UTC = "UTC"
DISC = (pd.Timestamp("2021-06-01", tz=UTC), pd.Timestamp("2024-01-01", tz=UTC))
GAP = (pd.Timestamp("2024-01-01", tz=UTC), pd.Timestamp("2024-01-11", tz=UTC))
OOS = (pd.Timestamp("2024-01-11", tz=UTC), pd.Timestamp("2025-07-01", tz=UTC))
BLIND = (pd.Timestamp("2025-07-01", tz=UTC), pd.Timestamp("2026-10-21", tz=UTC))
VAL_START = pd.Timestamp("2022-03-01", tz=UTC)
DAYNS = 86400 * 10**9
CONFIGS = {
    "C1": dict(num_leaves=15, min_data_in_leaf=1000, n_estimators=300, learning_rate=0.03),
    "C2": dict(num_leaves=31, min_data_in_leaf=500, n_estimators=300, learning_rate=0.03),
    "C3": dict(num_leaves=63, min_data_in_leaf=2000, n_estimators=500, learning_rate=0.03),
    "C4": dict(num_leaves=15, min_data_in_leaf=3000, n_estimators=800, learning_rate=0.02),
}
KS = [0.01, 0.02, 0.05, 0.10]
COST = {"PEP": 1.85, "PEP_STRESS": 2.775, "BIN_MAKER": 4.0, "BIN_TAKER": 10.0}
SLIP = 1.0


def load_ds() -> tuple[pd.DataFrame, list, dict]:
    ds = pd.read_parquet(f"{HERE}/cache/dataset.parquet")
    groups = json.load(open(f"{HERE}/cache/feature_groups.json"))
    feats = [f for g in ("PRICE", "FLOW", "DERIV", "DEPTH", "CAL") for f in groups[g]]
    feats = [f if f != "s_bp" else "s_bp" for f in feats]
    ds["tsn"] = ds["ts_dec"].astype("int64")
    return ds, feats, groups


def in_period(ds: pd.DataFrame, p) -> np.ndarray:
    return ((ds["ts_dec"] >= p[0]) & (ds["ts_dec"] < p[1])).to_numpy()


def cell_parts(cell: str):
    d, tp, h = cell.split("_")
    return (1 if d == "L" else -1), float(tp[2:]), int(h[1:])


def net_r(ds: pd.DataFrame, cell: str, cost: str | float = "PEP", optimistic: bool = False) -> np.ndarray:
    s = ds["s_bp"].to_numpy(np.float64)
    if optimistic:
        return ds[f"{cell}_optgross"].to_numpy(np.float64) / s
    g = ds[f"{cell}_gross"].to_numpy(np.float64)
    sl = (ds[f"{cell}_et"].to_numpy() == 1).astype(float)
    if cost == "FIX15":
        c = 15.0 / ds["p0"].to_numpy(np.float64) * 1e4
    elif isinstance(cost, str):
        c = COST[cost]
    else:
        c = float(cost)
    return (g - c - SLIP * sl) / s


def fit(X: pd.DataFrame, y: np.ndarray, cfg: dict, seed: int = 7) -> lgb.LGBMRegressor:
    mdl = lgb.LGBMRegressor(objective="regression", subsample=0.7, subsample_freq=1, colsample_bytree=0.7,
                            reg_lambda=10.0, random_state=seed, n_jobs=8, verbose=-1, **cfg)
    mdl.fit(X, y)
    return mdl


def rolling_thresholds(tsn: np.ndarray, pred: np.ndarray, hist_mask: np.ndarray, ks=KS,
                       window_days: int = 30, warm_days: int = 7) -> np.ndarray:
    """Her satır için eşik (len(ks) × n): saatlik yenilenen, son 30 günün (hist_mask) tahminlerinin üst k nicelikleri.
    Geçmiş < warm_days ise +inf (işlem yok). tsn sıralı varsayılır.
    """
    n = len(tsn)
    out = np.full((len(ks), n), np.inf)
    hts, hp = tsn[hist_mask], pred[hist_mask]
    if len(hts) == 0:
        return out
    first = hts[0]
    hour = tsn // (3600 * 10**9)
    uh, start = np.unique(hour, return_index=True)
    bounds = np.append(start, n)
    qs = [1 - k for k in ks]
    for j, hh in enumerate(uh):
        t = hh * 3600 * 10**9
        if t - first < warm_days * DAYNS:
            continue
        a = np.searchsorted(hts, t - window_days * DAYNS, "left")
        b = np.searchsorted(hts, t, "left")
        if b - a < 100:
            continue
        thr = np.quantile(hp[a:b], qs)
        out[:, bounds[j]:bounds[j + 1]] = thr[:, None]
    return out
