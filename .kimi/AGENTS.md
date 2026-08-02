# AGENTS.md — ForexSAI Trading Portal (Kimi Code)

> This file contains essential context for AI coding agents working on this project.
> **Last Updated (source AGENTS.md)**: 2026-02-27 — ported to Kimi Code format {{ KIMI_NOW }}
> **Project Type**: Full-stack AI Trading Dashboard
> **Language**: English (all code comments and documentation); operator conversation is often Turkish.
>
> This is the Kimi Code entry point for the ForexSAI project. It is a direct port of the
> project's root `AGENTS.md`, adapted to Kimi's template-variable and directory conventions.
> Nothing in the original Claude Code configuration (`/CLAUDE.md`, `/CLAUDE-REASONING.md`,
> `.claude/`) was modified to produce this file — it is a parallel, independently maintained copy.
>
> For the **deep, continuously-updated architecture reference** (data flow, signal model
> dependency graph, Supabase schema, env var catalog, gate flags, per-symbol rules), see:
> - `${KIMI_WORK_DIR}/.kimi/context/master-config.md` (ported from `/CLAUDE.md`)
> - `${KIMI_WORK_DIR}/.kimi/context/reasoning-protocols.md` (ported from `/CLAUDE-REASONING.md`)
>
> Those two files are the project's real "living memory" and change often (data flow revisions,
> new gates, new endpoints). This file covers the more stable project-scaffolding facts:
> stack, directory layout, build/test commands, conventions.

---

## Session Context

- Working directory: `${KIMI_WORK_DIR}`
- Current time: `${KIMI_NOW}`
- Project tree snapshot: `${KIMI_WORK_DIR_LS}`

---

## Project Overview

ForexSAI is an end-to-end AI-powered trading dashboard that combines ML predictions, pattern
intelligence, sentiment analysis, and Smart Money Concepts (SMC) for trading signals. It
provides real-time market analysis for NASDAQ 100 (`NDX.INDX`), Gold (`XAUUSD`), DAX 40
(`GDAXI.INDX`), and WTI Crude Oil (`USOIL.FOREX`).

### Key Features
- **Real-time Market Data**: MT5 → Redis (pub/sub + streams) → DataHub is the single source of
  truth for price/candle data (see master-config.md). Macro data (DXY/VIX/US10Y/EURUSD/USDTRY)
  comes from yfinance via `macro_data_service`, hourly.
- **ML Prediction Pipeline**: LightGBM models with 150+ technical features
  (`model_lgbm_nasdaq.joblib` for NDX+GDAXI, `model_lgbm_xauusd.joblib` for XAUUSD+USOIL)
- **Multi-timeframe Analysis**: 5m, 15m, 30m, 1h, 4h, 1d timeframes
- **6 Signal Models**: ML, PULSE 1 (algo scalp), PULSE 2 (ML+TA hybrid), PULSE 3 (MTF), EMEL
  (10-checkpoint strategic), SMC (ICT/order-block)
- **AI-Powered Analysis**: Anthropic Claude, DeepSeek, Groq, xAI, and Kimi/Moonshot (used for
  the bias-debate engine — see master-config.md `services/bias_debate_engine.py`)
- **Signal Lifecycle Tracking**: Automated TP/SL monitoring (2-minute interval loop)
- **Self-Learning System**: Tracks prediction accuracy, learning dashboards per model
- **Smart Money Concepts**: Order blocks, Fair Value Gaps (FVG), CHoCH/BOS, COT reports, whale
  tracking
- **Two-machine setup**: Mac (this repo, dev + panel backend) ↔ Windows box (MT5 terminal, live
  bot `yeni deneme/`, `claude_decider/`, `remote_agent/evolution_agent.py`). Code reaches the box
  via `git push` to `main` — the remote agent polls and restarts affected processes. Do not tell
  the operator to run commands on the box by hand; `scripts/remote.py` bridges to it from here.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  FRONTEND (Next.js 14)                         [Railway]        │
