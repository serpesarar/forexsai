"""
Background Scheduler Service
Runs in the background to continuously update market data and cache to Supabase.
"""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta
from utils.safe_supabase import safe_get_data, safe_get_error
from typing import Dict, Any, Optional, List

from order_block_detector import OrderBlockConfig
from database.supabase_client import get_supabase_client, is_db_available
from services.ml_prediction_service import get_ml_prediction
from services.order_block_service import service as order_block_service
from services.signal_analytics import parse_datetime, timeframe_cadence_minutes
from services.ta_service import compute_ta_snapshot
from services.data_fetcher import fetch_eod_candles, fetch_latest_price
from services.marketaux_service import fetch_marketaux_headlines
from services.outcome_tracker import check_pending_outcomes, check_multi_target_outcome
from services.error_analysis_service import check_and_analyze_failed_predictions
from services.signal_lifecycle import check_lifecycle_if_needed
from utils.market_hours import is_symbol_market_open

logger = logging.getLogger(__name__)

# Symbols to track
TRACKED_SYMBOLS = ["NDX.INDX", "XAUUSD", "GDAXI.INDX", "USOIL.FOREX"]

# Update intervals (seconds) - OPTIMIZED for 100K daily API call limit
# Each EODHD intraday/real-time request = 5 API calls
DATA_UPDATE_INTERVAL = 10    # Update price/TA data every 10 seconds for live prices
MACRO_UPDATE_INTERVAL = 300  # Update macro data (DXY, VIX, USDTRY) every 5 minutes
NEWS_UPDATE_INTERVAL = 600   # Update news every 10 minutes
OUTCOME_CHECK_INTERVAL = 120  # Check outcomes every 2 minutes
ERROR_ANALYSIS_INTERVAL = 3600  # Analyze errors every hour
PREDICTION_LOG_INTERVAL = 900  # Log ML predictions every 15 minutes

# Last update timestamps
_last_news_update: Dict[str, datetime] = {}
_last_news_hash: Dict[str, str] = {}
_last_outcome_check: Optional[datetime] = None
_last_error_analysis: Optional[datetime] = None
_last_prediction_log: Dict[str, datetime] = {}  # Per symbol
_last_pulse_log: Dict[str, datetime] = {}  # Per symbol, for Pulse signal logging
PULSE_LOG_INTERVAL = 180  # Log Pulse/EMEL signals every 3 minutes (sync with lifecycle)
_last_smc_log: Optional[datetime] = None
_last_smc_scope_log: Dict[tuple[str, str], datetime] = {}
SMC_LOG_INTERVAL = 180
_last_macro_update: Optional[datetime] = None
_cached_macro: Dict[str, Any] = {}  # Cached macro data

# Legacy/default scheduler logging targets.
# Intentionally excludes emel_inverse and post-expansion multi-timeframe loops
# so the historical model-performance panels keep only the original main history.
LEGACY_PULSE_LOG_TIMEFRAMES: Dict[str, str] = {
    "emel": "1h",
    "pulse1": "5m",
    "pulse2": "15m",
    "pulse3": "5m",
}

ML_AUTO_LOG_SCOPES: List[tuple[str, str]] = [
    ("main", "ml:main"),
    ("ultra_safe", "ml:ultra_safe"),
    ("balanced", "ml:balanced"),
    ("full_power", "ml:full_power"),
    ("aggressive", "ml:aggressive"),
]
NASDAQ_FAMILY_ML_AUTO_LOG_SCOPES: List[tuple[str, str]] = [
    ("nasdaq_precision", "ml:nasdaq_precision"),
]
NASDAQ_FAMILY_SYMBOLS = {"NDX.INDX", "GDAXI.INDX"}
SMC_AUTO_LOG_TIMEFRAMES = ["5m", "15m", "1h", "4h"]


def _get_ml_auto_log_scopes(symbol: str) -> List[tuple[str, str]]:
    scopes = list(ML_AUTO_LOG_SCOPES)
    if (symbol or "").upper().strip() in NASDAQ_FAMILY_SYMBOLS:
        scopes.extend(NASDAQ_FAMILY_ML_AUTO_LOG_SCOPES)
    return scopes


