"""dogrula.py — taban CAPREV'in NX-01 (Duka 1m, n 103, +0,278R) ve kart (MT5 uzun 1h, n 107, +0,240R) ile uyumu."""
import time, pandas as pd
import cr_motor as M
for n in ["DUKA_NDX", "MT5_LONG1H"]:
    t0 = time.time(); F = M.Feed(n); T = F.table()
    print(n, len(T), "R", round(T.R.mean(), 3), "bp", round(T.base.mean(), 1), "SL", (T.cls == "SL").sum(),
          "TP", (T.cls == "TP").sum(), "ZK", (T.cls == "ZK").sum(), T.d.min().date(), T.d.max().date(), f"{time.time()-t0:.0f}s")
    T.to_parquet(M.HERE / f"cache/{n}.parquet") if (M.HERE / "cache").exists() else None
