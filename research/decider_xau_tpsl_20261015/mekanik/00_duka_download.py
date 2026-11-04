"""Dukascopy XAUUSD 1m BID+ASK gün dosyalarını indirir (UTC, bar BAŞLANGIÇ damgası).

Kaynak: https://datafeed.dukascopy.com/datafeed/XAUUSD/YYYY/MM(0-index)/DD/{BID,ASK}_candles_min_1.bi5
Kayıt: 24 bayt big-endian: int32 saniye(gün başından), int32 open, close, low, high (×1e-3), float32 volume.
Çıktı: data/duka/raw/{side}/{YYYY-MM-DD}.bi5 (ham, önbellek) — 01_build_duka.py çözer.
Kullanım: python3 -I 00_duka_download.py 2008-01-01 2026-10-15
"""
from __future__ import annotations
import os, sys, time, datetime as dt, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(ROOT, "data", "duka", "raw")
UA = {"User-Agent": "Mozilla/5.0"}

MODE = os.environ.get("DUKA_MODE", "min")  # min: gün dosyası 1m | hour: ay dosyası 1h

def url(d: dt.date, side: str) -> str:
    if MODE == "hour":
        return (f"https://datafeed.dukascopy.com/datafeed/XAUUSD/{d.year}/{d.month-1:02d}/"
                f"{side}_candles_hour_1.bi5")
    return (f"https://datafeed.dukascopy.com/datafeed/XAUUSD/{d.year}/{d.month-1:02d}/{d.day:02d}/"
            f"{side}_candles_min_1.bi5")

def fetch(args) -> str:
    d, side = args
    sub = side if MODE == "min" else side + "_H1"
    out = os.path.join(RAW, sub, f"{d.isoformat()}.bi5")
    if os.path.exists(out):
        return "skip"
    for attempt in range(6):
        try:
            req = urllib.request.Request(url(d, side), headers=UA)
            with urllib.request.urlopen(req, timeout=30) as r:
                data = r.read()
            tmp = out + ".tmp"
            with open(tmp, "wb") as f:
                f.write(data)
            os.replace(tmp, out)
            return "ok"
        except urllib.error.HTTPError as e:
            if e.code == 404:
                open(out, "wb").close()
                return "404"
            time.sleep(2 + 5 * attempt)
        except Exception:
            time.sleep(2 + 5 * attempt)
    return "fail"

if __name__ == "__main__":
    a = dt.date.fromisoformat(sys.argv[1]); b = dt.date.fromisoformat(sys.argv[2])
    sides = sys.argv[3].split(",") if len(sys.argv) > 3 else ["BID", "ASK"]
    nthr = int(os.environ.get("DUKA_THREADS", "6"))
    for s in sides:
        os.makedirs(os.path.join(RAW, s if MODE == "min" else s + "_H1"), exist_ok=True)
    jobs = []
    d = a
    if MODE == "hour":
        d = d.replace(day=1)
        while d < b:
            for s in sides:
                jobs.append((d, s))
            d = (d.replace(day=28) + dt.timedelta(days=4)).replace(day=1)
    else:
        while d < b:
            if d.weekday() != 5:  # Cumartesi boş
                for s in sides:
                    jobs.append((d, s))
            d += dt.timedelta(days=1)
        if os.environ.get("DUKA_REVERSE"):
            jobs = jobs[::-1]
    cnt = {}
    t0 = time.time()
    with ThreadPoolExecutor(nthr) as ex:
        for i, r in enumerate(ex.map(fetch, jobs)):
            cnt[r] = cnt.get(r, 0) + 1
            if i % 100 == 0:
                print(i, len(jobs), cnt, f"{time.time()-t0:.0f}s", flush=True)
    print("DONE", cnt, f"{time.time()-t0:.0f}s")
