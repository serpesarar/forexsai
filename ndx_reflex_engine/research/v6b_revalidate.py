"""Leak-free re-validation: does the time-stop / PEF edge survive the feature fix?

Uses the FRESH gate models (data/models/hp_*, refit on the leak-fixed dataset) to
build entries, then runs the validated pure time-stop 15m exit (realistic gap-aware
fills) on 2025 holdout + 2026 broker. Pooled + per-family + 10-group. Compares to the
pre-fix PEF headline (+0.078R pooled).
"""
from __future__ import annotations

import glob
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
from research.transfer_test_2026 import fetch_candles, to_bar_frame  # noqa: E402
from research.v3_exit_systems import ext_arrays, run, metrics  # noqa: E402
from research.v6_direction import build_features  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("revalidate")
MD = config.MODELS_DIR
EXIT = {"stop_mode": "fixed", "time_exit_min": 15, "ts_min": 60, "gap_fill": True}


def score_gate(feats: pd.DataFrame, frozen: dict) -> pd.DataFrame:
    out = []
    for fam, cfg in frozen["families"].items():
        sub = feats[feats["family"] == fam].copy()
        if sub.empty:
            continue
        sl = {"chan_rev": 2.5, "vwap_rev": 2.5, "sweep": 2.0, "mom_cont": 1.5}[fam]
        if cfg["tau"] is None:
            sub["p"] = 1.0
            g = sub
        else:
            with open(os.path.join(MD, f"hp_{fam}_cal.pkl"), "rb") as fh:
                cal = pickle.load(fh)
            m = lgb.Booster(model_file=os.path.join(MD, f"hp_{fam}.txt"))
            sub["p"] = cal["iso"].predict(m.predict(sub[cal["cols"]]))
            g = sub[sub["p"] >= cfg["tau"]]
        gg = g[["ts", "direction", "family", "p"]].copy()
        gg["sl_atr"] = sl
        out.append(gg)
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame()


def main() -> None:
    with open(os.path.join(MD, "hp_frozen.json")) as f:
        frozen = json.load(f)
    log.info("clean-feature gate families: %s", list(frozen["families"]))

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

    # 2025 features from rebuilt (leak-fixed) dataset; 2026 fresh
    ds = pd.read_parquet(os.path.join(config.EVENTS_DIR, "dataset.parquet"))
    f25 = ds.drop_duplicates(subset=["ts", "direction", "family"])
    f26 = build_features(grp)

    split = date.fromisoformat("2025-04-11")
    g25 = score_gate(f25, frozen)
    eh = g25[g25["ts"].dt.date > split]
    e26 = score_gate(f26, frozen)
    log.info("clean-gate entries: holdout=%d 2026=%d", len(eh), len(e26))

    rh, r26 = run(eh, b25, EXIT), run(e26, b26, EXIT)
    log.info("\n══ LEAK-FREE time-stop 15m (pooled) ══")
    log.info("  HOLDOUT %s", metrics(rh))
    log.info("  2026    %s", metrics(r26))
    for fam in frozen["families"]:
        log.info("  %-9s HOLD %s | 2026 %s", fam,
                 metrics(rh[rh["family"] == fam]), metrics(r26[r26["family"] == fam]))

    # 10-group
    hd = sorted(rh["ts"].dt.date.astype(str).unique())
    chunks = np.array_split(np.array(hd), 5)
    rows = []
    for gi, ch in enumerate(chunks, 1):
        rows.append((f"G{gi} 2025", metrics(rh[rh["ts"].dt.date.astype(str).isin(set(ch))])))
    for gi, mo in enumerate([2, 3, 4, 5, 6], 6):
        rows.append((f"G{gi} 2026-{mo:02d}", metrics(r26[(r26["ts"].dt.year == 2026) & (r26["ts"].dt.month == mo)])))
    pos = 0
    log.info("\n══ LEAK-FREE 10-GROUP ══")
    for name, m in rows:
        ok = m.get("ev_r", -9) is not None and m.get("ev_r", -9) > 0
        pos += ok
        log.info("  %-14s n=%4s WR=%s EV=%s PF=%s", name, m.get("n"),
                 f"{m['wr']*100:.0f}%" if m.get("wr") is not None else "-",
                 f"{m['ev_r']:+.3f}" if m.get("ev_r") is not None else "-", m.get("pf"))
    pooled = pd.concat([rh, r26], ignore_index=True)
    log.info("  EV>0 in %d/10 | pooled n=%d WR=%.0f%% EV=%+.3fR (pre-fix PEF was +0.078R)",
             pos, len(pooled), pooled["r"].gt(0).mean() * 100, pooled["r"].mean())


if __name__ == "__main__":
    main()
