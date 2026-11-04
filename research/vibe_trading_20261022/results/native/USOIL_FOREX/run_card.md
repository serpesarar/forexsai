# Backtest Run Card

Generated: 2026-10-22T19:59:45.452708Z
Run directory: `/Users/melihcanodacioglu/Desktop/panel/research/vibe_trading_20261022/results/native/USOIL_FOREX`

## Backtest Summary
- codes: ['USOIL.FOREX']
- start_date: 2026-10-16
- end_date: 2026-10-20
- interval: 5m
- initial_cash: 1000000
- source: local

## Reproducibility
- config_hash: `c4d6a594d8691e52578cf4871d9d9f0ba05ee98401c7d13b1ab691fe80a93522`
- strategy_hash: `739f3d1d3cd49677ea55a5818fb6e82fc0741fd6317dfedf28ca1d5aff518669`

## Model provenance
- config.json: Unknown
- code/signal_engine.py: Unknown
- Training cutoff: Unknown

## Data Sources
- forexsai_local_broker_cache

## Metrics
- final_value: 985567.2572247679
- total_return: -0.0144327427752321
- annual_return: -0.7325650730605366
- max_drawdown: -0.0381862125855226
- sharpe: -5.455719185088544
- calmar: -19.184
- sortino: -7.4662
- win_rate: 0.38095238095238093
- profit_loss_ratio: 1.2855
- profit_factor: 0.7911
- max_consecutive_loss: 8
- avg_holding_days: 5.1
- trade_count: 42
- benchmark_return: 0.019332
- excess_return: -0.033765
- information_ratio: -7.0717
- tracking_error: 0.439262
- benchmark_beta: 0.0631
- avg_turnover: 0.052525
- total_turnover: 42.019644
- unfilled_plan_rejections: 0
- target_change_count: 84
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
- by_symbol: {"USOIL.FOREX": {"avg_pnl": -343.64, "count": 42, "total_pnl": -14432.74, "win_rate": 0.381}}
- by_exit_reason: {"signal": {"count": 42, "total_pnl": -14432.74}}
- dropped_target_adjustments: []

## Validation
- Not present.

## Warnings
- No strategy model provenance was recorded for config.json; writer identity is unknown.
- No strategy model provenance was recorded for code/signal_engine.py; writer identity is unknown.
- Training cutoff for unknown model is unknown; assume results may reflect what the model remembers.

## Execution records
- backtest (ok): 2026-10-22T19:59:45.406069Z → 2026-10-22T19:59:45.452570Z; args sha256 `183350b8dce11630c3fc7946e491a223b265d4a337c2c69f7680e31e08e4e607`, result sha256 `94ef1be78726b5db8b013e1299fd89742171caaaaa2704f1edc1420f3c067be2`

