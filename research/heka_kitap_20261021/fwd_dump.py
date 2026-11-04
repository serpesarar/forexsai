"""İleri sınama verisi: indicator_snapshots 15m (broker) → UTC düzeltme (lag kuralı, decider_xau_ileri/03 ile aynı)."""
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from supabase import create_client

HERE = Path(__file__).resolve().parent
load_dotenv(HERE.parents[1] / "backend" / ".env")
sb = create_client(os.environ["SUPABASE_URL"], os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ["SUPABASE_KEY"])
MAP = {"NDX": "NDX.INDX", "DAX": "GDAXI.INDX", "XAU": "XAUUSD", "OIL": "USOIL.FOREX"}

for sym, s in MAP.items():
    rows, last = [], "2026-05-20T00:00:00+00:00"
    while True:
        r = (sb.table("indicator_snapshots").select("candle_time,open,high,low,close,created_at")
             .eq("symbol", s).eq("timeframe", "15m").gt("candle_time", last).order("candle_time").limit(1000).execute())
        rows += r.data or []
        if len(r.data or []) < 1000:
            break
        last = r.data[-1]["candle_time"]
    d = pd.DataFrame(rows)
    d["ct"] = pd.to_datetime(d.candle_time, utc=True, format="ISO8601")
    d["ca"] = pd.to_datetime(d.created_at, utc=True, format="ISO8601")
    lag = (d.ca - d.ct).dt.total_seconds() / 60
    bad = (lag > -60) & (lag < 0)
    broker = lag <= -60
    d["ts"] = d.ct.where(~broker, d.ct - pd.Timedelta(hours=3))
    d["pref"] = (~broker).astype(int)
    d = d[~bad].sort_values(["ts", "pref"]).drop_duplicates("ts", keep="last")
    d[["ts", "open", "high", "low", "close"]].to_csv(HERE / "results" / f"fwd_{sym}_15m.csv", index=False)
    print(sym, len(d), "broker-etiketli", int(broker.sum()), "atılan", int(bad.sum()), d.ts.min(), d.ts.max())
