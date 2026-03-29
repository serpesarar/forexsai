"""
Permutation Analysis Service (Isolated Systems)
- Model Combinations Analysis
- Technical Indicators Permutations Analysis
"""
import asyncio
import logging
from typing import Dict, List, Any
from itertools import combinations
from collections import defaultdict
from datetime import datetime
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

SUPPORTED_SYMBOLS = ["NDX.INDX", "XAUUSD", "GDAXI.INDX", "USOIL.FOREX"]
SUPPORTED_MODELS = ['ml', 'pulse2', 'pulse3', 'emel', 'smc']

# ---------------------------------------------------------
# 1. MODEL COMBINATIONS ANALYSIS
# ---------------------------------------------------------
async def analyze_model_permutations(
    symbol: str, 
    direction: str = "BUY", 
    min_occurrences: int = 10,
    lookback_days: int = 30 # Deprecated as max limit, now starting point
) -> Dict[str, Any]:
    """
    Analyzes historical prediction_logs and groups them by concurrent triggers (±5 minutes).
    Generates all combinations of these concurrent models and calculates Win Rate.
    Dynamically extends lookback from 30 to 180 days if combinations have insufficient samples.
    """
    try:
        from database.supabase_client import get_supabase_client
        client = get_supabase_client()
        if not client:
            return {"error": "No database connection"}
        
        lookback_intervals = [30, 60, 90, 120, 180]
        logs = []
        last_cutoff = datetime.utcnow()
        current_days_used = 0
        
        async def fetch_logs_chunk(end_date_iso: str, start_date_iso: str):
            res = client.table("prediction_logs") \
                .select("id, created_at, model_type, ml_direction, outcome_results!inner(hit_target, hit_stop)") \
                .eq("symbol", symbol) \
                .eq("ml_direction", direction) \
                .gte("created_at", start_date_iso) \
                .lt("created_at", end_date_iso) \
                .execute()
            return res.get("data", []) if isinstance(res, dict) else getattr(res, "data", [])
        
        def compute_combos(current_logs):
            for log in current_logs:
                if "_ts" not in log:
                    if isinstance(log.get("created_at"), str):
                        try:
                            date_str = log["created_at"].replace("Z", "+00:00")
                            log["_ts"] = datetime.fromisoformat(date_str).timestamp()
                        except Exception:
                            log["_ts"] = 0
                    else:
                        log["_ts"] = 0
                        
            current_logs.sort(key=lambda x: x["_ts"])
            
            clusters = []
            current_cluster = []
            
            for log in current_logs:
                if not current_cluster:
                    current_cluster.append(log)
                else:
                    if log["_ts"] - current_cluster[0]["_ts"] <= 300:
                        current_cluster.append(log)
                    else:
                        clusters.append(current_cluster)
                        current_cluster = [log]
                        
            if current_cluster:
                clusters.append(current_cluster)
                
            combo_stats = defaultdict(lambda: {"wins": 0, "losses": 0, "profit": 0.0, "loss": 0.0, "total": 0})
            
            for cluster in clusters:
                models_in_cluster = list(set([str(log.get("model_type", "")).lower().strip() for log in cluster if log.get("model_type")]))
                if len(models_in_cluster) < 2:
                    continue
                    
                rep_log = cluster[0]
                outcomes = rep_log.get("outcome_results", [])
                
                is_win = False
                if outcomes and isinstance(outcomes, list) and len(outcomes) > 0:
                    is_win = outcomes[0].get("hit_target", False)
                    
                profit_value = 15.0 if is_win else 0.0
                loss_value = -15.0 if not is_win else 0.0
                
                for size in range(2, min(len(models_in_cluster) + 1, 7)):
                    for combo in combinations(sorted(models_in_cluster), size):
                        combo_key = "+".join(combo)
                        
                        combo_stats[combo_key]["total"] += 1
                        if is_win:
                            combo_stats[combo_key]["wins"] += 1
                            combo_stats[combo_key]["profit"] += profit_value
                        else:
                            combo_stats[combo_key]["losses"] += 1
                            combo_stats[combo_key]["loss"] += abs(loss_value)
                            
            return combo_stats, len(clusters)

        # Dynamic Fetch Loop
        combo_stats = {}
        total_clusters_analyzed = 0
        
        for idx, current_days in enumerate(lookback_intervals):
            current_days_used = current_days
            start_date = datetime.utcnow() - pd.Timedelta(days=current_days)
            
            # Fetch specifically the chunk missing (last_cutoff strictly backwards to start_date)
            new_logs = await asyncio.to_thread(fetch_logs_chunk, last_cutoff.isoformat(), start_date.isoformat())
            logs.extend(new_logs)
            last_cutoff = start_date
            
            # Recompute all combinations with the appended logs
            combo_stats, total_clusters_analyzed = compute_combos(logs)
            
            # Check if any generated combination has insufficient occurrences
            needs_more_data = False
            for stats in combo_stats.values():
                if stats["total"] < min_occurrences:
                    needs_more_data = True
                    break
                    
            if not needs_more_data:
                logger.info(f"[Permutations] Sufficient data reached at {current_days} days for {symbol} {direction}")
                break
            else:
                if idx < len(lookback_intervals) - 1:
                    logger.info(f"[Permutations] Extending lookback from {current_days} to {lookback_intervals[idx+1]} days for {symbol} {direction}")
        
        results = []
        for combo, stats in combo_stats.items():
            win_rate = stats["wins"] / max(stats["total"], 1)
            pf = stats["profit"] / (stats["loss"] if stats["loss"] > 0 else 1.0)
            exp = (win_rate * (stats["profit"] / max(1, stats["wins"]))) - ((1 - win_rate) * (stats["loss"] / max(1, stats["losses"])))
            
            results.append({
                "combination": combo,
                "symbol": symbol,
                "direction": direction,
                "total_signals": stats["total"],
                "wins": stats["wins"],
                "losses": stats["losses"],
                "win_rate": round(win_rate, 4),
                "profit_factor": round(pf, 2),
                "expectancy": round(exp, 2),
                "insufficient_data": stats["total"] < min_occurrences
            })
            
        results.sort(key=lambda x: x["win_rate"], reverse=True)
        
        return {
            "symbol": symbol,
            "direction": direction,
            "total_clusters_analyzed": total_clusters_analyzed,
            "lookback_days_used": current_days_used,
            "results": results
        }
    except Exception as e:
        logger.error(f"[Permutations] Model Error: {e}")
        return {"error": str(e)}

