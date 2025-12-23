# RTYHIIM Detector Guide

RTYHIIM is the real-time rhythm detector built on top of the rhythm engine. It evaluates dominant cycle period, regularity, and confidence to produce trade-ready signals.

## Backend Endpoint
`POST /api/rtyhiim/detect`

Response includes:
- `pattern_type`
- `dominant_period_s`
- `confidence`
- `regularity`
- `predictions`

## Frontend Panel
The **RTYHIIM Detector** panel displays:
- Pattern type
- Dominant period
- Confidence and regularity
- Buy/Sell direction
- Short-horizon predictions

## Integration with /api/run/all
The `/api/run/all` response now includes `rtyhiim` so you can combine it with ML, Order Blocks, and Claude analysis.

## Troubleshooting
- If no predictions appear, ensure the detector has enough ticks in its window.
- Adjust RTYHIIM env vars in `backend/.env` for window size and periods.
