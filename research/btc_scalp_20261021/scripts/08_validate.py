"""btc_scalp_1m doğrulamaları: (1) metrics sızıntı testi, (2) tasfiye vekili ↔ COIN-M tasfiye
(2023-06-25 → 2024-10-14) + plasebo, (3) funding tahmin geri-testi, (4) bazı tutarlılıklar.
Kullanım: python -I 08_validate.py <scalp_data_dir>
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd

RNG = np.random.default_rng(20261021)


def main() -> None:
    d = Path(sys.argv[1])
    rep: dict = {}
    g = pd.read_parquet(d / "btc_scalp_1m.parquet")
    # (1) metrics nedensellik
    rep["metrics_eff_after_row_ts"] = int((g["metrics_eff_ts"] > g["ts"]).sum())
    k = g.set_index("ts")
    buy, vol = k["perp_taker_buy_base"], k["perp_volume"]
    sell = vol - buy
    past = np.log(buy.rolling(5).sum() / sell.rolling(5).sum()).replace([np.inf, -np.inf], np.nan)  # [ts-4, ts]
    fut = past.shift(-5)                                                  # [ts+1, ts+5]
    x = np.log(k["taker_ls_vol_ratio_5m"].where(k["taker_ls_vol_ratio_5m"] > 0))
    out = {}
    for era, (a, b) in {"pre_2024-03-04": ("2021-06-01", "2024-03-03"), "post_2024-03-04": ("2024-03-05", "2026-10-20")}.items():
        xx, pp, ff = x.loc[a:b], past.loc[a:b], fut.loc[a:b]
        out[era] = {"corr_with_past_5m": round(float(xx.corr(pp)), 3), "corr_with_next_5m": round(float(xx.corr(ff)), 3)}
    rep["metrics_leak_test_taker_ratio"] = out
    # (2) tasfiye vekili ↔ CM tasfiye
    m = pd.read_parquet(d / "metrics_5m_effective.parquet")
    cm = pd.read_parquet(d / "cm_liq_5m.parquet")  # ts = 5dk kova başı
    a, b = pd.Timestamp("2023-06-26", tz="UTC"), pd.Timestamp("2024-10-13", tz="UTC")
    mm = m[(m["eff_ts"] >= a) & (m["eff_ts"] < b)].copy()
    cmi = cm.set_index("ts")
    mm["cm_long"] = cmi["cm_long_liq_usd"].reindex(mm["eff_ts"] - pd.Timedelta(minutes=5)).fillna(0).to_numpy()
    mm["cm_short"] = cmi["cm_short_liq_usd"].reindex(mm["eff_ts"] - pd.Timedelta(minutes=5)).fillna(0).to_numpy()
    res = {}
    for side, flag, col in [("long", "liq_proxy_long_5m", "cm_long"), ("short", "liq_proxy_short_5m", "cm_short")]:
        f = mm[flag] == 1
        top = mm[col] >= mm[col].quantile(0.995)
        pl = []
        for _ in range(200):
            idx = RNG.choice(len(mm), int(f.sum()), replace=False)
            pl.append(mm[col].to_numpy()[idx].mean())
        res[side] = {"n_windows": len(mm), "n_flag": int(f.sum()),
                     "mean_cm_liq_usd_flag": round(float(mm.loc[f, col].mean()), 0),
                     "mean_cm_liq_usd_unflag": round(float(mm.loc[~f, col].mean()), 0),
                     "placebo_random_mean_p50_p99": [round(float(np.percentile(pl, q)), 0) for q in (50, 99)],
                     "share_flag_with_any_cm_liq": round(float((mm.loc[f, col] > 0).mean()), 3),
                     "share_unflag_with_any_cm_liq": round(float((mm.loc[~f, col] > 0).mean()), 3),
                     "recall_top0.5pct_cm_liq_windows": round(float(f[top].mean()), 3),
                     "precision_flag_in_top0.5pct": round(float(top[f].mean()), 3),
                     "spearman_score_vs_cm": round(float(mm["liq_proxy_score_5m"].rank().corr(mm[col].rank() * (1 if side == 'short' else -1))), 3)}
    rep["liq_proxy_5m_vs_cm"] = res
    c1 = pd.read_parquet(d / "cm_liq_1m.parquet").set_index("ts")
    gg = g[(g["ts"] >= a) & (g["ts"] < b)].set_index("ts")
    res1 = {}
    for side, flag, col in [("long", "liq_flow_long_1m", "cm_long_liq_usd"), ("short", "liq_flow_short_1m", "cm_short_liq_usd")]:
        y = c1[col].reindex(gg.index).fillna(0)
        f = gg[flag] == 1
        top = y >= y.quantile(0.999)
        res1[side] = {"n_flag": int(f.sum()), "mean_cm_flag": round(float(y[f].mean()), 0), "mean_cm_unflag": round(float(y[~f].mean()), 0),
                      "recall_top0.1pct": round(float(f[top].mean()), 3), "precision_in_top0.1pct": round(float(top[f].mean()), 3)}
    rep["liq_flow_1m_vs_cm"] = res1
    # (3) funding tahmini geri-testi (mevcut uzlaşmalar)
    f = pd.read_parquet(d / "funding.parquet")
    pm = ((k["prem_open"] + k["prem_close"]) / 2)
    w = np.arange(1, 481, dtype=float)
    rows = []
    for H, r in zip(f["funding_time_nominal"], f["rate"]):
        seg = pm.loc[H - pd.Timedelta(minutes=480): H - pd.Timedelta(minutes=1)].to_numpy()
        if len(seg) != 480:
            continue
        ok = ~np.isnan(seg)
        P = (seg[ok] * w[ok]).sum() / w[ok].sum()
        rows.append((r, P + np.clip(0.0001 - P, -0.0005, 0.0005)))
    e = np.array([x[1] - x[0] for x in rows])
    rep["funding_estimate_backtest"] = {"n": len(rows), "mae_bp": round(float(np.abs(e).mean() * 1e4), 4),
                                        "p99_abs_bp": round(float(np.quantile(np.abs(e), .99) * 1e4), 4),
                                        "max_abs_bp": round(float(np.abs(e).max() * 1e4), 4),
                                        "corr": round(float(np.corrcoef([x[0] for x in rows], [x[1] for x in rows])[0, 1]), 5)}
    # funding_pred_running son dakikada (bar 7:59 vb.) gerçekleşenle
    last_min = g[(g["ts"] + pd.Timedelta(minutes=1)).dt.hour.isin([0, 8, 16]) & ((g["ts"] + pd.Timedelta(minutes=1)).dt.minute == 0)]
    j = last_min.assign(H=last_min["ts"] + pd.Timedelta(minutes=1)).merge(f, left_on="H", right_on="funding_time_nominal")
    rep["funding_pred_running_at_window_end_mae_bp"] = round(float((j["funding_pred_running"] - j["rate"]).abs().mean() * 1e4), 4)
    # (4) tutarlılık
    rep["basis_perp_spot_bp"] = g["basis_perp_spot_bp"].describe(percentiles=[.01, .5, .99]).round(2).to_dict()
    rep["prem_close_bp"] = g["prem_close_bp"].describe(percentiles=[.01, .5, .99]).round(2).to_dict()
    rep["perp_vs_spot_volume_ratio_median_by_year"] = (g["perp_volume"] / g["spot_volume"]).groupby(g["ts"].dt.year).median().round(2).to_dict()
    (d / "validation_report.json").write_text(json.dumps(rep, indent=1, default=str))
    print(json.dumps(rep, indent=1, default=str))


if __name__ == "__main__":
    main()
