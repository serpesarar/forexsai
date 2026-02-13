from datetime import datetime
import asyncio
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

import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from utils.json_response import NumpySafeJSONResponse, NumpySafeEncoder

logger = logging.getLogger(__name__)

_APP_START_TIME = time.time()
_conn_logger_task = None


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
    global _conn_logger_task

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

    # 3. Background scheduler (with WebSocket broadcast)
    try:
        from services.background_scheduler import start_scheduler
        start_scheduler()
        print("Background scheduler started (with WebSocket broadcast)")
    except Exception as e:
        print(f"Failed to start scheduler: {e}")

    # 4. Connection stats logger (every 60s)
    _conn_logger_task = asyncio.create_task(_connection_stats_logger())

    print(f"App ready in {time.time() - _APP_START_TIME:.1f}s")

    yield  # ── APP RUNNING ──

    # ── SHUTDOWN (graceful) ──────────────────────────────────────
    if _conn_logger_task:
        _conn_logger_task.cancel()

    try:
        from services.data_hub import stop_data_hub
        stop_data_hub()
        print("DataHub stopped")
    except Exception as e:
        print(f"Error stopping DataHub: {e}")

    try:
        from services.background_scheduler import stop_scheduler
        stop_scheduler()
        print("Background scheduler stopped")
    except Exception as e:
        print(f"Error stopping scheduler: {e}")

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
    checks = {"db": False, "db_latency_ms": None}

    try:
        from database.supabase_client import get_supabase_client
        client = get_supabase_client()
        if client:
            start = time.time()
            result = client.table("prediction_logs").select("id").limit(1).execute()
            latency = (time.time() - start) * 1000
            checks["db"] = result.get("error") is None
            checks["db_latency_ms"] = round(latency, 1)
    except Exception as e:
        checks["db_error"] = str(e)[:100]

    all_ok = checks["db"]
    status_code = 200 if all_ok else 503

    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=status_code,
        content={
            "ok": all_ok,
            "status": "ready" if all_ok else "not_ready",
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

# Try to import routers with error handling
try:
    from models.responses import HealthResponse, RunAllResponse
    from routers import (
        nasdaq,
        xauusd,
        pattern_engine,
        claude_patterns,
        claude_sentiment,
        order_blocks,
        rtyhiim,
        news,
        ta,
        data,
        prediction,
        ai_analysis,
        learning,
        fvg,
        claude_news,
        auth,
        live_news,
        mtf_analysis,
        earnings,
        trading_engine_test,
        emel_pulse,
        admin,
        clear_trend,
        deepseek_analysis,
        websocket,
        signal_lifecycle_router,
    )
    from services.data_fetcher import fetch_latest_price
    from services.ml_service import run_nasdaq_signal, run_xauusd_signal
    from services.pattern_engine_runner import run_pattern_engine
    from services.pattern_analyzer import run_claude_pattern_analysis
    from services.sentiment_analyzer import run_claude_sentiment
    from services.rtyhiim_service import run_rtyhiim_detector
    from services.order_block_service import service as order_block_service
    from order_block_detector import OrderBlockConfig

    app.include_router(nasdaq.router)
    app.include_router(xauusd.router)
    app.include_router(pattern_engine.router)
    app.include_router(claude_patterns.router)
    app.include_router(claude_sentiment.router)
    app.include_router(order_blocks.router)
    app.include_router(rtyhiim.router)
    app.include_router(news.router)
    app.include_router(ta.router)
    app.include_router(data.router)
    app.include_router(prediction.router)
    app.include_router(ai_analysis.router)
    app.include_router(learning.router)
    app.include_router(fvg.router)
    app.include_router(claude_news.router)
    app.include_router(auth.router)
    app.include_router(live_news.router)
    app.include_router(mtf_analysis.router)
    app.include_router(earnings.router)
    app.include_router(trading_engine_test.router)
    app.include_router(emel_pulse.router)
    app.include_router(admin.router)
    app.include_router(clear_trend.router)
    app.include_router(deepseek_analysis.router)
    app.include_router(websocket.router)
    app.include_router(signal_lifecycle_router.router)
    
    ROUTERS_LOADED = True
except Exception as e:
    ROUTERS_LOADED = False
    IMPORT_ERROR = str(e)
    IMPORT_TRACEBACK = traceback.format_exc()
    print(f"ERROR loading routers: {e}", file=sys.stderr)
    print(IMPORT_TRACEBACK, file=sys.stderr)

@app.get("/api/debug")
async def debug_info():
    from config import settings
    return {
        "routers_loaded": ROUTERS_LOADED,
        "import_error": IMPORT_ERROR if not ROUTERS_LOADED else None,
        "env_vars_os": {
            "EODHD_API_KEY": "set" if os.getenv("EODHD_API_KEY") else "not set",
            "ANTHROPIC_API_KEY": "set" if os.getenv("ANTHROPIC_API_KEY") else "not set",
            "DEEP_SEEKR1": "set" if os.getenv("DEEP_SEEKR1") else "not set",
            "SUPABASE_URL": "set" if os.getenv("SUPABASE_URL") else "not set",
            "SUPABASE_KEY": "set" if os.getenv("SUPABASE_KEY") else "not set",
            "SUPABASE_ANON_KEY": "set" if os.getenv("SUPABASE_ANON_KEY") else "not set",
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
    result = {"symbol": symbol, "errors": [], "info": []}
    
    # Check model file
    model_path = Path(__file__).parent / "models"
    result["model_dir"] = str(model_path)
    result["model_dir_exists"] = model_path.exists()
    
    if symbol.upper() in ["NASDAQ", "NDX.INDX", "NDX"]:
        model_file = model_path / "model_lgbm_nasdaq.joblib"
    elif symbol.upper() == "XAUUSD":
        model_file = model_path / "model_lgbm_xauusd.joblib"
    else:
        model_file = None
    
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
        normalized = "NDX.INDX" if symbol.upper() in ["NASDAQ", "NDX.INDX", "NDX"] else symbol.upper()
        
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


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
