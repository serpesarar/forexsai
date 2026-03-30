from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from itertools import combinations
from typing import Any, Dict, Iterable, List, Optional, Sequence
from uuid import uuid4

import numpy as np
import pandas as pd

from database.supabase_client import get_supabase_client, is_db_available
from services.candle_cache_store import load_candles
from services.permutation_analysis_service import analyze_model_permutations

logger = logging.getLogger(__name__)

DEFAULT_SYMBOLS = ("NDX.INDX", "XAUUSD", "GDAXI.INDX", "USOIL.FOREX")
DEFAULT_DIRECTIONS = ("BUY", "SELL")
DEFAULT_TECHNICAL_TIMEFRAMES = ("5m", "30m", "1h", "eod")
DEFAULT_QUANTILES = (0.025, 0.05, 0.075, 0.1, 0.125, 0.15, 0.175, 0.2, 0.225, 0.25, 0.275, 0.3, 0.325, 0.35, 0.375, 0.4, 0.425, 0.45, 0.475, 0.5, 0.525, 0.55, 0.575, 0.6, 0.625, 0.65, 0.675, 0.7, 0.725, 0.75, 0.775, 0.8, 0.825, 0.85, 0.875, 0.9, 0.925, 0.95, 0.975)
TIMEFRAME_RULES = {
    "5m": "5min",
    "15m": "15min",
    "30m": "30min",
    "1h": "1h",
    "4h": "4h",
    "eod": "1d",
}
RESAMPLE_SOURCES = {
    "30m": ("5m",),
    "1h": ("30m", "5m"),
    "4h": ("1h", "30m", "5m"),
}
SYMBOL_ALIASES = {
    "NASDAQ": "NDX.INDX",
    "NDX": "NDX.INDX",
    "DAX": "GDAXI.INDX",
    "GDAXI": "GDAXI.INDX",
    "XAU": "XAUUSD",
    "GOLD": "XAUUSD",
    "WTI": "USOIL.FOREX",
    "CL.COMM": "USOIL.FOREX",
    "USOIL": "USOIL.FOREX",
}


@dataclass
class AtomicRule:
    key: str
    feature: str
    operator: str
    threshold: float
    quantile: float
    mask: np.ndarray
    occurrences: int
    wins: int
    win_rate: float
    expectancy: float


@dataclass
class PermutationBatchConfig:
    symbols: Sequence[str] = DEFAULT_SYMBOLS
    directions: Sequence[str] = DEFAULT_DIRECTIONS
    technical_timeframes: Sequence[str] = DEFAULT_TECHNICAL_TIMEFRAMES
    model_lookback_days: int = 180
    model_min_occurrences: int = 5
    cluster_window_minutes: int = 10
    technical_min_occurrences: int = 40
    technical_candle_limit: int = 5000
    lookforward_candles: int = 5
    target_move_pct: float = 0.3
    stop_move_pct: float = 0.3
    quantiles: Sequence[float] = DEFAULT_QUANTILES
    top_thresholds_per_indicator: int = 6
    max_atomic_rules: int = 48
    max_combination_size: int = 6
    top_results_per_context: int = 750
    resample_missing_timeframes: bool = True
    dry_run: bool = True
    lookforward_grid: Sequence[int] = ()
    target_move_grid: Sequence[float] = ()
    stop_move_grid: Sequence[float] = ()
    walk_forward_splits: int = 0
    walk_forward_test_size: int = 80
    walk_forward_min_train_size: int = 250
    walk_forward_top_candidates: int = 250


def _utc_iso(value: Optional[datetime] = None) -> str:
    dt = value or datetime.now(timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _normalize_symbol(symbol: str) -> str:
    raw = (symbol or "").upper().strip()
    return SYMBOL_ALIASES.get(raw, raw)


def _rows(result: Any) -> List[Dict[str, Any]]:
    if isinstance(result, dict):
        data = result.get("data", [])
    else:
        data = getattr(result, "data", [])
    return data if isinstance(data, list) else []


def _chunked(values: List[Dict[str, Any]], size: int) -> Iterable[List[Dict[str, Any]]]:
    for index in range(0, len(values), size):
        yield values[index:index + size]


def _json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_ready(val) for key, val in value.items()}
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    return value


def _resolve_int_grid(values: Sequence[int], fallback: int) -> List[int]:
    resolved = sorted({int(value) for value in values if int(value) > 0}) if values else []
    return resolved or [int(fallback)]


def _resolve_float_grid(values: Sequence[float], fallback: float) -> List[float]:
    resolved = sorted({round(float(value), 6) for value in values if float(value) > 0}) if values else []
    return resolved or [round(float(fallback), 6)]


def _profile_float_fragment(value: float) -> str:
    return f"{float(value):.4f}".rstrip("0").rstrip(".").replace("-", "n").replace(".", "p")


def _build_profile_key(lookforward_candles: int, target_move_pct: float, stop_move_pct: float, walk_forward_splits: int = 0) -> str:
    return (
        f"lf{int(lookforward_candles)}_"
        f"tp{_profile_float_fragment(target_move_pct)}_"
        f"sl{_profile_float_fragment(stop_move_pct)}_"
        f"wf{int(max(walk_forward_splits, 0))}"
    )


def _parse_candle_datetime(value: Any, fallback_timestamp: Any = None) -> Optional[pd.Timestamp]:
    parsed = pd.to_datetime(value, utc=True, errors="coerce")
    if pd.isna(parsed) and fallback_timestamp not in (None, ""):
        parsed = pd.to_datetime(fallback_timestamp, unit="ms", utc=True, errors="coerce")
    return None if pd.isna(parsed) else parsed