def _get_last_persisted_smc_log_time(symbol: str, timeframe: str) -> Optional[datetime]:
    if not is_db_available():
        return None

    client = get_supabase_client()
    if client is None:
        return None

    try:
        result = client.table("prediction_logs").select(
            "created_at"
        ).eq(
            "symbol", symbol
        ).eq(
            "model_type", "smc"
        ).eq(
            "timeframe", timeframe
        ).order(
            "created_at", desc=True
        ).limit(1).execute()
        rows = safe_get_data(result) or []
        if not rows:
            return None
        return parse_datetime(rows[0].get("created_at"))
    except Exception as exc:
        logger.debug("smc last persisted lookup failed for %s %s: %s", symbol, timeframe, exc)
        return None


def _resolve_last_smc_log_time(symbol: str, timeframe: str) -> Optional[datetime]:
    memory_last = _last_smc_scope_log.get((symbol, timeframe))
    db_last = _get_last_persisted_smc_log_time(symbol, timeframe)
    if memory_last and db_last:
        return max(memory_last, db_last)
    return memory_last or db_last


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
    for key, sym in [("dxy", "DXY.INDX"), ("vix", "VIX.INDX"), ("vdax", "V1X.INDX"), ("eurusd", "EURUSD"), ("usdtry", "USDTRY")]:
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
        elif 7 <= hour_utc < 16:
            session = "europe_open"  # XETRA: 07:00-15:30 UTC
        elif 0 <= hour_utc < 8:
            session = "asia_open"
        
        # DAX-specific: mark XETRA session precisely
        if symbol == "GDAXI.INDX":
            if 7 <= hour_utc < 15 or (hour_utc == 15 and now_utc.minute <= 30):
                session = "xetra_open"
            elif 15 < hour_utc < 21:
                session = "us_overlap"  # DAX afterhours but US still open
            elif hour_utc >= 21 or hour_utc < 7:
                session = "closed"
        
        # Volume (simplified)
        volume_data = {
            "status": "NORMAL",
            "ratio": 1.0
        }
        
        # Volatility assessment
        # Use VDAX for DAX, VIX for everything else
        if symbol == "GDAXI.INDX":
            vol_price = macro.get("vdax", {}).get("price")
            vol_index_name = "VDAX"
        else:
            vol_price = macro.get("vix", {}).get("price")
            vol_index_name = "VIX"
        
        # DAX-specific volatility thresholds (VDAX is structurally lower than VIX)
        if symbol == "GDAXI.INDX":
            if vol_price and vol_price > 25:
                volatility_level = "EXTREME"
            elif vol_price and vol_price > 18:
                volatility_level = "HIGH"
            elif vol_price and vol_price < 12:
                volatility_level = "LOW"
            else:
                volatility_level = "NORMAL"
        else:
            if vol_price and vol_price > 30:
                volatility_level = "EXTREME"
            elif vol_price and vol_price > 20:
                volatility_level = "HIGH"
            elif vol_price and vol_price < 15:
                volatility_level = "LOW"
            else:
                volatility_level = "NORMAL"
        
        # Correlation matrix (DAX-specific)
        correlation = {}
        if symbol == "GDAXI.INDX":
            eurusd_price = macro.get("eurusd", {}).get("price")
            vdax_price = macro.get("vdax", {}).get("price")
            dxy_price = macro.get("dxy", {}).get("price")
            correlation = {
                "eurusd": {
                    "price": eurusd_price,
                    "direction": "negative",
                    "note": "Strong EUR = weaker DAX exports"
                },
                "vdax": {
                    "price": vdax_price,
                    "risk_level": "extreme" if vdax_price and vdax_price > 25 else "high" if vdax_price and vdax_price > 18 else "normal",
                    "note": "VDAX >18 = elevated risk, >25 = danger zone"
                },
                "dxy": {
                    "price": dxy_price,
                    "direction": "inverse",
                    "note": "Strong USD = pressure on European equities"
                },
            }
        
        return {
            "symbol": symbol,
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "ml_prediction": ml_dict,
            "ta_snapshot": ta_snapshot,
            "current_price": float(current_price) if current_price else None,
            "macro": macro,
            "session": {"current": session, "hour_utc": hour_utc},
            "volume": volume_data,
            "volatility": {"level": volatility_level, "index_price": vol_price, "index_name": vol_index_name},
            "correlation": correlation,
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
        if "XAU" in symbol:
            news_symbols = ["XAUUSD", "GOLD", "DXY", "USD"]
        elif "GDAXI" in symbol:
            news_symbols = ["DAX", "GER40", "GDAXI", "EURUSD", "ECB", "SAP", "Siemens", "Allianz", "BASF", "Deutsche Bank", "German IFO", "ZEW", "Bundesbank", "German GDP"]
        else:
            news_symbols = ["NDX", "NASDAQ", "VIX", "DXY"]
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


_cache_last_save: Dict[str, float] = {}  # symbol → last save epoch
CACHE_SAVE_INTERVAL = 300                # 5 minutes between Supabase cache writes


async def save_to_cache(symbol: str, data: Dict[str, Any], news: Optional[Dict[str, Any]] = None):
    """Save data to Supabase cache — throttled to every 5 min per symbol."""
    import time as _time
    now = _time.time()
    if now - _cache_last_save.get(symbol, 0) < CACHE_SAVE_INTERVAL:
        return
    
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
        
        if safe_get_data(result) and len(result["data"]) > 0:
            # Update existing — .eq() before .update(), no .execute() needed
            client.table("live_data_cache").eq("symbol", symbol).update(cache_data)
        else:
            # Insert new — .insert() auto-executes, no .execute() needed
            client.table("live_data_cache").insert(cache_data)
            
        _cache_last_save[symbol] = now
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
            if cached and not safe_get_error(cached):
                panels[panel_name] = cached
        except Exception:
            pass

    return panels


async def _warm_pulse_panel_cache(symbol: str) -> None:
    from routers.emel_pulse import get_pulse_analysis, get_pulse_ml_analysis, get_pulse_v3_analysis

    try:
        await get_pulse_analysis(symbol, timeframe="5m")
    except Exception as e:
        logger.debug(f"Pulse 1 warm cache skipped for {symbol}: {e}")

    try:
        await get_pulse_ml_analysis(symbol, timeframe="15m")
    except Exception as e:
        logger.debug(f"Pulse 2 warm cache skipped for {symbol}: {e}")

    try:
        await get_pulse_v3_analysis(symbol, timeframe="5m")
    except Exception as e:
        logger.debug(f"Pulse 3 warm cache skipped for {symbol}: {e}")


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

                await _warm_pulse_panel_cache(symbol)

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
            
            for strategy_scope, scoped_model_type in _get_ml_auto_log_scopes(symbol):
                ml_prediction = await get_ml_prediction(symbol, strategy=strategy_scope)

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
                    "source": "ml_scheduler",
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
                    timeframe="30m",
                    strategy=strategy_scope,
                    model_type=scoped_model_type,
                )

                if pred_id:
                    logger.info(
                        "Auto-logged prediction %s for %s (%s)",
                        pred_id[:8],
                        symbol,
                        scoped_model_type,
                    )
                
        except Exception as e:
            logger.error(f"Error auto-logging prediction for {symbol}: {e}")


