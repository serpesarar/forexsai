# Supabase AI-Ops Readiness Audit
_Generated 2026-04-30T16:32:42.703437Z_

## 1. Tables — existence + size + freshness
| Table | Exists | Rows | Latest age (hr) | Verdict |
|---|---|---|---|---|
| `prediction_logs` | ✓ | 85312 | 0.0 | ✓ Active |
| `outcome_results` | ✓ | 60303 | ? | ✓ Active |
| `signal_checks` | ✓ | 251490 | ? | ✓ Active |
| `error_analysis` | ✓ | 7 | 879.7 | ⚠ Tiny — likely broken pipeline |
| `failure_analyses` | ✓ | 0 | ? | ⚠ EMPTY (table exists, never written) |
| `learning_feedback` | ✓ | 0 | ? | ⚠ EMPTY (table exists, never written) |
| `candle_snapshots` | ✓ | 29779 | -0.0 | ✓ Active |
| `meta_combination_stats` | ✓ | 101 | ? | ✓ Active |
| `ml_strategy_performance` | ❌ | — | — | missing — 404: {"code":"PGRST205","details":null,"hint":"Per |
| `candle_cache` | ✓ | 51195 | ? | ✓ Active |
| `cot_data` | ❌ | — | — | missing — 404: {"code":"PGRST205","details":null,"hint":"Per |
| `model_improvements` | ❌ | — | — | missing — 404: {"code":"PGRST205","details":null,"hint":"Per |
| `model_iterations` | ❌ | — | — | missing — 404: {"code":"PGRST205","details":null,"hint":"Per |
| `model_audits` | ❌ | — | — | missing — 404: {"code":"PGRST205","details":null,"hint":"Per |
| `ai_ops_proposals` | ❌ | — | — | missing — 404: {"code":"PGRST205","details":null,"hint":"Per |
| `self_improvement_log` | ❌ | — | — | missing — 404: {"code":"PGRST205","details":null,"hint":"Per |
| `training_metrics` | ❌ | — | — | missing — 404: {"code":"PGRST205","details":null,"hint":"Per |
| `feature_importance_history` | ❌ | — | — | missing — 404: {"code":"PGRST205","details":null,"hint":"Per |
| `performance_alerts` | ❌ | — | — | missing — 404: {"code":"PGRST205","details":null,"hint":"Per |

## 2. Latest sample row per active table

### `prediction_logs` latest row
```json
{
  "id": "5a6e5b46-d70f-45db-8c06-220078e9b5f9",
  "symbol": "XAUUSD",
  "model_type": "smc",
  "ml_direction": "SELL",
  "status": "active",
  "resolution_reason": null,
  "created_at": "2026-04-30T16:32:39.425136+00:00",
  "factors": {
    "source": "SMART_MONEY_ZONES",
    "session": "overlap",
    "strategy": "SMART_MONEY_ZONES",
    "target_type": "static_pips",
    "signal_reasoning": [
      "Confluence score: -64",
      "bearish OB in premium",
      "CHoCH confirms",
      "BOS confirms",
      "FVG confluence",
      "OB revisited"
    ]
  }
}
```

### `error_analysis` latest row
```json
{
  "id": "1e81a8eb-583a-4598-aeb1-70d7d228f8f2",
  "prediction_id": "30da8f7b-7512-4fcc-97c9-5c2e4d502386",
  "error_type": "stoploss_hit",
  "prediction_direction": "BUY",
  "is_fake_move": true,
  "fake_move_type": "stop_hunt",
  "analysis_status": "failed",
  "ai_analysis": {
    "error": "Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': 'Your credit balance is too low to access the Anthropic API. Please go to Plans & Billing to upgrade or purchase credits.'}, 'request_id': 'req_011CZNtHShbQDETY5gum1Qpi'}"
  }
}
```

### `candle_snapshots` latest row
```json
{
  "id": "8b02124c-397d-4ce6-ba18-4aa4d321657e",
  "prediction_id": "75291993-066c-4c75-b071-047c53676214",
  "symbol": "NDX.INDX",
  "timeframe": "5m",
  "snapshot_type": "at_prediction",
  "candle_count": 100,
  "created_at": "2026-04-30T16:32:46.076218+00:00"
}
```

## 3. prediction_logs.factors fill rate (last 30 days)
> If indicator keys (rsi, macd, adx, etc.) aren't here, the AI-ops loop
> can't analyze WHAT a model saw at decision time.

Sample: **500 rows** scanned

| Key | Present | Rate% |
|---|---|---|
| `rsi_14` | 171 | 34.2% ⚠ |
| `rsi` | 0 | 0.0% ❌ |
| `rsi_14_M30` | 0 | 0.0% ❌ |
| `macd_hist` | 0 | 0.0% ❌ |
| `macd_hist_M30` | 0 | 0.0% ❌ |
| `adx` | 171 | 34.2% ⚠ |
| `adx_14` | 0 | 0.0% ❌ |
| `volume_ratio` | 1 | 0.2% ❌ |
| `vol_ratio` | 0 | 0.0% ❌ |
| `vol_z_M30` | 0 | 0.0% ❌ |
| `trend_direction` | 0 | 0.0% ❌ |
| `regime` | 40 | 8.0% ⚠ |
| `bb_pctb` | 0 | 0.0% ❌ |
| `bb_position` | 0 | 0.0% ❌ |
| `nearest_resistance_distance` | 0 | 0.0% ❌ |
| `resistance_distance` | 0 | 0.0% ❌ |
| `nearest_support_distance` | 0 | 0.0% ❌ |
| `support_distance` | 0 | 0.0% ❌ |
| `atr_14` | 0 | 0.0% ❌ |
| `session` | 500 | 100.0% ✓ |
| `strategy` | 499 | 99.8% ✓ |

## 4. error_analysis.analysis_status breakdown
Total scanned: 7

- `failed`: 7

**⚠ 7 rows failed because Anthropic API credit balance is exhausted.**