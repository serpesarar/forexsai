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

from services.ml_history_backfill_service import DEFAULT_ML_BACKFILL_SYMBOLS, run_ml_history_backfill


def _parse_symbols(raw_value: str):
    if not raw_value.strip():
        return list(DEFAULT_ML_BACKFILL_SYMBOLS)
    return [part.strip() for part in raw_value.split(",") if part.strip()]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--symbols", type=str, default=",".join(DEFAULT_ML_BACKFILL_SYMBOLS))
    parser.add_argument("--max-records", type=int, default=20000)
    parser.add_argument("--window-days", type=int, default=30)
    parser.add_argument("--sample-size", type=int, default=10)
    args = parser.parse_args()

    payload = run_ml_history_backfill(
        dry_run=not args.apply,
        symbols=_parse_symbols(args.symbols),
        max_records=args.max_records,
        window_days=args.window_days,
        sample_size=args.sample_size,
    )
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if payload.get("success") and not payload.get("error") else 1


if __name__ == "__main__":
    raise SystemExit(main())
