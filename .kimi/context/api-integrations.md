# API & Data Integrations — ForexSAI (Kimi Code context)

> Corrected from the template's generic placeholder (EODHD/Tiingo) to what this project actually
> uses. Per project owner instruction (2026-07-30): **do not reference EODHD anywhere** — it was
> a wrong/legacy vendor name that no longer applies. All price/candle data comes from ForexSAI's
> own MT5→Redis bridge system (the "meta köprü" / meta-bridge), not any third-party market-data
> vendor. See `.kimi/context/master-config.md` for the full data-flow diagram.

## Price & Candle Data — MT5 → Redis → DataHub (the project's own bridge, not a vendor API)

This is the **only** source of live price/candle data. There is no external market-data vendor
in this system.

```
MT5 (EA/Bot)  →  Redis (Railway-hosted)  →  backend/services/mt5_redis_client.py
                                                    │
                                                    ▼
                                      backend/services/data_hub.py
                                      (in-memory cache, single source of truth,
                                       WebSocket broadcast to frontend)
                                                    │
                                                    ▼
                                      data_fetcher.py / market_data_service.py
                                      (DataHub proxy — never call MT5/Redis directly)
```

- Pub/Sub: `mt5:tick` — instant tick (symbol, price, bid, ask, timestamp)
- Streams: `mt5:bar:5m`, `mt5:bar:1h`, `mt5:bar:1d` — closed bars
- Redis host: Railway (remote)
- Data mode flag: `MARKET_DATA_SOURCE=mt5_redis` (default) — no external fallback for price/candle
  data. `hybrid` mode adds a Yahoo Finance fallback for commodities only if MT5 goes stale; this
  is a fallback path, not a primary vendor.
- Symbols: `NDX.INDX` (NASDAQ 100), `GDAXI.INDX` (DAX 40), `XAUUSD` (Gold), `USOIL.FOREX` (WTI)
- Reference-only (not tradable, price/candle ingest only): `QQQ.US` (NDX premarket proxy)

## Macro Data — yfinance

- `backend/services/macro_data_service.py`, hourly refresh
- Series: DXY, VIX, US10Y, EURUSD, USDTRY
- No API key required
- Fully independent of the price/candle pipeline above

## News

- RSS aggregator today; a Telegram-based news detector is planned to replace/augment it.
- All external news/trading-data vendors (including the one this template's placeholder named)
  were fully removed from the system in 2026-06 — none of them are in the current codebase.

## AI / LLM Providers (analysis, not market data)

| Provider | Used for |
|---|---|
| Anthropic Claude | Pattern analysis, news analysis |
| DeepSeek (deepseek-reasoner) | Bias-debate "normal" agents, cost-efficient default |
| Kimi / Moonshot (`KIMI_API_KEY`, OpenAI-compatible) | Bias-debate CIO + "important" agents — routed via `services/llm_router.py` |
| Groq | LLM inference |
| xAI | Analysis |

Routing logic (`services/llm_router.py`): important/CIO/debate-critical calls → Kimi; routine/data
agents → DeepSeek Reasoner; fails open to a fallback if a key is missing.

## Infrastructure

| Component | Provider |
|---|---|
| Backend + Frontend hosting | Railway (Nixpacks) |
| Database | Supabase (PostgreSQL, RLS enabled on all tables) |
| Cache / message bus | Redis (Railway-hosted) — MT5 bridge pub/sub+streams, WebSocket broadcast cache |

## Key Endpoints (see master-config.md for the full, current list)

| Endpoint | Purpose |
|---|---|
| `GET /api/panel/pulse/{symbol}`, `/pulse-ml/{symbol}`, `/pulse-v3/{symbol}` | PULSE 1/2/3 |
| `GET /api/panel/emel/{symbol}` | EMEL (10-check) |
| `GET /api/panel/smc/{symbol}` | SMC (ICT/order block) |
| `GET /api/panel/regime/{symbol}` | Market regime |
| `GET /api/prediction/{symbol}?strategy=balanced` | ML prediction |
| `GET /api/fakeout/assess/{symbol}` | Live false-breakout radar |
| `GET /api/miroshark/current-bias?symbol=NDX.INDX` | Daily macro bias (NASDAQ-only) |
| `GET /api/learning/dashboard` | Model performance overview |