## Metric evidence
- final_value: `artifacts/metrics.csv`, column `final_value`, data row 1, sha256 `be89ae53da522fd7088cd46d4742f824a95c3e8dc89a19ba8ebc5bedfdd985e6`
- total_return: `artifacts/metrics.csv`, column `total_return`, data row 1, sha256 `be89ae53da522fd7088cd46d4742f824a95c3e8dc89a19ba8ebc5bedfdd985e6`
- annual_return: `artifacts/metrics.csv`, column `annual_return`, data row 1, sha256 `be89ae53da522fd7088cd46d4742f824a95c3e8dc89a19ba8ebc5bedfdd985e6`
- max_drawdown: `artifacts/metrics.csv`, column `max_drawdown`, data row 1, sha256 `be89ae53da522fd7088cd46d4742f824a95c3e8dc89a19ba8ebc5bedfdd985e6`
- sharpe: `artifacts/metrics.csv`, column `sharpe`, data row 1, sha256 `be89ae53da522fd7088cd46d4742f824a95c3e8dc89a19ba8ebc5bedfdd985e6`
- calmar: `artifacts/metrics.csv`, column `calmar`, data row 1, sha256 `be89ae53da522fd7088cd46d4742f824a95c3e8dc89a19ba8ebc5bedfdd985e6`
- sortino: `artifacts/metrics.csv`, column `sortino`, data row 1, sha256 `be89ae53da522fd7088cd46d4742f824a95c3e8dc89a19ba8ebc5bedfdd985e6`
- win_rate: `artifacts/metrics.csv`, column `win_rate`, data row 1, sha256 `be89ae53da522fd7088cd46d4742f824a95c3e8dc89a19ba8ebc5bedfdd985e6`
- profit_loss_ratio: `artifacts/metrics.csv`, column `profit_loss_ratio`, data row 1, sha256 `be89ae53da522fd7088cd46d4742f824a95c3e8dc89a19ba8ebc5bedfdd985e6`
- profit_factor: `artifacts/metrics.csv`, column `profit_factor`, data row 1, sha256 `be89ae53da522fd7088cd46d4742f824a95c3e8dc89a19ba8ebc5bedfdd985e6`
- max_consecutive_loss: `artifacts/metrics.csv`, column `max_consecutive_loss`, data row 1, sha256 `be89ae53da522fd7088cd46d4742f824a95c3e8dc89a19ba8ebc5bedfdd985e6`
- avg_holding_days: `artifacts/metrics.csv`, column `avg_holding_days`, data row 1, sha256 `be89ae53da522fd7088cd46d4742f824a95c3e8dc89a19ba8ebc5bedfdd985e6`
- trade_count: `artifacts/metrics.csv`, column `trade_count`, data row 1, sha256 `be89ae53da522fd7088cd46d4742f824a95c3e8dc89a19ba8ebc5bedfdd985e6`
- benchmark_return: `artifacts/metrics.csv`, column `benchmark_return`, data row 1, sha256 `be89ae53da522fd7088cd46d4742f824a95c3e8dc89a19ba8ebc5bedfdd985e6`
- excess_return: `artifacts/metrics.csv`, column `excess_return`, data row 1, sha256 `be89ae53da522fd7088cd46d4742f824a95c3e8dc89a19ba8ebc5bedfdd985e6`
- information_ratio: `artifacts/metrics.csv`, column `information_ratio`, data row 1, sha256 `be89ae53da522fd7088cd46d4742f824a95c3e8dc89a19ba8ebc5bedfdd985e6`
- tracking_error: `artifacts/metrics.csv`, column `tracking_error`, data row 1, sha256 `be89ae53da522fd7088cd46d4742f824a95c3e8dc89a19ba8ebc5bedfdd985e6`
- benchmark_beta: `artifacts/metrics.csv`, column `benchmark_beta`, data row 1, sha256 `be89ae53da522fd7088cd46d4742f824a95c3e8dc89a19ba8ebc5bedfdd985e6`
- avg_turnover: `artifacts/metrics.csv`, column `avg_turnover`, data row 1, sha256 `be89ae53da522fd7088cd46d4742f824a95c3e8dc89a19ba8ebc5bedfdd985e6`
- total_turnover: `artifacts/metrics.csv`, column `total_turnover`, data row 1, sha256 `be89ae53da522fd7088cd46d4742f824a95c3e8dc89a19ba8ebc5bedfdd985e6`
- unfilled_plan_rejections: `artifacts/metrics.csv`, column `unfilled_plan_rejections`, data row 1, sha256 `be89ae53da522fd7088cd46d4742f824a95c3e8dc89a19ba8ebc5bedfdd985e6`
- target_change_count: `artifacts/metrics.csv`, column `target_change_count`, data row 1, sha256 `be89ae53da522fd7088cd46d4742f824a95c3e8dc89a19ba8ebc5bedfdd985e6`
- rebalance_executed_bars: `artifacts/metrics.csv`, column `rebalance_executed_bars`, data row 1, sha256 `be89ae53da522fd7088cd46d4742f824a95c3e8dc89a19ba8ebc5bedfdd985e6`
- rebalance_executed_fills: `artifacts/metrics.csv`, column `rebalance_executed_fills`, data row 1, sha256 `be89ae53da522fd7088cd46d4742f824a95c3e8dc89a19ba8ebc5bedfdd985e6`
- rebalance_realized_turnover: `artifacts/metrics.csv`, column `rebalance_realized_turnover`, data row 1, sha256 `be89ae53da522fd7088cd46d4742f824a95c3e8dc89a19ba8ebc5bedfdd985e6`
- rebalance_turnover_mean: `artifacts/metrics.csv`, column `rebalance_turnover_mean`, data row 1, sha256 `be89ae53da522fd7088cd46d4742f824a95c3e8dc89a19ba8ebc5bedfdd985e6`
- rebalance_turnover_max: `artifacts/metrics.csv`, column `rebalance_turnover_max`, data row 1, sha256 `be89ae53da522fd7088cd46d4742f824a95c3e8dc89a19ba8ebc5bedfdd985e6`
- position_adjustment: `artifacts/metrics.csv`, column `position_adjustment`, data row 1, sha256 `be89ae53da522fd7088cd46d4742f824a95c3e8dc89a19ba8ebc5bedfdd985e6`
- rebalance_tolerance: `artifacts/metrics.csv`, column `rebalance_tolerance`, data row 1, sha256 `be89ae53da522fd7088cd46d4742f824a95c3e8dc89a19ba8ebc5bedfdd985e6`
- dropped_target_adjustment_count: `artifacts/metrics.csv`, column `dropped_target_adjustment_count`, data row 1, sha256 `be89ae53da522fd7088cd46d4742f824a95c3e8dc89a19ba8ebc5bedfdd985e6`

