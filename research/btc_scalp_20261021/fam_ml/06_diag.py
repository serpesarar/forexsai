"""POST-HOC teşhis (ön kayıtta yok; verdikti değiştirmez — yorum içindir):
 (a) seçim oynaklık/maliyet rejimi mi? seçilenlerin s_bp'si vs havuz; oynaklık-eşli plasebo (yıl×saat×s_bp ondalığı);
 (b) brüt R (maliyetsiz) vs plasebo brüt R;
 (c) yön becerisi: aynı seçilmiş zamanlarda ters yön hücresinin R'si (yön bilgisi yoksa ikisi benzer).
Çıktı results/diag_posthoc.json
"""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mlcore as mc  # noqa: E402

rng = np.random.default_rng(77)
NP = 500


def strat_placebo(key, pool, sel, y):
    pidx = np.where(pool)[0]
    pk = key[pidx]
    o = np.argsort(pk, kind="stable")
    pk, pidx = pk[o], pidx[o]
    ks, cnt = np.unique(key[sel], return_counts=True)
    tot, used = np.zeros(NP), 0
    for kk, cc in zip(ks, cnt):
        a, b = np.searchsorted(pk, kk, "left"), np.searchsorted(pk, kk, "right")
        if b == a:
            continue
        tot += y[pidx[a + rng.integers(0, b - a, (NP, cc))]].sum(1)
        used += cc
    return tot / max(used, 1)


def main():
    ds, feats, groups = mc.load_ds()
    spec = json.load(open(f"{HERE}/results/frozen_spec.json"))
    P = pd.read_parquet(f"{HERE}/cache/preds.parquet")
    tsn = ds["tsn"].to_numpy()
    yr = ds.ts_dec.dt.year.to_numpy()
    hr = ds.ts_dec.dt.hour.to_numpy()
    s = ds["s_bp"].to_numpy(np.float64)
    res = {}
    for cell in mc.CELLS:
        d, tp, H = mc.cell_parts(cell)
        opp = ("S" if d == 1 else "L") + cell[1:]
        k = spec["cells"][cell]["k"]
        valid = ds[f"valid_h{H}"].to_numpy()
        y = mc.net_r(ds, cell, "PEP")
        yg = ds[f"{cell}_gross"].to_numpy(np.float64) / s
        yo = mc.net_r(ds, opp, "PEP")
        yog = ds[f"{opp}_gross"].to_numpy(np.float64) / s
        res[cell] = {}
        for seg, col, hist, segm in (
                ("OOS", "m1", valid & (ds.ts_dec >= mc.GAP[0]).to_numpy(), mc.in_period(ds, mc.OOS)),
                ("BLIND", "m2", valid & mc.in_period(ds, mc.BLIND), mc.in_period(ds, mc.BLIND))):
            pr = np.nan_to_num(P[f"{cell}_{col}"].to_numpy(), nan=-9.0)
            thr = mc.rolling_thresholds(tsn, pr, hist, ks=[k])[0]
            ev = valid & segm
            pool = ev & np.isfinite(thr)
            sel = ev & (pr > thr)
            # s_bp ondalığı segment havuzu içinde
            qd = np.zeros(len(ds), int)
            qd[pool] = pd.qcut(s[pool], 10, labels=False, duplicates="drop")
            key3 = yr * 10000 + hr * 100 + qd
            key2 = yr * 100 + hr
            out = {"n": int(sel.sum()), "s_bp_sel_mean": float(s[sel].mean()), "s_bp_pool_mean": float(s[pool].mean()),
                   "floor_binding_sel": float((s[sel] <= 19.0001).mean()),
                   "floor_binding_pool": float((s[pool] <= 19.0001).mean()),
                   "net_r": float(y[sel].mean()), "gross_r": float(yg[sel].mean()),
                   "plc_hour_net": float(strat_placebo(key2, pool, sel, y).mean()),
                   "plc_hour_gross": float(strat_placebo(key2, pool, sel, yg).mean())}
            pv = strat_placebo(key3, pool, sel, y)
            pg = strat_placebo(key3, pool, sel, yg)
            out.update(plc_vol_net_mean=float(pv.mean()), plc_vol_net_pct=float((pv < out["net_r"]).mean()),
                       plc_vol_gross_mean=float(pg.mean()), plc_vol_gross_pct=float((pg < out["gross_r"]).mean()),
                       opp_dir_net_same_times=float(yo[sel].mean()), opp_dir_gross_same_times=float(yog[sel].mean()),
                       dir_skill_gross_r=float(yg[sel].mean() - yog[sel].mean()),
                       gross_bp_sel=float(ds[f"{cell}_gross"].to_numpy()[sel].mean()),
                       opp_gross_bp_sel=float(ds[f"{opp}_gross"].to_numpy()[sel].mean()))
            res[cell][seg] = out
            print(cell, seg, {kk: round(v, 4) for kk, v in out.items()}, flush=True)
    json.dump(res, open(f"{HERE}/results/diag_posthoc.json", "w"), indent=1)


if __name__ == "__main__":
    main()
