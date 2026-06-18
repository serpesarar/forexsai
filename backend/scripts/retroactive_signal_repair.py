import os
import sys
import asyncio
from datetime import datetime, timedelta, timezone

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings
if settings.supabase_url:
    os.environ["SUPABASE_URL"] = settings.supabase_url
if settings.supabase_key:
    os.environ["SUPABASE_SERVICE_ROLE_KEY"] = settings.supabase_key
    os.environ["SUPABASE_KEY"] = settings.supabase_key

from database.supabase_client import get_supabase_client
client = get_supabase_client()

from services.target_config import (
    calculate_target_prices,
    calculate_stoploss_price,
    pips_from_price_change,
)
from services.data_fetcher import fetch_intraday_candles
from utils.json_helpers import parse_json_field

def _as_utc(dt: datetime) -> datetime:
    return dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)

def _parse_dt(val) -> datetime:
    if not val:
        return datetime.now(timezone.utc)
    if isinstance(val, datetime):
        return _as_utc(val)
    val_str = str(val).strip()
    if val_str.endswith("Z"):
        val_str = val_str[:-1] + "+00:00"
    try:
        return _as_utc(datetime.fromisoformat(val_str))
    except ValueError:
        pass
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S%z", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return _as_utc(datetime.strptime(val_str, fmt))
        except ValueError:
            continue
    return _as_utc(datetime.now(timezone.utc))

def _utc_now() -> datetime:
    return datetime.now(timezone.utc)

def _utc_iso(dt: Optional[datetime] = None) -> str:
    return _as_utc(dt or _utc_now()).isoformat().replace("+00:00", "Z")

def _parse_candle_time(c: dict) -> datetime:
    ts = c.get("timestamp")
    if ts:
        return datetime.fromtimestamp(ts / 1000.0, tz=timezone.utc)
    date_val = c.get("date") or c.get("candle_time")
    if not date_val:
        return _utc_now()
    if isinstance(date_val, datetime):
        return _as_utc(date_val)
    return _parse_dt(date_val)

# average spread mapping
SYMBOL_SPREADS = {
    "NDX.INDX": 1.5,
    "XAUUSD": 2.5,
    "GDAXI.INDX": 2.0,
    "USOIL.FOREX": 3.0,
}

def get_pip_size(sym: str) -> float:
    sym_upper = sym.upper()
    if "XAUUSD" in sym_upper:
        return 0.1
    if "USOIL" in sym_upper or "CL.COMM" in sym_upper:
        return 0.01
    return 1.0

async def fetch_historical_signals(days=2):
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat().replace("+00:00", "Z")
    print(f"Fetching resolved signals since {cutoff}...")
    
    signals = []
    offset = 0
    chunk_size = 1000
    while True:
        try:
            res = client.table("prediction_logs") \
                .select("id, symbol, model_type, status, ml_direction, ml_entry_price, created_at, exit_price, exit_time, targets, stop_loss_pips, highest_profit_pips, lowest_drawdown_pips, resolution_reason") \
                .in_("status", ["completed", "stopped", "expired"]) \
                .gte("created_at", cutoff) \
                .range(offset, offset + chunk_size - 1) \
                .execute()
            data = res.data if hasattr(res, "data") else res.get("data") or []
            signals.extend(data)
            if len(data) < chunk_size:
                break
            offset += chunk_size
        except Exception as e:
            print("Error fetching signals:", e)
            break
            
    print(f"Retrieved {len(signals)} resolved signals.")
    return sorted(signals, key=lambda x: x.get("created_at") or "")

async def fetch_5m_candles_fallback(symbol, start_dt, end_dt):
    """Fallback to fetch 5m candles from candle_cache if 1m is not available."""
    start_iso = start_dt.isoformat().replace("+00:00", "Z")
    end_iso = end_dt.isoformat().replace("+00:00", "Z")
    try:
        res = client.table("candle_cache") \
            .select("candle_time, open, high, low, close, volume") \
            .eq("symbol", symbol) \
            .eq("timeframe", "5m") \
            .gte("candle_time", start_iso) \
            .lte("candle_time", end_iso) \
            .order("candle_time", desc=False) \
            .execute()
        data = res.data if hasattr(res, "data") else res.get("data") or []
        
        candles = []
        for row in data:
            ct = row["candle_time"]
            try:
                dt = _parse_dt(ct)
                ts = int(dt.timestamp() * 1000)
            except Exception:
                ts = 0
            candles.append({
                "timestamp": ts,
                "date": ct,
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row["volume"]),
            })
        return candles
    except Exception as e:
        print(f"Error loading 5m candles fallback for {symbol}: {e}")
        return []

