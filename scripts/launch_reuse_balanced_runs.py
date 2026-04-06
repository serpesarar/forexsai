#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from dotenv import load_dotenv

load_dotenv(BACKEND / ".env")

from database.supabase_client import get_supabase_client

OUTPUT_DIR = Path("~/Desktop/permutation_runs").expanduser()
TRACKER_SCRIPT = ROOT / "scripts" / "track_permutation_run.py"
RUNNER_SCRIPT = ROOT / "scripts" / "run_permutation_batch_fast.py"
MANIFEST_PATH = OUTPUT_DIR / "reuse_balanced_runs_manifest.json"

SYMBOLS = "NDX.INDX,XAUUSD,GDAXI.INDX,USOIL.FOREX"
DIRECTIONS = "BUY,SELL"
TIMEFRAMES = "5m,15m,30m,1h,4h,eod"
WATCH_INTERVAL = 15
RUN_ID_DISCOVERY_TIMEOUT_SECONDS = 120
RUN_ID_DISCOVERY_POLL_SECONDS = 3


@dataclass(frozen=True)
class LaunchJob:
    label: str
    source_model_run_id: str
    model_lookback_days: int
    model_min_occurrences: int
    cluster_window_minutes: int

    @property
    def log_path(self) -> Path:
        return OUTPUT_DIR / f"{self.label}.log"

    @property
    def progress_path(self) -> Path:
        return OUTPUT_DIR / f"{self.label}_progress.json"

    @property
    def summary_path(self) -> Path:
        return OUTPUT_DIR / f"{self.label}_summary.txt"


JOBS = [
    LaunchJob(
        label="reuse_7eb_balanced",
        source_model_run_id="7eb45c1d-a4be-4837-8b2e-26455a954cba",
        model_lookback_days=240,
        model_min_occurrences=4,
        cluster_window_minutes=10,
    ),
    LaunchJob(
        label="reuse_dc65_balanced",
        source_model_run_id="dc65184e-be7b-4786-88c0-12c177aada8b",
        model_lookback_days=365,
        model_min_occurrences=3,
        cluster_window_minutes=10,
    ),
]


def ensure_output_dir() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:
        return None


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_running_runs(client) -> list[dict[str, Any]]:
    result = (
        client.table("permutation_batch_runs")
        .select("id,status,started_at,parameters,summary")
        .order("started_at", desc=True)
        .limit(50)
        .execute()
    )
    return result.get("data") or []


def find_run_id(client, job: LaunchJob, launched_after: datetime) -> str:
    deadline = time.time() + RUN_ID_DISCOVERY_TIMEOUT_SECONDS
    while time.time() < deadline:
        for row in get_running_runs(client):
            params = row.get("parameters") or {}
            if params.get("reuse_model_run_id") != job.source_model_run_id:
                continue
            if not params.get("skip_model_stage"):
                continue
            started_at = parse_datetime(row.get("started_at"))
            if not started_at:
                continue
            if started_at >= launched_after - timedelta(seconds=5):
                return str(row["id"])
        time.sleep(RUN_ID_DISCOVERY_POLL_SECONDS)
    raise RuntimeError(f"Could not discover new run_id for {job.label}")


def build_run_command(job: LaunchJob) -> list[str]:
    return [
        sys.executable,
        str(RUNNER_SCRIPT),
        "--preset",
        "balanced",
        "--symbols",
        SYMBOLS,
        "--directions",
        DIRECTIONS,
        "--timeframes",
        TIMEFRAMES,
        "--model-lookback-days",
        str(job.model_lookback_days),
        "--model-min-occurrences",
        str(job.model_min_occurrences),
        "--cluster-window-minutes",
        str(job.cluster_window_minutes),
        "--reuse-model-run-id",
        job.source_model_run_id,
        "--skip-model-stage",
    ]


def build_tracker_command(job: LaunchJob, run_id: str) -> list[str]:
    return [
        sys.executable,
        str(TRACKER_SCRIPT),
        "--label",
        job.label,
        "--run-id",
        run_id,
        "--source-model-run-id",
        job.source_model_run_id,
        "--log-path",
        str(job.log_path),
        "--progress-out",
        str(job.progress_path),
        "--summary-out",
        str(job.summary_path),
        "--watch-interval",
        str(WATCH_INTERVAL),
    ]


