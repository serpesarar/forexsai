from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

for env_path in (BACKEND_DIR / ".env", ROOT / ".env"):
    if env_path.exists():
        load_dotenv(env_path)
        break

from services.permutation_batch_service import DEFAULT_DIRECTIONS, DEFAULT_QUANTILES, DEFAULT_SYMBOLS, DEFAULT_TECHNICAL_TIMEFRAMES, PermutationBatchConfig, run_permutation_batch


def _parse_csv(raw_value: str, fallback):
    if not raw_value.strip():
        return list(fallback)
    return [part.strip() for part in raw_value.split(",") if part.strip()]


def _parse_int_csv(raw_value: str):
    if not raw_value.strip():
        return []
    return [int(part.strip()) for part in raw_value.split(",") if part.strip()]


def _parse_float_csv(raw_value: str):
    if not raw_value.strip():
        return []
    return [float(part.strip()) for part in raw_value.split(",") if part.strip()]


DEFAULT_QUANTILES_CSV = ",".join(str(value) for value in DEFAULT_QUANTILES)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--symbols", type=str, default=",".join(DEFAULT_SYMBOLS))
    parser.add_argument("--directions", type=str, default=",".join(DEFAULT_DIRECTIONS))
    parser.add_argument("--technical-timeframes", type=str, default=",".join(DEFAULT_TECHNICAL_TIMEFRAMES))
    parser.add_argument("--model-lookback-days", type=int, default=180)
    parser.add_argument("--model-min-occurrences", type=int, default=5)
    parser.add_argument("--cluster-window-minutes", type=int, default=10)
    parser.add_argument("--technical-min-occurrences", type=int, default=40)
    parser.add_argument("--technical-candle-limit", type=int, default=5000)
    parser.add_argument("--lookforward-candles", type=int, default=5)
    parser.add_argument("--lookforward-grid", type=str, default="")
    parser.add_argument("--target-move-pct", type=float, default=0.3)
    parser.add_argument("--target-move-grid", type=str, default="")
    parser.add_argument("--stop-move-pct", type=float, default=0.3)
    parser.add_argument("--stop-move-grid", type=str, default="")
    parser.add_argument("--quantiles", type=str, default=DEFAULT_QUANTILES_CSV)
    parser.add_argument("--top-thresholds-per-indicator", type=int, default=6)
    parser.add_argument("--max-atomic-rules", type=int, default=48)
    parser.add_argument("--max-combination-size", type=int, default=6)
    parser.add_argument("--top-results-per-context", type=int, default=750)
    parser.add_argument("--walk-forward-splits", type=int, default=0)
    parser.add_argument("--walk-forward-test-size", type=int, default=80)
    parser.add_argument("--walk-forward-min-train-size", type=int, default=250)
    parser.add_argument("--walk-forward-top-candidates", type=int, default=250)
    parser.add_argument("--no-resample-missing-timeframes", action="store_true")
    args = parser.parse_args()

    config = PermutationBatchConfig(
        symbols=_parse_csv(args.symbols, DEFAULT_SYMBOLS),
        directions=_parse_csv(args.directions, DEFAULT_DIRECTIONS),
        technical_timeframes=_parse_csv(args.technical_timeframes, DEFAULT_TECHNICAL_TIMEFRAMES),
        model_lookback_days=args.model_lookback_days,
        model_min_occurrences=args.model_min_occurrences,
        cluster_window_minutes=args.cluster_window_minutes,
        technical_min_occurrences=args.technical_min_occurrences,
        technical_candle_limit=args.technical_candle_limit,
        lookforward_candles=args.lookforward_candles,
        lookforward_grid=_parse_int_csv(args.lookforward_grid),
        target_move_pct=args.target_move_pct,
        target_move_grid=_parse_float_csv(args.target_move_grid),
        stop_move_pct=args.stop_move_pct,
        stop_move_grid=_parse_float_csv(args.stop_move_grid),
        quantiles=[float(part.strip()) for part in args.quantiles.split(",") if part.strip()],
        top_thresholds_per_indicator=args.top_thresholds_per_indicator,
        max_atomic_rules=args.max_atomic_rules,
        max_combination_size=args.max_combination_size,
        top_results_per_context=args.top_results_per_context,
        walk_forward_splits=args.walk_forward_splits,
        walk_forward_test_size=args.walk_forward_test_size,
        walk_forward_min_train_size=args.walk_forward_min_train_size,
        walk_forward_top_candidates=args.walk_forward_top_candidates,
        resample_missing_timeframes=not args.no_resample_missing_timeframes,
        dry_run=not args.apply,
    )
    payload = asyncio.run(run_permutation_batch(config))
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if payload.get("success") else 1


if __name__ == "__main__":
    import asyncio

    raise SystemExit(main())
