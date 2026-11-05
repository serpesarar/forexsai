from __future__ import annotations
from pathlib import Path
import numpy as np, pandas as pd, yfinance as yf
from zoneinfo import ZoneInfo
ROOT = Path(__file__).resolve().parents[2]
NY = ZoneInfo("America/New_York")
A, Z = pd.Timestamp("2012-01-01", tz=NY), pd.Timestamp("2026-01-01", tz=NY)
def night(sym):
    q = yf.Ticker(sym).history(start="2010-01-01", end="2026-11-05", auto_adjust=False); q.index = q.index.tz_convert(NY).normalize()
    q["n"] = (q.Open.shift(-1) / q.Close - 1) * 1e4; return q
def dates(names, after=True):
    out = {}
    for s in names:
        try:
            x = yf.Ticker(s).get_earnings_dates(limit=100)
        except Exception as e:
            print("yok", s, type(e).__name__); continue
        for ts in x.index:
            l = ts.tz_convert(NY)
            if (l.hour >= 15) == after and (after or l.hour < 10):
                out.setdefault(l.normalize(), set()).add(s)
    return out
Q = night("QQQ"); S = night("SPY")
Qs = Q[(Q.index >= A) & (Q.index < Z)]
core = dates(("AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA"))
core_i = pd.DatetimeIndex(sorted(core)); core_i = core_i[(core_i >= A) & (core_i < Z)]
idx = Qs.index
def stat(v, base=None, lab=""):
    v = v[np.isfinite(v)]; rng = np.random.default_rng(4); o = len(v) // 2
    bs = np.array([rng.choice(v, len(v)).mean() for _ in range(5000)])
    print(f"{lab:38s} n={len(v):4d} ort={v.mean():6.1f} med={np.median(v):6.1f} isabet={(v>0).mean():.3f} P>0={np.mean(bs>0):.3f} P>2bp={np.mean(bs>2):.3f} y1={v[:o].mean():5.1f} y2={v[o:].mean():5.1f}")
pos = idx.searchsorted(core_i); pos = pos[pos < len(idx)]
print("(1) komşu geceler"); 
for k in range(-4, 5):
    p = pos + k; p = p[(p >= 0) & (p < len(idx))]
    stat(Qs.n.to_numpy()[p], lab=f"D{k:+d}")
others = np.setdiff1d(np.arange(len(idx)), pos); stat(Qs.n.to_numpy()[others], lab="bilanço dışı tüm geceler")
near = np.unique(np.concatenate([pos + k for k in (-3, -2, -1, 1, 2, 3)])); near = near[(near >= 0) & (near < len(idx))]; near = np.setdiff1d(near, pos)
stat(Qs.n.to_numpy()[near], lab="komşu ±3 (D hariç)")
print("(2) negatif kontrol: sabah raporcular, gece önce")
am = dates(("JPM", "WMT", "GS", "JNJ", "PG", "KO", "HD", "UNH"), after=False)
am_i = pd.DatetimeIndex(sorted(am)); am_i = am_i[(am_i >= A) & (am_i < Z)]
p2 = idx.searchsorted(am_i) - 1; p2 = p2[p2 >= 0]
p2 = np.setdiff1d(p2, pos); stat(Qs.n.to_numpy()[p2], lab="sabah raporu öncesi gece (QQQ)"); stat(S.n.reindex(idx).to_numpy()[p2], lab="sabah raporu öncesi gece (SPY)")
print("(3) kesit dışı şirketler")
oth = dates(("NFLX", "AVGO", "AMD", "ADBE", "COST", "INTC", "CSCO", "QCOM"))
for s in ("NFLX", "AVGO", "AMD", "ADBE", "COST", "INTC", "CSCO", "QCOM"):
    i = pd.DatetimeIndex(sorted(d for d, v in oth.items() if s in v)); i = i[(i >= A) & (i < Z)]; p = idx.searchsorted(i); p = np.setdiff1d(p[p < len(idx)], pos)
    stat(Qs.n.to_numpy()[p], lab=f"  {s} (çekirdekle çakışmayan)")
