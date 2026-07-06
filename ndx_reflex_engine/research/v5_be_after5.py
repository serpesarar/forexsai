"""V5 — 'SL → breakeven after 5 one-minute bars', tested on ALL strategy families.

User rule: from the entry point, once 5×1m candles have passed, move the stop-loss to
the entry level (breakeven). Reported per event family and pooled, under realistic
(gap-aware) fills, on the 2025 holdout + 2026 broker sets.

Variants:
  BE@5 (ride to 60m deadline)          — pure user rule, catastrophic far SL first 5 bars
  BE@5 + time-stop 15m                 — user rule + the validated time exit
  reference: time-stop 15m (no BE)     — the current best exit, for comparison
  reference: fixed far SL only (no BE)  — raw
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
from research.v3_exit_systems import ext_arrays, run  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("v5_be5")

VARIANTS = {
    "BE@5 -> 60m ride": {"stop_mode": "fixed", "be_after_bars": 5, "ts_min": 60, "gap_fill": True},
    "BE@5 + time15": {"stop_mode": "fixed", "be_after_bars": 5, "time_exit_min": 15, "ts_min": 60, "gap_fill": True},
    "BE@5 + time30": {"stop_mode": "fixed", "be_after_bars": 5, "time_exit_min": 30, "ts_min": 60, "gap_fill": True},
    "ref: time15 (no BE)": {"stop_mode": "fixed", "time_exit_min": 15, "ts_min": 60, "gap_fill": True},
    "ref: fixed SL only": {"stop_mode": "fixed", "ts_min": 60, "gap_fill": True},
}
FAMILIES = ["chan_rev", "vwap_rev", "sweep", "mom_cont"]


def fmt(m):
    if not m or m.get("n", 0) == 0:
        return "n=0"
    return (f"n={m['n']:4d} WR={m['wr']*100:5.1f}% EV={m['ev_r']:+.3f}R PF={m['pf']:.2f} "
            f"aw={m['avg_win']} al={m['avg_loss']}")


def main() -> None:
    raw = {os.path.basename(p).replace(".parquet", ""): pd.read_parquet(p)
           for p in sorted(glob.glob(os.path.join(config.BARS_DIR, "*.parquet")))}
    d25 = sorted(raw)
    b25 = {}
    for k, d in enumerate(d25):
        b25[d] = ext_arrays(raw[d], raw[d25[k - 1]] if k else None)
    grp = {str(x): g.reset_index(drop=True)
           for x, g in to_bar_frame(fetch_candles()).groupby(to_bar_frame(fetch_candles())["ts"].dt.date)}
    d26 = sorted(grp)
    b26 = {}
    for k, d in enumerate(d26):
        b26[d] = ext_arrays(grp[d], grp[d26[k - 1]] if k else None)

    e = entries_2025()
    eh = e[e["split"] == "hold"]
    e26 = entries_2026(grp)

    report = {}
    for vname, cfg in VARIANTS.items():
        log.info("\n══ %s ══", vname)
        # pooled + per family
        rh = run(eh, b25, cfg)
        r26 = run(e26, b26, cfg)
        log.info("  %-16s HOLD %s", "POOLED", fmt(metrics(rh)))
        log.info("  %-16s 2026 %s", "", fmt(metrics(r26)))
        fam_rows = {}
        for fam in FAMILIES:
            mh = metrics(rh[rh["family"] == fam]) if not rh.empty else {"n": 0}
            m26 = metrics(r26[r26["family"] == fam]) if not r26.empty else {"n": 0}
            fam_rows[fam] = {"hold": mh, "y2026": m26}
            log.info("  %-16s HOLD %s | 2026 %s", fam, fmt(mh), fmt(m26))
        report[vname] = {"hold_pooled": metrics(rh), "y2026_pooled": metrics(r26), "by_family": fam_rows}

    # 10-group for the user's core rule (BE@5 + time15)
    cfg = VARIANTS["BE@5 + time15"]
    log.info("\n══ BE@5 + time15 — 10-GROUP ══")
    rh = run(eh, b25, cfg)
    hd = sorted(rh["ts"].dt.date.astype(str).unique())
    chunks = np.array_split(np.array(hd), 5)
    pos = 0
    grp_rows = []
    for gi, ch in enumerate(chunks, 1):
        m = metrics(rh[rh["ts"].dt.date.astype(str).isin(set(ch))])
        grp_rows.append((f"G{gi} 2025", m))
    r26 = run(e26, b26, cfg)
    for gi, mo in enumerate([2, 3, 4, 5, 6], 6):
        m = metrics(r26[(r26["ts"].dt.year == 2026) & (r26["ts"].dt.month == mo)])
        grp_rows.append((f"G{gi} 2026-{mo:02d}", m))
    for name, m in grp_rows:
        ok = m.get("ev_r", -9) is not None and m.get("ev_r", -9) > 0
        pos += ok
        log.info("  %-14s %s", name, fmt(m))
    log.info("  EV>0 in %d/10", pos)

    with open(os.path.join(config.MODELS_DIR, "v5_be_after5.json"), "w") as f:
        json.dump(report, f, indent=2, default=str)
    log.info("\nsaved → v5_be_after5.json")


if __name__ == "__main__":
    main()
