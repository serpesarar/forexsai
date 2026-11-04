# ForexSAI — Codex reference map

This is Codex's expanded project reference, adapted from the existing Claude Code guides. `AGENTS.md` is automatically loaded at the beginning of work. Read this file by relevant section when the task needs detail. Documentation is a map; current code, database migrations, and verified runtime state decide what is live.

## Product and topology

ForexSAI combines real-time prices, ML and rule-based signals, technical patterns, sentiment, Smart Money Concepts, macro bias, and performance learning. The frontend is a Next.js App Router app in `frontend/`; FastAPI routers and services live in `backend/`; Supabase stores candle, prediction, outcome, and learning data. Railway hosts the backend and Redis; check current deployment configuration for the frontend rather than relying on old hosting labels.

The Mac contains the project source. A separate Windows MT5 box runs the terminal, live bot in `yeni deneme/`, `claude_decider/`, and `remote_agent/evolution_agent.py`. Its update agent polls `main`; a push can cause process restarts, sometimes delayed while a bot position is open. `scripts/remote.py` provides the bridge. Its `ask` path invokes the Windows Claude Code agent; Codex can inspect status and use other operations only when the task authorizes their effects. The box's ignored `yeni deneme/config.py` contains secrets, so tracked code uses defaults for new settings.

Tradable symbols are `NDX.INDX`, `GDAXI.INDX`, `XAUUSD`, and `USOIL.FOREX`. `QQQ.US` is a Nasdaq reference feed only. Centralize alias normalization in `backend/services/data_hub.py`; UI metadata is in `frontend/lib/symbolConfig.ts`. The Claude guide maps NDX/DAX to `model_lgbm_nasdaq.joblib` and XAU/USOIL to `model_lgbm_xauusd.joblib`; inspect the active model registry and loaded artifact before model work.

## Data and decision pipeline

1. MT5 bridge publishes ticks and closed bars through Redis (`mt5:tick`, `mt5:bar:5m`, `mt5:bar:1h`, `mt5:bar:1d`). `mt5_redis_client.py` receives them. `data_hub.py` owns in-memory price and candle state, and restores `candle_cache` on startup.
2. `data_fetcher.py` and market-data consumers normally read DataHub. `macro_data_service.py` obtains DXY, VIX, US10Y, EURUSD, and USDTRY separately through yfinance. `MARKET_DATA_SOURCE=mt5_redis` is the source default in `backend/config.py`; `hybrid` can use commodity fallback.
3. Regime and feature services feed the six principal model families: ML, Pulse 1, Pulse 2, Pulse 3, EMEL, and SMC. `signal_gates.py`, precision veto, and scope policies can alter or suppress output. Meta analysis combines model and technical context.
4. `prediction_logger.py` writes eligible directional signals to `prediction_logs`. HOLD, cooldown, deduplication, session checks, and stale candles can prevent a row. `signal_lifecycle.py` watches active rows and resolves TP, SL, and expiry. Periodic trajectory data goes to `signal_trajectory_snapshots`; `signal_checks` is legacy.
5. Learning routers and the Evolution panel analyze the stored results. Displayed counts can differ from raw DB rows because of status filtering and model-specific aggregation.

For DataHub changes, account for timeframe provenance: 5m can yield 15m and 30m; 30m or a real 1h bar can yield higher bars. The real XAUUSD 1h path is controlled by `XAU_REAL_H1_ENABLED`. Do not overwrite a valid real bar with a derived one. A Redis interruption can leave present but stale cached data; preserve reconnect and freshness checks.

## Important stores and service boundaries

| Data or behavior | Main location | Note |
|---|---|---|
| OHLCV persistence | `candle_cache`, `backend/services/data_hub.py` | Verify timestamp basis and closed-bar status |
| Signal history | `prediction_logs` | Active, completed, stopped, expired, invalid are distinct |
| Signal trajectory | `signal_trajectory_snapshots` | Replaced `signal_checks` |
| Outcome learning | `outcome_results`, `backend/routers/learning.py` | Check denominator and horizon |
| Shadow evidence | `shadow_pattern_trades`, `backend/services/shadow_trade_tracker.py` | Separate from live prediction/lifecycle |
| Daily Nasdaq bias | `daily_bias`, `backend/services/daily_bias_service.py` | MiroShark input to Nasdaq veto |
| Debate testing | `bias_test_log`, `backend/services/bias_test_service.py` | Separate test harness |
| CORTEX | `cortex_episodes`, `backend/services/cortex_memory.py` | Nasdaq memory and optional analogs |
| Evolution | `backend/data/evolution/`, `frontend/app/evolution/` | Registry, backlog, notes, go-live cards |

