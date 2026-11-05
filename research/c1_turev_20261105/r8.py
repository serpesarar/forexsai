import numpy as np, pandas as pd, itertools
from lab2 import *
pd.set_option("display.width", 220); pd.set_option("display.max_colwidth", 30)
PER = {"M30": [("k", "2022-08-15", "2025-01-01"), ("b", "2018-05-25", "2022-08-15"), ("s", "2025-01-01", "2027-01-01")]}
def rsi(S, a=.5):
    g = S.diff(); up = g.clip(lower=0).ewm(alpha=a, adjust=False).mean(); dn = (-g.clip(upper=0)).ewm(alpha=a, adjust=False).mean(); return 100 - 100 / (1 + up / (dn + 1e-12))
def mb(x):
    u, inv = np.unique(x.index.to_period("M").astype(str), return_inverse=True); S, N = np.bincount(inv, x.to_numpy()), np.bincount(inv); ix = np.random.default_rng(3).integers(0, len(u), (800, len(u))); return float(((S[ix].sum(1) / N[ix].sum(1)) > 0).mean())
rows = []
for sym, sess in (("NAS100", (570, 930)), ("XAUUSD", (510, 930)), ("SpotCrude", (540, 870))):
    for tf, per in (("M30", ((("k", "2022-08-15", "2025-01-01"), ("b", "2018-05-25", "2022-08-15"), ("s", "2025-01-01", "2027-01-01")))), ("M15", (("k", "2022-08-15", "2024-01-01"), ("b", "2024-01-01", "2025-01-01"), ("s", "2025-01-01", "2027-01-01")))):
        x = mt5_bars(sym, tf).reset_index(drop=True); x["m"] = x.ts_et.dt.hour * 60 + x.ts_et.dt.minute; x["d"] = x.ts_et.dt.normalize(); sp = SP[sym]; R2 = rsi(x.c); 
        vx = MAC.vix.shift(1).reindex(x.d, method="ffill").to_numpy(); ins = (x.m >= sess[0]) & (x.m < sess[1]) & (x.ts_et.dt.dayofweek < 5)
        barm = int(tf[1:]); o = x.o.to_numpy(); t = x.t.to_numpy()
        for th, side, vf, hold in itertools.product((5, 10), (1, -1), ("tümü", "vix≥18,4", "vix<18,4", "vix<15"), (1, 2, 4, 8)):
            trig = (R2 < th) if side > 0 else (R2 > 100 - th)
            mask = trig.to_numpy() & ins.to_numpy() & ({"tümü": np.ones(len(x), bool), "vix≥18,4": vx >= 18.4, "vix<18,4": vx < 18.4, "vix<15": vx < 15}[vf])
            ids = np.flatnonzero(mask); keep, last = [], -10**9
            for i in ids:
                if i >= last + hold: keep.append(i); last = i
            ids = np.array([i for i in keep if i + 1 + hold < len(x) and t[i + 1 + hold] - t[i + 1] <= hold * barm * 60 * 1.5], int)
            if len(ids) < 30: continue
            e = o[ids + 1]; ex = o[ids + 1 + hold]
            r = pd.Series(((ex / (e + sp) - 1) if side > 0 else (e / (ex + sp) - 1)) * 1e4, index=x.ts_et.iloc[ids].to_numpy())
            row = {"sym": sym, "tf": tf, "th": th, "yön": side, "vix": vf, "bar": hold}
            for p, a, b in per:
                q = r[(r.index >= a) & (r.index < b)]
                row[f"{p}_n"] = len(q)
                if len(q) >= 20: row[f"{p}_ort"] = round(q.mean(), 2); row[f"{p}_P"] = round(mb(q), 3); row[f"{p}_is"] = round((q > 0).mean(), 3)
            rows.append(row)
df = pd.DataFrame(rows); df.to_csv(HERE / "results/r8.csv", index=False); df["mp"] = df[["k_P", "b_P", "s_P"]].min(axis=1)
print("hücre", len(df)); c = ["sym", "tf", "th", "yön", "vix", "bar", "k_n", "k_ort", "k_is", "b_n", "b_ort", "s_n", "s_ort", "mp"]
print(df[(df.k_ort > 0) & (df.b_ort > 0) & (df.s_ort > 0)].sort_values("mp", ascending=False)[c].head(16).to_string(index=False))
