# Trading Dashboard

Modern, full-stack AI Trading Dashboard for NASDAQ and XAU/USD analysis. Includes ML signals, pattern engine, and Claude AI intelligence.

## Quick Start

```bash
# Terminal 1: Backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python main.py
```

```bash
# Terminal 2: Frontend
cd frontend
npm install
npm run dev
```

Open: http://localhost:3000

Backend health check: http://localhost:8000/api/health

## Environment Variables

Backend settings can be overridden via `.env`:

```
NASDAQ_MODEL_PATH=~/Desktop/nasdaq/models/
XAUUSD_MODEL_PATH=~/Desktop/xauusddata/models/
PATTERN_ENGINE_PATH=~/Desktop/video/pattern_engine_runtime.py
CLAUDE_PATTERNS_PATH=~/Desktop/trading-pattern-system/
ANTHROPIC_API_KEY=sk-ant-...
EODHD_API_KEY=...
MARKETAUX_API_KEY=...
MARKETAUX_BASE_URL=https://api.marketaux.com/v1/news/all
```

## API Documentation

Base URL: `http://localhost:8000`

### POST /api/run/all
Runs all analysis modules in parallel.

### POST /api/run/nasdaq
Returns NASDAQ ML signal.

### POST /api/run/xauusd
Returns XAU/USD ML signal.

### POST /api/run/pattern-engine
```json
{
  "last_n": 500,
  "select_top": 0.3,
  "output_selected_only": true
}
```

### POST /api/claude/analyze-patterns
```json
{
  "symbol": "NDX.INDX",
  "timeframes": ["5m", "15m", "30m", "1h", "4h", "1d"]
}
```

### POST /api/claude/analyze-sentiment
No body required.

### GET /api/health
Returns `{ "ok": true }`.

## Data Sources

- **EODHD WebSocket**: `wss://ws.eodhistoricaldata.com/ws/forex?api_token=YOUR_API_KEY`
  - Used for NASDAQ and XAU/USD live prices.
- **Marketaux**: `https://api.marketaux.com/v1/news/all`
  - Used for fundamental/news sentiment context.

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
