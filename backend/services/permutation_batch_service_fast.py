"""Fast permutation batch service - optimized for 1-2 day completion.

KEY OPTIMIZATIONS vs original:
1. Smaller grids: lookforward [5,8,13] vs [3,5,8,13,21,34]
2. Smaller target/stop grids: [0.3,0.5,0.8] vs 8 values
3. Fewer atomic rules: 24 vs 60-72
4. Lower combination size: 4 vs 6
5. Fewer top results: 300 vs 1500-2500
6. Fewer walk-forward splits: 2 vs 4-5
7. Fewer walk-forward candidates: 15 vs 50
8. Progress tracking with ETA estimation
9. Context-level periodic flush (every N contexts)
10. Aggressive early pruning in combination search
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple
from uuid import uuid4

import numpy as np
import pandas as pd

from database.supabase_client import get_supabase_client, is_db_available
from services.candle_cache_store import load_candles
from services.permutation_analysis_service import analyze_model_permutations

logger = logging.getLogger(__name__)

# === QUALITY-FIRST DEFAULTS FOR FAST RUN ===
# Target: 1-2 days with preserved result quality (not just speed)
DEFAULT_SYMBOLS = ("NDX.INDX", "XAUUSD", "GDAXI.INDX", "USOIL.FOREX")
DEFAULT_DIRECTIONS = ("BUY", "SELL")
DEFAULT_TECHNICAL_TIMEFRAMES = ("5m", "30m", "1h", "eod")

# Quantiles - still reduced but covering key percentiles
DEFAULT_QUANTILES_FAST = (
    0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 
    0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95
)

# Quality-first grids - balanced between coverage and speed
# BALANCED preset defaults (can be overridden per preset)
DEFAULT_LOOKFORWARD_GRID_BALANCED = (5, 8, 13, 21)        # 4 values (vs 5-6 in original)
DEFAULT_TARGET_GRID_BALANCED = (0.003, 0.005, 0.008, 0.012, 0.02)
DEFAULT_STOP_GRID_BALANCED = (0.002, 0.003, 0.005, 0.008, 0.012)

# QUALITY preset defaults - more comprehensive
DEFAULT_LOOKFORWARD_GRID_QUALITY = (3, 5, 8, 13, 21)      # 5 values
DEFAULT_TARGET_GRID_QUALITY = (0.002, 0.003, 0.004, 0.005, 0.008, 0.012, 0.016, 0.02)
DEFAULT_STOP_GRID_QUALITY = (0.0015, 0.002, 0.003, 0.004, 0.005, 0.008, 0.012, 0.016)

# Backward compatible defaults (used if no preset specified)
DEFAULT_LOOKFORWARD_GRID_FAST = DEFAULT_LOOKFORWARD_GRID_BALANCED
DEFAULT_TARGET_GRID_FAST = DEFAULT_TARGET_GRID_BALANCED
DEFAULT_STOP_GRID_FAST = DEFAULT_STOP_GRID_BALANCED

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
class PermutationBatchConfigFast:
    """Quality-first config for fast completion (target: 1-2 days).
    
    PRESETS:
    - balanced: 1-2 days, good quality, recommended default
    - quality: 2-3 days, higher quality, more comprehensive
    """
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
    quantiles: Sequence[float] = DEFAULT_QUANTILES_FAST
    top_thresholds_per_indicator: int = 5           # Balanced: 5 (vs original 6)
    max_atomic_rules: int = 32                       # Balanced: 32 (vs original 48)
    max_combination_size: int = 5                     # Balanced: 5 (vs original 6)
    top_results_per_context: int = 500               # Balanced: 500 (vs original 750)
    resample_missing_timeframes: bool = True
    dry_run: bool = False
    lookforward_grid: Sequence[int] = DEFAULT_LOOKFORWARD_GRID_FAST
    target_move_grid: Sequence[float] = DEFAULT_TARGET_GRID_FAST
    stop_move_grid: Sequence[float] = DEFAULT_STOP_GRID_FAST
    walk_forward_splits: int = 3                     # Balanced: 3 (vs original 4)
    walk_forward_test_size: int = 80
    walk_forward_min_train_size: int = 250
    walk_forward_top_candidates: int = 25            # Balanced: 25 (vs original 50)
    
    # Quality-first pruning thresholds (softer than aggressive)
    min_atomic_rule_win_rate: float = 0.40           # Softer: 40% (was 45%)
    min_combo_win_rate: float = 0.45                 # Softer: 45% (was 50%)
    
    # Progress tracking settings
    progress_log_interval: int = 10                  # Log every N contexts
    checkpoint_interval: int = 50                    # Write checkpoint every N contexts
    flush_interval: int = 20                        # Flush to DB every N contexts
    skip_model_stage: bool = False
    reuse_model_run_id: Optional[str] = None
    resume_run_id: Optional[str] = None
    allow_model_reuse_mismatch: bool = False


@dataclass
class ProgressState:
    """Track progress for ETA estimation."""
    run_id: str
    total_model_contexts: int = 0
    completed_model_contexts: int = 0
    total_technical_contexts: int = 0
    completed_technical_contexts: int = 0
    phase: str = "initializing"  # initializing, model, technical, walk_forward, completed, failed
    current_symbol: Optional[str] = None
    current_timeframe: Optional[str] = None
    current_direction: Optional[str] = None
    start_time: Optional[datetime] = None
    last_heartbeat: Optional[datetime] = None
    model_rows_written: int = 0
    technical_rows_written: int = 0
    contexts_since_last_flush: int = 0
    completed_model_context_keys: Set[str] = field(default_factory=set)
    completed_technical_context_keys: Set[str] = field(default_factory=set)

    def register_model_context(self, context_key: str) -> bool:
        if context_key in self.completed_model_context_keys:
            return False
        self.completed_model_context_keys.add(context_key)
        self.completed_model_contexts = len(self.completed_model_context_keys)
        return True

    def register_technical_context(self, context_key: str) -> bool:
        if context_key in self.completed_technical_context_keys:
            return False
        self.completed_technical_context_keys.add(context_key)
        self.completed_technical_contexts = len(self.completed_technical_context_keys)
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "total_model_contexts": self.total_model_contexts,
            "completed_model_contexts": self.completed_model_contexts,
            "total_technical_contexts": self.total_technical_contexts,
            "completed_technical_contexts": self.completed_technical_contexts,
            "phase": self.phase,
            "current_symbol": self.current_symbol,
            "current_timeframe": self.current_timeframe,
            "current_direction": self.current_direction,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            "model_rows_written": self.model_rows_written,
            "technical_rows_written": self.technical_rows_written,
            "completed_model_context_keys": sorted(self.completed_model_context_keys),
            "completed_technical_context_keys": sorted(self.completed_technical_context_keys),
            "elapsed_seconds": self.elapsed_seconds(),
            "model_pct": self.model_progress_pct(),
            "technical_pct": self.technical_progress_pct(),
            "eta_seconds": self.eta_seconds(),
        }
    
    def elapsed_seconds(self) -> float:
        if not self.start_time:
            return 0.0
        return (datetime.now(timezone.utc) - self.start_time).total_seconds()
    
    def model_progress_pct(self) -> float:
        if self.total_model_contexts == 0:
            return 0.0
        return 100.0 * self.completed_model_contexts / self.total_model_contexts
    
    def technical_progress_pct(self) -> float:
        if self.total_technical_contexts == 0:
            return 0.0
        return 100.0 * self.completed_technical_contexts / self.total_technical_contexts
    
    def overall_progress_pct(self) -> float:
        total = self.total_model_contexts + self.total_technical_contexts
        completed = self.completed_model_contexts + self.completed_technical_contexts
        if total == 0:
            return 0.0
        return 100.0 * completed / total
    
    def eta_seconds(self) -> Optional[float]:
        """Estimate remaining seconds based on current progress rate."""
        elapsed = self.elapsed_seconds()
        if elapsed < 30:  # Not enough data yet
            return None
        
        completed = self.completed_model_contexts + self.completed_technical_contexts
        total = self.total_model_contexts + self.total_technical_contexts
        
        if completed == 0 or total == 0:
            return None
        
        rate = completed / elapsed  # contexts per second
        remaining = total - completed
        return remaining / rate if rate > 0 else None
    
    def format_eta(self) -> str:
        eta = self.eta_seconds()
        if eta is None:
            return "calculating..."
        
        hours = int(eta // 3600)
        minutes = int((eta % 3600) // 60)
        
        if hours > 48:
            return f"~{hours // 24}d {(hours % 24)}h"
        elif hours > 0:
            return f"~{hours}h {minutes}m"
        else:
            return f"~{minutes}m"


def _utc_iso(value: Optional[datetime] = None) -> str:
    dt = value or datetime.now(timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        normalized = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
    except Exception:
        return None


def _normalize_symbol(symbol: str) -> str:
    raw = (symbol or "").upper().strip()
    return SYMBOL_ALIASES.get(raw, raw)


def _normalize_direction(direction: str) -> str:
    return (direction or "").upper().strip()


def _resolve_int_grid(grid: Sequence[int], default: int) -> Sequence[int]:
    return grid if grid else (default,)


def _resolve_float_grid(grid: Sequence[float], default: float) -> Sequence[float]:
    return grid if grid else (default,)


def _json_ready(value: Any) -> Any:
    if isinstance(value, (list, tuple)):
        return [_json_ready(v) for v in value]
    if isinstance(value, dict):
        return {k: _json_ready(v) for k, v in value.items()}
    if isinstance(value, (np.integer, np.floating)):
        return float(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    return value


def _rows(result: Dict[str, Any]) -> List[Dict[str, Any]]:
    if not result or not isinstance(result, dict):
        return []
    if result.get("error"):
        return []
    data = result.get("data")
    if isinstance(data, list):
        return data
    return []


def _profile_float_fragment(value: float) -> str:
    return f"{float(value):.4f}".rstrip("0").rstrip(".").replace("-", "n").replace(".", "p")


def _build_profile_key(lookforward: int, target: float, stop: float, splits: int) -> str:
    return (
        f"lf{int(lookforward)}_"
        f"tp{_profile_float_fragment(target)}_"
        f"sl{_profile_float_fragment(stop)}_"
        f"wf{int(splits)}"
    )


def _build_model_context_key(symbol: str, direction: str) -> str:
    return f"{_normalize_symbol(symbol)}|{_normalize_direction(direction)}"


def _build_technical_context_key(symbol: str, timeframe: str, direction: str, profile_key: str) -> str:
    return f"{_normalize_symbol(symbol)}|{timeframe}|{_normalize_direction(direction)}|{profile_key}"


def _build_technical_context_keys_for_timeframe(
    symbol: str,
    timeframe: str,
    directions: Sequence[str],
    lookforward_grid: Sequence[int],
    target_move_grid: Sequence[float],
    stop_move_grid: Sequence[float],
    walk_forward_splits: int,
) -> Set[str]:
    context_keys: Set[str] = set()
    for direction in directions:
        for lookforward_candles in lookforward_grid:
            for target_move_pct in target_move_grid:
                for stop_move_pct in stop_move_grid:
                    profile_key = _build_profile_key(lookforward_candles, target_move_pct, stop_move_pct, walk_forward_splits)
                    context_keys.add(_build_technical_context_key(symbol, timeframe, direction, profile_key))
    return context_keys


def _checkpoint_path(run_id: str) -> Path:
    checkpoint_dir = Path("/tmp/permutation_checkpoints")
    checkpoint_dir.mkdir(exist_ok=True)
    return checkpoint_dir / f"permutation_progress_{run_id}.json"


def _load_checkpoint(run_id: str) -> Dict[str, Any]:
    checkpoint_path = _checkpoint_path(run_id)
    if not checkpoint_path.exists():
        return {}
    try:
        with open(checkpoint_path) as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception as exc:
        logger.warning(f"[PermutationBatchFast] Failed to load checkpoint {checkpoint_path}: {exc}")
        return {}


def _get_run_record(client, run_id: str) -> Dict[str, Any]:
    result = client.table("permutation_batch_runs").select("id,status,batch_kind,started_at,completed_at,error,parameters,summary").eq("id", run_id).limit(1).execute()
    rows = _rows(result)
    return rows[0] if rows else {}


def _fetch_existing_model_context_keys(client, run_id: str) -> Set[str]:
    rows = _rows(
        client.table("model_permutation_batch_results")
        .select("symbol,direction")
        .eq("run_id", run_id)
        .eq("rank", 1)
        .execute()
    )
    return {
        _build_model_context_key(str(row.get("symbol") or ""), str(row.get("direction") or ""))
        for row in rows
    }


def _fetch_existing_technical_context_keys(client, run_id: str) -> Set[str]:
    rows = _rows(
        client.table("technical_permutation_batch_results")
        .select("symbol,direction,timeframe,profile_key")
        .eq("run_id", run_id)
        .eq("rank", 1)
        .execute()
    )
    return {
        _build_technical_context_key(
            str(row.get("symbol") or ""),
            str(row.get("timeframe") or ""),
            str(row.get("direction") or ""),
            str(row.get("profile_key") or ""),
        )
        for row in rows
    }


def _fetch_row_count(client, table: str, run_id: str) -> int:
    rows = _rows(client.table(table).select("run_id").eq("run_id", run_id).execute())
    return len(rows)


def _sequence_from_run_record(run_record: Dict[str, Any], key: str) -> List[str]:
    params = run_record.get("parameters") or {}
    values = params.get(key)
    if isinstance(values, list):
        return [str(value) for value in values]
    legacy_values = run_record.get(key)
    if isinstance(legacy_values, list):
        return [str(value) for value in legacy_values]
    return []


def _validate_model_reuse(client, source_run_id: str, config: PermutationBatchConfigFast, symbols: Sequence[str], directions: Sequence[str]) -> Tuple[Dict[str, Any], List[str]]:
    run_record = _get_run_record(client, source_run_id)
    if not run_record:
        raise RuntimeError(f"[PermutationBatchFast] reuse_model_run_id not found: {source_run_id}")

    params = run_record.get("parameters") or {}
    source_symbols = sorted({_normalize_symbol(value) for value in _sequence_from_run_record(run_record, "symbols")})
    source_directions = sorted({_normalize_direction(value) for value in _sequence_from_run_record(run_record, "directions")})
    target_symbols = sorted({_normalize_symbol(value) for value in symbols})
    target_directions = sorted({_normalize_direction(value) for value in directions})

    mismatches: List[str] = []
    if source_symbols and source_symbols != target_symbols:
        mismatches.append(f"symbols source={source_symbols} target={target_symbols}")
    if source_directions and source_directions != target_directions:
        mismatches.append(f"directions source={source_directions} target={target_directions}")
    if int(params.get("model_lookback_days") or 0) != int(config.model_lookback_days):
        mismatches.append(
            f"model_lookback_days source={params.get('model_lookback_days')} target={config.model_lookback_days}"
        )
    if int(params.get("model_min_occurrences") or 0) != int(config.model_min_occurrences):
        mismatches.append(
            f"model_min_occurrences source={params.get('model_min_occurrences')} target={config.model_min_occurrences}"
        )
    if int(params.get("cluster_window_minutes") or 0) != int(config.cluster_window_minutes):
        mismatches.append(
            f"cluster_window_minutes source={params.get('cluster_window_minutes')} target={config.cluster_window_minutes}"
        )
    if mismatches and not config.allow_model_reuse_mismatch:
        raise RuntimeError(
            "[PermutationBatchFast] Model reuse blocked due to parameter mismatch: " + "; ".join(mismatches)
        )
    return run_record, mismatches


def _copy_model_rows_from_run(client, source_run_id: str, target_run_id: str) -> Tuple[int, Set[str]]:
    rows = _rows(
        client.table("model_permutation_batch_results")
        .select("symbol,direction,combination,total_signals,wins,losses,win_rate,profit_factor,expectancy,avg_member_alignment,unanimous_win_rate,lookback_days,cluster_window_minutes,insufficient_data,rank")
        .eq("run_id", source_run_id)
        .execute()
    )
    if not rows:
        return 0, set()

    copied_rows: List[Dict[str, Any]] = []
    context_keys: Set[str] = set()
    for row in rows:
        copied = dict(row)
        copied["run_id"] = target_run_id
        copied_rows.append(copied)
        context_keys.add(_build_model_context_key(str(row.get("symbol") or ""), str(row.get("direction") or "")))

    _upsert_rows(client, "model_permutation_batch_results", copied_rows, "run_id,symbol,direction,combination")
    return len(copied_rows), context_keys


def _restore_progress_state(
    run_id: str,
    total_model_contexts: int,
    total_technical_contexts: int,
    checkpoint_data: Dict[str, Any],
    existing_model_context_keys: Set[str],
    existing_technical_context_keys: Set[str],
    existing_model_row_count: int,
    existing_technical_row_count: int,
) -> ProgressState:
    progress = ProgressState(
        run_id=run_id,
        total_model_contexts=total_model_contexts,
        total_technical_contexts=total_technical_contexts,
        phase=str(checkpoint_data.get("phase") or "initializing"),
        current_symbol=checkpoint_data.get("current_symbol"),
        current_timeframe=checkpoint_data.get("current_timeframe"),
        current_direction=checkpoint_data.get("current_direction"),
        start_time=_parse_datetime(checkpoint_data.get("start_time")) or datetime.now(timezone.utc),
        last_heartbeat=_parse_datetime(checkpoint_data.get("last_heartbeat")) or datetime.now(timezone.utc),
        model_rows_written=max(int(checkpoint_data.get("model_rows_written") or 0), existing_model_row_count),
        technical_rows_written=max(int(checkpoint_data.get("technical_rows_written") or 0), existing_technical_row_count),
        contexts_since_last_flush=0,
        completed_model_context_keys=set(checkpoint_data.get("completed_model_context_keys") or []),
        completed_technical_context_keys=set(checkpoint_data.get("completed_technical_context_keys") or []),
    )
    progress.completed_model_context_keys.update(existing_model_context_keys)
    progress.completed_technical_context_keys.update(existing_technical_context_keys)
    progress.completed_model_contexts = len(progress.completed_model_context_keys)
    progress.completed_technical_contexts = len(progress.completed_technical_context_keys)
    return progress


def _insert_run(client, batch_kind: str, config: PermutationBatchConfigFast) -> str:
    run_id = str(uuid4())
    record = {
        "id": run_id,
        "batch_kind": batch_kind,
        "status": "running",
        "started_at": _utc_iso(),
        "parameters": {
            "symbols": list(config.symbols),
            "directions": list(config.directions),
            "technical_timeframes": list(config.technical_timeframes),
            "model_lookback_days": config.model_lookback_days,
            "model_min_occurrences": config.model_min_occurrences,
            "cluster_window_minutes": config.cluster_window_minutes,
            "technical_min_occurrences": config.technical_min_occurrences,
            "technical_candle_limit": config.technical_candle_limit,
            "lookforward_grid": list(config.lookforward_grid),
            "target_move_grid": list(config.target_move_grid),
            "stop_move_grid": list(config.stop_move_grid),
            "max_atomic_rules": config.max_atomic_rules,
            "max_combination_size": config.max_combination_size,
            "top_results_per_context": config.top_results_per_context,
            "walk_forward_splits": config.walk_forward_splits,
            "walk_forward_top_candidates": config.walk_forward_top_candidates,
            "skip_model_stage": config.skip_model_stage,
            "reuse_model_run_id": config.reuse_model_run_id,
            "resume_run_id": config.resume_run_id,
        },
        "summary": {},
    }
    result = client.table("permutation_batch_runs").insert(record)
    if result.get("error"):
        raise RuntimeError(f"[PermutationBatchFast] Failed to insert run record: {result['error']}")
    return run_id


def _update_run_progress(client, run_id: str, progress: Dict[str, Any]) -> None:
    """Update run with progress info."""
    result = client.table("permutation_batch_runs").eq("id", run_id).update({
        "summary": progress,
    })
    if result.get("error"):
        logger.warning(f"[PermutationBatchFast] Failed to update progress: {result['error']}")


def _finish_run(client, run_id: str, status: str, summary: Dict[str, Any], error: Optional[str] = None) -> None:
    payload: Dict[str, Any] = {"status": status, "completed_at": _utc_iso(), "summary": summary}
    if error:
        payload["error"] = error
    result = client.table("permutation_batch_runs").eq("id", run_id).update(payload)
    if result.get("error"):
        logger.warning(f"[PermutationBatchFast] Failed to finish run: {result['error']}")


def _upsert_rows(client, table: str, rows: List[Dict[str, Any]], conflict_cols: str) -> None:
    if not rows:
        return
    BATCH_SIZE = 500
    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i : i + BATCH_SIZE]
        result = client.table(table).upsert(batch, on_conflict=conflict_cols)
        if result.get("error"):
            raise RuntimeError(f"[PermutationBatchFast] Upsert failed for {table}: {result['error']}")


def _write_checkpoint(progress: ProgressState, config: PermutationBatchConfigFast) -> None:
    """Write progress checkpoint to JSON file."""
    try:
        checkpoint_path = _checkpoint_path(progress.run_id)
        
        data = progress.to_dict()
        data["config"] = {
            "symbols": list(config.symbols),
            "directions": list(config.directions),
            "timeframes": list(config.technical_timeframes),
            "lookforward_grid": list(config.lookforward_grid),
            "target_move_grid": list(config.target_move_grid),
            "stop_move_grid": list(config.stop_move_grid),
            "model_lookback_days": config.model_lookback_days,
            "model_min_occurrences": config.model_min_occurrences,
            "cluster_window_minutes": config.cluster_window_minutes,
            "skip_model_stage": config.skip_model_stage,
            "reuse_model_run_id": config.reuse_model_run_id,
            "resume_run_id": config.resume_run_id,
        }
        
        with open(checkpoint_path, "w") as f:
            json.dump(data, f, indent=2, default=str)
    except Exception as e:
        logger.warning(f"[PermutationBatchFast] Failed to write checkpoint: {e}")


def _persist_progress(client, progress: ProgressState, config: PermutationBatchConfigFast) -> None:
    progress.last_heartbeat = datetime.now(timezone.utc)
    _write_checkpoint(progress, config)
    if not config.dry_run:
        _update_run_progress(client, progress.run_id, progress.to_dict())


def _mark_run_running(client, run_id: str, progress: Dict[str, Any]) -> None:
    result = client.table("permutation_batch_runs").eq("id", run_id).update({
        "status": "running",
        "completed_at": None,
        "error": None,
        "summary": progress,
    })
    if result.get("error"):
        logger.warning(f"[PermutationBatchFast] Failed to mark run {run_id} as running: {result['error']}")


def _log_progress(progress: ProgressState, force: bool = False) -> None:
    """Log current progress with ETA."""
    overall_pct = progress.overall_progress_pct()
    model_pct = progress.model_progress_pct()
    tech_pct = progress.technical_progress_pct()
    eta = progress.format_eta()
    elapsed = progress.elapsed_seconds()
    
    logger.info(
        f"[PermutationBatchFast] Progress | "
        f"Overall: {overall_pct:.1f}% | "
        f"Model: {model_pct:.1f}% ({progress.completed_model_contexts}/{progress.total_model_contexts}) | "
        f"Technical: {tech_pct:.1f}% ({progress.completed_technical_contexts}/{progress.total_technical_contexts}) | "
        f"Phase: {progress.phase} | "
        f"Current: {progress.current_symbol} {progress.current_timeframe} {progress.current_direction} | "
        f"Elapsed: {elapsed/3600:.1f}h | ETA: {eta}"
    )


def _load_technical_candles(symbol: str, timeframe: str, limit: int, allow_resample: bool) -> Tuple[pd.DataFrame, Optional[str]]:
    """Load candles and convert to DataFrame with timeout protection."""
    import concurrent.futures
    import time
    
    def load_with_timeout():
        candles_list = load_candles(symbol, timeframe, limit)
        
        # Convert list to DataFrame if we have data
        if candles_list and len(candles_list) > 0:
            candles = pd.DataFrame(candles_list)
            # Set timestamp as index if available
            if 'candle_time' in candles.columns:
                candles['candle_time'] = pd.to_datetime(candles['candle_time'])
                candles.set_index('candle_time', inplace=True)
            elif 'timestamp' in candles.columns:
                candles['timestamp'] = pd.to_datetime(candles['timestamp'], unit='ms')
                candles.set_index('timestamp', inplace=True)
            return candles, None
        
        candles = pd.DataFrame()
        if not allow_resample:
            return candles, None
        for source_tf in RESAMPLE_SOURCES.get(timeframe, ()):
            source_candles_list = load_candles(symbol, source_tf, limit * 6)
            if source_candles_list and len(source_candles_list) > 0:
                try:
                    source_candles = pd.DataFrame(source_candles_list)
                    if 'candle_time' in source_candles.columns:
                        source_candles['candle_time'] = pd.to_datetime(source_candles['candle_time'])
                        source_candles.set_index('candle_time', inplace=True)
                    elif 'timestamp' in source_candles.columns:
                        source_candles['timestamp'] = pd.to_datetime(source_candles['timestamp'], unit='ms')
                        source_candles.set_index('timestamp', inplace=True)
                    resampled = source_candles.resample(TIMEFRAME_RULES[timeframe]).agg({
                        "open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum",
                    }).dropna()
                    if not resampled.empty:
                        return resampled, source_tf
                except Exception:
                    continue
        return candles, None
    
    # Run with 30 second timeout
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(load_with_timeout)
        try:
            return future.result(timeout=30)
        except concurrent.futures.TimeoutError:
            logger.warning(f"[CandleLoad] Timeout loading {symbol}/{timeframe}, returning empty DataFrame")
            return pd.DataFrame(), None


def _prepare_technical_dataframe(candles: pd.DataFrame) -> pd.DataFrame:
    """Prepare technical indicators using pandas/numpy (no TA-Lib required)."""
    print(f"[DEBUG _prepare_technical_dataframe] Input candles shape: {candles.shape}, columns: {list(candles.columns)}")
    
    df = candles.copy()
    if df.empty or "close" not in df.columns:
        print("[DEBUG _prepare_technical_dataframe] Empty DataFrame or missing 'close' column")
        return pd.DataFrame()
    
    close = df["close"].astype(float)
    
    # Convert to numeric
    required_base = ['open', 'high', 'low', 'close', 'volume']
    for col in required_base:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    close = df["close"]
    high = df["high"]
    low = df["low"]
    volume = df["volume"]
    
    # Price-based features (always create these)
    df["price_return_1"] = close.pct_change(1)
    df["price_return_3"] = close.pct_change(3)
    df["price_return_5"] = close.pct_change(5)
    
    # Candle features
    open_price = df["open"]
    body = close - open_price
    candle_range = high - low
    df["body_pct"] = body / candle_range.replace(0, np.nan)
    df["range_pct"] = candle_range / close
    df["upper_wick_pct"] = (high - close) / candle_range.replace(0, np.nan)
    df["lower_wick_pct"] = (close - low) / candle_range.replace(0, np.nan)
    
    # EMAs and distances (create even if they exist in input)
    df["ema20"] = close.ewm(span=20, adjust=False).mean()
    df["ema50"] = close.ewm(span=50, adjust=False).mean()
    df["ema200"] = close.ewm(span=200, adjust=False).mean()
    df["ema20_dist"] = (close - df["ema20"]) / df["ema20"]
    df["ema50_dist"] = (close - df["ema50"]) / df["ema50"]
    df["ema200_dist"] = (close - df["ema200"]) / df["ema200"]
    
    # RSI
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss.replace(0, np.nan)
    df["rsi_14"] = 100 - (100 / (1 + rs))
    df["rsi_delta"] = df["rsi_14"].diff(3)
    
    # MACD
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    df["macd_hist"] = ema12 - ema26
    df["macd_hist_delta"] = df["macd_hist"].diff()
    
    # ATR and ratios
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    atr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1).rolling(window=14).mean()
    df["atr"] = atr
    df["atr_ratio"] = atr / close
    
    # ADX
    plus_dm = high.diff()
    minus_dm = -low.diff()
    plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
    minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)
    plus_di = 100 * plus_dm.rolling(window=14).mean() / atr.replace(0, np.nan)
    minus_di = 100 * minus_dm.rolling(window=14).mean() / atr.replace(0, np.nan)
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di).replace(0, np.nan)
    df["adx"] = dx.rolling(window=14).mean()
    df["adx_delta"] = df["adx"].diff()
    
    # Bollinger Bands
    sma20 = close.rolling(window=20).mean()
    std20 = close.rolling(window=20).std()
    upper_band = sma20 + (std20 * 2)
    lower_band = sma20 - (std20 * 2)
    df["bb_position"] = (close - lower_band) / (upper_band - lower_band).replace(0, np.nan)
    
    # CCI
    tp = (high + low + close) / 3
    sma_tp = tp.rolling(window=20).mean()
    mean_dev = tp.rolling(window=20).apply(lambda x: np.abs(x - x.mean()).mean(), raw=True)
    df["cci_20"] = (tp - sma_tp) / (0.015 * mean_dev.replace(0, np.nan))
    
    # Stochastic
    lowest_low = low.rolling(window=14).min()
    highest_high = high.rolling(window=14).max()
    df["stoch_k"] = 100 * (close - lowest_low) / (highest_high - lowest_low).replace(0, np.nan)
    df["stoch_d"] = df["stoch_k"].rolling(window=3).mean()
    df["willr_14"] = -100 * (highest_high - close) / (highest_high - lowest_low).replace(0, np.nan)
    
    # Volume features
    vol_sma20 = volume.rolling(window=20).mean()
    df["volume_ratio"] = volume / vol_sma20.replace(0, np.nan)
    money_flow = ((high + low + close) / 3.0) * volume
    direction = close.diff()
    positive_flow = money_flow.where(direction > 0, 0.0)
    negative_flow = money_flow.where(direction < 0, 0.0).abs()
    positive_mf = positive_flow.rolling(window=14).sum()
    negative_mf = negative_flow.rolling(window=14).sum()
    money_ratio = positive_mf / negative_mf.replace(0, np.nan)
    df["mfi_14"] = 100 - (100 / (1 + money_ratio))
    df["force_index_13"] = (close.diff() * volume).ewm(span=13, adjust=False).mean()
    df["roc_10"] = close.pct_change(10)
    
    # Log created columns for debugging
    created_cols = [c for c in df.columns if c not in candles.columns]
    print(f"[DEBUG _prepare_technical_dataframe] Created {len(created_cols)} new columns: {created_cols}")
    print(f"[DEBUG _prepare_technical_dataframe] Output shape: {df.shape}")
    
    return df


def _label_outcomes(df: pd.DataFrame, direction: str, lookforward: int, target_move: float, stop_move: float) -> pd.DataFrame:
    """Label outcomes for each candle based on forward price movements."""
    print(f"[DEBUG _label_outcomes] Input shape: {df.shape}, lookforward: {lookforward}, target_move: {target_move}, stop_move: {stop_move}")
    normalized_direction = direction.upper().strip()
    if normalized_direction not in {"BUY", "SELL"}:
        return pd.DataFrame()
    
    work_df = df.reset_index(drop=True).copy()
    closes = pd.to_numeric(work_df["close"], errors="coerce")
    highs = pd.to_numeric(work_df["high"], errors="coerce")
    lows = pd.to_numeric(work_df["low"], errors="coerce")
    win_flags: List[Optional[bool]] = []
    loss_flags: List[Optional[bool]] = []
    realized_returns: List[Optional[float]] = []
    for index in range(len(work_df)):
        if index + lookforward >= len(work_df):
            win_flags.append(None)
            loss_flags.append(None)
            realized_returns.append(None)
            continue
        current_close = float(closes.iloc[index])
        realized: Optional[float] = None
        is_win = False
        for step in range(1, lookforward + 1):
            future_high = float(highs.iloc[index + step])
            future_low = float(lows.iloc[index + step])
            if normalized_direction == "BUY":
                target_level = current_close * (1.0 + target_move)
                stop_level = current_close * (1.0 - stop_move)
                if future_low <= stop_level:
                    realized = -stop_move
                    is_win = False
                    break
                if future_high >= target_level:
                    realized = target_move
                    is_win = True
                    break
            else:
                target_level = current_close * (1.0 - target_move)
                stop_level = current_close * (1.0 + stop_move)
                if future_high >= stop_level:
                    realized = -stop_move
                    is_win = False
                    break
                if future_low <= target_level:
                    realized = target_move
                    is_win = True
                    break
        if realized is None:
            final_close = float(closes.iloc[index + lookforward])
            move_pct = (final_close - current_close) / current_close
            realized = move_pct if normalized_direction == "BUY" else -move_pct
            is_win = realized > 0
        win_flags.append(is_win)
        loss_flags.append(not is_win)
        realized_returns.append(realized)
    labeled = work_df.copy()
    labeled["is_win"] = win_flags
    labeled["is_loss"] = loss_flags
    labeled["realized_return"] = realized_returns
    labeled["lookforward_candles"] = lookforward
    labeled["target_move_pct"] = target_move
    labeled["stop_move_pct"] = stop_move
    labeled["direction"] = normalized_direction
    labeled = labeled.dropna(subset=["is_win", "is_loss", "realized_return", "close", "high", "low"]).reset_index(drop=True)
    print(f"[DEBUG _label_outcomes] Output shape: {labeled.shape}, is_win sum: {labeled['is_win'].sum()}, is_loss sum: {labeled['is_loss'].sum()}")
    return labeled


def _build_atomic_rules(df: pd.DataFrame, min_occurrences: int = 25, min_atomic_rule_win_rate: float = 0.6, quantiles: List[float] = [0.2, 0.4, 0.6, 0.8], top_thresholds_per_indicator: int = 5, max_atomic_rules: int = 48) -> List[AtomicRule]:
    """Build atomic rules from labeled technical data."""
    print(f"[DEBUG AtomicRules] Input shape: {df.shape}, columns: {list(df.columns)[:5]}...")
    atomic_rules: List[AtomicRule] = []
    feature_columns = [
        "rsi_14", "ema20_dist", "ema50_dist", "ema200_dist", "adx", "adx_delta", "macd_hist",
        "macd_hist_delta", "volume_ratio", "atr_ratio", "bb_position", "cci_20", "roc_10",
        "willr_14", "mfi_14", "force_index_13", "stoch_k", "stoch_d", "rsi_delta",
        "price_return_1", "price_return_3", "body_pct", "range_pct", "upper_wick_pct", "lower_wick_pct"
    ]
    
    # DEBUG: Check if required columns exist
    missing_cols = [c for c in feature_columns if c not in df.columns]
    available_cols = list(df.columns)
    print(f"[DEBUG AtomicRules] DataFrame shape: {df.shape}, all columns: {available_cols}")
    print(f"[DEBUG AtomicRules] Missing columns: {missing_cols}")
    
    # DEBUG: Check if is_win column exists
    if "is_win" not in df.columns:
        print(f"[ERROR AtomicRules] Missing 'is_win' column! Available: {available_cols}")
        return []
    
    win_array = df["is_win"].to_numpy(dtype=bool)
    return_array = df["realized_return"].to_numpy(dtype=float)

    rule_count = 0
    for feature in feature_columns:
        if feature not in df.columns:
            print(f"[DEBUG AtomicRules] Feature {feature} not in columns")
            continue
        series = df[feature].dropna()
        if len(series) < min_occurrences:
            print(f"[DEBUG AtomicRules] Feature {feature} has only {len(series)} values, need {min_occurrences}")
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
                feature_values = df[feature].to_numpy(dtype=float)
                mask = (feature_values >= threshold if operator == ">=" else feature_values <= threshold) & ~np.isnan(feature_values)
                occurrences = int(mask.sum())
                if occurrences < min_occurrences:
                    continue
                wins = int(win_array[mask].sum())
                win_rate = wins / max(occurrences, 1)
                if win_rate < min_atomic_rule_win_rate:
                    continue
                expectancy = float(return_array[mask].mean()) if occurrences > 0 else 0.0
                candidates.append(AtomicRule(
                    key=f"{feature}{operator}{round(threshold, 6)}", feature=feature, operator=operator,
                    threshold=threshold, quantile=float(quantile), mask=mask, occurrences=occurrences,
                    wins=wins, win_rate=win_rate, expectancy=expectancy,
                ))
        if candidates:
            print(f"[DEBUG AtomicRules] Feature {feature}: built {len(candidates)} candidates")
            rule_count += len(candidates)
        candidates.sort(key=lambda r: (r.win_rate, r.expectancy, r.occurrences), reverse=True)
        atomic_rules.extend(candidates[:top_thresholds_per_indicator])
    
    print(f"[DEBUG AtomicRules] Total candidates built: {rule_count}, final rules: {len(atomic_rules)}")
    atomic_rules.sort(key=lambda r: (r.win_rate, r.expectancy, r.occurrences), reverse=True)
    
    # DEBUG: Log results
    print(f"[DEBUG AtomicRules] Built {len(atomic_rules)} atomic rules from {len(df)} rows")
    
    return atomic_rules[:max_atomic_rules]


def _search_rule_combinations(df: pd.DataFrame, atomic_rules: List[AtomicRule],
                              min_occurrences: int, max_combination_size: int,
                              min_combo_win_rate: float = 0.45) -> List[Dict[str, Any]]:
    """Search rule combinations - quality-first with softer pruning."""
    if len(atomic_rules) < 2:
        return []
    win_array = df["is_win"].to_numpy(dtype=bool)
    return_array = df["realized_return"].to_numpy(dtype=float)
    results: List[Dict[str, Any]] = []
    
    # Quality-first: lower viable threshold, consider more rules
    viable_rules = [r for r in atomic_rules if r.win_rate >= 0.42]  # Was 0.50
    if len(viable_rules) < 2:
        viable_rules = atomic_rules[:max(24, len(atomic_rules) // 2)]  # Was 20

    for size in range(2, min(max_combination_size, len(viable_rules)) + 1):
        # Higher limits for quality
        max_combos = 8000 if size <= 3 else 4000  # Was 5000/2000
        for idx, combo in enumerate(combinations(viable_rules, size)):
            if idx >= max_combos:
                break
            feature_names = [r.feature for r in combo]
            if len(set(feature_names)) != len(feature_names):
                continue
            mask = combo[0].mask.copy()
            for rule in combo[1:]:
                mask &= rule.mask
                # Softer early break
                if int(mask.sum()) < min_occurrences:
                    break
            occurrences = int(mask.sum())
            if occurrences < min_occurrences:
                continue
            wins = int(win_array[mask].sum())
            win_rate = wins / max(occurrences, 1)
            # Softer win rate threshold
            if win_rate < min_combo_win_rate:
                continue
            losses = occurrences - wins
            selected_returns = return_array[mask]
            pos_sum = float(selected_returns[selected_returns > 0].sum())
            neg_sum = float(np.abs(selected_returns[selected_returns < 0].sum()))
            results.append({
                "rule_key": " && ".join(r.key for r in combo),
                "rule_definition": [{"indicator": r.feature, "operator": r.operator,
                                       "threshold": round(r.threshold, 8), "quantile": r.quantile} for r in combo],
                "threshold_quantiles": [r.quantile for r in combo], "combination_size": size,
                "occurrences": occurrences, "wins": wins, "losses": losses, "win_rate": win_rate,
                "profit_factor": pos_sum / neg_sum if neg_sum > 0 else (999.0 if pos_sum > 0 else 0.0),
                "expectancy": float(selected_returns.mean()) if occurrences > 0 else 0.0,
                "avg_forward_return": float(selected_returns.mean()) if occurrences > 0 else 0.0,
            })
    results.sort(key=lambda r: (r["win_rate"], r["expectancy"], r["occurrences"]), reverse=True)
    return results


# === PRESET FACTORIES ===

def get_balanced_preset() -> PermutationBatchConfigFast:
    """Balanced preset: 1-2 days, good quality.
    
    Estimated time: 18-30 hours for 4 symbols, 4 timeframes
    Quality: Good coverage with reasonable depth
    """
    return PermutationBatchConfigFast(
        lookforward_grid=DEFAULT_LOOKFORWARD_GRID_BALANCED,    # 4 values: (5, 8, 13, 21)
        target_move_grid=DEFAULT_TARGET_GRID_BALANCED,          # 5 values
        stop_move_grid=DEFAULT_STOP_GRID_BALANCED,             # 5 values
        top_thresholds_per_indicator=5,                         # 5 thresholds per indicator
        max_atomic_rules=32,                                    # 32 atomic rules
        max_combination_size=5,                                 # Up to 5-rule combinations
        top_results_per_context=500,                            # Keep top 500 per context
        walk_forward_splits=3,                                  # 3 walk-forward splits
        walk_forward_top_candidates=25,                         # 25 candidates per fold
        min_atomic_rule_win_rate=0.40,                          # Softer: 40%
        min_combo_win_rate=0.45,                                # Softer: 45%
        progress_log_interval=10,
        flush_interval=20,
    )


def get_quality_preset() -> PermutationBatchConfigFast:
    """Quality preset: 2-3 days, higher quality, more comprehensive.
    
    Estimated time: 36-60 hours for 4 symbols, 4 timeframes
    Quality: Deeper search, more combinations, better coverage
    """
    return PermutationBatchConfigFast(
        lookforward_grid=DEFAULT_LOOKFORWARD_GRID_QUALITY,    # 5 values: (3, 5, 8, 13, 21)
        target_move_grid=DEFAULT_TARGET_GRID_QUALITY,           # 8 values (full coverage)
        stop_move_grid=DEFAULT_STOP_GRID_QUALITY,               # 8 values (full coverage)
        top_thresholds_per_indicator=6,                       # 6 thresholds per indicator (original)
        max_atomic_rules=40,                                    # 40 atomic rules (vs 48 original)
        max_combination_size=5,                                 # Up to 5-rule combinations
        top_results_per_context=750,                            # Keep top 750 per context
        walk_forward_splits=4,                                  # 4 walk-forward splits (vs 4-5 original)
        walk_forward_top_candidates=40,                         # 40 candidates per fold
        min_atomic_rule_win_rate=0.38,                          # Even softer: 38%
        min_combo_win_rate=0.42,                                # Even softer: 42%
        progress_log_interval=10,
        flush_interval=25,                                        # Slightly less frequent flush
    )


def get_ultra_fast_preset() -> PermutationBatchConfigFast:
    """Ultra-fast preset: Hours, minimal but functional.
    
    Estimated time: 4-8 hours for 4 symbols, 4 timeframes
    Quality: Minimal but captures main patterns
    """
    return PermutationBatchConfigFast(
        lookforward_grid=(5, 8),                                # 2 values only
        target_move_grid=(0.3, 0.5, 0.8),                       # 3 values
        stop_move_grid=(0.3, 0.5, 0.8),                        # 3 values
        top_thresholds_per_indicator=3,                       # 3 thresholds per indicator
        max_atomic_rules=20,                                    # 20 atomic rules
        max_combination_size=4,                                 # Up to 4-rule combinations
        top_results_per_context=200,                            # Keep top 200 per context
        walk_forward_splits=2,                                  # 2 walk-forward splits
        walk_forward_top_candidates=12,                         # 12 candidates per fold
        min_atomic_rule_win_rate=0.42,
        min_combo_win_rate=0.45,
        progress_log_interval=5,
        flush_interval=10,
    )


def _mask_from_rule_definition(df: pd.DataFrame, rule_def: List[Dict[str, Any]]) -> np.ndarray:
    if df.empty:
        return np.zeros(0, dtype=bool)
    mask = np.ones(len(df), dtype=bool)
    for item in rule_def:
        indicator = str(item.get("indicator") or "")
        operator = str(item.get("operator") or "")
        threshold = float(item.get("threshold") or 0.0)
        if indicator not in df.columns:
            return np.zeros(len(df), dtype=bool)
        values = pd.to_numeric(df[indicator], errors="coerce").to_numpy(dtype=float)
        mask &= ((values >= threshold) if operator == ">=" else (values <= threshold)) & ~np.isnan(values)
        if not mask.any():
            break
    return mask


def _evaluate_rule_definition(df: pd.DataFrame, rule_def: List[Dict[str, Any]]) -> Dict[str, Any]:
    mask = _mask_from_rule_definition(df, rule_def)
    occurrences = int(mask.sum())
    if occurrences <= 0:
        return {"occurrences": 0, "wins": 0, "losses": 0, "win_rate": 0.0, "expectancy": 0.0,
                "avg_forward_return": 0.0, "positive_sum": 0.0, "negative_sum": 0.0}
    win_array = df["is_win"].to_numpy(dtype=bool)
    return_array = df["realized_return"].to_numpy(dtype=float)
    wins = int(win_array[mask].sum())
    losses = occurrences - wins
    selected_returns = return_array[mask]
    pos_sum = float(selected_returns[selected_returns > 0].sum())
    neg_sum = float(np.abs(selected_returns[selected_returns < 0].sum()))
    expectancy = float(selected_returns.mean()) if occurrences > 0 else 0.0
    return {"occurrences": occurrences, "wins": wins, "losses": losses,
            "win_rate": wins / max(occurrences, 1), "expectancy": expectancy,
            "avg_forward_return": expectancy, "positive_sum": pos_sum, "negative_sum": neg_sum}


def _build_walk_forward_slices(row_count: int, splits: int, min_train_size: int, test_size: int) -> List[Tuple[int, int]]:
    if splits <= 0 or row_count < (min_train_size + test_size):
        return []
    max_train_end = row_count - test_size
    if max_train_end <= min_train_size:
        return []
    train_end_points = np.linspace(min_train_size, max_train_end, num=max(splits, 1), dtype=int)
    slices: List[Tuple[int, int]] = []
    seen = set()
    for raw_train_end in train_end_points.tolist():
        train_end = int(max(min_train_size, min(raw_train_end, max_train_end)))
        if train_end in seen:
            continue
        seen.add(train_end)
        test_end = min(train_end + test_size, row_count)
        if test_end - train_end > 0:
            slices.append((train_end, test_end))
    return slices


def _rule_signature(rule_def: List[Dict[str, Any]]) -> str:
    """Create a unique signature for a rule definition for deduplication."""
    if not rule_def:
        return ""
    parts = []
    for item in rule_def:
        indicator = str(item.get("indicator") or "")
        operator = str(item.get("operator") or "")
        quantile = float(item.get("quantile") or 0)
        parts.append(f"{indicator}{operator}q{quantile:.6f}")
    return " && ".join(parts)


def _search_walk_forward_combinations(labeled_df: pd.DataFrame, config: PermutationBatchConfigFast,
                                      progress: Optional[ProgressState] = None) -> List[Dict[str, Any]]:
    """Walk-forward analysis - optimized."""
    slices = _build_walk_forward_slices(len(labeled_df), config.walk_forward_splits,
                                        config.walk_forward_min_train_size, config.walk_forward_test_size)
    if not slices:
        return []
    aggregate: Dict[str, Dict[str, Any]] = {}
    
    for fold_idx, (train_end, test_end) in enumerate(slices):
        if progress:
            progress.phase = f"walk_forward_fold_{fold_idx + 1}/{len(slices)}"
            progress.last_heartbeat = datetime.now(timezone.utc)
        train_df = labeled_df.iloc[:train_end].reset_index(drop=True)
        test_df = labeled_df.iloc[train_end:test_end].reset_index(drop=True)
        if len(train_df) < config.technical_min_occurrences or len(test_df) <= 0:
            continue
        atomic_rules = _build_atomic_rules(train_df, config.technical_min_occurrences,
                                           config.min_atomic_rule_win_rate, list(config.quantiles),
                                           config.top_thresholds_per_indicator, config.max_atomic_rules)
        if len(atomic_rules) < 2:
            continue
        train_rows = _search_rule_combinations(train_df, atomic_rules, config.technical_min_occurrences, config.max_combination_size, config.min_combo_win_rate)
        for row in train_rows[:max(1, config.walk_forward_top_candidates)]:
            signature = _rule_signature(row["rule_definition"])
            if not signature:
                continue
            validation = _evaluate_rule_definition(test_df, row["rule_definition"])
            if signature not in aggregate:
                aggregate[signature] = {
                    "rule_key": signature,
                    "components": [{"indicator": c["indicator"], "operator": c["operator"],
                                    "quantile": float(c.get("quantile") or 0.0),
                                    "threshold_sum": float(c.get("threshold") or 0.0), "count": 1}
                                   for c in row["rule_definition"]],
                    "threshold_quantiles": [float(c.get("quantile") or 0.0) for c in row["rule_definition"]],
                    "combination_size": int(row["combination_size"]),
                    "train_occurrences": 0, "train_wins": 0, "train_return_sum": 0.0,
                    "validation_occurrences": 0, "validation_wins": 0, "validation_return_sum": 0.0,
                    "validation_positive_sum": 0.0, "validation_negative_sum": 0.0,
                    "walk_forward_passes": 0, "walk_forward_folds": 0,
                }
            else:
                for idx, component in enumerate(row["rule_definition"]):
                    aggregate[signature]["components"][idx]["threshold_sum"] += float(component.get("threshold") or 0.0)
                    aggregate[signature]["components"][idx]["count"] += 1
            entry = aggregate[signature]
            entry["train_occurrences"] += int(row["occurrences"])
            entry["train_wins"] += int(row["wins"])
            entry["train_return_sum"] += float(row["expectancy"]) * int(row["occurrences"])
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
        val_occ = int(entry["validation_occurrences"])
        if val_occ < config.technical_min_occurrences or int(entry["walk_forward_passes"]) < min_passes:
            continue
        val_wins = int(entry["validation_wins"])
        val_neg_sum = float(entry["validation_negative_sum"])
        avg_def = [{"indicator": c["indicator"], "operator": c["operator"],
                    "threshold": round(c["threshold_sum"] / max(c["count"], 1), 8), "quantile": c["quantile"]}
                   for c in entry["components"]]
        train_occ = int(entry["train_occurrences"])
        train_wins = int(entry["train_wins"])
        val_exp = float(entry["validation_return_sum"]) / max(val_occ, 1)
        train_exp = float(entry["train_return_sum"]) / max(train_occ, 1)
        results.append({
            "rule_key": entry["rule_key"], "rule_definition": avg_def,
            "threshold_quantiles": entry["threshold_quantiles"], "combination_size": int(entry["combination_size"]),
            "occurrences": val_occ, "wins": val_wins, "losses": val_occ - val_wins,
            "win_rate": val_wins / max(val_occ, 1),
            "profit_factor": float(entry["validation_positive_sum"]) / val_neg_sum if val_neg_sum > 0 else (999.0 if float(entry["validation_positive_sum"]) > 0 else 0.0),
            "expectancy": val_exp, "avg_forward_return": val_exp,
            "train_occurrences": train_occ, "train_wins": train_wins,
            "train_win_rate": train_wins / max(train_occ, 1), "train_expectancy": train_exp,
            "validation_occurrences": val_occ, "validation_wins": val_wins,
            "validation_win_rate": val_wins / max(val_occ, 1), "validation_expectancy": val_exp,
            "walk_forward_splits": int(config.walk_forward_splits), "walk_forward_passes": int(entry["walk_forward_passes"]),
            "walk_forward_folds": int(entry["walk_forward_folds"]),
        })
    results.sort(key=lambda r: (r["validation_win_rate"], r["validation_expectancy"], r["validation_occurrences"], r["walk_forward_passes"]), reverse=True)
    return results


async def run_permutation_batch_fast(config: Optional[PermutationBatchConfigFast] = None) -> Dict[str, Any]:
    """Fast permutation batch with progress tracking and periodic flush.
    
    TARGET: 1-2 day completion vs 4+ days for original.
    """
    config = config or PermutationBatchConfigFast()
    if not is_db_available():
        return {"success": False, "error": "Database not available"}
    client = get_supabase_client()
    if not client:
        return {"success": False, "error": "No database connection"}

    symbols = [_normalize_symbol(s) for s in config.symbols]
    directions = [_normalize_direction(direction) for direction in config.directions]
    lookforward_grid = _resolve_int_grid(config.lookforward_grid, config.lookforward_candles)
    target_move_grid = _resolve_float_grid(config.target_move_grid, config.target_move_pct)
    stop_move_grid = _resolve_float_grid(config.stop_move_grid, config.stop_move_pct)
    
    # Calculate theoretical contexts for progress tracking
    total_model_contexts = len(symbols) * len(directions)
    total_technical_contexts = len(symbols) * len(config.technical_timeframes) * len(directions) * len(lookforward_grid) * len(target_move_grid) * len(stop_move_grid)

    checkpoint_data: Dict[str, Any] = {}
    existing_model_context_keys: Set[str] = set()
    existing_technical_context_keys: Set[str] = set()
    existing_model_row_count = 0
    existing_technical_row_count = 0

    if config.resume_run_id:
        run_id = config.resume_run_id
        run_record = _get_run_record(client, run_id)
        if not run_record:
            return {"success": False, "error": f"resume_run_id not found: {run_id}"}
        checkpoint_data = _load_checkpoint(run_id)
        existing_model_context_keys = _fetch_existing_model_context_keys(client, run_id)
        existing_technical_context_keys = _fetch_existing_technical_context_keys(client, run_id)
        existing_model_row_count = max(int(checkpoint_data.get("model_rows_written") or 0), _fetch_row_count(client, "model_permutation_batch_results", run_id))
        existing_technical_row_count = max(int(checkpoint_data.get("technical_rows_written") or 0), _fetch_row_count(client, "technical_permutation_batch_results", run_id))
    else:
        run_id = _insert_run(client, "full", config)

    progress = _restore_progress_state(
        run_id=run_id,
        total_model_contexts=total_model_contexts,
        total_technical_contexts=total_technical_contexts,
        checkpoint_data=checkpoint_data,
        existing_model_context_keys=existing_model_context_keys,
        existing_technical_context_keys=existing_technical_context_keys,
        existing_model_row_count=existing_model_row_count,
        existing_technical_row_count=existing_technical_row_count,
    )
    
    summary: Dict[str, Any] = {
        "run_id": run_id,
        "dry_run": config.dry_run,
        "model_contexts": progress.completed_model_contexts,
        "technical_contexts": len(existing_technical_context_keys),
        "technical_completed_contexts": progress.completed_technical_contexts,
        "model_rows": progress.model_rows_written,
        "technical_rows": progress.technical_rows_written,
        "technical_resampled": [],
        "technical_skipped": [],
        "total_theoretical_contexts": total_model_contexts + total_technical_contexts,
        "progress": {},
        "checkpoint_path": str(_checkpoint_path(run_id)),
        "skip_model_stage": config.skip_model_stage,
        "reuse_model_run_id": config.reuse_model_run_id,
        "resume_run_id": config.resume_run_id,
        "loaded_checkpoint_model_contexts": len(checkpoint_data.get("completed_model_context_keys") or []),
        "loaded_checkpoint_technical_contexts": len(checkpoint_data.get("completed_technical_context_keys") or []),
        "loaded_db_model_contexts": len(existing_model_context_keys),
        "loaded_db_technical_contexts": len(existing_technical_context_keys),
        "model_reuse_mismatches": [],
    }

    try:
        if config.resume_run_id and not config.dry_run:
            _mark_run_running(client, run_id, progress.to_dict())

        # ===== MODEL PHASE =====
        progress.phase = "model"
        _persist_progress(client, progress, config)
        _log_progress(progress, force=True)

        if config.reuse_model_run_id:
            _, mismatches = _validate_model_reuse(client, config.reuse_model_run_id, config, symbols, directions)
            summary["model_reuse_mismatches"] = mismatches
            if progress.model_rows_written == 0 and not progress.completed_model_context_keys and not config.dry_run:
                copied_model_rows, copied_context_keys = _copy_model_rows_from_run(client, config.reuse_model_run_id, run_id)
                progress.model_rows_written = max(progress.model_rows_written, copied_model_rows)
                for context_key in copied_context_keys:
                    progress.register_model_context(context_key)
                summary["model_rows_reused"] = copied_model_rows
                summary["model_contexts_reused"] = len(copied_context_keys)
                summary["model_contexts"] = progress.completed_model_contexts
                summary["model_rows"] = progress.model_rows_written
                _persist_progress(client, progress, config)
            else:
                summary["model_rows_reused"] = 0
                summary["model_contexts_reused"] = 0

        skip_model_stage = bool(config.skip_model_stage or config.reuse_model_run_id)

        if not skip_model_stage:
            for symbol in symbols:
                for direction in directions:
                    context_key = _build_model_context_key(symbol, direction)
                    if context_key in progress.completed_model_context_keys:
                        continue

                    progress.current_symbol = symbol
                    progress.current_direction = direction
                    progress.current_timeframe = None

                    model_result = await analyze_model_permutations(
                        symbol=symbol,
                        direction=direction,
                        min_occurrences=config.model_min_occurrences,
                        lookback_days=config.model_lookback_days,
                        cluster_window_minutes=config.cluster_window_minutes,
                    )
                    if model_result.get("error"):
                        continue

                    context_rows: List[Dict[str, Any]] = []
                    for rank, row in enumerate(model_result.get("results", []), start=1):
                        context_rows.append({
                            "run_id": run_id, "symbol": symbol, "direction": direction,
                            "combination": row.get("combination"),
                            "total_signals": int(row.get("total_signals", 0) or 0),
                            "wins": int(row.get("wins", 0) or 0),
                            "losses": int(row.get("losses", 0) or 0),
                            "win_rate": float(row.get("win_rate", 0) or 0),
                            "profit_factor": float(row.get("profit_factor", 0) or 0),
                            "expectancy": float(row.get("expectancy", 0) or 0),
                            "avg_member_alignment": float(row.get("avg_member_alignment", 0) or 0),
                            "unanimous_win_rate": float(row.get("unanimous_win_rate", 0) or 0),
                            "lookback_days": int(model_result.get("lookback_days_used", config.model_lookback_days)),
                            "cluster_window_minutes": int(model_result.get("cluster_window_minutes", config.cluster_window_minutes)),
                            "insufficient_data": bool(row.get("insufficient_data", False)),
                            "rank": rank,
                        })

                    if not config.dry_run:
                        _upsert_rows(client, "model_permutation_batch_results", context_rows, "run_id,symbol,direction,combination")

                    progress.model_rows_written += len(context_rows)
                    progress.register_model_context(context_key)
                    summary["model_contexts"] = progress.completed_model_contexts
                    summary["model_rows"] = progress.model_rows_written
                    _persist_progress(client, progress, config)

                    if progress.completed_model_contexts % config.progress_log_interval == 0:
                        _log_progress(progress)
        else:
            summary["model_contexts"] = progress.completed_model_contexts
            summary["model_rows"] = progress.model_rows_written
            _persist_progress(client, progress, config)

        _log_progress(progress, force=True)

        # ===== TECHNICAL PHASE =====
        progress.phase = "technical"
        _persist_progress(client, progress, config)
        _log_progress(progress, force=True)

        for symbol in symbols:
            for timeframe in config.technical_timeframes:
                progress.current_symbol = symbol
                progress.current_timeframe = timeframe

                candles, resampled_from = await asyncio.to_thread(
                    _load_technical_candles, symbol, timeframe, config.technical_candle_limit, config.resample_missing_timeframes
                )
                if resampled_from:
                    summary["technical_resampled"].append({
                        "symbol": symbol, "timeframe": timeframe, "source_timeframe": resampled_from, "candles": len(candles)
                    })
                if len(candles) < max(160, config.technical_min_occurrences * 3):
                    timeframe_context_keys = _build_technical_context_keys_for_timeframe(
                        symbol,
                        timeframe,
                        directions,
                        lookforward_grid,
                        target_move_grid,
                        stop_move_grid,
                        config.walk_forward_splits,
                    )
                    for context_key in timeframe_context_keys:
                        progress.register_technical_context(context_key)
                    summary["technical_skipped"].append({"symbol": symbol, "timeframe": timeframe, "reason": "not_enough_candles", "candles": len(candles)})
                    summary["technical_completed_contexts"] = progress.completed_technical_contexts
                    _persist_progress(client, progress, config)
                    continue

                prepared_df = await asyncio.to_thread(_prepare_technical_dataframe, candles)
                if prepared_df.empty or len(prepared_df) < max(140, config.technical_min_occurrences * 2):
                    timeframe_context_keys = _build_technical_context_keys_for_timeframe(
                        symbol,
                        timeframe,
                        directions,
                        lookforward_grid,
                        target_move_grid,
                        stop_move_grid,
                        config.walk_forward_splits,
                    )
                    for context_key in timeframe_context_keys:
                        progress.register_technical_context(context_key)
                    summary["technical_skipped"].append({"symbol": symbol, "timeframe": timeframe, "reason": "invalid_dataframe", "candles": len(prepared_df)})
                    summary["technical_completed_contexts"] = progress.completed_technical_contexts
                    _persist_progress(client, progress, config)
                    continue

                for direction in directions:
                    progress.current_direction = direction

                    for lookforward_candles in lookforward_grid:
                        for target_move_pct in target_move_grid:
                            for stop_move_pct in stop_move_grid:
                                profile_key = _build_profile_key(lookforward_candles, target_move_pct, stop_move_pct, config.walk_forward_splits)
                                context_key = _build_technical_context_key(symbol, timeframe, direction, profile_key)
                                if context_key in progress.completed_technical_context_keys:
                                    continue

                                labeled_df = await asyncio.to_thread(
                                    _label_outcomes, prepared_df, direction, lookforward_candles, target_move_pct, stop_move_pct
                                )
                                print(f"[DEBUG MAIN] After _label_outcomes: {len(labeled_df)} rows, is_win sum: {labeled_df['is_win'].sum() if 'is_win' in labeled_df.columns else 'N/A'}")
                                if labeled_df.empty or len(labeled_df) < config.technical_min_occurrences:
                                    summary["technical_skipped"].append({
                                        "symbol": symbol, "timeframe": timeframe, "direction": direction,
                                        "lookforward_candles": lookforward_candles, "target_move_pct": target_move_pct,
                                        "stop_move_pct": stop_move_pct, "reason": "not_enough_labeled_rows", "rows": len(labeled_df)
                                    })
                                    progress.register_technical_context(context_key)
                                    summary["technical_completed_contexts"] = progress.completed_technical_contexts
                                    _persist_progress(client, progress, config)
                                    continue

                                # Process based on walk-forward setting
                                logger.info(f"[Technical] Processing {symbol}/{timeframe}/{direction} - labeled_df has {len(labeled_df)} rows, {len(labeled_df.columns)} columns")
                                if config.walk_forward_splits > 0:
                                    combo_rows = await asyncio.to_thread(
                                        _search_walk_forward_combinations, labeled_df, config, progress
                                    )
                                else:
                                    atomic_rules = await asyncio.to_thread(
                                        _build_atomic_rules, labeled_df, 
                                        config.technical_min_occurrences,
                                        config.min_atomic_rule_win_rate,
                                        config.quantiles, 
                                        config.top_thresholds_per_indicator,
                                    )
                                    logger.info(f"[Technical] Built {len(atomic_rules)} atomic rules")
                                    if len(atomic_rules) < 2:
                                        summary["technical_skipped"].append({
                                            "symbol": symbol, "timeframe": timeframe, "direction": direction,
                                            "lookforward_candles": lookforward_candles, "target_move_pct": target_move_pct,
                                            "stop_move_pct": stop_move_pct, "reason": "not_enough_atomic_rules", "rules": len(atomic_rules)
                                        })
                                        progress.register_technical_context(context_key)
                                        summary["technical_completed_contexts"] = progress.completed_technical_contexts
                                        _persist_progress(client, progress, config)
                                        continue
                                    combo_rows = await asyncio.to_thread(
                                        _search_rule_combinations, labeled_df, atomic_rules, config.technical_min_occurrences, config.max_combination_size
                                    )
                                    logger.info(f"[Technical] Found {len(combo_rows)} combo rows")

                                if not combo_rows:
                                    summary["technical_skipped"].append({
                                        "symbol": symbol, "timeframe": timeframe, "direction": direction,
                                        "lookforward_candles": lookforward_candles, "target_move_pct": target_move_pct,
                                        "stop_move_pct": stop_move_pct, "reason": "no_combo_rows"
                                    })
                                    progress.register_technical_context(context_key)
                                    summary["technical_completed_contexts"] = progress.completed_technical_contexts
                                    _persist_progress(client, progress, config)
                                    continue

                                summary["technical_contexts"] += 1
                                context_rows: List[Dict[str, Any]] = []

                                for rank, row in enumerate(combo_rows[:config.top_results_per_context], start=1):
                                    context_rows.append({
                                        "run_id": run_id, "symbol": symbol, "direction": direction, "timeframe": timeframe,
                                        "profile_key": profile_key, "rule_key": row["rule_key"],
                                        "combination_size": int(row["combination_size"]),
                                        "rule_definition": _json_ready(row["rule_definition"]),
                                        "occurrences": int(row["occurrences"]), "wins": int(row["wins"]), "losses": int(row["losses"]),
                                        "win_rate": float(row["win_rate"]), "profit_factor": float(row["profit_factor"]),
                                        "expectancy": float(row["expectancy"]), "avg_forward_return": float(row["avg_forward_return"]),
                                        "target_move_pct": float(target_move_pct), "stop_move_pct": float(stop_move_pct),
                                        "lookforward_candles": int(lookforward_candles),
                                        "threshold_quantiles": _json_ready(row["threshold_quantiles"]),
                                        "train_occurrences": int(row.get("train_occurrences", 0)),
                                        "train_wins": int(row.get("train_wins", 0)),
                                        "train_win_rate": float(row.get("train_win_rate", row["win_rate"])),
                                        "train_expectancy": float(row.get("train_expectancy", row["expectancy"])),
                                        "validation_occurrences": int(row.get("validation_occurrences", row["occurrences"])),
                                        "validation_wins": int(row.get("validation_wins", row["wins"])),
                                        "validation_win_rate": float(row.get("validation_win_rate", row["win_rate"])),
                                        "validation_expectancy": float(row.get("validation_expectancy", row["expectancy"])),
                                        "walk_forward_splits": int(row.get("walk_forward_splits", config.walk_forward_splits)),
                                        "walk_forward_passes": int(row.get("walk_forward_passes", 0)),
                                        "walk_forward_folds": int(row.get("walk_forward_folds", 0)),
                                        "insufficient_data": int(row["occurrences"]) < config.technical_min_occurrences,
                                        "rank": rank,
                                    })

                                if not config.dry_run:
                                    _upsert_rows(client, "technical_permutation_batch_results", context_rows, "run_id,symbol,direction,timeframe,profile_key,rule_key")

                                progress.technical_rows_written += len(context_rows)
                                progress.register_technical_context(context_key)
                                summary["technical_rows"] = progress.technical_rows_written
                                summary["technical_completed_contexts"] = progress.completed_technical_contexts
                                _persist_progress(client, progress, config)

                                if progress.completed_technical_contexts % config.progress_log_interval == 0:
                                    _log_progress(progress)

        progress.phase = "completed"
        summary["model_contexts"] = progress.completed_model_contexts
        summary["model_rows"] = progress.model_rows_written
        summary["technical_rows"] = progress.technical_rows_written
        summary["technical_completed_contexts"] = progress.completed_technical_contexts
        _log_progress(progress, force=True)
        _write_checkpoint(progress, config)
        
        # Add progress to summary
        summary["progress"] = progress.to_dict()
        
        _finish_run(client, run_id, status="completed", summary=summary)
        return {"success": True, **summary}
        
    except Exception as exc:
        progress.phase = "failed"
        progress.last_heartbeat = datetime.now(timezone.utc)
        _write_checkpoint(progress, config)
        logger.error(f"[PermutationBatchFast] run failed: {exc}", exc_info=True)
        summary["model_contexts"] = progress.completed_model_contexts
        summary["model_rows"] = progress.model_rows_written
        summary["technical_rows"] = progress.technical_rows_written
        summary["technical_completed_contexts"] = progress.completed_technical_contexts
        summary["progress"] = progress.to_dict()
        _finish_run(client, run_id, status="failed", summary=summary, error=str(exc))
        return {"success": False, **summary, "error": str(exc)}

