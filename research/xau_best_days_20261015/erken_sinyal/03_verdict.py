"""PROTOCOL §5 verdikt şeması (mekanik). Çıktı: results/verdicts.csv"""
import os, numpy as np, pandas as pd
from common import RES
t = pd.read_csv(os.path.join(RES, "tests.csv")); s = pd.read_csv(os.path.join(RES, "strat.csv"))
tl = pd.read_csv(os.path.join(RES, "tail.csv")); ho = pd.read_csv(os.path.join(RES, "holdout.csv")).set_index("feat")
base = s[(s.feat == "TABAN") & (s.per == "dogrulama")].iloc[0]
rows = []
for _, r in t[t.per == "dogrulama"].iterrows():
    f, u = r.feat, r.use
    disc = t[(t.per == "kesif") & (t.feat == f) & (t.use == u)].iloc[0]
    st = s[(s.per == "dogrulama") & (s.feat == f) & (s.use == u)].iloc[0]
    tc = tl[(tl.per == "dogrulama") & (tl.feat == f)].iloc[0]; tk = tl[(tl.per == "kesif") & (tl.feat == f)].iloc[0]
    hd = ho.loc[f, "d_FILTRE" if u == "FILTRE" else "d_BOYUT2"]
    c1 = (r.d > 0) and (r.p_maxT <= 0.10)
    c2 = disc.d > 0
    c3 = (st.P >= 0.90) and (st.ex20 > base.ex20)
    c4 = (st.sharpe_w >= base.sharpe_w) and (u != "FILTRE" or st.per_week >= 1.0)
    c5 = (tc.did > 0) and (tc.did_P >= 0.90) and (tk.did > 0)
    c6 = bool(np.isfinite(hd) and hd > 0)
    if c1 and c2 and c3 and c4:
        v = "A" if (c5 and c6) else ("B-sürüklenme" if not c5 else "B")
    elif r.d > 0 and r.p_raw <= 0.10:
        v = "C"
    else:
        v = "RED"
    rows.append(dict(feat=f, name=r["name"], use=u, d_kesif=disc.d, d_dogr=r.d, p_raw=r.p_raw, p_holm=r.p_holm,
                     p_maxT=r.p_maxT, P_strat=st.P, ex20=st.ex20, ex20_taban=base.ex20, sharpe=st.sharpe_w,
                     sharpe_taban=base.sharpe_w, per_week=st.per_week, did_k=tk.did, did_d=tc.did, did_P=tc.did_P,
                     d_kasa=hd, c1=c1, c2=c2, c3=c3, c4=c4, c5=c5, c6=c6, verdikt=v))
v = pd.DataFrame(rows); v.to_csv(os.path.join(RES, "verdicts.csv"), index=False)
pd.set_option("display.width", 250); print(v.round(3).to_string())
