"""tablolar.py — her besleme için işlem tablosu → cache/<feed>.parquet. python tablolar.py"""
import time
import pandas as pd
import cr_motor as M
import cr_gunluk as G

FEEDS = ["DUKA_NDX", "MT5_NAS100", "MT5_US500", "MT5_US30", "MT5_US2000", "DUKA_DAX", "MT5_GER40",
         "EET30", "NQ", "DUKA_M30_2016_17", "MT5_LONG1H"]
if __name__ == "__main__":
    for n in FEEDS:
        t0 = time.time()
        T = M.Feed(n).table()
        T.to_parquet(M.HERE / f"cache/{n}.parquet")
        print(n, len(T), round(T.base.mean(), 1), (T.cls == "SL").mean().round(3), T.d.min().date(), T.d.max().date(),
              f"{time.time()-t0:.0f}s", flush=True)
    for nm, a, b in (("U_NDX_GUNLUK", "1990-01-01", "2015-12-31"), ("U_NDX_GUNLUK_2016", "2016-01-01", "2026-12-31")):
        T = G.table(a, b)
        T.to_parquet(M.HERE / f"cache/{nm}.parquet")
        print(nm, len(T), round(T.base.mean(), 1), (T.cls == "SL").mean().round(3), T.d.min().date(), T.d.max().date(), flush=True)
