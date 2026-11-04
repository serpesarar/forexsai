"""Kuyruk riski: en kötü işlem, maks. düşüş (σR, kümülatif), en kötü 10 işlem tarihleri — keşif NDX 1h."""
import pickle, numpy as np, pandas as pd
P = pickle.load(open("results/trades_NDX.pkl", "rb"))["trades"]
for k in [("RSI15", "F0", "MA5", None), ("IBS20", "F0", "k1", None), ("LOW3", "MA", "MA5", None), ("RSI10", "MA", "MA5", None),
          ("RSI15", "F0", "MA5", 2.0), ("IBS20", "F0", "k1", 2.0), ("LOW5", "F0", "MA5", None)]:
    T = P[k]; c = T.R.cumsum(); dd = (c - c.cummax()).min()
    w = T.nsmallest(5, "R")
    print(k, f"n={len(T)} en kötü {T.R.min():+.2f} σR, maksDD {dd:+.1f} σR, toplam {T.R.sum():+.1f}, toplam/|DD| {T.R.sum()/abs(dd):.1f};",
          "en kötü 5:", [(str(r.nyd.date()), round(r.R, 1)) for r in w.itertuples()])
