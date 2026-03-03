import os
import sys
from dotenv import load_dotenv
import httpx

load_dotenv()
url = os.getenv("SUPABASE_URL")
if url.endswith(".com"):
    url = url[:-1] + "o"
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")

if not url or not key:
    print("No creds")
    sys.exit(1)

with httpx.Client() as client:
    res = client.get(
        f"{url}/rest/v1/prediction_logs?select=symbol,status,created_at&symbol=in.(XAUUSD,USOIL.FOREX)&limit=1000",
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Prefer": "return=representation"
        }
    )
    if res.status_code != 200:
        print(res.text)
    else:
        data = res.json()
        counts = {}
        for row in data:
            sym = row['symbol']
            st = row['status']
            if sym not in counts:
                counts[sym] = {"total": 0}
            counts[sym]["total"] += 1
            counts[sym][st] = counts[sym].get(st, 0) + 1
        print("XAUUSD and US Oil Recent Stats:")
        for k, v in counts.items():
            print(f"{k}: {v}")
