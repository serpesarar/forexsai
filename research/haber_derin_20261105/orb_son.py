from __future__ import annotations
import sys
from pathlib import Path
import numpy as np, pandas as pd
H = Path(__file__).parent; sys.path[:0] = [str(H), str(H.parent / "dts_uyarlama_20261104")]
src = (H / "orb_derin.py").read_text().split('m5 = rs("5min")')[0]
exec(compile(src, "orb_core", "exec"))
ROOT = H.parents[1]; TH = 18.4
vfull = yf.Ticker("^VIX").history(start="2015-01-01", end="2026-11-05")["Close"]; vfull.index = vfull.index.tz_localize(None).normalize(); vfull = vfull.shift(1)
def addv(x):
    x = x.copy(); x["vix"] = vfull.reindex(x.d.dt.normalize().dt.tz_localize(None), method="ffill").to_numpy(); x["y"] = x.d.dt.year; return x
m5 = addv(run(rs("5min"), 5, 15, 1.3))
lz = pd.read_parquet(ROOT / "research/ndx_gate_forge/data/long_30m_utc.parquet"); lz["ts"] = pd.to_datetime(lz.ts, utc=True); lz = lz.sort_values("ts").reset_index(drop=True)[["ts", "open", "high", "low", "close"]]
m30 = addv(run(lz, 30, 30, 1.3)); m30 = m30[m30.d < "2024-01-01"]
z = np.load(ROOT / "backend/data/candle_history/NDX_1h.npz"); q = pd.DataFrame({k: z[k] for k in z.files}); q["ts"] = pd.to_datetime(q.ts.astype("int64"), unit="s", utc=True); q = q.sort_values("ts").reset_index(drop=True)
q = q[(q.ts >= "2016-06-01") & (q.ts < "2021-06-29")].reset_index(drop=True)
o0 = D.hm("10:00"); m60 = addv(run(q, 60, 60, 1.3)); o0 = D.hm("09:30")
P = pd.concat([m60.assign(tf="1h"), m30.assign(tf="30m"), m5.assign(tf="5m")]).sort_values("d").reset_index(drop=True); P["ay"] = P.d.dt.to_period("M").astype(str)
hi = P[P.vix >= TH]; lo = P[P.vix < TH]
pr(hi, "10 YIL C1 havuz"); pr(lo, "10 YIL VIX<18,4 havuz")
print(hi.groupby("y").agg(n=("R", "size"), R=("R", "mean"), bp=("bp", "mean")).round(3).T.to_string())
rng = np.random.default_rng(10)
# VIX etiket karıştırma: ay blokları içinde değil, yıl içinde gün etiketi karıştır (rejim yılını korur)
obs = hi.R.mean() - lo.R.mean(); diffs = []
for _ in range(5000):
    lab = P.groupby("y")["vix"].transform(lambda s: rng.permutation(s.to_numpy()))
    diffs.append(P.R[lab >= TH].mean() - P.R[lab < TH].mean())
print("fark hi-lo", round(obs, 3), "yıl-içi etiket permütasyon p", round(float((np.array(diffs) >= obs).mean()), 4))
# eşik plasebosu: yanlış değişken: 5 gün önceki VIX ile aynı oran ve rastgele kaydırma
for lag in (0, 20, 60, 120, 250):
    vv = P.vix.shift(lag) if lag else P.vix
    print("  vix kaydırma", lag, "hi R", round(P.R[vv >= TH].mean(), 3), "lo R", round(P.R[vv < TH].mean(), 3))
# aktarım: DAX 15m (OR15, 09:00 Berlin)
dx = pd.read_parquet(ROOT / "research/ndx_gate_forge/data/dax_15m.parquet"); dx["ts"] = pd.to_datetime(dx.ts, utc=True); dx = dx.sort_values("ts").reset_index(drop=True)
dd, mi = D.days_of(dx, "GDAXI"); oo, ff = D.hm("09:00"), D.hm("17:25"); arr = {"o": dx.open.to_numpy(), "h": dx.high.to_numpy(), "l": dx.low.to_numpy(), "c": dx.close.to_numpy()}
o0, f0 = oo, ff; rows = []
for dt in sorted(dd):
    zz = detail(arr, dd[dt], mi, 15, 15, 1.5)
    if zz: rows.append({"d": pd.Timestamp(dt), "R": zz[0], "bp": zz[1], "risk": zz[2]})
o0, f0 = D.hm("09:30"), D.hm("15:55")
dx_ = addv(pd.DataFrame(rows)); pr(dx_[dx_.vix >= TH], "DAX 15m VIX≥18,4"); pr(dx_[dx_.vix < TH], "DAX 15m VIX<18,4")
print(dx_.assign(hi=dx_.vix >= TH).groupby(["y", "hi"]).R.agg(["size", "mean"]).round(3).unstack("hi").to_string())
# son sinyaller + giriş saati dağılımı
m = m5[m5.vix >= TH]; print("risk puan medyan", "yaklaşık", round(float((m.risk / 1e4 * 27000).median()), 1), "isabet", round((m.R > 0).mean(), 3), "TP oranı", round((m.R >= 1.99).mean(), 3), "SL oranı", round((m.R <= -0.999).mean(), 3), "zaman çıkışı", round(((m.R > -0.999) & (m.R < 1.99)).mean(), 3))
m[["d", "R", "bp", "risk", "vix"]].to_csv(H / "results_c1_islemler_5m.csv", index=False)
P[["d", "tf", "R", "bp", "risk", "vix"]].to_csv(H / "results_havuz_10yil.csv", index=False)
