"""SC-17 — Dukascopy DEUIDXEUR 1m BID + ASK Çarşamba 2012-01 → 2017-12 indirici (sc_duka._al'ı yeniden kullanır, sabırlı döngü)."""
from __future__ import annotations

import datetime as dt
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sc_duka as SD  # noqa: E402

SD.FEED = "DEUIDXEUR"
SD.CH = SD.KOK / "data" / "chunks" / "DAX"
ARALIK = (dt.date(2012, 1, 1), dt.date(2017, 12, 31))


def isler():
    out = [(d, "BID") for d in SD.gunler(*ARALIK)] + [(d, "ASK") for d in SD.gunler(*ARALIK) if d.weekday() == 2]
    return [x for x in out if not (SD.CH / f"{x[0]:%Y%m%d}_{x[1]}.bi5").exists()]


def main() -> None:
    SD.CH.mkdir(parents=True, exist_ok=True)
    onceki = None
    for tur in range(80):
        x = isler()
        print(time.strftime("%H:%M:%S"), "tur", tur, "kalan", len(x), flush=True)
        if not x:
            break
        if onceki is not None and len(x) >= onceki:
            time.sleep(600)
        onceki = len(x)
        with ThreadPoolExecutor(2) as ex:
            list(ex.map(lambda z: SD._al(*z), x))
    print("DAX İNDİRME BİTTİ, kalan", len(isler()), flush=True)


if __name__ == "__main__":
    main()
