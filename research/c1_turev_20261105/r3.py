import numpy as np, pandas as pd, yfinance as yf, itertools
from lab import ledger, HERE
q = yf.Ticker("QQQ").history(start="1999-03-10", end="2026-11-05", auto_adjust=True); q.index = q.index.tz_localize(None).normalize()
v = yf.Ticker("^VIX").history(start="1999-01-01", end="2026-11-05")["Close"]; v.index = v.index.tz_localize(None).normalize()
d = pd.DataFrame({"o": q.Open, "h": q.High, "l": q.Low, "c": q.Close}); d["vix"] = v.reindex(d.index).ffill()
d["ret"] = d.c.pct_change() * 1e4; d["pos"] = (d.c - d.l) / (d.h - d.l + 1e-9)
g = d.c.diff(); up = g.clip(lower=0).ewm(alpha=.5, adjust=False).mean(); dn = (-g.clip(upper=0)).ewm(alpha=.5, adjust=False).mean(); d["rsi2"] = 100 - 100 / (1 + up / (dn + 1e-9))
d["low5"] = d.c <= d.c.rolling(5).min(); d["high5"] = d.c >= d.c.rolling(5).max(); dd = (g < 0).astype(int); d["down3"] = dd.rolling(3).sum() == 3; d["up3"] = (g > 0).astype(int).rolling(3).sum() == 3
d["ma200"] = d.c > d.c.rolling(200).mean(); d["ret5"] = d.c.pct_change(5) * 1e4
EX = {"gece": (d.o.shift(-1) / d.c - 1) * 1e4 - 2 - 2, "1g": (d.c.shift(-1) / d.c - 1) * 1e4 - 2 - 2, "3g": (d.c.shift(-3) / d.c - 1) * 1e4 - 2 - 6, "sabah gir, kapan": (d.c.shift(-1) / d.o.shift(-1) - 1) * 1e4 - 2}
LONG = {"vix≥18,4": d.vix >= 18.4, "vix18-25": d.vix.between(18.4, 25), "vix≥25": d.vix >= 25, "gün−": d.ret < 0, "gün≤−%1": d.ret <= -100, "gün≤−%2": d.ret <= -200, "dip kapanış": d.pos <= .25, "rsi2<10": d.rsi2 < 10, "rsi2<5": d.rsi2 < 5, "5g dibi": d.low5, "3 düşüş": d.down3, "5g≤−%4": d.ret5 <= -400}
base = list(LONG.items()); cond = dict(base)
for a, b in itertools.combinations(["vix≥18,4", "vix18-25", "gün−", "gün≤−%1", "dip kapanış", "rsi2<10", "5g dibi", "3 düşüş"], 2):
    cond[f"{a}∧{b}"] = LONG[a] & LONG[b]
for a in ["gün≤−%1", "rsi2<10", "5g dibi", "dip kapanış"]:
    cond[f"{a}∧ma200+"] = LONG[a] & d.ma200; cond[f"{a}∧ma200−"] = LONG[a] & ~d.ma200
SHORT = {"vix<15": d.vix < 15, "rsi2>90": d.rsi2 > 90, "rsi2>95": d.rsi2 > 95, "5g zirve": d.high5, "3 yükseliş": d.up3, "gün≥+%1": d.ret >= 100, "vix<15∧rsi2>90": (d.vix < 15) & (d.rsi2 > 90), "vix<15∧5g zirve": (d.vix < 15) & d.high5, "vix<15∧gün≥+%1": (d.vix < 15) & (d.ret >= 100), "vix≥18,4∧gün≥+%1": (d.vix >= 18.4) & (d.ret >= 100), "vix≥18,4∧rsi2>90": (d.vix >= 18.4) & (d.rsi2 > 90)}
PER = {"k": ("2012-01-01", "2024-01-01"), "b": ("1999-03-10", "2012-01-01"), "s": ("2024-01-01", "2026-11-05")}
def st(x, m, per):
    a, b = PER[per]; idx = (x.index >= a) & (x.index < b); s = x[idx & m.reindex(x.index).fillna(False).to_numpy()].dropna(); base_ = x[idx].dropna()
    if len(s) < 8: return {"n": len(s)}
    u, inv = np.unique(s.index.to_period("M").astype(str), return_inverse=True); S, N = np.bincount(inv, s.to_numpy()), np.bincount(inv); ix = np.random.default_rng(3).integers(0, len(u), (2000, len(u)))
    bm = S[ix].sum(1) / N[ix].sum(1); h = len(s) // 2
    return {"n": len(s), "ort": round(s.mean(), 1), "taban": round(base_.mean(), 1), "fark": round(s.mean() - base_.mean(), 1), "isabet": round((s > 0).mean(), 3), "P_fark": round(float((bm > base_.mean()).mean()), 3), "y1": round(s.iloc[:h].mean(), 1), "y2": round(s.iloc[h:].mean(), 1)}
rows = []
for sd, cs in ((1, cond), (-1, SHORT)):
    for (nm, m), (ex, x) in itertools.product(cs.items(), EX.items()):
        xx = sd * (x + (4 if ex != "sabah gir, kapan" and ex != "3g" else (8 if ex == "3g" else 2))) - (4 if ex not in ("3g", "sabah gir, kapan") else (8 if ex == "3g" else 2))
        row = {"yön": "uzun" if sd > 0 else "kısa", "koşul": nm, "çıkış": ex}
        for p in PER:
            r = st(xx, m, p); ledger("QQQ", f"T3 {row['yön']} {ex}", nm, p, {"n": r.get("n"), "R": None, "bp": r.get("ort"), "isabet": r.get("isabet"), "P": r.get("P_fark"), "y1": r.get("y1"), "y2": r.get("y2")})
            for kk, vv in r.items(): row[f"{p}_{kk}"] = vv
        rows.append(row)
df = pd.DataFrame(rows); df.to_csv(HERE / "results/r3.csv", index=False)
pd.set_option("display.width", 220); pd.set_option("display.max_colwidth", 34)
print("hücre", len(df))
ok = df[(df.k_n >= 40) & (df.k_P_fark >= .95) & (df.k_fark > 0) & (df.k_y1 > 0) & (df.k_y2 > 0) & (df.b_fark > 0)]
c = ["yön", "koşul", "çıkış", "k_n", "k_ort", "k_taban", "k_P_fark", "b_n", "b_ort", "b_taban", "b_P_fark", "s_n", "s_ort", "s_taban", "s_P_fark"]
print(len(ok)); print(ok.sort_values("k_fark", ascending=False)[c].head(40).to_string(index=False))
