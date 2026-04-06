#!/usr/bin/env python3
"""Check progress of running permutation batch (fast version).

USAGE:
    python3 scripts/check_permutation_progress.py
    
    # Check specific run:
    python3 scripts/check_permutation_progress.py --run-id <uuid>
    
    # Auto-refresh every 30 seconds:
    python3 scripts/check_permutation_progress.py --watch
    
    # Show all running runs:
    python3 scripts/check_permutation_progress.py --all
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

# Add backend to path
BACKEND = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(BACKEND))


def load_checkpoint(run_id: str) -> dict | None:
    """Load checkpoint from JSON file."""
    checkpoint_path = Path(f"/tmp/permutation_checkpoints/permutation_progress_{run_id}.json")
    if not checkpoint_path.exists():
        return None
    try:
        with open(checkpoint_path) as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading checkpoint: {e}")
        return None


def find_checkpoints() -> list[Path]:
    """Find all checkpoint files."""
    checkpoint_dir = Path("/tmp/permutation_checkpoints")
    if not checkpoint_dir.exists():
        return []
    return sorted(checkpoint_dir.glob("permutation_progress_*.json"))


def format_duration(seconds: float) -> str:
    """Format seconds as human-readable duration."""
    if seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f}m"
    elif seconds < 86400:
        return f"{seconds/3600:.1f}h"
    else:
        return f"{seconds/86400:.1f}d"


def format_eta(seconds: float | None) -> str:
    """Format ETA."""
    if seconds is None:
        return "calculating..."
    return format_duration(seconds)


def print_progress(data: dict, detailed: bool = False) -> None:
    """Print progress in a formatted way."""
    run_id = data.get("run_id", "unknown")
    phase = data.get("phase", "unknown")
    overall_pct = data.get("model_pct", 0) * 0.1 + data.get("technical_pct", 0) * 0.9
    
    print(f"\n{'='*70}")
    print(f"Run ID: {run_id}")
    print(f"Phase: {phase.upper()}")
    print(f"{'='*70}")
    
    # Progress bars
    model_pct = data.get("model_pct", 0)
    tech_pct = data.get("technical_pct", 0)
    
    model_bar = "█" * int(model_pct / 5) + "░" * (20 - int(model_pct / 5))
    tech_bar = "█" * int(tech_pct / 5) + "░" * (20 - int(tech_pct / 5))
    
    print(f"\nModel:       [{model_bar}] {model_pct:.1f}% ({data.get('completed_model_contexts', 0)}/{data.get('total_model_contexts', 0)})")
    print(f"Technical:   [{tech_bar}] {tech_pct:.1f}% ({data.get('completed_technical_contexts', 0)}/{data.get('total_technical_contexts', 0)})")
    
    # Current context
    current = f"{data.get('current_symbol', '-')} {data.get('current_timeframe', '-')} {data.get('current_direction', '-')}"
    print(f"\nCurrent:     {current}")
    
    # Timing
    elapsed = data.get("elapsed_seconds", 0)
    eta = data.get("eta_seconds")
    print(f"\nElapsed:     {format_duration(elapsed)}")
    print(f"ETA:         {format_eta(eta)}")
    
    # Rows written
    print(f"\nModel rows:      {data.get('model_rows_written', 0)}")
    print(f"Technical rows:  {data.get('technical_rows_written', 0)}")
    
    # Config summary if detailed
    if detailed and "config" in data:
        config = data["config"]
        print(f"\n{'='*70}")
        print("CONFIGURATION")
        print(f"{'='*70}")
        print(f"Symbols: {config.get('symbols', [])}")
        print(f"Timeframes: {config.get('timeframes', [])}")
        print(f"Lookforward: {config.get('lookforward_grid', [])}")
        print(f"Target: {config.get('target_move_grid', [])}")
        print(f"Stop: {config.get('stop_move_grid', [])}")


def print_summary_table(checkpoints: list[Path]) -> None:
    """Print summary table of all checkpoints."""
    print(f"\n{'='*100}")
    print(f"{'RUN ID':<36} {'PHASE':<12} {'PROGRESS':<10} {'ELAPSED':<10} {'ETA':<12} {'ROWS'}")
    print(f"{'-'*100}")
    
    for cp_path in checkpoints:
        try:
            with open(cp_path) as f:
                data = json.load(f)
            
            run_id = data.get("run_id", "unknown")[:8]
            phase = data.get("phase", "unknown")[:11]
            
            model_pct = data.get("model_pct", 0)
            tech_pct = data.get("technical_pct", 0)
            overall = f"{model_pct*0.1 + tech_pct*0.9:.1f}%"
            
            elapsed = format_duration(data.get("elapsed_seconds", 0))
            eta = format_eta(data.get("eta_seconds"))
            
            model_rows = data.get("model_rows_written", 0)
            tech_rows = data.get("technical_rows_written", 0)
            rows = f"M:{model_rows} T:{tech_rows}"
            
            print(f"{run_id:<36} {phase:<12} {overall:<10} {elapsed:<10} {eta:<12} {rows}")
        except Exception:
            continue
    
    print(f"{'='*100}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Check permutation batch progress")
    parser.add_argument("--run-id", type=str, default=None, help="Specific run ID to check")
    parser.add_argument("--watch", action="store_true", help="Auto-refresh every 30 seconds")
    parser.add_argument("--all", action="store_true", help="Show all running runs (summary)")
    parser.add_argument("--detailed", action="store_true", help="Show detailed info")
    args = parser.parse_args()
    
    if args.all:
        checkpoints = find_checkpoints()
        if not checkpoints:
            print("\nNo checkpoint files found.")
            print(f"Checkpoint directory: /tmp/permutation_checkpoints/")
            print("\nNote: Progress tracking only works for 'fast' variant runs.")
            return
        print_summary_table(checkpoints)
        return
    
    if args.run_id:
        # Check specific run
        while True:
            data = load_checkpoint(args.run_id)
            if data is None:
                print(f"\nNo checkpoint found for run ID: {args.run_id}")
                print(f"Expected: /tmp/permutation_checkpoints/permutation_progress_{args.run_id}.json")
                return
            
            # Clear screen in watch mode
            if args.watch:
                print("\033[2J\033[H", end="")
            
            print_progress(data, detailed=args.detailed)
            
            if not args.watch:
                break
            
            if data.get("phase") in ("completed", "failed"):
                print(f"\n>>> Run {data.get('phase').upper()} <<<")
                break
            
            time.sleep(30)
    else:
        # Find most recent checkpoint
        checkpoints = find_checkpoints()
        if not checkpoints:
            print("\nNo checkpoint files found.")
            print(f"Checkpoint directory: /tmp/permutation_checkpoints/")
            print("\nRun a fast permutation batch first:")
            print("  python3 scripts/run_permutation_batch_fast.py")
            return
        
        # Load most recent
        most_recent = max(checkpoints, key=lambda p: p.stat().st_mtime)
        data = load_checkpoint(most_recent.stem.replace("permutation_progress_", ""))
        
        if data:
            print_progress(data, detailed=args.detailed)
        else:
            print(f"\nCould not load checkpoint: {most_recent}")


if __name__ == "__main__":
    main()
