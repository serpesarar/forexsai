"""
Pattern Mining Service — self-feeding weekly pipeline.

Wraps xauusdegitim/pattern_miner.py for use inside FastAPI:
  - Weekly cron in main.py lifespan calls run_weekly_mining()
  - Persists rules to BOTH file (xauusdegitim/pattern_rules.json — for fast
    runtime matcher access) AND Supabase (pattern_mining_runs table — for
    redeploy resilience and history)
  - On startup, if local file is missing, restore_from_supabase() pulls the
    latest run and writes it back to disk
  - Manual trigger endpoint also routes here

This way the user never has to manually run pattern_miner.py — the system
self-feeds and survives Railway container restarts without losing rules.
"""
from __future__ import annotations

import asyncio
import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Make xauusdegitim/ importable
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_RESEARCH_DIR = _PROJECT_ROOT / "xauusdegitim"
if str(_RESEARCH_DIR) not in sys.path:
    sys.path.insert(0, str(_RESEARCH_DIR))

# Local file path the matcher reads from
RULES_PATH = _RESEARCH_DIR / "pattern_rules.json"

# Cron cadence
WEEKLY_INTERVAL_SECONDS = 7 * 24 * 3600
INITIAL_DELAY_SECONDS = 60 * 30   # wait 30 min after startup


# ---------------------------------------------------------------------------
# Supabase persistence
# ---------------------------------------------------------------------------

async def _persist_to_supabase(summary: dict, triggered_by: str = "cron",
                                 duration_seconds: float = 0.0) -> Optional[str]:
    """Write a row to pattern_mining_runs. Returns the row id or None on failure."""
    try:
        from database.supabase_client import get_supabase_client, is_db_available
    except ImportError:
        return None
    if not is_db_available():
        return None
    client = get_supabase_client()
    if client is None:
        return None
    try:
        payload = {
            "generated_at": summary.get("generated_at") or datetime.now(timezone.utc).isoformat(),
            "window_days": summary.get("days", 60),
            "total_signals": summary.get("total_signals", 0),
            "rules_count": summary.get("rules_count", 0),
            "winning_count": summary.get("winning_count", 0),
            "avoid_count": summary.get("avoid_count", 0),
            "segments_count": summary.get("segments_count", 0),
            "rules": summary.get("rules", []),
            "triggered_by": triggered_by,
            "status": summary.get("status", "completed"),
            "duration_seconds": round(duration_seconds, 2),
        }
        result = client.table("pattern_mining_runs").insert(payload)
        data = result.get("data") if isinstance(result, dict) else getattr(result, "data", None)
        if data:
            return data[0].get("id")
    except Exception as e:
        logger.exception("[pattern_mining] supabase persist failed: %s", e)
    return None


async def restore_from_supabase() -> bool:
    """If the local rules file is missing or empty, restore the most recent run.
    Called once at startup. Returns True if a restore happened."""
    if RULES_PATH.exists() and RULES_PATH.stat().st_size > 100:
        return False
    try:
        from database.supabase_client import get_supabase_client, is_db_available
    except ImportError:
        return False
    if not is_db_available():
        return False
    client = get_supabase_client()
    if client is None:
        return False
    try:
        result = client.table("pattern_mining_runs").select(
            "generated_at,window_days,total_signals,rules,rules_count"
        ).eq("status", "completed").order("generated_at", desc=True).limit(1)
        data = result.get("data") if isinstance(result, dict) else getattr(result, "data", []) or []
        if not data:
            logger.info("[pattern_mining] no historical run in Supabase to restore")
            return False
        row = data[0]
        rules_payload = {
            "generated_at": row.get("generated_at"),
            "days": row.get("window_days"),
            "total_signals": row.get("total_signals"),
            "rules": row.get("rules") or [],
        }
        RULES_PATH.parent.mkdir(parents=True, exist_ok=True)
        RULES_PATH.write_text(json.dumps(rules_payload, indent=2, default=str))
        logger.info(f"[pattern_mining] restored {row.get('rules_count')} rules from Supabase "
                    f"(generated_at={row.get('generated_at')})")
        # Force matcher to reload
        try:
            from services.pattern_matcher import reload_rules
            reload_rules()
        except Exception:
            pass
        return True
    except Exception as e:
        logger.exception("[pattern_mining] restore failed: %s", e)
        return False


# ---------------------------------------------------------------------------
# Mining runner
# ---------------------------------------------------------------------------