def _resample_candles(candles: List[Dict[str, Any]], target_timeframe: str) -> List[Dict[str, Any]]:
    rule = TIMEFRAME_RULES.get(target_timeframe)
    if not candles or not rule:
        return []

    df = pd.DataFrame(candles)
    if df.empty:
        return []

    df["dt"] = [
        _parse_candle_datetime(row.get("date"), row.get("timestamp"))
        for _, row in df.iterrows()
    ]
    for column in ["open", "high", "low", "close", "volume"]:
        df[column] = pd.to_numeric(df.get(column), errors="coerce")
    df = df.dropna(subset=["dt", "open", "high", "low", "close"]).sort_values("dt")
    if df.empty:
        return []

    resampled = (
        df.set_index("dt")
        .resample(rule, label="right", closed="right")
        .agg({
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum",
        })
        .dropna(subset=["open", "high", "low", "close"])
        .reset_index()
    )
    if resampled.empty:
        return []

    output: List[Dict[str, Any]] = []
    for _, row in resampled.iterrows():
        dt = row["dt"]
        output.append({
            "timestamp": int(dt.timestamp() * 1000),
            "date": dt.isoformat(),
            "open": float(row["open"]),
            "high": float(row["high"]),
            "low": float(row["low"]),
            "close": float(row["close"]),
            "volume": float(row["volume"] or 0.0),
        })
    return output


def _load_technical_candles(symbol: str, timeframe: str, limit: int, resample_missing_timeframes: bool) -> tuple[List[Dict[str, Any]], Optional[str]]:
    candles = load_candles(symbol, timeframe, limit)
    if candles or not resample_missing_timeframes:
        return candles, None

    for source_timeframe in RESAMPLE_SOURCES.get(timeframe, ()): 
        ratio_limit = limit * 12 if source_timeframe == "5m" else limit * 4
        source_candles = load_candles(symbol, source_timeframe, min(ratio_limit, 50000))
        if not source_candles:
            continue
        resampled = _resample_candles(source_candles, timeframe)
        if resampled:
            return resampled[-limit:], source_timeframe
    return [], None


def _upsert_rows(client, table_name: str, rows: List[Dict[str, Any]], on_conflict: str) -> None:
    if not rows:
        return
    for batch in _chunked(rows, 500):
        result = client.table(table_name).upsert(batch, on_conflict=on_conflict)
        if (result or {}).get("error"):
            raise RuntimeError(f"{table_name} upsert failed: {(result or {}).get('error')}")


def _insert_run(client, batch_kind: str, config: PermutationBatchConfig) -> str:
    run_id = str(uuid4())
    payload = {
        "id": run_id,
        "batch_kind": batch_kind,
        "status": "running",
        "symbols": list(config.symbols),
        "directions": list(config.directions),
        "timeframes": list(config.technical_timeframes),
        "parameters": _json_ready({
            "model_lookback_days": config.model_lookback_days,
            "model_min_occurrences": config.model_min_occurrences,
            "cluster_window_minutes": config.cluster_window_minutes,
            "technical_min_occurrences": config.technical_min_occurrences,
            "technical_candle_limit": config.technical_candle_limit,
            "lookforward_candles": config.lookforward_candles,
            "target_move_pct": config.target_move_pct,
            "stop_move_pct": config.stop_move_pct,
            "quantiles": list(config.quantiles),
            "top_thresholds_per_indicator": config.top_thresholds_per_indicator,
            "max_atomic_rules": config.max_atomic_rules,
            "max_combination_size": config.max_combination_size,
            "top_results_per_context": config.top_results_per_context,
            "resample_missing_timeframes": config.resample_missing_timeframes,
            "dry_run": config.dry_run,
            "lookforward_grid": list(config.lookforward_grid),
            "target_move_grid": list(config.target_move_grid),
            "stop_move_grid": list(config.stop_move_grid),
            "walk_forward_splits": config.walk_forward_splits,
            "walk_forward_test_size": config.walk_forward_test_size,
            "walk_forward_min_train_size": config.walk_forward_min_train_size,
            "walk_forward_top_candidates": config.walk_forward_top_candidates,
        }),
        "started_at": _utc_iso(),
    }
    result = client.table("permutation_batch_runs").insert(payload)
    if (result or {}).get("error"):
        raise RuntimeError((result or {}).get("error"))
    return run_id


def _finish_run(client, run_id: str, *, status: str, summary: Dict[str, Any], error: Optional[str] = None) -> None:
    payload: Dict[str, Any] = {
        "status": status,
        "summary": _json_ready(summary),
        "completed_at": _utc_iso(),
    }
    if error:
        payload["error"] = error
    result = client.table("permutation_batch_runs").eq("id", run_id).update(payload)
    if (result or {}).get("error"):
        raise RuntimeError((result or {}).get("error"))


