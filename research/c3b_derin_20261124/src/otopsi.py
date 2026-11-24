"""otopsi.py — C3b Duka 1m işlemlerinin betimleyici otopsisi (ön kayıttan ÖNCE; hüküm yok)."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "research/ndx_10y_1m_20261116/src"))
import lib  # noqa
m1 = lib.load_m1(); D = lib.daily_table(m1)
a = pd.read_parquet(ROOT / "research/ndx_10y_1m_20261116/results/a_trades.parquet")
c = a[a.rule == "C3B"].copy()
s = D[D.S.notna() & D.E.notna() & ~D.early].reset_index(drop=True)
S = s.S.values; r = np.r_[np.nan, S[1:] / S[:-1] - 1]
dvol = pd.Series(r).rolling(20).std().shift(1).values
z5 = (S / np.r_[[np.nan]*5, S[:-5]] - 1) / (dvol * np.sqrt(5))
sma200 = pd.Series(S).rolling(200).mean().values
hi252 = pd.Series(S).rolling(252, min_periods=60).max().values
vixp = lib.vix_prev_map(list(s.d))
ix = {d: i for i, d in enumerate(s.d)}
rows = []
for _, t in c.iterrows():
    i = ix[t.d]
    rows.append(dict(d=t.d, bp=t.net_bp, hold=t.hold, mae=t.mae, z5=z5[i], dvol=dvol[i]*1e4, r1=r[i]*1e4,
                     r5=(S[i]/S[i-5]-1)*1e4, above200=S[i] > sma200[i], dd252=(S[i]/hi252[i]-1)*100, vix=vixp.get(t.d)))
f = pd.DataFrame(rows); f["win"] = f.bp > 0
f["stress"] = (f.r1 <= -150) | (f.r5 <= -400); f["deep"] = f.z5 <= -1.072; f["vix18"] = f.vix >= 18.4
pd.set_option("display.width", 200)
print(f.sort_values("bp").head(18).round(2).to_string())
for k in ["stress", "deep", "vix18", "above200"]:
    print(k, f.groupby(k).bp.agg(["count", "mean", "sum", lambda x: (x > 0).mean(), "min"]).round(1).to_string())
print(f.groupby(["vix18", "deep"]).bp.agg(["count", "mean", "sum", "min"]).round(1))
print(f.groupby(pd.cut(f.dd252, [-50, -15, -8, -4, 0])).bp.agg(["count", "mean", "sum", "min"]).round(1))
f.to_parquet(Path(__file__).resolve().parents[1] / "cache/otopsi.parquet")
