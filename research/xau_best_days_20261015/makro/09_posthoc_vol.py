"""POST-HOC (05 sonuçları görüldükten sonra): R = $hareket / (1,5×ATR_H1). En iyi günlerde $ hareket ve SL$; düşük
oynaklık rejimi (gvol = ATR / önceki 2000-bar medyan ATR) kuyruk payını artırıyor mu? + rastgele BUY karşılığı."""
import os, numpy as np, pandas as pd
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
tr = pd.read_csv(os.path.join(OUT, "trades_feat.csv")); rb = pd.read_csv(os.path.join(OUT, "random_feat.csv"))
days = pd.read_csv(os.path.join(OUT, "days.csv"))
tr["sl_usd"] = tr.atr * 1.5; tr["usd_move"] = tr.R * tr.sl_usd; tr["pct_move"] = tr.usd_move / tr.entry_px * 100
t = tr[tr.ent_day.isin(days.head(20).ent_day)].sort_values("R", ascending=False)
print(t[["ent_day", "R", "sl_usd", "usd_move", "pct_move", "gvol", "vix_prev"]].round(2).to_string(index=False))
print("tüm işlemler gvol medyan", round(tr.gvol.median(), 2), "| en iyi 20 gvol medyan", round(t.gvol.median(), 2))
q = pd.qcut(tr.gvol, 5); qr = pd.qcut(rb.gvol, q.cat.categories.right.insert(0, 0).values if False else 5)
h1 = tr.year <= 2016
g = tr.groupby(q, observed=True).agg(n=("R", "size"), ortR=("R", "mean"), P3=("R", lambda r: (r >= 3).mean()), pct_move_med=("pct_move", lambda x: x.abs().median()))
g["ortR_0816"] = tr[h1].groupby(q[h1], observed=True).R.mean(); g["ortR_1726"] = tr[~h1].groupby(q[~h1], observed=True).R.mean()
g["P3_0816"] = tr[h1].groupby(q[h1], observed=True).R.apply(lambda r: (r >= 3).mean()); g["P3_1726"] = tr[~h1].groupby(q[~h1], observed=True).R.apply(lambda r: (r >= 3).mean())
print(g.round(3).to_string())
gr = rb.groupby(pd.cut(rb.gvol, q.cat.categories), observed=True).agg(n=("R", "size"), ortR=("R", "mean"), P3=("R", lambda r: (r >= 3).mean()))
print("rastgele BUY aynı kovalar\n", gr.round(3).to_string())
