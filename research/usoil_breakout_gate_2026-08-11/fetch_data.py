"""candle_cache'ten USOIL 5m + 1m barlarini indirip parquet'e yazar."""
from __future__ import annotations
import os, re, sys
from pathlib import Path
import pandas as pd, requests

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "data"
OUT.mkdir(exist_ok=True)

txt = (ROOT / "yeni deneme" / "config.py").read_text(encoding="utf-8", errors="replace")
URL = re.search(r'SUPABASE_URL\s*=\s*["\']([^"\']+)["\']', txt).group(1)
KEY = re.search(r'SUPABASE_SERVICE_KEY\s*=\s*["\']([^"\']+)["\']', txt).group(1)
H = {"apikey": KEY, "Authorization": f"Bearer {KEY}"}


def pull(symbol: str, tf: str) -> pd.DataFrame:
    rows, page, step = [], 0, 1000
    while True:
        r = requests.get(
            f"{URL}/rest/v1/candle_cache",
            headers=H,
            params={"symbol": f"eq.{symbol}", "timeframe": f"eq.{tf}",
                    "select": "candle_time,open,high,low,close,volume",
                    "order": "candle_time.asc",
                    "offset": page * step, "limit": step},
            timeout=90,
        )
        r.raise_for_status()
        b = r.json()
        rows += b
        print(f"  {tf}: {len(rows)}", end="\r", flush=True)
        if len(b) < step:
            break
        page += 1
    df = pd.DataFrame(rows)
    df["candle_time"] = pd.to_datetime(df["candle_time"], utc=True)
    df = df.drop_duplicates("candle_time").sort_values("candle_time").reset_index(drop=True)
    print(f"  {tf}: {len(df)} bar  {df.candle_time.iloc[0]} → {df.candle_time.iloc[-1]}")
    return df


if __name__ == "__main__":
    sym = sys.argv[1] if len(sys.argv) > 1 else "USOIL.FOREX"
    for tf in ("5m", "1m"):
        pull(sym, tf).to_parquet(OUT / f"{sym.replace('.','_')}_{tf}.parquet")
