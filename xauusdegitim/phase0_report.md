# XAUUSD Model — Phase 0 Diagnostic Report
_Generated 2026-04-29T00:41:39.918849+00:00 — lookback 90 days_

## 1. Current Model
- File: `/Users/melihcanodacioglu/Desktop/panel/backend/models/model_lgbm_xauusd.joblib`
- Type: Pipeline, classes=[0, 1]
- Features: 150

## 2. Live Prediction Behavior (last 90 days)
- Total XAUUSD logs: **20422** (ML-family: 2635)
- Direction distribution: {'BUY': 759, 'SELL': 1876}
- **BUY share: 28.8% / SELL share: 71.2%** → no extreme bias
- Status mix: {'active': 3, 'stopped': 1122, 'completed': 1041, 'expired': 469}
- Overall win rate (completed/resolved): **48.1%** (2163 resolved)

### Win rate by direction
- **BUY**: 37.9% (256/675)
- **SELL**: 52.8% (785/1488)

### Confidence calibration
| Bucket | Wins | Resolved | Win-Rate% |
|--------|------|----------|-----------|
| <50 | 542 | 1170 | 46.3 |
| 50-60 | 254 | 469 | 54.2 |
| 60-70 | 171 | 365 | 46.8 |
| 70-80 | 48 | 112 | 42.9 |
| 80+ | 26 | 47 | 55.3 |

### Resolution reasons
- `sl_hit`: 615
- `window_resolve_positive`: 540
- `market_closed_invalid`: 368
- `direction_flip`: 344
- `tp1_3_hit_then_sl`: 299
- `tp4_hit`: 170
- `NULL`: 167
- `window_resolve_negative`: 132

## 3. Outcome Results (MFE/MAE)
_no outcome data_

## 4. AI-Analyzed Failures (error_analysis table)
- Records: 7
- Failed direction split: {'BUY': 5, 'SELL': 2}

### Root causes (Claude-tagged)
- `unknown`: 7

### Fake move types
- `stop_hunt`: 5
- `liquidity_grab`: 2

## 5. failure_analyses (rule-based)
- Records: 0

## 6. learning_feedback active rules
- Active total: 0

## 7. candle_cache availability (for retraining)
- XAUUSD/5m: 5810
- XAUUSD/30m: 1561
- XAUUSD/1h: 3364
- range_error: 0