"""Dukascopy 1m BID+ASK, yalnız ABD olay günleri (NFP/CPI/FOMC/JH) 2012→2026-11, 5 USD majör. Bağımsız besleme (EK-6).
Kullanım: python duka_olay.py indir | build"""
from __future__ import annotations
import datetime as dt, lzma, struct, sys, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "fibo_altin_bolge_20261116" / "src"))
import duka_pull as dp  # noqa: E402

HERE = Path(__file__).resolve().parent
CH = HERE / "data" / "duka"
PAIRS = ["EURUSD", "USDJPY", "GBPUSD", "AUDUSD", "USDCAD"]
SCALE = {p: (1000.0 if p.endswith("JPY") else 100000.0) for p in PAIRS}
dp.CH = CH
dp.FEEDS.update({p: p for p in PAIRS})


def event_days() -> list[dt.date]:
    c = pd.read_csv(HERE.parent / "xau_best_days_20261015/makro/out/calendar.csv")
    d = pd.to_datetime(c.date)
    return sorted({x.date() for x in d if pd.Timestamp("2012-01-01") <= x <= pd.Timestamp("2026-11-13")})


def indir() -> None:
    todo = [(p, d, sd) for p in PAIRS for d in event_days() for sd in ("BID", "ASK")]
    for p in PAIRS:
        (CH / p).mkdir(parents=True, exist_ok=True)
    todo = [x for x in todo if not (CH / x[0] / f"{x[1]:%Y%m%d}_{x[2]}.bi5").exists()]
    print("todo", len(todo), flush=True)
    n = 0
    with ThreadPoolExecutor(16) as ex:
        for _ in ex.map(lambda x: dp._get(*x), todo):
            n += 1
            if n % 200 == 0:
                print(time.strftime("%H:%M:%S"), n, "/", len(todo), flush=True)
    print("İNDİRME BİTTİ", n, flush=True)


def build() -> None:
    for p in PAIRS:
        bid, ask = [], []
        for f in sorted((CH / p).glob("*.bi5")):
            d = dt.date(int(f.name[:4]), int(f.name[4:6]), int(f.name[6:8]))
            (bid if f.stem.endswith("BID") else ask).extend(dp.rows(f.read_bytes(), d, SCALE[p]))
        cols = ["t", "o", "h", "l", "c", "v"]
        b = pd.DataFrame(bid, columns=cols).drop_duplicates("t").sort_values("t")
        a = pd.DataFrame(ask, columns=cols).drop_duplicates("t")[["t", "o", "h", "l", "c"]].add_prefix("a_").rename(columns={"a_t": "t"})
        x = b.merge(a, on="t", how="left").reset_index(drop=True)
        x.to_parquet(HERE / "data" / f"duka_{p}_olay_1m.parquet")
        print(p, len(x), flush=True)


if __name__ == "__main__":
    {"indir": indir, "build": build}[sys.argv[1]]()
