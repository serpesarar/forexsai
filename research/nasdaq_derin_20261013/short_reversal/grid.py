"""Ön-kayıtlı 576 hücre ızgarası (PROTOCOL §3). Kullanım: python grid.py NDX|DAX"""
from __future__ import annotations

import pickle
import sys

import numpy as np
import pandas as pd

from engine import (DISC_END, EXITS, FILTERS, SIGNALS, STOPS, add_excess, baseline, block_boot, dax_1h, ndx_1h,
                    run_rule)

OUT = "results"


def summarize(T: pd.DataFrame) -> dict:
    if len(T) < 5:
        return {"n": len(T)}
    v, e = T.R.to_numpy(), T.ex.to_numpy()
    days = T.nyd.astype(str).to_numpy()
    mon = T.nyd.dt.to_period("M").astype(str).to_numpy()
    h = len(T) // 2
    yr = T.groupby(T.nyd.dt.year).ex.sum()
    per_day = T.groupby("nyd").R.sum().sort_values(ascending=False)
    return {"n": len(T), "per_yr": len(T) / ((T.nyd.max() - T.nyd.min()).days / 365.25 + 1e-9),
            "wr": (v > 0).mean(), "R": v.mean(), "ex": e.mean(), "totR": v.sum(),
            "P_R": np.mean(block_boot(v, days) > 0), "P_ex": np.mean(block_boot(e, days) > 0),
            "P_ex_mon": np.mean(block_boot(e, mon) > 0),
            "ex_h1": e[:h].mean(), "ex_h2": e[h:].mean(), "R_h1": v[:h].mean(), "R_h2": v[h:].mean(),
            "yrs_pos": int((yr > 0).sum()), "yrs": len(yr), "ex2022": float(yr.get(2022, np.nan)),
            "R_no5": v.sum() - per_day.iloc[:5].sum(), "R_no10": v.sum() - per_day.iloc[:10].sum(),
            "hold": T.h.mean(), "stop_rate": (T.how == "stop").mean(), "swapR": T.swapR.mean()}


def main(which: str) -> None:
    mk = ndx_1h() if which == "NDX" else dax_1h()
    d = mk.day
    start = d.index[d.sig.notna() & d.ma200.notna()][0]
    end = DISC_END if which == "NDX" else pd.Timestamp("2026-10-02")
    base = baseline(mk, start, end)
    print(which, "taban (stop,h)→σR:", {f"{k[0]}/{k[1]}": round(v, 3) for k, v in base.items() if k[1] in (1, 3, 5, 10)})
    rows, trades = [], {}
    for sn, sf in SIGNALS.items():
        smask = sf(d).fillna(False).to_numpy()
        for fn, ff in FILTERS.items():
            mask = smask & ff(d).fillna(False).to_numpy()
            for ex in EXITS:
                for st in STOPS:
                    T = add_excess(run_rule(mk, mask, ex, st, start, end), base, st)
                    key = (sn, fn, ex, st)
                    trades[key] = T
                    rows.append({"sig": sn, "filt": fn, "exit": ex, "stop": st if st else 0, **summarize(T)})
    G = pd.DataFrame(rows)
    G.to_csv(f"{OUT}/grid_{which}.csv", index=False)
    with open(f"{OUT}/trades_{which}.pkl", "wb") as f:
        pickle.dump({"trades": trades, "base": base, "start": start, "end": end}, f)
    print(f"{which}: {len(G)} hücre, fazla>0 oranı %{100 * (G.ex > 0).mean():.1f}, σR>0 oranı %{100 * (G.R > 0).mean():.1f}")


if __name__ == "__main__":
    main(sys.argv[1])
