from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from bisect import bisect_right
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from itertools import combinations
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from dotenv import load_dotenv

load_dotenv(BACKEND / ".env")

from database.supabase_client import get_supabase_client
from services.signal_analytics import filter_market_closed_invalid_signals, normalize_model_type, normalize_timeframe, sort_models
from services.target_config import calculate_stoploss_price, calculate_target_prices, pips_from_price_change

SUPPORTED_SYMBOLS = ["NDX.INDX", "XAUUSD", "GDAXI.INDX", "USOIL.FOREX"]
SUPPORTED_MODELS = ["ml", "pulse1", "pulse2", "pulse3", "emel", "smc"]
KNOWN_PRICE_TIMEFRAMES = {"1m", "5m", "15m", "30m", "1h", "4h", "1d"}
TIMEFRAME_EVALUATION_WINDOWS = {
    "1m": 2,
    "5m": 10,
    "15m": 15,
    "30m": 60,
    "1h": 120,
    "4h": 480,
    "1d": 2880,
}
DEFAULT_EVALUATION_WINDOW_MINUTES = 15
DEFAULT_SELECT_COLUMNS = (
    "id,symbol,created_at,model_type,strategy,timeframe,ml_direction,status,resolution_reason,"
    "ml_entry_price,exit_price,targets_hit,highest_profit_pips,lowest_drawdown_pips"
)
CANDLE_SELECT_COLUMNS = "candle_time,open,high,low,close,volume"
SUPABASE_ROW_CAP = 1000

def parse_datetime(value: Any) -> Optional[datetime]:
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc) if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None
    return parsed.astimezone(timezone.utc) if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def utc_iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def coerce_float(value: Any) -> Optional[float]:
    if value in (None, ""):
        return None
    try:
        parsed = float(value)
    except Exception:
        return None
    if math.isnan(parsed):
        return None
    return parsed


def extract_rows(result: Dict[str, Any]) -> List[Dict[str, Any]]:
    data = result.get("data") or []
    return data if isinstance(data, list) else []


def format_pct(value: Any) -> str:
    try:
        return f"{float(value) * 100:.2f}%"
    except Exception:
        return "0.00%"


def format_num(value: Any, digits: int = 2) -> str:
    try:
        return f"{float(value):.{digits}f}"
    except Exception:
        return f"{0:.{digits}f}"


def evaluation_window_minutes(timeframe: Optional[str]) -> int:
    normalized = normalize_timeframe(timeframe) or "15m"
    return TIMEFRAME_EVALUATION_WINDOWS.get(normalized, DEFAULT_EVALUATION_WINDOW_MINUTES)


def resolve_price_timeframe(selected_timeframe: Optional[str], event_timeframe: Optional[str]) -> str:
    normalized_selected = str(selected_timeframe or "signal").lower().strip()
    if normalized_selected in {"signal", "event", "auto", "all"}:
        return normalize_timeframe(event_timeframe) or "15m"
    normalized_fixed = normalize_timeframe(normalized_selected)
    if normalized_fixed in KNOWN_PRICE_TIMEFRAMES:
        return normalized_fixed
    return normalize_timeframe(event_timeframe) or "15m"


def query_row_threshold(limit: int) -> int:
    requested_limit = max(int(limit or 0), 1)
    return min(requested_limit, SUPABASE_ROW_CAP)


def choose_available_price_timeframe(
    preferred_timeframe: str,
    candles_by_timeframe: Dict[str, Sequence[Dict[str, Any]]],
) -> str:
    if candles_by_timeframe.get(preferred_timeframe):
        return preferred_timeframe
    if preferred_timeframe != "5m" and candles_by_timeframe.get("5m"):
        return "5m"
    return preferred_timeframe


def recursive_prediction_log_fetch(
    client,
    *,
    symbol: str,
    direction: str,
    start_dt: datetime,
    end_dt: datetime,
    limit: int,
    min_split_minutes: int,
) -> List[Dict[str, Any]]:
    result = (
        client.table("prediction_logs")
        .select(DEFAULT_SELECT_COLUMNS)
        .eq("symbol", symbol)
        .eq("ml_direction", direction)
        .gte("created_at", utc_iso(start_dt))
        .lt("created_at", utc_iso(end_dt))
        .neq("status", "active")
        .order("created_at")
        .limit(limit)
        .execute()
    )
    rows = extract_rows(result)
    if result.get("error"):
        raise RuntimeError(f"prediction_logs query failed for {symbol} {direction}: {result['error']}")
    window_minutes = max((end_dt - start_dt).total_seconds() / 60.0, 0.0)
    threshold = query_row_threshold(limit)
    if len(rows) < threshold or window_minutes <= min_split_minutes:
        return rows
    midpoint = start_dt + (end_dt - start_dt) / 2
    if midpoint <= start_dt or midpoint >= end_dt:
        return rows
    left_rows = recursive_prediction_log_fetch(
        client,
        symbol=symbol,
        direction=direction,
        start_dt=start_dt,
        end_dt=midpoint,
        limit=limit,
        min_split_minutes=min_split_minutes,
    )
    right_rows = recursive_prediction_log_fetch(
        client,
        symbol=symbol,
        direction=direction,
        start_dt=midpoint,
        end_dt=end_dt,
        limit=limit,
        min_split_minutes=min_split_minutes,
    )
    return left_rows + right_rows


