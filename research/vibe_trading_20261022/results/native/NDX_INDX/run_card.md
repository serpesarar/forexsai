# Backtest Run Card

Generated: 2026-10-22T19:59:45.236879Z
Run directory: `/Users/melihcanodacioglu/Desktop/panel/research/vibe_trading_20261022/results/native/NDX_INDX`

## Backtest Summary
- codes: ['NDX.INDX']
- start_date: 2026-10-16
- end_date: 2026-10-20
- interval: 5m
- initial_cash: 1000000
- source: local

## Reproducibility
- config_hash: `955b92a69076f30acc21d85afd7d6c0496c4e50ea5d0f0e2c6e88187b5c6ce91`
- strategy_hash: `739f3d1d3cd49677ea55a5818fb6e82fc0741fd6317dfedf28ca1d5aff518669`

## Model provenance
- config.json: Unknown
- code/signal_engine.py: Unknown
- Training cutoff: Unknown

## Data Sources
- forexsai_local_broker_cache

## Metrics
- final_value: 1001052.2158438129
- total_return: 0.001052215843812876
- annual_return: 0.10010632679583686
- max_drawdown: -0.01378256679980393
- sharpe: 0.8614703442285275
- calmar: 7.2633
- sortino: 1.1915
- win_rate: 0.4117647058823529
- profit_loss_ratio: 1.4909
- profit_factor: 1.0436
- max_consecutive_loss: 7
- avg_holding_days: 5.7
- trade_count: 34
- benchmark_return: -0.010809
- excess_return: 0.011861
- information_ratio: 3.5727
- tracking_error: 0.296689
- benchmark_beta: -0.1486
- avg_turnover: 0.042503
- total_turnover: 34.002754
- unfilled_plan_rejections: 0
- target_change_count: 67
- rebalance_executed_bars: 0
- rebalance_executed_fills: 0
- rebalance_realized_turnover: 0.0
- rebalance_turnover_mean: 0.5
- rebalance_turnover_max: 0.5
- position_adjustment: hold
- rebalance_tolerance: 0.0
- dropped_target_adjustment_count: 0

## Structured metrics

Non-scalar metrics, which the `metrics` block cannot hold - carried so they can be inspected by key instead of only as a flattened count.

- unfilled_plan_rejections_by_symbol: {}
- by_symbol: {"NDX.INDX": {"avg_pnl": 30.95, "count": 34, "total_pnl": 1052.22, "win_rate": 0.4118}}
- by_exit_reason: {"end_of_backtest": {"count": 1, "total_pnl": 516.25}, "signal": {"count": 33, "total_pnl": 535.97}}
- dropped_target_adjustments: []

## Validation
- Not present.

## Warnings
- No strategy model provenance was recorded for config.json; writer identity is unknown.
- No strategy model provenance was recorded for code/signal_engine.py; writer identity is unknown.
- Training cutoff for unknown model is unknown; assume results may reflect what the model remembers.

## Execution records
- backtest (ok): 2026-10-22T19:59:45.186768Z → 2026-10-22T19:59:45.236723Z; args sha256 `db2f4584e69d85a56c78e2e53fd009a65374fd634aad4155cc30d3f324455c30`, result sha256 `edcf6f11f42ff9fd33f4d2a05f64700958f3f8fa544d567d0bb4ba30327b2952`

