# Backtest Run Card

Generated: 2026-10-22T19:59:45.309306Z
Run directory: `/Users/melihcanodacioglu/Desktop/panel/research/vibe_trading_20261022/results/native/GDAXI_INDX`

## Backtest Summary
- codes: ['GDAXI.INDX']
- start_date: 2026-10-16
- end_date: 2026-10-21
- interval: 5m
- initial_cash: 1000000
- source: local

## Reproducibility
- config_hash: `2453adcffdf469a8896c5e11870de99b3feae1c5df8b4348042c93f8a6f71558`
- strategy_hash: `739f3d1d3cd49677ea55a5818fb6e82fc0741fd6317dfedf28ca1d5aff518669`

## Model provenance
- config.json: Unknown
- code/signal_engine.py: Unknown
- Training cutoff: Unknown

## Data Sources
- forexsai_local_broker_cache

## Metrics
- final_value: 1000239.2371267688
- total_return: 0.0002392371267687654
- annual_return: 0.021938175592141063
- max_drawdown: -0.005544200886372325
- sharpe: 0.3118110359671866
- calmar: 3.957
- sortino: 0.4229
- win_rate: 0.34210526315789475
- profit_loss_ratio: 1.9501
- profit_factor: 1.0141
- max_consecutive_loss: 6
- avg_holding_days: 5.7
- trade_count: 38
- benchmark_return: -0.002165
- excess_return: 0.002404
- information_ratio: 1.1689
- tracking_error: 0.179113
- benchmark_beta: -0.0279
- avg_turnover: 0.047497
- total_turnover: 37.997702
- unfilled_plan_rejections: 0
- target_change_count: 76
- rebalance_executed_bars: 0
- rebalance_executed_fills: 0
- rebalance_realized_turnover: 0.0
- rebalance_turnover_mean: 0.5
- rebalance_turnover_max: 0.5
- position_adjustment: hold
- rebalance_tolerance: 0.0
- dropped_target_adjustment_count: 0
- risk_xray_hhi: 1.0
- risk_xray_effective_n: 1.0
- risk_xray_annualized_vol: 0.15616165414052774
- risk_xray_max_drawdown: -0.024985514234942757
- risk_xray_avg_invested: 0.012631749316206397

## Structured metrics

Non-scalar metrics, which the `metrics` block cannot hold - carried so they can be inspected by key instead of only as a flattened count.

- unfilled_plan_rejections_by_symbol: {}
- by_symbol: {"GDAXI.INDX": {"avg_pnl": 6.3, "count": 38, "total_pnl": 239.24, "win_rate": 0.3421}}
- by_exit_reason: {"signal": {"count": 38, "total_pnl": 239.24}}
- dropped_target_adjustments: []

## Validation
- Not present.

## Warnings
- No strategy model provenance was recorded for config.json; writer identity is unknown.
- No strategy model provenance was recorded for code/signal_engine.py; writer identity is unknown.
- Training cutoff for unknown model is unknown; assume results may reflect what the model remembers.

## Execution records
- backtest (ok): 2026-10-22T19:59:45.261097Z → 2026-10-22T19:59:45.309149Z; args sha256 `289f81bed7dd0e04547c8bf8994a68417e7619e0e1f130f80713e98cfd9b1392`, result sha256 `496385a1b1d820d24bdad088dbe09688a29b01d5e1edd2488f6e12278680f4ad`

