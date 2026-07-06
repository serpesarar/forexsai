"""CORTEX confluence discovery — honest multi-timeframe pattern search.

Hypothesis (user): before NASDAQ moves up/down there is a *confluence* of
indicators. We test it rigorously on NQ futures, controlling every failure mode
that produced false edges before:

  * FEATURES: computed by us from raw NQ 5m (resampled M30/H1/H4), strictly
    causal — no repaint, no future bars, no borrowed 3500-col feature soup.
  * LABEL: forward NQ direction (+6h / +24h) from the leak-audited backfill.
  * SPLIT: chronological. Train <= 2022, TEST 2023-2024 untouched.
  * MODEL: LightGBM, heavily regularized (trees capture confluence/conjunctions).
  * PLACEBO: shuffled-label run must score ~0.5 AUC → proves the pipeline isn't
    leaking. A real edge = test AUC clearly > 0.5 while placebo ~ 0.5.

Verdict is reported either way. "No edge" is an acceptable, likely outcome.
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
from services.cortex_backfill import (  # noqa: E402
    load_nq_5m, solve_monthly_offsets, nq_to_et, load_sources, build_all, DECISION_TIMES,
)

TRAIN_END = "2022-12-31"


# ── Causal indicators (past-only) ─────────────────────────────────────────────
def _rsi(close: pd.Series, n: int = 14) -> pd.Series:
    d = close.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    rs = up / dn.replace(0, np.nan)
    return 100 - 100 / (1 + rs)


def _adx(h, l, c, n: int = 14) -> pd.Series:
    up = h.diff(); dn = -l.diff()
    plus = np.where((up > dn) & (up > 0), up, 0.0)
    minus = np.where((dn > up) & (dn > 0), dn, 0.0)
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1 / n, adjust=False).mean()
    pdi = 100 * pd.Series(plus, index=h.index).ewm(alpha=1 / n, adjust=False).mean() / atr
    mdi = 100 * pd.Series(minus, index=h.index).ewm(alpha=1 / n, adjust=False).mean() / atr
    dx = 100 * (pdi - mdi).abs() / (pdi + mdi).replace(0, np.nan)
    return dx.ewm(alpha=1 / n, adjust=False).mean()


def tf_features(bars: pd.DataFrame, tf: str) -> pd.DataFrame:
    """Causal indicator panel for one timeframe. Every value at row t uses only
    bars <= t."""
    c, h, l, v = bars["Close"], bars["High"], bars["Low"], bars["Volume"]
    ema12, ema26 = c.ewm(span=12).mean(), c.ewm(span=26).mean()
    ema20, ema50 = c.ewm(span=20).mean(), c.ewm(span=50).mean()
    macd = ema12 - ema26
    sma20 = c.rolling(20).mean(); std20 = c.rolling(20).std()
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1 / 14, adjust=False).mean()
    ret = c.pct_change()
    out = pd.DataFrame(index=bars.index)
    out[f"ret1_{tf}"] = ret
    out[f"ret3_{tf}"] = c.pct_change(3)
    out[f"ret6_{tf}"] = c.pct_change(6)
    out[f"px_ema20_{tf}"] = c / ema20 - 1
    out[f"ema20_50_{tf}"] = ema20 / ema50 - 1
    out[f"ema20_slope_{tf}"] = ema20.pct_change(3)
    out[f"rsi_{tf}"] = _rsi(c)
    out[f"macd_hist_{tf}"] = (macd - macd.ewm(span=9).mean()) / c
    out[f"atr_{tf}"] = atr / c
    out[f"boll_z_{tf}"] = (c - sma20) / std20.replace(0, np.nan)
    out[f"adx_{tf}"] = _adx(h, l, c)
    out[f"vol_ratio_{tf}"] = v / v.rolling(20).mean().replace(0, np.nan)
    out[f"rvol_{tf}"] = ret.rolling(20).std()
    return out


def build_feature_panel(nq_et: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Resample NQ 5m → M30/H1/H4 (right-labeled = known at bar close) + features."""
    s = nq_et.set_index("et")[["Open", "High", "Low", "Close", "Volume"]].copy()
    s.attrs = {}   # drop the cached day-index dict (breaks resample attr-merge)
    agg = {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}
    panels = {}
    for tf, rule in (("M30", "30min"), ("H1", "1h"), ("H4", "4h")):
        bars = s.resample(rule, label="right", closed="right").agg(agg).dropna()
        panels[tf] = tf_features(bars, tf)
    return panels


def _asof(panel: pd.DataFrame, when) -> dict:
    """Last feature row with index <= `when` (strictly causal)."""
    sub = panel.loc[:when]
    return sub.iloc[-1].to_dict() if len(sub) else {}


