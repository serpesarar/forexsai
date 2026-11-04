"""Dondurulmuş tahminlerden değerlendirme: kart, plasebo A, Holm, KÖR, yıl, maliyetler, kalibrasyon, AUC, profil.

Çıktılar: results/eval.json, results/cells_summary.csv, results/calibration.csv, results/k_sensitivity.csv,
results/selected_profile.csv, cache/trades_<cell>_<seg>.parquet
"""
import json
import os
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mlcore as mc  # noqa: E402

B = 2000
NPLAC = 500
rng = np.random.default_rng(2026)


def boot_day(r: np.ndarray, day: np.ndarray) -> tuple[float, float, float]:
    s = pd.DataFrame({"d": day, "r": r}).groupby("d")["r"].agg(["sum", "count"])
    S, C = s["sum"].to_numpy(), s["count"].to_numpy()
    idx = rng.integers(0, len(S), (B, len(S)))
    mb = S[idx].sum(1) / C[idx].sum(1)
    return float((mb > 0).mean()), float(np.quantile(mb, 0.025)), float(np.quantile(mb, 0.975))


def single_pos(ds_sel: pd.DataFrame, cell: str) -> np.ndarray:
    m = ds_sel["m"].to_numpy()
    k = ds_sel[f"{cell}_k"].to_numpy().astype(int)
    keep, free = [], -1
    for i in range(len(m)):
        e = m[i] + 1
        if e >= free:
            keep.append(i)
            free = e + k[i] + 1
    return np.array(keep, dtype=int)


def placebo(ds: pd.DataFrame, pool_mask: np.ndarray, sel_mask: np.ndarray, y: np.ndarray) -> np.ndarray:
    yr = ds["ts_dec"].dt.year.to_numpy()
    hr = ds["ts_dec"].dt.hour.to_numpy()
    key = yr * 100 + hr
    pool_idx = np.where(pool_mask)[0]
    pk = key[pool_idx]
    order = np.argsort(pk, kind="stable")
    pk_s, pidx_s = pk[order], pool_idx[order]
    sel_keys, cnt = np.unique(key[sel_mask], return_counts=True)
    tot = np.zeros(NPLAC)
    for kk, cc in zip(sel_keys, cnt):
        a, b = np.searchsorted(pk_s, kk, "left"), np.searchsorted(pk_s, kk, "right")
        if b == a:
            continue
        draws = pidx_s[a + rng.integers(0, b - a, (NPLAC, cc))]
        tot += y[draws].sum(1)
    return tot / sel_mask.sum()


def stats(ds: pd.DataFrame, sel: np.ndarray, cell: str) -> dict:
    d = ds.loc[sel]
    if len(d) == 0:
        return {"n": 0}
    y = mc.net_r(d, cell, "PEP")
    day = d["ts_dec"].dt.floor("D").to_numpy()
    s = d["s_bp"].to_numpy(np.float64)
    out = {"n": int(len(d)), "days": int(len(np.unique(day))), "mean_r": float(y.mean()),
           "mean_net_bp": float((y * s).mean()), "mean_gross_bp": float(d[f"{cell}_gross"].mean()),
           "mean_s_bp": float(s.mean()), "win_rate": float((y > 0).mean()),
           "tp_share": float((d[f"{cell}_et"] == 0).mean()), "sl_share": float((d[f"{cell}_et"] == 1).mean()),
           "time_share": float((d[f"{cell}_et"] == 2).mean()), "samebar_rate": float(d[f"{cell}_sb"].mean())}
    p, lo, hi = boot_day(y, day)
    out.update(p_ev_pos=p, ci95=[lo, hi])
    h = len(y) // 2
    out["half1"], out["half2"] = float(y[:h].mean()), float(y[h:].mean())
    for c in ("PEP_STRESS", "FIX15", "BIN_MAKER", "BIN_TAKER"):
        out[f"mean_r_{c}"] = float(mc.net_r(d, cell, c).mean())
    opt = mc.net_r(d, cell, optimistic=True)
    out["mean_r_optimistic"] = float(opt.mean())
    out["exec_gap"] = float(abs(opt.mean() - y.mean()))
    sp = single_pos(d, cell)
    out["single_pos_n"] = int(len(sp))
    out["single_pos_mean_r"] = float(y[sp].mean()) if len(sp) else np.nan
    out["trades_per_day_calendar"] = float(len(d) / max(1, (d.ts_dec.max() - d.ts_dec.min()).days + 1))
    yr = d["ts_dec"].dt.year.to_numpy()
    out["by_year"] = {int(Y): {"n": int((yr == Y).sum()), "mean_r": float(y[yr == Y].mean()),
                               "mean_net_bp": float((y * s)[yr == Y].mean())} for Y in np.unique(yr)}
    return out


