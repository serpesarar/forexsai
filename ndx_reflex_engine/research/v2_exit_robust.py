"""Robustness of the winning exit (ATR trailing) — is it real or a fluke?

1. Per-group: the same 10 disjoint groups (5×2025-holdout chunks + 5×2026 months),
   WR / EV / PF / n each, for the train-frozen trail params.
2. Parameter neighborhood: grid of (activate, trail) reported on HOLDOUT — a real
   edge is a plateau, a fluke is a spike.
3. Block bootstrap P(EV>0) on the pooled OOS (holdout+2026) trailing PnL.
"""
from __future__ import annotations

import json
import logging
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config  # noqa: E402
import glob  # noqa: E402
from research.transfer_test_2026 import fetch_candles, to_bar_frame  # noqa: E402
from research.v2_exit_study import (entries_2025, entries_2026, metrics,  # noqa: E402
                                    run_policy)

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("exit_robust")
RNG = np.random.default_rng(11)
PRM = {"activate_atr": 0.4, "trail_atr": 0.4, "ts_min": 60}


def main() -> None:
    bars25 = {os.path.basename(p).replace(".parquet", ""): pd.read_parquet(p)
              for p in sorted(glob.glob(os.path.join(config.BARS_DIR, "*.parquet")))}
    bars26_all = to_bar_frame(fetch_candles())
    bars26 = {str(d): g.reset_index(drop=True) for d, g in bars26_all.groupby(bars26_all["ts"].dt.date)}

    e25 = entries_2025()
    e_hold = e25[e25["split"] == "hold"]
    e26 = entries_2026(bars26)

    # ── 1. per-group ──
    log.info("══ 10-GROUP STABILITY (atr_trail arm=0.4 trail=0.4) ══")
    hold_days = sorted(e_hold["ts"].dt.date.astype(str).unique())
    chunks = np.array_split(np.array(hold_days), 5)
    all_rows = []
    for gi, ch in enumerate(chunks, 1):
        ent = e_hold[e_hold["ts"].dt.date.astype(str).isin(set(ch))]
        m = metrics(run_policy(ent, bars25, "atr_trail", PRM))
        all_rows.append(("G%d 2025 %s..%s" % (gi, ch[0], ch[-1]), m))
    for gi, month in enumerate([2, 3, 4, 5, 6], 6):
        ent = e26[(e26["ts"].dt.year == 2026) & (e26["ts"].dt.month == month)]
        m = metrics(run_policy(ent, bars26, "atr_trail", PRM))
        all_rows.append(("G%d 2026-%02d" % (gi, month), m))
    pos_ev = 0
    for name, m in all_rows:
        ok = m.get("ev_r", -9) is not None and m.get("ev_r", -9) > 0
        pos_ev += ok
        log.info("%-24s n=%4s WR=%s EV=%s PF=%s DD=%s", name, m.get("n"),
                 f"{m['wr']*100:.1f}%" if m.get("wr") is not None else "-",
                 f"{m['ev_r']:+.3f}" if m.get("ev_r") is not None else "-",
                 m.get("pf"), m.get("max_dd_r"))
    log.info("groups with EV>0: %d/10", pos_ev)

    # ── 2. parameter neighborhood on holdout ──
    log.info("\n══ PARAMETER NEIGHBORHOOD (HOLDOUT EV_R) ══")
    log.info("arm\\trail   " + "  ".join(f"{t:>6.1f}" for t in (0.3, 0.4, 0.5, 0.6, 0.8)))
    for act in (0.3, 0.4, 0.5, 0.6):
        cells = []
        for tr in (0.3, 0.4, 0.5, 0.6, 0.8):
            m = metrics(run_policy(e_hold, bars25, "atr_trail",
                                   {"activate_atr": act, "trail_atr": tr, "ts_min": 60}))
            cells.append(m.get("ev_r", float("nan")))
        log.info("arm=%.1f    " % act + "  ".join(f"{c:+6.3f}" for c in cells))

    # ── 3. bootstrap on pooled OOS ──
    log.info("\n══ BLOCK BOOTSTRAP P(EV>0), pooled holdout+2026 ══")
    rh = run_policy(e_hold, bars25, "atr_trail", PRM)
    r26 = run_policy(e26, bars26, "atr_trail", PRM)
    pooled = pd.concat([rh, r26], ignore_index=True)
    daily = pooled.groupby(pooled["ts"].dt.date)["r"].agg(list).to_list()
    means = []
    for _ in range(5000):
        pick = RNG.integers(0, len(daily), size=len(daily))
        means.append(np.mean([r for i in pick for r in daily[i]]))
    p_pos = float(np.mean(np.array(means) > 0))
    log.info("pooled n=%d WR=%.1f%% EV=%+.3fR PF=%.2f | P(EV>0)=%.3f",
             len(pooled), pooled["r"].gt(0).mean() * 100, pooled["r"].mean(),
             pooled[pooled.r > 0]["r"].sum() / -pooled[pooled.r <= 0]["r"].sum(), p_pos)
    with open(os.path.join(config.MODELS_DIR, "v1_exit_robust.json"), "w") as f:
        json.dump({"groups": [(n, m) for n, m in all_rows], "p_ev_pos": p_pos}, f, indent=2, default=str)


if __name__ == "__main__":
    main()
