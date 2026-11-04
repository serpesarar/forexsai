# Offline audit data contract

## Inputs

`--trades` is a JSON list. Each row needs `pid`, `direction` (`BUY` or `SELL`), `entry_time` and `exit_time` as ISO-8601 UTC timestamps, `entry_px`, `exit_px`, and actual `pnl`. Optional fields: `lot`, `sl_dist`, `tp_px`, `sl_px`, `strategy_tag`, `cohort`, and **exact pre-entry `risk_cash`**. The script uses actual PnL sign for win rate and treats zero PnL as neutral. It calculates realized R from `risk_cash` if present. Alternatively, an explicitly verified `sl_dist_verified: true` plus `sl_dist`, `lot`, and `--point-value` allows R calculation. Point value is account currency per one price point per one lot; verify it for each instrument. A missing or inferred stop makes R unavailable, never zero.

`--trades` may also be an MT5 deal export CSV (`box_export_trades_30d.py` columns: `position_id,direction,volume,open_time_utc,open_price,close_time_utc,close_price,sl_price,tp_price,profit,commission,swap,comment_in,...`). PnL is net of commission and swap. Its `sl_price` is the stop at close and may have been moved by breakeven/runner management, so it is never used as pre-entry risk. `--since` drops trades entered before a UTC timestamp for forward-period validation.

`--bars` is a CSV with `ts,open,high,low,close` (or MT5 export `time_utc` ISO bar-start instead of `ts`). `ts` is Unix UTC seconds at the **start** of a one-minute bar. The script uses only bars closed before entry and rejects windows with a stale latest bar or a gap greater than five minutes. Do not pass broker-local timestamps as UTC. The chart uses bars through exit, but decision features use only pre-entry bars.

The provided NDX pilot files cover June 15–July 9, 2026. They are a subset of executed trades; no WAIT or rejected opportunities are present. `research/trade_mgmt_ndx/build_dataset.py` inferred the untriggered stop/target side, so the pilot does **not** treat its stop distance as verified pre-entry risk and reports no R. `research/trade_mgmt_ndx/per_trade.json` is replay output, not the actual fill record, and should not be silently substituted for actual PnL.

## Outputs and interpretation

- `report.md`: cohort coverage, baseline, predefined confluence filters, chronological 70/30 split, and caveats.
- `summary.json`: machine-readable counts, split boundary, metrics, and chart selections.
- `trade_examples.png`: the first eligible win and loss by time, with 1m price path and decision-time context. These are selected chronologically, not for favorable appearance.

The predefined indicators are EMA20/EMA50 trend alignment, five-bar momentum alignment, and price versus EMA20. A score of three means all agree with trade direction; this is a descriptive confluence measure, not proof of a profitable strategy. Rules shown in the report are frozen in code before the final-period calculation; do not tune them on the final period and reuse it as OOS. The Wilson interval assumes independent Bernoulli trades and may be optimistic for clustered positions. A displayed 70% observed rate is not a guarantee of 70% future accuracy.

To promote a candidate, gather a later untouched period and the missing opportunity set, verify execution cost and one-position sequencing, then use the relevant `backend/research/go_live_gate.py` or `entry_gate_live_validation.py` card. Keep a record of all variants tested for multiple-testing review.