def _prepare_technical_dataframe(candles: List[Dict[str, Any]]) -> pd.DataFrame:
    import ta

    df = pd.DataFrame(candles)
    if df.empty:
        return df
    for column in ["open", "high", "low", "close", "volume"]:
        df[column] = pd.to_numeric(df.get(column), errors="coerce")
    df = df.dropna(subset=["open", "high", "low", "close"]).reset_index(drop=True)
    if df.empty:
        return df

    closes = df["close"]
    highs = df["high"]
    lows = df["low"]
    volumes = df.get("volume", pd.Series([0.0] * len(df))).fillna(0.0)

    df["rsi_14"] = ta.momentum.RSIIndicator(closes, window=14).rsi()
    df["ema_20"] = ta.trend.ema_indicator(closes, window=20)
    df["ema_50"] = ta.trend.ema_indicator(closes, window=50)
    df["ema_200"] = ta.trend.ema_indicator(closes, window=200)
    macd = ta.trend.MACD(closes)
    df["macd_hist"] = macd.macd_diff()
    df["adx"] = ta.trend.ADXIndicator(highs, lows, closes, window=14).adx()
    df["atr"] = ta.volatility.AverageTrueRange(highs, lows, closes, window=14).average_true_range()
    df["cci_20"] = ta.trend.CCIIndicator(highs, lows, closes, window=20).cci()
    df["roc_10"] = ta.momentum.ROCIndicator(closes, window=10).roc()
    df["willr_14"] = ta.momentum.WilliamsRIndicator(highs, lows, closes, lbp=14).williams_r()
    df["mfi_14"] = ta.volume.MFIIndicator(highs, lows, closes, volumes, window=14).money_flow_index()
    df["force_index_13"] = ta.volume.ForceIndexIndicator(closes, volumes, window=13).force_index()
    stoch = ta.momentum.StochasticOscillator(highs, lows, closes, window=14, smooth_window=3)
    df["stoch_k"] = stoch.stoch()
    df["stoch_d"] = stoch.stoch_signal()
    bb = ta.volatility.BollingerBands(closes, window=20, window_dev=2)
    df["bb_high"] = bb.bollinger_hband()
    df["bb_low"] = bb.bollinger_lband()

    df["ema20_dist"] = ((closes - df["ema_20"]) / df["ema_20"]) * 100
    df["ema50_dist"] = ((closes - df["ema_50"]) / df["ema_50"]) * 100
    df["ema200_dist"] = ((closes - df["ema_200"]) / df["ema_200"]) * 100
    df["vol_sma"] = volumes.rolling(window=20).mean()
    df["volume_ratio"] = np.where(df["vol_sma"] > 0, volumes / df["vol_sma"], 1.0)
    atr_median = df["atr"].rolling(window=20).median()
    df["atr_ratio"] = np.where(atr_median > 0, df["atr"] / atr_median, 1.0)
    band_width = (df["bb_high"] - df["bb_low"]).replace(0, np.nan)
    df["bb_position"] = (closes - df["bb_low"]) / band_width
    df["body_pct"] = np.where(df["open"] != 0, ((df["close"] - df["open"]) / df["open"]) * 100.0, 0.0)
    df["range_pct"] = np.where(df["open"] != 0, ((df["high"] - df["low"]) / df["open"]) * 100.0, 0.0)
    df["upper_wick_pct"] = np.where(df["open"] != 0, ((df["high"] - np.maximum(df["open"], df["close"])) / df["open"]) * 100.0, 0.0)
    df["lower_wick_pct"] = np.where(df["open"] != 0, ((np.minimum(df["open"], df["close"]) - df["low"]) / df["open"]) * 100.0, 0.0)
    df["macd_hist_delta"] = df["macd_hist"].diff()
    df["adx_delta"] = df["adx"].diff()
    df["rsi_delta"] = df["rsi_14"].diff()
    df["price_return_1"] = closes.pct_change() * 100.0
    df["price_return_3"] = closes.pct_change(3) * 100.0

    return df


def _label_outcomes(df: pd.DataFrame, direction: str, lookforward_candles: int, target_move_pct: float, stop_move_pct: float) -> pd.DataFrame:
    win_flags: List[Optional[bool]] = []
    realized_returns: List[Optional[float]] = []
    for index in range(len(df)):
        if index + lookforward_candles >= len(df):
            win_flags.append(None)
            realized_returns.append(None)
            continue
        current_close = float(df.loc[index, "close"])
        is_win = False
        realized = None
        for step in range(1, lookforward_candles + 1):
            future_index = index + step
            future_high = float(df.loc[future_index, "high"])
            future_low = float(df.loc[future_index, "low"])
            if direction == "BUY":
                target = current_close * (1 + target_move_pct / 100.0)
                stop_level = current_close * (1 - stop_move_pct / 100.0)
                if future_low <= stop_level:
                    is_win = False
                    realized = -stop_move_pct
                    break
                if future_high >= target:
                    is_win = True
                    realized = target_move_pct
                    break
            else:
                target = current_close * (1 - target_move_pct / 100.0)
                stop_level = current_close * (1 + stop_move_pct / 100.0)
                if future_high >= stop_level:
                    is_win = False
                    realized = -stop_move_pct
                    break
                if future_low <= target:
                    is_win = True
                    realized = target_move_pct
                    break
        if realized is None:
            final_close = float(df.loc[index + lookforward_candles, "close"])
            move_pct = ((final_close - current_close) / current_close) * 100.0
            realized = move_pct if direction == "BUY" else -move_pct
            is_win = realized > 0
        win_flags.append(is_win)
        realized_returns.append(realized)

    labeled = df.copy()
    labeled["is_win"] = win_flags
    labeled["realized_return"] = realized_returns
    return labeled.dropna(subset=["is_win", "realized_return", "close", "high", "low"]).reset_index(drop=True)


def _build_atomic_rules(df: pd.DataFrame, min_occurrences: int, quantiles: Sequence[float], top_thresholds_per_indicator: int, max_atomic_rules: int) -> List[AtomicRule]:
    feature_columns = [
        "rsi_14",
        "ema20_dist",
        "ema50_dist",
        "ema200_dist",
        "adx",
        "adx_delta",
        "macd_hist",
        "macd_hist_delta",
        "volume_ratio",
        "atr_ratio",
        "bb_position",
        "cci_20",
        "roc_10",
        "willr_14",
        "mfi_14",
        "force_index_13",
        "stoch_k",
        "stoch_d",
        "rsi_delta",
        "price_return_1",
        "price_return_3",
        "body_pct",
        "range_pct",
        "upper_wick_pct",
        "lower_wick_pct",
    ]
    atomic_rules: List[AtomicRule] = []
    win_array = df["is_win"].to_numpy(dtype=bool)
    return_array = df["realized_return"].to_numpy(dtype=float)

    for feature in feature_columns:
        series = df[feature].dropna()
        if len(series) < min_occurrences:
            continue
        candidates: List[AtomicRule] = []
        seen = set()
        for quantile in quantiles:
            threshold = float(series.quantile(quantile))
            for operator in (">=", "<="):
                dedupe_key = (feature, operator, round(threshold, 8))
                if dedupe_key in seen:
                    continue
                seen.add(dedupe_key)
                mask = df[feature].to_numpy(dtype=float) >= threshold if operator == ">=" else df[feature].to_numpy(dtype=float) <= threshold
                occurrences = int(mask.sum())
                if occurrences < min_occurrences:
                    continue
                wins = int(win_array[mask].sum())
                expectancy = float(return_array[mask].mean()) if occurrences > 0 else 0.0
                candidates.append(AtomicRule(
                    key=f"{feature}{operator}{round(threshold, 6)}",
                    feature=feature,
                    operator=operator,
                    threshold=threshold,
                    quantile=float(quantile),
                    mask=mask,
                    occurrences=occurrences,
                    wins=wins,
                    win_rate=wins / max(occurrences, 1),
                    expectancy=expectancy,
                ))
        candidates.sort(key=lambda rule: (rule.win_rate, rule.expectancy, rule.occurrences), reverse=True)
        atomic_rules.extend(candidates[:top_thresholds_per_indicator])

    atomic_rules.sort(key=lambda rule: (rule.win_rate, rule.expectancy, rule.occurrences), reverse=True)
    return atomic_rules[:max_atomic_rules]


