#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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


def format_pct(value: Any) -> str:
    try:
        return f"{float(value) * 100:.2f}%"
    except Exception:
        return "0.00%"


def format_num(value: Any, digits: int = 2) -> str:
    try:
        return f"{float(value):.{digits}f}"
    except Exception:
        return f"{0:.{digits}f}"


def get_run_record(client, run_id: str) -> dict[str, Any]:
    result = (
        client.table("permutation_batch_runs")
        .select("id,status,started_at,completed_at,parameters,summary,error")
        .eq("id", run_id)
        .limit(1)
        .execute()
    )
    data = result.get("data") or []
    if not data:
        raise RuntimeError(f"Run not found: {run_id}")
    return data[0]


def get_model_rows(client, run_id: str) -> list[dict[str, Any]]:
    result = (
        client.table("model_permutation_batch_results")
        .select("run_id,symbol,direction,combination,total_signals,wins,losses,win_rate,profit_factor,expectancy,avg_member_alignment,unanimous_win_rate,lookback_days,cluster_window_minutes,insufficient_data,rank")
        .eq("run_id", run_id)
        .order("symbol")
        .order("direction")
        .order("rank")
        .execute()
    )
    return result.get("data") or []


def classify_row(row: dict[str, Any], min_occurrences: int) -> str:
    total_signals = int(row.get("total_signals") or 0)
    win_rate = float(row.get("win_rate") or 0.0)
    profit_factor = float(row.get("profit_factor") or 0.0)
    expectancy = float(row.get("expectancy") or 0.0)
    insufficient = bool(row.get("insufficient_data", False)) or total_signals < min_occurrences
    if insufficient:
        return "weak_sample"
    if win_rate >= 0.7 and profit_factor >= 1.5 and expectancy > 0:
        return "strong"
    if win_rate >= 0.55 and profit_factor >= 1.0 and expectancy >= 0:
        return "usable"
    return "weak"


def sort_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        rows,
        key=lambda row: (
            bool(row.get("insufficient_data", False)),
            -(float(row.get("win_rate") or 0.0)),
            -(int(row.get("total_signals") or 0)),
            -(float(row.get("profit_factor") or 0.0)),
            -(float(row.get("expectancy") or 0.0)),
            int(row.get("rank") or 999999),
        ),
    )


def build_overview(rows: list[dict[str, Any]], min_occurrences: int) -> dict[str, Any]:
    classified_counts = defaultdict(int)
    for row in rows:
        classified_counts[classify_row(row, min_occurrences)] += 1
    return {
        "total_rows": len(rows),
        "strong_rows": classified_counts["strong"],
        "usable_rows": classified_counts["usable"],
        "weak_rows": classified_counts["weak"],
        "weak_sample_rows": classified_counts["weak_sample"],
        "avg_win_rate": round(sum(float(r.get("win_rate") or 0.0) for r in rows) / max(len(rows), 1), 4),
        "avg_profit_factor": round(sum(float(r.get("profit_factor") or 0.0) for r in rows) / max(len(rows), 1), 4),
        "avg_expectancy": round(sum(float(r.get("expectancy") or 0.0) for r in rows) / max(len(rows), 1), 4),
    }


def build_context_groups(rows: list[dict[str, Any]], min_occurrences: int, top_n: int) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row.get("symbol") or ""), str(row.get("direction") or ""))].append(row)
    contexts: list[dict[str, Any]] = []
    for (symbol, direction), group_rows in sorted(grouped.items()):
        sorted_group = sort_rows(group_rows)
        top_rows = []
        for row in sorted_group[:top_n]:
            top_rows.append({
                "rank": int(row.get("rank") or 0),
                "combination": row.get("combination"),
                "total_signals": int(row.get("total_signals") or 0),
                "wins": int(row.get("wins") or 0),
                "losses": int(row.get("losses") or 0),
                "win_rate": float(row.get("win_rate") or 0.0),
                "profit_factor": float(row.get("profit_factor") or 0.0),
                "expectancy": float(row.get("expectancy") or 0.0),
                "avg_member_alignment": float(row.get("avg_member_alignment") or 0.0),
                "unanimous_win_rate": float(row.get("unanimous_win_rate") or 0.0),
                "quality": classify_row(row, min_occurrences),
            })
        strong_count = sum(1 for row in group_rows if classify_row(row, min_occurrences) == "strong")
        usable_count = sum(1 for row in group_rows if classify_row(row, min_occurrences) == "usable")
        contexts.append({
            "symbol": symbol,
            "direction": direction,
            "row_count": len(group_rows),
            "strong_count": strong_count,
            "usable_count": usable_count,
            "top_rows": top_rows,
        })
    return contexts


