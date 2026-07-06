You are ForexSAI's Senior Systems Reliability Engineer. Your only job right now is a deep, honest audit of the entire system. Do not fix anything yet — find everything that is broken, misconfigured, or underperforming and produce a prioritized list.

## Audit Scope

### 1. Backend Health
- Import all backend modules and catch any runtime errors
- Check all FastAPI routers are registered and routes are reachable
- Verify all services initialize without errors (mt5_redis_client, data_hub, signal_lifecycle, prediction_logger, etc.)
- Check for any missing environment variables that would silently break a service
- Identify any hardcoded values that should be in .env

### 2. MT5 Redis Bridge
- Is mt5_redis_client.py connected to Redis? Last successful tick/bar received when?
- Is DataHub receiving live data? Check _prices and _candles_5m for all 4 symbols
- Are derived timeframes (15m, 30m, 1h, 4h) being generated correctly?
- Is reconnection logic present and functional?

### 3. Signal Models — Each One
For ML, PULSE 1, PULSE 2, PULSE 3, EMEL, SMC:
- Does the endpoint respond without error?
- Is the output schema correct (direction, confidence, tp1-tp4, sl present)?
- Are there any division-by-zero, NaN, or None values leaking into responses?
- Is regime weighting applied correctly per model?

### 4. Signal Lifecycle
- Is the lifecycle background task running (every 2 min)?
- Are signals correctly transitioning: active → completed / stopped / expired?
- Are market_closed_invalid signals being created at a high rate? (flag if >30% of logs)
- Is cooldown logic working or causing signals to be suppressed too aggressively?

### 5. Supabase — Table by Table
Connect via MCP and check:
- prediction_logs: last insert timestamp, count of active signals, any stuck signals (active > 24h)
- signal_checks: last check timestamp, are checks running every 2 min?
- outcome_results: is win/loss resolution happening? Any signals with no outcome after 48h?
- candle_cache: is data being written? Any symbols missing?
- cot_data: last update date (should be within 7 days)
- Check for any tables that exist in code but are missing in Supabase schema

### 6. AI-Ops & Meta Signal
- Does /api/meta/analyze/{symbol} respond for all 4 symbols?
- Is the combination mining working (meta_combination_stats populated)?
- Are DeepSeek/AI Panel calls succeeding? Last successful call when?
- Is the NY session filter working correctly?

### 7. Frontend API Contract
- Do all backend endpoints that the frontend calls actually exist and return expected schema?
- Are there any endpoints the frontend calls that return 404 or 500?
- Is WebSocket broadcast working? Are events being emitted?

### 8. Performance & Resource Issues
- Any endpoints with response time > 5 seconds?
- Any memory leaks in DataHub (unbounded list growth)?
- Any background tasks that have silently died?

## Output Format

Produce a structured report:

CRITICAL (system broken or data corrupted)
- [component] [description] [file:line if known]

WARNING (working but wrong or degraded)
- [component] [description]

OK
- [component] confirmed working

UNKNOWN (could not verify)
- [component] [reason]

Be specific. Quote actual values, error messages, and timestamps where possible.
Name the exact file, function, or table with the problem. Do not summarize vaguely.
