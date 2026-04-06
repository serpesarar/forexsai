#!/usr/bin/env python3
"""
Sadece MODEL PERMÜTASYONU çalıştıran script.
Teknik gösterge permütasyonu YOK.
"""

import asyncio
import os
import sys
import uuid
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.services.permutation_analysis_service import analyze_model_permutations
from backend.database.supabase_client import get_supabase_client, is_db_available


def _load_backend_env() -> None:
    env_path = Path(__file__).resolve().parent / "backend" / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _create_run_record(client, run_id: str, symbols, directions, lookback_days: int, min_occurrences: int, cluster_window_minutes: int):
    payload = {
        "id": run_id,
        "batch_kind": "model",
        "status": "running",
        "symbols": list(symbols),
        "directions": list(directions),
        "timeframes": [],
        "parameters": {
            "lookback_days": lookback_days,
            "min_occurrences": min_occurrences,
            "cluster_window_minutes": cluster_window_minutes,
        },
        "summary": {},
    }
    result = client.table("permutation_batch_runs").insert(payload)
    if result.get("error"):
        raise RuntimeError(f"Failed to create run record: {result['error']}")


def _finish_run_record(client, run_id: str, status: str, summary, error: str | None = None):
    payload = {
        "status": status,
        "summary": summary,
    }
    if error:
        payload["error"] = error
    result = client.table("permutation_batch_runs").eq("id", run_id).update(payload)
    if result.get("error"):
        print(f"[ModelPerm] Run status update error: {result['error']}")


def _dedupe_rows(rows):
    deduped = {}
    for row in rows:
        key = (
            row.get("run_id"),
            row.get("symbol"),
            row.get("direction"),
            row.get("combination"),
        )
        deduped[key] = row
    return list(deduped.values())


