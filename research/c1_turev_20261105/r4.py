import itertools, numpy as np, pandas as pd
from lab2 import *
pd.set_option("display.width", 230); pd.set_option("display.max_colwidth", 32)
def series(sym, tf, dm):
    x = mt5_bars(sym, tf); x["d"] = x.ts_et.dt.normalize(); x["m"] = x.ts_et.dt.hour * 60 + x.ts_et.dt.minute
    x = x[x.ts_et.dt.dayofweek < 5].reset_index(drop=True)
    ent = x[x.m == dm].set_index("d")
    prev = x.c.shift(1)[x.m == dm]; prev.index = ent.index; gapok = (x.t.diff()[x.m == dm].to_numpy() <= 3 * int(tf[1:] if tf[0] == "M" else 60) * 60)
    s = pd.DataFrame({"S": prev.to_numpy(), "E": ent.o.to_numpy()}, index=ent.index)[gapok]; s = s[~s.index.duplicated()]; return s
def feats(s, sym):
    g = s.S.diff(); up = g.clip(lower=0).ewm(alpha=.5, adjust=False).mean(); dn = (-g.clip(upper=0)).ewm(alpha=.5, adjust=False).mean(); f = pd.DataFrame(index=s.index)
    f["rsi2"] = 100 - 100 / (1 + up / (dn + 1e-12)); f["low5"] = s.S <= s.S.rolling(5).min(); f["high5"] = s.S >= s.S.rolling(5).max(); f["d3"] = (g < 0).rolling(3).sum() == 3; f["u3"] = (g > 0).rolling(3).sum() == 3
    f["r1"] = s.S.pct_change() * 1e4; f["r5"] = s.S.pct_change(5) * 1e4; f["ma200"] = s.S > s.S.rolling(200).mean(); f["dvol"] = s.S.pct_change().rolling(20).std() * 1e4
    idx = pd.DatetimeIndex(s.index); f["vix"] = MAC.vix.shift(1).reindex(idx, method="ffill").to_numpy(); iv = IV[IVK[sym]]; f["iv"] = iv.shift(1).reindex(idx, method="ffill").to_numpy(); f["ivm"] = iv.rolling(252, min_periods=120).median().shift(1).reindex(idx, method="ffill").to_numpy()
    return f
def conds(f, side):
    if side > 0:
        c = {"rsi2<10": f.rsi2 < 10, "rsi2<5": f.rsi2 < 5, "5g dibi": f.low5, "3 düşüş": f.d3, "gün≤−%1": f.r1 <= -100, "5g≤−%4": f.r5 <= -400}
    else:
        c = {"rsi2>90": f.rsi2 > 90, "rsi2>95": f.rsi2 > 95, "5g zirve": f.high5, "3 yükseliş": f.u3, "gün≥+%1": f.r1 >= 100, "5g≥+%4": f.r5 >= 400}
    out = dict(c)
    for k, v in c.items():
        out[f"{k}∧vix≥18,4"] = v & (f.vix >= 18.4); out[f"{k}∧vix<18,4"] = v & (f.vix < 18.4); out[f"{k}∧iv yüksek"] = v & (f.iv >= f.ivm); out[f"{k}∧iv düşük"] = v & (f.iv < f.ivm); out[f"{k}∧ma200+"] = v & f.ma200; out[f"{k}∧ma200−"] = v & ~f.ma200
    return out
PER = {"k": ("2022-08-15", "2025-01-01"), "b": ("2018-05-25", "2022-08-15"), "s": ("2025-01-01", "2027-01-01")}
CFG = {"NAS100": [("M30", 930), ("M30", 570), ("M15", 945)], "XAUUSD": [("M30", 930), ("M30", 510), ("M15", 945)], "SpotCrude": [("M30", 930), ("M30", 540), ("M15", 945)]}
rows = []
for sym, cf in CFG.items():
    for tf, dm in cf:
        s = series(sym, tf, dm); f = feats(s, sym); sp = SP[sym]
        for h in (1, 2, 3, 5):
            ex = s.E.shift(-h); nights = h
            lng = (ex / (s.E + sp) - 1) * 1e4 - 2.0 * nights; sht = ((s.E) / (ex + sp) - 1) * 1e4 + 2.0 * nights * 0 - 0.5 * nights
            for side, ret in ((1, lng), (-1, sht)):
                for nm, m in conds(f, side).items():
                    row = {"sym": sym, "tf": tf, "saat": f"{dm//60}:{dm%60:02d}", "yön": "uzun" if side > 0 else "kısa", "koşul": nm, "h": h}
                    for p, (a, b) in PER.items():
                        idx = (s.index >= a) & (s.index < b); x = ret[idx & m.fillna(False).to_numpy()].dropna(); bs = ret[idx].dropna()
                        if len(x) < 8:
                            row[f"{p}_n"] = len(x); continue
                        u, inv = np.unique(x.index.to_period("M").astype(str), return_inverse=True); S, N = np.bincount(inv, x.to_numpy()), np.bincount(inv); ix = np.random.default_rng(3).integers(0, len(u), (1500, len(u))); bm = S[ix].sum(1) / N[ix].sum(1); hh = len(x) // 2
                        row.update({f"{p}_n": len(x), f"{p}_ort": round(x.mean(), 1), f"{p}_taban": round(bs.mean(), 1), f"{p}_P": round(float((bm > bs.mean()).mean()), 3), f"{p}_Pabs": round(float((bm > 0).mean()), 3), f"{p}_isabet": round((x > 0).mean(), 3), f"{p}_y1": round(x.iloc[:hh].mean(), 1), f"{p}_y2": round(x.iloc[hh:].mean(), 1)})
                    rows.append(row)
                    ledger(sym, f"T4 {row['yön']} {tf} {row['saat']} h{h}", nm, "kbs", {"n": row.get("k_n"), "bp": row.get("k_ort"), "P": row.get("k_P")})
df = pd.DataFrame(rows); df.to_csv(HERE / "results/r4.csv", index=False); print("hücre", len(df))
c = ["tf", "saat", "yön", "koşul", "h", "k_n", "k_ort", "k_taban", "k_P", "b_n", "b_ort", "b_taban", "b_P", "s_n", "s_ort", "s_taban", "s_P"]
for sym, g in df.groupby("sym"):
    ok = g[(g.k_n >= 25) & (g.k_P >= .95) & (g.k_ort > g.k_taban) & (g.k_y1 > 0) & (g.k_y2 > 0) & (g.b_ort > g.b_taban) & (g.b_P >= .9) & (g.s_ort >= g.s_taban) & (g.k_ort > 0) & (g.b_ort > 0) & (g.s_ort > 0)]
    print(f"\n=== {sym} hücre {len(g)} tam aday {len(ok)}"); print(ok.sort_values("k_ort", ascending=False)[c].head(24).to_string(index=False))