async def evaluate_signal_chronologically(sig):
    sig_id = sig["id"]
    symbol = sig["symbol"]
    timeframe = sig.get("timeframe") or "30m"
    direction = sig.get("ml_direction")
    entry_price = float(sig.get("ml_entry_price") or 0.0)
    created_at_str = sig.get("created_at")
    status_db = sig.get("status")
    
    if not entry_price or not direction or direction not in {"BUY", "SELL"}:
        return None
        
    created_dt = _parse_dt(created_at_str)
    
    def _evaluation_window_minutes(tf):
        tf_clean = tf.lower().strip()
        if tf_clean == "1m": return 15
        if tf_clean == "5m": return 60
        if tf_clean == "15m": return 180
        if tf_clean == "30m": return 360
        if tf_clean == "1h": return 720
        if tf_clean == "4h": return 1440
        if tf_clean in ("eod", "1d"): return 4320
        return 360
        
    eval_minutes = _evaluation_window_minutes(timeframe)
    end_dt = created_dt + timedelta(minutes=eval_minutes + 15)
    
    # 1. Try to fetch 1m candles using our new dynamic fetcher
    age_minutes = (datetime.now(timezone.utc) - created_dt).total_seconds() / 60.0
    candle_limit = max(30, int(age_minutes) + 10)
    
    candles = []
    # Only fetch 1m if signal is recent (under 5 days) to avoid upstream vendor limit exhaustion
    if age_minutes < 7200: 
        try:
            candles = await fetch_intraday_candles(symbol, interval="1m", limit=candle_limit)
            # Filter candles starting from created_at
            cutoff_ms = created_dt.timestamp() * 1000
            candles = [c for c in candles if c.get("timestamp", 0) >= cutoff_ms]
        except Exception as e:
            print(f"Failed fetching 1m candles for {symbol}: {e}")
            
    # 2. Fallback to 5m candles if 1m is empty or unavailable
    if not candles:
        candles = await fetch_5m_candles_fallback(symbol, created_dt, end_dt)
        
    if not candles:
        return None
        
    # Reconstruct TP / SL prices
    tp_prices = calculate_target_prices(entry_price, direction, symbol, timeframe)
    sl_price = calculate_stoploss_price(entry_price, direction, symbol, timeframe)
    
    pip_size = get_pip_size(symbol)
    spread = SYMBOL_SPREADS.get(symbol, 2.0) * pip_size
    slippage = 1.0 * pip_size
    
    simulation_status = "active"
    exit_time = None
    exit_price = None
    targets_hit = {}
    targets_hit_times = {}
    
    high_reached = 0.0
    low_reached = 0.0
    
    for c in candles:
        c_time = _parse_candle_time(c)
        c_date = c.get("date") or _utc_iso(c_time)
        
        # Pre-entry wick guard: skip candle if it closed before or exactly at entry (within 60s)
        if (c_time - created_dt).total_seconds() < 60:
            continue
            
        c_high = float(c["high"])
        c_low = float(c["low"])
        c_close = float(c["close"])
        
        # Calculate running profit/drawdown
        if direction == "BUY":
            prof = pips_from_price_change(c_high - entry_price, symbol)
            draw = pips_from_price_change(c_low - entry_price, symbol)
        else:
            prof = pips_from_price_change(entry_price - c_low, symbol)
            draw = pips_from_price_change(entry_price - c_high, symbol)
            
        high_reached = max(high_reached, prof)
        low_reached = min(low_reached, draw)
        
        # Check TP hits
        for tp_name, tp_val in tp_prices.items():
            if targets_hit.get(tp_name):
                continue
            
            # Spread-aware target detection
            tp_pips_distance = abs(pips_from_price_change(abs(tp_val - entry_price), symbol))
            tp_drawdown_ok = tp_pips_distance <= 0 or high_reached >= tp_pips_distance * 0.6
            
            if direction == "BUY" and (c_high - spread) >= tp_val and tp_drawdown_ok:
                targets_hit[tp_name] = True
                targets_hit_times[tp_name] = c_date
            elif direction == "SELL" and (c_low + spread) <= tp_val and tp_drawdown_ok:
                targets_hit[tp_name] = True
                targets_hit_times[tp_name] = c_date
                
        # Check SL hit
        hit_stop = False
        sl_drawdown_ok = sl_price <= 0 or abs(low_reached) >= abs(pips_from_price_change(abs(entry_price - sl_price), symbol)) * 0.6
        if direction == "BUY" and c_low <= (sl_price + slippage) and sl_drawdown_ok:
            hit_stop = True
        elif direction == "SELL" and c_high >= (sl_price - slippage) and sl_drawdown_ok:
            hit_stop = True
            
        tp1_3_hit = any(tp in {"TP1", "TP2", "TP3"} for tp in targets_hit)
        
        if hit_stop:
            if tp1_3_hit:
                simulation_status = "completed"
                earliest_tp = min(targets_hit_times.keys(), key=lambda k: targets_hit_times[k])
                exit_time = targets_hit_times[earliest_tp]
                exit_price = tp_prices[earliest_tp]
                resolution_reason = "tp1_3_hit_then_sl"
                break
            else:
                simulation_status = "stopped"
                exit_time = c_date
                exit_price = sl_price
                resolution_reason = "sl_hit"
                break
                
        if targets_hit.get("TP4"):
            simulation_status = "completed"
            exit_time = targets_hit_times["TP4"]
            exit_price = tp_prices["TP4"]
            resolution_reason = "tp4_hit"
            break
            
    if simulation_status == "active" and candles:
        last_c = candles[-1]
        last_c_time = _parse_candle_time(last_c)
        last_c_date = last_c.get("date") or _utc_iso(last_c_time)
        last_c_close = float(last_c["close"])
        
        tp1_3_hit = any(tp in {"TP1", "TP2", "TP3"} for tp in targets_hit)
        tp1_distance = 0.0
        if tp_prices:
            try:
                tp1_price = tp_prices.get("TP1")
                if tp1_price and entry_price:
                    tp1_distance = abs(float(tp1_price) - float(entry_price))
            except Exception:
                pass
        real_tp_reached = tp1_3_hit or (
            tp1_distance > 0 and high_reached >= tp1_distance * 0.95
        )
        
        favorable_vs_entry = (direction == "BUY" and last_c_close > entry_price) or (direction == "SELL" and last_c_close < entry_price)
        
        if real_tp_reached:
            simulation_status = "completed"
            if targets_hit_times:
                earliest_tp = min(targets_hit_times.keys(), key=lambda k: targets_hit_times[k])
                exit_time = targets_hit_times[earliest_tp]
                exit_price = tp_prices[earliest_tp]
            else:
                exit_time = last_c_date
                exit_price = last_c_close
            resolution_reason = "window_resolve_positive"
        elif favorable_vs_entry:
            simulation_status = "expired"
            exit_time = last_c_date
            exit_price = last_c_close
            resolution_reason = "window_resolve_inconclusive"
        else:
            simulation_status = "stopped"
            exit_time = last_c_date
            exit_price = last_c_close
            resolution_reason = "window_resolve_negative"

    return {
        "id": sig_id,
        "symbol": symbol,
        "timeframe": timeframe,
        "direction": direction,
        "entry_price": entry_price,
        "created_at": created_at_str,
        "status_db": status_db,
        "status_sim": simulation_status,
        "exit_price": exit_price,
        "exit_time": exit_time,
        "resolution_reason": resolution_reason,
        "high_reached": high_reached,
        "low_reached": low_reached,
        "targets_hit": targets_hit,
        "target_prices": tp_prices,
        "resolved_sl_pips": abs(pips_from_price_change(abs(entry_price - sl_price), symbol))
    }

