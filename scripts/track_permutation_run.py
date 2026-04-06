#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from dotenv import load_dotenv

load_dotenv(BACKEND / ".env")

from database.supabase_client import get_supabase_client


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:
        return None


def load_checkpoint(run_id: str) -> dict:
    checkpoint_path = Path(f"/tmp/permutation_checkpoints/permutation_progress_{run_id}.json")
    if not checkpoint_path.exists():
        return {}
    try:
        return json.loads(checkpoint_path.read_text())
    except Exception:
        return {}


def format_duration(seconds: float | int | None) -> str:
    if seconds is None:
        return "calculating..."
    total_seconds = max(float(seconds), 0.0)
    if total_seconds < 60:
        return f"{int(total_seconds)}s"
    if total_seconds < 3600:
        return f"{total_seconds / 60:.1f}m"
    if total_seconds < 86400:
        return f"{total_seconds / 3600:.1f}h"
    return f"{total_seconds / 86400:.1f}d"


def get_run_record(client, run_id: str) -> dict:
    result = (
        client.table("permutation_batch_runs")
        .select("id,status,started_at,completed_at,error,summary,parameters")
        .eq("id", run_id)
        .limit(1)
        .execute()
    )
    data = result.get("data") or []
    return data[0] if data else {}


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, payload: dict) -> None:
    ensure_parent(path)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))


def write_text(path: Path, text: str) -> None:
    ensure_parent(path)
    path.write_text(text)


def build_snapshot(args: argparse.Namespace, run_record: dict, checkpoint: dict) -> dict:
    total_model_contexts = int(checkpoint.get("total_model_contexts") or 0)
    total_technical_contexts = int(checkpoint.get("total_technical_contexts") or 0)
    completed_model_contexts = int(checkpoint.get("completed_model_contexts") or 0)
    completed_technical_contexts = int(checkpoint.get("completed_technical_contexts") or 0)
    total_contexts = total_model_contexts + total_technical_contexts
    completed_contexts = completed_model_contexts + completed_technical_contexts
    percentage = (100.0 * completed_contexts / total_contexts) if total_contexts else 0.0
    eta_seconds = checkpoint.get("eta_seconds")
    last_heartbeat = checkpoint.get("last_heartbeat") or run_record.get("started_at")
    status = str(run_record.get("status") or ("running" if checkpoint else "starting"))
    phase = str(checkpoint.get("phase") or ("completed" if status == "completed" else "starting"))
    checkpoint_path = f"/tmp/permutation_checkpoints/permutation_progress_{args.run_id}.json"
    watch_command = f'while true; do clear; cat "{args.summary_out}"; sleep {args.watch_interval}; done'
    progress_watch_command = f'while true; do clear; cat "{args.progress_out}"; sleep {args.watch_interval}; done'
    raw_checkpoint_command = f"python3 scripts/check_permutation_progress.py --run-id {args.run_id} --watch"
    log_tail_command = f'tail -n 80 -f "{args.log_path}"'
    return {
        "label": args.label,
        "run_id": args.run_id,
        "source_model_run_id": args.source_model_run_id,
        "status": status,
        "phase": phase,
        "elapsed": format_duration(checkpoint.get("elapsed_seconds")),
        "eta": format_duration(eta_seconds),
        "total_contexts": total_contexts,
        "completed_contexts": completed_contexts,
        "percentage": round(percentage, 2),
        "current_symbol": checkpoint.get("current_symbol"),
        "current_timeframe": checkpoint.get("current_timeframe"),
        "current_direction": checkpoint.get("current_direction"),
        "model_reused": True,
        "model_rows_reused": int(checkpoint.get("model_rows_written") or 0),
        "technical_contexts_completed": completed_technical_contexts,
        "technical_contexts_total": total_technical_contexts,
        "technical_rows_written": int(checkpoint.get("technical_rows_written") or 0),
        "last_heartbeat": last_heartbeat,
        "checkpoint_path": checkpoint_path,
        "log_path": str(args.log_path),
        "progress_path": str(args.progress_out),
        "summary_path": str(args.summary_out),
        "watch_command": watch_command,
        "progress_watch_command": progress_watch_command,
        "raw_checkpoint_command": raw_checkpoint_command,
        "log_tail_command": log_tail_command,
        "results_tables": [
            "model_permutation_batch_results",
            "technical_permutation_batch_results",
        ],
        "error": run_record.get("error"),
    }


def build_summary_text(snapshot: dict) -> str:
    lines = [
        f"Label: {snapshot['label']}",
        f"New run id: {snapshot['run_id']}",
        f"Source model run id: {snapshot['source_model_run_id']}",
        f"Status: {snapshot['status']}",
        f"Phase: {snapshot['phase']}",
        f"Model reused: true",
        f"Model rows reused: {snapshot['model_rows_reused']}",
        f"Technical contexts completed: {snapshot['technical_contexts_completed']} / {snapshot['technical_contexts_total']}",
        f"Technical rows written: {snapshot['technical_rows_written']}",
        f"Last heartbeat: {snapshot['last_heartbeat']}",
        f"Approx progress: {snapshot['percentage']}% ({snapshot['completed_contexts']} / {snapshot['total_contexts']})",
        f"Approx remaining time: {snapshot['eta']}",
        f"Current context: {snapshot.get('current_symbol') or '-'} {snapshot.get('current_timeframe') or '-'} {snapshot.get('current_direction') or '-'}",
        "Results are written to: model_permutation_batch_results and technical_permutation_batch_results",
        f"Summary watch command: {snapshot['watch_command']}",
        f"Progress watch command: {snapshot['progress_watch_command']}",
        f"Raw checkpoint command: {snapshot['raw_checkpoint_command']}",
        f"Log tail command: {snapshot['log_tail_command']}",
    ]
    if snapshot.get("error"):
        lines.append(f"Error: {snapshot['error']}")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--source-model-run-id", required=True)
    parser.add_argument("--log-path", required=True)
    parser.add_argument("--progress-out", required=True)
    parser.add_argument("--summary-out", required=True)
    parser.add_argument("--watch-interval", type=int, default=15)
    args = parser.parse_args()

    args.log_path = Path(args.log_path).expanduser()
    args.progress_out = Path(args.progress_out).expanduser()
    args.summary_out = Path(args.summary_out).expanduser()

    client = get_supabase_client()
    if not client:
        raise SystemExit("No Supabase client available")

    while True:
        run_record = get_run_record(client, args.run_id)
        checkpoint = load_checkpoint(args.run_id)
        snapshot = build_snapshot(args, run_record, checkpoint)
        write_json(args.progress_out, snapshot)
        write_text(args.summary_out, build_summary_text(snapshot))
        if snapshot["status"] in {"completed", "failed"}:
            break
        time.sleep(args.watch_interval)


if __name__ == "__main__":
    main()
