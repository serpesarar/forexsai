"""
Background Scheduler Service
Runs in the background to continuously update market data and cache to Supabase.
"""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

from database.supabase_client import get_supabase_client, is_db_available
from services.ml_prediction_service import get_ml_prediction
from services.ta_service import compute_ta_snapshot
from services.data_fetcher import fetch_eod_candles, fetch_latest_price
from services.marketaux_service import fetch_marketaux_headlines
from services.outcome_tracker import check_pending_outcomes, check_multi_target_outcome
from services.error_analysis_service import check_and_analyze_failed_predictions

logger = logging.getLogger(__name__)

# Symbols to track
TRACKED_SYMBOLS = ["NDX.INDX", "XAUUSD"]

# Update intervals (seconds) - OPTIMIZED for 100K daily API call limit
# Each EODHD intraday/real-time request = 5 API calls
DATA_UPDATE_INTERVAL = 60   # Update price/TA data every 60 seconds (was 5s!)
MACRO_UPDATE_INTERVAL = 300  # Update macro data (DXY, VIX, USDTRY) every 5 minutes
NEWS_UPDATE_INTERVAL = 600   # Update news every 10 minutes
OUTCOME_CHECK_INTERVAL = 600  # Check outcomes every 10 minutes
ERROR_ANALYSIS_INTERVAL = 3600  # Analyze errors every hour
PREDICTION_LOG_INTERVAL = 3600  # Log predictions every hour

# Last update timestamps
_last_news_update: Dict[str, datetime] = {}
_last_news_hash: Dict[str, str] = {}
_last_outcome_check: Optional[datetime] = None
_last_error_analysis: Optional[datetime] = None
_last_prediction_log: Dict[str, datetime] = {}  # Per symbol
_last_macro_update: Optional[datetime] = None
_cached_macro: Dict[str, Any] = {}  # Cached macro data

# Scheduler running flag
_scheduler_running = False


async def _get_macro_data() -> Dict[str, Any]:
    """Get macro data from DataHub (0 API calls). DataHub fetches every 5min."""
    try:
        from services.data_hub import get_macro
        macro = get_macro()
        if macro and any(v.get("price") for v in macro.values()):
            return macro
    except ImportError:
        pass
    
    # Fallback: direct fetch with local cache (only before DataHub populates)
    global _last_macro_update, _cached_macro
    now = datetime.utcnow()
    if _last_macro_update and (now - _last_macro_update).total_seconds() < MACRO_UPDATE_INTERVAL and _cached_macro:
        return _cached_macro
    
    macro = {}
    for key, sym in [("dxy", "DXY.INDX"), ("vix", "VIX.INDX"), ("usdtry", "USDTRY")]:
        try:
            price = await fetch_latest_price(sym)
            macro[key] = {"symbol": sym, "price": float(price) if price else None}
        except Exception:
            macro[key] = _cached_macro.get(key, {"symbol": sym, "price": None})
    
    _cached_macro = macro
    _last_macro_update = now
    return macro