Supabase tables use RLS. Service credentials remain backend-only. Add a migration for a new table or column and evaluate indexes, policies, writers, readers, and any backfill. Do not infer current schema from a prose guide; migrations and authorized DB inspection are better evidence. The COT service fetches and caches data in memory; the Claude guide explicitly says there is no `cot_data` table.

## Research findings that affect implementation

- **Go-live discipline:** `backend/research/go_live_gate.py` measures event volume, positive EV/bootstrap confidence, chronological stability, spread stress, next-M1-open plus actual-spread entry, and one-position-at-a-time results. A bar-only study cannot fully reconstruct a panel-derived signal; use equivalent live or shadow trade evidence.
- **Future-bar leakage:** MT5 `copy_rates_from` can return bars after the requested date. Reconstruct past decisions with `_bars_upto.py`. Features and entry price must exist at decision time. An ambiguous TP and SL hit in the same bar needs a conservative rule.
- **Broker timestamps:** MT5 `time` may be broker UTC+2/+3. An August 2026 audit corrected 315,730 shifted 1m bars, invalidating earlier fakeout lab percentages. See `backend/research/candle_time_audit.py` and the August analyst reports.
- **Fakeout:** After corrected labels, only NDX passed the 70/70 OOS target; DAX, XAU, and USOIL artifacts were below the standard and tagged `verified_70_70=false`. `resolved_observed` is an outcome, not a predictive stage. Read `backend/data/evolution/analyst_reports/candle_zaman_ekseni_onarimi_2026-08-12.md` and `fakeout_teyit_ufku_2026-08-12.md` before changing detector claims or gates.
- **CORTEX:** Backfilled Nasdaq analog kNN did not demonstrate reliable +6h/+24h direction; `CORTEX_ANALOG_INJECT` was left off while recording remained. See `research/cortex_backfill/FINDINGS.md`.
- **USOIL breakout:** Realistic M1-plus-spread validation found negative EV and the scope moved to shadow. See `backend/data/evolution/analyst_reports/usoil_breakout_denetimi_2026-08-11.md`.
- **Debate bias:** The test harness is distinct from live `daily_bias`. The Claude notes used a primary intraday horizon of 240 minutes for NDX and 60 for DAX/XAU/USOIL. Check current horizon logic before using a debate result in live gates.
- **Precision veto:** MiroShark daily-bias adjustment was Nasdaq-only. Inspect `precision_veto_service.py`, `daily_bias_service.py`, and the current `MACRO_BIAS_ENABLED` setting before extending it.

These are dated implementation decisions and research results, not statements about today's deployment or future profitability.

## Change impact guide

| Changed element | Check next |
|---|---|
| MT5 ingest/DataHub field | Redis shape, normalization, candle cache, scheduler, models, WebSocket |
| ML feature | Feature computation, saved model names/order, training, responses, logs |
| Signal gate/scope | Caller order, logger safety net, bot default, lifecycle, validation card |
| API endpoint | Router import, schema/types, auth, cache, frontend client and UI states |
| Database schema | Migration, RLS, indexes, backfill, query paths |
| Frontend panel | Lazy import, symbol map, API/WS key, responsive layout, typecheck |
| Historical experiment | Causal timing, chronological split, spread/entry, sample size |

Use this as a selection guide, not a full-audit requirement for every edit. For frontend deployment changes run `cd frontend && npx tsc --noEmit` because TypeScript errors can block release. Focused behavior checks use Vitest or pytest. Avoid broad tests, costly API calls, and production writes without a task-specific reason.

## Operational and Claude-recipe equivalents

Read `scripts/remote.py` and its help before use. Remote status/diagnostic reads can support a task; remote writes, restarts, deployments, and live trading actions need task authorization. A push to `main` is itself operationally significant. For meaningful product changes, inspect `backend/scripts/evolution_session_log.py` usage and log a concise Turkish note with changed files; put genuine unfinished work into its backlog and register new systems/analyses. A Codex instruction-only edit does not need a trading-system note.

Claude's `.claude/commands/` are task recipes, not automatic Codex commands. Interpret matching user requests as follows and read the specific recipe only if its added detail helps:

| Claude recipe | Codex interpretation |
|---|---|
| `add-feature.md` | Trace service/router/schema/frontend contract, implement and verify |
| `build-symbol-page.md` | Symbol UI with live price, chart, six model families, context, performance |
| `debug-signal.md` | Trace MT5/Redis → DataHub → model/gate → logger → lifecycle → panel |
| `signal-check.md` | Audit model endpoints, confidence, regime, and log path |
| `panel-audit.md` | Investigate funnel counts with code and authorized data |
| `daily-review.md` | Review changes, system health, and outcomes with authorized runtime data |

Leave `.claude/`, `CLAUDE.md`, and `CLAUDE-REASONING.md` untouched for Codex-only maintenance. Their dated and internally superseded claims require confirmation against current code and corrected reports.
