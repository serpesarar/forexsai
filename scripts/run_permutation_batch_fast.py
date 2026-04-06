#!/usr/bin/env python3
"""Fast permutation batch runner - optimized for 1-2 day completion.

USAGE:
    python3 scripts/run_permutation_batch_fast.py
    
    # Or with custom parameters:
    python3 scripts/run_permutation_batch_fast.py \
        --symbols NDX.INDX XAUUSD \
        --lookforward-grid 5 8 \
        --target-grid 0.3 0.5 \
        --max-atomic-rules 20 \
        --top-results 200 \
        --walk-forward-splits 2

This is a SAFE COPY that does not interfere with running original runs.
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Add backend to path
BACKEND = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(BACKEND))

from services.permutation_batch_service_fast import (
    PermutationBatchConfigFast,
    run_permutation_batch_fast,
    get_balanced_preset,
    get_quality_preset,
    get_ultra_fast_preset,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S"
)


def parse_int_grid(s: str) -> list[int]:
    return [int(x) for x in s.split(",")]


def parse_float_grid(s: str) -> list[float]:
    return [float(x) for x in s.split(",")]


def parse_multi_value_args(values: list[str] | None) -> tuple[str, ...] | None:
    if not values:
        return None
    parsed: list[str] = []
    for value in values:
        parsed.extend(part.strip() for part in str(value).split(",") if part.strip())
    return tuple(parsed) if parsed else None


def print_preset_info():
    """Print detailed preset comparison."""
    print("\n" + "=" * 80)
    print("PRESET COMPARISON - Quality-First Fast Permutation")
    print("=" * 80)
    
    presets = {
        "ultra-fast": get_ultra_fast_preset(),
        "balanced": get_balanced_preset(),
        "quality": get_quality_preset(),
    }
    
    for name, cfg in presets.items():
        lf = cfg.lookforward_grid if cfg.lookforward_grid else (cfg.lookforward_candles,)
        tp = cfg.target_move_grid if cfg.target_move_grid else (cfg.target_move_pct,)
        sl = cfg.stop_move_grid if cfg.stop_move_grid else (cfg.stop_move_pct,)
        
        # Calculate theoretical contexts
        symbols = 4
        timeframes = 4
        directions = 2
        contexts = symbols * timeframes * directions * len(lf) * len(tp) * len(sl)
        
        print(f"\n{name.upper()}:")
        print(f"  Grid: {len(lf)}×{len(tp)}×{len(sl)} = {len(lf)*len(tp)*len(sl)} profiles per direction")
        print(f"  Technical contexts: {contexts}")
        print(f"  Atomic rules: {cfg.max_atomic_rules}")
        print(f"  Combo size: {cfg.max_combination_size}")
        print(f"  Top results: {cfg.top_results_per_context}")
        print(f"  Walk-forward: {cfg.walk_forward_splits} splits, {cfg.walk_forward_top_candidates} candidates")
        print(f"  Pruning: atomic≥{cfg.min_atomic_rule_win_rate:.0%}, combo≥{cfg.min_combo_win_rate:.0%}")
        
        if name == "ultra-fast":
            print(f"  ⏱  Estimated: 4-8 hours | Quality: Minimal but functional")
        elif name == "balanced":
            print(f"  ⏱  Estimated: 1-2 days | Quality: Good coverage, RECOMMENDED")
        elif name == "quality":
            print(f"  ⏱  Estimated: 2-3 days | Quality: Higher depth, more comprehensive")
    
    print("\n" + "=" * 80)
    print("")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Quality-first fast permutation batch runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXAMPLES:
  # List all presets with details:
  python3 scripts/run_permutation_batch_fast.py --list-presets
  
  # Run with balanced preset (RECOMMENDED):
  python3 scripts/run_permutation_batch_fast.py --preset balanced
  
  # Run with quality preset (more thorough):
  python3 scripts/run_permutation_batch_fast.py --preset quality
  
  # Run ultra-fast (minimal):
  python3 scripts/run_permutation_batch_fast.py --preset ultra-fast
  
  # Override specific parameters:
  python3 scripts/run_permutation_batch_fast.py --preset balanced --max-atomic-rules 36
  
  # Dry run (don't write to DB):
  python3 scripts/run_permutation_batch_fast.py --preset balanced --dry-run

PROGRESS TRACKING:
  # View all running:
  python3 scripts/check_permutation_progress.py --all
  
  # Watch specific run:
  python3 scripts/check_permutation_progress.py --run-id <uuid> --watch
        """
    )
    
    # Preset selection
    parser.add_argument("--preset", type=str, choices=["balanced", "quality", "ultra-fast"],
                        default="balanced", help="Configuration preset (default: balanced)")
    parser.add_argument("--list-presets", action="store_true",
                        help="Show detailed preset comparison and exit")
    parser.add_argument("--symbols", nargs="+", default=None,
                        help="Symbols to analyze (default: NDX.INDX XAUUSD GDAXI.INDX USOIL.FOREX)")
    parser.add_argument("--timeframes", nargs="+", default=None,
                        help="Timeframes (default: 5m 30m 1h eod)")
    parser.add_argument("--directions", nargs="+", default=None,
                        help="Directions (default: BUY SELL)")
    
    # Grid parameters (main cost drivers)
    parser.add_argument("--lookforward-grid", type=parse_int_grid, default=None,
                        help="Lookforward candles grid, comma-separated (default: 5,8,13)")
    parser.add_argument("--target-grid", type=parse_float_grid, default=None,
                        help="Target move %% grid, comma-separated (default: 0.3,0.5,0.8)")
    parser.add_argument("--stop-grid", type=parse_float_grid, default=None,
                        help="Stop move %% grid, comma-separated (default: 0.3,0.5,0.8)")
    
    # Atomic rule limits
    parser.add_argument("--max-atomic-rules", type=int, default=None,
                        help="Max atomic rules per context (default: 24)")
    parser.add_argument("--top-thresholds-per-indicator", type=int, default=None,
                        help="Top thresholds to keep per indicator (default: 4)")
    
    # Combination limits
    parser.add_argument("--max-combination-size", type=int, default=None,
                        help="Max combination size (default: 4)")
    parser.add_argument("--top-results", type=int, default=None,
                        help="Top results per context (default: 300)")
    
    # Walk-forward limits
    parser.add_argument("--walk-forward-splits", type=int, default=None,
                        help="Walk-forward splits (default: 2, set 0 to disable)")
    parser.add_argument("--walk-forward-top-candidates", type=int, default=None,
                        help="Top candidates per fold (default: 15)")
    
    # Data limits
    parser.add_argument("--technical-candle-limit", type=int, default=None,
                        help="Max candles to load (default: 5000)")
    parser.add_argument("--technical-min-occurrences", type=int, default=None,
                        help="Min occurrences for valid rules (default: 40)")
    
    # Model parameters
    parser.add_argument("--model-lookback-days", type=int, default=None,
                        help="Model lookback days (default: 180)")
    parser.add_argument("--model-min-occurrences", type=int, default=None,
                        help="Model min occurrences (default: preset value)")
    parser.add_argument("--cluster-window-minutes", type=int, default=None,
                        help="Model cluster window minutes (default: preset value)")
    
    # Progress tracking
    parser.add_argument("--progress-interval", type=int, default=10,
                        help="Log progress every N contexts (default: 10)")
    parser.add_argument("--flush-interval", type=int, default=20,
                        help="Flush to DB every N contexts (default: 20)")
    
    # Pruning thresholds
    parser.add_argument("--min-atomic-win-rate", type=float, default=None,
                        help="Min win rate for atomic rules (0.0-1.0)")
    parser.add_argument("--min-combo-win-rate", type=float, default=None,
                        help="Min win rate for combinations (0.0-1.0)")
    
    # Other
    parser.add_argument("--dry-run", action="store_true",
                        help="Dry run - don't write to database")
    parser.add_argument("--skip-model-stage", action="store_true",
                        help="Skip model stage and run technical stage only")
    parser.add_argument("--reuse-model-run-id", type=str, default=None,
                        help="Copy model rows from an existing run into the new fast run, then skip model analysis")
    parser.add_argument("--resume-run-id", type=str, default=None,
                        help="Resume an interrupted fast run using its existing run_id and checkpoint/DB progress")
    parser.add_argument("--allow-model-reuse-mismatch", action="store_true",
                        help="Allow model reuse even if source run model parameters differ from current config")
    
    args = parser.parse_args()
    
    # List presets if requested
    if args.list_presets:
        print_preset_info()
        sys.exit(0)
    
    # Get base config from preset
    if args.preset == "balanced":
        config = get_balanced_preset()
        preset_name = "BALANCED (recommended)"
    elif args.preset == "quality":
        config = get_quality_preset()
        preset_name = "QUALITY (higher quality)"
    elif args.preset == "ultra-fast":
        config = get_ultra_fast_preset()
        preset_name = "ULTRA-FAST (minimal)"
    else:
        config = get_balanced_preset()
        preset_name = "BALANCED (default)"

    parsed_symbols = parse_multi_value_args(args.symbols)
    parsed_timeframes = parse_multi_value_args(args.timeframes)
    parsed_directions = parse_multi_value_args(args.directions)
    
    # Apply overrides
    if parsed_symbols:
        config.symbols = parsed_symbols
    if parsed_timeframes:
        config.technical_timeframes = parsed_timeframes
    if parsed_directions:
        config.directions = parsed_directions
    if args.lookforward_grid:
        config.lookforward_grid = tuple(args.lookforward_grid)
    if args.target_grid:
        config.target_move_grid = tuple(args.target_grid)
    if args.stop_grid:
        config.stop_move_grid = tuple(args.stop_grid)
    if args.max_atomic_rules is not None:
        config.max_atomic_rules = args.max_atomic_rules
    if args.top_thresholds_per_indicator is not None:
        config.top_thresholds_per_indicator = args.top_thresholds_per_indicator
    if args.max_combination_size is not None:
        config.max_combination_size = args.max_combination_size
    if args.top_results is not None:
        config.top_results_per_context = args.top_results
    if args.walk_forward_splits is not None:
        config.walk_forward_splits = args.walk_forward_splits
    if args.walk_forward_top_candidates is not None:
        config.walk_forward_top_candidates = args.walk_forward_top_candidates
    if args.technical_candle_limit is not None:
        config.technical_candle_limit = args.technical_candle_limit
    if args.technical_min_occurrences is not None:
        config.technical_min_occurrences = args.technical_min_occurrences
    if args.model_lookback_days is not None:
        config.model_lookback_days = args.model_lookback_days
    if args.model_min_occurrences is not None:
        config.model_min_occurrences = args.model_min_occurrences
    if args.cluster_window_minutes is not None:
        config.cluster_window_minutes = args.cluster_window_minutes
    if args.progress_interval is not None:
        config.progress_log_interval = args.progress_interval
    if args.flush_interval is not None:
        config.flush_interval = args.flush_interval
    if args.min_atomic_win_rate is not None:
        config.min_atomic_rule_win_rate = args.min_atomic_win_rate
    if args.min_combo_win_rate is not None:
        config.min_combo_win_rate = args.min_combo_win_rate
    config.skip_model_stage = args.skip_model_stage
    config.reuse_model_run_id = args.reuse_model_run_id
    config.resume_run_id = args.resume_run_id
    config.allow_model_reuse_mismatch = args.allow_model_reuse_mismatch
    
    config.dry_run = args.dry_run
    
    # Calculate theoretical workload
    symbols = config.symbols
    directions = config.directions
    timeframes = config.technical_timeframes
    lf_grid = config.lookforward_grid if config.lookforward_grid else (config.lookforward_candles,)
    tp_grid = config.target_move_grid if config.target_move_grid else (config.target_move_pct,)
    sl_grid = config.stop_move_grid if config.stop_move_grid else (config.stop_move_pct,)
    
    model_contexts = len(symbols) * len(directions)
    technical_contexts = len(symbols) * len(timeframes) * len(directions) * len(lf_grid) * len(tp_grid) * len(sl_grid)
    
    # Print configuration
    print("\n" + "=" * 80)
    print(f"PERMUTATION BATCH FAST - {preset_name}")
    print("=" * 80)
    print(f"Symbols: {symbols}")
    print(f"Timeframes: {timeframes}")
    print(f"Directions: {directions}")
    print(f"Lookforward grid: {lf_grid} ({len(lf_grid)} values)")
    print(f"Target grid: {tp_grid} ({len(tp_grid)} values)")
    print(f"Stop grid: {sl_grid} ({len(sl_grid)} values)")
    print("-" * 80)
    print(f"Grid combinations per direction: {len(lf_grid)} × {len(tp_grid)} × {len(sl_grid)} = {len(lf_grid) * len(tp_grid) * len(sl_grid)}")
    print(f"Model contexts: {model_contexts}")
    print(f"Technical contexts: {technical_contexts}")
    print(f"Total theoretical contexts: {model_contexts + technical_contexts}")
    print("-" * 80)
    print(f"Max atomic rules: {config.max_atomic_rules}")
    print(f"Max combination size: {config.max_combination_size}")
    print(f"Top results per context: {config.top_results_per_context}")
    print(f"Walk-forward splits: {config.walk_forward_splits}")
    print(f"Walk-forward top candidates: {config.walk_forward_top_candidates}")
    print(f"Atomic win rate threshold: {config.min_atomic_rule_win_rate:.0%}")
    print(f"Combo win rate threshold: {config.min_combo_win_rate:.0%}")
    print(f"Model lookback days: {config.model_lookback_days}")
    print(f"Model min occurrences: {config.model_min_occurrences}")
    print(f"Cluster window minutes: {config.cluster_window_minutes}")
    print("-" * 80)
    print(f"Progress log interval: every {config.progress_log_interval} contexts")
    print(f"DB flush interval: every {config.flush_interval} contexts")
    print(f"Skip model stage: {config.skip_model_stage}")
    print(f"Reuse model run ID: {config.reuse_model_run_id}")
    print(f"Resume run ID: {config.resume_run_id}")
    print(f"Allow model reuse mismatch: {config.allow_model_reuse_mismatch}")
    print(f"Dry run: {config.dry_run}")
    print("=" * 80)
    print("")
    
    # Run
    result = asyncio.run(run_permutation_batch_fast(config))
    
    # Print summary
    print("\n" + "=" * 80)
    print("RESULT SUMMARY")
    print("=" * 80)
    print(f"Success: {result.get('success')}")
    print(f"Run ID: {result.get('run_id')}")
    print(f"Model contexts: {result.get('model_contexts')}")
    print(f"Model rows: {result.get('model_rows')}")
    print(f"Technical contexts: {result.get('technical_contexts')}")
    print(f"Technical rows: {result.get('technical_rows')}")
    print(f"Skipped contexts: {len(result.get('technical_skipped', []))}")
    
    if result.get('error'):
        print(f"ERROR: {result.get('error')}")
    
    # Progress summary if available
    if 'progress' in result and result['progress']:
        prog = result['progress']
        elapsed = prog.get('elapsed_seconds', 0)
        hours = int(elapsed // 3600)
        minutes = int((elapsed % 3600) // 60)
        print(f"Elapsed time: {hours}h {minutes}m")
    
    print("=" * 80)
    print(f"\nCheckpoint file: /tmp/permutation_checkpoints/permutation_progress_{result.get('run_id')}.json")
    print("View progress anytime: python3 scripts/check_permutation_progress.py")
    print("")
    
    sys.exit(0 if result.get('success') else 1)


if __name__ == "__main__":
    main()