## Metric evidence
- final_value: `artifacts/metrics.csv`, column `final_value`, data row 1, sha256 `a4d4be8869c48c397b71088936c509ed52675e76822764b78c01bb0d1e384c84`
- total_return: `artifacts/metrics.csv`, column `total_return`, data row 1, sha256 `a4d4be8869c48c397b71088936c509ed52675e76822764b78c01bb0d1e384c84`
- annual_return: `artifacts/metrics.csv`, column `annual_return`, data row 1, sha256 `a4d4be8869c48c397b71088936c509ed52675e76822764b78c01bb0d1e384c84`
- max_drawdown: `artifacts/metrics.csv`, column `max_drawdown`, data row 1, sha256 `a4d4be8869c48c397b71088936c509ed52675e76822764b78c01bb0d1e384c84`
- sharpe: `artifacts/metrics.csv`, column `sharpe`, data row 1, sha256 `a4d4be8869c48c397b71088936c509ed52675e76822764b78c01bb0d1e384c84`
- calmar: `artifacts/metrics.csv`, column `calmar`, data row 1, sha256 `a4d4be8869c48c397b71088936c509ed52675e76822764b78c01bb0d1e384c84`
- sortino: `artifacts/metrics.csv`, column `sortino`, data row 1, sha256 `a4d4be8869c48c397b71088936c509ed52675e76822764b78c01bb0d1e384c84`
- win_rate: `artifacts/metrics.csv`, column `win_rate`, data row 1, sha256 `a4d4be8869c48c397b71088936c509ed52675e76822764b78c01bb0d1e384c84`
- profit_loss_ratio: `artifacts/metrics.csv`, column `profit_loss_ratio`, data row 1, sha256 `a4d4be8869c48c397b71088936c509ed52675e76822764b78c01bb0d1e384c84`
- profit_factor: `artifacts/metrics.csv`, column `profit_factor`, data row 1, sha256 `a4d4be8869c48c397b71088936c509ed52675e76822764b78c01bb0d1e384c84`
- max_consecutive_loss: `artifacts/metrics.csv`, column `max_consecutive_loss`, data row 1, sha256 `a4d4be8869c48c397b71088936c509ed52675e76822764b78c01bb0d1e384c84`
- avg_holding_days: `artifacts/metrics.csv`, column `avg_holding_days`, data row 1, sha256 `a4d4be8869c48c397b71088936c509ed52675e76822764b78c01bb0d1e384c84`
- trade_count: `artifacts/metrics.csv`, column `trade_count`, data row 1, sha256 `a4d4be8869c48c397b71088936c509ed52675e76822764b78c01bb0d1e384c84`
- benchmark_return: `artifacts/metrics.csv`, column `benchmark_return`, data row 1, sha256 `a4d4be8869c48c397b71088936c509ed52675e76822764b78c01bb0d1e384c84`
- excess_return: `artifacts/metrics.csv`, column `excess_return`, data row 1, sha256 `a4d4be8869c48c397b71088936c509ed52675e76822764b78c01bb0d1e384c84`
- information_ratio: `artifacts/metrics.csv`, column `information_ratio`, data row 1, sha256 `a4d4be8869c48c397b71088936c509ed52675e76822764b78c01bb0d1e384c84`
- tracking_error: `artifacts/metrics.csv`, column `tracking_error`, data row 1, sha256 `a4d4be8869c48c397b71088936c509ed52675e76822764b78c01bb0d1e384c84`
- benchmark_beta: `artifacts/metrics.csv`, column `benchmark_beta`, data row 1, sha256 `a4d4be8869c48c397b71088936c509ed52675e76822764b78c01bb0d1e384c84`
- avg_turnover: `artifacts/metrics.csv`, column `avg_turnover`, data row 1, sha256 `a4d4be8869c48c397b71088936c509ed52675e76822764b78c01bb0d1e384c84`
- total_turnover: `artifacts/metrics.csv`, column `total_turnover`, data row 1, sha256 `a4d4be8869c48c397b71088936c509ed52675e76822764b78c01bb0d1e384c84`
- unfilled_plan_rejections: `artifacts/metrics.csv`, column `unfilled_plan_rejections`, data row 1, sha256 `a4d4be8869c48c397b71088936c509ed52675e76822764b78c01bb0d1e384c84`
- target_change_count: `artifacts/metrics.csv`, column `target_change_count`, data row 1, sha256 `a4d4be8869c48c397b71088936c509ed52675e76822764b78c01bb0d1e384c84`
- rebalance_executed_bars: `artifacts/metrics.csv`, column `rebalance_executed_bars`, data row 1, sha256 `a4d4be8869c48c397b71088936c509ed52675e76822764b78c01bb0d1e384c84`
- rebalance_executed_fills: `artifacts/metrics.csv`, column `rebalance_executed_fills`, data row 1, sha256 `a4d4be8869c48c397b71088936c509ed52675e76822764b78c01bb0d1e384c84`
- rebalance_realized_turnover: `artifacts/metrics.csv`, column `rebalance_realized_turnover`, data row 1, sha256 `a4d4be8869c48c397b71088936c509ed52675e76822764b78c01bb0d1e384c84`
- rebalance_turnover_mean: `artifacts/metrics.csv`, column `rebalance_turnover_mean`, data row 1, sha256 `a4d4be8869c48c397b71088936c509ed52675e76822764b78c01bb0d1e384c84`
- rebalance_turnover_max: `artifacts/metrics.csv`, column `rebalance_turnover_max`, data row 1, sha256 `a4d4be8869c48c397b71088936c509ed52675e76822764b78c01bb0d1e384c84`
- position_adjustment: `artifacts/metrics.csv`, column `position_adjustment`, data row 1, sha256 `a4d4be8869c48c397b71088936c509ed52675e76822764b78c01bb0d1e384c84`
- rebalance_tolerance: `artifacts/metrics.csv`, column `rebalance_tolerance`, data row 1, sha256 `a4d4be8869c48c397b71088936c509ed52675e76822764b78c01bb0d1e384c84`
- dropped_target_adjustment_count: `artifacts/metrics.csv`, column `dropped_target_adjustment_count`, data row 1, sha256 `a4d4be8869c48c397b71088936c509ed52675e76822764b78c01bb0d1e384c84`
- risk_xray_hhi: `artifacts/metrics.csv`, column `risk_xray_hhi`, data row 1, sha256 `a4d4be8869c48c397b71088936c509ed52675e76822764b78c01bb0d1e384c84`
- risk_xray_effective_n: `artifacts/metrics.csv`, column `risk_xray_effective_n`, data row 1, sha256 `a4d4be8869c48c397b71088936c509ed52675e76822764b78c01bb0d1e384c84`
- risk_xray_annualized_vol: `artifacts/metrics.csv`, column `risk_xray_annualized_vol`, data row 1, sha256 `a4d4be8869c48c397b71088936c509ed52675e76822764b78c01bb0d1e384c84`
- risk_xray_max_drawdown: `artifacts/metrics.csv`, column `risk_xray_max_drawdown`, data row 1, sha256 `a4d4be8869c48c397b71088936c509ed52675e76822764b78c01bb0d1e384c84`
- risk_xray_avg_invested: `artifacts/metrics.csv`, column `risk_xray_avg_invested`, data row 1, sha256 `a4d4be8869c48c397b71088936c509ed52675e76822764b78c01bb0d1e384c84`

