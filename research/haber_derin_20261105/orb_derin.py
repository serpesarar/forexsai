from __future__ import annotations
import sys
from pathlib import Path
import numpy as np, pandas as pd, yfinance as yf
H = Path(__file__).parent; sys.path[:0] = [str(H), str(H.parent / "dts_uyarlama_20261104")]
import ortak as O
import dts02_orb as D
ROOT = H.parents[1]
d = pd.read_parquet(O.DATA / "NDX_1m.parquet"); d = d.assign(ts=pd.to_datetime(d.t, unit="s", utc=True)).set_index("ts")
def rs(rule): return d.resample(rule, label="left", closed="left").agg(open=("open", "first"), high=("high", "max"), low=("low", "min"), close=("close", "last")).dropna().reset_index()
o0, f0 = D.hm("09:30"), D.hm("15:55")
vix = yf.Ticker("^VIX").history(start="2021-01-01", end="2026-11-05")["Close"]; vix.index = vix.index.tz_localize(None).normalize(); vix = vix.shift(1)

def detail(m, idx, mins, orm, bar, sp, side="long", tgt=2.0, entry_mode="break", rng=None, stop="or_mid"):
    """R + bp + risk_bp. entry_mode: break | orend | rand. rand/orend: risk = OR yarı genişliği (aynı geometri)."""
    o, h, l, c = m["o"], m["h"], m["l"], m["c"]
    r_ = [i for i in idx if mins[i] < o0 + orm]
    if len(r_) * bar < orm: return None
    oh, ol = h[r_].max(), l[r_].min(); post = [i for i in idx if mins[i] >= o0 + orm]
    long = side == "long"; k = None
    if entry_mode == "break":
        for p, q in enumerate(post):
            if mins[q] + bar > f0 - D.LAST_ENTRY_MIN: return None
            if (c[q] > oh) if long else (c[q] < ol): k = p; break
        if k is None: return None
    elif entry_mode == "orend":
        k = 0
    else:
        cand = [p for p, q in enumerate(post) if mins[q] + bar <= f0 - D.LAST_ENTRY_MIN]
        if not cand: return None
        k = int(rng.choice(cand))
    rest = post[k + 1:]
    if not rest: return None
    e = o[rest[0]] + sp if long else o[rest[0]] - sp
    if entry_mode == "break":
        st = (oh + ol) / 2; risk = (e - st) if long else (st - e)
    else:
        risk = (oh - ol) / 2 + abs(0.0); st = e - risk if long else e + risk
    if risk <= D.MIN_RISK * e: return None
    tg = e + tgt * risk if long else e - tgt * risk
    res = None
    for j in rest:
        if (l[j] <= st) if long else (h[j] >= st): res = -1.0; break
        if (h[j] >= tg) if long else (l[j] <= tg): res = tgt; break
    if res is None:
        x = c[rest[-1]]; res = ((x - e) if long else (e - x)) / risk
    return res, res * risk / e * 1e4, risk / e * 1e4

def run(df, bar, orm, sp, **kw):
    dd, mins = D.days_of(df, "NDX"); rows = []
    m = {"o": df.open.to_numpy(), "h": df.high.to_numpy(), "l": df.low.to_numpy(), "c": df.close.to_numpy()}
    for dt in sorted(dd):
        z = detail(m, dd[dt], mins, orm, bar, sp, **kw)
        if z: rows.append({"d": pd.Timestamp(dt), "R": z[0], "bp": z[1], "risk": z[2]})
    return pd.DataFrame(rows)
def pr(x, lab):
    if len(x) == 0: print(lab, "boş"); return
    v = x.R.to_numpy(); rng = np.random.default_rng(5); u, inv = np.unique(x.d.dt.to_period("M").astype(str), return_inverse=True); s, n = np.bincount(inv, v), np.bincount(inv); ix = rng.integers(0, len(u), (4000, len(u)))
    P = ((s[ix].sum(1) / n[ix].sum(1)) > 0).mean(); h = len(v) // 2
    print(f"{lab:40s} n={len(v):4d} ortR={v.mean():+.3f} isabet={(v>0).mean():.3f} P={P:.3f} y1={v[:h].mean():+.3f} y2={v[h:].mean():+.3f} | bp/işlem={x.bp.mean():+.2f} risk_bp={x.risk.median():.0f} yıl_bp={x.bp.sum()/max(1,(x.d.max()-x.d.min()).days/365):+.0f}")