def _search_rule_combinations(df: pd.DataFrame, atomic_rules: List[AtomicRule], min_occurrences: int, max_combination_size: int) -> List[Dict[str, Any]]:
    win_array = df["is_win"].to_numpy(dtype=bool)
    return_array = df["realized_return"].to_numpy(dtype=float)
    results: List[Dict[str, Any]] = []

    for size in range(2, min(max_combination_size, len(atomic_rules)) + 1):
        for combo in combinations(atomic_rules, size):
            feature_names = [rule.feature for rule in combo]
            if len(set(feature_names)) != len(feature_names):
                continue
            mask = combo[0].mask.copy()
            for rule in combo[1:]:
                mask &= rule.mask
                if int(mask.sum()) < min_occurrences:
                    break
            occurrences = int(mask.sum())
            if occurrences < min_occurrences:
                continue
            wins = int(win_array[mask].sum())
            losses = occurrences - wins
            selected_returns = return_array[mask]
            positive_sum = float(selected_returns[selected_returns > 0].sum())
            negative_sum = float(np.abs(selected_returns[selected_returns < 0].sum()))
            results.append({
                "rule_key": " && ".join(rule.key for rule in combo),
                "rule_definition": [
                    {
                        "indicator": rule.feature,
                        "operator": rule.operator,
                        "threshold": round(rule.threshold, 8),
                        "quantile": rule.quantile,
                    }
                    for rule in combo
                ],
                "threshold_quantiles": [rule.quantile for rule in combo],
                "combination_size": size,
                "occurrences": occurrences,
                "wins": wins,
                "losses": losses,
                "win_rate": wins / max(occurrences, 1),
                "profit_factor": positive_sum / negative_sum if negative_sum > 0 else (999.0 if positive_sum > 0 else 0.0),
                "expectancy": float(selected_returns.mean()) if occurrences > 0 else 0.0,
                "avg_forward_return": float(selected_returns.mean()) if occurrences > 0 else 0.0,
            })
    results.sort(key=lambda row: (row["win_rate"], row["expectancy"], row["occurrences"]), reverse=True)
    return results


def _rule_signature(rule_definition: List[Dict[str, Any]]) -> str:
    parts: List[str] = []
    for item in rule_definition:
        indicator = str(item.get("indicator") or "")
        operator = str(item.get("operator") or "")
        quantile = round(float(item.get("quantile") or 0.0), 6)
        parts.append(f"{indicator}{operator}q{quantile}")
    return " && ".join(parts)


def _mask_from_rule_definition(df: pd.DataFrame, rule_definition: List[Dict[str, Any]]) -> np.ndarray:
    if df.empty:
        return np.zeros(0, dtype=bool)
    mask = np.ones(len(df), dtype=bool)
    for item in rule_definition:
        indicator = str(item.get("indicator") or "")
        operator = str(item.get("operator") or "")
        threshold = float(item.get("threshold") or 0.0)
        if indicator not in df.columns:
            return np.zeros(len(df), dtype=bool)
        values = pd.to_numeric(df[indicator], errors="coerce").to_numpy(dtype=float)
        condition = values >= threshold if operator == ">=" else values <= threshold
        mask &= condition & ~np.isnan(values)
        if not mask.any():
            break
    return mask


def _evaluate_rule_definition(df: pd.DataFrame, rule_definition: List[Dict[str, Any]]) -> Dict[str, Any]:
    mask = _mask_from_rule_definition(df, rule_definition)
    occurrences = int(mask.sum())
    if occurrences <= 0:
        return {
            "occurrences": 0,
            "wins": 0,
            "losses": 0,
            "win_rate": 0.0,
            "expectancy": 0.0,
            "avg_forward_return": 0.0,
            "positive_sum": 0.0,
            "negative_sum": 0.0,
        }

    win_array = df["is_win"].to_numpy(dtype=bool)
    return_array = df["realized_return"].to_numpy(dtype=float)
    wins = int(win_array[mask].sum())
    losses = occurrences - wins
    selected_returns = return_array[mask]
    positive_sum = float(selected_returns[selected_returns > 0].sum())
    negative_sum = float(np.abs(selected_returns[selected_returns < 0].sum()))
    expectancy = float(selected_returns.mean()) if occurrences > 0 else 0.0
    return {
        "occurrences": occurrences,
        "wins": wins,
        "losses": losses,
        "win_rate": wins / max(occurrences, 1),
        "expectancy": expectancy,
        "avg_forward_return": expectancy,
        "positive_sum": positive_sum,
        "negative_sum": negative_sum,
    }


def _build_walk_forward_slices(row_count: int, splits: int, min_train_size: int, test_size: int) -> List[tuple[int, int]]:
    if splits <= 0 or row_count < (min_train_size + test_size):
        return []
    max_train_end = row_count - test_size
    if max_train_end <= min_train_size:
        return []
    train_end_points = np.linspace(min_train_size, max_train_end, num=max(splits, 1), dtype=int)
    slices: List[tuple[int, int]] = []
    seen = set()
    for raw_train_end in train_end_points.tolist():
        train_end = int(max(min_train_size, min(raw_train_end, max_train_end)))
        if train_end in seen:
            continue
        seen.add(train_end)
        test_end = min(train_end + test_size, row_count)
        if test_end - train_end <= 0:
            continue
        slices.append((train_end, test_end))
    return slices


