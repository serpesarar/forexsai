"""Ek ayrıştırmalar (ön kayıt §3 'VIX/MA200 bağımlılığı', 2022; DAX 30m tanım teşhisi; SPX/QQQ günlük). Yeniden ayar YOK."""
from __future__ import annotations

import pickle

import numpy as np
import pandas as pd

from engine import (EXITS, SIGNALS, MAXHOLD, VIX_TH, Market, _daily, add_ind, baseline, block_boot, macro, ndx_1h, run_rule,
                    add_excess, FILTERS)

pd.set_option("display.width", 220)


def split_by_state():
    P = pickle.load(open("results/trades_NDX.pkl", "rb"))
    mk = ndx_1h()
    d = mk.day
    b22 = baseline(mk, pd.Timestamp("2022-01-01"), pd.Timestamp("2023-01-01"))
    rows = []
    for (sn, fn, ex, st), T in P["trades"].items():
        if fn != "F0" or len(T) < 20:
            continue
        v = d.vix_prev.to_numpy()[T.t.to_numpy()]
        ma = (d.C > d.ma200).to_numpy()[T.t.to_numpy()]
        y22 = T.nyd.dt.year.to_numpy() == 2022
        own22 = (T.R[y22] - [b22[(st, int(min(h, MAXHOLD)))] for h in T.h[y22]]).mean() if y22.any() else np.nan
        rows.append({"sig": sn, "exit": ex, "stop": st or 0, "n": len(T),
                     "ex_vixHI": T.ex[v >= VIX_TH].mean(), "n_hi": int((v >= VIX_TH).sum()),
                     "ex_vixLO": T.ex[v < VIX_TH].mean(), "ex_aboveMA": T.ex[ma].mean(), "ex_belowMA": T.ex[~ma].mean(),
                     "n_below": int((~ma).sum()), "n22": int(y22.sum()), "R22": T.R[y22].mean(), "ex22_own": own22})
    S = pd.DataFrame(rows)
    S.to_csv("results/state_split_NDX.csv", index=False)
    print("F0 hücreleri (48 sinyal×çıkış×stop ... ) VIX/MA200 ayrışımı, ortalamalar:")
    print(S[["ex_vixHI", "ex_vixLO", "ex_aboveMA", "ex_belowMA", "R22", "ex22_own"]].describe().loc[["mean", "50%"]].round(3))
    print("VIX-yüksek > VIX-düşük oranı", (S.ex_vixHI > S.ex_vixLO).mean().round(3),
          "| MA200 altı > üstü oranı", (S.ex_belowMA > S.ex_aboveMA).mean().round(3),
          "| 2022 kendi-taban fazla > 0 oranı", (S.ex22_own > 0).mean().round(3), "| 2022 ham R>0 oranı", (S.R22 > 0).mean().round(3))
    print(S[S.stop == 0].round(3).to_string())


def dax30_diag():
    """DAX 30m (2021-03+): kapanış 17:00 Berlin'de başlayan 30m bar (17:30 nakit kapanışı), H/L 09:00–17:30, giriş 17:30 barı."""
    b = pd.read_parquet("/Users/melihcanodacioglu/Desktop/panel/research/ndx_gate_forge/data/dax_30m.parquet")
    b = b[["ts", "open", "high", "low", "close"]].reset_index(drop=True)
    d = add_ind(_daily(b, "Europe/Berlin", 30, 1020, 540, 540), None)
    mk = Market("DAX30m", b, d)
    start = d.index[d.sig.notna() & d.ma200.notna()][0]
    end = pd.Timestamp("2026-10-02")
    base = baseline(mk, start, end)
    print(f"\nDAX 30m teşhisi {start.date()}→ (17:30 kapanış): taban 1/3/5 gün",
          [round(base[(None, h)], 3) for h in (1, 3, 5)])
    for sn, fn, ex, st in [("IBS20", "F0", "k1", None), ("IBS30", "F0", "k1", None), ("RSI10", "MA", "MA5", None),
                           ("RSI15", "F0", "MA5", None), ("LOW3", "MA", "MA5", None), ("RSI10", "F0", "MA5", 2.0),
                           ("LOW5", "F0", "MA5", None)]:
        m = (SIGNALS[sn](d).fillna(False) & FILTERS[fn](d).fillna(False)).to_numpy()
        T = add_excess(run_rule(mk, m, ex, st, start, end), base, st)
        P = np.mean(block_boot(T.ex.to_numpy(), T.nyd.astype(str).to_numpy()) > 0)
        print(f"  {sn:5} {fn:3} {ex:3} s={st}: n={len(T)} ortR {T.R.mean():+.3f} fazla {T.ex.mean():+.3f} P %{100*P:.0f}")


