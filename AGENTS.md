# ForexSAI — Codex project instructions

This is the durable starting context for Codex in this repository, adapted from `CLAUDE.md` and `CLAUDE-REASONING.md`. The Claude files remain separate. Read the relevant section of `CODEX_PROJECT_CONTEXT.md` for deeper module and research history. Current code, migrations, and verified runtime state take precedence over dated docs. `PROJECT_CONTEXT_AI.md` is historical and does not describe today's symbols or data flow.

## Project and machines

ForexSAI is a trading analysis portal: Next.js frontend, FastAPI backend, Supabase persistence, MT5/Redis market feed, ML and rule-based signals, signal lifecycle, learning, and an Evolution panel. Canonical tradable symbols: `NDX.INDX`, `GDAXI.INDX`, `XAUUSD`, `USOIL.FOREX`. `QQQ.US` is a reference feed, not a tradable signal symbol. Older docs call oil `CL.COMM`; current code uses `USOIL.FOREX`.

The project spans this Mac and a Windows MT5 box. The box runs the terminal, live bot (`yeni deneme/`), `claude_decider/`, and `remote_agent/evolution_agent.py`. `scripts/remote.py` bridges to the box for status/diagnostics and specifically authorized remote operations. A push to `main` is picked up by its update agent and may restart affected processes. The ignored Windows `yeni deneme/config.py` contains secrets and is not distributed by Git; tracked bot defaults use `getattr(config, "NAME", default)`. Local source edits are safe to prepare; live trading, remote writes/restarts, and deployment need the user's task to authorize them.

## How to work here

- Start from this map; inspect the task's files and direct dependencies. Do not repeat a whole-repo audit for each small request.
- Read current files and preserve existing uncommitted work. Trace callers and consumers before changing a service or contract.
- For cross-layer edits, check backend router/service, frontend hook/type/component, WebSocket payload, cache, Supabase migration/RLS/index, and signal lifecycle as applicable. Update only the affected parts.
- Trading behavior and performance claims require causal timing, fresh data, realistic execution, and clear shadow/live status. Do not turn a backtest into a live strategy by default.
- Never reveal actual `.env` values or commit credentials. Do not infer live DB schema, active trades, or deployed flags from docs alone.
- Keep code comments and technical documentation in English unless an existing document or user request calls for Turkish. Explain results to this user in Turkish.
- For a meaningful product change, check `backend/scripts/evolution_session_log.py` usage and record a concise Turkish Evolution session note with changed paths; record genuinely unfinished work in its backlog. Add new services or analyses to the appropriate evolution registry. A pure Codex-instruction change does not need a trading-system note.

## Architecture map

| Concern | Main locations | Contract |
|---|---|---|
| Entry and scheduling | `backend/main.py`, `backend/services/background_scheduler.py` | Router imports, lifespan, periodic jobs |
| Market data | `backend/services/mt5_redis_client.py`, `data_hub.py`, `data_fetcher.py` | MT5 → Redis → DataHub → consumers |
| Signals | `backend/routers/emel_pulse.py`, `backend/services/ml_prediction_service.py`, `signal_gates.py`, `precision_veto_service.py` | ML, Pulse 1/2/3, EMEL, SMC, regime and veto |
| Tracking | `backend/services/prediction_logger.py`, `signal_lifecycle.py`, `backend/routers/learning.py` | Logged active signals → outcomes/performance |
| UI | `frontend/app/`, `frontend/components/`, `frontend/hooks/`, `frontend/lib/` | Next.js, WebSocket and HTTP data, state stores |
| Persistence | `supabase/migrations/`, `backend/database/` | Supabase PostgreSQL with RLS |
| Evidence | `backend/research/`, `research/`, `backend/data/evolution/` | Backtests, validation, go-live cards, backlog |

`MARKET_DATA_SOURCE=mt5_redis` is the backend config default: tradable price/candles come from MT5 via Redis (`mt5:tick`, `mt5:bar:5m`, `:1h`, `:1d`); macro data comes separately from yfinance through `macro_data_service`. `hybrid` can allow commodity Yahoo fallback. `data_fetcher.py` normally proxies DataHub. DataHub restores `candle_cache` and derives some higher timeframes. XAUUSD real 1h bars should not be overwritten by derived bars when `XAU_REAL_H1_ENABLED` is enabled. DataHub and scheduler share price/candle state; check both sides of changes.

