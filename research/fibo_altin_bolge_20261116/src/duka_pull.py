"""Dukascopy 1m BID (2018-01 → 2026-11-14) + ASK (yalnız 2025, spread modeli için) — DAX ve XAU (EK-3).

Tek işçi, nazik (istek arası PACE_S), 503/429'da üstel geri çekilme, kaldığı yerden sürer.
Kullanım: python src/duka_pull.py DAX   → data/chunks/DAX/YYYYMMDD_<SIDE>.bi5 ; sonra build → cache/<SYM>_1m_raw.parquet
"""
from __future__ import annotations

import datetime as dt
import lzma
import os
import struct
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parents[1]
CH = HERE / "data" / "chunks"
FEEDS = {"DAX": "DEUIDXEUR", "XAU": "XAUUSD", "CAC": "FRAIDXEUR", "STOXX": "EUSIDXEUR"}
SCALE = {"DAX": 1000.0, "XAU": 1000.0, "CAC": 1000.0, "STOXX": 1000.0}
BID_RANGE = (dt.date(2018, 1, 1), dt.date(2026, 11, 14))
ASK_RANGE = (dt.date(2025, 1, 1), dt.date(2025, 12, 31))
PACE_S = float(os.getenv("DUKA_PACE_S", "0.5"))
MAX_BLOCK_S = 3 * 3600
MAX_TRIES = int(os.getenv("DUKA_MAX_TRIES", "4"))
WORKERS = int(os.getenv("DUKA_WORKERS", "16"))


def days(a: dt.date, b: dt.date):
    while a <= b:
        if a.weekday() != 5:
            yield a
        a += dt.timedelta(1)


import http.client
import threading

_TL = threading.local()


def _conn() -> http.client.HTTPSConnection:
    c = getattr(_TL, "c", None)
    if c is None:
        c = _TL.c = http.client.HTTPSConnection("datafeed.dukascopy.com", timeout=180)
    return c


def _get(sym: str, d: dt.date, sd: str) -> bool:
    """Kalıcı (keep-alive) bağlantı: sunucu yeni TCP bağlantılarını yavaş kabul ediyor (2026-11-17)."""
    out = CH / sym / f"{d:%Y%m%d}_{sd}.bi5"
    path = f"/datafeed/{FEEDS[sym]}/{d:%Y}/{d.month - 1:02d}/{d:%d}/{sd}_candles_min_1.bi5"
    wait, blocked = 30, 0
    while True:
        try:
            c = _conn()
            c.request("GET", path, headers={"User-Agent": "Mozilla/5.0", "Connection": "keep-alive"})
            r = c.getresponse()
            body = r.read()
            if r.status == 200:
                raw = body
                break
            if r.status == 404:
                raw = b""
                break
            code = r.status
        except Exception as e:  # noqa: BLE001
            code = type(e).__name__
            try:
                _TL.c.close()
            except Exception:  # noqa: BLE001
                pass
            _TL.c = None
        print(time.strftime("%H:%M:%S"), sym, "engel", code, d, sd, "bekle", wait, flush=True)
        time.sleep(wait)
        blocked += 1
        wait = min(wait * 2, 120)
        if blocked >= MAX_TRIES:          # tekil kalıcı 503 günü işçiyi kilitlemesin; sonraki turda yeniden denenir
            print("ATLANDI", sym, d, sd, flush=True)
            return False
    out.write_bytes(raw)
    time.sleep(PACE_S)
    return True


def fetch_all(sym: str) -> None:
    """Sunucu her isteğe ~20 sn gecikmeyle yanıt veriyor (2026-11-17 ölçümü) → WORKERS paralel işçi."""
    from concurrent.futures import ThreadPoolExecutor
    (CH / sym).mkdir(parents=True, exist_ok=True)
    ask_days = [d for d in days(*ASK_RANGE) if d.weekday() == 2]      # 2025 Çarşambaları yeter (saat profili)
    todo = [(d, "BID") for d in days(*BID_RANGE)] + [(d, "ASK") for d in ask_days]
    todo = [x for x in todo if not (CH / sym / f"{x[0]:%Y%m%d}_{x[1]}.bi5").exists()]
    print(sym, "todo", len(todo), flush=True)
    done = 0
    with ThreadPoolExecutor(WORKERS) as ex:
        for ok in ex.map(lambda x: _get(sym, *x), todo):
            done += 1
            if not ok:
                print("VAZGEÇİLEN GÜN", sym, flush=True)
            if done % 100 == 0:
                print(time.strftime("%H:%M:%S"), sym, done, "/", len(todo), flush=True)
    print("İNDİRME BİTTİ", sym, done, flush=True)


def rows(raw: bytes, d: dt.date, scale: float) -> list[list[float]]:
    if not raw:
        return []
    base = int(dt.datetime.combine(d, dt.time(), tzinfo=dt.timezone.utc).timestamp())
    return [[base + s, o / scale, hi / scale, lo / scale, c / scale, v]
            for s, o, c, lo, hi, v in struct.iter_unpack(">5If", lzma.decompress(raw)) if v > 0 and min(o, c, lo, hi) > 0]


def build(sym: str) -> None:
    out = CH / sym
    cols = ["t", "open", "high", "low", "close", "vol"]
    bid, ask = [], []
    for f in sorted(out.glob("*.bi5")):
        d = dt.date(int(f.name[:4]), int(f.name[4:6]), int(f.name[6:8]))
        (bid if f.stem.endswith("BID") else ask).extend(rows(f.read_bytes(), d, SCALE[sym]))
    b = pd.DataFrame(bid, columns=cols).drop_duplicates("t").sort_values("t")
    a = pd.DataFrame(ask, columns=cols).drop_duplicates("t")[["t", "open"]].rename(columns={"open": "ask_open"})
    x = b.merge(a, on="t", how="left").reset_index(drop=True)
    (HERE / "cache").mkdir(exist_ok=True)
    x.to_parquet(HERE / "cache" / f"{sym}_1m_raw.parquet", index=False)
    print(sym, "yapıldı", len(x), pd.to_datetime(x.t.min(), unit="s"), pd.to_datetime(x.t.max(), unit="s"),
          "medyan", round(x.close.median(), 2), flush=True)


if __name__ == "__main__":
    for s in sys.argv[1:]:
        for _ in range(3):                # üç tur: atlanan günler yeniden
            fetch_all(s)
        build(s)
