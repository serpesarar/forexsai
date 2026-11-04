"""Ek duyarlılıklar (sonuç SONRASI, verdikti değiştirmez): swap −%22,5 varyantı, QB stopsuz vs bot biçimi,
post-hoc kollar için %50 küçültme senaryosu, 2026 yılı, kol bazında WR/başabaş."""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd
import lib_st as L

TR = pd.read_pickle(L.RES / "trades.pkl")
SETS = pd.read_pickle(L.RES / "portfolio_trades.pkl")
NAMES = ["S1_CORE", "S2_MAX10", "S3_QB", "S4_X04", "S5_CAPREV", "S6_OF02", "S7_DV04c"]
out = {}
# swap −%22,5
rows = []
for k in NAMES:
    d = SETS[k]
    p = d[d.split.isin(["OOS", "BLIND"])]
    extra = np.where(p.dir == 1, -(0.225 - 0.14) / 365, 0.0) * p.nights * p.sig / p.R_den
    rows.append({"kol": k, "POST_ortR": round(p.R.mean(), 4), "swap22.5_ortR": round((p.R + extra).mean(), 4),
                 "ort_gece": round(p.nights.mean(), 2), "WR": round((p.R > 0).mean(), 3),
                 "TP%": round((p.typ == 1).mean() * 100, 1), "SL%": round((p.typ == 0).mean() * 100, 1),
                 "zaman%": round((p.typ == 2).mean() * 100, 1)})
sw = pd.DataFrame(rows)
print(sw.to_string())
sw.to_csv(L.RES / "swap_sensitivity.csv", index=False)
q = TR["_QB_frozen"]
for s in ("DISC", "OOS", "BLIND"):
    m = q.split == s
    print(f"QB stopsuz {s}: n {m.sum()} ortR(ATR1h) {q.R[m].mean():+.4f} bp {q.bp[m].mean():+.2f}")
m = q.split.isin(["OOS", "BLIND"])
print(f"QB stopsuz POST: n {m.sum()} ortR(ATR1h) {q.R[m].mean():+.4f} bp {q.bp[m].mean():+.2f}")
qb = SETS["S3_QB"]; mm = qb.split.isin(["OOS", "BLIND"])
print(f"QB bot biçimi POST: ortR(2ATR) {qb.R[mm].mean():+.4f} = {2*qb.R[mm].mean():+.4f} ATR1h; bp {qb.bp[mm].mean():+.2f}; SL vuruş %{100*(qb.typ[mm]==0).mean():.1f}")
# post-hoc küçültme
for p, names in {"P-ALL-DV": NAMES[:6], "P-ALL": NAMES}.items():
    d = pd.concat([SETS[k] for k in names]); d = d[d.split.isin(["OOS", "BLIND"])]
    adj = d.R.copy()
    for k in ("S5_CAPREV", "S6_OF02", "S7_DV04c"):
        mk = d.sleeve == k
        if mk.any():
            adj[mk] = d.R[mk] - 0.5 * d.R[mk].mean()
    print(f"{p}: POST ortR {d.R.mean():+.4f} → post-hoc kollar %50 küçültülünce {adj.mean():+.4f}; post-hoc'suz (P-PRE) {pd.concat([SETS[k] for k in NAMES[:4]]).query('split in [\"OOS\",\"BLIND\"]').R.mean():+.4f}")
# 2026 ve son 12 ay
cut = L.em("2025-10-20")
for p, names in {"P-PRE": NAMES[:4], "P-ALL-DV": NAMES[:6]}.items():
    d = pd.concat([SETS[k] for k in names])
    m = d.ent_t >= cut
    print(f"{p} son 12 ay (2025-10-20→): n {m.sum()} ortR {d.R[m].mean():+.4f} bp {d.bp[m].mean():+.2f} P(EV>0) {L.day_boot(d.R[m].to_numpy(), (d.ent_t[m]//1440).to_numpy())[0]:.2f}")
    for k in names:
        dk = SETS[k]; mk = dk.ent_t >= cut
        print(f"   {k}: n {mk.sum()} ortR {dk.R[mk].mean():+.3f}")