def recursive_candle_fetch(
    client,
    *,
    symbol: str,
    timeframe: str,
    start_dt: datetime,
    end_dt: datetime,
    limit: int,
    min_split_minutes: int,
) -> List[Dict[str, Any]]:
    result = (
        client.table("candle_cache")
        .select(CANDLE_SELECT_COLUMNS)
        .eq("symbol", symbol)
        .eq("timeframe", timeframe)
        .gte("candle_time", utc_iso(start_dt))
        .lt("candle_time", utc_iso(end_dt))
        .order("candle_time")
        .limit(limit)
        .execute()
    )
    rows = extract_rows(result)
    if result.get("error"):
        raise RuntimeError(f"candle_cache query failed for {symbol} {timeframe}: {result['error']}")
    window_minutes = max((end_dt - start_dt).total_seconds() / 60.0, 0.0)
    threshold = query_row_threshold(limit)
    if len(rows) < threshold or window_minutes <= min_split_minutes:
        return rows
    midpoint = start_dt + (end_dt - start_dt) / 2
    if midpoint <= start_dt or midpoint >= end_dt:
        return rows
    left_rows = recursive_candle_fetch(
        client,
        symbol=symbol,
        timeframe=timeframe,
        start_dt=start_dt,
        end_dt=midpoint,
        limit=limit,
        min_split_minutes=min_split_minutes,
    )
    right_rows = recursive_candle_fetch(
        client,
        symbol=symbol,
        timeframe=timeframe,
        start_dt=midpoint,
        end_dt=end_dt,
        limit=limit,
        min_split_minutes=min_split_minutes,
    )
    return left_rows + right_rows


def dedupe_rows(rows: Iterable[Dict[str, Any]], key_name: str) -> List[Dict[str, Any]]:
    seen = set()
    output = []
    for row in rows:
        key = row.get(key_name)
        if key in seen:
            continue
        seen.add(key)
        output.append(row)
    return output


