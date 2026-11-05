import itertools, numpy as np, pandas as pd, yfinance as yf
from lab import ledger, HERE
pd.set_option("display.width", 220); pd.set_option("display.max_colwidth", 40)
def g(t):
    s = yf.Ticker(t).history(start="2000-06-01", end="2026-11-05", auto_adjust=True)["Close"]; s.index = s.index.tz_localize(None).normalize(); return s
P = pd.DataFrame({t: g(t) for t in ("QQQ", "SPY", "IWM", "GC=F", "CL=F", "^VIX", "^TNX", "DX-Y.NYB", "^VIX3M")}).sort_index(); P.loc[P["CL=F"] <= 5, "CL=F"] = np.nan
Pf = P.ffill(); chg = Pf.pct_change() * 100; chg["^TNX"] = Pf["^TNX"].diff(); chg["SPY/QQQ"] = np.log(Pf.QQQ / Pf.SPY).diff() * 100; chg["IWM/QQQ"] = np.log(Pf.QQQ / Pf.IWM).diff() * 100; chg["VIX2"] = chg["^VIX"]
Z = (chg - chg.rolling(60).mean().shift(1)) / chg.rolling(60).std().shift(1)
SIG = ["^VIX", "^TNX", "DX-Y.NYB", "CL=F", "GC=F", "QQQ", "SPY/QQQ", "IWM/QQQ"]; TG = ["QQQ", "GC=F", "CL=F"]
TH = (("≤−2", lambda z: z <= -2), ("≤−1,5", lambda z: z <= -1.5), ("≥1,5", lambda z: z >= 1.5), ("≥2", lambda z: z >= 2))
PER = {"k": ("2012-01-01", "2024-01-01"), "b": ("2001-01-01", "2012-01-01"), "s": ("2024-01-01", "2027-01-01")}
rows = []
for tg, sg, (tn, tf), h, sd in itertools.product(TG, SIG, TH, (1, 3), (1, -1)):
    px = P[tg].dropna(); ret = (px.shift(-h) / px - 1) * 1e4; ret = sd * ret - 3 - (2 * h if sd > 0 else .5 * h); m = tf(Z[sg]).reindex(ret.index).fillna(False)
    row = {"hedef": tg, "sinyal": sg, "eşik": tn, "h": h, "yön": sd}
    for p, (a, b) in PER.items():
        i = (ret.index >= a) & (ret.index < b); x = ret[i & m.to_numpy()].dropna(); bs = ret[i].dropna(); row[f"{p}_n"] = len(x)
        if len(x) < 10: continue
        u, inv = np.unique(x.index.to_period("M").astype(str), return_inverse=True); S, N = np.bincount(inv, x.to_numpy()), np.bincount(inv); ix = np.random.default_rng(3).integers(0, len(u), (800, len(u))); bm = S[ix].sum(1) / N[ix].sum(1); hh = len(x) // 2
        row.update({f"{p}_ort": round(x.mean(), 1), f"{p}_fazla": round(x.mean() - bs.mean(), 1), f"{p}_P": round(float((bm > bs.mean()).mean()), 3), f"{p}_is": round((x > 0).mean(), 3), f"{p}_y1": round(x.iloc[:hh].mean(), 1), f"{p}_y2": round(x.iloc[hh:].mean(), 1)})
    rows.append(row); ledger(tg, f"T13 {sg} {tn} h{h} y{sd}", "", "kbs", {"n": row.get("k_n"), "bp": row.get("k_ort"), "P": row.get("k_P")})
d = pd.DataFrame(rows); d.to_csv(HERE / "results/r11.csv", index=False); d["mp"] = d[["k_P", "b_P", "s_P"]].min(axis=1)
c = ["sinyal", "eşik", "h", "yön", "k_n", "k_ort", "k_fazla", "k_P", "b_n", "b_ort", "b_fazla", "b_P", "s_n", "s_ort", "s_fazla", "s_P", "mp"]
for t, g_ in d.groupby("hedef"):
    ok = g_[(g_.k_fazla > 0) & (g_.b_fazla > 0) & (g_.s_fazla > 0) & (g_.k_ort > 0) & (g_.b_ort > 0) & (g_.s_ort > 0)].sort_values("mp", ascending=False)
    print(f"\n== {t}: hücre {len(g_)} minP≥.9: {(g_.mp >= .9).sum()} (şans {len(g_) * .001:.2f}) ≥.8: {(g_.mp >= .8).sum()} (şans {len(g_) * .008:.2f})"); print(ok[c].head(10).to_string(index=False))