## Metric evidence
- final_value: `artifacts/metrics.csv`, column `final_value`, data row 1, sha256 `a1694df020e28d16c17aa534ee9a6a098351723b7fb668ff06f6147d0988083c`
- total_return: `artifacts/metrics.csv`, column `total_return`, data row 1, sha256 `a1694df020e28d16c17aa534ee9a6a098351723b7fb668ff06f6147d0988083c`
- annual_return: `artifacts/metrics.csv`, column `annual_return`, data row 1, sha256 `a1694df020e28d16c17aa534ee9a6a098351723b7fb668ff06f6147d0988083c`
- max_drawdown: `artifacts/metrics.csv`, column `max_drawdown`, data row 1, sha256 `a1694df020e28d16c17aa534ee9a6a098351723b7fb668ff06f6147d0988083c`
- sharpe: `artifacts/metrics.csv`, column `sharpe`, data row 1, sha256 `a1694df020e28d16c17aa534ee9a6a098351723b7fb668ff06f6147d0988083c`
- calmar: `artifacts/metrics.csv`, column `calmar`, data row 1, sha256 `a1694df020e28d16c17aa534ee9a6a098351723b7fb668ff06f6147d0988083c`
- sortino: `artifacts/metrics.csv`, column `sortino`, data row 1, sha256 `a1694df020e28d16c17aa534ee9a6a098351723b7fb668ff06f6147d0988083c`
- win_rate: `artifacts/metrics.csv`, column `win_rate`, data row 1, sha256 `a1694df020e28d16c17aa534ee9a6a098351723b7fb668ff06f6147d0988083c`
- profit_loss_ratio: `artifacts/metrics.csv`, column `profit_loss_ratio`, data row 1, sha256 `a1694df020e28d16c17aa534ee9a6a098351723b7fb668ff06f6147d0988083c`
- profit_factor: `artifacts/metrics.csv`, column `profit_factor`, data row 1, sha256 `a1694df020e28d16c17aa534ee9a6a098351723b7fb668ff06f6147d0988083c`
- max_consecutive_loss: `artifacts/metrics.csv`, column `max_consecutive_loss`, data row 1, sha256 `a1694df020e28d16c17aa534ee9a6a098351723b7fb668ff06f6147d0988083c`
- avg_holding_days: `artifacts/metrics.csv`, column `avg_holding_days`, data row 1, sha256 `a1694df020e28d16c17aa534ee9a6a098351723b7fb668ff06f6147d0988083c`
- trade_count: `artifacts/metrics.csv`, column `trade_count`, data row 1, sha256 `a1694df020e28d16c17aa534ee9a6a098351723b7fb668ff06f6147d0988083c`
- benchmark_return: `artifacts/metrics.csv`, column `benchmark_return`, data row 1, sha256 `a1694df020e28d16c17aa534ee9a6a098351723b7fb668ff06f6147d0988083c`
- excess_return: `artifacts/metrics.csv`, column `excess_return`, data row 1, sha256 `a1694df020e28d16c17aa534ee9a6a098351723b7fb668ff06f6147d0988083c`
- information_ratio: `artifacts/metrics.csv`, column `information_ratio`, data row 1, sha256 `a1694df020e28d16c17aa534ee9a6a098351723b7fb668ff06f6147d0988083c`
- tracking_error: `artifacts/metrics.csv`, column `tracking_error`, data row 1, sha256 `a1694df020e28d16c17aa534ee9a6a098351723b7fb668ff06f6147d0988083c`
- benchmark_beta: `artifacts/metrics.csv`, column `benchmark_beta`, data row 1, sha256 `a1694df020e28d16c17aa534ee9a6a098351723b7fb668ff06f6147d0988083c`
- avg_turnover: `artifacts/metrics.csv`, column `avg_turnover`, data row 1, sha256 `a1694df020e28d16c17aa534ee9a6a098351723b7fb668ff06f6147d0988083c`
- total_turnover: `artifacts/metrics.csv`, column `total_turnover`, data row 1, sha256 `a1694df020e28d16c17aa534ee9a6a098351723b7fb668ff06f6147d0988083c`
- unfilled_plan_rejections: `artifacts/metrics.csv`, column `unfilled_plan_rejections`, data row 1, sha256 `a1694df020e28d16c17aa534ee9a6a098351723b7fb668ff06f6147d0988083c`
- target_change_count: `artifacts/metrics.csv`, column `target_change_count`, data row 1, sha256 `a1694df020e28d16c17aa534ee9a6a098351723b7fb668ff06f6147d0988083c`
- rebalance_executed_bars: `artifacts/metrics.csv`, column `rebalance_executed_bars`, data row 1, sha256 `a1694df020e28d16c17aa534ee9a6a098351723b7fb668ff06f6147d0988083c`
- rebalance_executed_fills: `artifacts/metrics.csv`, column `rebalance_executed_fills`, data row 1, sha256 `a1694df020e28d16c17aa534ee9a6a098351723b7fb668ff06f6147d0988083c`
- rebalance_realized_turnover: `artifacts/metrics.csv`, column `rebalance_realized_turnover`, data row 1, sha256 `a1694df020e28d16c17aa534ee9a6a098351723b7fb668ff06f6147d0988083c`
- rebalance_turnover_mean: `artifacts/metrics.csv`, column `rebalance_turnover_mean`, data row 1, sha256 `a1694df020e28d16c17aa534ee9a6a098351723b7fb668ff06f6147d0988083c`
- rebalance_turnover_max: `artifacts/metrics.csv`, column `rebalance_turnover_max`, data row 1, sha256 `a1694df020e28d16c17aa534ee9a6a098351723b7fb668ff06f6147d0988083c`
- position_adjustment: `artifacts/metrics.csv`, column `position_adjustment`, data row 1, sha256 `a1694df020e28d16c17aa534ee9a6a098351723b7fb668ff06f6147d0988083c`
- rebalance_tolerance: `artifacts/metrics.csv`, column `rebalance_tolerance`, data row 1, sha256 `a1694df020e28d16c17aa534ee9a6a098351723b7fb668ff06f6147d0988083c`
- dropped_target_adjustment_count: `artifacts/metrics.csv`, column `dropped_target_adjustment_count`, data row 1, sha256 `a1694df020e28d16c17aa534ee9a6a098351723b7fb668ff06f6147d0988083c`

