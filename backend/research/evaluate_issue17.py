"""Read-only counterfactual on a JSON array export of prediction_logs.

Usage: python backend/research/evaluate_issue17.py prediction_logs.json
Requires entry-time factors; does not reconstruct them from today's candles.
No network, credentials, database writes, or automatic gate activation.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from services.pulse1_swing_high_filter import filter_inputs, is_candidate, would_block
from services.signal_metrics import aggregate_outcomes

RESOLVED = {"completed", "stopped"}


def parse_factors(value: Any) -> dict:
    """Accept JSONB objects or serialized JSONB from an export."""
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except ValueError:
            return {}
    return value if isinstance(value, dict) else {}


def metrics(rows: list[dict]) -> dict:
    """Use canonical outcomes, including partials, ambiguity and geometry."""
    canonical = aggregate_outcomes(rows).to_dict()
    wins = canonical["wins"] + canonical["partials"]
    return {
        "rows": len(rows), "resolved": canonical["n"], "wins": wins,
        "losses": canonical["losses"] + canonical["ambiguous"],
        "win_rate_pct": canonical["win_rate"], "canonical": canonical,
    }


def compare(rows: list[dict]) -> dict:
    """Measure winner removal, with missing-data coverage made explicit."""
    blocked = [r for r in rows if would_block(
        r["symbol"], r["ml_direction"], r["model_type"], r["factors"])]
    kept = [r for r in rows if not would_block(
        r["symbol"], r["ml_direction"], r["model_type"], r["factors"])]
    before, after, removed = metrics(rows), metrics(kept), metrics(blocked)
    complete = sum(all(v is not None for v in filter_inputs(r["factors"])) for r in rows)
    return {
        "before": before, "kept": after, "would_block": removed,
        "complete_feature_rows": complete, "missing_feature_rows": len(rows) - complete,
        "historical_winners_blocked_pct": (
            round(100 * removed["wins"] / before["wins"], 4) if before["wins"] else None),
        "win_rate_delta_pp": (
            round(after["win_rate_pct"] - before["win_rate_pct"], 4)
            if after["win_rate_pct"] is not None and before["win_rate_pct"] is not None
            else None),
    }


def evaluate(rows: list[dict]) -> dict:
    """Scope the export and report standalone rule impact, never a causal claim."""
    candidates = [dict(r, factors=parse_factors(r.get("factors"))) for r in rows
                  if is_candidate(r.get("symbol"), r.get("ml_direction"), r.get("model_type"))]
    resolved = [r for r in candidates if r.get("status") in RESOLVED]
    timestamps = sorted(str(r["created_at"]) for r in resolved if r.get("created_at"))
    complete = [r for r in resolved if all(v is not None for v in filter_inputs(r["factors"]))]
    return {
        "status": "descriptive_only" if resolved else "no_resolved_candidates",
        "feature_coverage_pct": round(100 * len(complete) / len(resolved), 4) if resolved else None,
        "input_rows": len(rows), "candidate_rows": len(candidates),
        "excluded_statuses": dict(Counter(
            str(r.get("status")) for r in candidates if r.get("status") not in RESOLVED)),
        "window": {"first": timestamps[0] if timestamps else None,
                   "last": timestamps[-1] if timestamps else None},
        "all_resolved_candidates": compare(resolved),
        "complete_feature_candidates": compare(complete),
        "by_regime": {label: compare([r for r in resolved
                                     if filter_inputs(r["factors"])[0] == label])
                      for label in ("transition", "unknown")},
        "by_target_type": {label: compare([r for r in resolved
                                           if str(r["factors"].get("target_type") or "missing") == label])
                           for label in sorted({str(r["factors"].get("target_type") or "missing")
                                                for r in resolved})},
        "pnl": None,
        "limitations": [
            "No complete entry-time factors means no historical safety conclusion.",
            "Canonical outcomes include partials/ambiguity; inspect expectancy and epoch breakdown, not WR alone.",
            "Canonical R may use legacy fallbacks; verify exit and stop geometry before relying on expectancy.",
            "MFE/MAE are excursions, not realized P/L; no P/L benefit is inferred.",
            "Standalone rule impact only: no replay of other guards, fills or portfolio effects.",
            "Export completeness, deduplication and a separate forward window must be checked before activation.",
        ],
    }


def main() -> None:
    """Print a reproducible JSON report without modifying the supplied export."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("export", type=Path)
    args = parser.parse_args()
    rows = json.loads(args.export.read_text())
    if not isinstance(rows, list) or any(not isinstance(r, dict) for r in rows):
        parser.error("Expected a JSON array of prediction_logs objects")
    print(json.dumps(evaluate(rows), indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
