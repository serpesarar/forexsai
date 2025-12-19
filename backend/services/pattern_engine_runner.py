from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import List

from backend.config import settings


def _path_exists(path: str) -> bool:
    return Path(path).expanduser().exists()


def run_pattern_engine(last_n: int, select_top: float, output_selected_only: bool) -> dict:
    model_ok = _path_exists(settings.pattern_engine_path)
    status = None if model_ok else f"Runtime not found: {settings.pattern_engine_path}"
    now = datetime.utcnow()
    patterns: List[dict] = []
    for idx in range(min(10, last_n)):
        timestamp = (now - timedelta(minutes=idx * 15)).isoformat() + "Z"
        patterns.append(
            {
                "timestamp": timestamp,
                "pattern_id": f"double_bottom_{idx + 1}",
                "route": "BUY" if idx % 2 == 0 else "SELL",
                "p_success": round(0.82 - idx * 0.01, 2),
                "trade_ok": idx % 3 != 0,
                "trade_thr": 0.65,
                "expected_next": "UP" if idx % 2 == 0 else "DOWN",
                "stage": "DETECTED",
            }
        )
    selected_count = int(last_n * select_top)
    return {
        "patterns": patterns,
        "total_candidates": last_n,
        "selected_count": selected_count,
        "selection_threshold": 0.65,
        "model_status": status,
    }
