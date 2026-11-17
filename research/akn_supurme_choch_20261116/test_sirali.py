"""Sıralı K1K2 kolunun kendi işlemleriyle hedefli önek testi: her işlemin dolumundan 1 dk sonra veri çöpe çevrilir."""
import numpy as np
import pandas as pd
import akn as A
import mtf as M

d = pd.read_parquet(A.DATA)
d = d.assign(ts=pd.to_datetime(d.t, unit="s", utc=True), spread=d.spr.astype(float)).sort_values("ts").drop_duplicates("ts").reset_index(drop=True)
d = d[["ts", "open", "high", "low", "close", "spread", "src"]]
t = pd.read_parquet("results/islemler.parquet")
t = t[(t.chain == "K1K2") & (t.ltf_v == "C53") & (t.giris == "E50")].sort_values("um")
rng = np.random.default_rng(3)
ok = 0
for um in t.um.iloc[::8]:
    ts = pd.Timestamp(int(um) * 60, unit="s", tz="UTC")
    w = d[d.ts < ts + pd.Timedelta(days=3)].reset_index(drop=True)
    c = int(np.searchsorted(w.ts, ts + pd.Timedelta(minutes=1)))
    g = w.copy()
    z = g.close.iloc[c - 1] + np.cumsum(rng.normal(0, 8, len(g) - c))
    g.loc[c:, ["open", "close"]] = np.c_[z, z + rng.normal(0, 3, len(z))]
    g.loc[c:, "high"] = g.loc[c:, ["open", "close"]].max(axis=1) + 4
    g.loc[c:, "low"] = g.loc[c:, ["open", "close"]].min(axis=1) - 4
    res = []
    for x in (w, g):
        cx = A.build(M.make_base(x, "NDX", 1))
        df = A.run(cx, "K1K2", "C53", "E50")
        res.append({(r.side, r.um, round(r.entry, 3), round(r.stop, 3)) for r in df.itertuples() if r.um <= um})
    assert res[0] == res[1], (ts, res[0] ^ res[1])
    assert any(r[1] == um for r in res[0]), ("işlem pencerede yeniden üretilmedi", ts)
    ok += 1
print("hedefli önek testi geçti:", ok, "işlem")