│  ├─ page.tsx (main SPA dashboard)                                │
│  ├─ Panel components (lazy-loaded, per symbol page)             │
│  ├─ WebSocketContext → real-time data                           │
│  ├─ Zustand stores (dashboard, chart, news, ML strategy)        │
│  ├─ React Query for HTTP fallback                               │
│  └─ Multi-language support (next-intl)                          │
├─────────────────────────────────────────────────────────────────┤
│  BACKEND (FastAPI)                             [Railway]        │
│  ├─ main.py (router registry, lifespan management)              │
│  ├─ DataHub (in-memory cache + WebSocket broadcast, services/data_hub.py) │
│  ├─ mt5_redis_client.py (MT5 Bridge listener: pub/sub + streams) │
│  ├─ BackgroundScheduler (periodic updates)                      │
│  ├─ ML Prediction Service (LightGBM models, 150+ features)      │
│  ├─ Signal Lifecycle (active signal tracking, 2min interval)    │
│  ├─ Signal Gates (services/signal_gates.py — centralized veto layer) │
│  └─ WebSocket broadcast                                         │
├─────────────────────────────────────────────────────────────────┤
│  DATABASE (Supabase PostgreSQL)                                 │
│  ├─ candle_cache (persistent OHLCV)                              │
│  ├─ prediction_logs (all signal tracking, entry/TP/SL/status)   │
│  ├─ signal_trajectory_snapshots (active-signal periodic snapshot; replaces deprecated signal_checks) │
│  ├─ outcome_results (resolved-signal outcome analysis)           │
│  ├─ signal_vetoes (Precision Veto Engine audit log)              │
│  ├─ daily_bias (MiroShark NASDAQ macro bias, NASDAQ-only)        │
│  ├─ cortex_episodes (CORTEX episodic memory, NASDAQ-only)        │
│  ├─ shadow_pattern_trades (shadow/paper-trade formation+fakeout verification) │
│  └─ users / pro_users (authentication)                           │
└─────────────────────────────────────────────────────────────────┘
```

See `.kimi/context/master-config.md` for the full data-flow diagram (MT5 → Redis → DataHub),
the 6-signal-model dependency map, regime→weight tables, and per-symbol EMEL weight tables —
those change often enough that they are not duplicated here.

---

## Technology Stack

### Frontend
| Category | Technology |
|----------|------------|
| Framework | Next.js 14 (App Router) |
| Language | TypeScript |
| Styling | Tailwind CSS |
| State Management | Zustand + React Query |
| Charts | Recharts, Lightweight Charts |
| Animation | Framer Motion |
| Testing | Vitest + jsdom |
| Internationalization | next-intl |

### Backend
| Category | Technology |
|----------|------------|
| Framework | FastAPI |
| Language | Python 3.11+ |
| ML/AI | LightGBM, XGBoost, scikit-learn |
| Data | Pandas, NumPy |
| Database | Supabase (PostgreSQL) |
| Cache / Bus | Redis (Railway-hosted — MT5 bridge pub/sub + streams, WebSocket broadcast cache) |
| AI APIs | Anthropic Claude, DeepSeek, Groq, xAI, Kimi/Moonshot |
| WebSocket | Native websockets library |

### Infrastructure
| Category | Technology |
|----------|------------|
| Deployment | Railway (backend + frontend), Nixpacks |
| Data source | MT5 Bridge (EA/Bot) → Redis (Railway) → DataHub (single source of truth) |
| Macro data | yfinance (DXY, VIX, US10Y, EURUSD, USDTRY), hourly |
| Container | Docker (optional, local dev) |

---

## Project Structure

```
panel/
├── backend/                    # FastAPI backend
│   ├── main.py                 # App entry point, router registry
│   ├── config.py                # Pydantic settings (.env loader)
│   ├── requirements.txt
│   ├── railway.toml
│   ├── Dockerfile
│   ├── routers/                 # API endpoints
│   │   ├── emel_pulse.py        # EMEL + PULSE 1/2/3 endpoints (main router)
│   │   ├── ml_router.py         # ML prediction endpoints
│   │   ├── data_router.py       # OHLCV/price data endpoints
│   │   ├── learning_router.py   # Performance analytics endpoints
│   │   └── ...
│   ├── services/                # Business logic
│   │   ├── data_hub.py                    # Centralized market data + WS broadcast
│   │   ├── mt5_redis_client.py            # MT5 Bridge listener
│   │   ├── ml_prediction_service.py       # LightGBM prediction + 150 features
│   │   ├── market_regime_service.py       # Regime detection (ADX + structure)
│   │   ├── signal_lifecycle.py            # Signal lifecycle (2min interval)
│   │   ├── signal_gates.py                # Centralized veto/gate layer
│   │   ├── order_block_service.py         # SMC/ICT analysis
│   │   ├── macro_data_service.py          # yfinance macro data
│   │   ├── fakeout_service.py             # Fakeout (false-breakout) radar
│   │   ├── shadow_trade_tracker.py        # Shadow/paper-trade verification
│   │   ├── bias_debate_engine.py          # Multi-agent macro bias debate
│   │   └── ...
│   ├── models/                  # ML model files (.joblib)
│   └── database/
│       └── supabase_client.py
│
├── frontend/                    # Next.js frontend
│   ├── src/app/                 # App Router pages
│   │   ├── page.tsx              # Dashboard (symbol cards)
│   │   └── dashboard/[symbol]/   # Per-symbol page
│   ├── src/components/
│   │   ├── dashboard/, signals/, charts/, shared/
│   ├── src/hooks/, src/lib/, src/services/, src/types/, src/stores/
│
├── claude_decider/              # Autonomous evidence-based decision agent (Windows box)
├── yeni deneme/                 # Live trading bot (Windows box, MT5-connected)
├── remote_agent/                # evolution_agent.py — headless Claude Code bridge on the box
├── supabase/migrations/         # SQL migration files
└── scripts/                     # Setup, test, and remote-bridge scripts (remote.py, evolution_session_log.py)
```

---

## Local Development Setup

### Prerequisites
- Python 3.11+
- Node.js 20+
- npm or yarn

### Backend
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cp backend/.env.example backend/.env   # fill in API keys
uvicorn backend.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev   # http://localhost:3000
```