def build_payload(run_record: dict[str, Any], rows: list[dict[str, Any]], top_n: int) -> dict[str, Any]:
    params = run_record.get("parameters") or {}
    min_occurrences = int(params.get("model_min_occurrences") or 0)
    sorted_rows = sort_rows(rows)
    for index, row in enumerate(sorted_rows, start=1):
        row["analysis_rank"] = index
        row["quality"] = classify_row(row, min_occurrences)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "run_id": run_record.get("id"),
        "status": run_record.get("status"),
        "started_at": run_record.get("started_at"),
        "completed_at": run_record.get("completed_at"),
        "error": run_record.get("error"),
        "parameters": params,
        "overview": build_overview(sorted_rows, min_occurrences),
        "contexts": build_context_groups(sorted_rows, min_occurrences, top_n),
        "overall_top": sorted_rows[:top_n],
        "overall_bottom": list(reversed(sorted_rows[-top_n:])),
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "analysis_rank",
        "rank",
        "symbol",
        "direction",
        "combination",
        "total_signals",
        "wins",
        "losses",
        "win_rate",
        "profit_factor",
        "expectancy",
        "avg_member_alignment",
        "unanimous_win_rate",
        "insufficient_data",
        "quality",
        "lookback_days",
        "cluster_window_minutes",
    ]
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name) for name in fieldnames})


def build_txt(payload: dict[str, Any], top_n: int) -> str:
    lines: list[str] = []
    params = payload.get("parameters") or {}
    overview = payload.get("overview") or {}
    lines.append(f"Run ID: {payload.get('run_id')}")
    lines.append(f"Status: {payload.get('status')}")
    lines.append(f"Started: {payload.get('started_at')}")
    lines.append(f"Lookback days: {params.get('model_lookback_days')}")
    lines.append(f"Model min occurrences: {params.get('model_min_occurrences')}")
    lines.append(f"Cluster window minutes: {params.get('cluster_window_minutes')}")
    lines.append(f"Total model rows: {overview.get('total_rows')} ")
    lines.append(f"Strong combinations: {overview.get('strong_rows')}")
    lines.append(f"Usable combinations: {overview.get('usable_rows')}")
    lines.append(f"Weak combinations: {overview.get('weak_rows')}")
    lines.append(f"Weak-sample combinations: {overview.get('weak_sample_rows')}")
    lines.append(f"Average success rate: {format_pct(overview.get('avg_win_rate'))}")
    lines.append("")
    lines.append(f"Overall Top {top_n} combinations")
    lines.append("=" * 90)
    for row in payload.get("overall_top") or []:
        lines.append(
            f"#{row.get('analysis_rank')} | {row.get('symbol')} {row.get('direction')} | {row.get('combination')} | "
            f"success={format_pct(row.get('win_rate'))} | wins={row.get('wins')}/{row.get('total_signals')} | "
            f"pf={format_num(row.get('profit_factor'))} | exp={format_num(row.get('expectancy'))} | quality={row.get('quality')}"
        )
    lines.append("")
    lines.append(f"Overall Weakest {top_n} combinations")
    lines.append("=" * 90)
    for row in payload.get("overall_bottom") or []:
        lines.append(
            f"#{row.get('analysis_rank')} | {row.get('symbol')} {row.get('direction')} | {row.get('combination')} | "
            f"success={format_pct(row.get('win_rate'))} | wins={row.get('wins')}/{row.get('total_signals')} | "
            f"pf={format_num(row.get('profit_factor'))} | exp={format_num(row.get('expectancy'))} | quality={row.get('quality')}"
        )
    for context in payload.get("contexts") or []:
        lines.append("")
        lines.append(f"Context: {context.get('symbol')} {context.get('direction')}")
        lines.append("-" * 90)
        lines.append(
            f"rows={context.get('row_count')} | strong={context.get('strong_count')} | usable={context.get('usable_count')}"
        )
        for row in context.get("top_rows") or []:
            lines.append(
                f"rank={row.get('rank')} | {row.get('combination')} | success={format_pct(row.get('win_rate'))} | "
                f"wins={row.get('wins')}/{row.get('total_signals')} | pf={format_num(row.get('profit_factor'))} | "
                f"exp={format_num(row.get('expectancy'))} | quality={row.get('quality')}"
            )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", action="append", required=True)
    parser.add_argument("--output-dir", default="~/Desktop/permutation_runs")
    parser.add_argument("--top", type=int, default=15)
    args = parser.parse_args()

    output_dir = Path(args.output_dir).expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)

    client = get_supabase_client()
    if not client:
        raise SystemExit("No Supabase client available")

    for run_id in args.run_id:
        run_record = get_run_record(client, run_id)
        rows = get_model_rows(client, run_id)
        if not rows:
            raise RuntimeError(f"No model rows found for run: {run_id}")
        payload = build_payload(run_record, rows, args.top)
        short_id = str(run_id).split("-")[0]
        json_path = output_dir / f"model_analysis_{short_id}.json"
        csv_path = output_dir / f"model_analysis_{short_id}.csv"
        txt_path = output_dir / f"model_analysis_{short_id}.txt"
        write_json(json_path, payload)
        write_csv(csv_path, payload.get("overall_top", []) + payload.get("overall_bottom", []))
        txt_path.write_text(build_txt(payload, args.top))
        print(json.dumps({
            "run_id": run_id,
            "json": str(json_path),
            "csv": str(csv_path),
            "txt": str(txt_path),
            "top_count": len(payload.get("overall_top") or []),
        }, ensure_ascii=False))


if __name__ == "__main__":
    main()
