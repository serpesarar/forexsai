from __future__ import annotations

from typing import Any, Dict, Optional

from services.ml_history_backfill_service import DESIRED_TIMEFRAME, plan_ml_backfill_update, run_ml_history_backfill


def plan_xauusd_ml_backfill_update(row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if (row.get("symbol") or "").upper().strip() != "XAUUSD":
        return None
    return plan_ml_backfill_update(row)


def run_xauusd_ml_history_backfill(
    *,
    dry_run: bool = True,
    client=None,
    max_records: int = 5000,
    window_days: int = 1,
    sample_size: int = 10,
) -> Dict[str, Any]:
    return run_ml_history_backfill(
        dry_run=dry_run,
        client=client,
        symbols=["XAUUSD"],
        max_records=max_records,
        window_days=window_days,
        sample_size=sample_size,
    )