async def update_symbol_data(symbol: str) -> Optional[Dict[str, Any]]:
    """Fetch and update data for a single symbol."""
    try:
        # Get ML prediction (uses internal cache in ml_prediction_service)
        ml_prediction = await get_ml_prediction(symbol)
        ml_dict = {
            "symbol": ml_prediction.symbol,
            "direction": ml_prediction.direction,
            "confidence": ml_prediction.confidence,
            "probability_up": ml_prediction.probability_up,
            "probability_down": ml_prediction.probability_down,
            "entry_price": ml_prediction.entry_price,
            "target_price": ml_prediction.target_price,
            "stop_price": ml_prediction.stop_price,
            "risk_reward": ml_prediction.risk_reward,
            "technical_score": ml_prediction.technical_score,
            "momentum_score": ml_prediction.momentum_score,
            "trend_score": ml_prediction.trend_score,
            "volatility_regime": ml_prediction.volatility_regime,
        }
        
        # Get TA snapshot
        ta_snapshot = await compute_ta_snapshot(symbol)
        
        # Get latest price (uses 60s cache in data_fetcher)
        current_price = await fetch_latest_price(symbol)
        
        # Get macro data (uses 5-minute cache)
        macro = await _get_macro_data()
        
        # Session info
        now_utc = datetime.utcnow()
        hour_utc = now_utc.hour
        session = "closed"
        if 13 <= hour_utc < 21:
            session = "us_open"
        elif 8 <= hour_utc < 16:
            session = "europe_open"
        elif 0 <= hour_utc < 8:
            session = "asia_open"
        
        # Volume (simplified)
        volume_data = {
            "status": "NORMAL",
            "ratio": 1.0
        }
        
        # Volatility assessment
        vix_price = macro.get("vix", {}).get("price")
        volatility_level = "NORMAL"
        if vix_price and vix_price > 20:
            volatility_level = "HIGH"
        elif vix_price and vix_price < 15:
            volatility_level = "LOW"
        
        return {
            "symbol": symbol,
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "ml_prediction": ml_dict,
            "ta_snapshot": ta_snapshot,
            "current_price": float(current_price) if current_price else None,
            "macro": macro,
            "session": {"current": session, "hour_utc": hour_utc},
            "volume": volume_data,
            "volatility": {"level": volatility_level, "vix": vix_price},
        }
    except Exception as e:
        logger.error(f"Error updating data for {symbol}: {e}")
        return None


async def update_news_if_needed(symbol: str) -> Optional[Dict[str, Any]]:
    """Update news only if enough time has passed or new news available."""
    global _last_news_update, _last_news_hash
    
    now = datetime.utcnow()
    last_update = _last_news_update.get(symbol)
    
    # Check if we need to update
    if last_update and (now - last_update).total_seconds() < NEWS_UPDATE_INTERVAL:
        return None  # No update needed
    
    try:
        # Fetch news
        news_symbols = ["XAUUSD", "GOLD", "DXY", "USD"] if "XAU" in symbol else ["NDX", "NASDAQ", "VIX", "DXY"]
        headlines = await fetch_marketaux_headlines(news_symbols)
        
        # Create hash to detect changes
        news_hash = json.dumps([h.get("title", "") for h in headlines[:5]], sort_keys=True)
        
        # Check if news changed
        if news_hash == _last_news_hash.get(symbol):
            _last_news_update[symbol] = now
            return None  # No new news
        
        _last_news_hash[symbol] = news_hash
        _last_news_update[symbol] = now
        
        return {
            "headlines": headlines,
            "count": len(headlines),
            "updated_at": now.isoformat() + "Z"
        }
    except Exception as e:
        logger.error(f"Error fetching news for {symbol}: {e}")
        return None


async def save_to_cache(symbol: str, data: Dict[str, Any], news: Optional[Dict[str, Any]] = None):
    """Save data to Supabase cache."""
    if not is_db_available():
        return
    
    client = get_supabase_client()
    if not client:
        return
    
    try:
        # Prepare cache data
        cache_data = {
            "symbol": symbol,
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "ml_prediction": json.dumps(data.get("ml_prediction", {})),
            "ta_snapshot": json.dumps(data.get("ta_snapshot", {})),
            "macro": json.dumps(data.get("macro", {})),
            "session": json.dumps(data.get("session", {})),
            "volume": json.dumps(data.get("volume", {})),
            "volatility": json.dumps(data.get("volatility", {})),
            "context_pack": json.dumps(data),
        }
        
        if news:
            cache_data["news"] = json.dumps(news)
            cache_data["news_updated_at"] = news.get("updated_at")
        
        # Upsert to cache
        result = client.table("live_data_cache").select("id").eq("symbol", symbol).execute()
        
        if result.get("data") and len(result["data"]) > 0:
            # Update existing
            client.table("live_data_cache").eq("symbol", symbol).update(cache_data).execute()
        else:
            # Insert new
            client.table("live_data_cache").insert(cache_data).execute()
            
        logger.debug(f"Cache updated for {symbol}")
    except Exception as e:
        logger.error(f"Error saving cache for {symbol}: {e}")


