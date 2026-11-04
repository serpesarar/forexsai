# Backtest Run Card

Generated: 2026-10-22T19:59:45.378678Z
Run directory: `/Users/melihcanodacioglu/Desktop/panel/research/vibe_trading_20261022/results/native/XAUUSD`

## Backtest Summary
- codes: ['XAUUSD']
- start_date: 2026-10-16
- end_date: 2026-10-20
- interval: 5m
- initial_cash: 1000000
- source: local

## Reproducibility
- config_hash: `c4099f71713096ae6d20e8b8b46ff21bd69646b995cf0b23fcbdf217b303a783`
- strategy_hash: `739f3d1d3cd49677ea55a5818fb6e82fc0741fd6317dfedf28ca1d5aff518669`

## Model provenance
- config.json: Unknown
- code/signal_engine.py: Unknown
- Training cutoff: Unknown

## Data Sources
- forexsai_local_broker_cache

## Metrics
- final_value: 988148.5064888404
- total_return: -0.01185149351115955
- annual_return: -0.6609438163726109
- max_drawdown: -0.013052311363015465
- sharpe: -15.23050550144069
- calmar: -50.6381
- sortino: -19.7581
- win_rate: 0.2916666666666667
- profit_loss_ratio: 1.0788
- profit_factor: 0.4442
- max_consecutive_loss: 4
- avg_holding_days: 6.6
- trade_count: 24
- benchmark_return: -0.005527
- excess_return: -0.006325
- information_ratio: -2.8644
- tracking_error: 0.207005
- benchmark_beta: -0.0673
- avg_turnover: 0.030005
- total_turnover: 24.003927
- unfilled_plan_rejections: 0
- target_change_count: 48
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
- by_symbol: {"XAUUSD": {"avg_pnl": -493.81, "count": 24, "total_pnl": -11851.49, "win_rate": 0.2917}}
- by_exit_reason: {"signal": {"count": 24, "total_pnl": -11851.49}}
- dropped_target_adjustments: []

## Validation
- Not present.

## Warnings
- No strategy model provenance was recorded for config.json; writer identity is unknown.
- No strategy model provenance was recorded for code/signal_engine.py; writer identity is unknown.
- Training cutoff for unknown model is unknown; assume results may reflect what the model remembers.

## Execution records
- backtest (ok): 2026-10-22T19:59:45.335586Z → 2026-10-22T19:59:45.378515Z; args sha256 `70af82060a595aea418bab3ed52fd47c529c012daf442d35fd69fd207d561cb5`, result sha256 `77f999edc5dc70e33171c5286def45056087c3527c1fc4562117e8e90ba5f710`