def _search_walk_forward_combinations(labeled_df: pd.DataFrame, config: PermutationBatchConfig) -> List[Dict[str, Any]]:
    slices = _build_walk_forward_slices(
        len(labeled_df),
        config.walk_forward_splits,
        config.walk_forward_min_train_size,
        config.walk_forward_test_size,
    )
    if not slices:
        return []

    aggregate: Dict[str, Dict[str, Any]] = {}
    for train_end, test_end in slices:
        train_df = labeled_df.iloc[:train_end].reset_index(drop=True)
        test_df = labeled_df.iloc[train_end:test_end].reset_index(drop=True)
        if len(train_df) < config.technical_min_occurrences or len(test_df) <= 0:
            continue

        atomic_rules = _build_atomic_rules(
            train_df,
            config.technical_min_occurrences,
            config.quantiles,
            config.top_thresholds_per_indicator,
            config.max_atomic_rules,
        )
        if len(atomic_rules) < 2:
            continue

        train_rows = _search_rule_combinations(
            train_df,
            atomic_rules,
            config.technical_min_occurrences,
            config.max_combination_size,
        )
        for row in train_rows[: max(1, config.walk_forward_top_candidates)]:
            signature = _rule_signature(row["rule_definition"])
            if not signature:
                continue
            validation = _evaluate_rule_definition(test_df, row["rule_definition"])
            if signature not in aggregate:
                aggregate[signature] = {
                    "rule_key": signature,
                    "components": [
                        {
                            "indicator": component["indicator"],
                            "operator": component["operator"],
                            "quantile": float(component.get("quantile") or 0.0),
                            "threshold_sum": float(component.get("threshold") or 0.0),
                            "count": 1,
                        }
                        for component in row["rule_definition"]
                    ],
                    "threshold_quantiles": [float(component.get("quantile") or 0.0) for component in row["rule_definition"]],
                    "combination_size": int(row["combination_size"]),
                    "train_occurrences": 0,
                    "train_wins": 0,
                    "train_return_sum": 0.0,
                    "validation_occurrences": 0,
                    "validation_wins": 0,
                    "validation_return_sum": 0.0,
                    "validation_positive_sum": 0.0,
                    "validation_negative_sum": 0.0,
                    "walk_forward_passes": 0,
                    "walk_forward_folds": 0,
                }
            else:
                for index, component in enumerate(row["rule_definition"]):
                    aggregate[signature]["components"][index]["threshold_sum"] += float(component.get("threshold") or 0.0)
                    aggregate[signature]["components"][index]["count"] += 1

            entry = aggregate[signature]
            train_occurrences = int(row["occurrences"])
            entry["train_occurrences"] += train_occurrences
            entry["train_wins"] += int(row["wins"])
            entry["train_return_sum"] += float(row["expectancy"]) * train_occurrences
            entry["validation_occurrences"] += int(validation["occurrences"])
            entry["validation_wins"] += int(validation["wins"])
            entry["validation_return_sum"] += float(validation["expectancy"]) * int(validation["occurrences"])
            entry["validation_positive_sum"] += float(validation["positive_sum"])
            entry["validation_negative_sum"] += float(validation["negative_sum"])
            entry["walk_forward_folds"] += 1
            if int(validation["occurrences"]) > 0:
                entry["walk_forward_passes"] += 1

    results: List[Dict[str, Any]] = []
    min_passes = max(1, min(config.walk_forward_splits, 2))
    for entry in aggregate.values():
        validation_occurrences = int(entry["validation_occurrences"])
        if validation_occurrences < config.technical_min_occurrences:
            continue
        if int(entry["walk_forward_passes"]) < min_passes:
            continue
        validation_wins = int(entry["validation_wins"])
        validation_negative_sum = float(entry["validation_negative_sum"])
        avg_rule_definition = [
            {
                "indicator": component["indicator"],
                "operator": component["operator"],
                "threshold": round(component["threshold_sum"] / max(component["count"], 1), 8),
                "quantile": component["quantile"],
            }
            for component in entry["components"]
        ]
        train_occurrences = int(entry["train_occurrences"])
        train_wins = int(entry["train_wins"])
        validation_expectancy = float(entry["validation_return_sum"]) / max(validation_occurrences, 1)
        train_expectancy = float(entry["train_return_sum"]) / max(train_occurrences, 1)
        results.append({
            "rule_key": entry["rule_key"],
            "rule_definition": avg_rule_definition,
            "threshold_quantiles": entry["threshold_quantiles"],
            "combination_size": int(entry["combination_size"]),
            "occurrences": validation_occurrences,
            "wins": validation_wins,
            "losses": validation_occurrences - validation_wins,
            "win_rate": validation_wins / max(validation_occurrences, 1),
            "profit_factor": float(entry["validation_positive_sum"]) / validation_negative_sum if validation_negative_sum > 0 else (999.0 if float(entry["validation_positive_sum"]) > 0 else 0.0),
            "expectancy": validation_expectancy,
            "avg_forward_return": validation_expectancy,
            "train_occurrences": train_occurrences,
            "train_wins": train_wins,
            "train_win_rate": train_wins / max(train_occurrences, 1),
            "train_expectancy": train_expectancy,
            "validation_occurrences": validation_occurrences,
            "validation_wins": validation_wins,
            "validation_win_rate": validation_wins / max(validation_occurrences, 1),
            "validation_expectancy": validation_expectancy,
            "walk_forward_splits": int(config.walk_forward_splits),
            "walk_forward_passes": int(entry["walk_forward_passes"]),
            "walk_forward_folds": int(entry["walk_forward_folds"]),
        })
    results.sort(
        key=lambda row: (
            row["validation_win_rate"],
            row["validation_expectancy"],
            row["validation_occurrences"],
            row["walk_forward_passes"],
        ),
        reverse=True,
    )
    return results


