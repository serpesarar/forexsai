import os
import sys

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings
# Manually populate os.environ so supabase_client can read them
if settings.supabase_url:
    os.environ["SUPABASE_URL"] = settings.supabase_url
if settings.supabase_key:
    os.environ["SUPABASE_SERVICE_ROLE_KEY"] = settings.supabase_key
    os.environ["SUPABASE_KEY"] = settings.supabase_key

from database.supabase_client import get_supabase_client
client = get_supabase_client()
print("Supabase client initialized:", client is not None)

# Query prediction logs count
count_res = client.table("prediction_logs").select("*").limit(5).execute()
print("Sample prediction logs in DB:", len(count_res.get("data") or []))

# Query mt5_trades table count and columns
try:
    count_res = client.table("mt5_trades").select("*").limit(1).execute()
    print("mt5_trades table is available!")
    if count_res.get("data"):
        print("Fields in mt5_trades:")
        for k, v in count_res.get("data")[0].items():
            print(f"  {k}: {v} (type: {type(v).__name__})")
    else:
        print("mt5_trades table exists but is empty.")
except Exception as e:
    print("mt5_trades table error:", e)
