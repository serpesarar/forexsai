"""
Permutation Analysis Service (Isolated Systems)
- Model Combinations Analysis
- Technical Indicators Permutations Analysis
"""
import asyncio
import logging
from typing import Dict, List, Any, Optional
from itertools import combinations
from collections import defaultdict
from datetime import datetime
import pandas as pd
import numpy as np

from services.candle_cache_store import load_candles
from services.signal_analytics import classify_signal, normalize_model_type, sort_models

logger = logging.getLogger(__name__)

SUPPORTED_SYMBOLS = ["NDX.INDX", "XAUUSD", "GDAXI.INDX", "USOIL.FOREX"]
SUPPORTED_MODELS = ["ml", "pulse1", "pulse2", "pulse3", "emel", "smc"]
SYMBOL_ALIASES = {
    "NASDAQ": "NDX.INDX",
    "NDX": "NDX.INDX",
    "NDX.INDX": "NDX.INDX",
    "DAX": "GDAXI.INDX",
    "GDAXI": "GDAXI.INDX",
    "GDAXI.INDX": "GDAXI.INDX",
    "XAU": "XAUUSD",
    "GOLD": "XAUUSD",
    "XAUUSD": "XAUUSD",
    "USOIL": "USOIL.FOREX",
    "WTI": "USOIL.FOREX",
    "CL.COMM": "USOIL.FOREX",
    "USOIL.FOREX": "USOIL.FOREX",
}
TECHNICAL_TIMEFRAME_FALLBACKS = ["1h", "30m", "15m", "5m"]
LOOKBACK_INTERVALS = [30, 60, 90, 120, 180]
TECHNICAL_COMBO_SIZES = (2, 3, 4)


def _normalize_symbol(symbol: str) -> str:
    raw = (symbol or "").upper().strip()
    return SYMBOL_ALIASES.get(raw, raw)


def _utc_iso(value: datetime) -> str:
    return value.replace(microsecond=0).isoformat() + "Z"


def _extract_rows(result: Any) -> List[Dict[str, Any]]:
    if isinstance(result, dict):
        data = result.get("data", [])
    else:
        data = getattr(result, "data", [])
    return data if isinstance(data, list) else []


def _parse_created_at(value: Any) -> float:
    if not isinstance(value, str) or not value:
        return 0.0
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except Exception:
        return 0.0


def _cluster_logs_by_time(logs: List[Dict[str, Any]], max_gap_seconds: int = 300) -> List[List[Dict[str, Any]]]:
    sorted_logs = sorted(logs, key=lambda item: item.get("_ts", 0.0))
    clusters: List[List[Dict[str, Any]]] = []
    current_cluster: List[Dict[str, Any]] = []

    for log in sorted_logs:
        if not current_cluster:
            current_cluster.append(log)
            continue

        cluster_start_ts = current_cluster[0].get("_ts", 0.0)
        current_ts = log.get("_ts", 0.0)
        if current_ts - cluster_start_ts <= max_gap_seconds:
            current_cluster.append(log)
        else:
            clusters.append(current_cluster)
            current_cluster = [log]

    if current_cluster:
        clusters.append(current_cluster)

    return clusters


def _select_better_entry(existing: Optional[Dict[str, Any]], candidate: Dict[str, Any]) -> Dict[str, Any]:
    if existing is None:
        return candidate

    existing_score = (
        1 if existing.get("is_win") else 0,
        abs(float(existing.get("pnl") or 0.0)),
        float(existing.get("_ts") or 0.0),
    )
    candidate_score = (
        1 if candidate.get("is_win") else 0,
        abs(float(candidate.get("pnl") or 0.0)),
        float(candidate.get("_ts") or 0.0),
    )
    return candidate if candidate_score > existing_score else existing


def _extract_cluster_model_entries(cluster: List[Dict[str, Any]], symbol: str) -> Dict[str, Dict[str, Any]]:
    per_model: Dict[str, Dict[str, Any]] = {}

    for log in cluster:
        normalized_model = normalize_model_type(log)
        if normalized_model not in SUPPORTED_MODELS:
            continue

        status, is_correct, pnl = classify_signal(log, default_symbol=symbol)
        if status not in {"completed", "stopped"} or is_correct is None or pnl is None:
            continue

        candidate = {
            "model_type": normalized_model,
            "is_win": bool(is_correct and pnl > 0),
            "pnl": float(pnl),
            "status": status,
            "_ts": float(log.get("_ts") or 0.0),
        }
        per_model[normalized_model] = _select_better_entry(per_model.get(normalized_model), candidate)

    return per_model


