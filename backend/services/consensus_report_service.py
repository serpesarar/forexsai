from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

logger = logging.getLogger(__name__)

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
DEFAULT_REPORT_DIR = Path("~/Desktop/permutation_runs").expanduser()
DEFAULT_REPORT_PREFIX = "consensus_model_analysis"


def _normalize_symbol(symbol: str) -> str:
    raw = str(symbol or "").upper().strip()
    return SYMBOL_ALIASES.get(raw, raw)


def _quality_rank(value: Optional[str]) -> int:
    return {
        "strong": 4,
        "usable": 3,
        "weak": 2,
        "weak_sample": 1,
    }.get(str(value or "weak_sample"), 0)


def _as_int(value: Any) -> int:
    try:
        return int(value or 0)
    except Exception:
        return 0


def _as_float(value: Any) -> float:
    try:
        return float(value or 0.0)
    except Exception:
        return 0.0


def _candidate_paths(prefix: Optional[str], report_path: Optional[str]) -> List[Path]:
    candidates: List[Path] = []
    if report_path:
        candidates.append(Path(report_path).expanduser())
    env_path = os.getenv("CONSENSUS_REPORT_PATH")
    if env_path:
        candidates.append(Path(env_path).expanduser())
    return candidates


def resolve_report_path(prefix: Optional[str] = None, report_path: Optional[str] = None) -> Path:
    for candidate in _candidate_paths(prefix, report_path):
        if candidate.is_file():
            return candidate

    report_prefix = str(prefix or os.getenv("CONSENSUS_REPORT_PREFIX") or DEFAULT_REPORT_PREFIX).strip()
    if not DEFAULT_REPORT_DIR.exists():
        raise FileNotFoundError(f"Consensus report directory not found: {DEFAULT_REPORT_DIR}")

    exact_path = DEFAULT_REPORT_DIR / f"{report_prefix}.json"
    if exact_path.is_file():
        return exact_path

    matches = sorted(
        DEFAULT_REPORT_DIR.glob(f"{report_prefix}*.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if matches:
        return matches[0]

    fallback_matches = sorted(
        DEFAULT_REPORT_DIR.glob("consensus_model_analysis*.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if fallback_matches:
        return fallback_matches[0]

    raise FileNotFoundError(f"No consensus report found in {DEFAULT_REPORT_DIR}")


def load_consensus_report(prefix: Optional[str] = None, report_path: Optional[str] = None) -> Dict[str, Any]:
    path = resolve_report_path(prefix=prefix, report_path=report_path)
    payload = json.loads(path.read_text())
    if not isinstance(payload, dict):
        raise ValueError("Consensus report payload is not a JSON object")
    payload["__report_path"] = str(path)
    return payload


def _rank_most_frequent(rows: Sequence[Dict[str, Any]], top: int) -> List[Dict[str, Any]]:
    ranked_rows = sorted(
        rows,
        key=lambda row: (
            _as_int(row.get("occurrences")),
            _as_int(row.get("resolved_count")),
            _as_float(row.get("completion_rate")),
            _as_float(row.get("win_rate")),
            _quality_rank(row.get("quality")),
        ),
        reverse=True,
    )
    return list(ranked_rows[:top])


def _rank_best_stable(rows: Sequence[Dict[str, Any]], top: int, min_occurrences: int) -> List[Dict[str, Any]]:
    eligible_rows = [
        row
        for row in rows
        if _as_int(row.get("occurrences")) >= max(_as_int(min_occurrences), 1)
        and _as_int(row.get("resolved_count")) >= 3
    ]
    ranked_rows = sorted(
        eligible_rows,
        key=lambda row: (
            _quality_rank(row.get("quality")),
            _as_float(row.get("stability_score")),
            _as_float(row.get("win_rate")),
            _as_float(row.get("completion_rate")),
            _as_int(row.get("occurrences")),
            _as_float(row.get("profit_factor")),
            _as_float(row.get("expectancy")),
        ),
        reverse=True,
    )
    return list(ranked_rows[:top])


def _serialize_rows(rows: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    serialized: List[Dict[str, Any]] = []
    for row in rows:
        serialized.append({
            "symbol": row.get("symbol"),
            "direction": row.get("direction"),
            "combination": row.get("combination"),
            "model_count": _as_int(row.get("model_count")),
            "occurrences": _as_int(row.get("occurrences")),
            "wins": _as_int(row.get("wins")),
            "losses": _as_int(row.get("losses")),
            "expired": _as_int(row.get("expired")),
            "resolved_count": _as_int(row.get("resolved_count")),
            "win_rate": _as_float(row.get("win_rate")),
            "completion_rate": _as_float(row.get("completion_rate")),
            "profit_factor": _as_float(row.get("profit_factor")),
            "expectancy": _as_float(row.get("expectancy")),
            "stability_score": _as_float(row.get("stability_score")),
            "quality": row.get("quality") or "weak",
            "first_seen_at": row.get("first_seen_at"),
            "last_seen_at": row.get("last_seen_at"),
        })
    return serialized


def _direction_payload(rows: Sequence[Dict[str, Any]], top: int, min_occurrences: int) -> Dict[str, Any]:
    most_frequent_rows = _serialize_rows(_rank_most_frequent(rows, top))
    best_stable_rows = _serialize_rows(_rank_best_stable(rows, top, min_occurrences))
    return {
        "total_rows": len(rows),
        "most_frequent": most_frequent_rows,
        "best_stable": best_stable_rows,
        "top_quality_counts": {
            "strong": sum(1 for row in rows if str(row.get("quality")) == "strong"),
            "usable": sum(1 for row in rows if str(row.get("quality")) == "usable"),
            "weak": sum(1 for row in rows if str(row.get("quality")) == "weak"),
            "weak_sample": sum(1 for row in rows if str(row.get("quality")) == "weak_sample"),
        },
    }


def _empty_direction_payload() -> Dict[str, Any]:
    return {
        "total_rows": 0,
        "most_frequent": [],
        "best_stable": [],
        "top_quality_counts": {"strong": 0, "usable": 0, "weak": 0, "weak_sample": 0},
    }


def _assign_quality(row: Dict[str, Any]) -> str:
    """Assign quality label based on signals and win_rate."""
    signals = _as_int(row.get("total_signals") or row.get("occurrences") or 0)
    wr = _as_float(row.get("win_rate") or 0)
    pf = _as_float(row.get("profit_factor") or 0)
    if signals >= 15 and wr >= 0.60 and pf >= 1.5:
        return "strong"
    if signals >= 8 and wr >= 0.50 and pf >= 1.0:
        return "usable"
    if signals >= 5:
        return "weak"
    return "weak_sample"


def _db_direction_payload(rows: List[Dict[str, Any]], top: int) -> Dict[str, Any]:
    """Build direction payload from DB rows (model_permutation_batch_results format)."""
    enriched = []
    for row in rows:
        quality = _assign_quality(row)
        signals = _as_int(row.get("total_signals") or 0)
        wins = _as_int(row.get("wins") or 0)
        losses = _as_int(row.get("losses") or 0)
        wr = _as_float(row.get("win_rate") or 0)
        pf = _as_float(row.get("profit_factor") or 0)
        exp = _as_float(row.get("expectancy") or 0)
        combo = row.get("combination") or ""
        enriched.append({
            "symbol": row.get("symbol"),
            "direction": row.get("direction"),
            "combination": combo,
            "model_count": len(combo.split("+")) if combo else 0,
            "occurrences": signals,
            "total_signals": signals,
            "wins": wins,
            "losses": losses,
            "expired": 0,
            "resolved_count": signals,
            "win_rate": wr,
            "completion_rate": 1.0,
            "profit_factor": pf,
            "expectancy": exp,
            "stability_score": wr * min(1.0, signals / 20.0),
            "quality": quality,
        })

    most_frequent = sorted(enriched, key=lambda r: (_as_int(r["total_signals"]), _as_float(r["win_rate"])), reverse=True)[:top]
    best_stable = sorted(
        [r for r in enriched if r["total_signals"] >= 5],
        key=lambda r: (_quality_rank(r["quality"]), _as_float(r["stability_score"]), _as_float(r["win_rate"])),
        reverse=True,
    )[:top]

    return {
        "total_rows": len(enriched),
        "most_frequent": most_frequent,
        "best_stable": best_stable,
        "top_quality_counts": {
            "strong": sum(1 for r in enriched if r["quality"] == "strong"),
            "usable": sum(1 for r in enriched if r["quality"] == "usable"),
            "weak": sum(1 for r in enriched if r["quality"] == "weak"),
            "weak_sample": sum(1 for r in enriched if r["quality"] == "weak_sample"),
        },
    }


def get_db_consensus_view(symbol: str, *, top: int = 6) -> Dict[str, Any]:
    """Build consensus view from model_permutation_batch_results in DB."""
    from database.supabase_client import get_supabase_client

    normalized_symbol = _normalize_symbol(symbol)
    client = get_supabase_client()
    if not client:
        logger.warning("[ConsensusReportService] No DB client for DB consensus")
        return {
            "symbol": normalized_symbol,
            "report_generated_at": None,
            "report_path": None,
            "parameters": {},
            "buy": _empty_direction_payload(),
            "sell": _empty_direction_payload(),
            "warning": "No database connection",
        }

    # Find latest completed batch run with model data
    runs_result = (
        client.table("permutation_batch_runs")
        .select("id,started_at,completed_at,parameters")
        .eq("status", "completed")
        .in_("batch_kind", ["full", "model"])
        .order("started_at", desc=True)
        .limit(10)
        .execute()
    )
    runs = runs_result.data if hasattr(runs_result, "data") else (runs_result.get("data") if isinstance(runs_result, dict) else [])
    if not runs:
        return {
            "symbol": normalized_symbol,
            "report_generated_at": None,
            "report_path": None,
            "parameters": {},
            "buy": _empty_direction_payload(),
            "sell": _empty_direction_payload(),
            "warning": "No completed batch runs found",
        }

    # Try each run until we find data for this symbol
    # Also try CL.COMM alias for USOIL.FOREX
    symbol_variants = [normalized_symbol]
    if normalized_symbol == "USOIL.FOREX":
        symbol_variants.append("CL.COMM")

    for run in (runs or []):
        run_id = run.get("id")
        if not run_id:
            continue

        for sym_variant in symbol_variants:
            result = (
                client.table("model_permutation_batch_results")
                .select("combination,direction,total_signals,wins,losses,win_rate,profit_factor,expectancy,lookback_days,insufficient_data")
                .eq("run_id", run_id)
                .eq("symbol", sym_variant)
                .eq("insufficient_data", False)
                .order("rank")
                .limit(100)
                .execute()
            )
            rows = result.data if hasattr(result, "data") else (result.get("data") if isinstance(result, dict) else [])
            if not rows:
                continue

            # Split by direction
            buy_rows = [r for r in rows if str(r.get("direction") or "").upper() == "BUY"]
            sell_rows = [r for r in rows if str(r.get("direction") or "").upper() == "SELL"]

            # If no direction column in model batch results, we need to query per direction
            if not buy_rows and not sell_rows:
                # Query separately by direction
                for dir_val in ["BUY", "SELL"]:
                    dir_result = (
                        client.table("model_permutation_batch_results")
                        .select("combination,direction,total_signals,wins,losses,win_rate,profit_factor,expectancy,lookback_days")
                        .eq("run_id", run_id)
                        .eq("symbol", sym_variant)
                        .eq("direction", dir_val)
                        .eq("insufficient_data", False)
                        .order("rank")
                        .limit(50)
                        .execute()
                    )
                    dir_rows = dir_result.data if hasattr(dir_result, "data") else (dir_result.get("data") if isinstance(dir_result, dict) else [])
                    if dir_val == "BUY":
                        buy_rows = dir_rows or []
                    else:
                        sell_rows = dir_rows or []

            params = run.get("parameters") or {}
            lookback = _as_int((buy_rows or sell_rows or [{}])[0].get("lookback_days") or params.get("model_lookback_days") or 0)

            return {
                "symbol": normalized_symbol,
                "report_generated_at": run.get("completed_at") or run.get("started_at"),
                "report_path": f"db:batch_run:{run_id}",
                "parameters": {
                    "lookback_days": lookback,
                    "bucket_minutes": _as_int(params.get("cluster_window_minutes") or 10),
                    "min_occurrences": _as_int(params.get("model_min_occurrences") or 5),
                    "target_level": "batch",
                },
                "buy": _db_direction_payload(buy_rows, top=top),
                "sell": _db_direction_payload(sell_rows, top=top),
            }

    return {
        "symbol": normalized_symbol,
        "report_generated_at": None,
        "report_path": None,
        "parameters": {},
        "buy": _empty_direction_payload(),
        "sell": _empty_direction_payload(),
        "warning": f"No batch results found for {normalized_symbol}",
    }


def get_symbol_consensus_view(
    symbol: str,
    *,
    top: int = 6,
    prefix: Optional[str] = None,
    report_path: Optional[str] = None,
) -> Dict[str, Any]:
    normalized_symbol = _normalize_symbol(symbol)
    try:
        payload = load_consensus_report(prefix=prefix, report_path=report_path)
    except FileNotFoundError as exc:
        logger.warning("[ConsensusReportService] %s — returning empty view", exc)
        return {
            "symbol": normalized_symbol,
            "report_generated_at": None,
            "report_path": None,
            "parameters": {},
            "buy": _empty_direction_payload(),
            "sell": _empty_direction_payload(),
            "warning": str(exc),
        }
    rows = payload.get("aggregates") or []
    if not isinstance(rows, list):
        rows = []
    params = payload.get("parameters") or {}
    min_occurrences = _as_int(params.get("min_occurrences") or 5)

    symbol_rows = [row for row in rows if _normalize_symbol(str(row.get("symbol") or "")) == normalized_symbol]
    buy_rows = [row for row in symbol_rows if str(row.get("direction") or "").upper() == "BUY"]
    sell_rows = [row for row in symbol_rows if str(row.get("direction") or "").upper() == "SELL"]

    return {
        "symbol": normalized_symbol,
        "report_generated_at": payload.get("generated_at"),
        "report_path": payload.get("__report_path"),
        "parameters": {
            "lookback_days": _as_int(params.get("lookback_days") or 0),
            "bucket_minutes": _as_int(params.get("bucket_minutes") or 0),
            "min_models_per_event": _as_int(params.get("min_models_per_event") or 0),
            "min_occurrences": min_occurrences,
            "max_combo_size": _as_int(params.get("max_combo_size") or 0),
            "target_level": params.get("target_level"),
            "price_timeframe": params.get("price_timeframe"),
            "tie_policy": params.get("tie_policy"),
        },
        "buy": _direction_payload(buy_rows, top=top, min_occurrences=min_occurrences),
        "sell": _direction_payload(sell_rows, top=top, min_occurrences=min_occurrences),
    }
