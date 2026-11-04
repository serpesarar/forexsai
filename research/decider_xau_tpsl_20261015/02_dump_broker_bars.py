"""Broker (Pepperstone MT5) XAUUSD barlarını indicator_snapshots'tan indirir (kutu kaydedicisi
data_recorder.py yazar; candle_cache emtia satırları 09-03'ten beri Yahoo vadelisi olduğu için
KULLANILMAZ). Ayrıca decider'ın canlı icraları (bot_trades, magic 52890989) indirilir.
Çıktılar: data/xau_{tf}_raw.csv  (candle_time HAM — zaman düzeltmesi 03_fix_time.py'da)
          data/decider_exec_bot_trades.csv"""
import os, csv, json
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

HERE = Path(__file__).resolve().parent
load_dotenv(HERE.parents[1] / "backend" / ".env")
sb = create_client(os.environ["SUPABASE_URL"],
                   os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ["SUPABASE_KEY"])
PAGE = 1000

def dump_tf(tf: str) -> None:
    out = HERE / "data" / f"xau_{tf}_raw.csv"
    n, last = 0, "2000-01-01T00:00:00+00:00"
    with open(out, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["candle_time", "open", "high", "low", "close", "volume", "created_at"])
        while True:   # keyset sayfalama (offset büyük tabloda yavaş)
            r = (sb.table("indicator_snapshots").select("candle_time,open,high,low,close,volume,created_at")
                 .eq("symbol", "XAUUSD").eq("timeframe", tf).gt("candle_time", last)
                 .order("candle_time").limit(PAGE).execute())
            rows = r.data or []
            for x in rows:
                w.writerow([x["candle_time"], x["open"], x["high"], x["low"], x["close"], x["volume"], x["created_at"]])
            n += len(rows)
            if len(rows) < PAGE:
                break
            last = rows[-1]["candle_time"]
    print(tf, n, out)

def dump_exec() -> None:
    r = (sb.table("bot_trades").select("*").eq("magic", 52890989).order("open_time").execute())
    rows = r.data or []
    out = HERE / "data" / "decider_exec_bot_trades.csv"
    keys = ["ticket", "host", "symbol", "direction", "volume", "open_time", "close_time", "open_price",
            "close_price", "sl", "tp", "profit", "commission", "swap", "comment", "magic", "raw", "inserted_at"]
    with open(out, "w", newline="") as f:
        w = csv.writer(f); w.writerow(keys)
        for x in rows:
            w.writerow([json.dumps(x[k]) if k == "raw" else x.get(k) for k in keys])
    print("exec", len(rows), out)

if __name__ == "__main__":
    dump_exec()
    for tf in ("1m", "5m", "15m", "1h"):
        dump_tf(tf)
