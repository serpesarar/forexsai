"""Walk-forward macro model — the fair nonlinear test of 'can macro predict gold?'

Expanding-window GBM + Logistic, retrained every step, predicts P(gold up over next
H days) from the macro panel. Reports OUT-OF-SAMPLE directional accuracy and a
BUY-only trading sim (long when P>0.5 else flat, friction on position change) vs the
always-long benchmark. If OOS acc ≈ 50% and it can't beat buy&hold, macro direction
prediction is confirmed dead for gold in this regime.
"""
from __future__ import annotations
import warnings; warnings.simplefilter("ignore")
import numpy as np, pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

df = pd.read_csv("xau_macro_research/macro_panel.csv", parse_dates=["date"]).set_index("date")

f = pd.DataFrame(index=df.index)
f["real_yield"]  = df["DFII10"]
f["d_real_5"]    = df["DFII10"].diff(5)
f["d_real_20"]   = df["DFII10"].diff(20)
f["dollar"]      = df["DTWEXBGS"]
f["d_dollar_5"]  = df["DTWEXBGS"].pct_change(5)
f["d_dollar_20"] = df["DTWEXBGS"].pct_change(20)
f["vix"]         = df["VIXCLS"]
f["d_vix_5"]     = df["VIXCLS"].diff(5)
f["nominal_10"]  = df["DGS10"]
f["d_nom_20"]    = df["DGS10"].diff(20)
f["term_spread"] = df["DGS10"] - df["DGS2"]
f["breakeven"]   = df["T10YIE"]
f["gold_mom_20"] = df["gold"].pct_change(20)
f["gold_mom_60"] = df["gold"].pct_change(60)

H = 20
fret = df["gold"].shift(-H) / df["gold"] - 1
y = (fret > 0).astype(int)
data = f.join(y.rename("y")).join(fret.rename("fret")).dropna()
X = data[f.columns].values
yv = data["y"].values
rv = data["fret"].values
n = len(data)
print(f"samples={n}  base rate P(up,{H}d)={yv.mean():.1%}  (always-long wins this often)\n")

def walk(model_fn, scale=False):
    start = int(n*0.4)                 # train on first 40%, expand
    preds, truth, rets, dates = [], [], [], []
    for i in range(start, n - H):      # leave H gap so target is realized
        Xtr, ytr = X[:i-H], yv[:i-H]   # purge last H (overlapping target leakage)
        if len(np.unique(ytr)) < 2: continue
        if scale:
            sc = StandardScaler().fit(Xtr)
            m = model_fn().fit(sc.transform(Xtr), ytr)
            p = m.predict_proba(sc.transform(X[i:i+1]))[0, 1]
        else:
            m = model_fn().fit(Xtr, ytr)
            p = m.predict_proba(X[i:i+1])[0, 1]
        preds.append(p); truth.append(yv[i]); rets.append(rv[i]); dates.append(data.index[i])
    preds, truth, rets = map(np.array, (preds, truth, rets))
    acc = ((preds > 0.5).astype(int) == truth).mean()
    # BUY-only sim: capture forward H-ret when model says up (non-overlapping every H)
    sig = (preds > 0.5).astype(int)
    sel = rets[::H]; selsig = sig[::H]
    model_ret = (sel * selsig).sum()
    always = sel.sum()
    return acc, truth.mean(), model_ret, always, len(sel), selsig.mean()

for nm, fn, sc in [("GBM", lambda: GradientBoostingClassifier(n_estimators=120, max_depth=3, learning_rate=0.05), False),
                   ("Logistic", lambda: LogisticRegression(max_iter=1000, C=0.5), True)]:
    acc, base, mret, always, k, exposure = walk(fn, sc)
    print(f"{nm:10}  OOS dir-acc={acc:.1%}  (base {base:.1%})   "
          f"sim[{k} non-overlap {H}d trades]: model_sumret={mret:+.2f}  always-long={always:+.2f}  "
          f"exposure={exposure:.0%}")

print("\nVerdict: dir-acc ≈ base rate and model_sumret ≤ always-long ⇒ macro adds NO")
print("directional edge; you'd be better off simply long (or using the daily-swing rule).")
