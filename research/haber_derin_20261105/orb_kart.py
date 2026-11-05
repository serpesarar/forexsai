from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
H = Path(__file__).parent; sys.path[:0] = [str(H), str(H.parent / "dts_uyarlama_20261104")]
src = (H / "orb_derin.py").read_text().split('m5 = rs("5min")')[0]
exec(compile(src, "orb_core", "exec"))
ROOT = H.parents[1]; TH = 18.4
vfull = yf.Ticker("^VIX").history(start="2015-01-01", end="2026-11-05")["Close"]; vfull.index = vfull.index.tz_localize(None).normalize(); vfull = vfull.shift(1)
def addv(x):
    x = x.copy(); x["vix"] = vfull.reindex(x.d.dt.normalize().dt.tz_localize(None), method="ffill").to_numpy(); x["y"] = x.d.dt.year; return x
m5 = rs("5min"); M = addv(run(m5, 5, 15, 1.3)); C = M[M.vix >= TH].sort_values("d")
print("=== (i) KART"); v = C.R.to_numpy(); h = len(v) // 2; rng = np.random.default_rng(2)
u, inv = np.unique(C.d.dt.to_period("M").astype(str), return_inverse=True); s, n_ = np.bincount(inv, v), np.bincount(inv); ix = rng.integers(0, len(u), (10000, len(u))); P = float(((s[ix].sum(1) / n_[ix].sum(1)) > 0).mean())
st = addv(run(m5, 5, 15, 1.3 * 1.5)); st = st[st.vix >= TH]; st34 = addv(run(m5, 5, 15, 3.4)); st34 = st34[st34.vix >= TH]
# iyimser: giriş kırılım barı KAPANIŞI, spread yok
def optim(df, bar, orm):
    dd, mins = D.days_of(df, "NDX"); o, hh, l, c = df.open.to_numpy(), df.high.to_numpy(), df.low.to_numpy(), df.close.to_numpy(); rows = []
    for dt in sorted(dd):
        r = D.trade(df, dd[dt], mins, o0, f0, orm, bar, "or_mid", 2.0, "long", 0.0, True)
        if r is not None: rows.append({"d": pd.Timestamp(dt), "R": r})
    return pd.DataFrame(rows)
D.ATR = D.atr14(m5); op = addv(optim(m5, 5, 15)); op = op[op.vix >= TH]
ort, iy = v.mean(), op.R.mean()
card = {"scope": "NDX_ORB_VIX", "n": int(len(v)), "ort_R": round(float(ort), 3), "P_EV": round(P, 3), "isabet": round(float((v > 0).mean()), 3), "yari1": round(float(v[:h].mean()), 3), "yari2": round(float(v[h:].mean()), 3),
        "stres_spread_x1_5": round(float(st.R.mean()), 3), "stres_spread_3_4pt": round(float(st34.R.mean()), 3), "iyimser_R": round(float(iy), 3), "icra_farki": round(float(iy - ort), 3), "icra_ort_yarisi_alti": bool(iy - ort <= ort / 2),
        "sira_bagimli": "günde ≤1 işlem; aynı anda tek pozisyon yapısal", "sira_R": round(float(ort), 3), "bp_islem": round(float(C.bp.mean()), 2)}
gec = [card["n"] >= 150, card["ort_R"] > 0 and P >= .9, card["yari1"] >= 0 and card["yari2"] >= 0, card["stres_spread_x1_5"] > 0, card["icra_ort_yarisi_alti"], True]
card["olcutler"] = gec; print(json.dumps(card, ensure_ascii=False, indent=0))
print("=== (v) yol"); eq = C.R.cumsum().to_numpy(); dd_ = (eq - np.maximum.accumulate(eq)).min(); seq = 0; worst = 0
for x in v:
    seq = seq + 1 if x < 0 else 0; worst = max(worst, seq)
print("toplam R", round(v.sum(), 1), "en büyük düşüş R", round(dd_, 1), "en uzun kayıp serisi", worst, "yıl başına işlem", C.groupby("y").size().to_dict(), "ay pozitif oranı", round(float((C.groupby(C.d.dt.to_period('M')).R.sum() > 0).mean()), 3))
print(C.groupby(C.d.dt.to_period("Q")).R.agg(["size", "sum"]).round(1).T.to_string())
print("=== (ii) 1h 2016-06→2021-06")
z = np.load(ROOT / "backend/data/candle_history/NDX_1h.npz"); q = pd.DataFrame({k: z[k] for k in z.files}); q["ts"] = pd.to_datetime(q.ts.astype("int64"), unit="s", utc=True); q = q.sort_values("ts").reset_index(drop=True)
q = q[(q.ts >= "2016-06-01") & (q.ts < "2021-06-30")].reset_index(drop=True)
print("bar saatleri ET", q.ts.dt.tz_convert("America/New_York").dt.hour.value_counts().sort_index().loc[8:12].to_dict(), "dakika", q.ts.dt.minute.value_counts().to_dict())
o0 = D.hm("10:00"); h1 = addv(run(q, 60, 60, 1.3)); o0 = D.hm("09:30")
print(h1.assign(hi=h1.vix >= TH).groupby(["y", "hi"]).agg(n=("R", "size"), R=("R", "mean"), bp=("bp", "mean")).round(3).unstack("hi").to_string())
pr(h1[h1.vix >= TH], "1h C1 2016-21"); pr(h1[h1.vix < TH], "1h VIX<18,4 2016-21")
print("=== (iii) broker verisi 2026")
b = pd.read_parquet(ROOT / "research/ndx_19puan_20261030/data/bars_used.parquet"); b = b[b.ts >= "2026-02-08"].set_index("ts")
for src_ in (("MT5",), ("MT5", "snapshot", "cache_early", "cache_tail")):
    bb = b[b.source.isin(src_)]
    r5 = bb.resample("5min", label="left", closed="left").agg(open=("open", "first"), high=("high", "max"), low=("low", "min"), close=("close", "last")).dropna().reset_index()
    x = addv(run(r5, 5, 15, 1.3)); pr(x[x.vix >= TH], f"broker/önbellek {src_[0]}+{len(src_)-1} C1"); pr(x[x.vix < TH], "   VIX<18,4")
dk = M[M.d >= "2026-02-08"]; pr(dk[dk.vix >= TH], "Dukascopy aynı dönem C1")
print("=== (iv) aktarım DAX/SPX-benzeri")
dx = pd.read_parquet(ROOT / "research/ndx_gate_forge/data/dax_15m.parquet"); print(dx.columns.tolist()[:6], dx.shape)
