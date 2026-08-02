---
format_version: "1.0"
project_type: "trading_portal"
last_updated: "2026-02-13"
symbols_tracked: ["NDX.INDX", "GDAXI.INDX", "XAUUSD", "USOIL.FOREX"]
deployment: "Railway (Nixpacks)"
api_base_url: "https://upbeat-flow-production.up.railway.app"
ws_base_url: "wss://upbeat-flow-production.up.railway.app"
database: "Supabase (PostgreSQL)"
frontend_framework: "Next.js 14 (App Router)"
state_management: "Zustand + React Query"
external_data_api: "NONE — price/candle: MT5 → Redis → DataHub (own pipeline); macro: yfinance. EODHD/Tiingo/marketaux REMOVED 2026-06."
ai_apis: ["Anthropic Claude", "DeepSeek", "Groq", "xAI", "Kimi/Moonshot"]
---

# PROJECT_CONTEXT_AI — ForexSAI Trading Portal

> ⚠️ **STALENESS WARNING (added 2026-08-01):** This registry was last substantively updated
> **2026-02-13** and describes an OBSOLETE architecture. Do NOT treat its model names, data
> source, or symbol list as authoritative. Two things changed materially since:
> 1. **Data source:** the "EODHD data pump" described below NO LONGER EXISTS. Price/candle data
>    now flows **MT5 → Redis → DataHub** (the project's own bridge); macro comes from yfinance.
>    EODHD/Tiingo/marketaux were fully removed 2026-06. Ignore every `EODHD*` reference here.
> 2. **Symbols:** the system now trades **4** symbols (NDX.INDX, GDAXI.INDX, XAUUSD, USOIL.FOREX),
>    not the 2 listed in older sections.
>
> **The current source of truth is `/CLAUDE.md` (+ `.kimi/context/master-config.md`, its port).**
> Model names are exactly: **ML, PULSE 1/2/3, EMEL, SMC** (panel) + **Meta** (fusion) +
> **AI Panel** + **Claude Decider** + **MT5 Bot** (`yeni deneme/`). There is NO "Cloud Desa",
> NO "MetaBrain / Meta5", NO "Stage 4 pipeline" — if you see those anywhere, they are garbled
> legacy names. Read CLAUDE.md/master-config.md before quoting anything from this file.

## ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────────┐
│  FRONTEND (Next.js 14)                         [Railway]        │
│  ├─ page.tsx (1544 lines — main SPA dashboard)                  │
│  ├─ 15 Panel components (lazy-loaded)                           │
│  ├─ WebSocketContext → real-time data                           │
│  ├─ useCachedDashboardData → HTTP fallback                      │
│  └─ Zustand stores (dashboard, chart, news, ML strategy)        │
├─────────────────────────────────────────────────────────────────┤
│  BACKEND (FastAPI)                             [Railway]         │
│  ├─ main.py (FastAPI app, 28 routers)                           │
│  ├─ DataHub (MT5→Redis→DataHub in-memory cache; no EODHD)       │
│  ├─ BackgroundScheduler (periodic updates)                      │
│  ├─ ML Prediction Service (LightGBM models)                     │
│  ├─ Signal Lifecycle (active signal tracking)                   │
│  ├─ Trading Engine (16 sub-modules)                             │
│  └─ WebSocket broadcast (/ws/all)                               │
├─────────────────────────────────────────────────────────────────┤
│  DATABASE (Supabase)                                            │
│  ├─ candle_cache (persistent OHLCV)                             │
│  ├─ prediction_logs (signal tracking)                           │
│  ├─ signal_checks (lifecycle pings)                             │
│  ├─ failure_autopsies (post-mortem)                              │
│  ├─ users / pro_users (auth)                                    │
│  └─ scheduler_state (job timestamps)                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## MODULE_REGISTRY

### BACKEND — CORE INFRASTRUCTURE

#### MOD-001: FastAPI Application
- **file_path**: `backend/main.py`
- **purpose**: FastAPI app entrypoint; registers all 28 routers, lifespan (startup/shutdown), CORS, health checks.
- **entry_points**:
  - `lifespan()` — trigger: `auto_load` — starts DataHub, BackgroundScheduler, SignalLifecycle
  - `root()` — trigger: `api_call` — GET `/` health
  - `health_liveness()` — trigger: `api_call` — GET `/health/live`
  - `health_readiness()` — trigger: `api_call` — GET `/health/ready` (checks DB)
- **dependencies**: All routers (MOD-010–MOD-037), all services
- **known_issues**:
  - ISS-001: If any router import fails, ALL routers are skipped (try/except wraps entire block). Symptom: 404 on all API endpoints.

#### MOD-002: Configuration
- **file_path**: `backend/config.py`
- **purpose**: Pydantic settings class loading all env vars (.env file).
- **key_settings**: `eodhd_api_key`, `supabase_url`, `supabase_key`, `anthropic_api_key`, `deepseek_api_key`, `redis_url`, `TELEGRAM_BOT_TOKEN`
- **known_issues**:
  - ISS-002: Model paths default to `~/Desktop/` which only works locally, not on Railway. Railway uses env vars.

#### MOD-003: Database Client
- **file_path**: `backend/database/supabase_client.py`
- **purpose**: Supabase client initialization and connection pooling.
- **dependencies**: `supabase_url`, `supabase_key` from MOD-002

---

### BACKEND — DATA PIPELINE

#### MOD-010: DataHub (Centralized Market Data)
> ⚠️ CORRECTED 2026-08-01 — this block described the removed EODHD pump. Current reality below.
- **file_path**: `backend/services/data_hub.py`
- **purpose**: Single in-memory source of truth for all price/candle data. Fed by the MT5→Redis
  bridge listener (`services/mt5_redis_client.py`), NOT by any external HTTP data vendor.
  Persists to Supabase `candle_cache`; broadcasts to the frontend over WebSocket.
- **entry_points**:
  - `get_candles(symbol, timeframe)` — returns in-memory candles (derives 15m/30m/1h/4h)
  - `get_price(symbol)` — latest price from the MT5 tick stream
  - `ingest_live_price()` / `ingest_candles()` — called by `mt5_redis_client` on tick/bar
- **data source**: **MT5 → Redis (`mt5:tick`, `mt5:bar:5m/1h/1d`) → DataHub.** Macro
  (DXY/VIX/US10Y/EURUSD/USDTRY) is a SEPARATE service (`macro_data_service`, yfinance, hourly).
  **No EODHD / no external market-data API** (removed 2026-06).
- **data_flow**: MT5 bridge → Redis pub/sub + streams → `mt5_redis_client` → DataHub in-memory →
  Supabase `candle_cache`; `data_fetcher.py`/`market_data_service.py` read from DataHub ONLY.
- **timeframes_stored**: 5m (native), 15m/30m (derived from 5m), 1h/4h (derived; XAU from real 1h
  when available), 1d
- **symbols**: NDX.INDX, GDAXI.INDX, XAUUSD, USOIL.FOREX + macro references (DXY, VIX, US10Y) + QQQ (reference-only)
- **known_issues**:
  - If the MT5 Redis bridge disconnects, DataHub goes stale — the fix is
    `mt5_redis_client.py` reconnect logic, NOT a fallback vendor. Check `/health/ready`.
  - On Railway cold start, persistent-cache load may lag Supabase — empty charts for 2-3 min.

#### MOD-011: Background Scheduler
- **file_path**: `backend/services/background_scheduler.py`
- **purpose**: Periodic update loop — runs analysis, caches results to Supabase, checks outcomes, logs predictions.
- **entry_points**:
  - `start_scheduler()` — trigger: `auto_load` (from lifespan)
  - `background_scheduler_loop()` — trigger: `auto_load` (every 60s)
  - `run_update_cycle()` — trigger: `auto_load` — updates all symbols
  - `save_to_cache()` — trigger: `auto_load` — writes to Supabase (throttled 5min/symbol)
  - `log_predictions_if_needed()` — trigger: `auto_load` (every 30min)
  - `log_pulse_signals_if_needed()` — trigger: `auto_load` (every 30min)
- **dependencies**: MOD-010 (DataHub), MOD-020 (ML), MOD-025 (Signal Lifecycle)
- **intervals**: update_cycle=60s, news=600s, outcomes=600s, predictions=1800s, errors=3600s

#### MOD-012: WebSocket Manager
- **file_path**: `backend/services/ws_manager.py`
- **purpose**: Manages WebSocket connections, broadcasts cached data to connected clients.
- **entry_points**:
  - `broadcast()` — sends data to all connected clients
- **router**: `backend/routers/websocket.py` → `/ws/all`

---

### BACKEND — ANALYSIS & PREDICTION SERVICES

#### MOD-020: ML Prediction Service
- **file_path**: `backend/services/ml_prediction_service.py` (2252 lines)
- **purpose**: Loads LightGBM models, computes 150+ technical features, generates BUY/SELL/HOLD predictions with layered confidence.
- **entry_points**:
  - `predict(symbol)` — trigger: `api_call` — full prediction pipeline
  - `_compute_technical_indicators(closes, highs, lows, volumes)` — internal
  - `_apply_layered_confidence(base_confidence, adjustments, strategy)` — internal
  - `_should_allow_direction_change(symbol, direction, confidence, price)` — signal stability gate
- **models**:
  - `backend/models/model_lgbm_nasdaq.joblib` (5.8MB)
  - `backend/models/model_lgbm_xauusd.joblib` (4.7MB)
  - `backend/models/%80nasdaq_meta_lgb_v2.pkl` (17.8MB)
  - `backend/models/xau_meta_dir_lgbm_v2.pkl` (19.6MB)
- **dependencies**: MOD-010 (DataHub for candles), MOD-022 (Market Regime)
- **confidence_layers**: Critical (50%, harmonic), Technical (30%, geometric), Context (20%, arithmetic)
- **strategy_presets**: ultra_safe, balanced, aggressive
- **known_issues**:
  - ISS-020: Signal cooldown (15min) can suppress valid reversals. Param: `SIGNAL_COOLDOWN_MINUTES`
  - ISS-021: Feature vector mismatch if model was trained on different indicators. Symptom: ValueError on predict.

#### MOD-021: Trend Analyzer
- **file_path**: `backend/services/trend_analyzer.py` (850 lines)
- **purpose**: Multi-timeframe trend analysis with EMA alignment, fractal pivot detection, S/R clustering, RSI divergence, OBV volume confirmation.
- **entry_points**:
  - `analyze_trend(symbol)` — trigger: `api_call` — full trend analysis
  - `detect_fractal_pivots(highs, lows)` — S/R level detection
  - `cluster_sr_levels(pivots, current_price)` — groups nearby levels
  - `detect_pivot_rsi_divergence(...)` — divergence signals
  - `detect_conflicts(...)` — indicator conflict detection
- **dependencies**: MOD-010 (DataHub), MOD-024 (Technical Indicators)
- **output**: `TrendAnalysisResult` dataclass

#### MOD-022: Market Regime Service
- **file_path**: `backend/services/market_regime_service.py` (692 lines)
- **purpose**: Detects market regime using ADX + ATR + Swing Structure. Controls allowed trade directions, RSI thresholds, model weights.
- **entry_points**:
  - `detect_regime(symbol, force_refresh)` — trigger: `api_call` — cached 30min
  - `detect_order_blocks(opens, highs, lows, closes, volumes)` — ICT order blocks
- **regimes**: STRONG_TREND_UP, STRONG_TREND_DOWN, RANGING, TRANSITION
- **dependencies**: MOD-010 (DataHub for 4H/1H/EOD candles)
- **output**: `RegimeResult` dataclass with model_weights, rsi_thresholds, allowed_directions

#### MOD-023: Adaptive TP/SL
- **file_path**: `backend/services/adaptive_tp_sl.py`
- **purpose**: Dynamic multi-target take-profit and stop-loss calculation based on ATR, S/R levels, and regime.

#### MOD-024: Technical Indicators
- **file_path**: `backend/services/technical_indicators.py`
- **purpose**: Core TA functions: EMA, SMA, RSI, ATR, MACD, Bollinger, Stochastic, OBV.
- **consumers**: MOD-020, MOD-021, MOD-022, MOD-030, MOD-031

#### MOD-025: Signal Lifecycle
- **file_path**: `backend/services/signal_lifecycle.py` (1018 lines)
- **purpose**: Tracks active signals every 5min, captures wicks (session high/low), detects target hits and stop losses, creates failure autopsies with indicator snapshots.
- **entry_points**:
  - `run_lifecycle_check()` — trigger: `auto_load` (from scheduler, every 5min)
  - `_process_signal(client, signal)` — processes one active signal
  - `_create_failure_autopsy(client, signal, targets_hit, current_price)` — post-mortem
- **dependencies**: MOD-010 (DataHub prices), MOD-024 (indicators for autopsy)
- **database_tables**: `prediction_logs`, `signal_checks`, `failure_autopsies`
- **known_issues**:
  - ISS-025: Circuit breaker after 5 consecutive price fetch failures per symbol. Reset: 60s.

#### MOD-026: Outcome Tracker
- **file_path**: `backend/services/outcome_tracker.py`
- **purpose**: Evaluates prediction accuracy by comparing predicted vs actual price movement.

#### MOD-027: Error Analysis Service
- **file_path**: `backend/services/error_analysis_service.py`
- **purpose**: Analyzes failed predictions patterns, identifies systematic errors.

#### MOD-028: Prediction Logger
- **file_path**: `backend/services/prediction_logger.py`
- **purpose**: Logs ML predictions to Supabase for learning system analysis.

---

### BACKEND — TRADING ENGINE (16 Sub-Modules)

#### MOD-030: Trading Engine Core
- **file_path**: `backend/services/trading_engine/__init__.py`
- **purpose**: Orchestrates all trading engine sub-modules into a unified decision pipeline.
- **sub_modules**:
  - `constants.py` — magic numbers, thresholds
  - `helpers.py` — shared utility functions
  - `decision_layers.py` — layered decision making (critical, technical, context)
  - `confluence_engine.py` — multi-indicator confluence scoring
  - `regime_blocker.py` — blocks trades against regime
  - `regime_detector.py` — lightweight regime detection
  - `adaptive_threshold.py` — dynamic confidence thresholds
  - `mtf_analyzer.py` — multi-timeframe analysis
  - `mtf_validator.py` — cross-timeframe validation
  - `pattern_prioritizer.py` — pattern ranking by recency and strength
  - `signal_state_machine.py` — signal state transitions (SCOUT→CONFIRM→ACTIVE→COMPLETE)
  - `layer_conflict_resolver.py` — resolves conflicting layer signals
  - `learning_integration.py` — connects to error analysis for adaptive behavior
  - `portfolio_risk_manager.py` — position sizing, max exposure

---

### BACKEND — API ROUTERS

#### MOD-031: Clear Trend Router
- **file_path**: `backend/routers/clear_trend.py`
- **purpose**: Simplified trend analysis API. GET `/api/clear-trend/{symbol}?timeframe=1H`
- **entry_points**:
  - `get_clear_trend(symbol, timeframe)` — trigger: `api_call`
  - `_find_support_resistance_levels(...)` — pivot-based S/R
  - `_calculate_trend(closes, highs, lows)` — EMA+momentum trend
  - `_calculate_trade_zones(...)` — entry/target/stop
- **response_includes**: price, trend (direction, strength, %), levels (all S/R with distances), trade_zones, chart_data (closes, dates, trend_channel), explanations
- **dependencies**: MOD-010 (DataHub), MOD-024 (Technical Indicators)

#### MOD-032: EMEL + Pulse Router (LARGEST FILE: 2144 lines)
- **file_path**: `backend/routers/emel_pulse.py`
- **purpose**: Houses 5 strategic analysis endpoints — the core trading signal generators.
- **entry_points**:
  - `get_emel_analysis(symbol, timeframe)` — trigger: `api_call` — 9-checkpoint strategic analysis. GET `/api/emel/{symbol}`
  - `get_pulse_analysis(symbol, timeframe)` — trigger: `api_call` — Pulse 1 algorithmic scalp. GET `/api/pulse/{symbol}`
  - `get_pulse_ml_analysis(symbol, timeframe)` — trigger: `api_call` — Pulse 2 ML hybrid. GET `/api/pulse-ml/{symbol}`
  - `get_pulse_v3_analysis(symbol)` — trigger: `api_call` — Pulse 3 multi-TF. GET `/api/pulse-v3/{symbol}`
  - `get_market_regime(symbol)` — trigger: `api_call` — Market regime. GET `/api/market-regime/{symbol}`
  - `debug_ema_calculation(symbol, timeframe)` — trigger: `api_call` — EMA debug
- **dependencies**: MOD-010, MOD-020, MOD-021, MOD-022, MOD-024, MOD-030

#### MOD-033: Prediction Router
- **file_path**: `backend/routers/prediction.py`
- **purpose**: ML prediction endpoint. POST `/api/run/prediction/{symbol}`
- **dependencies**: MOD-020

#### MOD-034: Auth Router
- **file_path**: `backend/routers/auth.py` (17.6KB)
- **purpose**: User registration, login, JWT auth, Pro upgrades. `/api/auth/*`
- **dependencies**: MOD-003 (Supabase), `backend/services/auth_service.py`

#### MOD-035: Learning Router
- **file_path**: `backend/routers/learning.py` (57KB — VERY LARGE)
- **purpose**: Learning dashboard API — trade history analysis, pattern recognition, error analysis. `/api/learning/*`
- **dependencies**: MOD-025, MOD-027, MOD-028

#### MOD-036: Live News Router
- **file_path**: `backend/routers/live_news.py`
- **purpose**: Live news feed with sentiment analysis. `/api/live-news/*`
- **dependencies**: `live_news_monitor.py`, `gold_news_analyzer.py`

#### MOD-037: Signal Lifecycle Router
- **file_path**: `backend/routers/signal_lifecycle_router.py`
- **purpose**: Signal management API — active signals, lifecycle metrics. `/api/signals/*`
- **dependencies**: MOD-025

#### MOD-038: Claude News Router
- **file_path**: `backend/routers/claude_news.py`
- **purpose**: Claude AI news analysis. `/api/claude-news/*`
- **dependencies**: `claude_news_analyzer.py` (Anthropic API)

#### MOD-039: MTF Analysis Router
- **file_path**: `backend/routers/mtf_analysis.py`
- **purpose**: Multi-timeframe analysis. `/api/mtf-analysis/{symbol}`
- **dependencies**: `mtf_analysis_service.py`

---

### FRONTEND — PAGE & LAYOUT

#### MOD-050: Main Dashboard Page
- **file_path**: `frontend/app/page.tsx` (1544 lines — LARGEST FRONTEND FILE)
- **purpose**: Main SPA dashboard. Lazy-loads all panels, renders signal cards, market tickers, navigation.
- **entry_points**:
  - `HomePage()` — trigger: `auto_load` — renders entire dashboard
  - `fetchAll()` — trigger: `button_click` — dispatches `dashboard-refresh` event
  - `renderCardContent(cardId)` — maps card IDs to panel components
- **dependencies**: All panel components (MOD-060–MOD-074), MOD-080 (hooks), MOD-090 (stores)
- **lazy_imports** (card_id → component):
  - `"clear-trend"` → `ClearTrendPanelV3` (was ClearTrendPanel, renamed for cache bust)
  - `"signal-nasdaq"` / `"signal-xauusd"` → inline signal cards
  - `"emel"` → `EmelPanel`
  - `"pulse"` → `PulsePanel`
  - `"pulse-v3"` → `PulseV3Panel`
  - `"pulse-ml"` → `PulseMLPanel`
  - `"mtf"` → `MTFMatrixPanel`
  - `"risk-reward"` → `RiskRewardPanel`
  - `"smc"` → `SMCPanel`
  - `"seasonality"` → `SeasonalityPanel`
  - `"learning"` → `LearningDashboardV2`
  - `"cot-whale"` → `COTWhalePanel`
  - `"ml-prediction"` → `MLPredictionPanel`
  - `"live-chart"` → `LiveChartPanel`
  - `"adaptive-tpsl"` → `AdaptiveTPSLPanel`

#### MOD-051: App Layout
- **file_path**: `frontend/app/layout.tsx`
- **purpose**: Root layout with providers (QueryClient, WebSocket, i18n).

#### MOD-052: Providers
- **file_path**: `frontend/app/providers.tsx`
- **purpose**: React Query provider, WebSocket provider wrapper.

---

### FRONTEND — PANEL COMPONENTS

#### MOD-060: ClearTrendPanel (V3 — Active)
- **file_path**: `frontend/components/panels/ClearTrendPanelV3.tsx`
- **purpose**: Clear Trend panel — displays current price, trend direction/strength, S/R levels, trade suggestions, TrendChannelChart.
- **data_source**: HTTP fetch to `/api/clear-trend/{symbol}` + WebSocket (`useWSPanelData`)
- **dependencies**: MOD-075 (TrendChannelChart)
- **known_issues**:
  - ISS-060: `chart_data` from backend may be undefined (optional field). Guard: `data.chart_data && data.chart_data.closes.length > 5`

#### MOD-061: CyberpunkTrendPanel (INACTIVE — kept for reference)
- **file_path**: `frontend/components/panels/CyberpunkTrendPanel.tsx`
- **purpose**: Alternative cyberpunk-styled Clear Trend panel. NOT imported by page.tsx.

#### MOD-062: EmelPanel
- **file_path**: `frontend/components/panels/EmelPanel.tsx`
- **purpose**: EMEL strategy panel — 9-checkpoint analysis display.
- **data_source**: `/api/emel/{symbol}`

#### MOD-063: PulsePanel
- **file_path**: `frontend/components/panels/PulsePanel.tsx`
- **purpose**: Pulse 1 algorithmic scalp panel.
- **data_source**: `/api/pulse/{symbol}`

#### MOD-064: PulseV3Panel
- **file_path**: `frontend/components/panels/PulseV3Panel.tsx`
- **purpose**: Pulse 3 multi-timeframe hybrid panel.
- **data_source**: `/api/pulse-v3/{symbol}`

#### MOD-065: PulseMLPanel
- **file_path**: `frontend/components/panels/PulseMLPanel.tsx`
- **purpose**: Pulse 2 ML hybrid panel.
- **data_source**: `/api/pulse-ml/{symbol}`

#### MOD-066: MTFMatrixPanel
- **file_path**: `frontend/components/panels/MTFMatrixPanel.tsx`
- **purpose**: Multi-timeframe alignment matrix.
- **data_source**: `/api/mtf-analysis/{symbol}`

#### MOD-067: LearningDashboardV2
- **file_path**: `frontend/components/panels/LearningDashboardV2.tsx`
- **purpose**: Trade learning dashboard — performance analytics, pattern success rates.
- **data_source**: `/api/learning/*`

#### MOD-068: RiskRewardPanel
- **file_path**: `frontend/components/panels/RiskRewardPanel.tsx`
- **purpose**: Risk/reward calculator and visualization.

#### MOD-069: SMCPanel
- **file_path**: `frontend/components/panels/SMCPanel.tsx`
- **purpose**: Smart Money Concepts (ICT) analysis panel.

#### MOD-070: SeasonalityPanel
- **file_path**: `frontend/components/panels/SeasonalityPanel.tsx`
- **purpose**: Historical seasonality patterns display.

#### MOD-071: COTWhalePanel
- **file_path**: `frontend/components/panels/COTWhalePanel.tsx`
- **purpose**: COT report data and whale tracking.
- **data_source**: `/api/cot/*`, `/api/whale/*`

#### MOD-072: MLPredictionPanel
- **file_path**: `frontend/components/MLPredictionPanel.tsx`
- **purpose**: ML prediction display with confidence layers visualization.
- **data_source**: `/api/run/prediction/{symbol}`

#### MOD-073: MLFactorPanel
- **file_path**: `frontend/components/MLFactorPanel.tsx`
- **purpose**: ML confidence factor breakdown — strategy presets (ultra_safe, balanced, aggressive).
- **data_source**: Inline calculation from cached data

#### MOD-074: AdaptiveTPSLPanel
- **file_path**: `frontend/components/AdaptiveTPSLPanel.tsx`
- **purpose**: Adaptive take-profit/stop-loss display.

#### MOD-075: TrendChannelChart (Shared)
- **file_path**: `frontend/components/panels/TrendChannelChart.tsx`
- **purpose**: SVG-based trend channel chart with S/R lines, date axis, scrollable data window, pulsing proximity effects.
- **props**: `closes, dates?, upper, lower, middle, supportLevels, resistanceLevels, currentPrice, decimals, supportProximity, resistanceProximity, supportIntensity, resistanceIntensity`
- **consumers**: MOD-060 (ClearTrendPanelV3), MOD-061 (CyberpunkTrendPanel)

---

### FRONTEND — HOOKS & STATE

#### MOD-080: useCachedDashboardData
- **file_path**: `frontend/hooks/useCachedDashboardData.ts`
- **purpose**: Primary data hook — combines WebSocket data with HTTP fallback (React Query).
- **entry_points**:
  - `useCachedDashboardData()` — returns `{ nasdaq, xauusd, isLoading, refetch }`
  - `cachedToSignalCard(cached, symbol)` — converts to signal card format
- **data_flow**: WebSocket → immediate | HTTP (`/api/data/cached/{symbol}`) → 30s polling

#### MOD-081: useLivePrices
- **file_path**: `frontend/hooks/useLivePrices.ts`
- **purpose**: Real-time price ticker for header display.
- **data_source**: WebSocket + HTTP fallback

#### MOD-082: useMTFAnalysis
- **file_path**: `frontend/hooks/useMTFAnalysis.ts`
- **purpose**: Multi-timeframe analysis hook.
- **data_source**: `/api/mtf-analysis/{symbol}`

#### MOD-083: useProximityAnimation
- **file_path**: `frontend/hooks/useProximityAnimation.ts`
- **purpose**: Calculates S/R proximity intensity for chart pulsing effects.

#### MOD-084: useWebSocket
- **file_path**: `frontend/hooks/useWebSocket.ts`
- **purpose**: Low-level WebSocket connection hook (used by WebSocketContext).

#### MOD-090: Zustand Stores
- **file_path**: `frontend/lib/store.ts`
- **purpose**: Global state stores: `useDashboardStore`, `useDetailPanelStore`, `useChartStore`, `useNewsStore`, `useMLStrategyStore`
- **key_state**:
  - `useDashboardStore.fetchAll()` — dispatches `dashboard-refresh` CustomEvent
  - `useMLStrategyStore.getConfig(symbol)` — returns strategy preset + enabled factors

#### MOD-091: WebSocketContext
- **file_path**: `frontend/contexts/WebSocketContext.tsx`
- **purpose**: React context providing WebSocket connection state and per-symbol data to all components.
- **hooks_exported**: `useWSData()`, `useWSSymbolData(symbol)`, `useWSPanelData(symbol, panelKey)`
- **known_issues**:
  - ISS-091: Reconnect backoff can delay data up to 30s after network interruption. Max: `RECONNECT_MAX_MS = 30000`

#### MOD-092: API Client
- **file_path**: `frontend/lib/api.ts`
- **purpose**: Shared `fetcher()` function, React Query hooks for legacy panels (nasdaq, xauusd, pattern engine, claude).
- **timeout**: 15000ms per request
- **api_base**: `https://upbeat-flow-production.up.railway.app`

---

### FRONTEND — LEGACY/BROKEN COMPONENTS (ts-nocheck applied)

#### MOD-095: ClaudeNewsAnalysisPanel
- **file_path**: `frontend/components/ClaudeNewsAnalysisPanel.tsx`
- **status**: `@ts-nocheck` — uses missing `@/components/ui/*` imports (Card, Button, Badge, Progress)
- **fix_required**: Install shadcn/ui components OR rewrite with plain HTML

#### MOD-096: SentimentPanel
- **file_path**: `frontend/components/SentimentPanel.tsx`
- **status**: `@ts-nocheck` — accesses `data.sentiment`, `data.key_factors` etc. without null checks
- **fix_required**: Add proper typing and null guards

#### MOD-097: XauusdPanel
- **file_path**: `frontend/components/XauusdPanel.tsx`
- **status**: `@ts-nocheck` — accesses `data.signal`, `data.metrics.*` without null checks

#### MOD-098: PatternEnginePanel
- **file_path**: `frontend/components/PatternEnginePanel.tsx`
- **status**: `@ts-nocheck` — type issues with pattern data shape

---

## ERROR_SIGNATURES

```yaml
# === CRITICAL: Site-Breaking ===

- pattern: "all API endpoints return 404"
  likely_module: "MOD-001"
  function: "lifespan() or router imports"
  check: "ROUTERS_LOADED flag, IMPORT_ERROR variable"
  fix: "Check stderr for import traceback, fix broken import"

- pattern: "prices frozen / charts not updating"
  likely_module: "MOD-010"
  function: "_pump_cycle()"
  param_to_check: "MT5 Redis bridge connection, _last ingest timestamps"
  fix: "Check /health/ready, verify mt5_redis_client reconnect (NOT an API key — no vendor)"

- pattern: "new code not appearing on live site"
  likely_module: "BUILD_PIPELINE"
  check: "Run `npx tsc --noEmit` in frontend/ — ANY error blocks Railway deployment"
  fix: "Fix TS errors or add // @ts-nocheck to broken files"

# === FRONTEND ===

- pattern: "panel shows 'Loading...' forever"
  likely_module: "MOD-080 or MOD-091"
  function: "useCachedDashboardData() or useWSPanelData()"
  check: "WebSocket status, API response in Network tab"

- pattern: "chart not loading in Clear Trend"
  likely_module: "MOD-060"
  function: "ClearTrendPanelV3 render"
  param_to_check: "data.chart_data (may be undefined from backend)"
  fix: "Ensure backend clear_trend.py returns chart_data with closes/dates/trend_channel"

- pattern: "signal card shows wrong confidence"
  likely_module: "MOD-020"
  function: "_apply_layered_confidence()"
  param_to_check: "strategy preset, enabled layers"

- pattern: "S/R lines invisible on chart"
  likely_module: "MOD-075"
  function: "TrendChannelChart SVG render"
  param_to_check: "supportLevels/resistanceLevels arrays, PAD.bottom value"

# === BACKEND ===

- pattern: "ML prediction ValueError"
  likely_module: "MOD-020"
  function: "_compute_technical_indicators() or predict()"
  check: "Feature count mismatch between model and computed features"

- pattern: "regime always returns RANGING"
  likely_module: "MOD-022"
  function: "detect_regime()"
  check: "ADX calculation, 4H candle data availability"

- pattern: "signal lifecycle not tracking"
  likely_module: "MOD-025"
  function: "run_lifecycle_check()"
  check: "scheduler_state table, _price_fetch_failures circuit breaker"

- pattern: "Supabase connection errors"
  likely_module: "MOD-003"
  check: "/health/ready endpoint, connection pool stats at /debug/connections"
```

---

## CHANGE_PROTOCOL

```yaml
rule_01: "NEVER modify MOD-010 (DataHub) without testing MOD-011 (Scheduler) — they share _candle_store and _price_store globals"
rule_02: "NEVER modify TrendChannelChart props interface without updating ALL consumers (ClearTrendPanelV3, CyberpunkTrendPanel)"
rule_03: "After ANY frontend change, run `npx tsc --noEmit` in frontend/ before pushing — TS errors SILENTLY BLOCK Railway deployment"
rule_04: "page.tsx imports panels as lazy(() => import(...)). Changing a panel filename requires updating the import in page.tsx"
rule_05: "ML model changes require matching feature vector changes in _compute_technical_indicators()"
rule_06: "Regime changes (MOD-022) cascade to: EMEL (allowed_directions), Pulse (direction blocking), ML (confidence adjustments)"
rule_07: "API_BASE is hardcoded in multiple files. grep for 'upbeat-flow-production' to find all instances"
rule_08: "WebSocket panel keys must match: backend ws_manager broadcast keys ↔ frontend useWSPanelData(symbol, panelKey)"
rule_09: "Signal lifecycle depends on prediction_logs having status='active'. Never bulk-update statuses without checking lifecycle logic"
rule_10: "The .env file is NOT committed. Railway env vars are set in the Railway dashboard"
rule_11: "Backend and frontend are SEPARATE Railway services. Each has its own railway.toml"
rule_12: "frontend/railway.toml build command: 'npm ci && npm run build'. Start: 'npm start'"
rule_13: "backend/railway.toml: Nixpacks auto-detects Python. Dockerfile is alternative"
```

---

## QUICK_REFERENCE

```yaml
# User complaint → What to check

- "user_says: 'risk wrong'" -> check: "MOD-030: trading_engine/portfolio_risk_manager.py"
- "user_says: 'chart stuck'" -> check: "MOD-010: MT5 Redis bridge (mt5_redis_client) reconnect"
- "user_says: 'signal late'" -> check: "MOD-020: SIGNAL_COOLDOWN_MINUTES (default 15)"
- "user_says: 'panel disappeared'" -> check: "MOD-050: page.tsx renderCardContent(), check cardId mapping"
- "user_says: 'confidence too low'" -> check: "MOD-020: _apply_layered_confidence(), strategy presets"
- "user_says: 'confidence too high'" -> check: "MOD-020: floor_ratio in STRATEGY_PRESETS"
- "user_says: 'wrong direction'" -> check: "MOD-022: detect_regime(), allowed_directions"
- "user_says: 'deployment not working'" -> check: "Run tsc in frontend/, check Railway build logs"
- "user_says: 'websocket disconnected'" -> check: "MOD-091: WebSocketProvider, /ws/all endpoint"
- "user_says: 'no news'" -> check: "MOD-036: live_news_monitor.py, MARKETAUX_API_KEY"
- "user_says: 'dates missing'" -> check: "MOD-031: clear_trend.py chart_data.dates generation"
- "user_says: 'target/stop wrong'" -> check: "MOD-023: adaptive_tp_sl.py, MOD-031: _calculate_trade_zones()"
- "user_says: 'learning panel empty'" -> check: "MOD-067 + MOD-035: learning router, prediction_logs table"
- "user_says: 'login broken'" -> check: "MOD-034: auth.py, Supabase users table"
```

---

## DEPENDENCY_GRAPH

```
MT5→Redis ──→ MOD-010 (DataHub) ──→ MOD-011 (Scheduler) ──→ Supabase
                │                        │
                ├──→ MOD-020 (ML Prediction) ──→ MOD-028 (Prediction Logger) ──→ Supabase
                │       │
                │       ├──→ MOD-030 (Trading Engine) [16 sub-modules]
                │       │
                │       └──→ MOD-022 (Market Regime) ──→ MOD-032 (EMEL/Pulse Router)
                │
                ├──→ MOD-021 (Trend Analyzer) ──→ MOD-031 (Clear Trend Router)
                │
                ├──→ MOD-025 (Signal Lifecycle) ──→ MOD-026 (Outcome Tracker)
                │                                    │
                │                                    └──→ MOD-027 (Error Analysis)
                │
                └──→ MOD-012 (WS Manager) ──→ WebSocket /ws/all
                                                    │
                                                    ▼
                                            MOD-091 (WebSocketContext)
                                                    │
                        ┌───────────────────────────┼───────────────────┐
                        │                           │                   │
                   MOD-080                     MOD-060              MOD-062-065
              (useCachedDashboard)        (ClearTrendPanelV3)     (Emel/Pulse)
                        │                      │
                        └──────→ MOD-050 (page.tsx) ←──────────────────┘
```

---

## SINGLE_POINTS_OF_FAILURE

```yaml
- spof_1:
    component: "MOD-010 (DataHub)"
    impact: "ALL panels lose data if DataHub stops"
    mitigation: "Supabase cache provides stale data for ~15 min"
    monitor: "/health/ready"

- spof_2:
    component: "MT5 Redis bridge (mt5_redis_client)"
    impact: "No new market data if the MT5→Redis bridge disconnects (reconnect logic, not a vendor quota)"
    mitigation: "None — single data provider"
    monitor: "Check DataHub logs for empty responses"

- spof_3:
    component: "Supabase"
    impact: "Auth fails, cached data unavailable on cold start, signal lifecycle stops"
    mitigation: "In-memory DataHub survives Supabase outage if already seeded"
    monitor: "/health/ready, /debug/connections"

- spof_4:
    component: "page.tsx"
    impact: "Any crash in this 1544-line file breaks entire dashboard"
    mitigation: "ErrorBoundary wraps individual panels"
    monitor: "Browser console errors"

- spof_5:
    component: "TypeScript build"
    impact: "ANY TS error in ANY file blocks Railway deployment — old version stays live"
    mitigation: "Pre-push check: `npx tsc --noEmit`"
    monitor: "Railway build logs"
```

---

## FILE_SIZE_HOTSPOTS (complexity indicators)

```
backend/routers/emel_pulse.py          99,690 bytes (2144 lines) — 5 endpoints, entire trading logic
backend/services/ml_prediction_service.py  102,267 bytes (2252 lines) — ML pipeline
backend/routers/learning.py            57,479 bytes — learning dashboard
backend/services/mtf_analysis_service.py   58,944 bytes — MTF analysis
backend/services/signal_lifecycle.py   41,766 bytes — signal tracking
frontend/app/page.tsx                  67,194 bytes (1544 lines) — entire dashboard
frontend/components/PatternEngineV2.tsx 43,638 bytes — large panel
frontend/components/InfoTooltip.tsx    42,023 bytes — tooltip system
```

---

## ENV_VARS_REQUIRED

```yaml
# Critical (app won't work without these)
REDIS_URL: "Railway Redis URL — MT5 bridge pub/sub + streams (price/candle source)"
SUPABASE_URL: "Supabase project URL"
SUPABASE_KEY: "Supabase service role key"

# Nice to have (features degrade gracefully)
ANTHROPIC_API_KEY: "Claude AI analysis"
DEEP_SEEKR1: "DeepSeek analysis"
GROQ_API_KEY: "Groq LLM"
XAI_API_KEY: "xAI analysis"
MARKETAUX_API_KEY: "News API"
X_BEARER_TOKEN: "Twitter/X monitoring"
REDIS_URL: "WebSocket broadcast cache"
RESEND_API_KEY: "Email service"
TELEGRAM_BOT_TOKEN: "Telegram notifications"
TELEGRAM_CHAT_ID: "Telegram chat target"
```