---

## Build & Test Commands

```bash
# Frontend
cd frontend && npm run dev      # dev server
cd frontend && npm run build    # production build
cd frontend && npm run lint
cd frontend && npm run test     # Vitest

# CRITICAL pre-deploy check — Railway silently blocks deploy on ANY TS error:
cd frontend && npx tsc --noEmit

# Backend
uvicorn backend.main:app --reload
bash scripts/test_api.sh
curl -s http://localhost:8000/api/health | jq
```

---

## Code Style Guidelines

### Python (Backend)
- Type hints everywhere; async/await (FastAPI native)
- Docstring: Google style
- try/except + logging, never a silent fail
- Supabase: prefer batch insert/upsert
- Tests: pytest + pytest-asyncio

### TypeScript (Frontend)
- Strict mode
- Interface > Type for exported types
- Custom hooks use `use` prefix
- Functional components only (no class components)
- API calls live in the service layer, never inline in a component
- Tailwind: try a utility before writing a custom class

### General
- No magic numbers — define as constants
- Max ~50 lines per function; split if larger
- Strip debug print/console.log before considering work done

---

## Key Conventions & Rules

1. **Router imports fail closed**: if any backend router import fails, ALL routers can be
   skipped (symptom: 404 on every API). Check `/api/debug`.
2. **Frontend TypeScript**: any TS error silently blocks Railway deploy. Always run
   `npx tsc --noEmit` before pushing.
3. **DataHub is the only reader of MT5/Redis** — `data_fetcher.py` and
   `market_data_service.py` read from DataHub only, never connect to MT5/Redis directly.
4. **ML model changes** require matching feature-vector changes; models carry
   `feature_names_in_`.
5. **Signal Lifecycle** depends on `prediction_logs.status='active'` — never bulk-update
   statuses without checking lifecycle logic (2-minute interval, `signal_lifecycle.py`).
6. **Environment files**: `.env` is not committed; Railway uses dashboard env vars. The Windows
   box's `yeni deneme/config.py` is also gitignored (contains credentials) — new settings ship
   as `getattr(config, "NAME", default)`, so the default lives in code, not in the box's config.
7. **Code reaches the Windows box via `git push` to `main`** — feature branches are invisible to
   the box's remote agent (10-minute poll).
8. **Every meaningful session logs to the Evolution Panel** — see "1. KURAL" in
   `.kimi/context/master-config.md`. This is a hard project rule, not optional cleanup.

---

## Environment Variables

See `.kimi/context/master-config.md` for the full, current environment variable catalog — it is
extensive (signal gates, shadow tracker, bias debate windows, per-symbol thresholds) and changes
frequently. Critical minimum to run anything: `SUPABASE_URL`, `SUPABASE_KEY`, `REDIS_URL`.

---

## Common Issues & Solutions

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| All APIs return 404 | Router import failure | Check `/api/debug`, fix broken import |
| Prices frozen / charts stuck | MT5 Redis bridge disconnected | Check `/health/ready`, `mt5_redis_client.py` reconnect logic |
| Panel shows 'Loading...' forever | WebSocket/data hook issue | Check WS status, API response in Network tab |
| New code not on live site | TypeScript error blocking deploy | Run `npx tsc --noEmit`, fix errors |
| ML prediction ValueError | Feature count mismatch | Check model's `feature_names_in_` vs computed features |
| `market_closed_invalid` ratio spiking | Session-boundary drift in signal_lifecycle | See `signal_lifecycle.py:593` MCI gate (30min grace buffer) |
| Bot running stale code on the box | Restart deferred by open position, debt mechanism missing/broken | See "borç mekanizması" note in master-config.md — check first if this recurs |

---

## Security Considerations

1. Never commit API keys; use Railway env vars / gitignored `config.py` on the box.
2. Backend CORS is permissive in dev — tighten for anything production-sensitive.
3. JWT auth, tokens kept in memory (not localStorage).
4. Supabase RLS enabled on all tables; service role key bypasses RLS (backend only).
5. The Windows box's remote-agent protocol explicitly forbids touching live MT5 processes or
   manually opening orders — respect that boundary even when working from this side.

---

## Additional Documentation

- `/CLAUDE.md`, `/CLAUDE-REASONING.md` — Claude Code's master config (source for
  `.kimi/context/master-config.md` / `reasoning-protocols.md`)
- `/PROJECT_CONTEXT_AI.md` — ⚠️ HISTORICAL module registry (last real update 2026-02-13,
  describes the removed EODHD architecture + only 2 symbols). Carries a staleness banner.
  Do NOT source model names, data flow, or symbol list from it — use master-config.md.
  Current model names: ML, PULSE 1/2/3, EMEL, SMC, Meta, AI Panel, Claude Decider, MT5 Bot.
- `/FOREXSAI_SISTEM_DOKUMANTASYONU.md`, `/ForexSAI_Model_Dokumantasyonu.md`,
  `/ForexSAI_Teknik_Detaylar.md` — Turkish system/model documentation
- `/docs/` — self-learning system, order blocks, dashboard extensions guides
