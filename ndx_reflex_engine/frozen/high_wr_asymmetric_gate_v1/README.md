# high_wr_asymmetric_gate_v1 — FROZEN 2026-07-04

NDX Reflex Engine V1 high-win-rate mode. **Do not overwrite.** Proven ≥70% WR
(floor 77.8%, pooled ~82%, n=3,374) across 10 disjoint date groups: 5 chunks of
the 2025 Dukascopy holdout + 5 monthly slices of real 2026 USTEC broker candles.
Full proof table: `prove70_report.json`; protocol: `../../DESIGN.md`,
results narrative: `../../FINDINGS.md` §"10-group ≥70% WR proof".

## Contents
- `hp_frozen.json` — frozen (geometry, tau) per family + train-OOS stats
- `hp_{chan_rev,vwap_rev,sweep}.txt` — LightGBM boosters (Tier A features)
- `hp_*_cal.pkl` — isotonic calibrators + feature column lists
- mom_cont runs base-rate (tau=null in hp_frozen.json), no model file
- `prove70_report.json` — the 10-group WR proof
- `battery_report.json`, `geometry_choice.json` — V1 validation context

## Known properties
- WR 77.8–85.8% per group under bid/ask replay + 1pt slippage (2026: 2pt synthetic spread)
- **EV ≈ −0.06R/group (slightly negative)** — asymmetric geometry (TP 0.4×ATR, SL 2.0–2.5×ATR;
  breakeven ≈86% at sl2.5). NOT a standalone trading book.
- Valid uses: confidence layer, signal-quality filter, panel display model, warning
  system, research baseline.

## Reproduce / re-score
Selection: `research/high_precision.py` (train split only, target 85% train-OOS WR).
Proof: `research/prove_70.py` (reads live copies under `data/models/` — point it at
these files if the live copies are later replaced).