def _load_completed_runs(client, limit: int = 20) -> List[Dict[str, Any]]:
    result = (
        client.table("permutation_batch_runs")
        .select("id,batch_kind,status,parameters,summary,started_at,completed_at,error")
        .eq("status", "completed")
        .in_("batch_kind", ["full", "model", "technical"])
        .order("started_at", desc=True)
        .limit(limit)
        .execute()
    )
    return _rows(result)


def _format_rule_threshold(value: Any) -> str:
    try:
        numeric = float(value)
    except Exception:
        return str(value)
    if abs(numeric) >= 100:
        return f"{numeric:.2f}"
    if abs(numeric) >= 10:
        return f"{numeric:.3f}"
    return f"{numeric:.4f}".rstrip("0").rstrip(".")


def _format_rule_definition(rule_definition: Any) -> str:
    if not isinstance(rule_definition, list):
        return str(rule_definition or "")
    parts: List[str] = []
    for item in rule_definition:
        if not isinstance(item, dict):
            continue
        indicator = str(item.get("indicator") or "condition")
        operator = str(item.get("operator") or "")
        threshold = _format_rule_threshold(item.get("threshold"))
        parts.append(f"{indicator} {operator} {threshold}".strip())
    return " AND ".join(parts)


def _load_technical_batch_rows(client, run_id: str, symbol: str, direction: str, limit: int, *, preferred_only: bool) -> List[Dict[str, Any]]:
    preferred_lookforward = 5
    preferred_target = 0.3
    preferred_stop = 0.3
    new_select = "profile_key,timeframe,rule_key,rule_definition,occurrences,wins,losses,win_rate,profit_factor,expectancy,avg_forward_return,target_move_pct,stop_move_pct,lookforward_candles,insufficient_data,rank,walk_forward_splits,walk_forward_passes,validation_occurrences,validation_wins,validation_win_rate,validation_expectancy"
    legacy_select = "timeframe,rule_key,rule_definition,occurrences,wins,losses,win_rate,profit_factor,expectancy,avg_forward_return,target_move_pct,stop_move_pct,lookforward_candles,insufficient_data,rank"

    def _query(select_columns: str) -> Dict[str, Any]:
        query = (
            client.table("technical_permutation_batch_results")
            .select(select_columns)
            .eq("run_id", run_id)
            .eq("symbol", symbol)
            .eq("direction", direction)
        )
        if preferred_only:
            query = (
                query
                .eq("lookforward_candles", preferred_lookforward)
                .eq("target_move_pct", preferred_target)
                .eq("stop_move_pct", preferred_stop)
            )
        return query.limit(limit).execute()

    primary = _query(new_select)
    if not primary.get("error"):
        return _rows(primary)

    fallback = _query(legacy_select)
    rows = _rows(fallback)
    for row in rows:
        row.setdefault(
            "profile_key",
            _build_profile_key(
                int(row.get("lookforward_candles") or preferred_lookforward),
                float(row.get("target_move_pct") or preferred_target),
                float(row.get("stop_move_pct") or preferred_stop),
                0,
            ),
        )
        row.setdefault("walk_forward_splits", 0)
        row.setdefault("walk_forward_passes", 0)
        row.setdefault("validation_occurrences", int(row.get("occurrences") or 0))
        row.setdefault("validation_wins", int(row.get("wins") or 0))
        row.setdefault("validation_win_rate", float(row.get("win_rate") or 0.0))
        row.setdefault("validation_expectancy", float(row.get("expectancy") or 0.0))
    return rows


def get_latest_model_batch_results(symbol: str, direction: str, limit: int = 150) -> Dict[str, Any]:
    client = get_supabase_client()
    if not client:
        return {"error": "No database connection"}

    normalized_symbol = _normalize_symbol(symbol)
    normalized_direction = (direction or "BUY").upper().strip()
    runs = _load_completed_runs(client)

    for run in runs:
        run_id = run.get("id")
        if not run_id:
            continue
        rows = _rows(
            client.table("model_permutation_batch_results")
            .select("combination,total_signals,wins,losses,win_rate,profit_factor,expectancy,avg_member_alignment,unanimous_win_rate,lookback_days,cluster_window_minutes,insufficient_data,rank")
            .eq("run_id", run_id)
            .eq("symbol", normalized_symbol)
            .eq("direction", normalized_direction)
            .order("rank")
            .limit(limit)
            .execute()
        )
        if not rows:
            continue

        first_row = rows[0]
        return {
            "symbol": normalized_symbol,
            "direction": normalized_direction,
            "source": "batch",
            "batch_run_id": run_id,
            "generated_at": run.get("completed_at") or run.get("started_at"),
            "lookback_days_used": int(first_row.get("lookback_days") or 0),
            "cluster_window_minutes": int(first_row.get("cluster_window_minutes") or 0),
            "results": [
                {
                    "combination": row.get("combination"),
                    "symbol": normalized_symbol,
                    "direction": normalized_direction,
                    "total_signals": int(row.get("total_signals") or 0),
                    "wins": int(row.get("wins") or 0),
                    "losses": int(row.get("losses") or 0),
                    "win_rate": float(row.get("win_rate") or 0.0),
                    "profit_factor": float(row.get("profit_factor") or 0.0),
                    "expectancy": float(row.get("expectancy") or 0.0),
                    "avg_member_alignment": float(row.get("avg_member_alignment") or 0.0),
                    "unanimous_win_rate": float(row.get("unanimous_win_rate") or 0.0),
                    "insufficient_data": bool(row.get("insufficient_data", False)),
                }
                for row in rows
            ],
        }

    return {"error": f"No completed model batch results for {normalized_symbol} {normalized_direction}"}


