"""Önek sızıntı testi: kesimden sonrası çöpe çevrilince kesimden ÖNCE dolan işlemlerin girişi/stopu değişmemeli."""
from __future__ import annotations

import numpy as np
import pandas as pd

import akn as A
import mtf as M


def sub(d: pd.DataFrame) -> M.Base:
    return M.make_base(d, "NDX", 1)


def sig(B, chain, ltf, em):
    cx = A.build(B)
    df = A.run(cx, chain, ltf, em)
    return set() if df.empty else {(r.side, r.f, round(r.entry, 3), round(r.stop, 3)) for r in df.itertuples()}, cx


def main() -> None:
    d = pd.read_parquet(A.DATA)
    d = d.assign(ts=pd.to_datetime(d.t, unit="s", utc=True), spread=d.spr.astype(float))
    d = d[(d.ts >= "2025-01-01") & (d.ts < "2025-04-01")].sort_values("ts").drop_duplicates("ts").reset_index(drop=True)
    d = d[["ts", "open", "high", "low", "close", "spread", "src"]]
    rng = np.random.default_rng(7)
    for cut_ts in ("2025-02-11 15:43", "2025-03-06 20:17"):
        c = int(np.searchsorted(d.ts, pd.Timestamp(cut_ts, tz="UTC")))
        g = d.copy()
        w = g.close.iloc[c - 1] + np.cumsum(rng.normal(0, 6, len(g) - c))
        g.loc[c:, "open"], g.loc[c:, "close"] = w, w + rng.normal(0, 3, len(w))
        g.loc[c:, "high"] = np.maximum(g.loc[c:, "open"], g.loc[c:, "close"]) + rng.exponential(4, len(w))
        g.loc[c:, "low"] = np.minimum(g.loc[c:, "open"], g.loc[c:, "close"]) - rng.exponential(4, len(w))
        Bf, Bg = sub(d), sub(g)
        for chain in ("K1K2", "K2", "K1", "K0"):
            for ltf in ("C53", "C1"):
                a, _ = sig(Bf, chain, ltf, "E50")
                b, _ = sig(Bg, chain, ltf, "E50")
                a = {x for x in a if x[1] < c}
                b = {x for x in b if x[1] < c}
                assert a == b, (cut_ts, chain, ltf, a ^ b)
                print(f"önek {cut_ts} {chain} {ltf}: {len(a)} işlem aynı", flush=True)
    print("ÖNEK TESTİ GEÇTİ")


if __name__ == "__main__":
    main()