## Artifacts
- `artifacts/equity.csv` (91858 bytes, sha256 `b867b60d604b27881c565f7d05281ea836c8c0ea7df06ddac0225ff3bebf48af`)
- `artifacts/fills.jsonl` (21736 bytes, sha256 `402a6799a4429e37d0f622fce4912da30f3b52328beae512f648aa4c982b7e85`)
- `artifacts/metrics.csv` (974 bytes, sha256 `a4d4be8869c48c397b71088936c509ed52675e76822764b78c01bb0d1e384c84`)
- `artifacts/ohlcv_GDAXI.INDX.csv` (51285 bytes, sha256 `58441c6ff13ea7ea790acba83b3718866479cb6c3417b5e90a877361d3c7e7b9`)
- `artifacts/positions.csv` (26577 bytes, sha256 `9369bb95d64286d401abc9ff185d716f40d2f827d5cabf4d7aa05c6b736469d2`)
- `artifacts/rebalance_notes.json` (25889 bytes, sha256 `80cfb7ab1d18e3ff1b9ef4d5d4fb9d00766bd16a28cae45281ead26b006d5fe2`)
- `artifacts/rebalance_notes.md` (7487 bytes, sha256 `3c349b86a06370626bd60e34fe285b2c0c98d66ed5460ad64d79e9c14a33d337`)
- `artifacts/risk_xray.json` (1307 bytes, sha256 `3cea8e5c97313cb2afc32307d1c4967eedf28489f05efd80b2e3aeb2d7869f04`)
- `artifacts/risk_xray.md` (296 bytes, sha256 `475ed7f9d3f08a4cceeee90ccb117ffe084860b7f819d48501e6859c447ed7fc`)
- `artifacts/target_positions.csv` (24124 bytes, sha256 `366c05ee43d9589e64c73c18cce4a9b5da6b2b4f33d2925127ae5729c886837c`)
- `artifacts/trades.csv` (5781 bytes, sha256 `34c54f2e1c069a916fc8456ed7749c36debcab892ce3d5e55dcf1167df3987f6`)
- `code/signal_engine.py` (9612 bytes, sha256 `739f3d1d3cd49677ea55a5818fb6e82fc0741fd6317dfedf28ca1d5aff518669`)
- `config.json` (238 bytes, sha256 `2453adcffdf469a8896c5e11870de99b3feae1c5df8b4348042c93f8a6f71558`)
