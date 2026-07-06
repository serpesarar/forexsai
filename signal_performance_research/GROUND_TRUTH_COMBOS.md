# Meta-Intelligence Engine — Combinations Rebuilt on Honest 1m Ground Truth

The previous per-symbol combinations came from `meta_combination_stats`, which the
`combinatorial_auditor` builds with `is_win = (status == "completed")` — the
**inflated 5m-candle label** (see [[ground-truth-wr-inflation]]: 27% of production
"wins" are SL-first losses on 1m). Here every combination is **re-graded on the
honest 1m replay** (74,438 resolved signals ≤ 2026-05-21, system's own TP/SL ladder,
first-touch on real 1m bars, OHLC tie heuristic). WR = honest win rate; EV = mean
**signed pips per resolved trade** (win = +pips to TP, loss = −pips to SL), gross of
spread, comparable **only within a symbol**.

## How the Meta Engine builds combinations (current logic)

1. Each **meta** signal stores `factors.source_combo` = the set of base models that
   agreed when it fired (e.g. `emel+pulse1+pulse2+smc`). Base-model rows (ml, pulse,
   smc…) carry **no** source_combo.
2. `combinatorial_auditor.mine_combination_rules` groups meta rows by
   `source_combo × symbol × regime`, computes WR/PF/expectancy, upserts
   `meta_combination_stats`.
3. `MetaEngine.get_best_combinations` reads the top rows by `win_rate` and uses them
   to boost/penalize the live combo. **So the engine inherits the inflation directly**
   and only ever "knows" the handful of source_combo strings meta itself logged.

Two consequences fixed below: (a) the existing combos' WR was overstated; (b) the
engine never evaluates the *much larger* space of base-model agreements that aren't a
logged meta combo.

---

## Baseline (honest, per symbol — all resolved signals)

| symbol | GT-WR | EV pips | PF | N |
|---|---|---|---|---|
| USOIL.FOREX | 72.6% | +17.5 | 1.80 | 37,893 |
| XAUUSD | 71.0% | +17.1 | 1.39 | 21,775 |
| GDAXI.INDX | 75.6% | +5.3 | 1.25 | 7,462 |
| NDX.INDX | 71.0% | +17.3 | 1.62 | 6,568 |

A combo only earns its place if it beats this baseline on BOTH WR and EV with real N.

## A. The system's EXISTING meta combos, re-graded honestly

| symbol | source_combo | honest WR | EV | PF | N | vs prod |
|---|---|---|---|---|---|---|
| USOIL | emel+pulse1+pulse2+smc | 74.5% | +16.6 | 1.91 | 1489 | was ~84% → −10pp |
| XAUUSD | emel+pulse1+pulse2+pulse3+smc | 75.4% | +27.2 | 1.74 | 1000 | holds up |
| GDAXI | emel+ml | 81.7% | +9.7 | 1.74 | 432 | strong |
| NDX | emel+pulse1+pulse3+smc | 72.5% | +25.3 | 1.87 | 363 | holds up |

They are still **net-positive** after de-inflation (the consensus filter is doing real
work), but USOIL's headline combo loses ~10pp and none is the *best* available — the
engine is leaving better combos on the table (Section B).

## B. Consensus DEPTH lift (honest) — the key structural finding

| # base families agreeing | USOIL | XAUUSD | GDAXI | NDX |
|---|---|---|---|---|
| 1 | 65.2% / +5.0 | 61.4% / **−6.9** | 60.3% / **−13.6** | 66.7% / −1.7 |
| 2 | 70.2% / +15.9 | 69.8% / +13.2 | 72.2% / +1.0 | 72.8% / +14.5 |
| **3** | **75.2% / +21.4** | **73.6% / +24.2** | 79.5% / +14.2 | **74.5% / +27.3** |
| 4 | 74.1% / +18.9 | 73.4% / +23.7 | **84.0% / +7.9** | 70.0% / +20.7 |
| 5+ | 73.5% / +16.5 | 71.9% / +18.9 | 79.8% / +8.3 | 56.1% / **−10.3** (N=542) |

