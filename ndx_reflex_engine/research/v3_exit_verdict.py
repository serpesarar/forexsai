"""Exit-systems VERDICT under two fill conventions — the honesty gate.

Every stop/trail exit is scored under:
  optimistic  = fill at the stop level (assumes live intrabar fill at the resting stop)
  realistic   = gap-aware fill min(stop, bar_open) (can't fill better than the open)
Target/time/ML exits fill at real prices (limit or close) → convention-IMMUNE (one column).

An exit is only credited as a genuine improvement if it is positive under the REALISTIC
convention on BOTH the 2025 holdout and 2026 broker sets. Anything that is positive only
under the optimistic convention is a fill-assumption artifact, not an edge.
"""
from __future__ import annotations

import glob
import json
import logging
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config  # noqa: E402
from research.transfer_test_2026 import fetch_candles, to_bar_frame  # noqa: E402
from research.v2_exit_study import entries_2025, entries_2026, metrics  # noqa: E402
from research.v3_exit_systems import ext_arrays, run, train_ml_exit  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("verdict")
RNG = np.random.default_rng(9)

STOP_BASED = {"atr_trail", "chandelier", "supertrend", "donchian", "swing", "structure"}
CANDS = {
    "atr_trail 0.4/0.4": {"stop_mode": "atr_trail", "arm": 0.4, "trail": 0.4, "ts_min": 60},
    "chandelier m2.0": {"stop_mode": "chandelier", "N": 10, "m": 2.0, "ts_min": 60},
    "chandelier m2.5": {"stop_mode": "chandelier", "N": 10, "m": 2.5, "ts_min": 60},
    "swing_low": {"stop_mode": "swing", "ts_min": 60},
    "donchian N10": {"stop_mode": "donchian", "N": 10, "ts_min": 60},
    "supertrend 10/3": {"stop_mode": "supertrend", "ts_min": 60},
    "hybrid part+chand": {"stop_mode": "chandelier", "N": 10, "m": 2.5, "partial": True,
                          "tp1": 0.4, "time_exit_min": 45, "ts_min": 60},
    "vwap_target": {"stop_mode": "fixed", "target_mode": "vwap", "tp": 0.8, "ts_min": 60},
    "liquidity_target": {"stop_mode": "fixed", "target_mode": "liquidity", "tp": 1.0, "ts_min": 60},
    "ml_exit": {"stop_mode": "fixed", "ml_exit": True, "ml_tau": 0.6, "ts_min": 60},
    "time_based 15m": {"stop_mode": "fixed", "time_exit_min": 15, "ts_min": 60},
}


def boot(res):
    if res.empty:
        return 0.0
    daily = res.groupby(res["ts"].dt.date)["r"].agg(list).to_list()
    m = [np.mean([r for i in RNG.integers(0, len(daily), len(daily)) for r in daily[i]])
         for _ in range(2000)]
    return float(np.mean(np.array(m) > 0))


def main() -> None:
    raw = {os.path.basename(p).replace(".parquet", ""): pd.read_parquet(p)
           for p in sorted(glob.glob(os.path.join(config.BARS_DIR, "*.parquet")))}
    d25 = sorted(raw)
    b25 = {}
    for k, d in enumerate(d25):
        b25[d] = ext_arrays(raw[d], raw[d25[k - 1]] if k else None)
    grp = {str(x): g.reset_index(drop=True) for x, g in to_bar_frame(fetch_candles()).groupby(
        to_bar_frame(fetch_candles())["ts"].dt.date)}
    d26 = sorted(grp)
    b26 = {}
    for k, d in enumerate(d26):
        b26[d] = ext_arrays(grp[d], grp[d26[k - 1]] if k else None)

    e = entries_2025()
    eh, etr = e[e["split"] == "hold"], e[e["split"] == "train"]
    e26 = entries_2026(grp)
    mlm = train_ml_exit(etr, b25)

    log.info("%-20s %-7s | %-26s | %-26s | verdict", "exit", "conv", "HOLDOUT", "2026")
    out = []
    for name, cfg in CANDS.items():
        immune = cfg["stop_mode"] not in STOP_BASED
        convs = [("real", {**cfg})] if immune else [("optim", {**cfg}),
                                                    ("real", {**cfg, "gap_fill": True})]
        rec = {"name": name, "immune": immune}
        for cv, c in convs:
            mh = metrics(run(eh, b25, c, mlm))
            m26 = metrics(run(e26, b26, c, mlm))
            rec[cv] = {"hold": mh, "y2026": m26}
            log.info("%-20s %-7s | EV=%+.3f WR=%4.0f%% PF=%.2f | EV=%+.3f WR=%4.0f%% PF=%.2f",
                     name, cv, mh.get("ev_r", 0), (mh.get("wr") or 0) * 100, mh.get("pf", 0),
                     m26.get("ev_r", 0), (m26.get("wr") or 0) * 100, m26.get("pf", 0))
        real = rec["real"]
        rec["robust_pos"] = (real["hold"].get("ev_r", -9) > 0 and real["y2026"].get("ev_r", -9) > 0)
        out.append(rec)

    log.info("\n══ CONVENTION-ROBUST POSITIVE (real fills, both OOS sets) ══")
    winners = [r for r in out if r["robust_pos"]]
    if not winners:
        log.info("NONE — no exit is positive under realistic fills on both holdout and 2026.")
    for r in winners:
        cfg = CANDS[r["name"]]
        pooled = pd.concat([run(eh, b25, {**cfg, **({} if r["immune"] else {"gap_fill": True})}, mlm),
                            run(e26, b26, {**cfg, **({} if r["immune"] else {"gap_fill": True})}, mlm)],
                           ignore_index=True)
        log.info("%-20s pooled n=%d WR=%.0f%% EV=%+.3fR PF=%.2f P(EV>0)=%.3f",
                 r["name"], len(pooled), pooled["r"].gt(0).mean() * 100, pooled["r"].mean(),
                 pooled[pooled.r > 0]["r"].sum() / max(-pooled[pooled.r <= 0]["r"].sum(), 1e-9),
                 boot(pooled))

    with open(os.path.join(config.MODELS_DIR, "v3_exit_verdict.json"), "w") as f:
        json.dump(out, f, indent=2, default=str)
    log.info("\nsaved → v3_exit_verdict.json")


if __name__ == "__main__":
    main()