## Artifacts
- `artifacts/equity.csv` (91872 bytes, sha256 `42e3c429277cbc7e48418b7595d9062462de6816c1534f766ea9a6edfd59ee2b`)
- `artifacts/fills.jsonl` (23877 bytes, sha256 `5cdc496432b575d769c028cb8cda6493ea419fa9613488a2a26aff9ef6b7f5f8`)
- `artifacts/metrics.csv` (793 bytes, sha256 `be89ae53da522fd7088cd46d4742f824a95c3e8dc89a19ba8ebc5bedfdd985e6`)
- `artifacts/ohlcv_USOIL.FOREX.csv` (49203 bytes, sha256 `033d8708ce6b0e028da35b422528a2bfd911ab601fd2a508bdaebbbfd1071b3e`)
- `artifacts/positions.csv` (26555 bytes, sha256 `eb6fffa632a0c7aa91620af32a80ef1e5e0459a0928f952f2a61e71b641ae2d9`)
- `artifacts/rebalance_notes.json` (28729 bytes, sha256 `e03de50fec38817006c3488605fb1335589f1adfb1ed22fbd7afc7d6848cb417`)
- `artifacts/rebalance_notes.md` (8409 bytes, sha256 `4485174bc0c6befa28468c60e934b08a11ee03f155c4f9e53440a4b2229c7cc6`)
- `artifacts/target_positions.csv` (24133 bytes, sha256 `8d63222354a6f9590a87aece4430e8c2189d76741083920d8e7a20d74622ef42`)
- `artifacts/trades.csv` (6632 bytes, sha256 `9145bb3eb6b1c64b72d65b0222e380c966106bf2fb91846ab2e603cc01f298cf`)
- `code/signal_engine.py` (9612 bytes, sha256 `739f3d1d3cd49677ea55a5818fb6e82fc0741fd6317dfedf28ca1d5aff518669`)
- `config.json` (239 bytes, sha256 `c4d6a594d8691e52578cf4871d9d9f0ba05ee98401c7d13b1ab691fe80a93522`)
