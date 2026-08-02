# Project Structure — ForexSAI (Kimi Code context)

> Ported from the repo's root `/AGENTS.md` "Project Structure" and "File Size Hotspots"
> sections, with paths verified against the current tree. Kept as a separate file because it's
> long-lived scaffolding info, unlike the fast-changing flags/endpoints in `master-config.md`.

```
/Users/melihcanodacioglu/Desktop/panel/
├── backend/                    # FastAPI backend
│   ├── main.py                 # App entry point, router registry, lifespan
│   ├── config.py               # Pydantic settings (.env loader)
│   ├── requirements.txt        # Python dependencies
│   ├── railway.toml            # Railway deployment config
│   ├── Dockerfile              # Container config
│   ├── routers/                 # API endpoints
│   │   ├── emel_pulse.py        # Main trading endpoints (EMEL + PULSE 1/2/3)
│   │   ├── learning.py          # Learning dashboard API
│   │   ├── miroshark_router.py  # MiroShark macro bias webhook/bridge
│   │   ├── bias_test_router.py  # Bias-debate test harness
│   │   ├── auth.py              # JWT authentication
│   │   ├── websocket.py         # WebSocket endpoints
│   │   └── ...
│   ├── services/                 # Business logic
│   │   ├── data_hub.py                 # Centralized market data (in-memory cache + WS broadcast)
│   │   ├── mt5_redis_client.py         # MT5 Bridge listener (pub/sub + streams)
│   │   ├── ml_prediction_service.py    # ML pipeline (LightGBM, 150+ features)
│   │   ├── background_scheduler.py     # Periodic tasks
│   │   ├── signal_lifecycle.py         # Signal tracking (2min interval)
│   │   ├── signal_gates.py             # Centralized veto/gate layer
│   │   ├── macro_data_service.py       # yfinance macro data (hourly)
│   │   ├── fakeout_service.py          # False-breakout detector runtime
│   │   ├── shadow_trade_tracker.py     # Formation + fakeout paper-trade verification
│   │   ├── bias_debate_engine.py       # Multi-agent macro bias debate
│   │   └── ...
│   ├── database/
│   │   └── supabase_client.py
│   ├── models/                  # ML model files (.joblib)
│   ├── research/                # Offline research/mining scripts (fakeout_lab.py, etc.)
│   ├── scripts/                  # evolution_session_log.py and other one-off scripts
│   └── data/                     # Static rule files (fakeout_rules*.json), evolution panel state
│
├── frontend/                   # Next.js frontend
│   ├── src/app/                 # App Router
│   │   ├── page.tsx              # Dashboard (symbol cards)
│   │   ├── dashboard/[symbol]/   # Per-symbol page
│   │   ├── layout.tsx
│   │   └── providers.tsx
│   ├── src/components/
│   │   ├── dashboard/            # Dashboard widgets
│   │   ├── signals/               # Signal cards and panels
│   │   ├── charts/                # Chart components (SharedChart)
│   │   └── shared/                # Shared UI (StatusBadge, DirectionIndicator, SkeletonLoader)
│   ├── src/hooks/                 # useWebSocket, useLivePrices, etc.
│   ├── src/lib/                   # Utilities
│   ├── src/services/               # API client service layer
│   ├── src/types/                  # TypeScript type definitions
│   ├── src/stores/                 # Zustand stores
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.ts
│   └── railway.toml
│
├── claude_decider/              # Autonomous evidence-based decision agent (runs on Windows box)
│   └── memory/LESSONS.md         # Accumulated lessons injected into decider prompts
├── yeni deneme/                 # Live trading bot (Windows box, MT5-connected)
├── remote_agent/                # evolution_agent.py — headless Claude Code bridge on the box
├── scripts/                      # remote.py (panel→box bridge), evolution_session_log.py
├── supabase/migrations/          # SQL migration files
├── docs/                         # SELF_LEARNING_SYSTEM_GUIDE.md, order_blocks.md, MIROSHARK_SETUP.md, etc.
└── PROJECT_CONTEXT_AI.md        # Detailed module registry
```

## File Size Hotspots (complexity indicators)

| File | Notes |
|------|-------|
| `backend/routers/emel_pulse.py` | Main trading logic — EMEL + PULSE 1/2/3 endpoints |
| `backend/services/ml_prediction_service.py` | ML pipeline, ~150 features |
| `backend/routers/learning.py` | Learning dashboard, multiple performance panels |
| `backend/services/signal_lifecycle.py` | Signal tracking, 2-minute interval loop |
| `frontend/src/app/page.tsx` | Main dashboard SPA (symbol cards only — panels live per-symbol) |

## Two-Machine Split

| Location | Runs |
|---|---|
| Mac (this repo) | Dev environment, panel backend + frontend, Kimi Code / Claude Code sessions |
| Windows box | MT5 terminal, live trading bot (`yeni deneme/`), `claude_decider/`, `remote_agent/evolution_agent.py` |

Code reaches the box only via `git push` to `main` (the box's remote agent polls every ~10
minutes and restarts the affected process). Never tell the operator to run something on the box
by hand — bridge to it with `scripts/remote.py` from this machine instead.
