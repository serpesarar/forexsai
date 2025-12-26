# AI Trading Dashboard

An end-to-end trading dashboard combining ML signals, Claude pattern intelligence, sentiment analysis, and SMC-style order blocks.

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload
```

```bash
cd frontend
npm install
npm run dev
```

The frontend runs on `http://localhost:3000` and the backend on `http://localhost:8000`.

## API Endpoints

### POST /api/run/nasdaq
Runs the NASDAQ ML signal pipeline.

### POST /api/run/xauusd
Runs the XAU/USD ML signal pipeline.

### POST /api/run/pattern-engine
Runs the pattern engine.

### POST /api/claude/analyze-patterns
Claude pattern detection.

### POST /api/claude/analyze-sentiment
No body required.

### GET /api/health
Returns `{ "ok": true }`.

## Data Sources

- **EODHD WebSocket**: `wss://ws.eodhistoricaldata.com/ws/forex?api_token=YOUR_API_KEY`
  - Used for NASDAQ and XAU/USD live prices.
- **Marketaux**: `https://api.marketaux.com/v1/news/all`
  - Used for fundamental/news sentiment context.

## Dashboard Extensions

- Advanced charting + news feed guide: `docs/dashboard_extensions.md`

## Docker (Optional)

```bash
docker-compose up --build
```

## Testing

```bash
bash scripts/test_api.sh
```

## Order Block Detector (SMC)

See the integration guide: `docs/order_blocks.md`

## RTYHIIM Detector

See the integration guide: `docs/rtyhiim.md`

## E2E Checklist

1. `POST /api/run/pattern-engine` returns CSV output reference.
2. UI displays top 30 patterns with `trade_thr` column.
3. Confidence scores render as progress bars.
4. Missing model files show warning toast.
5. Mobile layout works on iPad widths.
6. `Run All` completes under 60 seconds.

## Troubleshooting

- **CORS issues**: Ensure backend runs on port `8000` and frontend on `3000`.
- **Model not found**: Verify `.env` paths to model files.
- **Claude errors**: Confirm `ANTHROPIC_API_KEY` is set.
- **Pattern engine runtime missing**: Update `PATTERN_ENGINE_PATH`.
- **EODHD WebSocket**: Set `EODHD_API_KEY` and verify your symbol subscription (e.g. `XAUUSD`).
- **Marketaux errors**: Set `MARKETAUX_API_KEY` for sentiment news ingestion.
