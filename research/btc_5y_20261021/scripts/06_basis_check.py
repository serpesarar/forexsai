"""Baz farkının kaynağı: broker BTCUSD mid vs Binance BTCUSDT vs Coinbase BTC-USD,
ve Coinbase USDT-USD kuru. Coinbase mumu: [time, low, high, open, close, volume].

Kullanım: python -I 06_basis_check.py <data_dir>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd


def cb(path: Path) -> pd.Series:
    rows = json.loads(path.read_text())
    df = pd.DataFrame(rows, columns=["t", "low", "high", "open", "close", "vol"])
    return df.set_index(pd.to_datetime(df["t"], unit="s", utc=True))["close"].sort_index()


def main() -> None:
    d = Path(sys.argv[1])
    b = pd.read_parquet(d / "broker_btcusd_m1.parquet").set_index("ts_utc")
    b["mid"] = b["close"] + b["spread_usd"] / 2
    n = pd.read_parquet(d / "btc_1m.parquet", columns=["ts", "close"]).set_index("ts")["close"]
    out = []
    for p in sorted((d / "raw" / "coinbase").glob("btcusd_*.json")):
        day = p.stem.split("_")[1]
        c = cb(p)
        u = cb(d / "raw" / "coinbase" / f"usdtusd_{day}.json")
        j = pd.concat([b["mid"].rename("broker_mid"), n.rename("binance_usdt"), c.rename("coinbase_usd"),
                       u.rename("usdt_usd")], axis=1, join="inner").dropna()
        j["binance_in_usd"] = j["binance_usdt"] * j["usdt_usd"]
        out.append({"day": day, "n": len(j),
                    "broker_minus_coinbase_med": round(float((j.broker_mid - j.coinbase_usd).median()), 2),
                    "binance_minus_coinbase_med": round(float((j.binance_usdt - j.coinbase_usd).median()), 2),
                    "binanceUSD_minus_coinbase_med": round(float((j.binance_in_usd - j.coinbase_usd).median()), 2),
                    "broker_minus_binance_med": round(float((j.broker_mid - j.binance_usdt).median()), 2),
                    "usdt_usd_med": round(float(j.usdt_usd.median()), 5)})
    print(json.dumps(out, indent=1))
    (d / "basis_check.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