async def check_outcomes_if_needed():
    """Check prediction outcomes periodically."""
    global _last_outcome_check
    
    now = datetime.utcnow()
    
    # Check if we need to run outcome check
    if _last_outcome_check and (now - _last_outcome_check).total_seconds() < OUTCOME_CHECK_INTERVAL:
        return
    
    _last_outcome_check = now
    
    try:
        # Check 1-hour outcomes
        outcomes_1h = await check_pending_outcomes("1h")
        if outcomes_1h:
            logger.info(f"Checked {len(outcomes_1h)} 1h outcomes")
        
        # Check 24-hour outcomes (less frequently, every hour is enough)
        outcomes_24h = await check_pending_outcomes("24h")
        if outcomes_24h:
            logger.info(f"Checked {len(outcomes_24h)} 24h outcomes")
            
    except Exception as e:
        logger.error(f"Error checking outcomes: {e}")


def _get_cached_panel_data(symbol: str) -> Dict[str, Any]:
    """Read cached panel responses from the panel response cache.
    Panel data is cached by the route handlers when served via HTTP.
    This avoids re-computing heavy analysis in the scheduler cycle."""
    from services.redis_client import cache_get

    panels = {}
    panel_keys = {
        "pulse_v3": f"panel:pulse_v3:{symbol}",
        "emel": f"panel:emel:{symbol}",
        "mtf": f"panel:mtf:{symbol}",
        "clear_trend": f"panel:clear_trend:{symbol}",
    }

    for panel_name, cache_key in panel_keys.items():
        try:
            cached = cache_get(cache_key)
            if cached and not cached.get("error"):
                panels[panel_name] = cached
        except Exception:
            pass

    return panels


async def run_update_cycle():
    """Run one update cycle for all symbols."""
    broadcast_batch = {}

    for symbol in TRACKED_SYMBOLS:
        try:
            # Update market data (ML, TA, price, macro)
            data = await update_symbol_data(symbol)
            if data:
                # Check for news updates
                news = await update_news_if_needed(symbol)
                
                # Save to Supabase cache (legacy)
                await save_to_cache(symbol, data, news)

                # Read cached panel data for broadcast (panels cache their responses via HTTP)
                panel_data = _get_cached_panel_data(symbol)

                # Build broadcast payload — includes ALL data panels need
                broadcast_payload = {
                    "type": "update",
                    "symbol": symbol,
                    "timestamp": data.get("updated_at"),
                    "data": data,
                    "panels": panel_data,
                }
                if news:
                    broadcast_payload["news"] = news

                broadcast_batch[symbol] = broadcast_payload

                # Cache to Redis for instant delivery to new WS connections
                try:
                    from services.redis_client import cache_set
                    cache_set(f"broadcast:{symbol}", broadcast_payload, ttl=300)
                except Exception:
                    pass
                
        except Exception as e:
            logger.error(f"Error in update cycle for {symbol}: {e}")
        
        # Small delay between symbols
        await asyncio.sleep(0.5)

    # Broadcast to all connected WebSocket clients
    if broadcast_batch:
        try:
            from services.ws_manager import manager
            await manager.broadcast_all(broadcast_batch)
            logger.debug(f"Broadcast sent to {manager.total_clients} clients")
        except Exception as e:
            logger.error(f"WebSocket broadcast error: {e}")


async def analyze_errors_if_needed():
    """Analyze failed predictions periodically (every hour)."""
    global _last_error_analysis
    
    now = datetime.utcnow()
    
    # Check if we need to run error analysis
    if _last_error_analysis and (now - _last_error_analysis).total_seconds() < ERROR_ANALYSIS_INTERVAL:
        return
    
    _last_error_analysis = now
    
    try:
        # Analyze predictions that are at least 4 hours old
        analyses = await check_and_analyze_failed_predictions(hours_ago=4, limit=5)
        if analyses:
            logger.info(f"Completed {len(analyses)} error analyses")
    except Exception as e:
        logger.error(f"Error in error analysis: {e}")


