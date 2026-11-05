"""DTS-01 eki — NDX 4h RSI<30 fazla getirisi VIX≥18,4 / stres günü (CAPREV koşulları) dışında da sürüyor mu? Ön-kayıt: Ek-2."""
import numpy as np
import pandas as pd
from common import load, month_boot, SPREAD
import dts01_tarayici as T

m = pd.read_csv("../ndx_gate_forge/data/macro_daily_patched.csv", usecols=["date", "VIX_close", "NDXCASH_close"]).dropna()
m["date"] = pd.to_datetime(m.date).dt.date; m = m.sort_values("date")
m["r1"] = m.NDXCASH_close.pct_change(); m["r5"] = m.NDXCASH_close.pct_change(5)
m["vix_prev"] = m.VIX_close.shift(1); m["stres_prev"] = ((m.r1 <= -0.015) | (m.r5 <= -0.04)).shift(1)
mm = m.set_index("date")
d = load("NDX", "4h"); c, o = d.close.to_numpy(), d.open.to_numpy(); n = len(c)
sig = T.setups(c)["oversold"]
day = d.ts.dt.tz_convert("America/New_York").dt.date
vix = day.map(mm.vix_prev).to_numpy(float); stres = day.map(mm.stres_prev).astype(float).to_numpy()
months = d.ts.dt.strftime("%Y-%m").to_numpy(); first = (d.ts < d.ts.iloc[n // 2]).to_numpy()
for h in (1, 5, 10):
    fwd = np.full(n, np.nan); v = np.arange(n) + h < n
    e = np.r_[o[1:], np.nan] + SPREAD["NDX"]; fwd[v] = 1e4 * (c[np.arange(n)[v] + h] / e[v] - 1)
    base = np.nanmean(fwd)
    for nm, cond in (("VIX≥18,4", vix >= 18.4), ("VIX<18,4", vix < 18.4), ("stres", stres == 1), ("stres değil", stres == 0),
                     ("VIX<18,4 ∧ stres değil", (vix < 18.4) & (stres == 0))):
        k = np.flatnonzero(sig & cond & np.isfinite(fwd)); ex = fwd[k] - base
        if len(k) < 10:
            print(f"h={h:2d} {nm:24s} n={len(k)}"); continue
        print(f"h={h:2d} {nm:24s} n={len(k):4d} fazla {ex.mean():+7.1f} bp  P {month_boot(ex, months[k]):.3f}  y1 {ex[first[k]].mean() if first[k].any() else float('nan'):+6.1f}  y2 {ex[~first[k]].mean() if (~first[k]).any() else float('nan'):+6.1f}")
