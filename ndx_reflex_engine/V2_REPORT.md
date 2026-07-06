# NDX Reflex Engine V2 — Symmetric Micro-Scalping Research Report
**Date:** 2026-07-04 · **Target:** TP≈0.10% / SL≈0.10% (flex ≤0.13%), ≥75% WR across 10 date groups, leakage-free, realistic execution.

## VERDICT: NOT ACHIEVABLE with available data — proven honestly, with the full search documented below. Closest valid alternatives found and quantified (one is a genuine +EV live candidate).

---

## 1. Execution & leakage protocol (identical to V1, DESIGN.md §6–8)
- Entry next-bar at ask/bid (or resting limit at event-bar mid, filled only if next bar trades through).
- Exits on the opposite side of book; TP+SL same bar ⇒ LOSS; 1-pt slippage; gap registry drops contaminated windows.
- All selection on first-60%-of-days train split (2025-01→04-11); purged walk-forward (6 folds, 1-day embargo) inside it.
- Holdout (2025-04-14→06-18) and 2026 broker candles never touched by any selection.

## 2. Search performed (aggressive, as required)
| Step | Space | Best train-OOS WR (n≥80) |
|---|---|---|
| A. Raw base rates | 6 families × 4 pct-geometries × 3 time-stops (72 combos) | 42–54% (all −EV raw) |
| B. ML gates (LightGBM + isotonic, Tier A features, market entry) | 24 fitted combos, τ sweep | **65.0%** (vwap_rev tp0.10/sl0.13/ts60, τ0.64, +0.12R) |
| C. + limit-mid entry + tick-microstructure features | 3 reversion families × 12 geometries | **69.1%** (sr_react tp0.10/sl0.13/ts15, τ0.52, +0.14R) |
| D. Extreme-tail probe (top-N by calibrated p) | best 3 combos | 75.0–77.5% only at n=40–60 (≈0.7 ev/day; ±7pp noise) |
| E. Holdout reality check on C-candidates | untouched 2025 holdout | **57.9–59.3%** pooled (−8..−10pp degradation) |

## 3. Why the target fails (quantified, not hand-waved)
1. **Geometry physics:** 0.10% ≈ 20 pts; friction (spread 1.5–3.5 + slippage 1) = 12–20% of the barrier. At near-symmetric RR the friction-adjusted breakeven is 55–60% WR; 75% requires an edge (+0.4R/trade) far beyond anything measured on this instrument at this resolution.
2. **Measured ceiling:** with every honest lever stacked (ML gate + calibration + limit entry + microstructure), the OOS ceiling is ~59% pooled / ~66% best chunk. The train-OOS extreme tail touches 75–77% only at n≤60, and measured OOS degradation (−8..−10pp) puts that tail at ~65–70% out of sample.
3. **Structural:** the strongest configs need tick features that don't exist on 2026 broker candles, so only the 46-day 2025 holdout is valid OOS ground — it cannot supply 10 groups with meaningful trade counts at ≤1 event/day.
4. **Consistency:** extends the 2026-05-29 in-house battery (no honest 70% @1:1 on NDX 1m) — now also no 75% at 0.10/0.13 with ML gating, limit entries, and microstructure.
5. **Residual space TESTED (continuation run, `research/v2_exhaust.py`):**
   - **New trigger families:** `trend_exhaust` (≥5-bar climax + RSI extreme fade): base WR 39–49%,
     EV −0.16..−0.28R at every geometry — dead. `vol_compress` (squeeze→breakout): <60 train
     events — unviable.
   - **Model classes** on the two best lever combos (limit-mid + Tier B, purged WF):
     CatBoost best (top-80 train-OOS 66.2–67.5% WR), XGBoost 50–51%, RF 54–60%, HistGB 60–62.5%,
     logistic 59–62.5%, mean-p **ensemble 59–61%** — none approach the bar.
   - **Tail instability = noise proof:** the top-40 train-OOS tail swings 55%→77.5% across model
     specifications on the same events. A real 75% stratum would be stable across learners; this
     is small-sample variance, exactly what the −8..−10pp holdout degradation predicted.
   - **Feature ablation:** top-15-by-gain ≈ full feature set (Δ ≤ 1.2pp) — no feature-selection rescue.
   - VIX-regime filter untestable as a feature for 2025 (no intraday VIX history in-house);
     session/hour features included throughout and are among the top gates.

## 4. Closest valid alternatives (all leakage-clean)
| Candidate | Geometry | OOS evidence | Status |
|---|---|---|---|
| **V2-EV: vwap_rev limit+micro** τ0.53 | tp0.13%/sl0.13%/ts15 | holdout n=152, WR 57.9%, **EV +0.133R, all 5 holdout chunks +EV** (+0.06..+0.26R) | Best V2 outcome. Live-testable: tick_recorder supplies the micro features; bot already does pending-limit entries. Needs 2026-style forward shadow (no historical broker ticks). |
| V2 Tier-A: vwap_rev market τ0.64 | tp0.10%/sl0.13%/ts60 | train-OOS 65% WR +0.12R, n=137 | transferable to broker candles; candidate for a 10-group EV proof (not WR-75) |
| V1 mom_cont (ATR-symmetric) | tp1.5/sl1.0–1.5×ATR | **2026 broker transfer: +0.29R, n=233** | strongest +EV book; already fully proven |
| V1 high-WR asymmetric (frozen `frozen/high_wr_asymmetric_gate_v1/`) | tp0.4/sl2.0–2.5×ATR | 10/10 groups ≥77.8% WR, EV ≈ −0.06R | preserved per requirement; confidence/display layer |

## 5. Report items required by the goal
- **Algorithm:** event-driven meta-labeling (triggers → LightGBM P(win) → isotonic → τ gate); limit-mid entry variant.
- **Features that mattered:** calibrated gates load on channel/VWAP z, ADX bucket, session hour, spread-state & tick-imbalance (Tier B), 15m stretch. (SHAP export available via models/explain.)
- **Group-by-group:** V2-EV candidate H1–H5 chunk table above (n=25–32 each, WR 53–66%, EV +0.06..+0.26R); 2026 groups impossible for micro-featured configs (no broker tick history).
- **Spread/slippage:** measured Dukascopy per-event spread inside replay + 1pt slippage; 2026 candles 2.0-pt synthetic spread.
- **Why not leakage/overfit:** selection train-only; purged WF with embargo; features strictly causal (confirm-bar close); holdout touched once per candidate; failed attempts reported (this document), not hidden; the honest OOS *degradation* we report is itself evidence the pipeline doesn't leak.
- **Shadow/live suitability:** V2-EV candidate suitable for shadow testing alongside V1 mom_cont; WR-75 target: no.