def launch_detached(command: list[str], log_path: Path) -> int:
    ensure_output_dir()
    with open(log_path, "a") as log_file:
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        process = subprocess.Popen(
            command,
            cwd=str(ROOT),
            stdout=log_file,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
            env=env,
        )
        return int(process.pid)


def write_initial_progress(job: LaunchJob, run_id: str) -> None:
    initial_payload = {
        "label": job.label,
        "run_id": run_id,
        "source_model_run_id": job.source_model_run_id,
        "status": "running",
        "phase": "starting",
        "elapsed": "0s",
        "eta": "calculating...",
        "total_contexts": 0,
        "completed_contexts": 0,
        "percentage": 0.0,
        "current_symbol": None,
        "current_timeframe": None,
        "current_direction": None,
        "model_reused": True,
        "log_path": str(job.log_path),
        "progress_path": str(job.progress_path),
        "summary_path": str(job.summary_path),
    }
    job.progress_path.write_text(json.dumps(initial_payload, indent=2, ensure_ascii=False))
    job.summary_path.write_text(
        "\n".join(
            [
                f"Label: {job.label}",
                f"New run id: {run_id}",
                f"Source model run id: {job.source_model_run_id}",
                "Status: running",
                "Phase: starting",
                "Model reused: true",
                f"Log file: {job.log_path}",
                f"Progress file: {job.progress_path}",
                f"Summary file: {job.summary_path}",
            ]
        )
        + "\n"
    )


def manifest_entry(job: LaunchJob, run_id: str, run_pid: int, tracker_pid: int) -> dict[str, Any]:
    return {
        "label": job.label,
        "run_id": run_id,
        "source_model_run_id": job.source_model_run_id,
        "run_pid": run_pid,
        "tracker_pid": tracker_pid,
        "log_path": str(job.log_path),
        "progress_path": str(job.progress_path),
        "summary_path": str(job.summary_path),
        "summary_watch_command": f'while true; do clear; cat "{job.summary_path}"; sleep {WATCH_INTERVAL}; done',
        "progress_watch_command": f'while true; do clear; cat "{job.progress_path}"; sleep {WATCH_INTERVAL}; done',
        "log_tail_command": f'tail -n 80 -f "{job.log_path}"',
        "raw_checkpoint_command": f"python3 scripts/check_permutation_progress.py --run-id {run_id} --watch",
    }


def print_report(entries: list[dict[str, Any]]) -> None:
    print("=" * 100)
    print("NEW BALANCED REUSE RUNS STARTED")
    print("=" * 100)
    for entry in entries:
        print(f"Label: {entry['label']}")
        print(f"  New run_id: {entry['run_id']}")
        print(f"  Source model run: {entry['source_model_run_id']}")
        print(f"  Log: {entry['log_path']}")
        print(f"  Progress: {entry['progress_path']}")
        print(f"  Summary: {entry['summary_path']}")
        print(f"  Summary watch: {entry['summary_watch_command']}")
        print(f"  Progress watch: {entry['progress_watch_command']}")
        print(f"  Log tail: {entry['log_tail_command']}")
        print(f"  Raw checkpoint watch: {entry['raw_checkpoint_command']}")
        print("-" * 100)
    print(f"Manifest: {MANIFEST_PATH}")


def main() -> None:
    ensure_output_dir()
    client = get_supabase_client()
    if not client:
        raise SystemExit("No Supabase client available")

    manifest: dict[str, Any] = {
        "created_at": iso_now(),
        "output_dir": str(OUTPUT_DIR),
        "jobs": [],
    }
    entries: list[dict[str, Any]] = []

    for job in JOBS:
        launched_after = datetime.now(timezone.utc)
        run_pid = launch_detached(build_run_command(job), job.log_path)
        run_id = find_run_id(client, job, launched_after)
        write_initial_progress(job, run_id)
        tracker_log_path = OUTPUT_DIR / f"{job.label}_tracker.log"
        tracker_pid = launch_detached(build_tracker_command(job, run_id), tracker_log_path)
        entry = manifest_entry(job, run_id, run_pid, tracker_pid)
        entry["tracker_log_path"] = str(tracker_log_path)
        entries.append(entry)
        manifest["jobs"].append(entry)
        time.sleep(2)

    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    print_report(entries)


if __name__ == "__main__":
    main()
