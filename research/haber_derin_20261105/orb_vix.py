from __future__ import annotations
import sys
from pathlib import Path
import numpy as np, pandas as pd
H = Path(__file__).parent; sys.path[:0] = [str(H), str(H.parent / "dts_uyarlama_20261104")]
sys.argv = ["x"]
import importlib.util
src = (H / "orb_derin.py").read_text().split('m5 = rs("5min")')[0]
exec(compile(src, "orb_core", "exec"))
ROOT = H.parents[1]
m5 = rs("5min")
lz = pd.read_parquet(ROOT / "research/ndx_gate_forge/data/long_30m_utc.parquet"); lz["ts"] = pd.to_datetime(lz.ts, utc=True); lz = lz.sort_values("ts").reset_index(drop=True)[["ts", "open", "high", "low", "close"]]
z15 = np.load(ROOT / "backend/data/candle_history/NDX_15m.npz"); q = pd.DataFrame({k: z15[k] for k in z15.files}); q["ts"] = pd.to_datetime(q.ts.astype("int64"), unit="s", utc=True); q = q.sort_values("ts").reset_index(drop=True)
vixf = vix.copy()
def addv(x):
    x = x.copy(); x["vix"] = vixf.reindex(x.d.dt.normalize().dt.tz_localize(None), method="ffill").to_numpy(); x["y"] = x.d.dt.year; return x
sets = {"5m": addv(run(m5, 5, 15, 1.3)), "15m": addv(run(q, 15, 15, 1.3)), "30m": addv(run(lz, 30, 30, 1.3))}
for k, x in sets.items():
    print(f"\n== {k}")
    t = x.assign(hi=x.vix >= 18.4).groupby(["y", "hi"]).agg(n=("R", "size"), R=("R", "mean"), bp=("bp", "mean"), isabet=("R", lambda s: (s > 0).mean())).round(3).unstack("hi")
    print(t.to_string())
    pr(x[x.vix >= 18.4], f"{k} C1 VIX≥18,4 tüm"); pr(x[x.vix < 18.4], f"{k} VIX<18,4 tüm")
    hi, lo = x[x.vix >= 18.4].R.to_numpy(), x[x.vix < 18.4].R.to_numpy(); rng = np.random.default_rng(6)
    print("  fark hi−lo", round(hi.mean() - lo.mean(), 3), "P", round(np.mean([rng.choice(hi, len(hi)).mean() > rng.choice(lo, len(lo)).mean() for _ in range(5000)]), 3))
x = sets["5m"]
pr(x[(x.vix >= 18.4) & (x.y == 2026)], "5m C1 2026"); pr(x[(x.vix >= 18.4) & (x.d >= "2026-07-01")], "5m C1 2026-H2")
y = sets["30m"]; pr(y[(y.vix >= 18.4) & (y.d < "2024-01-01")], "30m C1 2021-23")
print("\neşik duyarlılığı 5m:", {th: (int((x.vix >= th).sum()), round(x[x.vix >= th].R.mean(), 3), round(x[x.vix >= th].bp.mean(), 1)) for th in (15, 18.4, 20, 25)})
print("eşik duyarlılığı 30m:", {th: (int((y.vix >= th).sum()), round(y[y.vix >= th].R.mean(), 3), round(y[y.vix >= th].bp.mean(), 1)) for th in (15, 18.4, 20, 25)})
# tabanlar (5m)
print("\n=== b2/b3 tabanları")
dd, mins = D.days_of(m5, "NDX"); M = {"o": m5.open.to_numpy(), "h": m5.high.to_numpy(), "l": m5.low.to_numpy(), "c": m5.close.to_numpy()}
rng = np.random.default_rng(7)
allr = []
for dt in sorted(dd):
    for _ in range(5):
        z = detail(M, dd[dt], mins, 15, 5, 1.3, entry_mode="rand", rng=rng)
        if z: allr.append((pd.Timestamp(dt), z[0], z[1]))
ar = pd.DataFrame(allr, columns=["d", "R", "bp"]); ar = addv(ar)
def b2(sel, lab):
    n = len(sel); pool = ar.R.to_numpy() if lab == "tüm" else ar[ar.vix >= 18.4].R.to_numpy()
    pl = np.array([rng.choice(pool, n).mean() for _ in range(5000)])
    print(f"b2 {lab}: strateji {sel.R.mean():+.3f} n={n} rastgele-long {pl.mean():+.3f} p={np.mean(pl >= sel.R.mean()):.4f}")
b2(x, "tüm"); b2(x[x.vix >= 18.4], "VIX≥18,4")
# b3: kırılımdan sonraki rastgele bar (o anda bilinen)
def after_break(day_idx):
    r_ = [i for i in day_idx if mins[i] < o0 + 15]
    if len(r_) * 5 < 15: return None
    oh, ol = M["h"][r_].max(), M["l"][r_].min(); post = [i for i in day_idx if mins[i] >= o0 + 15]
    kk = next((p for p, q_ in enumerate(post) if mins[q_] + 5 <= f0 - D.LAST_ENTRY_MIN and M["c"][q_] > oh), None)
    if kk is None: return None
    cand = [p for p, q_ in enumerate(post) if p > kk + 1 and mins[q_] + 5 <= f0 - D.LAST_ENTRY_MIN]
    if not cand: return None
    p = int(rng.choice(cand)); rest = post[p + 1:]
    if not rest: return None
    e = M["o"][rest[0]] + 1.3; risk = (oh - ol) / 2; st, tg = e - risk, e + 2 * risk
    if risk <= D.MIN_RISK * e: return None
    for j in rest:
        if M["l"][j] <= st: return -1.0
        if M["h"][j] >= tg: return 2.0
    return (M["c"][rest[-1]] - e) / risk
b3 = []
for dt in sorted(dd):
    for _ in range(5):
        v = after_break(dd[dt])
        if v is not None: b3.append((pd.Timestamp(dt), v))
b3 = pd.DataFrame(b3, columns=["d", "R"]); print("b3 kırılım sonrası rastgele bar uzun", round(b3.R.mean(), 3), "n", len(b3))
g = pd.concat([x.groupby("d").R.mean(), b3.groupby("d").R.mean()], axis=1, keys=["a", "b"]).dropna(); dl = (g.a - g.b).to_numpy(); print("  eşleşik a−b", round(dl.mean(), 3), "P", round(np.mean([rng.choice(dl, len(dl)).mean() > 0 for _ in range(5000)]), 3), "n", len(dl))
