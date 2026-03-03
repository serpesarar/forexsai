import asyncio
import os
import sys

# Add the directory to the path to make sure routers can be imported
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from routers.learning import get_historical_signals_endpoint

async def main():
    try:
        res = await get_historical_signals_endpoint("XAUUSD", 30)
        print("Success!")
        print(res.keys() if isinstance(res, dict) else res)
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
