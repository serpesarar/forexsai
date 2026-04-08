"""
Run backtest manually to verify it works with real EODH data.
Usage: cd /Users/melihcanodacioglu/Desktop/panel && .venv/bin/python backend/scripts/run_backtest.py
"""
import asyncio
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BACKEND_ROOT = os.path.join(PROJECT_ROOT, "backend")
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, BACKEND_ROOT)

# Load environment variables from backend/.env file
from dotenv import load_dotenv
env_path = os.path.join(BACKEND_ROOT, ".env")
if os.path.exists(env_path):
    load_dotenv(env_path)
    print(f"Loaded env from: {env_path}")


async def main():
    from backend.models.order_blocks import BacktestRequest
    from backend.services.order_block_service import OrderBlockService

    print("Initializing OrderBlockService...")
    svc = OrderBlockService()

    print("Running backtest for NAS100 5m...")
    req = BacktestRequest(symbol="NAS100", timeframe="5m", config={})
    result = await svc.backtest(req)

    print("\n=== BACKTEST RESULTS ===")
    print(f"Total signals : {result.get('total_signals', 0)}")
    print(f"Wins          : {result.get('wins', 0)}")
    print(f"Losses        : {result.get('losses', 0)}")
    print(f"Win rate      : {result.get('win_rate', 0)}%")
    print(f"Sharpe        : {result.get('sharpe_ratio', 'N/A')}")
    print(f"Max drawdown  : {result.get('max_drawdown', 'N/A')}")
    print(f"Grade         : {result.get('grade', 'N/A')}")

    if result.get("rule_performance"):
        print("\n=== RULE PERFORMANCE ===")
        for rule, stats in result["rule_performance"].items():
            wr = stats.get("win_rate", 0)
            count = stats.get("count", 0)
            print(f"  {rule:<35} win={wr:.1f}%  count={count}")


asyncio.run(main())