**Single-model signals are ~break-even-to-negative** (XAUUSD/GDAXI EV negative solo) —
honest proof that an edge only appears with agreement. **The robust sweet spot is 3
agreeing base families** (peak EV for USOIL/XAUUSD/NDX); GDAXI peaks at 4. **Going
deeper does NOT help and NDX 5+ collapses** — correcting the earlier inflated claim
that "4+ models" was uniformly best. Recommend the engine require **≥2, target 3**
agreeing families and stop rewarding 5-model stacks.

## C. NEW recommended combinations per symbol (robust: high WR + EV + real N)

Excludes tiny-N (<150) overfit cells like the 100%-WR / 7-model pockets.

**USOIL.FOREX** — *SMC paired with pulse is the engine it's missing*
| combo | WR | EV | PF | N |
|---|---|---|---|---|
| pulse1+smc | 81.4% | +54.4 | 3.37 | 527 |
| pulse2+pulse3+smc | 87.6% | +41.2 | 4.73 | 161 |
| pulse3+smc | 83.3% | +32.1 | 3.04 | 221 |
| pulse1+pulse3+smc | 77.2% | +35.3 | 2.53 | 1000 |

**XAUUSD** — *emel + pulse stacks (the only honest lift on a ~coin-flip instrument)*
| combo | WR | EV | PF | N |
|---|---|---|---|---|
| emel+pulse1+pulse2+pulse3 | 84.1% | +45.7 | 2.91 | 396 |
| emel+pulse1+pulse3 | 85.2% | +55.3 | 3.49 | 135 |
| pulse1+pulse2+pulse3 | 78.4% | +36.5 | 2.12 | 4051 |
| ai_panel+smc (pair) | 78.8% | +33.3 | 2.05 | 231 |

**GDAXI.INDX** — *pulse triplet ± smc (low pip EV but high WR/PF)*
| combo | WR | EV | PF | N |
|---|---|---|---|---|
| pulse1+pulse3+smc | 79.1% | +31.1 | 2.25 | 570 |
| ml+pulse1+pulse2+pulse3 | 86.8% | +16.0 | 3.41 | 302 |
| pulse2+pulse3 | 87.8% | +19.6 | 2.91 | 335 |
| emel+pulse2 (pair) | 88.5% | +8.5 | 2.49 | 619 |

**NDX.INDX** — *pulse triplet is the star, emel adds WR*
| combo | WR | EV | PF | N |
|---|---|---|---|---|
| pulse1+pulse2+pulse3 | 84.2% | +47.0 | 3.91 | 1627 |
| emel+pulse1+pulse2+pulse3 | 89.2% | +55.9 | 5.94 | 435 |
| emel+pulse2 (pair) | 80.9% | +39.8 | 2.97 | 853 |
| pulse1+pulse3 (pair) | 76.4% | +27.3 | 2.21 | 3869 |

---

## What this changes for the Meta Engine

1. **`meta_combination_stats` is built on the inflated label.** Re-grade it on 1m
   ground truth (the `combinatorial_auditor` already has an MT5-matched real-pnl path;
   extend that to a 1m replay grade), or at minimum stop trusting absolute WR.
2. **`smc` is undervalued, especially on USOIL** — pairing smc with pulse gives the
   best honest WR+EV there, yet the logged meta combos under-use it. Surface
   smc+pulse combos.
3. **`emel`+pulse stacks are the honest edge on XAUUSD and NDX** — these beat the
   premium ML scopes, which de-inflate the hardest.
4. **Cap consensus depth at 3 (USOIL/XAUUSD/NDX) or 4 (GDAXI).** Deeper stacks add no
   honest WR and NDX 5+ is negative — the current "more agreement = better" weighting
   is overfit beyond 3.
5. **All EV is gross of spread + uses a generous hold.** A positive within-symbol pips
   EV is necessary but, per [[multi-asset-scalp-no-edge]], not a guarantee of net edge
   after real costs — treat these as the honest *relative ranking*, not a profit promise.

Reproducible: `signal_performance_research/{gt_replay_driver,combo_rebuild}.py`,
`gt_per_signal.jsonl`, `combo_rebuild_results.txt`.