async def run_mining_now(days: int = 60, triggered_by: str = "manual") -> dict:
    """Execute BOTH mining cycles: signal-based (pattern_miner) AND chart-based
    (price_action_miner). Persists each. Returns combined summary."""
    started = time.monotonic()
    combined: dict = {"signal": {}, "chart": {}}
    loop = asyncio.get_running_loop()

    # === Signal-based pattern miner ===
    try:
        import pattern_miner  # type: ignore
        combined["signal"] = await loop.run_in_executor(
            None,
            lambda: pattern_miner.run_mining(
                days=days, write_files=True, verbose=False
            ),
        )
    except Exception as e:
        logger.exception("[pattern_mining] signal miner failed: %s", e)
        combined["signal"] = {"status": "error", "error": str(e), "rules_count": 0, "rules": []}

    # === Chart-based price action miner (model-independent) ===
    try:
        import price_action_miner  # type: ignore
        combined["chart"] = await loop.run_in_executor(
            None,
            lambda: price_action_miner.run_chart_mining(
                symbols=["XAUUSD", "NDX.INDX", "GDAXI.INDX", "USOIL.FOREX"],
                timeframes=["5m", "15m", "30m", "1h"],
                days=days, write_files=True,
            ),
        )
    except Exception as e:
        logger.exception("[pattern_mining] chart miner failed: %s", e)
        combined["chart"] = {"status": "error", "error": str(e), "rules_count": 0, "rules": []}

    duration = time.monotonic() - started
    total_rules = (combined["signal"].get("rules_count") or 0) + (combined["chart"].get("rules_count") or 0)

    # Compose flat summary (Supabase row uses signal-based stats; full results are logged)
    summary: dict = {
        "status": "ok" if total_rules > 0 else "no_rules",
        "duration_seconds": round(duration, 2),
        "rules_count": total_rules,
        "signal_rules": combined["signal"].get("rules_count", 0),
        "chart_rules": combined["chart"].get("rules_count", 0),
        "generated_at": combined["signal"].get("generated_at") or datetime.now(timezone.utc).isoformat(),
        "days": days,
        "total_signals": combined["signal"].get("total_signals", 0),
        "winning_count": combined["signal"].get("winning_count", 0),
        "avoid_count": combined["signal"].get("avoid_count", 0),
        "segments_count": combined["signal"].get("segments_count", 0),
        # Persist all rules for cross-restart restoration. Chart rules included.
        "rules": (combined["signal"].get("rules") or []) + (combined["chart"].get("rules") or []),
    }

    # Persist to Supabase
    row_id = await _persist_to_supabase(summary, triggered_by=triggered_by,
                                         duration_seconds=duration)
    if row_id:
        summary["supabase_run_id"] = row_id

    # Trigger matcher reload — picks up BOTH JSON files
    try:
        from services.pattern_matcher import reload_rules
        reloaded = reload_rules()
        summary["matcher_rules_loaded"] = reloaded
    except Exception as e:
        logger.warning("[pattern_mining] matcher reload failed: %s", e)

    logger.info(f"[pattern_mining] {triggered_by} run done: signal={summary['signal_rules']} "
                f"chart={summary['chart_rules']} total={total_rules}, {duration:.1f}s")
    return summary


# ---------------------------------------------------------------------------
# Weekly cron loop
# ---------------------------------------------------------------------------

async def weekly_loop() -> None:
    """Self-feeding weekly cron. Started from main.py lifespan."""
    # Initial delay: let other startup tasks settle, then run a fresh mining cycle
    # so newly-deployed instances have current rules within ~30 minutes.
    await asyncio.sleep(INITIAL_DELAY_SECONDS)
    try:
        await restore_from_supabase()
    except Exception:
        pass
    while True:
        try:
            summary = await run_mining_now(days=60, triggered_by="cron")
            logger.info("[pattern_mining] weekly cycle complete: %s",
                        {k: v for k, v in summary.items() if k != "rules"})
        except Exception as e:
            logger.exception("[pattern_mining] weekly cycle failed: %s", e)
        # Sleep until next week
        await asyncio.sleep(WEEKLY_INTERVAL_SECONDS)


# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------

async def get_status() -> dict:
    """For the frontend status badge."""
    out: dict = {"local_file_exists": RULES_PATH.exists()}
    if RULES_PATH.exists():
        try:
            data = json.loads(RULES_PATH.read_text())
            out["local_generated_at"] = data.get("generated_at")
            out["local_rules_count"] = len(data.get("rules") or [])
            out["local_window_days"] = data.get("days")
        except Exception:
            pass
    # Latest Supabase run
    try:
        from database.supabase_client import get_supabase_client, is_db_available
        if is_db_available():
            client = get_supabase_client()
            if client is not None:
                r = client.table("pattern_mining_runs").select(
                    "id,generated_at,rules_count,winning_count,avoid_count,"
                    "total_signals,window_days,triggered_by,duration_seconds,status"
                ).order("generated_at", desc=True).limit(5)
                data = r.get("data") if isinstance(r, dict) else getattr(r, "data", []) or []
                out["recent_runs"] = data
                if data:
                    out["latest_run"] = data[0]
    except Exception as e:
        out["status_error"] = str(e)[:200]
    return out
