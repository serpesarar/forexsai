#!/usr/bin/env python3
"""Quick check for running permutation batch runs."""
from pathlib import Path
import sys

# Add backend to path
BACKEND = Path("/Users/melihcanodacioglu/Desktop/panel/backend")
sys.path.insert(0, str(BACKEND))

from dotenv import load_dotenv
load_dotenv(BACKEND / ".env")

print("Importing supabase client...")
from database.supabase_client import get_supabase_client

print("Getting client...")
client = get_supabase_client()

print("Querying running runs...")
runs = client.table("permutation_batch_runs") \
    .select("id,status,started_at,parameters") \
    .eq("status", "running") \
    .order("started_at", desc=False) \
    .limit(20) \
    .execute()

data = runs.get("data", [])
print(f"\n{'='*80}")
print(f"Found {len(data)} running permutation batch runs")
print(f"{'='*80}")

for r in data:
    rid = r["id"]
    params = r.get("parameters") or {}
    print(f"\nRun ID: {rid}")
    print(f"Started: {r['started_at']}")
    print(f"Status: {r['status']}")
    print(f"  model_lookback_days: {params.get('model_lookback_days')}")
    print(f"  technical_candle_limit: {params.get('technical_candle_limit')}")
    print(f"  max_atomic_rules: {params.get('max_atomic_rules')}")
    print(f"  walk_forward_splits: {params.get('walk_forward_splits')}")
    print(f"  top_results_per_context: {params.get('top_results_per_context')}")
    print(f"  lookforward_grid: {params.get('lookforward_grid')}")
    print(f"  target_move_grid: {params.get('target_move_grid')}")
    print(f"  stop_move_grid: {params.get('stop_move_grid')}")
    
    # Try to get row counts (might be slow)
    print("  Counting rows...")
    try:
        model_data = client.table("model_permutation_batch_results").select("run_id").eq("run_id", rid).execute().get("data", [])
        print(f"  model_rows: {len(model_data)} (queried, not exact count)")
    except Exception as e:
        print(f"  model_rows: Error - {e}")
    
    try:
        tech_data = client.table("technical_permutation_batch_results").select("run_id").eq("run_id", rid).execute().get("data", [])
        print(f"  technical_rows: {len(tech_data)} (queried, not exact count)")
    except Exception as e:
        print(f"  technical_rows: Error - {e}")
    
    print("-" * 40)

print("\nDone!")