def daily_cash(col: str):
    """Nakit/ETF günlük (makro dosyası, ≤2026-07-28): kapanışta karar ve kapanışta giriş (iyimser, maliyetsiz), k gün / MA5."""
    m = macro().loc[:"2026-07-28"]
    d = pd.DataFrame({"C": m[f"{col}_close"], "H": m[f"{col}_high"], "L": m[f"{col}_low"]}).dropna()
    C = d.C
    ch = C.diff()
    up = ch.clip(lower=0).ewm(alpha=.5, adjust=False).mean(); dn = (-ch).clip(lower=0).ewm(alpha=.5, adjust=False).mean()
    d["rsi2"] = 100 - 100 / (1 + up / dn)
    d["ma200"], d["ma5"] = C.rolling(200).mean(), C.rolling(5).mean()
    d["ibs"] = (C - d.L) / (d.H - d.L)
    d["low3"] = C <= C.rolling(3).min()
    d["sig"] = C.pct_change().rolling(20).std()
    d = d.dropna()
    Cv, ma5, sg = d.C.to_numpy(), d.ma5.to_numpy(), d.sig.to_numpy()
    base = {h: np.nanmean([(Cv[t + h] - Cv[t]) / (sg[t] * Cv[t]) for t in range(len(d) - h)]) for h in range(1, 11)}
    rules = {"IBS20 k1": (d.ibs < .2, "k1"), "RSI10∧MA MA5": ((d.rsi2 < 10) & (d.C > d.ma200), "MA5"),
             "RSI15 MA5": (d.rsi2 < 15, "MA5"), "LOW3∧MA MA5": (d.low3 & (d.C > d.ma200), "MA5")}
    print(f"\n{col} günlük (iyimser kapanış icrası, maliyetsiz) {d.index[0].date()}→{d.index[-1].date()}, taban h1 {base[1]:+.3f}")
    for name, (msk, ex) in rules.items():
        msk = msk.to_numpy(); t, R, X, D = 0, [], [], []
        while t < len(d) - 11:
            if msk[t]:
                if ex == "k1":
                    x = t + 1
                else:
                    x = next((j for j in range(t + 1, t + 11) if Cv[j] > ma5[j]), t + 10)
                r = (Cv[x] - Cv[t]) / (sg[t] * Cv[t]); R.append(r); X.append(r - base[x - t]); D.append(d.index[t]); t = x
            else:
                t += 1
        R, X = np.array(R), np.array(X); h = len(R) // 2
        yrs = pd.Series(X, index=pd.DatetimeIndex(D)).groupby(lambda z: z.year).sum()
        print(f"  {name:13} n={len(R)} ortR {R.mean():+.3f} fazla {X.mean():+.3f} yarılar {X[:h].mean():+.3f}/{X[h:].mean():+.3f} "
              f"fazla+ yıl {int((yrs>0).sum())}/{len(yrs)}")


if __name__ == "__main__":
    split_by_state()
    dax30_diag()
    for c in ("SPX", "QQQ", "NDXCASH"):
        daily_cash(c)
