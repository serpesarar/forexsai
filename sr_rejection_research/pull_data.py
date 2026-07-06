"""Faz 0 — prediction_logs (resolved sinyaller) + candle_cache OHLC'yi yerele çek."""
import json, sys
from pathlib import Path
from dotenv import dotenv_values
from supabase import create_client

ROOT = Path("/Users/melihcanodacioglu/Desktop/panel")
OUT = ROOT / "sr_rejection_research" / "data"
c = dotenv_values(ROOT / "backend" / ".env")
sb = create_client(c["SUPABASE_URL"], c.get("SUPABASE_SERVICE_ROLE_KEY") or c["SUPABASE_KEY"])

def page(q_builder):
    rows, off = [], 0
    while True:
        r = q_builder(off).execute().data
        rows += r
        if len(r) < 1000:
            break
        off += 1000
    return rows

# 1) prediction_logs — resolved sinyaller (gerekli kolonlar)
print("prediction_logs çekiliyor...")
cols = "model_type,symbol,timeframe,created_at,ml_direction,ml_entry_price,status,highest_profit_pips,lowest_drawdown_pips,targets"
pl = page(lambda off: sb.table("prediction_logs").select(cols)
          .in_("status", ["completed", "stopped"])
          .order("created_at").range(off, off + 999))
(OUT / "signals.json").write_text(json.dumps(pl))
print(f"  signals.json: {len(pl)} satır")

# 2) candle_cache — native TF'ler (5m/30m/1h/1m); 15m=5m'den, 4h=1h'ten türetilecek
SYMBOLS = ["NDX.INDX", "GDAXI.INDX", "USOIL.FOREX", "XAUUSD"]
for tf in ["1h", "30m", "5m", "1m"]:
    for sym in SYMBOLS:
        rows = page(lambda off, s=sym, t=tf: sb.table("candle_cache")
                    .select("candle_time,open,high,low,close,volume")
                    .eq("symbol", s).eq("timeframe", t)
                    .order("candle_time").range(off, off + 999))
        (OUT / f"{sym}_{tf}.json").write_text(json.dumps(rows))
        print(f"  {sym} {tf}: {len(rows)} bar")
print("Faz 0 bitti.")
