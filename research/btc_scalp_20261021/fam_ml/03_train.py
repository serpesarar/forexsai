"""İç CV (yalnız DISC) → (yapılandırma, k) dondur → DISC modeli → OOS tahmini; DISC+OOS modeli → BLIND tahmini.

Çıktılar: results/frozen_spec.json, results/innercv.csv, cache/preds.parquet, cache/models/*.txt
"""
import json
import os
import sys
import time

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mlcore as mc  # noqa: E402


def folds(ds):
    edges = pd.date_range(mc.VAL_START, mc.DISC[1], periods=5)
    out = []
    for a, b in zip(edges[:-1], edges[1:]):
        tr = ((ds.ts_dec >= mc.DISC[0]) & (ds.ts_dec < a - pd.Timedelta(days=1))).to_numpy()
        va = ((ds.ts_dec >= a) & (ds.ts_dec < b)).to_numpy()
        out.append((tr, va))
    return out


def main():
    t0 = time.time()
    ds, feats, groups = mc.load_ds()
    tsn = ds["tsn"].to_numpy()
    os.makedirs(f"{HERE}/cache/models", exist_ok=True)
    F = folds(ds)
    rows = []
    spec = {"features": feats, "groups": groups, "configs": mc.CONFIGS, "ks": mc.KS, "cells": {}}
    preds = pd.DataFrame({"m": ds["m"], "ts_dec": ds["ts_dec"]})
    for cell in mc.CELLS:
        d, tp, H = mc.cell_parts(cell)
        valid = ds[f"valid_h{H}"].to_numpy()
        y = mc.net_r(ds, cell, "PEP")
        best = None
        oof_store = {}
        for cname, cfg in mc.CONFIGS.items():
            oof = np.full(len(ds), np.nan)
            for tr, va in F:
                trm = tr & valid
                mdl = mc.fit(ds.loc[trm, feats], y[trm], cfg)
                vam = va & valid
                oof[vam] = mdl.predict(ds.loc[vam, feats])
            oof_store[cname] = oof
            for k_i, k in enumerate(mc.KS):
                sel = np.zeros(len(ds), bool)
                for tr, va in F:
                    vam = va & valid
                    thr = mc.rolling_thresholds(tsn, np.nan_to_num(oof, nan=-9), vam, ks=[k])[0]
                    sel |= vam & (oof > thr)
                n = int(sel.sum())
                mr = float(np.mean(y[sel])) if n else np.nan
                vv = valid & ~np.isnan(oof)
                sp = float(pd.Series(oof[vv]).corr(pd.Series(y[vv]), method="spearman"))
                rows.append(dict(cell=cell, config=cname, k=k, n=n, mean_r=mr, spearman=sp,
                                 base_mean_r=float(np.mean(y[vv]))))
                if n >= 300 and (best is None or mr > best[2]):
                    best = (cname, k, mr, n)
            print(f"{cell} {cname} {time.time()-t0:.0f}s", flush=True)
        cname, k, mr, n = best
        preds[f"{cell}_oof"] = oof_store[cname]
        cfg = mc.CONFIGS[cname]
        # model 1: DISC
        trm = mc.in_period(ds, mc.DISC) & valid
        m1 = mc.fit(ds.loc[trm, feats], y[trm], cfg)
        m1.booster_.save_model(f"{HERE}/cache/models/{cell}_m1.txt")
        p1 = np.full(len(ds), np.nan)
        after = (ds.ts_dec >= mc.GAP[0]).to_numpy()
        p1[after] = m1.predict(ds.loc[after, feats])
        preds[f"{cell}_m1"] = p1
        # model 2: DISC+OOS (son 1 gün arınma)
        trm2 = (mc.in_period(ds, mc.DISC) | (mc.in_period(ds, mc.OOS) &
                (ds.ts_dec < mc.OOS[1] - pd.Timedelta(days=1)).to_numpy())) & valid
        m2 = mc.fit(ds.loc[trm2, feats], y[trm2], cfg)
        m2.booster_.save_model(f"{HERE}/cache/models/{cell}_m2.txt")
        p2 = np.full(len(ds), np.nan)
        bl = mc.in_period(ds, mc.BLIND)
        p2[bl] = m2.predict(ds.loc[bl, feats])
        preds[f"{cell}_m2"] = p2
        imp = pd.Series(m1.booster_.feature_importance("gain"), index=feats).sort_values(ascending=False)
        spec["cells"][cell] = {"config": cname, "k": k, "innercv_mean_r": mr, "innercv_n": n,
                               "gain_top20_m1": imp.head(20).round(1).to_dict()}
        print(f"== {cell}: dondu {cname} k={k} iç-CV ortR {mr:+.4f} n={n} ({time.time()-t0:.0f}s)", flush=True)
    pd.DataFrame(rows).to_csv(f"{HERE}/results/innercv.csv", index=False)
    best_cell = max(spec["cells"], key=lambda c: spec["cells"][c]["innercv_mean_r"])
    spec["priority_cell"] = best_cell
    json.dump(spec, open(f"{HERE}/results/frozen_spec.json", "w"), indent=1, default=str)
    preds.to_parquet(f"{HERE}/cache/preds.parquet", index=False)
    print(f"öncelikli hücre {best_cell}; bitti {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
