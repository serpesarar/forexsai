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

logger = logging.getLogger(__name__)

# Symbols to track
TRACKED_SYMBOLS = ["NDX.INDX", "XAUUSD"]

# Update intervals (seconds)
DATA_UPDATE_INTERVAL = 5  # Update price/TA data every 5 seconds
NEWS_UPDATE_INTERVAL = 300  # Update news every 5 minutes

# Last news update timestamps
_last_news_update: Dict[str, datetime] = {}
_last_news_hash: Dict[str, str] = {}

# Scheduler running flag
_scheduler_running = False


async def update_symbol_data(symbol: str) -> Optional[Dict[str, Any]]:
    """Fetch and update data for a single symbol."""
    try:
        # Get ML prediction
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
        
        # Get latest price
        current_price = await fetch_latest_price(symbol)
        
        # Get macro data
        macro = {}
        for key, sym in [("dxy", "DXY.INDX"), ("vix", "VIX.INDX"), ("usdtry", "USDTRY")]:
            price = await fetch_latest_price(sym)
            macro[key] = {"symbol": sym, "price": float(price) if price else None}
        
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


async def run_update_cycle():
    """Run one update cycle for all symbols."""
    for symbol in TRACKED_SYMBOLS:
        try:
            # Update market data
            data = await update_symbol_data(symbol)
            if data:
                # Check for news updates
                news = await update_news_if_needed(symbol)
                
                # Save to cache
                await save_to_cache(symbol, data, news)
                
        except Exception as e:
            logger.error(f"Error in update cycle for {symbol}: {e}")
        
        # Small delay between symbols
        await asyncio.sleep(0.5)


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