def build_bucket_start(dt: datetime, bucket_minutes: int) -> datetime:
    epoch_seconds = int(dt.timestamp())
    bucket_seconds = max(bucket_minutes, 1) * 60
    bucket_epoch = (epoch_seconds // bucket_seconds) * bucket_seconds
    return datetime.fromtimestamp(bucket_epoch, tz=timezone.utc)


def prepare_logs(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    filtered = filter_market_closed_invalid_signals(rows)
    prepared: List[Dict[str, Any]] = []
    for row in filtered:
        parsed_dt = parse_datetime(row.get("created_at"))
        if parsed_dt is None:
            continue
        model = normalize_model_type(row)
        if model not in SUPPORTED_MODELS:
            continue
        direction = str(row.get("ml_direction") or "").upper().strip()
        if direction not in {"BUY", "SELL"}:
            continue
        prepared.append({
            **row,
            "_created_dt": parsed_dt,
            "_model": model,
            "_timeframe": normalize_timeframe(row.get("timeframe")) or "15m",
            "_entry_price": coerce_float(row.get("ml_entry_price")),
        })
    prepared.sort(key=lambda item: item["_created_dt"])
    return dedupe_rows(prepared, "id")


def build_events(
    logs: Sequence[Dict[str, Any]],
    *,
    symbol: str,
    direction: str,
    bucket_minutes: int,
    min_models_per_event: int,
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    grouped: Dict[Tuple[str, str, str], List[Dict[str, Any]]] = defaultdict(list)
    for row in logs:
        bucket_start = build_bucket_start(row["_created_dt"], bucket_minutes)
        bucket_key = (symbol, direction, utc_iso(bucket_start))
        grouped[bucket_key].append(row)
    events: List[Dict[str, Any]] = []
    stats = {
        "raw_rows": len(logs),
        "bucket_count": len(grouped),
        "discarded_low_model_count": 0,
        "discarded_missing_entry": 0,
    }
    for (_, _, bucket_iso), bucket_rows in sorted(grouped.items(), key=lambda item: item[0][2]):
        sorted_rows = sorted(bucket_rows, key=lambda item: item["_created_dt"])
        per_model: Dict[str, Dict[str, Any]] = {}
        for row in sorted_rows:
            model = row["_model"]
            if model not in per_model:
                per_model[model] = row
        if len(per_model) < min_models_per_event:
            stats["discarded_low_model_count"] += 1
            continue
        representative_rows = sorted(per_model.values(), key=lambda item: item["_created_dt"])
        entry_source = next((row for row in representative_rows if row.get("_entry_price") is not None), None)
        if entry_source is None:
            stats["discarded_missing_entry"] += 1
            continue
        models = sort_models(per_model.keys())
        bucket_start_dt = parse_datetime(bucket_iso)
        if bucket_start_dt is None:
            bucket_start_dt = representative_rows[0]["_created_dt"]
        events.append({
            "event_id": f"{symbol}|{direction}|{bucket_iso}",
            "symbol": symbol,
            "direction": direction,
            "bucket_start": bucket_iso,
            "event_time": utc_iso(entry_source["_created_dt"]),
            "event_timeframe": entry_source["_timeframe"],
            "entry_price": float(entry_source["_entry_price"]),
            "models": models,
            "model_rows": [
                {
                    "id": row.get("id"),
                    "model": row["_model"],
                    "created_at": utc_iso(row["_created_dt"]),
                    "timeframe": row["_timeframe"],
                    "entry_price": row.get("_entry_price"),
                    "status": row.get("status"),
                }
                for row in representative_rows
            ],
            "bucket_size": len(sorted_rows),
            "distinct_models": len(models),
            "bucket_start_dt": bucket_start_dt,
            "event_dt": entry_source["_created_dt"],
        })
    return events, stats


def prepare_candles(rows: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    prepared = []
    for row in rows:
        candle_dt = parse_datetime(row.get("candle_time"))
        if candle_dt is None:
            continue
        open_price = coerce_float(row.get("open"))
        high_price = coerce_float(row.get("high"))
        low_price = coerce_float(row.get("low"))
        close_price = coerce_float(row.get("close"))
        if None in {open_price, high_price, low_price, close_price}:
            continue
        prepared.append({
            "candle_time": utc_iso(candle_dt),
            "_dt": candle_dt,
            "_ts_ms": candle_dt.timestamp() * 1000.0,
            "open": float(open_price),
            "high": float(high_price),
            "low": float(low_price),
            "close": float(close_price),
            "volume": coerce_float(row.get("volume")) or 0.0,
        })
    prepared.sort(key=lambda item: item["_ts_ms"])
    return dedupe_rows(prepared, "candle_time")


def resolve_hit_sequence(direction: str, hit_target: bool, hit_stop: bool, tie_policy: str) -> Optional[str]:
    if hit_target and hit_stop:
        return "loss" if tie_policy == "stop_first" else "win"
    if hit_target:
        return "win"
    if hit_stop:
        return "loss"
    return None


def simulate_event_outcome(
    event: Dict[str, Any],
    candles: Sequence[Dict[str, Any]],
    candle_timestamps_ms: Sequence[float],
    *,
    target_level: str,
    price_timeframe: str,
    tie_policy: str,
) -> Dict[str, Any]:
    entry_price = float(event["entry_price"])
    direction = event["direction"]
    symbol = event["symbol"]
    event_timeframe = event["event_timeframe"]
    event_dt: datetime = event["event_dt"]
    window_minutes = evaluation_window_minutes(event_timeframe)
    target_prices = calculate_target_prices(entry_price, direction, symbol, event_timeframe)
    target_price = target_prices.get(target_level)
    if target_price is None:
        ordered_targets = sorted(target_prices.items(), key=lambda item: item[0])
        if not ordered_targets:
            return {
                "outcome": "no_market_data",
                "resolved": False,
                "reason": "no_target_config",
                "target_level": target_level,
                "target_price": None,
                "stop_price": None,
                "evaluation_window_minutes": window_minutes,
                "price_timeframe": price_timeframe,
            }
        target_level, target_price = ordered_targets[0]
    stop_price = calculate_stoploss_price(entry_price, direction, symbol, event_timeframe)
    start_ms = event_dt.timestamp() * 1000.0
    end_ms = (event_dt + timedelta(minutes=window_minutes)).timestamp() * 1000.0
    start_index = bisect_right(candle_timestamps_ms, start_ms)
    if start_index >= len(candles):
        return {
            "outcome": "no_market_data",
            "resolved": False,
            "reason": "no_post_event_candles",
            "target_level": target_level,
            "target_price": round(float(target_price), 4),
            "stop_price": round(float(stop_price), 4),
            "evaluation_window_minutes": window_minutes,
            "price_timeframe": price_timeframe,
        }
    resolution = None
    resolved_candle = None
    for candle in candles[start_index:]:
        candle_ts = float(candle["_ts_ms"])
        if candle_ts > end_ms:
            break
        high_price = float(candle["high"])
        low_price = float(candle["low"])
        if direction == "BUY":
            resolution = resolve_hit_sequence(direction, high_price >= target_price, low_price <= stop_price, tie_policy)
        else:
            resolution = resolve_hit_sequence(direction, low_price <= target_price, high_price >= stop_price, tie_policy)
        if resolution:
            resolved_candle = candle
            break
    last_index = bisect_right(candle_timestamps_ms, end_ms) - 1
    last_close = None
    if 0 <= last_index < len(candles):
        last_close = float(candles[last_index]["close"])
    if resolution == "win":
        realized_return = pips_from_price_change(abs(float(target_price) - entry_price), symbol)
        resolution_minutes = max((parse_datetime(resolved_candle["candle_time"]) - event_dt).total_seconds() / 60.0, 0.0) if resolved_candle else None
        return {
            "outcome": "win",
            "resolved": True,
            "reason": "target_hit",
            "target_level": target_level,
            "target_price": round(float(target_price), 4),
            "stop_price": round(float(stop_price), 4),
            "exit_price": round(float(target_price), 4),
            "realized_return": round(float(realized_return), 4),
            "evaluation_window_minutes": window_minutes,
            "price_timeframe": price_timeframe,
            "resolved_at": resolved_candle["candle_time"] if resolved_candle else None,
            "resolution_minutes": round(float(resolution_minutes), 2) if resolution_minutes is not None else None,
            "terminal_close": round(float(last_close), 4) if last_close is not None else None,
        }
    if resolution == "loss":
        realized_return = -pips_from_price_change(abs(float(stop_price) - entry_price), symbol)
        resolution_minutes = max((parse_datetime(resolved_candle["candle_time"]) - event_dt).total_seconds() / 60.0, 0.0) if resolved_candle else None
        return {
            "outcome": "loss",
            "resolved": True,
            "reason": "stop_hit",
            "target_level": target_level,
            "target_price": round(float(target_price), 4),
            "stop_price": round(float(stop_price), 4),
            "exit_price": round(float(stop_price), 4),
            "realized_return": round(float(realized_return), 4),
            "evaluation_window_minutes": window_minutes,
            "price_timeframe": price_timeframe,
            "resolved_at": resolved_candle["candle_time"] if resolved_candle else None,
            "resolution_minutes": round(float(resolution_minutes), 2) if resolution_minutes is not None else None,
            "terminal_close": round(float(last_close), 4) if last_close is not None else None,
        }
    terminal_return = None
    if last_close is not None:
        raw_change = last_close - entry_price
        directional_change = raw_change if direction == "BUY" else -raw_change
        terminal_return = pips_from_price_change(abs(directional_change), symbol)
        if directional_change < 0:
            terminal_return = -terminal_return
    return {
        "outcome": "expired",
        "resolved": False,
        "reason": "window_expired",
        "target_level": target_level,
        "target_price": round(float(target_price), 4),
        "stop_price": round(float(stop_price), 4),
        "exit_price": round(float(last_close), 4) if last_close is not None else None,
        "realized_return": 0.0,
        "terminal_return": round(float(terminal_return), 4) if terminal_return is not None else None,
        "evaluation_window_minutes": window_minutes,
        "price_timeframe": price_timeframe,
        "resolved_at": None,
        "resolution_minutes": None,
        "terminal_close": round(float(last_close), 4) if last_close is not None else None,
    }


def classify_combo(row: Dict[str, Any], min_occurrences: int) -> str:
    occurrences = int(row.get("occurrences") or 0)
    win_rate = float(row.get("win_rate") or 0.0)
    profit_factor = float(row.get("profit_factor") or 0.0)
    expectancy = float(row.get("expectancy") or 0.0)
    completion_rate = float(row.get("completion_rate") or 0.0)
    if occurrences < min_occurrences:
        return "weak_sample"
    if win_rate >= 0.70 and profit_factor >= 1.5 and expectancy > 0 and completion_rate >= 0.60:
        return "strong"
    if win_rate >= 0.55 and profit_factor >= 1.0 and expectancy >= 0:
        return "usable"
    return "weak"


def stability_score(occurrences: int, win_rate: float, completion_rate: float) -> float:
    return round(win_rate * math.log(max(occurrences, 0) + 1.0) * completion_rate, 4)


def aggregate_combos(
    events: Sequence[Dict[str, Any]],
    *,
    max_combo_size: int,
    min_occurrences: int,
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    aggregate_map: Dict[Tuple[str, str, str], Dict[str, Any]] = {}
    skipped_no_market_data = 0
    for event in events:
        outcome = event.get("outcome")
        if outcome == "no_market_data":
            skipped_no_market_data += 1
            continue
        models = list(event.get("models") or [])
        if len(models) < 2:
            continue
        event_day = str(event.get("bucket_start") or "")[:10]
        combo_size_limit = min(max_combo_size, len(models))
        for size in range(2, combo_size_limit + 1):
            for combo_tuple in combinations(models, size):
                combo = "+".join(combo_tuple)
                key = (event["symbol"], event["direction"], combo)
                if key not in aggregate_map:
                    aggregate_map[key] = {
                        "symbol": event["symbol"],
                        "direction": event["direction"],
                        "combination": combo,
                        "model_count": size,
                        "occurrences": 0,
                        "wins": 0,
                        "losses": 0,
                        "expired": 0,
                        "resolved_count": 0,
                        "profit_sum": 0.0,
                        "loss_sum": 0.0,
                        "return_sum": 0.0,
                        "resolved_return_sum": 0.0,
                        "resolution_minutes_sum": 0.0,
                        "resolution_minutes_count": 0,
                        "first_seen_at": event["event_time"],
                        "last_seen_at": event["event_time"],
                        "unique_bucket_days": set(),
                    }
                row = aggregate_map[key]
                row["occurrences"] += 1
                row["first_seen_at"] = min(str(row["first_seen_at"]), str(event["event_time"]))
                row["last_seen_at"] = max(str(row["last_seen_at"]), str(event["event_time"]))
                row["unique_bucket_days"].add(event_day)
                realized_return = float(event.get("realized_return") or 0.0)
                row["return_sum"] += realized_return
                if outcome == "win":
                    row["wins"] += 1
                    row["resolved_count"] += 1
                    row["profit_sum"] += max(realized_return, 0.0)
                    row["resolved_return_sum"] += realized_return
                elif outcome == "loss":
                    row["losses"] += 1
                    row["resolved_count"] += 1
                    row["loss_sum"] += abs(min(realized_return, 0.0))
                    row["resolved_return_sum"] += realized_return
                elif outcome == "expired":
                    row["expired"] += 1
                resolution_minutes = event.get("resolution_minutes")
                if resolution_minutes is not None:
                    row["resolution_minutes_sum"] += float(resolution_minutes)
                    row["resolution_minutes_count"] += 1
    rows: List[Dict[str, Any]] = []
    for aggregate in aggregate_map.values():
        occurrences = int(aggregate["occurrences"])
        resolved_count = int(aggregate["resolved_count"])
        wins = int(aggregate["wins"])
        win_rate = wins / max(resolved_count, 1)
        completion_rate = resolved_count / max(occurrences, 1)
        profit_factor = aggregate["profit_sum"] / aggregate["loss_sum"] if aggregate["loss_sum"] > 0 else (999.0 if aggregate["profit_sum"] > 0 else 0.0)
        expectancy = aggregate["return_sum"] / max(occurrences, 1)
        resolved_expectancy = aggregate["resolved_return_sum"] / max(resolved_count, 1) if resolved_count else 0.0
        avg_resolution_minutes = aggregate["resolution_minutes_sum"] / max(aggregate["resolution_minutes_count"], 1) if aggregate["resolution_minutes_count"] else None
        row = {
            "symbol": aggregate["symbol"],
            "direction": aggregate["direction"],
            "combination": aggregate["combination"],
            "model_count": aggregate["model_count"],
            "occurrences": occurrences,
            "wins": wins,
            "losses": int(aggregate["losses"]),
            "expired": int(aggregate["expired"]),
            "resolved_count": resolved_count,
            "win_rate": round(win_rate, 4),
            "completion_rate": round(completion_rate, 4),
            "profit_factor": round(profit_factor, 2),
            "expectancy": round(expectancy, 4),
            "resolved_expectancy": round(resolved_expectancy, 4),
            "avg_resolution_minutes": round(avg_resolution_minutes, 2) if avg_resolution_minutes is not None else None,
            "first_seen_at": aggregate["first_seen_at"],
            "last_seen_at": aggregate["last_seen_at"],
            "unique_bucket_days": len(aggregate["unique_bucket_days"]),
            "stability_score": stability_score(occurrences, win_rate, completion_rate),
        }
        row["quality"] = classify_combo(row, min_occurrences)
        rows.append(row)
    rows.sort(
        key=lambda item: (
            item["quality"] == "weak_sample",
            -(float(item.get("win_rate") or 0.0)),
            -(int(item.get("occurrences") or 0)),
            -(float(item.get("profit_factor") or 0.0)),
            -(float(item.get("stability_score") or 0.0)),
            item.get("combination") or "",
        )
    )
    return rows, {"skipped_no_market_data_events": skipped_no_market_data}


def build_context_groups(rows: Sequence[Dict[str, Any]], top_n: int) -> List[Dict[str, Any]]:
    grouped: Dict[Tuple[str, str], List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(row["symbol"], row["direction"])].append(row)
    contexts = []
    for (symbol, direction), group_rows in sorted(grouped.items()):
        contexts.append({
            "symbol": symbol,
            "direction": direction,
            "row_count": len(group_rows),
            "strong_count": sum(1 for row in group_rows if row.get("quality") == "strong"),
            "usable_count": sum(1 for row in group_rows if row.get("quality") == "usable"),
            "weak_count": sum(1 for row in group_rows if row.get("quality") == "weak"),
            "weak_sample_count": sum(1 for row in group_rows if row.get("quality") == "weak_sample"),
            "top_rows": list(group_rows[:top_n]),
        })
    return contexts


def build_overview(events: Sequence[Dict[str, Any]], rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    quality_counts = defaultdict(int)
    for row in rows:
        quality_counts[row.get("quality") or "weak"] += 1
    resolved_events = [event for event in events if event.get("outcome") in {"win", "loss"}]
    wins = sum(1 for event in resolved_events if event.get("outcome") == "win")
    return {
        "total_events": len(events),
        "resolved_events": len(resolved_events),
        "expired_events": sum(1 for event in events if event.get("outcome") == "expired"),
        "no_market_data_events": sum(1 for event in events if event.get("outcome") == "no_market_data"),
        "overall_event_win_rate": round(wins / max(len(resolved_events), 1), 4),
        "total_combos": len(rows),
        "strong_rows": quality_counts["strong"],
        "usable_rows": quality_counts["usable"],
        "weak_rows": quality_counts["weak"],
        "weak_sample_rows": quality_counts["weak_sample"],
    }


def quality_rank(quality: Optional[str]) -> int:
    return {
        "strong": 4,
        "usable": 3,
        "weak": 2,
        "weak_sample": 1,
    }.get(str(quality or "weak_sample"), 0)


def build_most_frequent_rows(rows: Sequence[Dict[str, Any]], top_n: int) -> List[Dict[str, Any]]:
    ranked_rows = sorted(
        rows,
        key=lambda row: (
            int(row.get("occurrences") or 0),
            int(row.get("resolved_count") or 0),
            float(row.get("completion_rate") or 0.0),
            float(row.get("win_rate") or 0.0),
            quality_rank(row.get("quality")),
        ),
        reverse=True,
    )
    return list(ranked_rows[:top_n])


def build_best_stable_rows(
    rows: Sequence[Dict[str, Any]],
    *,
    top_n: int,
    min_occurrences: int,
) -> List[Dict[str, Any]]:
    eligible_rows = [
        row
        for row in rows
        if int(row.get("occurrences") or 0) >= max(int(min_occurrences or 0), 1)
        and int(row.get("resolved_count") or 0) >= 3
    ]
    ranked_rows = sorted(
        eligible_rows,
        key=lambda row: (
            quality_rank(row.get("quality")),
            float(row.get("stability_score") or 0.0),
            float(row.get("win_rate") or 0.0),
            float(row.get("completion_rate") or 0.0),
            int(row.get("occurrences") or 0),
            float(row.get("profit_factor") or 0.0),
            float(row.get("expectancy") or 0.0),
        ),
        reverse=True,
    )
    return list(ranked_rows[:top_n])


def build_payload(
    *,
    events: Sequence[Dict[str, Any]],
    combo_rows: Sequence[Dict[str, Any]],
    args: argparse.Namespace,
    fetch_stats: Dict[str, Any],
) -> Dict[str, Any]:
    serializable_events = []
    for event in events:
        serializable_events.append({
            key: value
            for key, value in event.items()
            if key not in {"bucket_start_dt", "event_dt"}
        })
    most_frequent_rows = build_most_frequent_rows(combo_rows, args.top)
    best_stable_rows = build_best_stable_rows(
        combo_rows,
        top_n=args.top,
        min_occurrences=args.min_occurrences,
    )
    return {
        "generated_at": utc_iso(datetime.now(timezone.utc)),
        "parameters": {
            "symbols": list(args.symbol),
            "directions": list(args.direction),
            "lookback_days": args.lookback_days,
            "bucket_minutes": args.bucket_minutes,
            "min_models_per_event": args.min_models_per_event,
            "min_occurrences": args.min_occurrences,
            "max_combo_size": args.max_combo_size,
            "target_level": args.target_level,
            "price_timeframe": args.price_timeframe,
            "tie_policy": args.tie_policy,
            "query_limit": args.query_limit,
        },
        "fetch_stats": fetch_stats,
        "overview": build_overview(events, combo_rows),
        "overall_top": list(combo_rows[: args.top]),
        "overall_bottom": list(reversed(combo_rows[-args.top :])),
        "most_frequent_common": most_frequent_rows,
        "best_stable": best_stable_rows,
        "contexts": build_context_groups(combo_rows, args.top),
        "events": serializable_events,
        "aggregates": list(combo_rows),
    }


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))


def write_csv(path: Path, rows: Sequence[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "symbol",
        "direction",
        "combination",
        "model_count",
        "occurrences",
        "wins",
        "losses",
        "expired",
        "resolved_count",
        "win_rate",
        "completion_rate",
        "profit_factor",
        "expectancy",
        "resolved_expectancy",
        "avg_resolution_minutes",
        "unique_bucket_days",
        "stability_score",
        "quality",
        "first_seen_at",
        "last_seen_at",
    ]
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name) for name in fieldnames})


def build_txt(payload: Dict[str, Any], top_n: int) -> str:
    overview = payload.get("overview") or {}
    params = payload.get("parameters") or {}
    fetch_stats = payload.get("fetch_stats") or {}
    lines = []
    lines.append(f"Generated: {payload.get('generated_at')}")
    lines.append(f"Lookback days: {params.get('lookback_days')}")
    lines.append(f"Bucket minutes: {params.get('bucket_minutes')}")
    lines.append(f"Min models/event: {params.get('min_models_per_event')}")
    lines.append(f"Min occurrences: {params.get('min_occurrences')}")
    lines.append(f"Max combo size: {params.get('max_combo_size')}")
    lines.append(f"Target level: {params.get('target_level')}")
    lines.append(f"Price timeframe: {params.get('price_timeframe')}")
    lines.append(f"Tie policy: {params.get('tie_policy')}")
    lines.append(f"Total events: {overview.get('total_events')}")
    lines.append(f"Resolved events: {overview.get('resolved_events')}")
    lines.append(f"Expired events: {overview.get('expired_events')}")
    lines.append(f"No-market-data events: {overview.get('no_market_data_events')}")
    lines.append(f"Overall event win rate: {format_pct(overview.get('overall_event_win_rate'))}")
    lines.append(f"Total combo rows: {overview.get('total_combos')}")
    lines.append(f"Strong combinations: {overview.get('strong_rows')}")
    lines.append(f"Usable combinations: {overview.get('usable_rows')}")
    lines.append(f"Weak combinations: {overview.get('weak_rows')}")
    lines.append(f"Weak-sample combinations: {overview.get('weak_sample_rows')}")
    lines.append(f"Fetched log rows: {fetch_stats.get('fetched_log_rows')}")
    lines.append(f"Fetched candle rows: {fetch_stats.get('fetched_candle_rows')}")
    lines.append("")
    lines.append(f"Most Frequent Common Combos ({top_n})")
    lines.append("=" * 90)
    for row in payload.get("most_frequent_common") or []:
        lines.append(
            f"{row.get('symbol')} {row.get('direction')} | {row.get('combination')} | "
            f"occ={row.get('occurrences')} | wins={row.get('wins')}/{row.get('resolved_count')} | "
            f"expired={row.get('expired')} | completion={format_pct(row.get('completion_rate'))} | "
            f"win_rate={format_pct(row.get('win_rate'))} | pf={format_num(row.get('profit_factor'))} | "
            f"exp={format_num(row.get('expectancy'), 4)} | quality={row.get('quality')}"
        )
    lines.append("")
    lines.append(f"Best Stable Combos ({top_n})")
    lines.append("=" * 90)
    for row in payload.get("best_stable") or []:
        lines.append(
            f"{row.get('symbol')} {row.get('direction')} | {row.get('combination')} | "
            f"occ={row.get('occurrences')} | wins={row.get('wins')}/{row.get('resolved_count')} | "
            f"expired={row.get('expired')} | stability={format_num(row.get('stability_score'), 4)} | "
            f"completion={format_pct(row.get('completion_rate'))} | win_rate={format_pct(row.get('win_rate'))} | "
            f"pf={format_num(row.get('profit_factor'))} | exp={format_num(row.get('expectancy'), 4)} | quality={row.get('quality')}"
        )
    lines.append("")
    lines.append(f"Overall Top {top_n} combinations")
    lines.append("=" * 90)
    for row in payload.get("overall_top") or []:
        lines.append(
            f"{row.get('symbol')} {row.get('direction')} | {row.get('combination')} | "
            f"occ={row.get('occurrences')} | wins={row.get('wins')}/{row.get('resolved_count')} | "
            f"expired={row.get('expired')} | win_rate={format_pct(row.get('win_rate'))} | "
            f"pf={format_num(row.get('profit_factor'))} | exp={format_num(row.get('expectancy'), 4)} | quality={row.get('quality')}"
        )
    lines.append("")
    lines.append(f"Overall Weakest {top_n} combinations")
    lines.append("=" * 90)
    for row in payload.get("overall_bottom") or []:
        lines.append(
            f"{row.get('symbol')} {row.get('direction')} | {row.get('combination')} | "
            f"occ={row.get('occurrences')} | wins={row.get('wins')}/{row.get('resolved_count')} | "
            f"expired={row.get('expired')} | win_rate={format_pct(row.get('win_rate'))} | "
            f"pf={format_num(row.get('profit_factor'))} | exp={format_num(row.get('expectancy'), 4)} | quality={row.get('quality')}"
        )
    for context in payload.get("contexts") or []:
        lines.append("")
        lines.append(f"Context: {context.get('symbol')} {context.get('direction')}")
        lines.append("-" * 90)
        lines.append(
            f"rows={context.get('row_count')} | strong={context.get('strong_count')} | "
            f"usable={context.get('usable_count')} | weak={context.get('weak_count')} | weak_sample={context.get('weak_sample_count')}"
        )
        for row in context.get("top_rows") or []:
            lines.append(
                f"{row.get('combination')} | occ={row.get('occurrences')} | wins={row.get('wins')}/{row.get('resolved_count')} | "
                f"expired={row.get('expired')} | win_rate={format_pct(row.get('win_rate'))} | "
                f"pf={format_num(row.get('profit_factor'))} | exp={format_num(row.get('expectancy'), 4)} | quality={row.get('quality')}"
            )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", action="append", default=[])
    parser.add_argument("--direction", action="append", default=[])
    parser.add_argument("--lookback-days", type=int, default=365)
    parser.add_argument("--bucket-minutes", type=int, default=5)
    parser.add_argument("--min-models-per-event", type=int, default=2)
    parser.add_argument("--min-occurrences", type=int, default=5)
    parser.add_argument("--max-combo-size", type=int, default=4)
    parser.add_argument("--target-level", default="TP1")
    parser.add_argument("--price-timeframe", default="signal")
    parser.add_argument("--tie-policy", choices=["stop_first", "target_first"], default="stop_first")
    parser.add_argument("--query-limit", type=int, default=4000)
    parser.add_argument("--min-split-minutes", type=int, default=60)
    parser.add_argument("--output-dir", default="~/Desktop/permutation_runs")
    parser.add_argument("--output-prefix", default="consensus_model_analysis")
    parser.add_argument("--top", type=int, default=15)
    args = parser.parse_args()

    args.symbol = args.symbol or list(SUPPORTED_SYMBOLS)
    args.direction = [direction.upper().strip() for direction in (args.direction or ["BUY", "SELL"])]
    args.symbol = [str(symbol).upper().strip() for symbol in args.symbol]
    args.price_timeframe = str(args.price_timeframe or "signal").lower().strip()

    client = get_supabase_client()
    if not client:
        raise SystemExit("No Supabase client available")

    lookback_start = datetime.now(timezone.utc) - timedelta(days=max(args.lookback_days, 1))
    analysis_end = datetime.now(timezone.utc) + timedelta(days=3)
    fetched_log_rows = 0
    fetched_candle_rows = 0
    all_events: List[Dict[str, Any]] = []
    fetch_stats: Dict[str, Any] = {
        "log_fetches": [],
        "candle_fetches": [],
        "event_build_stats": [],
    }

    for symbol in args.symbol:
        symbol_logs: List[Dict[str, Any]] = []
        for direction in args.direction:
            raw_logs = recursive_prediction_log_fetch(
                client,
                symbol=symbol,
                direction=direction,
                start_dt=lookback_start,
                end_dt=analysis_end,
                limit=args.query_limit,
                min_split_minutes=args.min_split_minutes,
            )
            prepared_logs = prepare_logs(raw_logs)
            symbol_direction_logs = [row for row in prepared_logs if row.get("symbol") == symbol and row.get("ml_direction") == direction]
            symbol_logs.extend(symbol_direction_logs)
            fetched_log_rows += len(symbol_direction_logs)
            fetch_stats["log_fetches"].append({
                "symbol": symbol,
                "direction": direction,
                "rows": len(symbol_direction_logs),
            })
            events, event_stats = build_events(
                symbol_direction_logs,
                symbol=symbol,
                direction=direction,
                bucket_minutes=args.bucket_minutes,
                min_models_per_event=args.min_models_per_event,
            )
            fetch_stats["event_build_stats"].append({
                "symbol": symbol,
                "direction": direction,
                **event_stats,
                "events": len(events),
            })
            all_events.extend(events)

        symbol_events = [event for event in all_events if event.get("symbol") == symbol]
        if not symbol_events:
            continue
        required_timeframes = sorted({
            resolve_price_timeframe(args.price_timeframe, event.get("event_timeframe"))
            for event in symbol_events
        })
        if "5m" not in required_timeframes:
            required_timeframes.append("5m")
            required_timeframes.sort()
        candles_by_timeframe: Dict[str, List[Dict[str, Any]]] = {}
        candle_timestamps_by_timeframe: Dict[str, List[float]] = {}
        for timeframe in required_timeframes:
            candle_rows = recursive_candle_fetch(
                client,
                symbol=symbol,
                timeframe=timeframe,
                start_dt=lookback_start - timedelta(days=1),
                end_dt=analysis_end,
                limit=args.query_limit,
                min_split_minutes=max(args.min_split_minutes, 240),
            )
            prepared_candles = prepare_candles(candle_rows)
            candles_by_timeframe[timeframe] = prepared_candles
            candle_timestamps_by_timeframe[timeframe] = [float(candle["_ts_ms"]) for candle in prepared_candles]
            fetched_candle_rows += len(prepared_candles)
            fetch_stats["candle_fetches"].append({
                "symbol": symbol,
                "timeframe": timeframe,
                "rows": len(prepared_candles),
            })
        for event in symbol_events:
            preferred_price_timeframe = resolve_price_timeframe(args.price_timeframe, event.get("event_timeframe"))
            resolved_price_timeframe = choose_available_price_timeframe(preferred_price_timeframe, candles_by_timeframe)
            event_candles = candles_by_timeframe.get(resolved_price_timeframe) or []
            event_candle_timestamps = candle_timestamps_by_timeframe.get(resolved_price_timeframe) or []
            outcome_payload = simulate_event_outcome(
                event,
                event_candles,
                event_candle_timestamps,
                target_level=args.target_level,
                price_timeframe=resolved_price_timeframe,
                tie_policy=args.tie_policy,
            )
            if resolved_price_timeframe != preferred_price_timeframe:
                outcome_payload["preferred_price_timeframe"] = preferred_price_timeframe
            event.update(outcome_payload)

    combo_rows, aggregate_stats = aggregate_combos(
        all_events,
        max_combo_size=args.max_combo_size,
        min_occurrences=args.min_occurrences,
    )
    fetch_stats.update(aggregate_stats)
    fetch_stats["fetched_log_rows"] = fetched_log_rows
    fetch_stats["fetched_candle_rows"] = fetched_candle_rows

    payload = build_payload(events=all_events, combo_rows=combo_rows, args=args, fetch_stats=fetch_stats)

    output_dir = Path(args.output_dir).expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"{args.output_prefix}.json"
    csv_path = output_dir / f"{args.output_prefix}.csv"
    txt_path = output_dir / f"{args.output_prefix}.txt"
    write_json(json_path, payload)
    write_csv(csv_path, combo_rows)
    txt_path.write_text(build_txt(payload, args.top))
    print(json.dumps({
        "json": str(json_path),
        "csv": str(csv_path),
        "txt": str(txt_path),
        "events": len(all_events),
        "combos": len(combo_rows),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
