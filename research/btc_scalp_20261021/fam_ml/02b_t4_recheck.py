"""T4 yeniden sınama: döngü referansı, build ile aynı float64 s_bp kullanır (02_selftest float32 okuyordu).
8 hücre × 3.000 rastgele geçerli karar. Çıktı results/selftest_t4_float64.json
"""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import feat  # noqa: E402
import labels  # noqa: E402


def main():
    rng = np.random.default_rng(12)
    df = feat.load()
    X, _ = feat.build_features(df)
    s64 = X["s_bp"].to_numpy().astype(np.float64)
    ds = pd.read_parquet(f"{HERE}/cache/dataset.parquet")
    bad = feat.bad_mask(df)
    o, h, l, c = (df[f"spot_{x}"].to_numpy().copy() for x in ("open", "high", "low", "close"))
    for a in (o, h, l, c):
        a[bad] = np.nan
    out = {}
    for d in (1, -1):
        for tp in (1.0, 1.5):
            for H in (30, 60):
                nm = f"{'L' if d == 1 else 'S'}_tp{tp:g}_h{H}"
                idx = rng.choice(np.where(ds[f"valid_h{H}"])[0], 3000, replace=False)
                mm32 = mm64 = 0
                for i in idx:
                    r = ds.iloc[i]
                    m = int(r.m)
                    ref = (r[f"{nm}_gross"], r[f"{nm}_et"], r[f"{nm}_k"])
                    for s, tag in ((s64[m], 64), (r.s_bp, 32)):
                        g, et, k = labels.simulate_loop(o, h, l, c, m + 1, r.p0, s / 1e4, tp, H, d)
                        ok = abs(g - ref[0]) < 1e-3 and et == ref[1] and k == ref[2]
                        if not ok:
                            if tag == 64:
                                mm64 += 1
                            else:
                                mm32 += 1
                out[nm] = {"n": 3000, "mismatch_float64": mm64, "mismatch_float32_input": mm32}
                print(nm, out[nm], flush=True)
    out["PASS_float64"] = all(v["mismatch_float64"] == 0 for v in out.values() if isinstance(v, dict))
    json.dump(out, open(f"{HERE}/results/selftest_t4_float64.json", "w"), indent=1)
    print("T4 float64:", "GEÇTİ" if out["PASS_float64"] else "DÜŞTÜ")


if __name__ == "__main__":
    main()
