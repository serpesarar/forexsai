"""
Mark AI-Ops proposals generated BEFORE the pre-entry wick leak fix as stale.

The lifecycle leak (commit 32033c6, 2026-05-19) inflated `highest_profit_pips`
on NDX/GDAXI/USOIL signals — pre-entry candle wicks were being credited as TP
hits within seconds. Any proposal whose simulator pulled win-rate or net-pnl
from data spanning that leak window is untrustworthy.

This script marks pending proposals as 'stale_pre_leak_fix' so the UI can
filter them out, while preserving the audit trail. New proposals generated
after the cutoff date will reflect the honest, post-fix distribution.

Usage (run on Railway shell or any env with backend creds):
    python -m backend.scripts.mark_stale_proposals --dry-run
    python -m backend.scripts.mark_stale_proposals --apply

Cutoff defaults to 2026-05-19T00:00:00Z (lifecycle fix deploy date).
"""
from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("mark_stale_proposals")

DEFAULT_CUTOFF_ISO = "2026-05-19T00:00:00+00:00"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cutoff", default=DEFAULT_CUTOFF_ISO,
                    help="ISO timestamp; proposals older than this are stale")
    ap.add_argument("--apply", action="store_true",
                    help="Actually write the update (default: dry-run)")
    ap.add_argument("--include-approved", action="store_true",
                    help="Also mark status='approved' proposals (default: pending only)")
    args = ap.parse_args()

    try:
        cutoff = datetime.fromisoformat(args.cutoff.replace("Z", "+00:00"))
    except ValueError:
        logger.error("bad --cutoff: %s", args.cutoff)
        sys.exit(1)

    try:
        from database.supabase_client import get_supabase_client
    except ImportError:
        # Allow running from project root
        sys.path.insert(0, ".")
        from backend.database.supabase_client import get_supabase_client  # type: ignore

    client = get_supabase_client()

    target_statuses = ["pending"]
    if args.include_approved:
        target_statuses.append("approved")

    q = client.table("improvement_proposals").select(
        "id,proposal_type,status,created_at,symbol,model_type"
    ).in_("status", target_statuses).lt("created_at", cutoff.isoformat())
    res = q.execute()
    rows = res.data if hasattr(res, "data") else (res.get("data") or [])

    if not rows:
        logger.info("No stale proposals to mark (cutoff=%s, statuses=%s)",
                    cutoff.isoformat(), target_statuses)
        return

    logger.info("Found %d stale proposals (cutoff %s):", len(rows), cutoff.isoformat())
    by_type: dict[str, int] = {}
    for r in rows:
        t = r.get("proposal_type") or "unknown"
        by_type[t] = by_type.get(t, 0) + 1
    for t, n in sorted(by_type.items(), key=lambda kv: -kv[1]):
        logger.info("  %-25s %d", t, n)

    if not args.apply:
        logger.info("DRY-RUN — pass --apply to write the update.")
        return

    ids = [r["id"] for r in rows]
    BATCH = 100
    updated = 0
    for i in range(0, len(ids), BATCH):
        chunk = ids[i:i + BATCH]
        upd = client.table("improvement_proposals").update({
            "status": "stale_pre_leak_fix",
            "review_notes": (
                "Auto-marked stale: simulator metrics derived from "
                "pre-2026-05-19 prediction_logs containing pre-entry wick "
                "TP-hit contamination (lifecycle leak fix commit 32033c6). "
                "Win-rate / net-pnl claims should be re-evaluated against "
                "post-fix data before approval."
            ),
        }).in_("id", chunk).execute()
        n = len(upd.data) if hasattr(upd, "data") and upd.data else len(chunk)
        updated += n
        logger.info("  marked %d/%d", updated, len(ids))

    logger.info("Done — %d proposals moved to 'stale_pre_leak_fix'.", updated)


if __name__ == "__main__":
    main()
