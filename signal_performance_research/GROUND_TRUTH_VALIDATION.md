# Combo Validation — Leak-Free + Robustness Proof

Two independent gates run on the honest 1m ground-truth outcomes (`gt_per_signal.jsonl`,
74,438 resolved signals ≤ 2026-05-21). Reproducible:
`signal_performance_research/{leak_audit,validate_combos}.py`.

## Gate 1 — Leak audit (`leak_audit.py`) — PASSED

3,000 random signals (seed 42) re-run through the production 1m replay with a per-bar
trace. Four checks, **0 violations each**:

1. entry bar ts ≥ signal `created_at` (floored to the minute) — never enter before the signal.
2. exit bar ts ≥ entry bar ts — verdict never from a pre-entry bar.
3. no traced bar has ts < entry ts — walk is strictly forward.
4. TP/SL levels reproducible from the entry price alone (tol 0.02 USOIL / 0.1 else) —
   levels are not set with future data.

Result: **NO LEAK DETECTED — all checks clean.** The replay is forward-only and the
TP/SL ladder is a deterministic function of entry price.

## Gate 2 — Robustness (`validate_combos.py`)

The pulse models log every 1–3 min, so member-level N is inflated by near-duplicate
rows. Three stress tests:

- **Independence:** collapse each (symbol, direction, combo) to ONE trade per disjoint
  15-min (and 60-min) bucket; outcome = consensus of the agreeing members. WR must
  survive de-duplication.
- **Out-of-sample:** split buckets by date at the median; the test-half WR must ≈ in-sample.
- **Bootstrap 95% CI:** resample independent 15m buckets; the CI **lower bound** must
  clear the symbol baseline.

A combo is **certain** only if it survives all three.

### Verdict table (15m-independent WR, OOS, CI-lower vs baseline)

| symbol | combo | 15m WR (N) | OOS | CI-lo vs base | verdict |
|---|---|---|---|---|---|
| USOIL (72.6%) | pulse1+smc | 82% (120) | 85% | 75% > base | ✅ certain |
| USOIL | pulse3+smc | 92% (24) | 100% | 79% > base | ✅ certain |
| USOIL | pulse2+pulse3+smc | 91% (22) | 91% | 77% > base | ✅ certain (small N) |
| USOIL | pulse1+pulse3+smc | 75% (103) | 77% | 66% < base | ⚠️ not separable |
| XAUUSD (71.0%) | pulse1+pulse2+pulse3 | 79% (979) | 83% | 77% > base | ✅ certain — strongest |
| XAUUSD | emel+pulse1+pulse2+pulse3 | 83% (76) | 95% | 74% > base | ✅ certain |
| XAUUSD | emel+pulse1+pulse3 | 84% (25) | 92% | 68% < base | ⚠️ small-N |
| GDAXI (75.6%) | pulse2+pulse3 | 89% (90) | 93% | 82% > base | ✅ certain |
| GDAXI | ml+pulse1+pulse2+pulse3 | 89% (36) | 83% | 78% > base | ✅ certain (small N) |
| GDAXI | pulse1+pulse3+smc | 80% (55) | 68% | 69% < base | ❌ OOS < base, reject |
| NDX (71.0%) | pulse1+pulse2+pulse3 | 82% (240) | 84% | 78% > base | ✅ certain — star |
| NDX | emel+pulse1+pulse2+pulse3 | 77% (30) | 60% | 63% < base | ❌ OOS collapse, reject |
| NDX | emel+pulse2 | exact N=4 | — | — | ❌ pair-count artifact |

### Certain combos (leak-free + robust)
- USOIL → **pulse1+smc**, **pulse3+smc**, pulse2+pulse3+smc
- XAUUSD → **pulse1+pulse2+pulse3** (979 independent trades, CI 77–82%), emel+pulse1+pulse2+pulse3
- GDAXI → **pulse2+pulse3**, ml+pulse1+pulse2+pulse3
- NDX → **pulse1+pulse2+pulse3**

### Rejected by robustness (passed leak audit but overfit)
- GDAXI pulse1+pulse3+smc, NDX emel+pulse1+pulse2+pulse3 — OOS WR fell below their own
  baseline; the high member-WR was overlapping-sample inflation.
- NDX emel+pulse2 — the prior 80.9%/N853 was a *pair* count (any bucket containing the
  pair). As an EXACT independent combo it is N=4. Discard; the pulse-triplet is the NDX edge.

**Conclusion:** the durable, leak-free edges are the **pulse-triplet** (XAU/NDX/GDAXI via
pulse2+pulse3) and **smc+pulse pairs** (USOIL). Deeper emel-stacks look strong at member
level but are artifacts of repeat logging once independence is enforced — consistent with
the depth-3 robust-peak finding. EV is gross of spread; this is honest relative ranking,
not a net-profit guarantee ([[multi-asset-scalp-no-edge]]).
