import json, sys
from datetime import datetime
from pathlib import Path
import numpy as np, pandas as pd
import veri as VR
R, G, NY, FIN = VR.R, VR.G, VR.NY, VR.FIN
HERE = Path(__file__).resolve().parents[1]
HS = (5, 7, 10, 15, 20)
def trades(b, st, name):
    dp = VR.daily_frame(b, st); p = dp.o960
    k1 = ((p / dp.tw - 1) * 1e4 <= -50) & (p < dp.o900)
    t, o, sp = b.t.values, b.o.values, b.sp.values
    days = list(dp.index); tol = 300 if st == 60 else st; rows = []
    for i, d in enumerate(days[:-1]):
        if not k1.iloc[i]: continue
        u0 = VR.ts(d, 16, 0); i0 = int(np.searchsorted(t, u0))
        if i0 >= len(t) or t[i0] - u0 > tol: continue
        ask = o[i0] + sp[i0]; rec = {"d": d, "besleme": name, "donem": "KESIF" if d <= pd.Timestamp("2021-10-31") else "TEST"}
        pc = p.iloc[i]
        for H in HS:
            for mode in ("XP", "BE"):
                prev, ex = pc, None
                for j in range(i + 1, min(i + H + 1, len(days))):
                    pj = p.iloc[j]
                    if not np.isfinite(pj): continue
                    up = pj > prev
                    if (j - i) <= 5:
                        if up or (mode == "XP" and j == i + H) or (mode == "XP" and j == len(days) - 1): ex = j; break
                        if mode == "BE" and j - i == 5 and H == 5: ex = j; break
                    else:
                        cond = up if mode == "XP" else (pj >= ask)
                        if cond or j == i + H: ex = j; break
                    prev = pj
                if ex is None: continue
                rec[f"{mode}{H}"] = (p.iloc[ex] / ask - 1) * 1e4 - FIN * (days[ex] - d).days
        rows.append(rec)
    return pd.DataFrame(rows)
feeds = {"DUKA_NDX": (G.ndx_bars(), 60)}
for s, since in (("NAS100", None), ("US500", "2018-06-01"), ("US30", None), ("US2000", None)):
    feeds[f"MT5_{s}"] = (R.KD.mt5_m30(s, since), 1800)
T = pd.concat([trades(b, st, nm) for nm, (b, st) in feeds.items()], ignore_index=True)
T.to_parquet(HERE / "results/ek7_uzun.parquet")
def mm(v, d):
    v = np.asarray(v); ok = np.isfinite(v); v, d = v[ok], np.asarray(d)[ok]
    eq = pd.Series(v, index=pd.to_datetime(d)).sort_index().cumsum()
    return {"toplam": v.sum(), "zarar": v[v < 0].sum(), "DD": (eq - eq.cummax()).min(), "kotu10": np.sort(v)[:max(1, len(v) // 10)].mean(), "n": len(v)}
out = {}
cols = [f"{m}{H}" for H in HS for m in ("XP", "BE")]
for f, g in T.groupby("besleme"):
    for e, z in g.groupby("donem"):
        b = mm(z.XP5, z.d)
        out[f"{f}_{e}"] = {c: {"kar×": round(mm(z[c], z.d)["toplam"] / b["toplam"], 2), "zarar×": round(mm(z[c], z.d)["zarar"] / b["zarar"], 2),
                               "DD×": round(mm(z[c], z.d)["DD"] / b["DD"], 2), "kotu10×": round(mm(z[c], z.d)["kotu10"] / b["kotu10"], 2)} for c in cols}
for k, v in out.items():
    print("==", k, f"(taban XP5)")
    for c, m in v.items(): print(f"   {c:6s} kâr× {m['kar×']:5.2f} zarar× {m['zarar×']:5.2f} DD× {m['DD×']:5.2f} kötü10× {m['kotu10×']:5.2f}")
(HERE / "results/ek7_uzun.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=float))