## Metric evidence
- final_value: `artifacts/metrics.csv`, column `final_value`, data row 1, sha256 `ff49e895c378efbb09c079883946f7978d90252f036b4f71d944264d1c600945`
- total_return: `artifacts/metrics.csv`, column `total_return`, data row 1, sha256 `ff49e895c378efbb09c079883946f7978d90252f036b4f71d944264d1c600945`
- annual_return: `artifacts/metrics.csv`, column `annual_return`, data row 1, sha256 `ff49e895c378efbb09c079883946f7978d90252f036b4f71d944264d1c600945`
- max_drawdown: `artifacts/metrics.csv`, column `max_drawdown`, data row 1, sha256 `ff49e895c378efbb09c079883946f7978d90252f036b4f71d944264d1c600945`
- sharpe: `artifacts/metrics.csv`, column `sharpe`, data row 1, sha256 `ff49e895c378efbb09c079883946f7978d90252f036b4f71d944264d1c600945`
- calmar: `artifacts/metrics.csv`, column `calmar`, data row 1, sha256 `ff49e895c378efbb09c079883946f7978d90252f036b4f71d944264d1c600945`
- sortino: `artifacts/metrics.csv`, column `sortino`, data row 1, sha256 `ff49e895c378efbb09c079883946f7978d90252f036b4f71d944264d1c600945`
- win_rate: `artifacts/metrics.csv`, column `win_rate`, data row 1, sha256 `ff49e895c378efbb09c079883946f7978d90252f036b4f71d944264d1c600945`
- profit_loss_ratio: `artifacts/metrics.csv`, column `profit_loss_ratio`, data row 1, sha256 `ff49e895c378efbb09c079883946f7978d90252f036b4f71d944264d1c600945`
- profit_factor: `artifacts/metrics.csv`, column `profit_factor`, data row 1, sha256 `ff49e895c378efbb09c079883946f7978d90252f036b4f71d944264d1c600945`
- max_consecutive_loss: `artifacts/metrics.csv`, column `max_consecutive_loss`, data row 1, sha256 `ff49e895c378efbb09c079883946f7978d90252f036b4f71d944264d1c600945`
- avg_holding_days: `artifacts/metrics.csv`, column `avg_holding_days`, data row 1, sha256 `ff49e895c378efbb09c079883946f7978d90252f036b4f71d944264d1c600945`
- trade_count: `artifacts/metrics.csv`, column `trade_count`, data row 1, sha256 `ff49e895c378efbb09c079883946f7978d90252f036b4f71d944264d1c600945`
- benchmark_return: `artifacts/metrics.csv`, column `benchmark_return`, data row 1, sha256 `ff49e895c378efbb09c079883946f7978d90252f036b4f71d944264d1c600945`
- excess_return: `artifacts/metrics.csv`, column `excess_return`, data row 1, sha256 `ff49e895c378efbb09c079883946f7978d90252f036b4f71d944264d1c600945`
- information_ratio: `artifacts/metrics.csv`, column `information_ratio`, data row 1, sha256 `ff49e895c378efbb09c079883946f7978d90252f036b4f71d944264d1c600945`
- tracking_error: `artifacts/metrics.csv`, column `tracking_error`, data row 1, sha256 `ff49e895c378efbb09c079883946f7978d90252f036b4f71d944264d1c600945`
- benchmark_beta: `artifacts/metrics.csv`, column `benchmark_beta`, data row 1, sha256 `ff49e895c378efbb09c079883946f7978d90252f036b4f71d944264d1c600945`
- avg_turnover: `artifacts/metrics.csv`, column `avg_turnover`, data row 1, sha256 `ff49e895c378efbb09c079883946f7978d90252f036b4f71d944264d1c600945`
- total_turnover: `artifacts/metrics.csv`, column `total_turnover`, data row 1, sha256 `ff49e895c378efbb09c079883946f7978d90252f036b4f71d944264d1c600945`
- unfilled_plan_rejections: `artifacts/metrics.csv`, column `unfilled_plan_rejections`, data row 1, sha256 `ff49e895c378efbb09c079883946f7978d90252f036b4f71d944264d1c600945`
- target_change_count: `artifacts/metrics.csv`, column `target_change_count`, data row 1, sha256 `ff49e895c378efbb09c079883946f7978d90252f036b4f71d944264d1c600945`
- rebalance_executed_bars: `artifacts/metrics.csv`, column `rebalance_executed_bars`, data row 1, sha256 `ff49e895c378efbb09c079883946f7978d90252f036b4f71d944264d1c600945`
- rebalance_executed_fills: `artifacts/metrics.csv`, column `rebalance_executed_fills`, data row 1, sha256 `ff49e895c378efbb09c079883946f7978d90252f036b4f71d944264d1c600945`
- rebalance_realized_turnover: `artifacts/metrics.csv`, column `rebalance_realized_turnover`, data row 1, sha256 `ff49e895c378efbb09c079883946f7978d90252f036b4f71d944264d1c600945`
- rebalance_turnover_mean: `artifacts/metrics.csv`, column `rebalance_turnover_mean`, data row 1, sha256 `ff49e895c378efbb09c079883946f7978d90252f036b4f71d944264d1c600945`
- rebalance_turnover_max: `artifacts/metrics.csv`, column `rebalance_turnover_max`, data row 1, sha256 `ff49e895c378efbb09c079883946f7978d90252f036b4f71d944264d1c600945`
- position_adjustment: `artifacts/metrics.csv`, column `position_adjustment`, data row 1, sha256 `ff49e895c378efbb09c079883946f7978d90252f036b4f71d944264d1c600945`
- rebalance_tolerance: `artifacts/metrics.csv`, column `rebalance_tolerance`, data row 1, sha256 `ff49e895c378efbb09c079883946f7978d90252f036b4f71d944264d1c600945`
- dropped_target_adjustment_count: `artifacts/metrics.csv`, column `dropped_target_adjustment_count`, data row 1, sha256 `ff49e895c378efbb09c079883946f7978d90252f036b4f71d944264d1c600945`

## Artifacts
- `artifacts/equity.csv` (90597 bytes, sha256 `09ba74312b190c4117a74973e1b7615c22e719a4873f7d40f85ce03dc425fd42`)
- `artifacts/fills.jsonl` (13521 bytes, sha256 `9ada97476004c5fb6730917d9f5e09cbedadce7f836b074f05aa7f0571248968`)
- `artifacts/metrics.csv` (799 bytes, sha256 `ff49e895c378efbb09c079883946f7978d90252f036b4f71d944264d1c600945`)
- `artifacts/ohlcv_XAUUSD.csv` (51627 bytes, sha256 `989f2889be2debfaa97ccba5fa70eb2ff4aab1fce791d965fc5951104260403b`)
- `artifacts/positions.csv` (26027 bytes, sha256 `449307cd6669dfe6a7721d8c893ceaf0087bb14745b37049a0db35f2f9a73f39`)
- `artifacts/rebalance_notes.json` (16091 bytes, sha256 `fc256904eabec55faa33d42f9c5cb0a8c862a20af6641eececb643fab168bee4`)
- `artifacts/rebalance_notes.md` (4433 bytes, sha256 `1d5474372ad9ecbcbfaafc8e6e0e01f80fc34c07138a846fd4532544e2dcb3ae`)
- `artifacts/target_positions.csv` (24127 bytes, sha256 `5ddd637f9e9688775dafc0ed734e9a8cf1c8573928b53212799f713df4cad3cd`)
- `artifacts/trades.csv` (3548 bytes, sha256 `2dd34a98654ca3190b020f6c717c37ce0e5ea110903664c8e6c1acdf65e474ed`)
- `code/signal_engine.py` (9612 bytes, sha256 `739f3d1d3cd49677ea55a5818fb6e82fc0741fd6317dfedf28ca1d5aff518669`)
- `config.json` (234 bytes, sha256 `c4099f71713096ae6d20e8b8b46ff21bd69646b995cf0b23fcbdf217b303a783`)