all_oth = pd.DatetimeIndex(sorted(oth)); all_oth = all_oth[(all_oth >= A) & (all_oth < Z)]; p = np.setdiff1d(idx.searchsorted(all_oth), pos); p = p[p < len(idx)]
stat(Qs.n.to_numpy()[p], lab="8 şirket toplam")
print("(4) makro çakışması çıkarılınca")
c = pd.read_csv(ROOT / "research/xau_best_days_20261015/makro/out/calendar.csv"); c["d"] = pd.to_datetime(c.date).dt.tz_localize(NY)
mi = idx.searchsorted(pd.DatetimeIndex(c.d)); ms = np.unique(np.concatenate([mi, mi - 1]))
keep = np.setdiff1d(pos, ms); stat(Qs.n.to_numpy()[keep], lab="makro günü/öncesi hariç"); stat(Qs.n.to_numpy()[np.intersect1d(pos, ms)], lab="yalnız makro çakışan")
print("(5) SPY"); stat(S.n.reindex(idx).to_numpy()[pos], lab="SPY aynı geceler"); stat(S.n.reindex(idx).to_numpy()[others], lab="SPY diğer")
print("(7) yıl yıl (QQQ)")
y = pd.Series(Qs.n.to_numpy()[pos], index=idx[pos]); oy = pd.Series(Qs.n.to_numpy()[others], index=idx[others])
print(pd.DataFrame({"n": y.groupby(y.index.year).size(), "ort": y.groupby(y.index.year).mean().round(1), "isabet": y.groupby(y.index.year).apply(lambda s: round((s > 0).mean(), 2)), "diğer": oy.groupby(oy.index.year).mean().round(1)}).T.to_string())
print("(8) plasebo: yıl-eşlemeli rastgele geceler")
rng = np.random.default_rng(8); yrs = idx.year.to_numpy(); per = [np.flatnonzero(yrs == yy) for yy in np.unique(yrs)]; cnt = [(yrs[pos] == yy).sum() for yy in np.unique(yrs)]
pl = np.array([np.nanmean(np.concatenate([Qs.n.to_numpy()[rng.choice(a, c_, replace=False)] for a, c_ in zip(per, cnt)])) for _ in range(5000)])
print("gerçek", round(float(np.nanmean(Qs.n.to_numpy()[pos])), 2), "plasebo ort", round(float(pl.mean()), 2), "p", round(float((pl >= np.nanmean(Qs.n.to_numpy()[pos])).mean()), 4))
print("(6) NDX 1h icra")
z = np.load(ROOT / "backend/data/candle_history/NDX_1h.npz"); d = pd.DataFrame({k: z[k] for k in z.files}); d["dt"] = pd.to_datetime(d.ts.astype("int64"), unit="s", utc=True).dt.tz_convert(NY); d = d.set_index("dt").sort_index()
out = []
for D in core_i:
    if D < pd.Timestamp("2016-06-01", tz=NY): continue
    a_ = D + pd.Timedelta(hours=15); nxt = idx[idx.searchsorted(D) + 1] if idx.searchsorted(D) + 1 < len(idx) else None
    if nxt is None or a_ not in d.index: continue
    b_ = nxt + pd.Timedelta(hours=9)
    if b_ not in d.index: continue
    e, x = d.close.at[a_], d.close.at[b_]
    out.append((D, (x / e - 1) * 1e4 - 3.0 / e * 1e4 - 2.0))
o = pd.DataFrame(out, columns=["d", "r"])
for lab, m in (("2016-2023", o.d < pd.Timestamp("2024-01-01", tz=NY)), ("2024-2025", o.d >= pd.Timestamp("2024-01-01", tz=NY))):
    stat(o.r[m].to_numpy(), lab=f"NDX 1h net {lab}")
