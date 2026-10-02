"""U evreni için BUY/SELL × {G80, GS, GR} sonuçları + ileri getiriler."""
import time
import numpy as np, pandas as pd
from common import load_1m, simulate, fwd_points, atr, DATA

b = load_1m()
b["atr70"] = atr(b.high.to_numpy(), b.low.to_numpy(), b.close.to_numpy(), 70)
seg_start = b.groupby("seg").t.transform("min")
ok = (b.t - seg_start > 2 * 86400) & b.utc_h.between(6, 21) & (b.wd <= 4) & b.period.ne("")
idx = np.flatnonzero(ok.to_numpy())
print("entries", len(idx))
D = np.clip(6 * b.atr70.to_numpy()[idx], 40, 250)
rows = {"i": idx}
t0 = time.time()
for s, sn in [(1, "B"), (-1, "S")]:
    side = np.full(len(idx), s)
    for g, tp, sl in [("G80", np.full(len(idx), 80.), np.full(len(idx), 110.)), ("GS", D, D), ("GR", 2 * D, D)]:
        R, dur, why = simulate(b, idx, side, tp, sl)
        rows[f"R_{g}_{sn}"] = R.astype("float32")
        rows[f"dur_{g}_{sn}"] = dur.astype("float32")
        rows[f"why_{g}_{sn}"] = why
    for H in (15, 60, 240):
        rows[f"f{H}_{sn}"] = fwd_points(b, idx, side, H).astype("float32")
print("sim s", round(time.time() - t0, 1))
L = pd.DataFrame(rows)
L["D"] = D.astype("float32")
L.to_parquet(DATA / "labels.parquet")
m = b.iloc[idx][["period"]].reset_index(drop=True)
print(pd.concat([m, L], axis=1).groupby("period")[["R_G80_B", "R_G80_S", "R_GS_B", "R_GS_S", "f60_B", "f60_S"]].mean().round(4))
for g in ["G80", "GS", "GR"]:
    print(g, pd.Series(L[f"why_{g}_B"]).value_counts(normalize=True).round(3).to_dict(), "dur med", float(np.nanmedian(L[f"dur_{g}_B"])))
