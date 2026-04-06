#!/usr/bin/env python3
"""Minimal test to debug why technical analysis never starts."""
import sys
from pathlib import Path

# Add backend to path (same as run_permutation_batch_fast.py)
BACKEND = Path(__file__).parent / "backend"
sys.path.insert(0, str(BACKEND))

import os
os.environ['SUPABASE_URL'] = 'https://xdmtbykebfpqutfgdfqs.supabase.co'
os.environ['SUPABASE_SERVICE_ROLE_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhkbXRieWtlYmZwcXV0ZmdkZnFzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODI0NDIwNSwiZXhwIjoyMDgzODIwMjA1fQ.oOr7u4poVBy3tdNaA0sHETTODHlxc7SfZTYAW-nxrQk'

import asyncio
from services.permutation_batch_service_fast import run_permutation_batch_fast, get_balanced_preset

async def test():
    print("Starting minimal test...")
    config = get_balanced_preset()
    config.symbols = ['NDX.INDX']  # Only test one symbol
    config.technical_timeframes = ['1h']  # Only one timeframe
    config.lookforward_grid = [10]  # Minimal grid
    config.target_move_grid = [0.005, 0.01, 0.015]  # 0.5%, 1%, 1.5% - realistic for 1h
    config.stop_move_grid = [0.003, 0.005, 0.008]   # 0.3%, 0.5%, 0.8% - realistic stops
    config.max_combination_size = 2  # Very small
    config.max_atomic_rules = 10
    config.dry_run = False  # Real test - will write to DB
    
    print(f"Config: symbols={config.symbols}, timeframes={config.technical_timeframes}")
    print(f"Grid sizes: lookforward={len(config.lookforward_grid)}, target={len(config.target_move_grid)}, stop={len(config.stop_move_grid)}")
    print(f"Expected technical contexts: {len(config.symbols) * len(config.technical_timeframes) * len(config.directions) * len(config.lookforward_grid) * len(config.target_move_grid) * len(config.stop_move_grid)}")
    
    result = await run_permutation_batch_fast(config)
    print(f"\nResult: {result}")

if __name__ == '__main__':
    asyncio.run(test())
