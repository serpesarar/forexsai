"""
candle_cache'ten temiz bar çek → bot_live_audit/bars/*.json
1m: USOIL+XAU (06-22'ye dek var) | 1h: 4 sembol (temiz, 06-24'e dek, XAU hariç)
supabase-py ile sayfalı çekim (MCP context'i şişirmesin diye yerel dosyaya).
"""
import json, os
from pathlib import Path
from dotenv import dotenv_values
from supabase import create_client

ROOT=Path("/Users/melihcanodacioglu/Desktop/panel")
cfg=dotenv_values(ROOT/"backend"/".env")
url=cfg.get("SUPABASE_URL"); key=cfg.get("SUPABASE_SERVICE_ROLE_KEY") or cfg.get("SUPABASE_KEY")
sb=create_client(url, key)
OUT=ROOT/"bot_live_audit"/"bars"; OUT.mkdir(exist_ok=True)

def fetch(sym, tf, start="2026-06-13", end="2026-06-25"):
    rows=[]; step=1000; off=0
    while True:
        q=(sb.table("candle_cache").select("candle_time,open,high,low,close,volume")
           .eq("symbol",sym).eq("timeframe",tf)
           .gte("candle_time",start).lt("candle_time",end)
           .order("candle_time").range(off, off+step-1))
        r=q.execute().data
        rows+=r
        if len(r)<step: break
        off+=step
    # dedupe by candle_time (XAU 1h snapshot kirliliği için son kayıt kalır)
    seen={}
    for b in rows: seen[b["candle_time"]]=b
    clean=sorted(seen.values(), key=lambda x:x["candle_time"])
    (OUT/f"{sym}_{tf}.json").write_text(json.dumps(clean))
    fb=clean[0]["candle_time"] if clean else "—"; lb=clean[-1]["candle_time"] if clean else "—"
    print(f"  {sym:12s} {tf:3s}: {len(clean):6d} bar  ({fb} → {lb})")
    return len(clean)

print("1m (scalp çözünürlüğü):")
fetch("USOIL.FOREX","1m"); fetch("XAUUSD","1m")
print("1h (yedek/yavaş işlemler):")
for s in ["NDX.INDX","GDAXI.INDX","USOIL.FOREX","XAUUSD"]:
    fetch(s,"1h")
print("bitti.")
