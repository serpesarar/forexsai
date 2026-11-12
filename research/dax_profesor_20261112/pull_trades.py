"""DAX (GER40) bot işlemlerini bot_trades'ten çeker."""
import os, json, sys
from pathlib import Path
from dotenv import load_dotenv
load_dotenv("backend/.env")
from supabase import create_client
c = create_client(os.environ["SUPABASE_URL"], os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ["SUPABASE_KEY"])
r = c.table("bot_trades").select("ticket,symbol,direction,volume,open_time,close_time,open_price,close_price,sl,tp,profit,commission,swap,comment,magic,raw").eq("symbol","GER40").order("open_time").execute()
out = Path("research/dax_profesor_20261112/data"); out.mkdir(parents=True, exist_ok=True)
(out/"dax_trades.json").write_text(json.dumps(r.data, default=str, ensure_ascii=False, indent=0))
print(len(r.data))
