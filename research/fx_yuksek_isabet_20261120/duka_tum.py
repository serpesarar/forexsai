"""Dukascopy 1m BID+ASK tüm günler 2015-01 → 2026-11-13, 5 USD majör (EK-7). Kullanım: indir | build"""
from __future__ import annotations
import datetime as dt, sys, time
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
import duka_olay as du
dp = du.dp
A, B = dt.date(2018, 1, 1), dt.date(2026, 11, 13)
PAIRS = ["AUDUSD", "GBPUSD", "EURUSD", "USDCAD"]


def indir() -> None:
    todo = [(p, d, "BID") for p in PAIRS for d in dp.days(A, B)] + [(p, d, "ASK") for p in PAIRS for d in dp.days(A, B) if d.weekday() == 2]
    todo = [x for x in todo if not (du.CH / x[0] / f"{x[1]:%Y%m%d}_{x[2]}.bi5").exists()]
    print("todo", len(todo), flush=True)
    n = 0
    with ThreadPoolExecutor(16) as ex:
        for _ in ex.map(lambda x: dp._get(*x), todo):
            n += 1
            if n % 1000 == 0:
                print(time.strftime("%H:%M:%S"), n, "/", len(todo), flush=True)
    print("İNDİRME BİTTİ", n, flush=True)


def build() -> None:
    for p in PAIRS:
        bid, ask = [], []
        for f in sorted((du.CH / p).glob("*.bi5")):
            d = dt.date(int(f.name[:4]), int(f.name[4:6]), int(f.name[6:8]))
            if d < A:
                continue
            (bid if f.stem.endswith("BID") else ask).extend(dp.rows(f.read_bytes(), d, du.SCALE[p]))
        cols = ["t", "o", "h", "l", "c", "v"]
        b = pd.DataFrame(bid, columns=cols).drop_duplicates("t").sort_values("t")
        a = pd.DataFrame(ask, columns=cols).drop_duplicates("t")[["t", "o", "h", "l", "c"]].add_prefix("a_").rename(columns={"a_t": "t"})
        b.merge(a, on="t", how="left").reset_index(drop=True).to_parquet(du.HERE / "data" / f"duka_{p}_1m.parquet")
        print(p, len(b), flush=True)


if __name__ == "__main__":
    {"indir": indir, "build": build}[sys.argv[1]]()