def assemble(start="2019-08-16", end="2024-08-09") -> pd.DataFrame:
    from zoneinfo import ZoneInfo
    src = load_sources()
    episodes = build_all(src, date.fromisoformat(start), date.fromisoformat(end))
    panels = build_feature_panel(src.nq_et)
    ny = ZoneInfo("America/New_York")
    rows = []
    for ep in episodes:
        if ep["out_6h_dir"] is None and ep["out_24h_dir"] is None:
            continue
        d = date.fromisoformat(ep["ny_date"])
        tmin = DECISION_TIMES[ep["decision_time"]]
        when = pd.Timestamp(f"{d} {tmin // 60:02d}:{tmin % 60:02d}", tz=ny)
        feat = {}
        for tf in ("M30", "H1", "H4"):
            feat.update(_asof(panels[tf], when))
        # macro + regime (known by decision time: daily <= D-1, morning macro released)
        _vord = {"LOW": 0, "NORMAL": 1, "ELEVATED": 2, "HIGH": 3, "EXTREME": 4}
        _mord = {"STRONG_TREND_UP": 1, "RANGING": 0, "STRONG_TREND_DOWN": -1}
        feat.update({
            "ny_date": ep["ny_date"], "decision_time": ep["decision_time"],
            "overnight_change": ep.get("overnight_change"),
            "first_hour_move": ep.get("first_hour_move"),
            "vix_regime_ord": _vord.get(ep.get("vix_regime")),
            "vix_price": ep.get("vix_price"),
            "vix_chg": ep.get("vix_chg"),
            "dxy_chg": ep.get("dxy_chg"),
            "us10y_chg": ep.get("us10y_chg"),
            "market_regime_ord": _mord.get(ep.get("market_regime")),
            "prior_up": 1 if ep.get("prior_day_dir") == "up" else 0 if ep.get("prior_day_dir") == "down" else np.nan,
            "prior_day_change_pct": ep.get("prior_day_change_pct"),
            "range_position": ep.get("range_position"),
            "day_of_week": ep.get("day_of_week"),
            "y6": 1 if ep["out_6h_dir"] == "positive" else 0 if ep["out_6h_dir"] == "negative" else np.nan,
            "y24": 1 if ep["out_24h_dir"] == "positive" else 0 if ep["out_24h_dir"] == "negative" else np.nan,
        })
        rows.append(feat)
    return pd.DataFrame(rows)


# ── Modeling ──────────────────────────────────────────────────────────────────
def _fit_eval(df: pd.DataFrame, ycol: str, dtime: str, seed: int = 0) -> dict:
    import lightgbm as lgb
    from sklearn.metrics import roc_auc_score, accuracy_score

    d = df[df["decision_time"] == dtime].dropna(subset=[ycol]).copy()
    feat_cols = [c for c in d.columns if c not in
                 ("ny_date", "decision_time", "y6", "y24")]
    d = d.replace([np.inf, -np.inf], np.nan)
    tr, te = d[d["ny_date"] <= TRAIN_END], d[d["ny_date"] > TRAIN_END]
    if len(tr) < 200 or len(te) < 100:
        return {"decision_time": dtime, "y": ycol, "insufficient": True,
                "n_train": len(tr), "n_test": len(te)}
    Xtr, ytr = tr[feat_cols], tr[ycol].astype(int)
    Xte, yte = te[feat_cols], te[ycol].astype(int)

    def train(y):
        m = lgb.LGBMClassifier(
            n_estimators=200, num_leaves=15, min_child_samples=40,
            learning_rate=0.02, subsample=0.8, colsample_bytree=0.6,
            reg_alpha=1.0, reg_lambda=1.0, random_state=seed, verbose=-1)
        m.fit(Xtr, y)
        return m

    model = train(ytr)
    proba = model.predict_proba(Xte)[:, 1]
    auc = roc_auc_score(yte, proba)
    acc = accuracy_score(yte, (proba >= 0.5).astype(int))
    base = max(yte.mean(), 1 - yte.mean())         # majority-class baseline

    # placebo: shuffled training labels
    rng = np.random.default_rng(seed)
    plac = train(pd.Series(rng.permutation(ytr.values), index=ytr.index))
    plac_auc = roc_auc_score(yte, plac.predict_proba(Xte)[:, 1])

    imp = sorted(zip(feat_cols, model.feature_importances_), key=lambda x: -x[1])[:12]
    return {
        "decision_time": dtime, "y": ycol, "n_train": len(tr), "n_test": len(te),
        "test_up_rate": round(yte.mean(), 3),
        "test_AUC": round(auc, 4), "placebo_AUC": round(plac_auc, 4),
        "test_acc": round(acc, 4), "majority_baseline": round(base, 4),
        "edge_vs_baseline_pp": round((acc - base) * 100, 2),
        "top_features": [f"{k}:{int(v)}" for k, v in imp],
    }


def run() -> dict:
    import json, os
    df = assemble()
    os.makedirs("research/cortex_confluence", exist_ok=True)
    df.to_parquet("research/cortex_confluence/dataset.parquet")
    results = []
    for dt in DECISION_TIMES:
        for y in ("y6", "y24"):
            results.append(_fit_eval(df, y, dt))
    with open("research/cortex_confluence/results.json", "w") as f:
        json.dump(results, f, indent=2)
    return {"dataset_rows": len(df), "results": results}


if __name__ == "__main__":
    import json
    print(json.dumps(run()["results"], indent=2))