# ---------------------------------------------------------
# 2. TECHNICAL INDICATOR PERMUTATIONS ANALYSIS
# ---------------------------------------------------------
async def analyze_technical_permutations(
    symbol: str,
    direction: str = "BUY",
    min_occurrences: int = 15,
    lookforward_candles: int = 5,
    take_profit_pct: float = 0.3
) -> Dict[str, Any]:
    """
    Analyzes historical candlestick data, groups technical conditions into buckets,
    and calculates probability of a successful move strictly guarded by SL logic.
    """
    try:
        import ta
        from database.supabase_client import get_supabase_client
        client = get_supabase_client()
        if not client:
            return {"error": "No database connection"}
            
        def fetch_candles():
            return client.table("candle_cache") \
                .select("timestamp, open, high, low, close, volume") \
                .eq("symbol", symbol) \
                .eq("timeframe", "1h") \
                .order("timestamp", desc=True) \
                .limit(1500) \
                .execute()
                
        res = await asyncio.to_thread(fetch_candles)
            
        data = res.get("data", []) if isinstance(res, dict) else getattr(res, "data", [])
        if not data or len(data) < 50:
            return {"error": "Not enough candles in database"}
            
        # Supabase returns desc, we need asc for TA indicator history
        data.reverse()
        df = pd.DataFrame(data)
        if df.empty or "close" not in df.columns:
            return {"error": "Invalid dataframe structure"}
            
        closes = df["close"]
        highs = df["high"]
        lows = df["low"]
        volumes = df.get("volume", pd.Series([0]*len(df)))
        
        df["rsi_14"] = ta.momentum.RSIIndicator(closes, window=14).rsi()
        df["ema_20"] = ta.trend.ema_indicator(closes, window=20)
        df["ema_50"] = ta.trend.ema_indicator(closes, window=50)
        
        macd = ta.trend.MACD(closes)
        df["macd_hist"] = macd.macd_diff()
        
        df["adx"] = ta.trend.ADXIndicator(highs, lows, closes, window=14).adx()
        
        df["ema_20_dist"] = ((closes - df["ema_20"]) / df["ema_20"]) * 100
        df["ema_50_dist"] = ((closes - df["ema_50"]) / df["ema_50"]) * 100
        
        df["vol_sma"] = volumes.rolling(window=20).mean()
        df["volume_ratio"] = np.where(df["vol_sma"] > 0, volumes / df["vol_sma"], 1.0)
        
        def get_rsi_bucket(val):
            if pd.isna(val): return None
            if val > 70: return "RSI>70"
            if val > 50: return "RSI:50-70"
            if val > 30: return "RSI:30-50"
            return "RSI<30"
            
        def get_ema20_dist_bucket(val):
            if pd.isna(val): return None
            if val > 1.0: return "EMA20Dist>+1%"
            if val > 0: return "EMA20Dist:0_to_1%"
            if val > -1.0: return "EMA20Dist:-1_to_0%"
            return "EMA20Dist<-1%"
            
        def get_vol_bucket(val):
            if pd.isna(val): return None
            if val > 1.3: return "VolRatio>1.3"
            if val > 1.0: return "VolRatio:1.0-1.3"
            if val > 0.7: return "VolRatio:0.7-1.0"
            return "VolRatio<0.7"
            
        def get_adx_bucket(val):
            if pd.isna(val): return None
            if val > 30: return "ADX>30"
            if val > 20: return "ADX:20-30"
            return "ADX<20"
            
        def get_macd_bucket(val):
            if pd.isna(val): return None
            return "MACD>0" if val > 0 else "MACD<0"
            
        df["b_rsi"] = df["rsi_14"].apply(get_rsi_bucket)
        df["b_ema20"] = df["ema_20_dist"].apply(get_ema20_dist_bucket)
        df["b_vol"] = df["volume_ratio"].apply(get_vol_bucket)
        df["b_adx"] = df["adx"].apply(get_adx_bucket)
        df["b_macd"] = df["macd_hist"].apply(get_macd_bucket)
        
        win_flags = []
        for i in range(len(df)):
            if i + lookforward_candles >= len(df):
                win_flags.append(None)
                continue
                
            current_close = df.loc[i, "close"]
            is_win = False
            
            # Use fixed 0.3% Stop Loss barrier mapping 1:1 with TP 
            # to check if price hits SL BEFORE TP.
            stop_loss_pct = take_profit_pct
            
            for j in range(1, lookforward_candles + 1):
                future_idx = i + j
                if direction == "BUY":
                    target = current_close * (1 + (take_profit_pct / 100.0))
                    stop_level = current_close * (1 - (stop_loss_pct / 100.0))
                    
                    if df.loc[future_idx, "low"] <= stop_level:
                        # hit stop loss! failed.
                        is_win = False
                        break
                    if df.loc[future_idx, "high"] >= target:
                        # hit target before SL!
                        is_win = True
                        break
                        
                else: # SELL
                    target = current_close * (1 - (take_profit_pct / 100.0))
                    stop_level = current_close * (1 + (stop_loss_pct / 100.0))
                    
                    if df.loc[future_idx, "high"] >= stop_level:
                        # hit stop loss!
                        is_win = False
                        break
                    if df.loc[future_idx, "low"] <= target:
                        # hit target before SL!
                        is_win = True
                        break
                        
            win_flags.append(is_win)
            
        df["is_win"] = win_flags
        
        df_valid = df.dropna(subset=["b_rsi", "b_ema20", "b_vol", "b_adx", "b_macd", "is_win"])
        
        combo_stats = defaultdict(lambda: {"total": 0, "wins": 0})
        
        for idx, row in df_valid.iterrows():
            features = [
                row["b_rsi"],
                row["b_ema20"],
                row["b_vol"],
                row["b_adx"],
                row["b_macd"]
            ]
            
            for size in [2, 3]:
                for combo in combinations(features, size):
                    combo_key = " AND ".join(sorted(combo))
                    combo_stats[combo_key]["total"] += 1
                    if row["is_win"]:
                        combo_stats[combo_key]["wins"] += 1
                        
        results = []
        for combo, stats in combo_stats.items():
            if stats["total"] >= min_occurrences:
                win_rate = stats["wins"] / stats["total"]
                results.append({
                    "indicator_combo": combo,
                    "symbol": symbol,
                    "direction": direction,
                    "occurrences": stats["total"],
                    "wins": stats["wins"],
                    "win_rate": round(win_rate, 4)
                })
                
        results.sort(key=lambda x: (x["win_rate"], x["occurrences"]), reverse=True)
        
        return {
            "symbol": symbol,
            "direction": direction,
            "target_move_pct": take_profit_pct,
            "lookforward_candles": lookforward_candles,
            "results": results[:150]
        }
    except Exception as e:
         logger.error(f"[Permutations] Tech Indicator Error: {e}")
         return {"error": str(e)}
