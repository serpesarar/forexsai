# Issue #17: XAU PULSE1 BUY swing-high filter

## Decision

Prepare the proposed predicate, but ship it in **shadow mode by default**.
Historical winner impact is **not validated**. Do not interpret the issue's
six failure examples or its estimated 5–10% winner removal as a backtest.
No live configuration, trading data, or deployment was changed by this work.

Issue: https://github.com/serpesarar/forexsai/issues/17
Baseline inspected: `b2a596e` on `main` (2026-10-26).

## Findings

- The proposed `/app/models/pulse1/signal_filter.py` does not exist in this
  checkout. PULSE1 is implemented in `backend/routers/emel_pulse.py`.
- Existing XAU BUY AI-Ops guards (001/002/003) use the feature snapshot there.
  No existing guard implements this issue's swing-high predicate.
- `signal_feature_snapshot._compute_aggregates` uses **0.3 ATR** for
  `near_resistance`. Therefore a 0.36 ATR distance with `near_resistance=false`
  is consistent with that definition, not evidence of a calculation bug.
- The distance is `(max(high over last 30 bars) - last close) / ATR` on M30,
  not a separate pivot-high or order-book resistance detector.
- Snapshot `regime_label` is separate from `market_regime_service`'s router
  regime. The new predicate uses the requested snapshot field.
- This checkout contains price and trade research archives, but no located
  PULSE1 outcome export containing the required entry-time M30 distance and
  regime fields. Supabase credentials were not available in this environment.
  The six source rows and historical winners could not be independently
  checked. Candles or today's snapshot cannot substitute for entry-time factors.
- Existing canonical metrics explicitly distinguish geometry epochs and
  partial/ambiguous outcomes. A higher raw win rate alone cannot justify
  activation; MFE/MAE are not realized trade P/L.

## Implementation

`pulse1_swing_high_filter.would_block` is the shared, deterministic predicate:

1. Symbol is XAUUSD or an established gold alias (XAUUSD.FOREX/GOLD).
2. Model is PULSE1, not PULSE2/3, ML, or inverse shadow models.
3. Direction is BUY.
4. Snapshot explicitly says `transition` or `unknown`.
5. Finite `M30_dist_swing_high_30_atr < 2.0`.

Exactly 2.0 passes. Missing regimes do not silently become `unknown`; missing,
boolean, malformed and non-finite distances do not become zero. Signed finite
distances retain the issue's literal `< 2.0` semantics.

The live gate is wired into `services.signal_gates`, which is already used by
the PULSE1 panel and `prediction_logger` safety net. The panel sets both signal
and signal type to HOLD when a gate blocks, before calling its signal logger.
Existing gates run first. Feature fetching reuses the shared 30-second snapshot
cache; out-of-scope and disabled calls do not fetch it. Fetch errors fail open.
The existing router AI-Ops guards remain in place.

In shadow mode, `pulse1_swing_high_gate` verdicts use the existing collector.
For signals that survive the remaining pipeline and are actually recorded,
`prediction_logger` writes `factors.shadow_gates` and
`factors.shadow_gate_reasons`, alongside the eventual outcome. The gate is also
registered in the Shadow Mode overview. A candidate rejected elsewhere is not
represented as a shadow trade by this change.

| Configuration | Behavior |
|---|---|
| `PULSE1_SWING_HIGH_GATE_ENABLED=1`, `PULSE1_SWING_HIGH_GATE_BLOCK=0` | Default: measure only |
| `PULSE1_SWING_HIGH_GATE_BLOCK=1` | Opt-in: matching BUY becomes HOLD |
| `PULSE1_SWING_HIGH_GATE_ENABLED=0` | Disable evaluation entirely |

Only literal `1` enables blocking. Typographical or truthy strings do not
accidentally activate it. Configuration changes require normal service restart
and panel-cache expiry (or an explicit refreshed request); this patch does not
invalidate deployed caches or change environment variables.

## Historical validation tool

`backend/research/evaluate_issue17.py` reads a **JSON array** of exported
`prediction_logs` rows and prints JSON. It performs no network calls, database
writes, parameter search, or gate activation. Use a complete, deduplicated export
with the following columns (entry-time factors, not reconstructed factors):

```sql
SELECT id, created_at, symbol, model_type, ml_direction, status,
       resolution_reason, timeframe, factors, ml_entry_price,
       ml_target_price, ml_stop_price, stop_loss_pips, exit_price,
       targets, targets_hit, highest_profit_pips, lowest_drawdown_pips
FROM prediction_logs
WHERE symbol IN ('XAUUSD', 'XAUUSD.FOREX', 'GOLD')
  AND model_type = 'pulse1'
  AND ml_direction = 'BUY'
  AND status IN ('completed', 'stopped')
ORDER BY created_at, id;
```

```bash
python backend/research/evaluate_issue17.py /path/to/prediction_logs.json
```

The report exposes before/kept/blocked outcome counts, blocked historical
winners, feature coverage, complete-case results, regime strata and target-type
epochs. Every metric set includes the repository's `aggregate_outcomes`
canonical metrics (expectancy, break-even WR, ambiguity, partials and warnings).
Absolute P/L is left unavailable rather than treating excursion statistics as
realized profit. Legacy canonical R fallbacks must still be audited against
exit/stop data. This is a standalone rule comparison, not an execution or
portfolio replay, and does not reconstruct which old guards would have fired.

Before activating: verify export coverage and outcome corrections, reproduce
the six issue examples, quantify winner removal by current geometry epoch, and
evaluate a separate later window without retuning 2.0 ATR. Check realized net
expectancy after execution costs as well as WR. If data are missing or the
effect is adverse/inconclusive, keep shadow mode. The issue's automatic
7-day rollback description was not verified or configured by this patch.

## Verification

```bash
python -m pytest backend/tests/test_pulse1_swing_high_filter.py \
  backend/tests/test_signal_gates_entry_score.py \
  backend/tests/test_shadow_gates.py backend/tests/test_shadow_overview.py -q
cd frontend && npx tsc --noEmit
```

Tests cover strict threshold boundaries, explicit unknown, missing/malformed
features, symbol/model/direction scope, shadow and blocking verdicts, disable
and fetch-error paths, existing-gate precedence, real panel HOLD/logging
consistency, canonical ambiguity, winner removal and geometry separation.
Synthetic test rows validate software behavior only; they are not historical
evidence of trading performance.

Results: the four targeted suites pass **95 tests**; `npx tsc --noEmit` and
`git diff --check` pass. Adding `test_signal_metrics.py` and
`test_signal_analytics.py` gives **123 passed, 1 failed**. The failing
`test_hourly_stopped_rows_use_canonical_fixed_stop_loss_when_stored_loss_is_inflated`
expects GDAXI loss -50.0 but receives -81.3. Running that analytics suite
against unmodified files from baseline `b2a596e` reproduces the same failure
(16 passed, 1 failed). It is outside this XAU/PULSE1 change; no unrelated
stop calculation was modified.
