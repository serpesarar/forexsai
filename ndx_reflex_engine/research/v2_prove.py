"""V2 proof — frozen symmetric micro-scalp candidates on the 10 untouched groups.

Same groups as V1's proof (5×2025 holdout chunks + 5×2026 broker months), pct
geometry, PASS bar = WR ≥ 0.75 in every group. Full metrics per group:
n, WR, EV(R), profit factor, max drawdown (R, cumulative), avg win, avg loss.

Usage: python3 research/v2_prove.py
"""
from __future__ import annotations

import json
import logging
import os
import pickle
import sys
from datetime import date

import lightgbm as lgb
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config  # noqa: E402
from features.pack import compute_feature_frame, event_features  # noqa: E402
from labels.triple_barrier import Geometry, label_events_fast  # noqa: E402
from triggers.detect import detect_day  # noqa: E402
from research.transfer_test_2026 import fetch_candles, to_bar_frame  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("v2_prove")

WR_BAR = 0.75


def score_and_label(cfg: dict, fam: str, feats: pd.DataFrame,
                    bars_by_day: dict[str, pd.DataFrame]) -> pd.DataFrame:
    with open(os.path.join(config.MODELS_DIR, f"{cfg['tag']}_cal.pkl"), "rb") as f:
        cal = pickle.load(f)
    m = lgb.Booster(model_file=os.path.join(config.MODELS_DIR, f"{cfg['tag']}.txt"))
    id_cols = ["ts", "direction", "family"]
    keep = id_cols + [c for c in cal["cols"] if c not in id_cols]
    sub = (feats.loc[feats["family"] == fam, keep]
           .drop_duplicates(subset=id_cols).reset_index(drop=True))
    if sub.empty:
        return pd.DataFrame()
    sub["p"] = cal["iso"].predict(m.predict(sub[cal["cols"]]))
    gated = sub[sub["p"] >= cfg["tau"]].reset_index(drop=True)
    if gated.empty:
        return pd.DataFrame()
    geo = Geometry(cfg["tp_pct"], cfg["sl_pct"], cfg["ts_min"], mode="pct")
    labs = []
    for d, grp in gated.groupby(gated["ts"].dt.date.astype(str)):
        if d in bars_by_day:
            labs.append(label_events_fast(bars_by_day[d], grp.reset_index(drop=True), geo))
    if not labs:
        return pd.DataFrame()
    lab = pd.concat(labs, ignore_index=True)
    lab = lab[lab["outcome"].isin(["win", "loss"])].copy()
    lab["y"] = (lab["outcome"] == "win").astype(int)
    lab["r_net"] = lab["r_multiple"] - config.SLIPPAGE_PTS / lab["sl_dist"]
    return lab


def metrics(name: str, lab: pd.DataFrame) -> dict:
    if lab.empty:
        return {"group": name, "n": 0, "pass": False}
    lab = lab.sort_values("ts")
    r = lab["r_net"].to_numpy()
    wins, losses = r[lab["y"] == 1], r[lab["y"] == 0]
    equity = np.cumsum(r)
    dd = float(np.max(np.maximum.accumulate(equity) - equity)) if len(r) else 0.0
    pf = float(wins.sum() / max(-losses.sum(), 1e-9)) if len(losses) else np.inf
    wr = float(lab["y"].mean())
    return {"group": name, "n": len(lab), "wr": round(wr, 4), "ev": round(float(r.mean()), 4),
            "pf": round(pf, 3), "max_dd_r": round(dd, 2),
            "avg_win": round(float(wins.mean()), 3) if len(wins) else None,
            "avg_loss": round(float(losses.mean()), 3) if len(losses) else None,
            "pass": bool(wr >= WR_BAR)}


def main() -> None:
    with open(os.path.join(config.MODELS_DIR, "v2_frozen.json")) as f:
        frozen = json.load(f)
    if not frozen["families"]:
        log.info("no frozen V2 candidates — nothing to prove")
        return
    split_day = date.fromisoformat(frozen["split_day"])

    # 2025 holdout
    ds = pd.read_parquet(os.path.join(config.EVENTS_DIR, "dataset.parquet"))
    hold = ds[ds["ts"].dt.date > split_day]
    days25 = sorted(hold["ts"].dt.date.astype(str).unique())
    bars25 = {d: pd.read_parquet(os.path.join(config.BARS_DIR, f"{d}.parquet"))
              for d in days25 if os.path.exists(os.path.join(config.BARS_DIR, f"{d}.parquet"))}
    chunks = np.array_split(np.array(days25), 5)

    # 2026 broker
    bars26_all = to_bar_frame(fetch_candles())
    days26 = sorted(bars26_all["ts"].dt.date.unique())
    bars26, feat26 = {}, []
    for i, d in enumerate(days26):
        day_bars = bars26_all[bars26_all["ts"].dt.date == d].reset_index(drop=True)
        bars26[str(d)] = day_bars
        prev = None if i == 0 else bars26_all[bars26_all["ts"].dt.date == days26[i - 1]].reset_index(drop=True)
        ev = detect_day(day_bars, prev, d)
        if ev.empty:
            continue
        ctx = pd.concat([prev, day_bars]) if prev is not None else day_bars
        fe = event_features(compute_feature_frame(ctx.reset_index(drop=True)), ev)
        if not fe.empty:
            feat26.append(fe)
    feats26 = pd.concat(feat26, ignore_index=True)

    for key, cfg in frozen["families"].items():
        fam = key.split("|")[0]
        log.info("\n=== V2 CANDIDATE %s (tau=%.2f, tp=%.2f%% sl=%.2f%% ts=%d) ===",
                 key, cfg["tau"], cfg["tp_pct"] * 100, cfg["sl_pct"] * 100, cfg["ts_min"])
        rows = []
        for gi, chunk in enumerate(chunks, start=1):
            feats = hold[hold["ts"].dt.date.astype(str).isin(set(chunk))]
            rows.append(metrics(f"G{gi} 2025 {chunk[0]}..{chunk[-1]}",
                                score_and_label(cfg, fam, feats, bars25)))
        for gi, month in enumerate([2, 3, 4, 5, 6], start=6):
            mf = feats26[(feats26["ts"].dt.year == 2026) & (feats26["ts"].dt.month == month)]
            rows.append(metrics(f"G{gi} 2026-{month:02d}", score_and_label(cfg, fam, mf, bars26)))
        all_pass = all(r.get("pass") for r in rows)
        for r in rows:
            log.info("%-26s n=%4s WR=%s EV=%s PF=%s DD=%s aw=%s al=%s %s",
                     r["group"], r["n"],
                     f"{r['wr']*100:.1f}%" if r.get("wr") is not None else "-",
                     f"{r['ev']:+.3f}" if r.get("ev") is not None else "-",
                     r.get("pf", "-"), r.get("max_dd_r", "-"),
                     r.get("avg_win", "-"), r.get("avg_loss", "-"),
                     "PASS" if r.get("pass") else "FAIL")
        log.info("CANDIDATE VERDICT: %s", "ALL 10 PASS" if all_pass else "NOT PROVEN")
        with open(os.path.join(config.MODELS_DIR, f"v2_proof_{cfg['tag']}.json"), "w") as f:
            json.dump({"cfg": cfg, "groups": rows, "all_pass": all_pass}, f, indent=2)


if __name__ == "__main__":
    main()
