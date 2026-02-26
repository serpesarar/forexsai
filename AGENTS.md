# AGENTS.md — ForexSAI Trading Portal

> This file contains essential context for AI coding agents working on this project.  
> **Last Updated**: 2026-02-25  
> **Project Type**: Full-stack AI Trading Dashboard  
> **Language**: English (all code comments and documentation)

---

## Project Overview

ForexSAI is an end-to-end trading dashboard that combines ML signals, Claude pattern intelligence, sentiment analysis, and SMC (Smart Money Concepts) style order blocks. It provides real-time trading signals and analysis for NASDAQ (NDX.INDX) and Gold (XAUUSD).

### Key Features
- **Real-time Market Data**: EODHD WebSocket integration for live prices
- **ML Prediction Pipeline**: LightGBM models with 150+ technical features
- **Multi-timeframe Analysis**: 5m, 15m, 30m, 1h, 4h, 1d timeframes
- **AI-Powered Analysis**: Anthropic Claude, DeepSeek, Groq, xAI integrations
- **Signal Lifecycle Tracking**: Automated TP/SL monitoring with failure autopsies
- **Learning System**: Self-improving prediction accuracy tracking

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  FRONTEND (Next.js 14)                         [Railway]        │
│  ├─ page.tsx (main SPA dashboard, ~64KB)                        │
│  ├─ 15+ Panel components (lazy-loaded)                          │
│  ├─ WebSocketContext → real-time data                           │
│  ├─ Zustand stores (dashboard, chart, news, ML strategy)        │
│  └─ React Query for HTTP fallback                               │
├─────────────────────────────────────────────────────────────────┤
│  BACKEND (FastAPI)                             [Railway]        │
│  ├─ main.py (28 routers, lifespan management)                   │
│  ├─ DataHub (centralized EODHD data pump)                       │
│  ├─ BackgroundScheduler (periodic updates)                      │
│  ├─ ML Prediction Service (LightGBM models)                     │
│  ├─ Signal Lifecycle (active signal tracking)                   │
│  ├─ Trading Engine (16 sub-modules)                             │
│  └─ WebSocket broadcast (/ws/all)                               │
├─────────────────────────────────────────────────────────────────┤
│  DATABASE (Supabase PostgreSQL)                                 │
│  ├─ candle_cache (persistent OHLCV)                             │
│  ├─ prediction_logs (signal tracking)                           │
│  ├─ signal_checks (lifecycle pings)                             │
│  ├─ failure_autopsies (post-mortem analysis)                    │
│  ├─ users / pro_users (authentication)                          │
│  └─ scheduler_state (job timestamps)                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

### Frontend
| Category | Technology |
|----------|------------|
| Framework | Next.js 14 (App Router) |
| Language | TypeScript 5.5 |
| Styling | Tailwind CSS 3.4 |
| State Management | Zustand 4.5 + React Query 5.51 |
| Charts | Recharts 2.12, Lightweight Charts 4.2 |
| Animation | Framer Motion |
| Testing | Vitest 2.0 |
| UI Components | Custom (no shadcn/ui) |

### Backend
| Category | Technology |
|----------|------------|
| Framework | FastAPI 0.111 |
| Language | Python 3.11+ |
| ML/AI | LightGBM 4.3, XGBoost 2.0, scikit-learn 1.5 |
| Data | Pandas 2.2, NumPy 1.26 |
| Database | Supabase (PostgreSQL) |
| Cache | Redis (optional, memory fallback) |
| AI APIs | Anthropic, DeepSeek, Groq, xAI, OpenAI |

