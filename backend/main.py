from datetime import datetime
import asyncio
import importlib
import time
import os
import sys
import logging
import traceback
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv

# Load .env file - try multiple locations
env_paths = [
    Path(__file__).parent / ".env",  # backend/.env
    Path(__file__).parent.parent / ".env",  # project root/.env
]
for env_path in env_paths:
    if env_path.exists():
        load_dotenv(env_path)
        break

from config import settings

import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from utils.json_response import NumpySafeJSONResponse, NumpySafeEncoder

logger = logging.getLogger(__name__)

_APP_START_TIME = time.time()
_conn_logger_task = None
_mt5_redis_task = None


async def _connection_stats_logger():
    """Log Supabase connection pool stats every 60s for observability."""
    while True:
        await asyncio.sleep(60)
        try:
            from database.supabase_client import get_supabase_client
            client = get_supabase_client()
            if client:
                stats = client.get_stats()
                logger.info(
                    f"[ConnPool] reqs={stats['total_requests']} "
                    f"errs={stats['total_errors']} "
                    f"retries={stats['total_retries']} "
                    f"err_rate={stats['error_rate_pct']}% "
                    f"rpm={stats['requests_per_minute']} "
                    f"closed={stats['client_closed']}"
                )
        except Exception:
            pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan: startup + shutdown in one place."""
    global _conn_logger_task, _mt5_redis_task

    # ── STARTUP (non-blocking, fast) ─────────────────────────────
    # 1. Redis (optional)
    try:
        from services.redis_client import get_redis, is_redis_available
        get_redis()
        print(f"Redis: {'connected' if is_redis_available() else 'not available (using memory fallback)'}")
    except Exception as e:
        print(f"Redis init skipped: {e}")

    # 2. DataHub (centralized data pump) — runs as background task
    try:
        from services.data_hub import start_data_hub
        asyncio.create_task(start_data_hub())
        print("DataHub started - centralized market data pump")
    except Exception as e:
        print(f"Failed to start DataHub: {e}")

    # 2.1 Register candle close event handlers (event-driven model refresh)
    try:
        from services.candle_event_handlers import register_all_candle_event_handlers
        register_all_candle_event_handlers()
        print("Candle close event handlers registered")
    except Exception as e:
        print(f"Failed to register candle event handlers: {e}")

    # 2.5 MT5 Redis listener (optional, source-mode controlled)
    try:
        from services.mt5_redis_client import start_mt5_redis_listener
        _mt5_redis_task = asyncio.create_task(start_mt5_redis_listener())
        print("MT5 Redis listener task started")
    except Exception as e:
        print(f"Failed to start MT5 Redis listener: {e}")

    # 2.6 Macro data service (DXY/VIX/US10Y from Yahoo, hourly refresh)
    try:
        from services.macro_data_service import ensure_started as start_macros
        asyncio.create_task(start_macros())
        print("✅ Macro data service başlatıldı (DXY/VIX/US10Y, hourly refresh)")
    except Exception as e:
        print(f"❌ Macro data service başlatılamadı: {e}")

    # 2.6b Pandemic Sensitivity Index (basket-driven health-crisis early-warning, 6h refresh)
    try:
        from services.pandemic_sensitivity_service import ensure_started as start_psi
        asyncio.create_task(start_psi())
        print("✅ Pandemic Sensitivity Index başlatıldı (6h basket refresh)")
    except Exception as e:
        print(f"❌ Pandemic Sensitivity Index başlatılamadı: {e}")

    # 2.7 AI-Ops orchestrator (daily failure-cluster + DeepSeek proposal cycle)
    try:
        from services.ai_ops_orchestrator import orchestrate_ai_ops

        async def ai_ops_loop():
            # Wait 5 min after startup so other services warm up first
            await asyncio.sleep(300)
            while True:
                try:
                    summary = await orchestrate_ai_ops(window_days=7)
                    logger.info("[ai_ops] daily cycle: %s", summary)
                except Exception as e:
                    logger.error("[ai_ops] cycle failed: %s", e)
                # Run once per 24h
                await asyncio.sleep(86400)

        asyncio.create_task(ai_ops_loop())
        print("✅ AI-Ops orchestrator başlatıldı (24h cycle, DeepSeek proposals)")
    except Exception as e:
        print(f"❌ AI-Ops orchestrator başlatılamadı: {e}")

    # 2.8 Pattern mining cron (weekly self-feeding rule discovery)
    try:
        from services.pattern_mining_service import weekly_loop as pattern_mining_loop
        asyncio.create_task(pattern_mining_loop())
        print("✅ Pattern mining cron başlatıldı (weekly self-feeding rules)")
    except Exception as e:
        print(f"❌ Pattern mining cron başlatılamadı: {e}")

    # 2.9 Post-deploy monitor (daily live-vs-simulation tracking for implemented proposals)
    try:
        from services.post_deploy_monitor import daily_loop as post_deploy_loop
        asyncio.create_task(post_deploy_loop())
        print("✅ Post-deploy monitor başlatıldı (daily proposal tracking)")
    except Exception as e:
        print(f"❌ Post-deploy monitor başlatılamadı: {e}")

    # 2.10 TP/SL optimizer (daily MFE/MAE grid search → optimal TP/SL recommendations)
    try:
        from services.tp_sl_optimizer import daily_loop as tp_sl_loop
        asyncio.create_task(tp_sl_loop())
        print("✅ TP/SL optimizer başlatıldı (daily MFE/MAE grid search)")
    except Exception as e:
        print(f"❌ TP/SL optimizer başlatılamadı: {e}")

    # 2.11 Auto-triage (6h cycle: classify pending proposals into apply/review/reject)
    try:
        from services.ai_ops_auto_triage import cron_loop as auto_triage_loop
        asyncio.create_task(auto_triage_loop())
        print("✅ Auto-triage başlatıldı (6h cycle, pending → apply/review/reject)")
    except Exception as e:
        print(f"❌ Auto-triage başlatılamadı: {e}")

    # 3. PULSE + EMEL SCHEDULER (Doğrudan Başlat - 15dk'da bir)
    try:
        from services.background_scheduler import log_pulse_signals_if_needed
        # Pulse'ı hemen başlat ve arka planda çalıştır
        asyncio.create_task(log_pulse_signals_if_needed())
        print("✅ Pulse/EMEL scheduler başlatıldı (her 15dk'da kontrol)")
    except Exception as e:
        print(f"❌ Pulse scheduler hatası: {e}")

    # 4. LIFECYCLE CHECKER (Her 2 dakikada TP/SL kontrolü)
    try:
        from services.signal_lifecycle import check_lifecycle_if_needed
        async def lifecycle_loop():
            while True:
                try:
                    await check_lifecycle_if_needed()
                    logger.info("♻️ Lifecycle check tamamlandı")
                except Exception as e:
                    logger.error(f"Lifecycle hatası: {e}")
                await asyncio.sleep(120)  # 2 dakika bekle
        
        asyncio.create_task(lifecycle_loop())
        print("✅ Lifecycle checker başlatıldı (her 2dk'da)")
    except Exception as e:
        print(f"❌ Lifecycle hatası: {e}")

    # 5. EODHD REAL-TIME WEBSOCKET (Anlık fiyat verisi)
    # Disabled by user request: API tier does not allow forex/indices WebSockets, 
    # and using ETF proxies shows incorrect absolute price values. 
    # Relying entirely on DataHub 5s REST polling instead.
    # try:
    #     from services.eodhd_websocket_client import start_eodhd_websocket
    #     asyncio.create_task(start_eodhd_websocket())
    #     print("✅ EODHD WebSocket client başlatıldı - Gerçek zamanlı fiyat verisi")
    # except Exception as e:
    #     print(f"⚠️ EODHD WebSocket başlatılamadı: {e}")

    # 5.5 META INTELLIGENCE ENGINE (Her dakika kontrol/log)
    try:
        from services.meta_analysis_engine import SUPPORTED_SYMBOLS, get_meta_signal
        
        async def meta_engine_loop():
            # Wait a bit before starting to ensure other systems are ready
            await asyncio.sleep(15)
            logger.info("🤖 Meta-Intelligence Engine loop starting...")
            while True:
                try:
                    for sym in SUPPORTED_SYMBOLS:
                        # get_meta_signal also processes and logs the signal
                        # We just need to call it periodically
                        await get_meta_signal(sym)
                    logger.debug("🤖 Meta-Engine check completed for all symbols")
                except Exception as e:
                    logger.error(f"Meta-Engine loop error: {e}")
                
                # Check every 60 seconds
                await asyncio.sleep(60)

        asyncio.create_task(meta_engine_loop())
        print("✅ Meta-Intelligence Engine başlatıldı (60s check)")
    except Exception as e:
        print(f"❌ Meta-Engine başlatılamadı: {e}")

    # 6. Background scheduler (diğer görevler için)
    try:
        from services.background_scheduler import start_scheduler
        start_scheduler()
        print("Background scheduler started (with WebSocket broadcast)")
    except Exception as e:
        print(f"Failed to start scheduler: {e}")

    try:
        if settings.oil_baltic_sync_autostart:
            from services.baltic_index_service import baltic_sync_loop
            asyncio.create_task(baltic_sync_loop(settings.oil_baltic_sync_interval_seconds))
            print("Oil Baltic sync started")
    except Exception as e:
        print(f"Failed to start Oil Baltic sync: {e}")

    try:
        if settings.oil_ais_autostart and settings.aisstream_api_key:
            from services.ais_oil_collector import start_ais_oil_collector
            start_ais_oil_collector()
            print("AIS oil collector started")
    except Exception as e:
        print(f"Failed to start AIS oil collector: {e}")

    # 6. Connection stats logger (every 60s)
    _conn_logger_task = asyncio.create_task(_connection_stats_logger())

    print(f"App ready in {time.time() - _APP_START_TIME:.1f}s")

    yield  # ── APP RUNNING ──

    # ── SHUTDOWN (graceful) ──────────────────────────────────────
    if _conn_logger_task:
        _conn_logger_task.cancel()

    if _mt5_redis_task:
        _mt5_redis_task.cancel()

    try:
        from services.data_hub import stop_data_hub
        stop_data_hub()
        print("DataHub stopped")
    except Exception as e:
        print(f"Error stopping DataHub: {e}")

    try:
        from services.mt5_redis_client import stop_mt5_redis_listener
        await stop_mt5_redis_listener()
        print("MT5 Redis listener stopped")
    except Exception as e:
        print(f"Error stopping MT5 Redis listener: {e}")

    try:
        from services.background_scheduler import stop_scheduler
        stop_scheduler()
        print("Background scheduler stopped")
    except Exception as e:
        print(f"Error stopping scheduler: {e}")

    try:
        from services.baltic_index_service import stop_baltic_sync
        stop_baltic_sync()
    except Exception as e:
        print(f"Error stopping Oil Baltic sync: {e}")

    try:
        from services.ais_oil_collector import stop_ais_oil_collector
        stop_ais_oil_collector()
    except Exception as e:
        print(f"Error stopping AIS oil collector: {e}")

    try:
        from services.rss_aggregator import close_rss_aggregator
        await close_rss_aggregator()
    except Exception as e:
        print(f"Error closing RSS aggregator: {e}")

    # Close Supabase HTTP client gracefully
    try:
        from database.supabase_client import get_supabase_client
        client = get_supabase_client()
        if client:
            client.close()
    except Exception:
        pass


app = FastAPI(
    title="AI Trading Dashboard API",
    version="0.1.0",
    default_response_class=NumpySafeJSONResponse,
    lifespan=lifespan,
)

# CORS - allow all origins for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler to catch serialization errors and return JSON
from fastapi import Request
from fastapi.responses import PlainTextResponse
import traceback as tb_module

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import logging
    logging.getLogger("global").error(f"Unhandled exception on {request.url.path}: {exc}\n{tb_module.format_exc()}")
    return PlainTextResponse(
        content=f'{{"error": "{str(exc)[:200]}", "path": "{request.url.path}"}}',
        status_code=500,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Content-Type": "application/json"
        }
    )

# Panel response cache middleware (caches panel API responses for WS broadcast)
try:
    from middleware.panel_cache import PanelCacheMiddleware
    app.add_middleware(PanelCacheMiddleware)
except Exception as e:
    print(f"Panel cache middleware skipped: {e}")

# ═══════════════════════════════════════════════════════════════════
# HEALTH & READINESS (enterprise pattern)
# ═══════════════════════════════════════════════════════════════════

@app.get("/")
async def root():
    return {"message": "AI Trading Dashboard API", "status": "ok"}

@app.get("/api/version")
async def version_check():
    """Returns the deployed git commit hash for debugging."""
    return {"version": "529a989-nan-fix", "deployed_at": "2026-03-03T20:50:00Z"}


@app.get("/api/health")
async def health_liveness():
    """Liveness probe — NO DB, NO external calls. Just 'process alive'.
    Railway/K8s uses this to know the container is running."""
    return {
        "ok": True,
        "status": "alive",
        "uptime_seconds": round(time.time() - _APP_START_TIME, 1),
    }


@app.get("/api/ready")
async def health_readiness():
    """Readiness probe — checks DB connectivity with a 2s timeout.
    Returns 503 if DB is unreachable so load balancer stops sending traffic."""
    checks = {"db": False, "db_latency_ms": None, "degraded": False}

    try:
        from database.supabase_client import get_auth_error, get_supabase_client, is_auth_failed
        client = get_supabase_client()
        auth_failed = is_auth_failed()
        auth_failed = auth_failed if isinstance(auth_failed, bool) else False
        if client:
            start = time.time()
            result = client.table("prediction_logs").select("id").limit(1).execute()
            latency = (time.time() - start) * 1000
            checks["db"] = result.get("error") is None
            checks["db_latency_ms"] = round(latency, 1)
            if auth_failed:
                checks["degraded"] = True
                auth_error = get_auth_error()
                if auth_error is not None:
                    checks["db_auth_error"] = str(auth_error)[:200]
                checks["db"] = False
        elif auth_failed:
            checks["degraded"] = True
            auth_error = get_auth_error()
            if auth_error is not None:
                checks["db_auth_error"] = str(auth_error)[:200]
    except Exception as e:
        checks["db_error"] = str(e)[:100]

    all_ok = checks["db"] or checks["degraded"]
    status_code = 200 if all_ok else 503

    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=status_code,
        content={
            "ok": all_ok,
            "status": "degraded_ready" if checks["degraded"] else ("ready" if all_ok else "not_ready"),
            "checks": checks,
            "uptime_seconds": round(time.time() - _APP_START_TIME, 1),
        },
    )


@app.get("/api/stats/connections")
async def connection_stats():
    """Supabase connection pool observability endpoint."""
    try:
        from database.supabase_client import get_supabase_client
        client = get_supabase_client()
        if client:
            return {"ok": True, "pool": client.get_stats()}
        return {"ok": False, "error": "No Supabase client"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

ROUTERS_LOADED = False
IMPORT_ERROR = None

try:
    from routers import clear_trend
    app.include_router(clear_trend.router)
except Exception as e:
    print(f"ERROR loading clear_trend router: {e}", file=sys.stderr)

# Try to import routers with error handling
router_errors = []
router_module_names = [
    "patterns_stub",
    "nasdaq",
    "xauusd",
    "usoil",
    "dax",
    "oil_baltic_intelligence",
    "pattern_engine",
    "claude_news",
    "claude_sentiment",
    "order_blocks",
    "rtyhiim",
    "ta",
    "data",
    "prediction",
    "ai_analysis",
    "learning",
    "fvg",
    "auth",
    "mtf_analysis",
    "trading_engine_test",
    "emel_pulse",
    "admin",
    "deepseek_analysis",
    "websocket",
    "signal_lifecycle_router",
    "strategy_optimizer",
    "news_correlation",
    "rss_router",
    "prices",
    "economic_calendar_router",
    "meta_engine_router",
    "permutation_router",
    "ai_ops_router",
    "pandemic_sensitivity",
]

for module_name in router_module_names:
    try:
        module = importlib.import_module(f"routers.{module_name}")
        router = getattr(module, "router", None)
        if router is None:
            raise AttributeError("router attribute missing")
        app.include_router(router)
    except Exception as e:
        router_errors.append(f"{module_name}: {e}")
        print(f"ERROR loading router {module_name}: {e}", file=sys.stderr)

if router_errors:
    ROUTERS_LOADED = False
    IMPORT_ERROR = "; ".join(router_errors[:5])
    IMPORT_TRACEBACK = "\n".join(router_errors)
else:
    ROUTERS_LOADED = True

@app.get("/api/debug")
async def debug_info():
    from config import settings
    
    # List all registered routes
    routes = []
    for route in app.routes:
        if hasattr(route, "methods") and hasattr(route, "path"):
            routes.append({
                "path": route.path,
                "methods": list(route.methods) if route.methods else [],
                "name": route.name if hasattr(route, "name") else None
            })
    
    return {
        "routers_loaded": ROUTERS_LOADED,
        "import_error": IMPORT_ERROR if not ROUTERS_LOADED else None,
        "registered_routes_count": len(routes),
        "sample_routes": routes[:20],  # First 20 routes
        "env_vars_os": {
            "EODHD_API_KEY": "set" if os.getenv("EODHD_API_KEY") else "not set",
            "ANTHROPIC_API_KEY": "set" if os.getenv("ANTHROPIC_API_KEY") else "not set",
            "DEEP_SEEKR1": "set" if os.getenv("DEEP_SEEKR1") else "not set",
            "SUPABASE_URL": "set" if os.getenv("SUPABASE_URL") else "not set",
            "SUPABASE_KEY": "set" if os.getenv("SUPABASE_KEY") else "not set",
        },
        "settings_config": {
            "anthropic_api_key": "set" if settings.anthropic_api_key else "not set",
            "deepseek_api_key": "set" if settings.deepseek_api_key else "not set",
            "eodhd_api_key": "set" if settings.eodhd_api_key else "not set",
        }
    }


@app.get("/api/debug/ml-model/{symbol}")
async def debug_ml_model(symbol: str):
    """Debug ML model loading and prediction for a symbol."""
    from pathlib import Path
    from services.ml_prediction_service import (
        get_ml_model_filename,
        normalize_ml_market_symbol,
        resolve_ml_model_symbol,
    )

    result = {"symbol": symbol, "errors": [], "info": []}
    
    # Check model file
    model_path = Path(__file__).parent / "models"
    result["model_dir"] = str(model_path)
    result["model_dir_exists"] = model_path.exists()
    normalized_symbol = normalize_ml_market_symbol(symbol)
    model_family_symbol = resolve_ml_model_symbol(symbol)
    model_filename = get_ml_model_filename(symbol)

    result["normalized_market_symbol"] = normalized_symbol
    result["model_family_symbol"] = model_family_symbol
    result["model_filename"] = model_filename
    
    if model_filename:
        model_file = model_path / model_filename
    else:
        model_file = None
        result["errors"].append(f"No model family mapped for symbol: {symbol}")
    
    if model_file:
        result["model_file"] = str(model_file)
        result["model_file_exists"] = model_file.exists()
        
        if model_file.exists():
            try:
                import joblib
                model = joblib.load(model_file)
                result["model_loaded"] = True
                result["model_type"] = str(type(model))
                if hasattr(model, 'feature_names_in_'):
                    features = list(model.feature_names_in_)
                    result["feature_count"] = len(features)
                    result["features_sample"] = features[:20]
                else:
                    result["errors"].append("Model has no feature_names_in_")
            except Exception as e:
                result["model_loaded"] = False
                result["errors"].append(f"Model load error: {str(e)}")
    
    # Check data fetching
    try:
        from services.data_fetcher import fetch_30m_candles, fetch_latest_price, fetch_eod_candles
        normalized = normalized_symbol
        
        candles_30m = await fetch_30m_candles(normalized, limit=50)
        result["candles_30m_count"] = len(candles_30m) if candles_30m else 0
        
        candles_eod = await fetch_eod_candles(normalized, limit=50)
        result["candles_eod_count"] = len(candles_eod) if candles_eod else 0
        
        price = await fetch_latest_price(normalized)
        result["latest_price"] = price
        
        if not candles_30m or len(candles_30m) < 50:
            result["info"].append(f"M30 candles: {len(candles_30m) if candles_30m else 0}")
        if not candles_eod or len(candles_eod) < 50:
            result["errors"].append(f"Insufficient EOD candles: {len(candles_eod) if candles_eod else 0}")
    except Exception as e:
        result["errors"].append(f"Data fetch error: {str(e)}")
    
    return result


@app.get("/api/debug/news-test")
async def debug_news_test():
    """Test news API sources."""
    import httpx
    from config import settings
    
    result = {"eodhd_news": None, "marketaux_news": None}
    
    # Test EODHD News API
    if settings.eodhd_api_key:
        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                resp = await client.get(
                    "https://eodhistoricaldata.com/api/news",
                    params={
                        "api_token": settings.eodhd_api_key,
                        "s": "GOLD,GLD.US,DXY.INDX",
                        "limit": 5,
                        "fmt": "json",
                    },
                )
                result["eodhd_status"] = resp.status_code
                if resp.status_code == 200:
                    data = resp.json()
                    result["eodhd_news"] = [{"title": n.get("title", "")[:80], "date": n.get("date", "")} for n in (data or [])[:3]]
                else:
                    result["eodhd_error"] = resp.text[:200]
        except Exception as e:
            result["eodhd_error"] = str(e)
    
    # Test MarketAux
    if settings.marketaux_api_key:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    settings.marketaux_base_url,
                    params={
                        "api_token": settings.marketaux_api_key,
                        "symbols": "XAUUSD,GOLD",
                        "limit": 5,
                        "language": "en",
                    },
                )
                result["marketaux_status"] = resp.status_code
                if resp.status_code == 200:
                    data = resp.json().get("data", [])
                    result["marketaux_news"] = [{"title": n.get("title", "")[:80], "published": n.get("published_at", "")} for n in (data or [])[:3]]
                else:
                    result["marketaux_error"] = resp.text[:200]
        except Exception as e:
            result["marketaux_error"] = str(e)
    
    return result


@app.get("/api/debug/intraday-test/{symbol}")
async def debug_intraday_test(symbol: str):
    """Test EODHD intraday API directly."""
    import httpx
    from config import settings
    
    result = {"symbol": symbol, "tests": []}
    
    # Normalize symbol
    if symbol.upper() == "XAUUSD":
        test_symbols = ["XAUUSD.FOREX", "XAU.FOREX", "XAUUSD", "GC.COMEX"]
    else:
        test_symbols = [symbol]
    
    for test_sym in test_symbols:
        test_result = {"symbol": test_sym}
        url = f"https://eodhistoricaldata.com/api/intraday/{test_sym}"
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                # Use 1m for forex (EODHD only provides 1m for forex)
                interval = "1m" if ".FOREX" in test_sym.upper() else "5m"
                resp = await client.get(
                    url,
                    params={
                        "api_token": settings.eodhd_api_key,
                        "fmt": "json",
                        "interval": interval,
                    },
                )
                test_result["status_code"] = resp.status_code
                if resp.status_code == 200:
                    data = resp.json()
                    if isinstance(data, list):
                        test_result["count"] = len(data)
                        if data:
                            test_result["sample"] = data[-1]
                    else:
                        test_result["response_type"] = str(type(data))
                        test_result["response_preview"] = str(data)[:200]
                else:
                    test_result["error"] = resp.text[:200]
        except Exception as e:
            test_result["exception"] = str(e)
        
        result["tests"].append(test_result)
    
    return result


# ═══════════════════════════════════════════════════════════════════
# SLIPPAGE & COT API ENDPOINTS
# ═══════════════════════════════════════════════════════════════════

@app.get("/api/slippage/stats")
async def get_slippage_stats():
    """Get slippage statistics and current position multiplier."""
    try:
        from services.slippage_monitor import get_slippage_stats, get_position_multiplier
        stats = await get_slippage_stats()
        return {
            "success": True,
            "data": {
                "average_slippage": stats.average_slippage,
                "max_slippage": stats.max_slippage,
                "min_slippage": stats.min_slippage,
                "favorable_count": stats.favorable_count,
                "unfavorable_count": stats.unfavorable_count,
                "total_trades": stats.total_trades,
                "position_multiplier": stats.position_multiplier,
                "high_slippage_mode": stats.high_slippage_mode,
                "last_10_trades": stats.last_10_trades,
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/slippage/log")
async def log_execution(data: dict):
    """Log a trade execution for slippage tracking."""
    try:
        from services.slippage_monitor import handle_execution_webhook
        result = await handle_execution_webhook(data)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/cot/summary")
async def get_cot_summary():
    """Get COT report summary for all tracked symbols."""
    try:
        from services.cot_report_service import get_cot_summary
        summary = await get_cot_summary()
        return {"success": True, "data": summary}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/cot/{symbol}")
async def get_cot_data(symbol: str):
    """Get COT report data for a specific symbol."""
    try:
        from services.cot_report_service import fetch_cot_data
        from dataclasses import asdict
        cot = await fetch_cot_data(symbol)
        return {"success": True, "data": asdict(cot)}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/cot/history/{symbol}")
async def get_cot_history(symbol: str):
    """Get COT historical data for a symbol (up to 52 weeks)."""
    try:
        from services.cot_report_service import get_cot_history as _get_history
        history = _get_history(symbol)
        return {"success": True, "data": history}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/whale/dashboard")
async def get_whale_dashboard():
    """Get whale tracking dashboard data for all symbols."""
    try:
        from services.whale_tracker_service import get_whale_dashboard as _get_dashboard
        data = await _get_dashboard()
        return {"success": True, "data": data}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/whale/{symbol}")
async def get_whale_snapshot(symbol: str):
    """Get whale tracking snapshot for a specific symbol."""
    try:
        from services.whale_tracker_service import get_whale_snapshot as _get_snap
        from dataclasses import asdict
        snap = await _get_snap(symbol)
        return {"success": True, "data": asdict(snap)}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/whale/features/{symbol}")
async def get_whale_features(symbol: str):
    """Get whale ML features for a specific symbol."""
    try:
        from services.whale_tracker_service import get_whale_features as _get_feats
        feats = await _get_feats(symbol)
        return {"success": True, "data": feats}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/candlestick-patterns/{symbol}")
async def get_candlestick_patterns(symbol: str):
    """
    Get candlestick patterns for a symbol across M15, M30, H1, H4 timeframes.
    Returns detected patterns with explanations in Turkish.
    """
    try:
        from services.candlestick_pattern_service import detect_candlestick_patterns
        result = await detect_candlestick_patterns(symbol, ["15m", "30m", "1h", "4h"])
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


# NOTE: Startup/shutdown logic is now in the `lifespan` context manager above.
# The old @app.on_event("startup") / @app.on_event("shutdown") pattern is removed.


@app.get("/api/datahub/status")
async def datahub_status():
    """Get DataHub status - shows what data is cached and when it was last fetched."""
    try:
        from services.data_hub import get_hub_status
        return get_hub_status()
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/datahub/reseed")
async def datahub_reseed():
    """Force DataHub to do a full re-seed (fetch full candle history instead of delta)."""
    try:
        from services.data_hub import force_reseed
        return force_reseed()
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/datahub/purge-stale-cache")
async def datahub_purge_stale_cache(
    symbol: str | None = None,
    max_age_hours: float = 96,
):
    """Purge candle_cache rows older than `max_age_hours` (default 96h / 4 days).

    After purging, trigger a force re-seed so DataHub fetches fresh data.
    Optionally filter by `symbol` (e.g. NDX.INDX).
    """
    try:
        from services.candle_cache_store import purge_stale_candles
        from services.data_hub import force_reseed
        purge_result = purge_stale_candles(symbol=symbol, max_age_hours=max_age_hours)
        reseed_result = force_reseed()
        return {
            "purge": purge_result,
            "reseed": reseed_result,
            "message": "Stale cache purged and full re-seed triggered",
        }
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/datahub/clear-symbol/{symbol_path:path}")
async def datahub_clear_symbol(symbol_path: str):
    """Remove ALL candle_cache rows for a specific symbol and force re-seed.

    Useful when a single symbol has corrupted price data.
    """
    try:
        from services.candle_cache_store import purge_stale_candles
        from services.data_hub import force_reseed
        # Purge with max_age_hours=0 deletes everything up to now
        purge_result = purge_stale_candles(symbol=symbol_path, max_age_hours=0)
        reseed_result = force_reseed()
        return {
            "symbol": symbol_path,
            "purge": purge_result,
            "reseed": reseed_result,
            "message": f"All cached candles cleared for {symbol_path} — re-seed triggered",
        }
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/mt5-redis/diagnostics")
async def mt5_redis_diagnostics():
    """Diagnostic endpoint to check MT5 Redis listener status, stream existence, and counters."""
    try:
        from services.mt5_redis_client import get_mt5_redis_diagnostics
        return await get_mt5_redis_diagnostics()
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/datahub/flow-check")
async def datahub_flow_check(symbols: str | None = None):
    """Verify that market analysis inputs are currently available from DataHub cache only."""
    try:
        from services.data_hub import get_flow_check

        requested_symbols = [item.strip() for item in (symbols or "").split(",") if item.strip()] or None
        return get_flow_check(requested_symbols)
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.get("/api/market/status")
async def market_status():
    """
    Get market open/closed status for all tracked symbols.
    Shows when each market opens/closes and when prices will update.
    """
    from datetime import datetime, timezone
    
    now_utc = datetime.now(timezone.utc)
    hour_utc = now_utc.hour
    minute_utc = now_utc.minute
    current_time = f"{hour_utc:02d}:{minute_utc:02d} UTC"
    
    # Market hours (UTC)
    # NDX.INDX (NASDAQ): 09:30 - 16:00 UTC (Mon-Fri)
    # GDAXI.INDX (DAX): 07:00 - 15:30 UTC (Mon-Fri)  
    # XAUUSD (Forex): 22:00 Sun - 22:00 Fri UTC (5-day, 24h except weekend)
    # CL.COMM (Oil): 01:00 - 23:00 UTC (Mon-Fri)
    
    markets = {
        "NDX.INDX": {
            "name": "NASDAQ-100",
            "open_utc": "09:30",
            "close_utc": "16:00",
            "timezone": "America/New_York",
            "days": "Mon-Fri",
        },
        "GDAXI.INDX": {
            "name": "DAX-40",
            "open_utc": "07:00",
            "close_utc": "15:30",
            "timezone": "Europe/Berlin",
            "days": "Mon-Fri",
        },
        "XAUUSD": {
            "name": "Gold/USD (Forex)",
            "open_utc": "22:00 (Sun)",
            "close_utc": "22:00 (Fri)",
            "timezone": "UTC",
            "days": "Sun-Fri (5-day 24h)",
        },
        "USOIL.FOREX": {
            "name": "WTI Crude Oil",
            "open_utc": "01:00",
            "close_utc": "23:00",
            "timezone": "America/New_York",
            "days": "Mon-Fri",
        },
    }
    
    # Calculate status for each market
    for symbol, info in markets.items():
        open_h, open_m = map(int, info["open_utc"].split(":")[0:2])
        close_h, close_m = map(int, info["close_utc"].split(":")[0:2])
        
        current_minutes = hour_utc * 60 + minute_utc
        open_minutes = open_h * 60 + open_m
        close_minutes = close_h * 60 + close_m
        
        if open_minutes <= current_minutes < close_minutes:
            status = "OPEN"
            next_event = f"Closes at {info['close_utc']} UTC"
        else:
            status = "CLOSED"
            if current_minutes < open_minutes:
                next_event = f"Opens at {info['open_utc']} UTC"
            else:
                next_event = f"Opens tomorrow at {info['open_utc']} UTC"
        
        info["status"] = status
        info["next_event"] = next_event
    
    return {
        "current_time_utc": current_time,
        "note": "Prices only update during market hours. EODHD API returns last close when market is closed.",
        "markets": markets,
    }


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