def card(st: dict) -> dict:
    c = {
        "1_n150": st["n"] >= 150,
        "2_mean_pboot": st["mean_r"] > 0 and st["p_ev_pos"] >= 0.90,
        "3_halves": st["half1"] >= 0 and st["half2"] >= 0,
        "4_stress": st["mean_r_PEP_STRESS"] > 0,
        "5_exec_gap": st["exec_gap"] <= 0.5 * abs(st["mean_r"]),
        "6_single_pos": st["single_pos_mean_r"] > 0,
    }
    c["score"] = int(sum(c.values()))
    return c


def main():
    ds, feats, groups = mc.load_ds()
    spec = json.load(open(f"{HERE}/results/frozen_spec.json"))
    P = pd.read_parquet(f"{HERE}/cache/preds.parquet")
    assert np.array_equal(P["m"].to_numpy(), ds["m"].to_numpy())
    tsn = ds["tsn"].to_numpy()
    res, rows, calib, ksens, prof = {}, [], [], [], []
    for cell in mc.CELLS:
        d, tp, H = mc.cell_parts(cell)
        k = spec["cells"][cell]["k"]
        valid = ds[f"valid_h{H}"].to_numpy()
        y_all = mc.net_r(ds, cell, "PEP")
        res[cell] = {"frozen": spec["cells"][cell]}
        segs = {
            "OOS": (P[f"{cell}_m1"].to_numpy(), valid & (ds.ts_dec >= mc.GAP[0]).to_numpy(), mc.in_period(ds, mc.OOS)),
            "BLIND": (P[f"{cell}_m2"].to_numpy(), valid & mc.in_period(ds, mc.BLIND), mc.in_period(ds, mc.BLIND)),
            "DISC_innerCV": (P[f"{cell}_oof"].to_numpy(), valid & ~np.isnan(P[f"{cell}_oof"].to_numpy()),
                             ~np.isnan(P[f"{cell}_oof"].to_numpy())),
        }
        for seg, (pred, hist, segmask) in segs.items():
            pr = np.nan_to_num(pred, nan=-9.0)
            if seg == "DISC_innerCV":
                # fold sınırlarında ısınmayı tekrarlamamak için iç-CV seçimi 03'teki ile aynı (fold-başı)
                edges = pd.date_range(mc.VAL_START, mc.DISC[1], periods=5)
                thr = np.full((len(mc.KS), len(ds)), np.inf)
                for a, b in zip(edges[:-1], edges[1:]):
                    fm = hist & ((ds.ts_dec >= a) & (ds.ts_dec < b)).to_numpy()
                    t_ = mc.rolling_thresholds(tsn, pr, fm)
                    thr[:, fm] = t_[:, fm]
            else:
                thr = mc.rolling_thresholds(tsn, pr, hist)
            evalm = valid & segmask
            elig = evalm & np.isfinite(thr[0])
            for ki, kk in enumerate(mc.KS):
                sel = evalm & (pr > thr[ki])
                yy = y_all[sel]
                ksens.append(dict(cell=cell, seg=seg, k=kk, n=int(sel.sum()),
                                  mean_r=float(yy.mean()) if len(yy) else np.nan,
                                  base_mean_r=float(y_all[elig].mean())))
            ki = mc.KS.index(k)
            sel = evalm & (pr > thr[ki])
            st = stats(ds, sel, cell)
            st["base_unfiltered_mean_r"] = float(y_all[elig].mean())
            st["base_unfiltered_n"] = int(elig.sum())
            if st["n"]:
                st["card"] = card(st)
                pl = placebo(ds, elig, sel, y_all)
                st["placebo_mean"] = float(pl.mean())
                st["placebo_p95"] = float(np.quantile(pl, 0.95))
                st["placebo_pct"] = float((pl < st["mean_r"]).mean())
                # mutlak eşik (pred > 0), yalnız rapor
                sa = evalm & (pr > 0) & (pred == pred)
                st["abs_thr0"] = {"n": int(sa.sum()), "mean_r": float(y_all[sa].mean()) if sa.sum() else np.nan}
                ds.loc[sel, ["m", "ts_dec", "s_bp", f"{cell}_gross", f"{cell}_et", f"{cell}_k"]].assign(
                    pred=pr[sel], r=y_all[sel]).to_parquet(f"{HERE}/cache/trades_{cell}_{seg}.parquet")
            # kalibrasyon + AUC (değerlendirme satırlarının hepsi)
            ev = evalm & (pred == pred)
            if ev.sum() > 1000:
                q = pd.qcut(pred[ev], 10, labels=False, duplicates="drop")
                cdf = pd.DataFrame({"q": q, "p": pred[ev], "y": y_all[ev]}).groupby("q").agg(
                    pred_mean=("p", "mean"), real_mean=("y", "mean"), n=("y", "size")).reset_index()
                cdf["cell"], cdf["seg"] = cell, seg
                calib.append(cdf)
                st["auc_netpos"] = float(roc_auc_score(y_all[ev] > 0, pred[ev]))
                st["auc_tpfirst"] = float(roc_auc_score(ds[f"{cell}_et"].to_numpy()[ev] == 0, pred[ev]))
                st["spearman"] = float(pd.Series(pred[ev]).corr(pd.Series(y_all[ev]), method="spearman"))
                top = pd.Series(pred[ev]).rank(pct=True).to_numpy() > 0.9
                st["top_decile_mean_r"] = float(y_all[ev][top].mean())
            res[cell][seg] = st
            if seg in ("OOS", "BLIND") and st["n"]:
                Xs = ds.loc[sel, feats]
                Xa = ds.loc[elig, feats]
                z = (Xs.mean() - Xa.mean()) / Xa.std().replace(0, np.nan)
                for f_, v in z.items():
                    prof.append(dict(cell=cell, seg=seg, feature=f_, z_diff=float(v)))
            rows.append(dict(cell=cell, seg=seg, k=k, **{kx: st.get(kx) for kx in (
                "n", "days", "mean_r", "mean_net_bp", "mean_gross_bp", "p_ev_pos", "half1", "half2",
                "mean_r_PEP_STRESS", "mean_r_optimistic", "exec_gap", "single_pos_n", "single_pos_mean_r",
                "mean_r_FIX15", "mean_r_BIN_MAKER", "mean_r_BIN_TAKER", "win_rate", "samebar_rate",
                "base_unfiltered_mean_r", "placebo_pct", "auc_netpos", "auc_tpfirst", "spearman",
                "trades_per_day_calendar")}, card=st.get("card", {}).get("score")))
            print(cell, seg, "n", st["n"], "ortR", round(st.get("mean_r", np.nan), 4), "taban",
                  round(st["base_unfiltered_mean_r"], 4), "kart", st.get("card", {}).get("score"),
                  "plasebo%", st.get("placebo_pct"), flush=True)
    # Holm (OOS, tek yönlü p = 1 − P(EV>0))
    pv = {c: 1 - res[c]["OOS"].get("p_ev_pos", 0) for c in mc.CELLS}
    order = sorted(pv, key=pv.get)
    holm, run = {}, 0.0
    for i, c in enumerate(order):
        run = max(run, min(1.0, (len(order) - i) * pv[c]))
        holm[c] = run
    for c in mc.CELLS:
        o, bl = res[c]["OOS"], res[c]["BLIND"]
        ok_card = o.get("card", {}).get("score") == 6
        extra = {"placebo95": o.get("placebo_pct", 0) >= 0.95, "holm": holm[c] < 0.05,
                 "blind_sign": bl.get("mean_r", -1) > 0}
        res[c]["holm_p"] = holm[c]
        res[c]["extra"] = extra
        res[c]["verdict_pre_placeboB"] = "RED" if not ok_card else ("ADAY(B bekliyor)" if all(extra.values())
                                                                     else "SHADOW")
    json.dump(res, open(f"{HERE}/results/eval.json", "w"), indent=1, default=float)
    pd.DataFrame(rows).to_csv(f"{HERE}/results/cells_summary.csv", index=False)
    pd.concat(calib).to_csv(f"{HERE}/results/calibration.csv", index=False)
    pd.DataFrame(ksens).to_csv(f"{HERE}/results/k_sensitivity.csv", index=False)
    pd.DataFrame(prof).to_csv(f"{HERE}/results/selected_profile.csv", index=False)
    print({c: (res[c]["verdict_pre_placeboB"], round(res[c]["holm_p"], 3)) for c in mc.CELLS})


if __name__ == "__main__":
    main()