Signals flow through regime/data → ML/Pulse/EMEL/SMC → gates/veto/ensemble → `prediction_logger` → lifecycle → Supabase and UI. `signal_trajectory_snapshots` replaced legacy `signal_checks`. Lifecycle requires `prediction_logs.status='active'`; do not bulk-change statuses without tracing it. `cot_data` is not a persistent Supabase table in the current Claude reference.

## Trading and research invariants

- A new scope or strategy needs `backend/research/go_live_gate.py` validation before `LIVE`: at least 150 resolved events, positive EV and bootstrap probability, both chronological halves, spread stress, next-M1-open plus actual-spread execution, and one-position-at-a-time performance. Panel-derived scopes need equivalent live/shadow trade validation. Keep unvalidated scopes in `SHADOW`/`RED`.
- For past decisions, use `backend/research/_bars_upto.py`: `mt5.copy_rates_from(sym, tf, date, n)` can return bars *after* `date`. MT5 bar timestamps may use broker UTC+2/+3. Normalize before labels, features, or writes; see `backend/research/candle_time_audit.py`.
- August 2026 corrected fakeout research superseded July percentages in `CLAUDE.md`: after shifted 1m labels were repaired, only NDX passed the 70/70 OOS target; other artifacts were tagged `verified_70_70=false` and the gate remained shadow. Read dated reports before citing model quality.
- CORTEX analog kNN did not show reliable directional edge in its backfill; analog injection was left off while episode capture remained. USOIL breakout moved to shadow after realistic execution showed negative EV. These are dated decisions, so verify current code and flags.
- Shadow and blocking flags in `signal_gates`, debate/fakeout gates, and bot defaults are consequential. An ignored Windows config may rely on a tracked default.
- Performance denominators must distinguish `completed`, `stopped`, `expired`, `market_closed_invalid`, and signals never logged because of HOLD, cooldown, deduplication, or staleness. Observed resolutions are not forecasts.

## Stack and validation

Frontend: Next.js 14, React, TypeScript, Tailwind, Zustand/React Query, Vitest. Actual `frontend/tsconfig.json` has `"strict": false` despite an older Claude statement. For frontend changes that could affect deployment run `cd frontend && npx tsc --noEmit`; run focused Vitest tests when behavior warrants it. Backend: FastAPI, Python 3.11+, LightGBM/XGBoost/scikit-learn, Supabase, Redis; use type hints, async I/O where suitable, logging, and focused pytest. Schema changes need a migration and consideration of RLS/indexes. ML feature changes must match saved model `feature_names_in_` and `_compute_technical_indicators()`. Router import failures can make many APIs return 404. Lazy panel imports, WebSocket keys, and HTTP response types must agree with the frontend.

## Further reference

- `.agents/skills/trade-edge-lab/SKILL.md`: use for offline trade autopsy, decision-time chart confluence, and candidate strategy validation; live gates remain subject to the existing go-live evidence standard.
- `docs/KAPI_KAYIT_DEFTERI.md`: BEFORE searching for any new gate/filter/strategy read this registry of everything already tested (results, reasons, evidence pitfalls); AFTER finishing, append your result there (see CLAUDE.md 3. KURAL).
- `CODEX_PROJECT_CONTEXT.md`: Codex's expanded architecture, decisions, change checklist, and adapted Claude command workflows.
- `CLAUDE.md`, `CLAUDE-REASONING.md`: original detail; consult only relevant sections and account for superseded claims. Do not edit them for Codex-only setup.
- `docs/CORTEX_PLAN.md`, `docs/BIAS_TEST_GUIDE.md`, `docs/order_blocks.md`, `docs/SELF_LEARNING_SYSTEM_GUIDE.md`: topic guidance.
- `backend/data/evolution/analyst_reports/` and `research/*/FINDINGS.md`: dated evidence; newer corrected findings supersede older claims.
