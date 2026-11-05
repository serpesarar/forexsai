"""Dukascopy 1m bid/ask (gerçek UTC, bar başlangıç damgası), 4 sembol. Uç nokta ve biçim fcr_ilk_mum_20261027/pull_duka.py ile aynı.

Tek işçi, istekler arası 1 sn, 429'da uzun geri çekilme. Kaldığı yerden sürer (gün dosyaları `data/chunks`).
"""
from __future__ import annotations
import datetime as dt, lzma, struct, sys, time, urllib.error, urllib.request
from pathlib import Path
import pandas as pd

DATA = Path(__file__).resolve().parent / "data"
FEEDS = {"NDX": "USA100IDXUSD", "DAX": "DEUIDXEUR", "XAU": "XAUUSD", "USOIL": "LIGHTCMDUSD"}
SCALE = {"NDX": 1000.0, "DAX": 1000.0, "XAU": 1000.0, "USOIL": 1000.0}
BEGIN, END = dt.date(2020, 1, 1), dt.date(2026, 11, 5)
PAUSE_S = 1.0
BACKOFF_S = 120


def fetch(sym: str, d: dt.date, side: str) -> bytes:
    p = DATA / "chunks" / sym / f"{d:%Y%m%d}_{side}.bi5"
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists():
        return p.read_bytes()
    url = f"https://datafeed.dukascopy.com/datafeed/{FEEDS[sym]}/{d:%Y}/{d.month - 1:02d}/{d:%d}/{side}_candles_min_1.bi5"
    tries = 0
    while True:
        try:
            with urllib.request.urlopen(urllib.request.Request(url), timeout=40) as r:
                raw = r.read()
            break
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raw = b""
                break
            tries += 1
            print(f"{sym} {d} {side} HTTP {e.code}, {BACKOFF_S * tries}s", flush=True)
            time.sleep(BACKOFF_S * min(tries, 5))
        except Exception as e:
            tries += 1
            print(f"{sym} {d} {side} {type(e).__name__}", flush=True)
            time.sleep(30)
    p.write_bytes(raw)
    time.sleep(PAUSE_S)
    return raw


def rows(raw: bytes, d: dt.date, scale: float) -> list[list[float]]:
    if not raw:
        return []
    base = int(dt.datetime.combine(d, dt.time(), tzinfo=dt.timezone.utc).timestamp())
    out = []
    for secs, o, c, lo, hi, v in struct.iter_unpack(">5If", lzma.decompress(raw)):
        if v > 0 and min(o, c, lo, hi) > 0:
            out.append([base + secs, o / scale, hi / scale, lo / scale, c / scale, v])
    return out


def build(sym: str) -> None:
    days = [BEGIN + dt.timedelta(days=i) for i in range((END - BEGIN).days) if (BEGIN + dt.timedelta(days=i)).weekday() != 5]
    days = days[::-1]   # yeniden eskiye: en değerli dönem önce iner
    by = {"BID": [], "ASK": []}
    for i, d in enumerate(days, 1):
        for side in by:
            by[side] += rows(fetch(sym, d, side), d, SCALE[sym])
        if i % 100 == 0:
            print(sym, i, "/", len(days), d, flush=True)
    cols = ["t", "open", "high", "low", "close", "volume"]
    bid = pd.DataFrame(by["BID"], columns=cols).drop_duplicates("t")
    ask = pd.DataFrame(by["ASK"], columns=cols).drop_duplicates("t")[["t", "open", "high", "low", "close"]]
    ask.columns = ["t", "ask_open", "ask_high", "ask_low", "ask_close"]
    x = bid.merge(ask, on="t").sort_values("t").reset_index(drop=True)
    x["ts"] = pd.to_datetime(x.t, unit="s", utc=True)
    x["spread_px"] = x.ask_open - x.open
    x.to_parquet(DATA / f"{sym}_1m.parquet", index=False)
    print(sym, "bitti", len(x), x.ts.min(), x.ts.max(), "medyan fiyat", round(x.close.median(), 2), "medyan spread", round(x.spread_px.median(), 4), flush=True)


if __name__ == "__main__":
    for s in sys.argv[1:]:
        build(s)
