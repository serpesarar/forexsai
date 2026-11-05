import numpy as np, pandas as pd, itertools, time
from lab2 import *
pd.set_option("display.width", 220); pd.set_option("display.max_colwidth", 30)
PER = {"k": ("2022-08-15", "2025-01-01"), "b": ("2018-05-25", "2022-08-15"), "s": ("2025-01-01", "2027-01-01")}
rows = []
def mboot(x):
    u, inv = np.unique(x.index.to_period("M").astype(str), return_inverse=True); S, N = np.bincount(inv, x.to_numpy()), np.bincount(inv); ix = np.random.default_rng(3).integers(0, len(u), (800, len(u))); return float(((S[ix].sum(1) / N[ix].sum(1)) > 0).mean())
for sym in ("XAUUSD", "SpotCrude", "NAS100"):
    x = mt5_bars(sym, "M30"); x = x[x.ts_et.dt.minute == 0].copy(); x["d"] = x.ts_et.dt.normalize(); x["hr"] = x.ts_et.dt.hour
    O = x.pivot_table(index="d", columns="hr", values="o", aggfunc="first"); sp = SP[sym]; iv = IV[IVK[sym]]; ivm = iv.rolling(252, min_periods=120).median()
    hi = (iv.shift(1) >= ivm.shift(1)).reindex(O.index, method="ffill").fillna(False)
    for h0, dur in itertools.product(range(24), (2, 4, 6, 8, 12, 16)):
        h1 = (h0 + dur) % 24; nextd = h0 + dur >= 24
        if h0 not in O or h1 not in O: continue
        e = O[h0]; ex = O[h1].shift(-1) if nextd else O[h1]
        crosses17 = (h0 < 17 <= h0 + dur) or (h0 + dur >= 41)
        fin = 2.0 if crosses17 else 0.0
        lng = (ex / (e + sp) - 1) * 1e4 - fin; sht = (e / (ex + sp) - 1) * 1e4 - (0.5 if crosses17 else 0)
        for side, ret in ((1, lng), (-1, sht)):
            for fn, m in (("tümü", pd.Series(True, index=O.index)), ("iv yüksek", hi), ("iv düşük", ~hi)):
                row = {"sym": sym, "h0": h0, "dur": dur, "yön": "uzun" if side > 0 else "kısa", "filtre": fn}
                for p, (a, b) in PER.items():
                    r = ret[(ret.index >= a) & (ret.index < b) & m.to_numpy()].dropna()
                    if len(r) < 30: row[f"{p}_n"] = len(r); continue
                    hh = len(r) // 2; row.update({f"{p}_n": len(r), f"{p}_ort": round(r.mean(), 2), f"{p}_P": round(mboot(r), 3), f"{p}_y1": round(r.iloc[:hh].mean(), 2), f"{p}_y2": round(r.iloc[hh:].mean(), 2), f"{p}_isabet": round((r > 0).mean(), 3)})
                rows.append(row)
df = pd.DataFrame(rows); df.to_csv(HERE / "results/r7.csv", index=False); print("hücre", len(df))
df["mp"] = df[["k_P", "b_P", "s_P"]].min(axis=1)
c = ["h0", "dur", "yön", "filtre", "k_n", "k_ort", "k_P", "b_ort", "b_P", "s_ort", "s_P", "mp"]
for s, g in df.groupby("sym"):
    print(f"\n== {s} hücre {len(g)} | min P ≥ .90 sayısı {(g.mp >= .9).sum()} (şans {len(g) * .1**3:.1f}) | ≥ .95: {(g.mp >= .95).sum()} (şans {len(g) * .05**3:.2f})")
    print(g[(g.k_ort > 0) & (g.b_ort > 0) & (g.s_ort > 0)].sort_values("mp", ascending=False)[c].head(12).to_string(index=False))