async def _log_pulse_signal(symbol: str, direction: str, confidence: float,
                           entry_price: float, model_type: str, strategy: str,
                           timeframe: str = "5m",
                           ta: dict = None, extra: dict = None):
    """Helper: log a Pulse/EMEL signal to prediction_logs via log_prediction()."""
    try:
        from services.prediction_logger import log_prediction

        context = {
            "symbol": symbol,
            "ta": ta or {},
            "source": strategy,
            "ml_prediction": {
                "direction": direction,
                "confidence": confidence,
                "entry_price": entry_price,
                "target_price": None,
                "stop_price": None,
            },
            "distances": {},
            "volume": {},
            "trend_channel": {},
            "macro": {},
            "news": {},
        }
        if extra:
            context.update(extra)

        analysis = {
            "final_decision": direction,
            "confidence": confidence,
            "model_used": strategy,
        }

        pred_id = await log_prediction(
            symbol=symbol,
            context=context,
            analysis=analysis,
            timeframe=timeframe,
            strategy=strategy,
            model_type=model_type,
        )
        if pred_id:
            logger.info(f"✅ {symbol} {model_type} sinyali kaydedildi: {direction} (id={pred_id[:8]})")
            return pred_id
        else:
            logger.debug(f"⏭️ {symbol} {model_type} sinyeli atlandı (duplicate veya cooldown)")
            return None
    except Exception as e:
        logger.error(f"❌ {symbol} {model_type} kayıt hatası: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None


async def log_pulse_signals_if_needed():
    """Check all Pulse/EMEL models for all symbols and log BUY/SELL signals.
    Runs every PULSE_LOG_INTERVAL. Dedup handled by prediction_logger (active signal check)."""
    global _last_pulse_log

    now = datetime.utcnow()

    for symbol in TRACKED_SYMBOLS:
        last_log = _last_pulse_log.get(symbol)
        if last_log and (now - last_log).total_seconds() < PULSE_LOG_INTERVAL:
            continue

        _last_pulse_log[symbol] = now

        if not is_db_available():
            continue

        for model_type, tf in LEGACY_PULSE_LOG_TIMEFRAMES.items():
            try:
                await _check_and_log_pulse(symbol, model_type, None, tf)
                await asyncio.sleep(0.3)
            except Exception as e:
                logger.error(f"{model_type} {tf} log error {symbol}: {e}")


async def log_smc_signals_if_needed():
    global _last_smc_log

    now = datetime.utcnow()
    if _last_smc_log and (now - _last_smc_log).total_seconds() < SMC_LOG_INTERVAL:
        return

    _last_smc_log = now

    config = OrderBlockConfig(
        fractal_period=2,
        min_displacement_atr=1.0,
        min_score=45,
        zone_type="wick",
        max_tests=3,
    )

    for symbol in TRACKED_SYMBOLS:
        if not is_symbol_market_open(symbol, now):
            continue
        for timeframe in SMC_AUTO_LOG_TIMEFRAMES:
            cadence_minutes = timeframe_cadence_minutes(timeframe) or max(int(SMC_LOG_INTERVAL / 60), 1)
            last_scope_log = _resolve_last_smc_log_time(symbol, timeframe)
            if last_scope_log and (now - last_scope_log).total_seconds() < cadence_minutes * 60:
                continue
            try:
                await order_block_service.detect(
                    symbol,
                    timeframe,
                    500,
                    config,
                    use_cache=False,
                    log_signals=True,
                )
                _last_smc_scope_log[(symbol, timeframe)] = now
                await asyncio.sleep(0.15)
            except Exception as e:
                logger.error(f"smc {symbol} {timeframe} log error: {e}")


async def _check_and_log_pulse(symbol: str, model_type: str, client, timeframe: str = "5m"):
    """Run one model's analysis for one symbol and log if BUY/SELL."""
    try:
        from routers.emel_pulse import get_pulse_v3_analysis, get_pulse_ml_analysis, get_pulse_analysis, get_emel_analysis

        if model_type == "pulse3":
            result = await get_pulse_v3_analysis(symbol, timeframe=timeframe)
            strategy, sig_key = "PULSE_V3", "direction"
        elif model_type == "pulse2":
            result = await get_pulse_ml_analysis(symbol, timeframe=timeframe)
            strategy, sig_key = "PULSE_ML", "signal"
        elif model_type == "pulse1":
            result = await get_pulse_analysis(symbol, timeframe=timeframe)
            strategy, sig_key = "PULSE_V1", "signal"
        elif model_type in ["emel", "emel_inverse"]:
            result = await get_emel_analysis(symbol, timeframe=timeframe)
            strategy, sig_key = "EMEL", "signal"
        else:
            return

        if not isinstance(result, dict) or safe_get_error(result):
            return

        sig = result.get(sig_key, "HOLD")
        if sig not in ("BUY", "SELL"):
            return

        # Extract entry price — handle dict format from Pulse 1 ({"current": 24898.87})
        entry = result.get("entry_price")
        if not entry:
            price_field = result.get("price", 0)
            if isinstance(price_field, dict):
                entry = price_field.get("current", 0)
            else:
                entry = price_field
        if not entry or not isinstance(entry, (int, float)) or entry <= 0:
            logger.debug(f"{model_type} {symbol}: no valid entry price, skipping")
            return
        conf = result.get("confidence", 50) or 50
        
        # Determine actual model constraint explicitly 
        final_model_type = model_type
        if model_type == "emel_inverse":
            # the reverse logic is usually integrated in the emel_pulse API itself,
            # but if this is just logging directly from here, we need to enforce that sig is inverted
            sig = "SELL" if sig == "BUY" else ("BUY" if sig == "SELL" else "HOLD")
            strategy = "EMEL_INVERSE"
            
        await _log_pulse_signal(symbol, sig, conf, entry, final_model_type, strategy, timeframe)

    except Exception as e:
        logger.error(f"{model_type} log error {symbol}: {e}")


async def _check_and_catchup():
    """On startup, check scheduler_state for stale jobs. If lifecycle_check
    hasn't run in >10 min, force an immediate lifecycle pass. Non-blocking."""
    if not is_db_available():
        return
    client = get_supabase_client()
    if not client:
        return
    try:
        result = client.table("scheduler_state").select(
            "job_name, last_run_at"
        ).eq("job_name", "lifecycle_check").limit(1).execute()
        rows = safe_get_data(result)
        if not rows:
            return
        last_run = rows[0].get("last_run_at")
        if last_run:
            from datetime import datetime, timezone
            last_dt = datetime.fromisoformat(last_run.replace("Z", "+00:00"))
            age_s = (datetime.now(timezone.utc) - last_dt).total_seconds()
            if age_s > 600:  # >10 min stale
                logger.info(f"scheduler.catchup | lifecycle_check stale ({age_s:.0f}s ago), running immediate pass")
                await check_lifecycle_if_needed()
            else:
                logger.info(f"scheduler.catchup | lifecycle_check fresh ({age_s:.0f}s ago), no catch-up needed")
        else:
            logger.info("scheduler.catchup | lifecycle_check never ran, running immediate pass")
            await check_lifecycle_if_needed()
    except Exception as e:
        logger.debug(f"scheduler.catchup error: {e}")


async def background_scheduler_loop():
    """Main background scheduler loop."""
    global _scheduler_running
    
    if _scheduler_running:
        logger.warning("Scheduler already running")
        return
    
    _scheduler_running = True
    logger.info("Background scheduler started")

    # Non-blocking catch-up: check if jobs are stale from previous crash/restart
    try:
        await _check_and_catchup()
    except Exception as e:
        logger.debug(f"Catch-up error (non-fatal): {e}")
    
    while _scheduler_running:
        try:
            await run_update_cycle()
            # Check outcomes periodically
            await check_outcomes_if_needed()
            # Signal lifecycle: price check every 3 min (internally gated)
            await check_lifecycle_if_needed()
            # Analyze errors periodically (self-learning)
            await analyze_errors_if_needed()
            # Log ML predictions every 15 min
            await log_predictions_if_needed()
            # Log Pulse/EMEL signals every 15 min
            await log_pulse_signals_if_needed()
            await log_smc_signals_if_needed()
            from services.ai_panel_signal_logger import log_ai_panel_signals_if_needed
            await log_ai_panel_signals_if_needed()
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
        
        if safe_get_data(result) and len(result["data"]) > 0:
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


# RSS Aggregation tracking
_last_rss_update: Optional[datetime] = None
RSS_UPDATE_INTERVAL = 420  # 7 minutes for RSS feeds (was 2 min)


async def run_rss_aggregation_if_needed():
    """Run RSS aggregation every 7 minutes (optimized for cost)"""
    global _last_rss_update
    
    now = datetime.utcnow()
    
    # Check if we need to run RSS aggregation
    if _last_rss_update and (now - _last_rss_update).total_seconds() < RSS_UPDATE_INTERVAL:
        return
    
    _last_rss_update = now
    
    try:
        from services.rss_aggregator import get_rss_aggregator
        
        aggregator = get_rss_aggregator()
        stats = await aggregator.run_aggregation_cycle()
        
        if stats["new"] > 0 or stats["ai_analyzed"] > 0:
            logger.info(f"RSS aggregation: {stats}")
    
    except Exception as e:
        logger.error(f"RSS aggregation error: {e}")


# Pattern Analysis tracking - günde 2 kez
_last_pattern_analysis: Optional[datetime] = None

async def run_pattern_analysis_if_needed():
    """Run pattern analysis twice daily:
    1. US market açılışından 1 saat sonra (15:30 UTC)
    2. US market kapanışından 2 saat önce (19:00 UTC)
    """
    global _last_pattern_analysis
    
    now = datetime.utcnow()
    hour = now.hour
    minute = now.minute
    
    # US açılış: 14:30 UTC -> 1 saat sonra: 15:30 UTC
    # US kapanış: 21:00 UTC -> 2 saat önce: 19:00 UTC
    
    is_analysis_time = (
        (hour == 15 and minute >= 25 and minute <= 35) or  # 15:30 ±5dk
        (hour == 19 and minute >= 0 and minute <= 10)      # 19:00 ±5dk
    )
    
    if not is_analysis_time:
        return
    
    # Son çalışmadan en az 2 saat geçmiş mi?
    if _last_pattern_analysis and (now - _last_pattern_analysis).total_seconds() < 7200:
        return
    
    _last_pattern_analysis = now
    
    # Pattern analyzer disabled
    logger.info(f"Pattern analysis skipped (disabled) at {hour}:{minute:02d} UTC")


# Patch the background_scheduler_loop to include RSS
_original_background_scheduler_loop = background_scheduler_loop


async def background_scheduler_loop_with_rss():
    """Main background scheduler loop with RSS support."""
    global _scheduler_running
    
    if _scheduler_running:
        logger.warning("Scheduler already running")
        return
    
    _scheduler_running = True
    logger.info("Background scheduler started (with RSS support)")

    # Non-blocking catch-up: check if jobs are stale from previous crash/restart
    try:
        await _check_and_catchup()
    except Exception as e:
        logger.debug(f"Catch-up error (non-fatal): {e}")
    
    while _scheduler_running:
        try:
            await run_update_cycle()
            # Check outcomes periodically
            await check_outcomes_if_needed()
            # Signal lifecycle: price check every 3 min (internally gated)
            await check_lifecycle_if_needed()
            # Analyze errors periodically (self-learning)
            await analyze_errors_if_needed()
            # Log ML predictions every 15 min
            await log_predictions_if_needed()
            # Log Pulse/EMEL signals every 15 min
            await log_pulse_signals_if_needed()
            await log_smc_signals_if_needed()
            from services.ai_panel_signal_logger import log_ai_panel_signals_if_needed
            await log_ai_panel_signals_if_needed()
            # RSS aggregation disabled locally since Python listener performs it
            # await run_rss_aggregation_if_needed()
            # Pattern analysis twice daily (US open +1h, close -2h)
            await run_pattern_analysis_if_needed()
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
        
        # Wait before next cycle
        await asyncio.sleep(DATA_UPDATE_INTERVAL)
    
    logger.info("Background scheduler stopped")


# Replace the original function
import sys
sys.modules[__name__].background_scheduler_loop = background_scheduler_loop_with_rss