async def run_model_permutations_only(
    symbols=None,
    directions=None,
    lookback_days=180,
    min_occurrences=5,
    cluster_window_minutes=10,
    dry_run=False
):
    """
    Sadece model permütasyonlarını çalıştır.
    
    Returns:
        Dict: {
            "success": True/False,
            "run_id": str,
            "model_contexts": int,
            "model_rows": int,
            "results": [...]
        }
    """
    
    _load_backend_env()
    
    if not is_db_available():
        return {"success": False, "error": "Database not available"}
    
    client = get_supabase_client()
    if not client:
        return {"success": False, "error": "No database connection"}
    
    symbols = symbols or ["NDX.INDX"]
    directions = directions or ["BUY", "SELL"]
    
    # Create run record with UUID
    run_id = str(uuid.uuid4())
    _create_run_record(client, run_id, symbols, directions, lookback_days, min_occurrences, cluster_window_minutes)
    
    print(f"[ModelPerm] Starting run: {run_id}")
    print(f"[ModelPerm] Symbols: {symbols}")
    print(f"[ModelPerm] Directions: {directions}")
    print(f"[ModelPerm] Lookback: {lookback_days} days")
    print(f"[ModelPerm] Min occurrences: {min_occurrences}")
    print(f"[ModelPerm] Dry run: {dry_run}")
    
    summary = {
        "success": True,
        "run_id": run_id,
        "dry_run": dry_run,
        "model_contexts": 0,
        "model_rows": 0,
        "results": []
    }
    
    model_rows_to_write = []
    
    for symbol in symbols:
        for direction in directions:
            print(f"\n[ModelPerm] Processing {symbol}/{direction}...")
            
            model_result = await analyze_model_permutations(
                symbol=symbol,
                direction=direction,
                min_occurrences=min_occurrences,
                lookback_days=lookback_days,
                cluster_window_minutes=cluster_window_minutes,
            )
            
            if model_result.get("error"):
                print(f"[ModelPerm] Error for {symbol}/{direction}: {model_result['error']}")
                continue
            
            summary["model_contexts"] += 1
            
            results = model_result.get("results", [])
            print(f"[ModelPerm] Found {len(results)} combinations")
            print(f"[ModelPerm] Clusters analyzed: {model_result.get('total_clusters_analyzed', 0)}")
            print(f"[ModelPerm] Lookback used: {model_result.get('lookback_days_used', lookback_days)} days")
            
            for rank, row in enumerate(results, start=1):
                model_rows_to_write.append({
                    "run_id": run_id,
                    "symbol": symbol,
                    "direction": direction,
                    "combination": row.get("combination"),
                    "total_signals": int(row.get("total_signals", 0) or 0),
                    "wins": int(row.get("wins", 0) or 0),
                    "losses": int(row.get("losses", 0) or 0),
                    "win_rate": float(row.get("win_rate", 0) or 0),
                    "profit_factor": float(row.get("profit_factor", 0) or 0),
                    "expectancy": float(row.get("expectancy", 0) or 0),
                    "avg_member_alignment": float(row.get("avg_member_alignment", 0) or 0),
                    "unanimous_win_rate": float(row.get("unanimous_win_rate", 0) or 0),
                    "lookback_days": int(model_result.get("lookback_days_used", lookback_days)),
                    "cluster_window_minutes": int(model_result.get("cluster_window_minutes", cluster_window_minutes)),
                    "insufficient_data": bool(row.get("insufficient_data", False)),
                    "rank": rank,
                })
                
                # Print top 5
                if rank <= 5:
                    print(f"  #{rank}: {row.get('combination')} | "
                          f"Win: {row.get('win_rate', 0):.2%} | "
                          f"PF: {row.get('profit_factor', 0):.2f} | "
                          f"Signals: {row.get('total_signals', 0)}")
    
    model_rows_to_write = _dedupe_rows(model_rows_to_write)
    summary["model_rows"] = len(model_rows_to_write)
    
    # Write to DB if not dry run
    if not dry_run and model_rows_to_write:
        print(f"\n[ModelPerm] Writing {len(model_rows_to_write)} rows to DB...")
        try:
            # Batch insert - our custom client auto-executes
            for i in range(0, len(model_rows_to_write), 100):
                batch = model_rows_to_write[i:i+100]
                result = client.table("model_permutation_batch_results").upsert(
                    batch, 
                    on_conflict="run_id,symbol,direction,combination"
                )
                if result.get("error"):
                    raise RuntimeError(result["error"])
                # result is already dict, don't call .execute()
                print(f"[ModelPerm] Written batch {i//100 + 1}/{(len(model_rows_to_write)+99)//100}")
            print(f"[ModelPerm] DB write complete!")
        except Exception as e:
            print(f"[ModelPerm] DB write error: {e}")
            summary["db_error"] = str(e)
            _finish_run_record(client, run_id, "failed", summary, str(e))
            return summary
    elif dry_run:
        print(f"\n[ModelPerm] DRY RUN - Would write {len(model_rows_to_write)} rows")
    
    print(f"\n[ModelPerm] Summary:")
    print(f"  - Model contexts: {summary['model_contexts']}")
    print(f"  - Total rows: {summary['model_rows']}")
    _finish_run_record(client, run_id, "completed", summary)
    
    return summary


async def main():
    """Main entry point."""
    
    # Configuration
    CONFIG = {
        "symbols": ["NDX.INDX", "XAUUSD", "GDAXI.INDX", "CL.COMM"],
        "directions": ["BUY", "SELL"],
        "lookback_days": 180,
        "min_occurrences": 20,
        "cluster_window_minutes": 10,
        "dry_run": False,  # True = sadece göster, yazma
    }
    
    print("="*60)
    print("MODEL PERMÜTASYON BAŞLATILIYOR")
    print("="*60)
    
    result = await run_model_permutations_only(**CONFIG)
    
    print("\n" + "="*60)
    if result.get("success"):
        print("BAŞARILI!")
        print(f"Run ID: {result['run_id']}")
        print(f"Model Contexts: {result['model_contexts']}")
        print(f"Total Rows: {result['model_rows']}")
        if result.get("db_error"):
            print(f"DB Error: {result['db_error']}")
    else:
        print(f"HATA: {result.get('error')}")
    print("="*60)
    
    return result


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result.get("success") else 1)
