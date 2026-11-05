"""Dukascopy 1m BID seri, nazik: istek arası 2 sn, engelde uzun geri çekilme. Kullanım: duka_serial.py XAU 2024-01-01 2026-11-04"""
from __future__ import annotations
import datetime as dt, lzma, struct, sys, time, urllib.error, urllib.request
from pathlib import Path
import pandas as pd
FEEDS = {"XAU": "XAUUSD", "USOIL": "LIGHTCMDUSD", "DAX": "DEUIDXEUR"}
OUT = Path(__file__).parent / "data"
def main(sym, a, b):
    out = OUT / sym; out.mkdir(parents=True, exist_ok=True)
    d = dt.date.fromisoformat(b); stop = dt.date.fromisoformat(a); done = 0; wait = 60
    while d >= stop:
        if d.weekday() != 5 and not (out / f"{d:%Y%m%d}.bi5").exists():
            url = f"https://datafeed.dukascopy.com/datafeed/{FEEDS[sym]}/{d:%Y}/{d.month-1:02d}/{d:%d}/BID_candles_min_1.bi5"
            while True:
                try:
                    raw = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "ForexSAI-research"}), timeout=60).read(); wait = 60; break
                except urllib.error.HTTPError as e:
                    if e.code == 404: raw = b""; break
                    print(time.strftime("%H:%M"), "engel", e.code, d, "bekle", wait, flush=True); time.sleep(wait); wait = min(wait * 2, 1800)
                except Exception as e:
                    print(time.strftime("%H:%M"), type(e).__name__, d, flush=True); time.sleep(wait); wait = min(wait * 2, 1800)
            (out / f"{d:%Y%m%d}.bi5").write_bytes(raw); done += 1
            if done % 50 == 0: print(time.strftime("%H:%M"), sym, done, d, flush=True)
            time.sleep(2.0)
        d -= dt.timedelta(days=1)
    print("BİTTİ", sym, done, flush=True)
if __name__ == "__main__":
    main(*sys.argv[1:4])