m5 = rs("5min")
base = run(m5, 5, 15, 1.3); base["y"] = base.d.dt.year
print("=== ana (5m OR15 or_mid 2R uzun)"); pr(base, "tüm 2024-26")
for y in (2024, 2025, 2026): pr(base[base.y == y], f"  {y}")
print("=== (e) spread"); pr(run(m5, 5, 15, 3.4), "spread 3,4 pt"); pr(run(m5, 5, 15, 2.0), "spread 2,0 pt")
print("=== (c) kısa"); s_ = run(m5, 5, 15, 1.3, side="short"); pr(s_, "kısa")
for y in (2024, 2025, 2026): pr(s_[s_.d.dt.year == y], f"  kısa {y}")
print("=== (b) taban"); rng = np.random.default_rng(1)
oe = run(m5, 5, 15, 1.3, entry_mode="orend"); pr(oe, "OR sonu uzun (kırılım şartsız)")
rd = pd.concat([run(m5, 5, 15, 1.3, entry_mode="rand", rng=rng) for _ in range(10)]); rd = rd.sort_values("d"); pr(rd, "rastgele bar uzun ×10")
g1 = base.groupby("d").R.mean(); g2 = rd.groupby("d").R.mean(); j = pd.concat([g1, g2], axis=1, keys=["a", "b"]).dropna(); dl = (j.a - j.b).to_numpy()
print("  eşleşik fark kırılım−rastgele", round(dl.mean(), 3), "n", len(dl), "P", round(np.mean([rng.choice(dl, len(dl)).mean() > 0 for _ in range(5000)]), 3))
g3 = oe.groupby("d").R.mean(); j = pd.concat([g1, g3], axis=1, keys=["a", "b"]).dropna(); dl = (j.a - j.b).to_numpy(); print("  eşleşik fark kırılım−OR sonu", round(dl.mean(), 3), "P", round(np.mean([rng.choice(dl, len(dl)).mean() > 0 for _ in range(5000)]), 3))
print("=== (d) stop genişliği (risk_bp kovaları)"); base["k"] = pd.qcut(base.risk, 4, labels=False, duplicates="drop"); print(base.groupby("k").agg(n=("R", "size"), R=("R", "mean"), bp=("bp", "mean"), risk=("risk", "median")).round(2).to_string())
print("=== (f) VIX"); base["vix"] = vix.reindex(base.d.dt.normalize().dt.tz_localize(None)).ffill().to_numpy(); print(base.groupby(base.vix >= 18.4).agg(n=("R", "size"), R=("R", "mean"), bp=("bp", "mean")).round(3).to_string())
print("=== (a) ayı: 30m / 15m")
lz = pd.read_parquet(ROOT / "research/ndx_gate_forge/data/long_30m_utc.parquet"); print(lz.columns.tolist()[:8], lz.shape)
tc = "ts" if "ts" in lz else lz.columns[0]
lz["ts"] = pd.to_datetime(lz[tc], utc=True) if str(lz[tc].dtype).startswith("datetime") else pd.to_datetime(lz[tc], unit="s", utc=True)
print(lz.ts.min(), lz.ts.max())
lz = lz.sort_values("ts").reset_index(drop=True)[["ts", "open", "high", "low", "close"]]
b30 = run(lz, 30, 30, 1.3); b30["y"] = b30.d.dt.year
print(b30.groupby("y").agg(n=("R", "size"), R=("R", "mean"), isabet=("R", lambda s: (s > 0).mean()), bp=("bp", "mean")).round(3).to_string())
pr(b30[(b30.d >= "2021-07-01") & (b30.d < "2023-03-01")], "30m OR30 2021-07→2023-02 (ayı dahil)")
z15 = np.load(ROOT / "backend/data/candle_history/NDX_15m.npz"); q = pd.DataFrame({k: z15[k] for k in z15.files}); q["ts"] = pd.to_datetime(q.ts.astype("int64"), unit="s", utc=True); q = q.sort_values("ts").reset_index(drop=True)
b15 = run(q, 15, 15, 1.3); b15["y"] = b15.d.dt.year
print(b15.groupby("y").agg(n=("R", "size"), R=("R", "mean"), isabet=("R", lambda s: (s > 0).mean()), bp=("bp", "mean")).round(3).to_string())
