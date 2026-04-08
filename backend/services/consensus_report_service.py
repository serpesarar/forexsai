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