def get_latest_technical_batch_results(symbol: str, direction: str, limit: int = 150) -> Dict[str, Any]:
    client = get_supabase_client()
    if not client:
        return {"error": "No database connection"}

    normalized_symbol = _normalize_symbol(symbol)
    normalized_direction = (direction or "BUY").upper().strip()
    runs = _load_completed_runs(client)

    for run in runs:
        run_id = run.get("id")
        if not run_id:
            continue
        preferred_rows = _load_technical_batch_rows(
            client,
            run_id,
            normalized_symbol,
            normalized_direction,
            limit * 6,
            preferred_only=True,
        )
        rows = preferred_rows
        if not rows:
            rows = _load_technical_batch_rows(
                client,
                run_id,
                normalized_symbol,
                normalized_direction,
                limit * 6,
                preferred_only=False,
            )
        if not rows:
            continue

        rows.sort(key=lambda row: (-int(row.get("walk_forward_splits") or 0), int(row.get("rank") or 999999)))
        selected_profile_key = rows[0].get("profile_key")
        filtered_rows = [row for row in rows if row.get("profile_key") == selected_profile_key][:limit]
        first_row = filtered_rows[0]
        return {
            "symbol": normalized_symbol,
            "direction": normalized_direction,
            "source": "batch",
            "batch_run_id": run_id,
            "generated_at": run.get("completed_at") or run.get("started_at"),
            "target_move_pct": float(first_row.get("target_move_pct") or 0.0),
            "lookforward_candles": int(first_row.get("lookforward_candles") or 0),
            "stop_move_pct": float(first_row.get("stop_move_pct") or 0.0),
            "walk_forward_splits": int(first_row.get("walk_forward_splits") or 0),
            "profile_key": selected_profile_key,
            "results": [
                {
                    "indicator_combo": _format_rule_definition(row.get("rule_definition")) or str(row.get("rule_key") or ""),
                    "symbol": normalized_symbol,
                    "direction": normalized_direction,
                    "timeframe": row.get("timeframe"),
                    "occurrences": int(row.get("occurrences") or 0),
                    "wins": int(row.get("wins") or 0),
                    "losses": int(row.get("losses") or 0),
                    "win_rate": float(row.get("win_rate") or 0.0),
                    "profit_factor": float(row.get("profit_factor") or 0.0),
                    "expectancy": float(row.get("expectancy") or 0.0),
                    "avg_forward_return": float(row.get("avg_forward_return") or 0.0),
                    "validation_occurrences": int(row.get("validation_occurrences") or 0),
                    "validation_wins": int(row.get("validation_wins") or 0),
                    "validation_win_rate": float(row.get("validation_win_rate") or 0.0),
                    "validation_expectancy": float(row.get("validation_expectancy") or 0.0),
                    "walk_forward_splits": int(row.get("walk_forward_splits") or 0),
                    "walk_forward_passes": int(row.get("walk_forward_passes") or 0),
                    "insufficient_data": bool(row.get("insufficient_data", False)),
                }
                for row in filtered_rows
            ],
        }

    return {"error": f"No completed technical batch results for {normalized_symbol} {normalized_direction}"}


