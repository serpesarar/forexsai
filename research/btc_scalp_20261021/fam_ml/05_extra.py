"""Ek fitler (dondurulmuş yapılandırma/k ile, yalnız DISC eğitimi → OOS):
  T5 kasıtlı sızıntı · Plasebo B (etiketi dairesel kaydırılmış modeller) · ablation · TreeSHAP.
Kullanım: python 05_extra.py <iş> [hücreler,virgüllü] [n_shuffle]
  iş ∈ {leak, shuffle, ablation, shap}
"""
import json
import os
import sys
import time

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import feat  # noqa: E402
import mlcore as mc  # noqa: E402


def oos_select(ds, pred, valid, k):
    tsn = ds["tsn"].to_numpy()
    pr = np.nan_to_num(pred, nan=-9.0)
    hist = valid & (ds.ts_dec >= mc.GAP[0]).to_numpy()
    thr = mc.rolling_thresholds(tsn, pr, hist, ks=[k])[0]
    evalm = valid & mc.in_period(ds, mc.OOS)
    return evalm & (pr > thr), evalm & np.isfinite(thr)


def run_model(ds, feats, cell, cfg, k, y_train=None, extra=None, seed=7):
    d, tp, H = mc.cell_parts(cell)
    valid = ds[f"valid_h{H}"].to_numpy()
    y = mc.net_r(ds, cell, "PEP")
    yt = y if y_train is None else y_train
    trm = mc.in_period(ds, mc.DISC) & valid
    X = ds[feats] if extra is None else pd.concat([ds[feats], extra], axis=1)
    mdl = mc.fit(X.loc[trm], yt[trm], cfg, seed=seed)
    after = (ds.ts_dec >= mc.GAP[0]).to_numpy()
    pred = np.full(len(ds), np.nan)
    pred[after] = mdl.predict(X.loc[after])
    sel, elig = oos_select(ds, pred, valid, k)
    ev = valid & mc.in_period(ds, mc.OOS)
    out = {"n": int(sel.sum()), "mean_r": float(y[sel].mean()), "base": float(y[elig].mean()),
           "auc_netpos": float(roc_auc_score(y[ev] > 0, pred[ev])),
           "spearman": float(pd.Series(pred[ev]).corr(pd.Series(y[ev]), method="spearman"))}
    return out, mdl


def main():
    job = sys.argv[1]
    spec = json.load(open(f"{HERE}/results/frozen_spec.json"))
    cells = sys.argv[2].split(",") if len(sys.argv) > 2 and sys.argv[2] != "all" else mc.CELLS
    nsh = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    ds, feats, groups = mc.load_ds()
    t0 = time.time()
    path = f"{HERE}/results/extra_{job}.json"
    res = json.load(open(path)) if os.path.exists(path) else {}
    for cell in cells:
        cfg = mc.CONFIGS[spec["cells"][cell]["config"]]
        k = spec["cells"][cell]["k"]
        d, tp, H = mc.cell_parts(cell)
        if job == "leak":
            df = feat.load(cols=["ts", "spot_open", "spot_close"])
            o, c = df.spot_open.to_numpy(), df.spot_close.to_numpy()
            e = ds["m"].to_numpy() + 1
            fwd = d * (c[np.minimum(e + 14, len(c) - 1)] / o[e] - 1) * 1e4
            sd = np.nanstd(fwd)
            rng = np.random.default_rng(5)
            r = {}
            for mult in (1.0, 3.0):
                leak = pd.DataFrame({"LEAK": fwd + rng.normal(0, mult * sd, len(fwd))})
                r[f"noise{mult:g}sd"], _ = run_model(ds, feats, cell, cfg, k, extra=leak)
                print(cell, mult, r[f"noise{mult:g}sd"], flush=True)
            res[cell] = r
        elif job == "shuffle":
            y = mc.net_r(ds, cell, "PEP")
            valid = ds[f"valid_h{H}"].to_numpy()
            trm = mc.in_period(ds, mc.DISC) & valid
            idx = np.where(trm)[0]
            rng = np.random.default_rng(99)
            r = []
            for s in range(nsh):
                shift = int(rng.integers(30 * 288, len(idx) - 30 * 288))
                ys = y.copy()
                ys[idx] = np.roll(y[idx], shift)
                o, _ = run_model(ds, feats, cell, cfg, k, y_train=ys, seed=100 + s)
                o["shift_rows"] = shift
                r.append(o)
                print(cell, "shuffle", s, round(o["mean_r"], 4), f"{time.time()-t0:.0f}s", flush=True)
            res[cell] = r
        elif job == "ablation":
            sets = {
                "A0_PRICE": groups["PRICE"],
                "A1_PRICE+CAL": groups["PRICE"] + groups["CAL"],
                "A2_+FLOW": groups["PRICE"] + groups["CAL"] + groups["FLOW"],
                "A3_+DERIV": groups["PRICE"] + groups["CAL"] + groups["FLOW"] + groups["DERIV"],
                "A3b_PRICE+CAL+DERIV": groups["PRICE"] + groups["CAL"] + groups["DERIV"],
            }
            r = {}
            for nm, fs in sets.items():
                r[nm], _ = run_model(ds, fs, cell, cfg, k)
                print(cell, nm, r[nm], f"{time.time()-t0:.0f}s", flush=True)
            res[cell] = r
        elif job == "shap":
            bst = lgb.Booster(model_file=f"{HERE}/cache/models/{cell}_m1.txt")
            valid = ds[f"valid_h{H}"].to_numpy()
            ev = np.where(valid & mc.in_period(ds, mc.OOS))[0]
            rng = np.random.default_rng(3)
            smp = rng.choice(ev, min(40000, len(ev)), replace=False)
            contrib = bst.predict(ds.loc[smp, feats], pred_contrib=True)[:, :-1]
            mabs = pd.Series(np.abs(contrib).mean(0), index=feats)
            grp = {g: float(mabs[[f for f in groups[g] if f in mabs.index]].sum()) for g in groups}
            # en yüksek tahmin %5'indeki örnekler: hangi faktörler birlikte iteliyor
            pred = contrib.sum(1)
            top = pred >= np.quantile(pred, 0.95)
            ctop = pd.Series(contrib[top].mean(0), index=feats)
            gtop = {g: float(ctop[[f for f in groups[g] if f in ctop.index]].sum()) for g in groups}
            corr = pd.DataFrame(contrib[:, [feats.index(f) for f in mabs.sort_values().index[-12:]]],
                                columns=list(mabs.sort_values().index[-12:])).corr()
            res[cell] = {"mean_abs_top25": mabs.sort_values(ascending=False).head(25).to_dict(),
                         "group_mean_abs": grp, "top5pct_mean_contrib_top15": ctop.sort_values(
                             ascending=False).head(15).to_dict(), "top5pct_group_contrib": gtop,
                         "shap_corr_top12": corr.round(2).to_dict()}
            print(cell, "shap grp", {g: round(v, 4) for g, v in grp.items()}, flush=True)
        json.dump(res, open(path, "w"), indent=1)
    print("bitti", f"{time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
