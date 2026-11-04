"""Özellik + etiket veri setini kur: cache/dataset.parquet

Karar satırları: m, (m+1) % 5 == 0. Her hücre (yön × TP çarpanı × H) için: geçerlilik, brüt bp, çıkış tipi,
çıkış barı, aynı-bar bayrağı, iyimser brüt bp. s_bp ortak (karar anı ATR5).
"""
import os
import sys
import time

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import feat  # noqa: E402
import labels  # noqa: E402

CELLS = [(d, tp, H) for d in (1, -1) for tp in (1.0, 1.5) for H in (30, 60)]


def cell_name(d, tp, H):
    return f"{'L' if d == 1 else 'S'}_tp{tp:g}_h{H}"


def main():
    t0 = time.time()
    df = feat.load()
    n = len(df)
    X, G = feat.build_features(df)
    print(f"özellikler {X.shape} {time.time()-t0:.0f}s", flush=True)
    bad = feat.bad_mask(df)
    o = df["spot_open"].to_numpy().copy()
    h = df["spot_high"].to_numpy().copy()
    l = df["spot_low"].to_numpy().copy()
    c = df["spot_close"].to_numpy().copy()
    for a in (o, h, l, c):
        a[bad] = np.nan
    m = np.arange(4, n - 61, 5)
    e = m + 1
    p0 = o[e]
    s_bp = X["s_bp"].to_numpy()[m].astype(np.float64)
    fc = feat.forced_close_minutes(n)[m]
    bcs = np.concatenate([[0], np.cumsum(bad)])
    base_ok = ~np.isnan(p0) & ~np.isnan(c[m]) & ~np.isnan(s_bp) & (fc >= 0)
    base_ok &= (bcs[m + 1] - bcs[np.maximum(m - 60, 0)]) == 0
    MX, MN = labels.sparse_tables(h, l)
    print(f"seyrek tablo {time.time()-t0:.0f}s", flush=True)
    out = pd.DataFrame({"m": m.astype(np.int32), "ts_dec": (df["ts"] + pd.Timedelta(minutes=1)).iloc[m].to_numpy(),
                        "p0": p0, "c_sig": c[m], "s_bp": s_bp.astype(np.float32)})
    s_frac = np.where(np.isnan(s_bp), 0.0019, s_bp / 1e4)
    p0f = np.where(np.isnan(p0), c[m], p0)
    p0f = np.where(np.isnan(p0f), 1.0, p0f)
    for H in (30, 60):
        ok = base_ok & (e + H <= fc) & ((bcs[e + H] - bcs[e]) == 0)
        out[f"valid_h{H}"] = ok
    for d, tp, H in CELLS:
        nm = cell_name(d, tp, H)
        r = labels.simulate(o, h, l, c, MX, MN, e, p0f, s_frac, tp, H, d)
        out[f"{nm}_gross"] = r["gross_bp"]
        out[f"{nm}_et"] = r["exit_type"]
        out[f"{nm}_k"] = r["k_exit"]
        out[f"{nm}_sb"] = r["samebar"]
        cs = np.where(np.isnan(c[m]), p0f, c[m])
        ro = labels.simulate(o, h, l, c, MX, MN, e, cs, s_frac, tp, H, d, gap_aware=False)
        out[f"{nm}_optgross"] = ro["gross_bp"]
        print(f"  {nm} {time.time()-t0:.0f}s", flush=True)
    Xd = X.iloc[m].reset_index(drop=True)
    full = pd.concat([out, Xd.drop(columns=["s_bp"])], axis=1)
    full.to_parquet(f"{HERE}/cache/dataset.parquet", index=False)
    import json
    json.dump(G, open(f"{HERE}/cache/feature_groups.json", "w"), indent=1)
    print(f"bitti {full.shape} {time.time()-t0:.0f}s; valid30 {out.valid_h30.sum():,} valid60 {out.valid_h60.sum():,}")


if __name__ == "__main__":
    main()
