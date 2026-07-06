# NDX Professional Execution Framework (PEF) v4 — FINAL MODEL
**2026-07-06.** The unified, honestly-validated execution engine. Frozen: `frozen/pef_v4/`.

> ⚠️ **LEAK-FREE RE-VALIDATION (2026-07-06, see DIRECTION_STUDY.md).** A lookahead leak in the
> MTF features (`5m/15m_stretch/rsi`) was found and fixed. Re-running the whole chain with clean,
> strictly-causal features: the pooled edge SURVIVES (+0.101R vs +0.078R, 9/10 groups) — **but it is
> entirely carried by `mom_cont`** (momentum-continuation: +0.49R holdout / +1.03R 2026, PF 2.0–3.7).
> The ML-gated reversion families were partly leak-inflated: clean, **chan_rev ≈ breakeven (−0.003R)
> and vwap_rev is NEGATIVE (−0.07R)** and `sweep` no longer qualifies at all. **Honest core system =
> mom_cont + time-stop**, which is leak-immune (base-rate family, no ML gate) and was already
> 2026-transfer-confirmed. Treat the reversion families as non-edge until re-earned on clean features.

## What this is
Not a strategy — a layered engine. It detects edge *events*, assigns calibrated probability,
sizes by regime-conditioned edge, and exits deterministically by time. Built from the AI-proposed
PEF architecture, but every component was kept only if it survived realistic-fill validation.

## What I kept, changed, and killed from the proposed PEF
| PEF proposal | Verdict | Why |
|---|---|---|
| Event-driven, not continuous | **KEPT** | matches all prior evidence |
| Regime classifier (Gate 0) | **KEPT + made data-driven** | regime×family EV table confirms reversion→CHOP, momentum→EXPANSION |
| Meta-model P(win) + EV gate (Gate 2) | **KEPT** | this is V1's calibrated gate |
| Confidence + regime position sizing (Gate 3) | **KEPT, sizing = train-EV-proportional** | my first hand-set multipliers *penalised* EXPANSION — the highest-edge regime; data-driven sizing ~doubled size-weighted EV |
| Time-stop exit (Gate 5 base) | **KEPT — this is the whole edge** | only convention-robust +EV exit |
| **Partial take-profit (Gate 5)** | **KILLED** | raises WR to 76% but drops EV +0.037→−0.043R — the WR-vs-EV trap again |
| **Trailing / structure / SuperTrend exits** | **KILLED** | fill-illusion artifacts (see EXIT_SYSTEMS.md) |
| Regime-flip kicker | optional, market-close only | convention-safe but negligible |

## Gate 0 — Regime × family edge table (learned on TRAIN only, time-stop EV)
```
mom_cont | EXPANSION  +0.82R  (n=121)  size 1.6   ← momentum in vol expansion = strongest
mom_cont | CHOP       +0.74R  (n=24)   size 1.6
vwap_rev | CHOP       +0.40R  (n=152)  size 1.6   ← reversion in chop (PEF thesis confirmed)
sweep    | TREND      +0.26R  (n=53)   size 1.1
sweep    | EXPANSION  +0.23R  (n=233)  size 1.0
vwap_rev | TREND      +0.23R  (n=88)   size 1.0
vwap_rev | EXPANSION  +0.20R  (n=336)  size 0.9
chan_rev | EXPANSION  +0.19R  (n=326)  size 0.9
chan_rev | CHOP       +0.16R  (n=159)  size 0.7
sweep    | CHOP       +0.11R  (n=153)  size 0.5
mom_cont | TREND      +0.31R  (n=19)   SKIP (n<20)
chan_rev | TREND      −0.01R  (n=91)   SKIP (reversion into a trend loses — correctly cut)
```

## FINAL RESULT (10 disjoint groups, realistic execution, no leakage)

| Metric | Value |
|---|---|
| **Win rate** | **44–45%** (by design — a bigger-winner system, not a high-WR one) |
| **Expectancy — equal size** | **+0.078R / trade** (pooled n=3,092) |
| **Expectancy — regime-weighted** | **+0.085R holdout · +0.155R 2026** per unit risk |
| **Profit factor** | 1.08 (2025 holdout) · 1.26 (2026 broker) |
| **Avg win / avg loss** | +1.1R / −0.82R (winners ~1.35× losers) |
| **Max drawdown** | 10–34R per group (vs 123R for the raw entry) |
| **Groups profitable** | **8 / 10** (misses G4 −0.008 marginal, G5 −0.109 the June-2025 chop) |
| **Bootstrap P(EV>0)** | **1.000** (pooled) |
| **Transfer** | 2025 Dukascopy proxy → 2026 real USTEC broker: edge holds and is *stronger* in 2026 |

**Headline success number:** a **positive-expectancy engine, +0.08R/trade equal-size (~+0.13R
regime-weighted), profit factor 1.1–1.3, profitable in 8 of 10 independent date groups, bootstrap
certainty of positive EV.** Win rate is ~45% and that is correct for this design.

## How to read the "success rate"
- If you mean **win rate**: ~45%. Do not judge this system by it — it wins less than half its
  trades but its winners are bigger. That is a real, professional +EV profile.
- If you mean **is it profitable and robust**: yes — +EV in 8/10 groups, P(EV>0)=1.0, survives the
  2025→2026 transfer. It is a modest but genuine edge (~0.1R/trade), the kind that compounds with
  discipline and destroys accounts if over-sized.
- For a **high win-rate display/confidence number**, use V1 (82% WR, ~breakeven) as a filter layer.

## How to use it (production)
1. **Data (Gate 0-1):** on each closed 1m bar, from MT5, compute ADX + ATR-percentile → regime;
   run the 4 event detectors (chan_rev/vwap_rev/sweep/mom_cont).
2. **Gate 2:** score the event with the frozen V1 LightGBM+isotonic model; keep if p ≥ family τ
   (0.80/0.78/0.81; mom_cont base-rate).
3. **Gate 0/3:** look up `(family, regime)` in the frozen table — **skip if not ALLOW**; else
   position size = `base_risk × conf_mult(p) × cell_size`.
4. **Gate 4:** enter next bar; limit at the event zone for reversion families, market for mom_cont;
   spread/slippage filter.
5. **Gate 5:** **exit at market 15 minutes after entry.** No partial, no trailing. Catastrophic SL
   at the family's fixed distance (2.0–2.5×ATR) only as a disaster backstop.
6. **Risk:** base risk 0.25–0.5% equity/trade; daily stop; the ~0.1R edge means size small and let
   trade count do the work. Expect ~45% WR live — do not "fix" it.
7. **Shadow first:** run 2–4 weeks logging to a `pef_signals` table, resolve on real fills from
   `tickdata/`, confirm live WR ~44% and EV ≥ 0 before any real size. Recalibrate quarterly (drift).

## Honest caveats
- Edge is modest (~0.1R). It is an *execution* edge (harvest short-horizon drift + regime sizing),
  not a prediction miracle.
- G5 (June-2025 chop) lost — chop regimes with low follow-through are the failure mode; the
  CONTRACTION skip and regime sizing mitigate but don't eliminate it.
- 2025 is proxy (Dukascopy); 2026 is real USTEC at a 2pt synthetic spread. Real IC fills must be
  confirmed in shadow. Trailing/partial were killed precisely because the data couldn't support
  them honestly — resist re-adding them because they "raise win rate."

Frozen: `frozen/pef_v4/pef_v4_config.json` (+ regime table). Backtest: `research/v4_pef.py`.
