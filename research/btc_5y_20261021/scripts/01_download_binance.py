"""Binance public data (data.binance.vision) BTCUSDT 1m kline indirici.

Aylık zip'ler (2021-06 .. 2026-09) + Ekim 2026 günlük zip'ler (01..20).
Her zip'in .CHECKSUM (SHA256) dosyası indirilip doğrulanır. Zip içeriği
ÇALIŞTIRILMAZ, yalnız CSV olarak okunur (02_build.py).

Kullanım: python -I 01_download_binance.py <raw_dir>
"""
from __future__ import annotations

import hashlib
import sys
import time
import urllib.request
from pathlib import Path

BASE = "https://data.binance.vision/data/spot"
SYMBOL = "BTCUSDT"
START = (2021, 6)
END_MONTH = (2026, 9)
DAILY_MONTH = "2026-10"
DAILY_DAYS = range(1, 21)


def months():
    y, m = START
    while (y, m) <= END_MONTH:
        yield f"{y:04d}-{m:02d}"
        m += 1
        if m == 13:
            y, m = y + 1, 1


def fetch(url: str, retries: int = 4) -> bytes:
    for i in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001
            if i == retries - 1:
                raise
            print(f"  retry {url}: {e}", flush=True)
            time.sleep(2 * (i + 1))
    raise RuntimeError


def get(url: str, dest: Path) -> str:
    ck = fetch(url + ".CHECKSUM").decode().split()[0].strip()
    if dest.exists() and hashlib.sha256(dest.read_bytes()).hexdigest() == ck:
        return "cached-ok"
    data = fetch(url)
    h = hashlib.sha256(data).hexdigest()
    if h != ck:
        return f"CHECKSUM-MISMATCH {h} != {ck}"
    dest.write_bytes(data)
    return "ok"


def main() -> None:
    raw = Path(sys.argv[1])
    (raw / "monthly").mkdir(parents=True, exist_ok=True)
    (raw / "daily").mkdir(parents=True, exist_ok=True)
    log = []
    for ym in months():
        name = f"{SYMBOL}-1m-{ym}.zip"
        st = get(f"{BASE}/monthly/klines/{SYMBOL}/1m/{name}", raw / "monthly" / name)
        print(name, st, flush=True)
        log.append(f"{name}\t{st}")
    for d in DAILY_DAYS:
        name = f"{SYMBOL}-1m-{DAILY_MONTH}-{d:02d}.zip"
        try:
            st = get(f"{BASE}/daily/klines/{SYMBOL}/1m/{name}", raw / "daily" / name)
        except Exception as e:  # noqa: BLE001
            st = f"MISSING {e}"
        print(name, st, flush=True)
        log.append(f"{name}\t{st}")
    (raw / "download_log.tsv").write_text("\n".join(log) + "\n")


if __name__ == "__main__":
    main()
