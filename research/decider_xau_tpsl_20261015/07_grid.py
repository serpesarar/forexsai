"""Q3: karşı-olgu geometri ızgarası — decider girişleri üzerinde (yön ayrı). Çıktı: results/grid_*.csv,
results/grid_summary.txt, data/grid_cache_<grup>.npz (yarılar/plasebo için yeniden kullanılır)."""
import numpy as np
import pandas as pd
import core, grid_lib as G

HERE = core.HERE; OUT = HERE / "results"
A = pd.read_pickle(HERE / "data" / "analysis_set.pkl")
A = A[~A.data_gap_240m.astype(bool)].copy()
P = core.Paths(core.load_1m())
A["path_i0"] = [P.first_idx_at_or_after(t) for t in A.path_start_utc]
A["day"] = A.decision_time_utc.dt.strftime("%Y-%m-%d")
A = A.sort_values("decision_time_utc").reset_index(drop=True)
A.to_pickle(HERE / "data" / "grid_set.pkl")
GROUPS = {"BUY": A.direction == "BUY", "SELL": A.direction == "SELL",
          "BUY_exec": A.executed, "BUY_rr067_epoch": (A.direction == "BUY") & (A.j_rr.round(2) == 0.67)}
L = []
cells = G.cells_fixed(A, P)
np.savez_compressed(HERE / "data" / "grid_cache_all.npz", **{k: v for k, v in cells.items()})
risks = G.risk_arrays(A)


def flat_table(stats: dict, fam: str, axes: list[tuple[str, np.ndarray]]) -> pd.DataFrame:
    idx = pd.MultiIndex.from_product([a for _, a in axes], names=[n for n, _ in axes])
    return pd.DataFrame({k: np.asarray(v).reshape(-1) for k, v in stats.items()}, index=idx).reset_index().assign(family=fam)


AXES = {"atr": [("tp_atr", G.TP_ATR), ("sl_atr", G.SL_ATR)], "usd": [("tp_usd", G.TP_USD), ("sl_usd", G.SL_USD)],
        "scale": [("tp_x_orig", G.TP_SCALE), ("sl_x_orig", G.SL_SCALE)], "time_only": [("H_min", np.array(G.TIME_H))],
        "time_sl": [("H_min", np.array(G.TIME_H)), ("sl_atr", G.TIME_SL_ATR)], "orig_cap": [("H_min", np.array(G.TIME_H))]}
for gname, m in GROUPS.items():
    idx = np.where(m.values)[0]
    days = A.day.values[idx]
    tabs = []
    for fam, ax in AXES.items():
        st = G.summarize(cells[fam][idx], risks[fam][idx], days)
        tabs.append(flat_table(st, fam, ax))
    T = pd.concat(tabs, ignore_index=True)
    T.to_csv(OUT / f"grid_{gname}.csv", index=False)
    L.append(f"\n=== {gname}  n={len(idx)}  gün={len(set(days))}  dönem {A.decision_time_utc.iloc[idx].min():%m-%d}→{A.decision_time_utc.iloc[idx].max():%m-%d}")
    orig = T[(T.family == "scale") & (T.tp_x_orig == 1.0) & (T.sl_x_orig == 1.0)]
    L.append("ORİJİNAL (tp×1, sl×1): " + orig[["WR", "EV_R", "R_lo", "R_hi", "P_R_gt0", "EV_usd"]].round(3).to_string(index=False, header=True))
    for fam in AXES:
        t = T[T.family == fam].sort_values("EV_R", ascending=False)
        cols = [c for c in ("tp_atr", "sl_atr", "tp_usd", "sl_usd", "tp_x_orig", "sl_x_orig", "H_min") if c in t and t[c].notna().any()]
        L.append(f"-- {fam}: hücre {len(t)} | EV_R>0 olan {int((t.EV_R>0).sum())} | P>0.95 olan {int((t.P_R_gt0>0.95).sum())} | en iyi 5:")
        L.append(t.head(5)[cols + ["WR", "EV_R", "R_lo", "R_hi", "P_R_gt0", "EV_usd", "usd_lo", "usd_hi"]].round(3).to_string(index=False))
    # ATR ızgarası EV_R ısı haritası
    H = T[T.family == "atr"].pivot(index="tp_atr", columns="sl_atr", values="EV_R").round(3)
    L.append("ATR ızgarası EV_R (satır TP×ATR5, sütun SL×ATR5):\n" + H.to_string())
    H = T[T.family == "atr"].pivot(index="tp_atr", columns="sl_atr", values="EV_usd").round(2)
    L.append("ATR ızgarası EV $ / 0.01 lot:\n" + H.to_string())
(OUT / "grid_summary.txt").write_text("\n".join(L))
print("\n".join(L))