def _score_combo_members(combo_members: List[Dict[str, Any]]) -> Dict[str, Any]:
    pnl_values = [float(member.get("pnl") or 0.0) for member in combo_members]
    positive_count = sum(1 for pnl in pnl_values if pnl > 0)
    negative_count = sum(1 for pnl in pnl_values if pnl < 0)
    total_members = len(combo_members)
    avg_pnl = sum(pnl_values) / max(total_members, 1)
    median_pnl = float(np.median(pnl_values)) if pnl_values else 0.0
    alignment_ratio = positive_count / max(total_members, 1)

    is_win = positive_count > (total_members / 2)
    if not is_win and total_members > 0 and positive_count == negative_count and median_pnl > 0:
        is_win = True

    return {
        "is_win": is_win,
        "avg_pnl": avg_pnl,
        "median_pnl": median_pnl,
        "alignment_ratio": alignment_ratio,
        "positive_count": positive_count,
        "negative_count": negative_count,
        "unanimous": positive_count == total_members and total_members > 0,
    }


# ---------------------------------------------------------
# 1. MODEL COMBINATIONS ANALYSIS
# ---------------------------------------------------------
async def analyze_model_permutations(
    symbol: str,
    direction: str = "BUY",
    min_occurrences: int = 10,
    lookback_days: int = 30,
    cluster_window_minutes: int = 10,
) -> Dict[str, Any]:
    """
    Analyzes historical prediction_logs and groups them by concurrent triggers (±5 minutes).
    Generates all combinations of these concurrent models and calculates Win Rate.
    Dynamically extends lookback from 30 to 180 days if combinations have insufficient samples.
    """
    try:
        from database.supabase_client import get_supabase_client

        symbol = _normalize_symbol(symbol)
        direction = (direction or "BUY").upper().strip()
        if symbol not in SUPPORTED_SYMBOLS:
            return {"error": f"Unsupported symbol: {symbol}"}
        if direction not in {"BUY", "SELL"}:
            return {"error": f"Unsupported direction: {direction}"}

        client = get_supabase_client()
        if not client:
            return {"error": "No database connection"}

        minimum_start_days = max(30, int(lookback_days or 30))
        lookback_intervals = [days for days in LOOKBACK_INTERVALS if days >= minimum_start_days]
        if minimum_start_days not in lookback_intervals:
            lookback_intervals = [minimum_start_days, *lookback_intervals]
        logs: List[Dict[str, Any]] = []
        last_cutoff = datetime.utcnow()
        current_days_used = 0

        def fetch_logs_chunk(end_date_iso: str, start_date_iso: str) -> List[Dict[str, Any]]:
            result = client.table("prediction_logs") \
                .select("id, symbol, created_at, model_type, strategy, timeframe, ml_direction, status, resolution_reason, targets_hit, highest_profit_pips, lowest_drawdown_pips, ml_entry_price, exit_price") \
                .eq("symbol", symbol) \
                .eq("ml_direction", direction) \
                .gte("created_at", start_date_iso) \
                .lt("created_at", end_date_iso) \
                .neq("status", "active") \
                .limit(5000) \
                .execute()
            return _extract_rows(result)

        def compute_combos(current_logs: List[Dict[str, Any]]):
            for log in current_logs:
                if "_ts" not in log:
                    log["_ts"] = _parse_created_at(log.get("created_at"))

            clusters = _cluster_logs_by_time(current_logs, max_gap_seconds=max(60, int(cluster_window_minutes * 60)))
            combo_stats = defaultdict(lambda: {
                "wins": 0,
                "losses": 0,
                "profit": 0.0,
                "loss": 0.0,
                "total": 0,
                "alignment_sum": 0.0,
                "unanimous_wins": 0,
            })
            scored_clusters = 0

            for cluster in clusters:
                model_entries = _extract_cluster_model_entries(cluster, symbol)
                if len(model_entries) < 2:
                    continue

                scored_clusters += 1
                ordered_models = sort_models(model_entries.keys())
                max_combo_size = min(len(ordered_models), 6)

                for size in range(2, max_combo_size + 1):
                    for combo in combinations(ordered_models, size):
                        combo_key = "+".join(combo)
                        combo_members = [model_entries[model_name] for model_name in combo]
                        combo_score = _score_combo_members(combo_members)
                        combo_pnl = combo_score["avg_pnl"]

                        combo_stats[combo_key]["total"] += 1
                        combo_stats[combo_key]["alignment_sum"] += combo_score["alignment_ratio"]
                        if combo_score["unanimous"]:
                            combo_stats[combo_key]["unanimous_wins"] += 1
                        if combo_score["is_win"]:
                            combo_stats[combo_key]["wins"] += 1
                            combo_stats[combo_key]["profit"] += max(combo_pnl, 0.0)
                        else:
                            combo_stats[combo_key]["losses"] += 1
                            combo_stats[combo_key]["loss"] += abs(min(combo_pnl, 0.0))

            return combo_stats, len(clusters), scored_clusters

        combo_stats: Dict[str, Dict[str, Any]] = {}
        total_clusters_analyzed = 0
        scored_clusters = 0

        for idx, current_days in enumerate(lookback_intervals):
            current_days_used = current_days
            start_date = datetime.utcnow() - pd.Timedelta(days=current_days)

            new_logs = await asyncio.to_thread(fetch_logs_chunk, _utc_iso(last_cutoff), _utc_iso(start_date))
            logs.extend(new_logs)
            last_cutoff = start_date

            combo_stats, total_clusters_analyzed, scored_clusters = compute_combos(logs)
            needs_more_data = not any(stats["total"] >= min_occurrences for stats in combo_stats.values())

            if not needs_more_data:
                logger.info(f"[Permutations] Sufficient data reached at {current_days} days for {symbol} {direction}")
                break
            if idx < len(lookback_intervals) - 1:
                logger.info(f"[Permutations] Extending lookback from {current_days} to {lookback_intervals[idx + 1]} days for {symbol} {direction}")

        results = []
        for combo, stats in combo_stats.items():
            win_rate = stats["wins"] / max(stats["total"], 1)
            avg_win = stats["profit"] / max(1, stats["wins"])
            avg_loss = stats["loss"] / max(1, stats["losses"])
            pf = stats["profit"] / stats["loss"] if stats["loss"] > 0 else (999.0 if stats["wins"] > 0 else 0.0)
            exp = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)
            avg_member_alignment = stats["alignment_sum"] / max(stats["total"], 1)
            unanimous_win_rate = stats["unanimous_wins"] / max(stats["total"], 1)

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
                "avg_member_alignment": round(avg_member_alignment, 4),
                "unanimous_win_rate": round(unanimous_win_rate, 4),
                "insufficient_data": stats["total"] < min_occurrences,
            })

        results.sort(
            key=lambda x: (
                x["insufficient_data"],
                -x["win_rate"],
                -x["total_signals"],
                -x["profit_factor"],
            )
        )

        return {
            "symbol": symbol,
            "direction": direction,
            "total_clusters_analyzed": total_clusters_analyzed,
            "scored_clusters": scored_clusters,
            "lookback_days_used": current_days_used,
            "cluster_window_minutes": cluster_window_minutes,
            "results": results[:150],
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

        symbol = _normalize_symbol(symbol)
        direction = (direction or "BUY").upper().strip()
        if symbol not in SUPPORTED_SYMBOLS:
            return {"error": f"Unsupported symbol: {symbol}"}
        if direction not in {"BUY", "SELL"}:
            return {"error": f"Unsupported direction: {direction}"}

        data: List[Dict[str, Any]] = []
        timeframe_used = "1h"
        for timeframe in TECHNICAL_TIMEFRAME_FALLBACKS:
            candidate = await asyncio.to_thread(load_candles, symbol, timeframe, 1500)
            if len(candidate) > len(data):
                data = candidate
                timeframe_used = timeframe
            if len(candidate) >= 120:
                data = candidate
                timeframe_used = timeframe
                break

        if not data or len(data) < 60:
            return {"error": "Not enough candles in persistent cache"}

        df = pd.DataFrame(data)
        if df.empty or "close" not in df.columns:
            return {"error": "Invalid dataframe structure"}

        for col in ["open", "high", "low", "close", "volume"]:
            if col not in df.columns:
                df[col] = 0.0
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df = df.dropna(subset=["open", "high", "low", "close"]).reset_index(drop=True)
        if len(df) < 60:
            return {"error": "Not enough clean candles for technical analysis"}

        closes = df["close"]
        highs = df["high"]
        lows = df["low"]
        volumes = df.get("volume", pd.Series([0] * len(df))).fillna(0.0)

        df["rsi_14"] = ta.momentum.RSIIndicator(closes, window=14).rsi()
        df["ema_20"] = ta.trend.ema_indicator(closes, window=20)
        df["ema_50"] = ta.trend.ema_indicator(closes, window=50)
        df["ema_200"] = ta.trend.ema_indicator(closes, window=200)

        macd = ta.trend.MACD(closes)
        df["macd_hist"] = macd.macd_diff()

        df["adx"] = ta.trend.ADXIndicator(highs, lows, closes, window=14).adx()

        df["atr"] = ta.volatility.AverageTrueRange(highs, lows, closes, window=14).average_true_range()

        bb = ta.volatility.BollingerBands(closes, window=20, window_dev=2)
        df["bb_high"] = bb.bollinger_hband()
        df["bb_mid"] = bb.bollinger_mavg()
        df["bb_low"] = bb.bollinger_lband()

        df["ema_20_dist"] = ((closes - df["ema_20"]) / df["ema_20"]) * 100
        df["ema_50_dist"] = ((closes - df["ema_50"]) / df["ema_50"]) * 100
        df["atr_ratio"] = np.where(df["atr"].rolling(window=20).median() > 0, df["atr"] / df["atr"].rolling(window=20).median(), 1.0)

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

        def get_ema_stack_bucket(ema20, ema50, ema200):
            if pd.isna(ema20) or pd.isna(ema50) or pd.isna(ema200): return None
            if ema20 > ema50 > ema200: return "EMAStack:BULL"
            if ema20 < ema50 < ema200: return "EMAStack:BEAR"
            return "EMAStack:MIXED"

        def get_price_ema200_bucket(price, ema200):
            if pd.isna(price) or pd.isna(ema200): return None
            return "Close>EMA200" if price >= ema200 else "Close<EMA200"

        def get_bb_bucket(price, bb_high, bb_mid, bb_low):
            if pd.isna(price) or pd.isna(bb_high) or pd.isna(bb_mid) or pd.isna(bb_low): return None
            if price >= bb_high: return "BB:AboveUpper"
            if price >= bb_mid: return "BB:UpperHalf"
            if price >= bb_low: return "BB:LowerHalf"
            return "BB:BelowLower"

        def get_atr_bucket(val):
            if pd.isna(val): return None
            if val > 1.25: return "ATR:High"
            if val > 0.85: return "ATR:Normal"
            return "ATR:Low"

        df["b_rsi"] = df["rsi_14"].apply(get_rsi_bucket)
        df["b_ema20"] = df["ema_20_dist"].apply(get_ema20_dist_bucket)
        df["b_vol"] = df["volume_ratio"].apply(get_vol_bucket)
        df["b_adx"] = df["adx"].apply(get_adx_bucket)
        df["b_macd"] = df["macd_hist"].apply(get_macd_bucket)
        df["b_ema_stack"] = df.apply(lambda row: get_ema_stack_bucket(row["ema_20"], row["ema_50"], row["ema_200"]), axis=1)
        df["b_price_ema200"] = df.apply(lambda row: get_price_ema200_bucket(row["close"], row["ema_200"]), axis=1)
        df["b_bb"] = df.apply(lambda row: get_bb_bucket(row["close"], row["bb_high"], row["bb_mid"], row["bb_low"]), axis=1)
        df["b_atr"] = df["atr_ratio"].apply(get_atr_bucket)

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

                else:  # SELL
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

        df_valid = df.dropna(subset=["b_rsi", "b_ema20", "b_vol", "b_adx", "b_macd", "b_ema_stack", "b_price_ema200", "b_bb", "b_atr", "is_win"])

        combo_stats = defaultdict(lambda: {"total": 0, "wins": 0})

        for idx, row in df_valid.iterrows():
            features = [
                row["b_rsi"],
                row["b_ema_stack"],
                row["b_price_ema200"],
                row["b_ema20"],
                row["b_vol"],
                row["b_adx"],
                row["b_macd"],
                row["b_bb"],
                row["b_atr"],
            ]

            for size in TECHNICAL_COMBO_SIZES:
                for combo in combinations(features, size):
                    combo_key = " AND ".join(sorted(combo))
                    combo_stats[combo_key]["total"] += 1
                    if row["is_win"]:
                        combo_stats[combo_key]["wins"] += 1

        results = []
        for combo, stats in combo_stats.items():
            win_rate = stats["wins"] / max(stats["total"], 1)
            results.append({
                "indicator_combo": combo,
                "symbol": symbol,
                "direction": direction,
                "occurrences": stats["total"],
                "wins": stats["wins"],
                "win_rate": round(win_rate, 4),
                "combination_size": combo.count(" AND ") + 1,
                "insufficient_data": stats["total"] < min_occurrences,
            })

        results.sort(
            key=lambda x: (
                x["insufficient_data"],
                -x["win_rate"],
                -x["occurrences"],
            )
        )

        return {
            "symbol": symbol,
            "direction": direction,
            "timeframe_used": timeframe_used,
            "candles_analyzed": len(df),
            "target_move_pct": take_profit_pct,
            "lookforward_candles": lookforward_candles,
            "results": results[:150]
        }
    except Exception as e:
        logger.error(f"[Permutations] Tech Indicator Error: {e}")
        return {"error": str(e)}
