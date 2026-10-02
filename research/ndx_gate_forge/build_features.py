import sys, time
import pandas as pd
from common import load_1m, DATA
from features import build
b = load_1m()
for tf in [int(x) for x in sys.argv[1:]] or [1]:
    t0 = time.time()
    f = build(b, tf)
    f.to_parquet(DATA / f"feat_tf{tf}.parquet")
    print(tf, f.shape, round(time.time()-t0,1), "s")
    print(f[["vr15","skew120","rv30_rel","v15_rel","rng15_rel","range_used","day_pos","pos4","h1_trend","prev_day_ret","gap"]].describe().T.round(3))
