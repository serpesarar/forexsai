"""pull_data.py — Supabase'ten NDX araştırma veri setini indir (yerel, Mac).

Çıktılar → research/ndx_buy_lab/data/
  bars_<TF>.csv         NDX.INDX mumları (candle_cache), tick-kirliliği temizli
  signals.csv           prediction_logs NDX sinyalleri (factors JSON dahil)
  macro_daily.csv       VIX/DXY/US10Y/QQQ günlük (yfinance) — SADECE önceki kapanış

Dürüstlük notları:
  * 1m mumlarında saniye != 0 olan satırlar TICK KİRLİLİĞİDİR (memory:
    candle-tick-pollution-fix) → atılır.
  * Aynı (tf, ts) için birden fazla satır varsa en son fetched_at kazanır.
  * Makro veriler günlüktür; kullanımda MUTLAKA bir gün kaydırılır (bugünün
    kapanışı karar anında bilinemez).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "data"
OUT.mkdir(exist_ok=True)

sys.path.insert(0, str(ROOT / "backend"))

SYMBOL = "NDX.INDX"
TFS = ["1m", "5m", "15m", "30m", "1h"]
PAGE = 1000


def client():
    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT / "backend" / ".env")
    except ImportError:
        pass
    url = os.getenv("SUPABASE_URL")
    key = (os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_SERVICE_KEY")
           or os.getenv("SUPABASE_KEY"))
    if not url or not key:
        sys.exit("SUPABASE_URL/KEY yok")
    from supabase import create_client
    return create_client(url, key)


def fetch_all(cl, table: str, select: str, filters: list, order_col: str) -> pd.DataFrame:
    """Keyset yerine range pagination (order sabit) — tüm satırları getirir."""
    rows, start = [], 0
    while True:
        q = cl.table(table).select(select)
        for col, op, val in filters:
            q = getattr(q, op)(col, val)
        q = q.order(order_col).range(start, start + PAGE - 1)
        r = q.execute()
        batch = r.data or []
        rows.extend(batch)
        if len(batch) < PAGE:
            break
        start += PAGE
        if start % 20000 == 0:
            print(f"    …{start}", flush=True)
    return pd.DataFrame(rows)


def pull_bars(cl) -> None:
    for tf in TFS:
        print(f"  bars {tf} …", flush=True)
        df = fetch_all(
            cl, "candle_cache",
            "candle_time,open,high,low,close,volume,fetched_at",
            [("symbol", "eq", SYMBOL), ("timeframe", "eq", tf)],
            "candle_time",
        )
        if df.empty:
            print(f"    {tf}: BOŞ")
            continue
        df["ts"] = pd.to_datetime(df["candle_time"], utc=True)
        n0 = len(df)
        # tick kirliliği: saniye/mikrosaniye sıfır olmalı
        df = df[(df["ts"].dt.second == 0) & (df["ts"].dt.microsecond == 0)]
        # TF ızgarasına hizalı mı?
        minute_grid = {"1m": 1, "5m": 5, "15m": 15, "30m": 30, "1h": 60}[tf]
        mins = df["ts"].dt.hour * 60 + df["ts"].dt.minute
        df = df[mins % minute_grid == 0]
        # duplikeler: en son fetched_at kazanır
        df = (df.sort_values(["ts", "fetched_at"])
                .drop_duplicates("ts", keep="last")
                .sort_values("ts"))
        df = df[["ts", "open", "high", "low", "close", "volume"]]
        df.to_csv(OUT / f"bars_{tf}.csv", index=False)
        print(f"    {tf}: {len(df)} bar (ham {n0}, atılan {n0-len(df)})  "
              f"{df['ts'].min()} → {df['ts'].max()}")


def pull_signals(cl) -> None:
    print("  signals …", flush=True)
    df = fetch_all(
        cl, "prediction_logs",
        ("id,created_at,symbol,timeframe,model_type,ml_direction,ml_confidence,"
         "ml_entry_price,ml_target_price,ml_stop_price,status,close_reason,"
         "resolution_reason,exit_price,closed_at,targets,targets_hit,"
         "highest_profit_pips,lowest_drawdown_pips,factors,signal_source,strategy"),
        [("symbol", "eq", SYMBOL)],
        "created_at",
    )
    if df.empty:
        print("    BOŞ"); return
    for col in ("factors", "targets", "targets_hit"):
        if col in df.columns:
            df[col] = df[col].apply(lambda v: json.dumps(v, ensure_ascii=False)
                                    if isinstance(v, (dict, list)) else v)
    df.to_csv(OUT / "signals.csv", index=False)
    print(f"    {len(df)} sinyal  {df['created_at'].min()} → {df['created_at'].max()}")


def pull_macro() -> None:
    print("  makro (yfinance) …", flush=True)
    try:
        import yfinance as yf
    except ImportError:
        print("    yfinance yok — atlandı"); return
    tickers = {"VIX": "^VIX", "DXY": "DX-Y.NYB", "US10Y": "^TNX",
               "QQQ": "QQQ", "NDXCASH": "^NDX", "SPX": "^GSPC",
               "VIX3M": "^VIX3M", "HYG": "HYG", "TLT": "TLT"}
    frames = []
    for name, t in tickers.items():
        try:
            d = yf.download(t, start="2024-01-01", progress=False, auto_adjust=False)
            if d is None or d.empty:
                print(f"    {name}: boş"); continue
            if isinstance(d.columns, pd.MultiIndex):
                d.columns = d.columns.get_level_values(0)
            s = d[["Close", "High", "Low", "Open"]].copy()
            s.columns = [f"{name}_close", f"{name}_high", f"{name}_low", f"{name}_open"]
            frames.append(s)
        except Exception as e:
            print(f"    {name}: hata {e}")
    if not frames:
        return
    m = pd.concat(frames, axis=1).sort_index()
    m.index.name = "date"
    m.to_csv(OUT / "macro_daily.csv")
    print(f"    {len(m)} gün  {m.index.min().date()} → {m.index.max().date()}")


if __name__ == "__main__":
    cl = client()
    pull_bars(cl)
    pull_signals(cl)
    pull_macro()
    print("bitti →", OUT)
