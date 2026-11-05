"""Broker barlarıyla çok sembollü gün tablosu ve hücre koşucusu."""
from __future__ import annotations
import numpy as np, pandas as pd, yfinance as yf
from lab import *
SP = {"NAS100": 1.3, "XAUUSD": 0.25, "SpotCrude": 0.03}
def _iv():
    p = HERE / "results/iv.parquet"
    if p.exists(): return pd.read_parquet(p)
    def g(t):
        s = yf.Ticker(t).history(start="2015-01-01", end="2026-11-06")["Close"]; s.index = s.index.tz_localize(None).normalize(); return s
    m = pd.DataFrame({"gvz": g("^GVZ"), "ovx": g("^OVX"), "vxn": g("^VXN")}); m.to_parquet(p); return m
IV = _iv()
IVK = {"NAS100": "vxn", "XAUUSD": "gvz", "SpotCrude": "ovx", "GER40": "vxn"}
def build2(sym: str, tf: str, o0: int, f0: int, a=None, b=None) -> list[Day]:
    x = mt5_bars(sym, tf)
    if a: x = x[x.ts_et >= a]
    if b: x = x[x.ts_et < b]
    m_ = (x.ts_et.dt.hour * 60 + x.ts_et.dt.minute).to_numpy(); dt = x.ts_et.dt.date.to_numpy()
    o, h, l, c = (x[k].to_numpy(float) for k in "ohlc")
    by = {}
    for i, dd in enumerate(dt): by.setdefault(dd, []).append(i)
    iv = IV[IVK[sym]].dropna(); ivm = iv.rolling(252, min_periods=120).median()
    out, closes, rets = [], [], []
    for dd in sorted(by):
        if pd.Timestamp(dd).dayofweek >= 5: continue
        ix = np.array(by[dd]); m = m_[ix]; r = ix[(m >= o0) & (m < f0)]
        if len(r) == 0: continue
        pc = closes[-1] if closes else np.nan; ppc = closes[-2] if len(closes) > 1 else np.nan; c5 = closes[-5] if len(closes) >= 5 else np.nan
        key = pd.Timestamp(dd); pv = MAC[MAC.index < key]; v1 = pv.iloc[-1] if len(pv) else None; v2 = pv.iloc[-2] if len(pv) > 1 else None
        i1 = iv[iv.index < key]; im = ivm[ivm.index < key]
        f = {"vix": v1.vix if v1 is not None else np.nan, "vixchg": (v1.vix - v2.vix) if v2 is not None else np.nan, "vix3m": v1.vix3m if v1 is not None else np.nan, "vvix": np.nan,
             "gap": (o[r[0]] / pc - 1) * 1e4 if pc == pc else np.nan, "r1": (pc / ppc - 1) * 1e4 if ppc == ppc else np.nan, "r5": (pc / c5 - 1) * 1e4 if c5 == c5 else np.nan,
             "rv20": float(np.std(rets[-20:]) * 1e4) if len(rets) >= 20 else np.nan, "dow": key.dayofweek, "data": dd in CAL_DAYS, "y": dd.year,
             "rv_q": float(pd.Series(rets[-250:]).rolling(20).std().rank(pct=True).iloc[-1]) if len(rets) >= 40 else np.nan,
             "iv": float(i1.iloc[-1]) if len(i1) else np.nan, "ivm": float(im.iloc[-1]) if len(im) and im.iloc[-1] == im.iloc[-1] else np.nan}
        out.append(Day(dd, m, o[ix], h[ix], l[ix], c[ix], f)); closes.append(c[r[-1]])
        if pc == pc: rets.append(c[r[-1]] / pc - 1)
    return out
FLT2 = dict(FILTERS); FLT2.update({"iv yüksek": lambda f: f["iv"] >= f["ivm"], "iv düşük": lambda f: f["iv"] < f["ivm"], "iv yüksek∧dün−": lambda f: f["iv"] >= f["ivm"] and f["r1"] < 0, "iv yüksek∧dün+": lambda f: f["iv"] >= f["ivm"] and f["r1"] > 0, "iv düşük∧dün−": lambda f: f["iv"] < f["ivm"] and f["r1"] < 0, "iv düşük∧dün+": lambda f: f["iv"] < f["ivm"] and f["r1"] > 0})
def brk(day, bar, orlen, side, a0, last, end, sp, tgt=2.0, stopk="mid", fade=False):
    z = or_of(day, a0, orlen, bar)
    if not z: return None
    oh, ol, ie = z
    for i in range(ie + 1, len(day.o)):
        if day.m[i] + bar > last: return None
        if (day.c[i] > oh) if side > 0 else (day.c[i] < ol):
            if not fade:
                st = (oh + ol) / 2 if stopk == "mid" else (ol if side > 0 else oh)
                return sim(day, i + 1, side, st, tgt, end, sp)
            s2 = -side; w = (oh - ol) / 2 if stopk == "mid" else (oh - ol)
            return sim(day, i + 1, s2, (day.c[i] + w) if s2 < 0 else (day.c[i] - w), tgt, end, sp)
    return None
def reclaim(day, bar, orlen, side, a0, last, end, sp, tgt=2.0, within=4):
    z = or_of(day, a0, orlen, bar)
    if not z: return None
    oh, ol, ie = z; n = len(day.o)
    for i in range(ie + 1, n):
        if day.m[i] + bar > last: return None
        if (day.c[i] < ol) if side > 0 else (day.c[i] > oh):
            for k in range(i + 1, min(i + 1 + within, n)):
                if day.m[k] + bar > last: return None
                if (day.c[k] > ol) if side > 0 else (day.c[k] < oh):
                    st = day.l[i:k + 1].min() if side > 0 else day.h[i:k + 1].max()
                    return sim(day, k + 1, side, st, tgt, end, sp)
            return None
    return None
def evalset(days, fn, fl):
    rows = []
    for d in days:
        try:
            if not bool(fl(d.f)): continue
        except Exception:
            continue
        z = fn(d)
        if z: rows.append((str(d.d), z[0], z[1], z[2]))
    return metrics(rows), rows
