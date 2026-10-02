"""candle_cache GDAXI 1h/30m/15m (07-28 onarımı sonrası UTC) → data/dax_{tf}.parquet"""
import requests, pandas as pd
from dotenv import dotenv_values
from common import DATA, ROOT
env = dotenv_values(ROOT / "backend/.env")
url = env["SUPABASE_URL"].rstrip("/")
key = env.get("SUPABASE_SERVICE_ROLE_KEY") or env["SUPABASE_KEY"]
for tf in ["1h", "30m", "15m"]:
    rows, lo = [], 0
    while True:
        r = requests.get(f"{url}/rest/v1/candle_cache",
                         params={"symbol": "eq.GDAXI.INDX", "timeframe": f"eq.{tf}",
                                 "select": "candle_time,open,high,low,close,volume", "order": "candle_time.asc"},
                         headers={"apikey": key, "Authorization": f"Bearer {key}", "Range-Unit": "items",
                                  "Range": f"{lo}-{lo + 999}"}, timeout=60)
        r.raise_for_status(); ch = r.json(); rows += ch
        if len(ch) < 1000: break
        lo += 1000
    d = pd.DataFrame(rows)
    d["ts"] = pd.to_datetime(d.candle_time, utc=True, format="ISO8601")
    d = d[(d.ts.dt.second == 0)].sort_values("ts").drop_duplicates("ts")
    d[["ts", "open", "high", "low", "close", "volume"]].to_parquet(DATA / f"dax_{tf}.parquet")
    be = d.ts.dt.tz_convert("Europe/Berlin")
    d["rng"] = d.high - d.low
    g = d.assign(y=be.dt.year.values, m=(be.dt.hour * 60 + be.dt.minute).values).groupby(["y", "m"]).rng.median().reset_index()
    pk = g.loc[g.groupby("y").rng.idxmax()]
    print(tf, len(d), d.ts.min(), d.ts.max(), "en oynak Berlin dakikası/yıl:", [(int(a), f"{int(b)//60:02d}:{int(b)%60:02d}") for a, b in zip(pk.y, pk.m)][-12:])
    print("   yıl başına bar:", d.ts.dt.year.value_counts().sort_index().to_dict())