### Infrastructure
| Category | Technology |
|----------|------------|
| Deployment | Railway (Nixpacks) |
| Frontend URL | https://upbeat-flow-production.up.railway.app |
| API/WebSocket | Same domain (wss:// for WebSocket) |
| Container | Docker (optional, local dev) |

---

## Project Structure

```
/Users/melihcanodacioglu/Desktop/panel/
├── backend/                    # FastAPI backend
│   ├── main.py                 # App entry point, 28 routers
│   ├── config.py               # Pydantic settings (.env loader)
│   ├── requirements.txt        # Python dependencies
│   ├── railway.toml            # Railway deployment config
│   ├── Dockerfile              # Container config
│   ├── routers/                # API endpoints (34 files)
│   │   ├── emel_pulse.py       # Main trading endpoints (103KB!)
│   │   ├── clear_trend.py      # Clear trend analysis
│   │   ├── learning.py         # Learning dashboard API (57KB)
│   │   ├── auth.py             # JWT authentication
│   │   └── ...
│   ├── services/               # Business logic (59 files)
│   │   ├── data_hub.py         # Centralized market data
│   │   ├── ml_prediction_service.py  # ML pipeline (102KB)
│   │   ├── background_scheduler.py   # Periodic tasks
│   │   ├── signal_lifecycle.py       # Signal tracking
│   │   └── trading_engine/     # 16 sub-modules
│   ├── database/               # Database clients
│   ├── models/                 # ML model files (.joblib, .pkl)
│   └── utils/                  # Shared utilities
│
├── frontend/                   # Next.js frontend
│   ├── app/                    # App Router
│   │   ├── page.tsx            # Main dashboard (64KB!)
│   │   ├── layout.tsx          # Root layout
│   │   ├── globals.css         # Global styles
│   │   └── (auth)/, (public)/  # Route groups
│   ├── components/             # React components (79 files)
│   │   ├── panels/             # Dashboard panels (20 files)
│   │   │   ├── ClearTrendPanelV3.tsx
│   │   │   ├── EmelPanel.tsx
│   │   │   ├── PulsePanel.tsx
│   │   │   └── ...
│   │   └── *.tsx               # Other components
│   ├── hooks/                  # Custom hooks (8 files)
│   ├── contexts/               # React contexts
│   ├── lib/                    # Utilities, stores
│   ├── package.json            # NPM dependencies
│   ├── next.config.js          # Next.js config
│   ├── tailwind.config.ts      # Tailwind config
│   ├── vitest.config.ts        # Test config
│   └── railway.toml            # Railway deployment config
│
├── docs/                       # Documentation
├── scripts/                    # Setup & test scripts
├── supabase/migrations/        # Database migrations
└── PROJECT_CONTEXT_AI.md       # Detailed module registry
```

---

## Local Development Setup

### Prerequisites
- Python 3.11+
- Node.js 20+
- npm or yarn

### Backend Setup
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt

# Environment variables
cp backend/.env.example backend/.env
# Edit backend/.env with your API keys

# Start development server
uvicorn backend.main:app --reload --port 8000
```

### Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Environment variables (if needed)
# NEXT_PUBLIC_API_URL defaults to localhost in dev

# Start development server
npm run dev  # Runs on http://localhost:3000
```

### Docker (Alternative)
```bash
docker-compose up --build
```

---

## Build Commands

### Frontend
```bash
cd frontend

# Development
npm run dev

# Production build
npm run build

# Start production server
npm start

# Linting
npm run lint

# Testing
npm run test  # Vitest
```

### Backend
```bash
# Development (with auto-reload)
uvicorn backend.main:app --reload

# Production (using main.py directly)
python backend/main.py

# Alternative with uvicorn
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

---

## Testing

### Backend Tests
```bash
# Run all tests
bash scripts/test_api.sh

# Manual endpoint testing
curl -s http://localhost:8000/api/health | jq
```

### Frontend Tests
```bash
cd frontend
npm run test  # Vitest with jsdom
```

### Critical Pre-Deploy Check
```bash
# ALWAYS run this before deploying to Railway!
cd frontend
npx tsc --noEmit
```
**⚠️ WARNING**: ANY TypeScript error will SILENTLY BLOCK Railway deployment!

---

## Environment Variables

### Critical (App won't work without these)
| Variable | Source | Description |
|----------|--------|-------------|
| `EODHD_API_KEY` | EODHD | Market data API key |
| `SUPABASE_URL` | Supabase | Database URL |
| `SUPABASE_KEY` | Supabase | Service role key |

### AI/ML Features (Graceful degradation)
| Variable | Source | Description |
|----------|--------|-------------|
| `ANTHROPIC_API_KEY` | Anthropic | Claude AI analysis |
| `DEEP_SEEKR1` | DeepSeek | DeepSeek analysis |
| `GROQ_API_KEY` | Groq | Groq LLM |
| `XAI_API_KEY` | xAI | xAI analysis |
| `MARKETAUX_API_KEY` | Marketaux | News API |

### Optional Features
| Variable | Description |
|----------|-------------|
| `REDIS_URL` | WebSocket broadcast cache |
| `RESEND_API_KEY` | Email service |
| `TELEGRAM_BOT_TOKEN` | Telegram notifications |
| `X_BEARER_TOKEN` | Twitter/X monitoring |

### Model Paths (Local dev only, Railway uses env)
| Variable | Default |
|----------|---------|
| `NASDAQ_MODEL_PATH` | `~/Desktop/nasdaq/models/` |
| `XAUUSD_MODEL_PATH` | `~/Desktop/xauusddata/models/` |

---

## Code Style Guidelines

### Python (Backend)
- Follow PEP 8
- Use type hints where practical
- Async/await for I/O operations
- Pydantic models for request/response validation
- Log with `logging` module, not print

### TypeScript (Frontend)
- **Strict mode is OFF** (`"strict": false` in tsconfig)
- Path alias: `@/*` maps to `./*`
- Functional components with hooks
- Zustand for global state
- React Query for server state

### CSS/Styling
- Tailwind CSS for all styling
- CSS variables for theming (see `theme.tokens.css`)
- Custom animations defined in `tailwind.config.ts`
- Glassmorphism effects: `backdrop-blur-glass`, `shadow-glass`

---

## Key Conventions & Rules

1. **Router Imports**: All 28 routers are imported in a try/except block in `main.py`. If ANY import fails, ALL routers are skipped (symptom: 404 on all APIs).

2. **Frontend TypeScript**: ANY TS error blocks Railway deployment. Always run `npx tsc --noEmit` before pushing.

3. **DataHub & Scheduler**: They share `_candle_store` and `_price_store` globals. Never modify one without considering the other.

4. **ML Model Changes**: Require matching feature vector changes in `_compute_technical_indicators()`.

5. **Panel Lazy Loading**: `page.tsx` imports panels as `lazy(() => import(...))`. Changing a panel filename requires updating the import.

6. **WebSocket Keys**: Panel keys must match between backend `ws_manager` broadcast and frontend `useWSPanelData(symbol, panelKey)`.

7. **Signal Lifecycle**: Depends on `prediction_logs` having `status='active'`. Never bulk-update statuses without checking lifecycle logic.

8. **Environment Files**: `.env` is NOT committed. Railway uses dashboard env vars.

---

## Common Issues & Solutions

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| All APIs return 404 | Router import failure | Check stderr for traceback, fix broken import |
| Prices frozen / charts stuck | DataHub pump failure | Check `/health/ready`, verify EODHD key quota |
| Panel shows 'Loading...' forever | WebSocket/data hook issue | Check WS status, API response in Network tab |
| New code not on live site | TypeScript error blocking deploy | Run `npx tsc --noEmit`, fix errors or add `// @ts-nocheck` |
| Chart not loading in Clear Trend | `chart_data` undefined | Guard: `data.chart_data?.closes?.length > 5` |
| ML prediction ValueError | Feature count mismatch | Check model vs computed features |
| Signal lifecycle not tracking | Circuit breaker triggered | Check `_price_fetch_failures`, reset after 60s |

---

## API Endpoints

### Health & Status
- `GET /` - Health check
- `GET /api/health` - Health status
- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe (checks DB)

### Trading Signals
- `GET /api/clear-trend/{symbol}` - Clear trend analysis
- `GET /api/emel/{symbol}` - EMEL 9-checkpoint analysis
- `GET /api/pulse/{symbol}` - Pulse 1 algorithmic scalp
- `GET /api/pulse-ml/{symbol}` - Pulse 2 ML hybrid
- `GET /api/pulse-v3/{symbol}` - Pulse 3 multi-TF
- `GET /api/mtf-analysis/{symbol}` - Multi-timeframe matrix

### ML & Predictions
- `POST /api/run/prediction/{symbol}` - ML prediction
- `GET /api/market-regime/{symbol}` - Market regime detection

### Data & News
- `GET /api/data/cached/{symbol}` - Cached data
- `GET /api/live-news/*` - Live news feed
- `GET /api/claude-news/*` - Claude news analysis

### Auth & User
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Current user

### WebSocket
- `wss://host/ws/all` - Real-time data stream

---

## File Size Hotspots (Complexity Indicators)

| File | Size | Notes |
|------|------|-------|
| `backend/routers/emel_pulse.py` | 104KB, 2144 lines | 5 endpoints, main trading logic |
| `backend/services/ml_prediction_service.py` | 102KB, 2252 lines | ML pipeline |
| `backend/routers/learning.py` | 57KB | Learning dashboard |
| `frontend/app/page.tsx` | 64KB, 1544 lines | Main dashboard SPA |
| `backend/services/mtf_analysis_service.py` | 59KB | MTF analysis |
| `backend/services/signal_lifecycle.py` | 42KB | Signal tracking |

---

## External Dependencies

### Data Providers
- **EODHD** (`api.eod-cloud.com`, `ws.eodhistoricaldata.com`) - Market data, WebSocket
- **Marketaux** - News sentiment

### AI Providers
- **Anthropic Claude** - Pattern analysis, news analysis
- **DeepSeek** - Analysis
- **Groq** - LLM inference
- **xAI** - Analysis

### Infrastructure
- **Railway** - Hosting
- **Supabase** - PostgreSQL database
- **Redis** - Optional cache

---

## Additional Documentation

- `PROJECT_CONTEXT_AI.md` - Detailed module registry with 40+ modules
- `docs/SELF_LEARNING_SYSTEM_GUIDE.md` - Learning system details
- `docs/dashboard_extensions.md` - Charting & news feed guide
- `docs/order_blocks.md` - SMC order block integration
- `docs/rtyhiim.md` - RTYHIIM detector guide

---

## Contact & Resources

- **Live URL**: https://upbeat-flow-production.up.railway.app
- **Deployment**: Railway dashboard
- **Database**: Supabase dashboard
