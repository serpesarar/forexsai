"""D1–D4 teşhis, HB-01 verisiyle (2026-03-09→05-20, broker 1m, eksen düzeltilmiş). İşlem yok; yalnız |getiri| zamanlaması."""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "backend"), str(ROOT / "research/haber_olay_20261105")]
import ortak as H
from services.newsfeed.classifier import classify
from services.newsfeed.dedup import tokens

SYMS = {"NDX": "NDX.INDX", "GDAXI": "GDAXI.INDX", "XAUUSD": "XAUUSD", "USOIL": "USOIL.FOREX"}
LAGS = np.arange(-30, 31)

def bars(sym):
    d = H.load_bars(sym); d = d[(d.ts >= H.START) & (d.ts < H.END)].copy()
    d["min"] = d.ts.dt.floor("min"); d["r"] = np.log(d.c).diff().abs() * 1e4
    d.loc[d.ts.diff().dt.total_seconds() > 300, "r"] = np.nan   # açılış boşluğu haber etkisi sayılmaz
    x = d.set_index("min")["r"].dropna()
    base = x.groupby([x.index.dayofweek, x.index.hour, x.index.minute]).transform("median")
    # gün×saat×dakika tek gözlem azdır: saat×dakika medyanı kullanılır
    base = x.groupby([x.index.hour, x.index.minute]).transform("median")
    return x, x / base.replace(0, np.nan)

def curve(ratio, ts):
    """Olay kilitli medyan yerine ortalama |r|/olağan; t=0 başlığın düştüğü dakika."""
    idx = ratio.index
    fl = ts.dt.floor("min")
    pos = idx.searchsorted(fl); pos = np.minimum(pos, len(idx) - 1)
    exact = idx[pos] == pd.DatetimeIndex(fl)
    pos = pos[exact]
    vals = ratio.to_numpy(); out = {}
    for lag in LAGS:
        p = pos + lag; ok = (p >= 0) & (p < len(vals))
        out[lag] = np.nanmean(vals[p[ok]])
    return pd.Series(out)

n = H.load_news()
n = n[(n.ts_pub >= H.START) & (n.ts_pub < H.END) & (n.delay.abs() <= 600)].copy()
print("başlık", len(n), "kaynak", n.source.nunique() if "source" in n else None, list(n.columns)[:14])
n = n.sort_values("ts_pub").reset_index(drop=True)
txt = n["headline"].fillna("").astype(str)
cl = [classify(t, "squawk") for t in txt]
n["etype"] = [c.event_type for c in cl]; n["rel"] = [c.relevance for c in cl]; n["syms"] = [c.symbols for c in cl]; n["op"] = [c.is_opinion for c in cl]
# D4 yenilik: son 24 sa başlıklarıyla token kapsama ≥0,6 → tekrar
seen, novel = [], []
times = n.ts_pub.astype("int64").to_numpy() // 10**9
from collections import deque, defaultdict
win = deque(); inv = defaultdict(set)
for i, t in enumerate(txt):
    tk = set(tokens(t))
    while win and times[i] - win[0][0] > 86400:
        _, j, tj = win.popleft()
        for w in tj: inv[w].discard(j)
    cnt = defaultdict(int)
    for w in tk:
        for j in inv.get(w, ()): cnt[j] += 1
    best = max(cnt.values()) / max(1, len(tk)) if cnt else 0.0
    novel.append(best < 0.6)
    win.append((times[i], i, tk))
    for w in tk: inv[w].add(i)
n["novel"] = novel
print("yeni pay", round(n.novel.mean(), 3))

