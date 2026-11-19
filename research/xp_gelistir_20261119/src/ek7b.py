import json
from pathlib import Path
import numpy as np, pandas as pd
import veri as VR
R, G, FIN = VR.R, VR.G, VR.FIN
HERE = Path(__file__).resolve().parents[1]
HS = (5, 10, 15, 20, 40)
def trades(b, st, name):
    dp = VR.daily_frame(b, st); p = dp.o960.values
    k1 = (((dp.o960 / dp.tw - 1) * 1e4 <= -50) & (dp.o960 < dp.o900)).values
    t, o, sp = b.t.values, b.o.values, b.sp.values
    days = list(dp.index); tol = 300 if st == 60 else st; rows = []
    for i, d in enumerate(days[:-1]):
        if not k1[i]: continue
        u0 = VR.ts(d, 16, 0); i0 = int(np.searchsorted(t, u0))
        if i0 >= len(t) or t[i0] - u0 > tol: continue
        ask = o[i0] + sp[i0]
        rec = {"d": d, "besleme": name, "donem": "KESIF" if d <= pd.Timestamp("2021-10-31") else "TEST"}
        # taban XP (en geç 5)
        prev, ex = p[i], None
        for j in range(i + 1, min(i + 6, len(days))):
            if not np.isfinite(p[j]): continue
            if p[j] > prev or j == min(i + 5, len(days) - 1): ex = j; break
            prev = p[j]
        if ex is None: continue
        rec["XP"] = (p[ex] / ask - 1) * 1e4 - FIN * (days[ex] - d).days
        for H in HS:
            ex = None
            for j in range(i + 1, min(i + H + 1, len(days))):
                if not np.isfinite(p[j]): continue
                if p[j] >= ask or j == i + H: ex = j; break
            if ex is None: ex = min(i + H, len(days) - 1)
            rec[f"BE{H}"] = (p[ex] / ask - 1) * 1e4 - FIN * (days[ex] - d).days
            rec[f"BE{H}_gun"] = ex - i
        rows.append(rec)
    return pd.DataFrame(rows)
feeds = {"DUKA_NDX": (G.ndx_bars(), 60)}
for s, since in (("NAS100", None), ("US500", "2018-06-01"), ("US30", None), ("US2000", None)):
    feeds[f"MT5_{s}"] = (R.KD.mt5_m30(s, since), 1800)
T = pd.concat([trades(b, st, nm) for nm, (b, st) in feeds.items()], ignore_index=True)
T.to_parquet(HERE / "results/ek7b.parquet")
def mm(v, d):
    v = np.asarray(v, float); d = np.asarray(d)
    eq = pd.Series(v, index=pd.to_datetime(d)).sort_index().cumsum()
    return {"toplam": v.sum(), "zarar": v[v < 0].sum(), "DD": (eq - eq.cummax()).min(), "kotu10": np.sort(v)[:max(1, len(v) // 10)].mean(),
            "isabet": (v > 0).mean() * 100, "en_kotu": v.min()}
out = {}
for f, g in T.groupby("besleme"):
    for e, z in g.groupby("donem"):
        b = mm(z.XP, z.d); rec = {"taban": {k: round(float(v), 1) for k, v in b.items()}}
        for H in HS:
            p_ = mm(z[f"BE{H}"], z.d)
            rec[f"BE{H}"] = {"kar×": round(p_["toplam"] / b["toplam"], 2), "zarar×": round(p_["zarar"] / b["zarar"], 2), "DD×": round(p_["DD"] / b["DD"], 2),
                             "kotu10×": round(p_["kotu10"] / b["kotu10"], 2), "isabet": round(p_["isabet"], 1), "en_kotu": round(p_["en_kotu"]),
                             "ort_gun": round(float(z[f"BE{H}_gun"].mean()), 1)}
        out[f"{f}_{e}"] = rec
        print("==", f, e, "taban", rec["taban"])
        for H in HS: print("   ", f"BE{H}", rec[f"BE{H}"])
(HERE / "results/ek7b.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=float))
