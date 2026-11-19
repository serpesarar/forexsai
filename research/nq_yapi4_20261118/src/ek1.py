import json, numpy as np, pandas as pd
import yapi4 as Y
M, V = Y.M, Y.V
m = M.mega()[M.STOCKS].dropna(how="all")
out = {}
for t in ("QQQ", "SPY", "NDX"):
    x = V.ndx_frame() if t == "NDX" else M.N.frame(t)
    mm = m.reindex(x.index)
    g = (mm > mm.rolling(10).mean()).sum(axis=1) / mm.notna().sum(axis=1)
    wash = (g <= 1 / 12 + 1e-9).values & (mm.notna().sum(axis=1) >= 10).values
    r2 = V.rsi2(x.c).values
    if t == "NDX":
        ep = M.episodes(x, wash, 5, 1)
        out["NDX_1995_1999_BT2"] = M.placebo(x, ep[(ep.d >= "1995-06-01") & (ep.d <= "1999-02-28")], 5, 1)
        ep2 = M.episodes(x, wash & (r2 >= 10), 5, 1)
        out["NDX_1995_1999_BT2_rsi_ust"] = M.placebo(x, ep2[(ep2.d >= "1995-06-01") & (ep2.d <= "1999-02-28")], 5, 1)
        continue
    ep = M.episodes(x, wash, 5, 1)
    ep["rsi_alt"] = pd.Series(r2 < 10, index=x.index).reindex(ep.d).values
    out[f"{t}_a_BT2_rsi_alt_payi"] = round(float(ep.rsi_alt.mean()), 3)
    for nm, sub in (("rsi_alt", ep.rsi_alt.values), ("rsi_ust", ~ep.rsi_alt.values)):
        e = ep[sub]
        out[f"{t}_a_{nm}"] = {"KESIF": M.placebo(x, e[e.d <= M.KES], 5, 1), "TEST": M.placebo(x, e[e.d >= M.TEST0], 5, 1)}
    out[f"{t}_b_BT2_rsi_ust_epizot"] = Y.by(x, wash & (r2 >= 10), 5, 1, str(M.KES.date()), str(M.TEST0.date()))
    tr = V.rule_trades(t)["C3b"]; tr = tr[tr.d >= "2001-01-01"].reset_index(drop=True)
    wm = pd.Series(wash, index=x.index).reindex(tr.d).fillna(False).values.astype(bool)
    for e, em in (("KESIF", (tr.d <= M.KES).values), ("TEST", (tr.d >= M.TEST0).values)):
        out[f"{t}_c_C3b_x_BT2_{e}"] = V.diff_stat(tr, wm & em, em)
for k, v in out.items(): print(k, v)
Y.RES.joinpath("ek1.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))