async def main():
    days = 2
    if len(sys.argv) > 1:
        try:
            days = int(sys.argv[1])
        except ValueError:
            pass
            
    print(f"=== RETROACTIVE SIGNAL REPAIR STARTED (WINDOW: {days} DAYS) ===")
    signals = await fetch_historical_signals(days)
    
    if not signals:
        print("No resolved signals found to repair.")
        return
        
    mismatches = []
    processed = 0
    repaired = 0
    
    # Process sequentially to avoid database lock issues
    for sig in signals:
        processed += 1
        if processed % 50 == 0:
            print(f"  Processed {processed}/{len(signals)} signals...")
            
        audit_res = await evaluate_signal_chronologically(sig)
        if not audit_res:
            continue
            
        status_db = audit_res["status_db"]
        status_sim = audit_res["status_sim"]
        
        # We consider expired in DB as stopped if simulated as stopped
        is_mismatch = (status_db != status_sim) and not (status_db == "expired" and status_sim == "stopped")
        
        if is_mismatch:
            repaired += 1
            mismatches.append(audit_res)
            
            # Perform DB repair update
            update_data = {
                "status": status_sim,
                "exit_price": round(float(audit_res["exit_price"]), 4) if audit_res["exit_price"] else None,
                "exit_time": audit_res["exit_time"],
                "resolution_reason": f"repair:{audit_res['resolution_reason']}",
                "highest_profit_pips": round(audit_res["high_reached"], 2),
                "lowest_drawdown_pips": round(audit_res["low_reached"], 2),
                "targets_hit": dict(audit_res["targets_hit"]),
                "targets": dict(audit_res["target_prices"]),
                "stop_loss_pips": round(audit_res["resolved_sl_pips"], 2)
            }
            
            try:
                client.table("prediction_logs").eq("id", sig["id"]).update(update_data)
                print(f"  [REPAIRED] ID: {sig['id'][:8]} | Symbol: {audit_res['symbol']} | Model: {sig['model_type']} | DB: {status_db.upper()} -> Sim: {status_sim.upper()} (Reason: {audit_res['resolution_reason']})")
            except Exception as e:
                print(f"  [ERROR] Failed to update signal {sig['id']}: {e}")
                
        # Limit parallel execution stress
        await asyncio.sleep(0.05)
        
    print("\n=== REPAIR WORK SUMMARY ===")
    print(f"Total resolved signals processed: {processed}")
    print(f"Total incorrect outcomes repaired in DB: {repaired}")
    print(f"Repair Success Rate: {((processed - repaired) / processed) * 100:.2f}% accurate outcomes before repair")
    print("===========================")

if __name__ == "__main__":
    asyncio.run(main())
