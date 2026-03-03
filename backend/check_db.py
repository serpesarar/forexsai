import asyncio
from services.supabase_client import get_supabase_client

async def main():
    client = get_supabase_client()
    res = client.table("prediction_logs").select("symbol, status").execute()
    logs = res.get("data", [])
    
    counts = {}
    for l in logs:
        sym = l.get("symbol")
        st = l.get("status")
        if sym not in counts:
            counts[sym] = {"total": 0, "active": 0, "completed": 0, "stopped": 0, "other": 0}
        counts[sym]["total"] += 1
        if st in counts[sym]:
            counts[sym][st] += 1
        else:
            counts[sym]["other"] += 1
            
    for sym, c in counts.items():
        print(f"{sym}: {c}")

if __name__ == "__main__":
    asyncio.run(main())