## Artifacts
- `artifacts/equity.csv` (90121 bytes, sha256 `4ae8852332687c1b343f4b600ae840425b5342f13cebe4b8de9c07afdc91ee8d`)
- `artifacts/fills.jsonl` (19442 bytes, sha256 `8250f6e7b193c152eb3583f53d973d02b0e94542412b1e7798f0d653445cf0b5`)
- `artifacts/metrics.csv` (793 bytes, sha256 `a1694df020e28d16c17aa534ee9a6a098351723b7fb668ff06f6147d0988083c`)
- `artifacts/ohlcv_NDX.INDX.csv` (51885 bytes, sha256 `4e5300dd4f27bdbb90db5d476df014d92e3c6c9c32ea153b0bd8fd128491ff24`)
- `artifacts/positions.csv` (26443 bytes, sha256 `1157bf585a6e4856ce1f2c1171b56cac5cb0aca39d862d751e5400047d9cc241`)
- `artifacts/rebalance_notes.json` (22593 bytes, sha256 `8156161ab313af7aae4ccbd2c258f28ae1bc9c60687d013eed59660c53185c51`)
- `artifacts/rebalance_notes.md` (6361 bytes, sha256 `fceea29e49410ff22cc84cf16fd8f7ff0f1668c10c4ec99613ae027c98750720`)
- `artifacts/target_positions.csv` (24119 bytes, sha256 `871ed1d1f1755bfdf1ba58c0aed92bc3c65b577e581edd65004d2bc1cc5f849b`)
- `artifacts/trades.csv` (5049 bytes, sha256 `2668cfa735384a94798d0d867b183dcc75b5313ab216d71b41674dde7e83a0da`)
- `code/signal_engine.py` (9612 bytes, sha256 `739f3d1d3cd49677ea55a5818fb6e82fc0741fd6317dfedf28ca1d5aff518669`)
- `config.json` (236 bytes, sha256 `955b92a69076f30acc21d85afd7d6c0496c4e50ea5d0f0e2c6e88187b5c6ce91`)