async def run_permutation_batch(config: Optional[PermutationBatchConfig] = None) -> Dict[str, Any]:
    config = config or PermutationBatchConfig()
    if not is_db_available():
        return {"success": False, "error": "Database not available"}
    client = get_supabase_client()
    if not client:
        return {"success": False, "error": "No database connection"}

    symbols = [_normalize_symbol(symbol) for symbol in config.symbols]
    lookforward_grid = _resolve_int_grid(config.lookforward_grid, config.lookforward_candles)
    target_move_grid = _resolve_float_grid(config.target_move_grid, config.target_move_pct)
    stop_move_grid = _resolve_float_grid(config.stop_move_grid, config.stop_move_pct)
    run_id = _insert_run(client, "full", config)
    summary: Dict[str, Any] = {
        "run_id": run_id,
        "dry_run": config.dry_run,
        "model_contexts": 0,
        "technical_contexts": 0,
        "model_rows": 0,
        "technical_rows": 0,
        "technical_resampled": [],
        "technical_skipped": [],
    }

    try:
        model_rows_to_write: List[Dict[str, Any]] = []
        for symbol in symbols:
            for direction in config.directions:
                model_result = await analyze_model_permutations(
                    symbol=symbol,
                    direction=direction,
                    min_occurrences=config.model_min_occurrences,
                    lookback_days=config.model_lookback_days,
                    cluster_window_minutes=config.cluster_window_minutes,
                )
                if model_result.get("error"):
                    continue
                summary["model_contexts"] += 1
                for rank, row in enumerate(model_result.get("results", []), start=1):
                    model_rows_to_write.append({
                        "run_id": run_id,
                        "symbol": symbol,
                        "direction": direction,
                        "combination": row.get("combination"),
                        "total_signals": int(row.get("total_signals", 0) or 0),
                        "wins": int(row.get("wins", 0) or 0),
                        "losses": int(row.get("losses", 0) or 0),
                        "win_rate": float(row.get("win_rate", 0) or 0),
                        "profit_factor": float(row.get("profit_factor", 0) or 0),
                        "expectancy": float(row.get("expectancy", 0) or 0),
                        "avg_member_alignment": float(row.get("avg_member_alignment", 0) or 0),
                        "unanimous_win_rate": float(row.get("unanimous_win_rate", 0) or 0),
                        "lookback_days": int(model_result.get("lookback_days_used", config.model_lookback_days) or config.model_lookback_days),
                        "cluster_window_minutes": int(model_result.get("cluster_window_minutes", config.cluster_window_minutes) or config.cluster_window_minutes),
                        "insufficient_data": bool(row.get("insufficient_data", False)),
                        "rank": rank,
                    })
        summary["model_rows"] = len(model_rows_to_write)
        if not config.dry_run:
            _upsert_rows(client, "model_permutation_batch_results", model_rows_to_write, "run_id,symbol,direction,combination")

        technical_rows_to_write: List[Dict[str, Any]] = []
        for symbol in symbols:
            for timeframe in config.technical_timeframes:
                candles, resampled_from = await asyncio.to_thread(
                    _load_technical_candles,
                    symbol,
                    timeframe,
                    config.technical_candle_limit,
                    config.resample_missing_timeframes,
                )
                if resampled_from:
                    summary["technical_resampled"].append({"symbol": symbol, "timeframe": timeframe, "source_timeframe": resampled_from, "candles": len(candles)})
                if len(candles) < max(160, config.technical_min_occurrences * 3):
                    summary["technical_skipped"].append({"symbol": symbol, "timeframe": timeframe, "reason": "not_enough_candles", "candles": len(candles)})
                    continue
                prepared_df = await asyncio.to_thread(_prepare_technical_dataframe, candles)
                if prepared_df.empty or len(prepared_df) < max(140, config.technical_min_occurrences * 2):
                    summary["technical_skipped"].append({"symbol": symbol, "timeframe": timeframe, "reason": "invalid_dataframe", "candles": len(prepared_df)})
                    continue
                for direction in config.directions:
                    for lookforward_candles in lookforward_grid:
                        for target_move_pct in target_move_grid:
                            for stop_move_pct in stop_move_grid:
                                labeled_df = await asyncio.to_thread(
                                    _label_outcomes,
                                    prepared_df,
                                    direction,
                                    lookforward_candles,
                                    target_move_pct,
                                    stop_move_pct,
                                )
                                if labeled_df.empty or len(labeled_df) < config.technical_min_occurrences:
                                    summary["technical_skipped"].append({
                                        "symbol": symbol,
                                        "timeframe": timeframe,
                                        "direction": direction,
                                        "lookforward_candles": lookforward_candles,
                                        "target_move_pct": target_move_pct,
                                        "stop_move_pct": stop_move_pct,
                                        "reason": "not_enough_labeled_rows",
                                        "rows": len(labeled_df),
                                    })
                                    continue

                                if config.walk_forward_splits > 0:
                                    combo_rows = await asyncio.to_thread(
                                        _search_walk_forward_combinations,
                                        labeled_df,
                                        config,
                                    )
                                else:
                                    atomic_rules = await asyncio.to_thread(
                                        _build_atomic_rules,
                                        labeled_df,
                                        config.technical_min_occurrences,
                                        config.quantiles,
                                        config.top_thresholds_per_indicator,
                                        config.max_atomic_rules,
                                    )
                                    if len(atomic_rules) < 2:
                                        summary["technical_skipped"].append({
                                            "symbol": symbol,
                                            "timeframe": timeframe,
                                            "direction": direction,
                                            "lookforward_candles": lookforward_candles,
                                            "target_move_pct": target_move_pct,
                                            "stop_move_pct": stop_move_pct,
                                            "reason": "not_enough_atomic_rules",
                                            "rules": len(atomic_rules),
                                        })
                                        continue
                                    combo_rows = await asyncio.to_thread(
                                        _search_rule_combinations,
                                        labeled_df,
                                        atomic_rules,
                                        config.technical_min_occurrences,
                                        config.max_combination_size,
                                    )

                                if not combo_rows:
                                    summary["technical_skipped"].append({
                                        "symbol": symbol,
                                        "timeframe": timeframe,
                                        "direction": direction,
                                        "lookforward_candles": lookforward_candles,
                                        "target_move_pct": target_move_pct,
                                        "stop_move_pct": stop_move_pct,
                                        "reason": "no_combo_rows",
                                    })
                                    continue

                                profile_key = _build_profile_key(
                                    lookforward_candles,
                                    target_move_pct,
                                    stop_move_pct,
                                    config.walk_forward_splits,
                                )
                                summary["technical_contexts"] += 1
                                for rank, row in enumerate(combo_rows[: config.top_results_per_context], start=1):
                                    technical_rows_to_write.append({
                                        "run_id": run_id,
                                        "symbol": symbol,
                                        "direction": direction,
                                        "timeframe": timeframe,
                                        "profile_key": profile_key,
                                        "rule_key": row["rule_key"],
                                        "combination_size": int(row["combination_size"]),
                                        "rule_definition": _json_ready(row["rule_definition"]),
                                        "occurrences": int(row["occurrences"]),
                                        "wins": int(row["wins"]),
                                        "losses": int(row["losses"]),
                                        "win_rate": float(row["win_rate"]),
                                        "profit_factor": float(row["profit_factor"]),
                                        "expectancy": float(row["expectancy"]),
                                        "avg_forward_return": float(row["avg_forward_return"]),
                                        "target_move_pct": float(target_move_pct),
                                        "stop_move_pct": float(stop_move_pct),
                                        "lookforward_candles": int(lookforward_candles),
                                        "threshold_quantiles": _json_ready(row["threshold_quantiles"]),
                                        "train_occurrences": int(row.get("train_occurrences", 0) or 0),
                                        "train_wins": int(row.get("train_wins", 0) or 0),
                                        "train_win_rate": float(row.get("train_win_rate", row["win_rate"]) or 0.0),
                                        "train_expectancy": float(row.get("train_expectancy", row["expectancy"]) or 0.0),
                                        "validation_occurrences": int(row.get("validation_occurrences", row["occurrences"]) or 0),
                                        "validation_wins": int(row.get("validation_wins", row["wins"]) or 0),
                                        "validation_win_rate": float(row.get("validation_win_rate", row["win_rate"]) or 0.0),
                                        "validation_expectancy": float(row.get("validation_expectancy", row["expectancy"]) or 0.0),
                                        "walk_forward_splits": int(row.get("walk_forward_splits", config.walk_forward_splits) or 0),
                                        "walk_forward_passes": int(row.get("walk_forward_passes", 0) or 0),
                                        "walk_forward_folds": int(row.get("walk_forward_folds", 0) or 0),
                                        "insufficient_data": int(row["occurrences"]) < config.technical_min_occurrences,
                                        "rank": rank,
                                    })
        summary["technical_rows"] = len(technical_rows_to_write)
        if not config.dry_run:
            _upsert_rows(client, "technical_permutation_batch_results", technical_rows_to_write, "run_id,symbol,direction,timeframe,profile_key,rule_key")

        _finish_run(client, run_id, status="completed", summary=summary)
        return {"success": True, **summary}
    except Exception as exc:
        logger.error(f"[PermutationBatch] run failed: {exc}", exc_info=True)
        _finish_run(client, run_id, status="failed", summary=summary, error=str(exc))
        return {"success": False, **summary, "error": str(exc)}
