import numpy as np, pandas as pd, itertools
from lab2 import *
from r4_core import series, feats
pd.set_option("display.width", 230); pd.set_option("display.max_colwidth", 34)
PER = {"k": ("2022-08-15", "2025-01-01"), "b": ("2018-05-25", "2022-08-15"), "s": ("2025-01-01", "2027-01-01")}
CFG = {"NAS100": [("M30", 930)], "XAUUSD": [("M30", 930), ("M30", 510)], "SpotCrude": [("M30", 930), ("M30", 540)]}
vx = MAC.vix.dropna(); vxr = (vx / vx.rolling(10).mean()).shift(1); vxj = vx.pct_change().shift(1) * 100
def day_hl(sym, dm):
    x = mt5_bars(sym, "M30"); x["d"] = x.ts_et.dt.normalize(); x["m"] = x.ts_et.dt.hour * 60 + x.ts_et.dt.minute
    o0 = 570 if sym == "NAS100" else 510 if sym == "XAUUSD" else 540
    y = x[(x.m >= o0) & (x.m < dm)] if dm > o0 else x[(x.m < dm) & (x.m >= 0)]
    return y.groupby("d").h.max(), y.groupby("d").l.min()
Sx = {s: series(s, "M30", 930) for s in CFG}; Fx = {s: feats(Sx[s], s) for s in CFG}
rows = []
for sym, cf in CFG.items():
    others = [o for o in CFG if o != sym]
    for tf, dm in cf:
        s = series(sym, tf, dm); f = feats(s, sym); sp = SP[sym]
        H, L = day_hl(sym, dm); hh, ll = H.reindex(s.index), L.reindex(s.index); ibs = (s.S - ll) / (hh - ll + 1e-9)
        z3 = s.S.pct_change(3) / (s.S.pct_change().rolling(60).std() * np.sqrt(3)); z5 = s.S.pct_change(5) / (s.S.pct_change().rolling(60).std() * np.sqrt(5))
        idx = pd.DatetimeIndex(s.index); vr = vxr.reindex(idx, method="ffill"); vj = vxj.reindex(idx, method="ffill")
        ndown = (s.S.diff() < 0).astype(int); run_ = ndown.groupby((ndown == 0).cumsum()).cumsum()
        L_ = {"ibs<0,2": ibs < .2, "ibs<0,1": ibs < .1, "ibs<0,2∧rsi2<10": (ibs < .2) & (f.rsi2 < 10), "ibs<0,2∧gün−": (ibs < .2) & (f.r1 < 0), "z3<−1,5": z3 < -1.5, "z3<−2": z3 < -2, "z5<−1,5": z5 < -1.5, "z5<−2": z5 < -2,
              "vix/ort10>1,1": vr > 1.1, "vix/ort10>1,2": vr > 1.2, "vix sıçrama>%10": vj > 10, "vix sıçrama>%20": vj > 20, "rsi2<10∧vix/ort10>1,1": (f.rsi2 < 10) & (vr > 1.1), "rsi2<10∧vix/ort10≤1,1": (f.rsi2 < 10) & (vr <= 1.1), "düşüş≥2": run_ >= 2, "düşüş≥3": run_ >= 3, "düşüş≥4": run_ >= 4, "düşüş≥5": run_ >= 5}
        for o in others:
            fo = Fx[o].reindex(idx, method="ffill"); so = Sx[o].S.reindex(idx, method="ffill").pct_change() * 1e4
            L_[f"rsi2<10∧{o} rsi2<20"] = (f.rsi2 < 10) & (fo.rsi2 < 20); L_[f"rsi2<10∧{o} rsi2>50"] = (f.rsi2 < 10) & (fo.rsi2 > 50); L_[f"{o} rsi2<10"] = fo.rsi2 < 10; L_[f"{o} gün≤−%1"] = so <= -100; L_[f"{o} gün≥+%1"] = so >= 100; L_[f"gün−∧{o} gün+"] = (f.r1 < 0) & (so > 0); L_[f"gün−∧{o} gün−"] = (f.r1 < 0) & (so < 0)
        U_ = {"rsi2>90": f.rsi2 > 90, "rsi2>95": f.rsi2 > 95, "5g zirve": f.high5, "ibs>0,8": ibs > .8, "ibs>0,9": ibs > .9, "z3>1,5": z3 > 1.5, "z5>2": z5 > 2, "vix/ort10<0,9": vr < .9, "rsi2>90∧vix<15": (f.rsi2 > 90) & (f.vix < 15), "rsi2>90∧vix≥18,4": (f.rsi2 > 90) & (f.vix >= 18.4), "5g zirve∧ma200+": f.high5 & f.ma200}
        for h in (1, 2, 3):
            ex = s.E.shift(-h); lng = (ex / (s.E + sp) - 1) * 1e4 - 2.0 * h; sht = (s.E / (ex + sp) - 1) * 1e4 - 0.5 * h
            for side, ret, cs in ((1, lng, L_), (1, lng, U_), (-1, sht, U_), (-1, sht, L_)):
                for nm, m in cs.items():
                    row = {"sym": sym, "tf": tf, "saat": f"{dm//60}:{dm%60:02d}", "yön": "uzun" if side > 0 else "kısa", "koşul": nm, "h": h}
                    for p, (a, b) in PER.items():
                        i_ = (s.index >= a) & (s.index < b); x = ret[i_ & m.fillna(False).to_numpy()].dropna(); bs = ret[i_].dropna()
                        if len(x) < 8: row[f"{p}_n"] = len(x); continue
                        u, inv = np.unique(x.index.to_period("M").astype(str), return_inverse=True); S_, N_ = np.bincount(inv, x.to_numpy()), np.bincount(inv); ix = np.random.default_rng(3).integers(0, len(u), (1500, len(u))); bm = S_[ix].sum(1) / N_[ix].sum(1); hh_ = len(x) // 2
                        row.update({f"{p}_n": len(x), f"{p}_ort": round(x.mean(), 1), f"{p}_taban": round(bs.mean(), 1), f"{p}_P": round(float((bm > bs.mean()).mean()), 3), f"{p}_isabet": round((x > 0).mean(), 3), f"{p}_y1": round(x.iloc[:hh_].mean(), 1), f"{p}_y2": round(x.iloc[hh_:].mean(), 1)})
                    rows.append(row); ledger(sym, f"T5 {row['yön']} {row['saat']} h{h}", nm, "kbs", {"n": row.get("k_n"), "bp": row.get("k_ort"), "P": row.get("k_P")})
df = pd.DataFrame(rows).drop_duplicates(["sym", "saat", "yön", "koşul", "h"]); df.to_csv(HERE / "results/r5.csv", index=False); print("hücre", len(df))
c = ["saat", "yön", "koşul", "h", "k_n", "k_ort", "k_P", "b_n", "b_ort", "b_P", "s_n", "s_ort", "s_P"]
for sym, g in df.groupby("sym"):
    ok = g[(g.k_n >= 25) & (g.k_P >= .95) & (g.k_y1 > 0) & (g.k_y2 > 0) & (g.k_ort > 0) & (g.b_ort > 0) & (g.b_P >= .9) & (g.s_ort > g.s_taban) & (g.s_ort > 0)]
    print(f"\n=== {sym} hücre {len(g)} tam aday {len(ok)}"); print(ok.sort_values("k_ort", ascending=False)[c].head(26).to_string(index=False))
