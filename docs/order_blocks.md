# Order Block Detector (SMC) Integration Guide

## Overview
The Order Block Detector adds Smart Money Concepts (SMC) to the AI Trading Dashboard. It identifies bullish/bearish order blocks, validates displacement and structure breaks, and surfaces entry signals with risk/reward metrics.

## Backend Setup
1. Add API keys to `backend/.env` if needed.
2. Start backend:

```bash
cd backend
python main.py
```

### Endpoints
- `POST /api/order-blocks/detect`
- `POST /api/order-blocks/check-entry`
- `POST /api/order-blocks/backtest`

### Example Request
```json
{
  "symbol": "NDX.INDX",
  "timeframe": "5m",
  "limit": 500,
  "config": {
    "fractal_period": 2,
    "min_displacement_atr": 1.0,
    "min_score": 50.0,
    "zone_type": "wick",
    "max_tests": 2
  }
}
```

## Frontend Usage
1. Start frontend:

```bash
cd frontend
npm run dev
```

2. Open the dashboard and use the **Order Block Detector** panel:
   - Select timeframe
   - Tune settings (fractal period, displacement ATR, min score)
   - Click **Scan Order Blocks**

## Combining Signals
The detector returns a `combined_signal` in the detect response. Example reasoning:
- ML model signal
- Order block validation
- Claude pattern alignment
- Market sentiment

Use the combined signal to gate trades alongside rhythm and pattern modules.

## Configuration
Backend settings (optional):

```
OB_FRACTAL_PERIOD=2
OB_MIN_DISPLACEMENT_ATR=1.0
OB_MIN_SCORE=50.0
OB_ZONE_TYPE=wick
OB_MAX_TESTS=2
```

Frontend settings are stored in `localStorage` and can be reset in the panel.

## Troubleshooting
- **No order blocks**: ensure `limit >= 50`, lower `min_score`.
- **Slow scans**: reduce `limit` to 200-300.
- **Missing data**: check the data feed for valid candles.

## SMC Concepts (Quick Primer)
- **Order Block**: The last up/down candle before a strong move.
- **BOS (Break of Structure)**: Price breaks prior swing.
- **CHoCH (Change of Character)**: Early shift in structure.
- **FVG (Fair Value Gap)**: Price inefficiency zone.
- **Premium/Discount**: Relative position in range.

## Testing
Backend:
```bash
pytest tests/test_order_blocks.py
```

Frontend:
```bash
cd frontend
npm run test
```
