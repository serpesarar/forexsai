import json
from pathlib import Path
from dotenv import dotenv_values
from supabase import create_client
ROOT=Path("/Users/melihcanodacioglu/Desktop/panel"); OUT=ROOT/"sr_rejection_research"/"data"
c=dotenv_values(ROOT/"backend"/".env")
sb=create_client(c["SUPABASE_URL"], c.get("SUPABASE_SERVICE_ROLE_KEY") or c["SUPABASE_KEY"])
for sym in ["NDX.INDX","GDAXI.INDX","USOIL.FOREX","XAUUSD"]:
    rows,off=[],0
    while True:
        r=(sb.table("candle_cache").select("candle_time,open,high,low,close,volume")
           .eq("symbol",sym).eq("timeframe","1m").order("candle_time").range(off,off+999)).execute().data
        rows+=r
        if len(r)<1000: break
        off+=1000
    (OUT/f"{sym}_1m.json").write_text(json.dumps(rows))
    print(f"  {sym} 1m: {len(rows)} bar")
print("1m pull bitti")
