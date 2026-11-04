"""Sızıntı öz-sınamaları T1–T4 (ön kayıt §6). T5 (kasıtlı sızıntı) 03_train.py içinde."""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import feat  # noqa: E402
import labels  # noqa: E402


def same(a: pd.DataFrame, b: pd.DataFrame) -> tuple[int, str]:
    bad, worst = 0, ""
    for col in a.columns:
        x, y = a[col].to_numpy(np.float64), b[col].to_numpy(np.float64)
        eq = (x == y) | (np.isnan(x) & np.isnan(y))
        k = int((~eq).sum())
        if k:
            bad += k
            worst += f"{col}:{k} "
    return bad, worst


def main():
    rng = np.random.default_rng(11)
    res = {}
    df = feat.load(cols=feat.ALL_COLS + feat.CHECK_COLS)
    n = len(df)
    Xf, _ = feat.build_features(df[feat.ALL_COLS])
    # T1 önek: veri cut'tan sonra kesilir
    cuts = sorted(rng.integers(200_000, n - 1000, 5).tolist())
    t1 = []
    for cut in cuts:
        Xp, _ = feat.build_features(df[feat.ALL_COLS].iloc[:cut + 1].copy())
        k, w = same(Xp, Xf.iloc[:cut + 1])
        t1.append({"cut": int(cut), "mismatch": k, "cols": w})
        print("T1", cut, k, w, flush=True)
    res["T1_prefix"] = t1
    # T2 giriş barı ve sonrası bozulur (kesmek yerine değiştirilir)
    t2 = []
    for cut in cuts[:3]:
        d2 = df[feat.ALL_COLS].copy()
        sl = slice(cut + 1, None)
        num = [c for c in d2.columns if c != "ts" and pd.api.types.is_numeric_dtype(d2[c])]
        for col in num:
            v = d2[col].to_numpy().copy()
            if v.dtype.kind == "f":
                v[sl] = v[sl] * 1.37 + rng.normal(0, 1, len(v[sl]))
            else:
                v[sl] = rng.integers(0, 2, len(v[sl]))
            d2[col] = v
        Xp, _ = feat.build_features(d2)
        k, w = same(Xp.iloc[:cut + 1], Xf.iloc[:cut + 1])
        k_after, _ = same(Xp.iloc[cut + 1:cut + 2000], Xf.iloc[cut + 1:cut + 2000])
        t2.append({"cut": int(cut), "mismatch_upto_cut": k, "cols": w, "changed_after_cut_cells": k_after})
        print("T2", cut, k, w, "after:", k_after, flush=True)
    res["T2_entrybar_perturb"] = t2
    # T3 kaynak nedenselliği
    ts = df["ts"]
    me = df["metrics_eff_ts"]
    ft = df["funding_last_time"]
    res["T3"] = {
        "metrics_eff_gt_ts": int((me > ts).sum()),
        "funding_time_gt_close": int((ft > ts + pd.Timedelta(minutes=1)).sum()),
        "bd_snap_age_neg": int((df["bd_snap_age_s"] < 0).sum()),
        "bd_snap_age_gt_60_nonnull_share": float((df["bd_snap_age_s"] > 60).mean()),
    }
    print("T3", res["T3"], flush=True)
    # T4 etiket motoru vs döngü
    ds = pd.read_parquet(f"{HERE}/cache/dataset.parquet")
    bad = feat.bad_mask(df)
    o, h, l, c = (df[f"spot_{x}"].to_numpy().copy() for x in ("open", "high", "low", "close"))
    for a in (o, h, l, c):
        a[bad] = np.nan
    t4 = {}
    for d in (1, -1):
        for tp in (1.0, 1.5):
            for H in (30, 60):
                nm = f"{'L' if d == 1 else 'S'}_tp{tp:g}_h{H}"
                idx = rng.choice(np.where(ds[f"valid_h{H}"])[0], 3000, replace=False)
                mm = 0
                for i in idx:
                    r = ds.iloc[i]
                    g, et, k = labels.simulate_loop(o, h, l, c, int(r.m) + 1, r.p0, r.s_bp / 1e4, tp, H, d)
                    if not (abs(g - r[f"{nm}_gross"]) < 1e-3 and et == r[f"{nm}_et"] and k == r[f"{nm}_k"]):
                        mm += 1
                t4[nm] = mm
                print("T4", nm, mm, flush=True)
    res["T4_label_loop_mismatch"] = t4
    json.dump(res, open(f"{HERE}/results/selftest.json", "w"), indent=1)
    ok = all(x["mismatch"] == 0 for x in t1) and all(x["mismatch_upto_cut"] == 0 for x in t2) and \
        res["T3"]["metrics_eff_gt_ts"] == 0 and res["T3"]["funding_time_gt_close"] == 0 and \
        res["T3"]["bd_snap_age_neg"] == 0 and all(v == 0 for v in t4.values())
    print("TÜM ÖZ-SINAMALAR:", "GEÇTİ" if ok else "DÜŞTÜ")


if __name__ == "__main__":
    main()