async def log_predictions_if_needed():
    """Log predictions to database periodically for learning system."""
    global _last_prediction_log
    
    now = datetime.utcnow()
    
    for symbol in TRACKED_SYMBOLS:
        # Check if we need to log for this symbol
        last_log = _last_prediction_log.get(symbol)
        if last_log and (now - last_log).total_seconds() < PREDICTION_LOG_INTERVAL:
            continue
        
        _last_prediction_log[symbol] = now
        
        try:
            from services.prediction_logger import log_prediction
            from database.supabase_client import is_db_available
            
            if not is_db_available():
                continue
            
            # Get ML prediction
            ml_prediction = await get_ml_prediction(symbol, strategy="balanced")
            
            # Build context for logging
            context = {
                "symbol": symbol,
                "ml_prediction": {
                    "direction": ml_prediction.direction,
                    "confidence": ml_prediction.confidence,
                    "probability_up": ml_prediction.probability_up,
                    "probability_down": ml_prediction.probability_down,
                    "entry_price": ml_prediction.entry_price,
                    "target_price": ml_prediction.target_price,
                    "stop_price": ml_prediction.stop_price,
                },
                "ta": {},
                "distances": {},
                "volume": {},
                "trend_channel": {},
                "macro": {},
                "news": {},
            }
            
            analysis = {
                "final_decision": ml_prediction.direction,
                "confidence": ml_prediction.confidence,
                "model_used": ml_prediction.model_version,
            }
            
            pred_id = await log_prediction(
                symbol=symbol,
                context=context,
                analysis=analysis,
                timeframe="1d",
                strategy="balanced"  # Default strategy for auto-logged predictions
            )
            
            if pred_id:
                logger.info(f"Auto-logged prediction {pred_id[:8]} for {symbol}")
                
        except Exception as e:
            logger.error(f"Error auto-logging prediction for {symbol}: {e}")


async def background_scheduler_loop():
    """Main background scheduler loop."""
    global _scheduler_running
    
    if _scheduler_running:
        logger.warning("Scheduler already running")
        return
    
    _scheduler_running = True
    logger.info("Background scheduler started")
    
    while _scheduler_running:
        try:
            await run_update_cycle()
            # Check outcomes periodically
            await check_outcomes_if_needed()
            # Analyze errors periodically (self-learning)
            await analyze_errors_if_needed()
            # Log predictions periodically for learning
            await log_predictions_if_needed()
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
        
        # Wait before next cycle
        await asyncio.sleep(DATA_UPDATE_INTERVAL)
    
    logger.info("Background scheduler stopped")


def start_scheduler():
    """Start the background scheduler."""
    asyncio.create_task(background_scheduler_loop())
    logger.info("Background scheduler task created")


def stop_scheduler():
    """Stop the background scheduler."""
    global _scheduler_running
    _scheduler_running = False
    logger.info("Background scheduler stop requested")


async def get_cached_data(symbol: str) -> Optional[Dict[str, Any]]:
    """Get cached data from Supabase."""
    if not is_db_available():
        return None
    
    client = get_supabase_client()
    if not client:
        return None
    
    try:
        result = client.table("live_data_cache").select("*").eq("symbol", symbol).execute()
        
        if result.get("data") and len(result["data"]) > 0:
            row = result["data"][0]
            return {
                "symbol": row.get("symbol"),
                "updated_at": row.get("updated_at"),
                "ml_prediction": json.loads(row.get("ml_prediction", "{}")),
                "ta_snapshot": json.loads(row.get("ta_snapshot", "{}")),
                "macro": json.loads(row.get("macro", "{}")),
                "session": json.loads(row.get("session", "{}")),
                "volume": json.loads(row.get("volume", "{}")),
                "volatility": json.loads(row.get("volatility", "{}")),
                "news": json.loads(row.get("news", "{}")),
                "context_pack": json.loads(row.get("context_pack", "{}")),
            }
        return None
    except Exception as e:
        logger.error(f"Error getting cached data for {symbol}: {e}")
        return None