cal = pd.read_csv(ROOT / "research/xau_best_days_20261015/makro/out/calendar.csv")
cal["ts"] = pd.to_datetime(cal.ts_utc, utc=True)
cal = cal[(cal.ts >= H.START) & (cal.ts < H.END)]
print("takvim", cal.event.value_counts().to_dict())
rows = []
for sym, name in SYMS.items():
    x, ratio = bars(sym)
    print(f"\n== {sym} bar {len(x)}")
    c = curve(ratio, cal.ts)
    print("D1 takvim t=0..+3:", c.loc[0:3].round(2).to_dict(), "t=-3..-1:", c.loc[-3:-1].round(2).to_dict())
    rel = n[n.syms.map(lambda s: name in s) & ~n.op]
    groups = {
        "tüm ilgili": rel,
        "ilgi≥75": rel[rel.rel >= 75],
        "yeni ilgi≥75": rel[(rel.rel >= 75) & rel.novel],
        "tekrar ilgi≥75": rel[(rel.rel >= 75) & ~rel.novel],
        "yeni, takvim dışı": rel[(rel.rel >= 75) & rel.novel & ~rel.etype.isin(["macro_print", "cb_decision"])],
    }
    for g, sub in groups.items():
        if len(sub) < 20: continue
        cu = curve(ratio, sub.ts_pub)
        # plasebo: aynı saat-dakika, rastgele ±1..4 hafta kaydırma; 200 çekiliş
        rng = np.random.default_rng(5)
        pc = []
        for _ in range(60):
            off = pd.to_timedelta(rng.integers(1, 5, len(sub)) * rng.choice([-1, 1], len(sub)) * 7, unit="D")
            pc.append(curve(ratio, pd.Series(sub.ts_pub.values, dtype="datetime64[ns, UTC]") + off))
        pc = pd.concat(pc, axis=1); cu = cu / pc.mean(axis=1)
        rows.append({"sym": sym, "grup": g, "n": len(sub), "önce_-30_-6": round(cu.loc[-30:-6].mean(), 3), "-5_-1": round(cu.loc[-5:-1].mean(), 3), "0": round(cu.loc[0], 3), "+1_+5": round(cu.loc[1:5].mean(), 3), "+6_+30": round(cu.loc[6:30].mean(), 3), "tepe_lag": int(cu.idxmax())})
    # D3 ters sorgu
    r5 = x.rolling(5).sum()
    med = r5.groupby(r5.index.hour).transform("median")
    shock = (r5 / med >= 4)
    t_cal = cal.ts.astype("int64").to_numpy() // 10**9
    last = None; onset = []
    for ts in shock[shock].index:
        if last is not None and (ts - last).total_seconds() < 1800: continue
        if len(t_cal) and (np.abs(t_cal - int(ts.timestamp())) <= 1200).any(): continue
        last = ts; w = x.loc[ts - pd.Timedelta(minutes=5):ts]
        k = w[w >= med.loc[ts] * 0.4]
        onset.append(k.index[0] if len(k) else ts)
    hl = rel[(rel.rel >= 75) & rel.novel].ts_pub.astype("int64").to_numpy() // 10**9
    def delays(on):
        out = []
        for o in on:
            s = int(pd.Timestamp(o).timestamp())
            j = np.searchsorted(hl, s - 3600)
            cand = hl[j:np.searchsorted(hl, s + 1800)]
            out.append(np.nan if len(cand) == 0 else cand[np.argmin(np.abs(cand - s))] - s)
        return np.array(out, float)
    dl = delays(onset)
    rng = np.random.default_rng(3); all_idx = x.index
    pl = delays(all_idx[rng.integers(0, len(all_idx), 3000)])
    def prof(a):
        a = a[np.isfinite(a)] if len(a) else a
        tot = len(a)
        return {"önce>5dk": (a < -300).mean(), "-5..-1dk": ((a >= -300) & (a < -60)).mean(), "±1dk": (np.abs(a) <= 60).mean(), "+1..5dk": ((a > 60) & (a <= 300)).mean(), "+5..30dk": (a > 300).mean(), "n": tot}
    print("D3 şok", len(onset), "en yakın başlık(≤±): gerçek", {k: round(v, 3) for k, v in prof(dl).items()})
    print("D3 plasebo               ", {k: round(v, 3) for k, v in prof(pl).items()})
print(); print(pd.DataFrame(rows).to_string(index=False))
