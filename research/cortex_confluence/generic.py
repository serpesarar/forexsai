"""Generic confluence discovery — run the NASDAQ pipeline on any intraday
instrument (gold, DAX, ...). Same causal features, same leak-safe forward target,
same LONG/SHORT combo search. Decision points are bars-of-day; horizons are
bar-offsets (weekend-gap-safe). Chronological train/test split.
"""
from __future__ import annotations

import sys
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[2] / "backend"))
from services.cortex_backfill import load_dxy_daily, load_us10y_daily  # noqa: E402


# ── Causal indicators (self-contained; identical to the NASDAQ study) ─────────
def _rsi(close, n=14):
    d = close.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))


def _adx(h, l, c, n=14):
    up = h.diff(); dn = -l.diff()
    plus = np.where((up > dn) & (up > 0), up, 0.0)
    minus = np.where((dn > up) & (dn > 0), dn, 0.0)
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1 / n, adjust=False).mean()
    pdi = 100 * pd.Series(plus, index=h.index).ewm(alpha=1 / n, adjust=False).mean() / atr
    mdi = 100 * pd.Series(minus, index=h.index).ewm(alpha=1 / n, adjust=False).mean() / atr
    dx = 100 * (pdi - mdi).abs() / (pdi + mdi).replace(0, np.nan)
    return dx.ewm(alpha=1 / n, adjust=False).mean()


def tf_features(bars, tf):
    c, h, l, v = bars["Close"], bars["High"], bars["Low"], bars["Volume"]
    ema12, ema26 = c.ewm(span=12).mean(), c.ewm(span=26).mean()
    ema20, ema50 = c.ewm(span=20).mean(), c.ewm(span=50).mean()
    macd = ema12 - ema26
    sma20, std20 = c.rolling(20).mean(), c.rolling(20).std()
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1 / 14, adjust=False).mean()
    ret = c.pct_change()
    out = pd.DataFrame(index=bars.index)
    out[f"ret1_{tf}"] = ret
    out[f"ret3_{tf}"] = c.pct_change(3)
    out[f"ret6_{tf}"] = c.pct_change(6)
    out[f"px_ema20_{tf}"] = c / ema20 - 1
    out[f"ema20_50_{tf}"] = ema20 / ema50 - 1
    out[f"ema20_slope_{tf}"] = ema20.pct_change(3)
    out[f"rsi_{tf}"] = _rsi(c)
    out[f"macd_hist_{tf}"] = (macd - macd.ewm(span=9).mean()) / c
    out[f"atr_{tf}"] = atr / c
    out[f"boll_z_{tf}"] = (c - sma20) / std20.replace(0, np.nan)
    out[f"adx_{tf}"] = _adx(h, l, c)
    out[f"vol_ratio_{tf}"] = v / v.rolling(20).mean().replace(0, np.nan)
    out[f"rvol_{tf}"] = ret.rolling(20).std()
    return out

M30_PER = {"3h": 6, "6h": 12, "24h": 48}     # bar offsets on the M30 series
DEC_HOURS = [8, 10, 13, 15]                   # candidate decision hours (file clock)
FLAT = {"3h": 0.08, "6h": 0.12, "24h": 0.20}  # % flat bands (gold-scale ~ ok)


def load_m30(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]
    tc = next(c for c in df.columns if "time" in c or "date" in c)
    df["dt"] = pd.to_datetime(df[tc], errors="coerce")
    df = df.dropna(subset=["dt"]).sort_values("dt")
    keep = {"open": "Open", "high": "High", "low": "Low", "close": "Close",
            "volume": "Volume", "tick_volume": "Volume"}
    ren = {k: v for k, v in keep.items() if k in df.columns}
    out = df.set_index("dt")[list(ren)].rename(columns=ren)
    if "Volume" not in out:
        out["Volume"] = 1.0
    return out[~out.index.duplicated(keep="last")]


def _panels(m30: pd.DataFrame) -> pd.DataFrame:
    agg = {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}
    feat = tf_features(m30, "M30")
    for tf, rule in (("H1", "1h"), ("H4", "4h")):
        bars = m30.resample(rule, label="right", closed="right").agg(agg).dropna()
        f = tf_features(bars, tf)
        feat = feat.join(f.reindex(feat.index, method="ffill"))   # causal ffill
    return feat


def _enrich(d: pd.DataFrame) -> pd.DataFrame:
    def gt0(c): return (d[c] > 0).astype(int) if c in d else 0
    d["trend_agree"] = gt0("ema20_50_M30") + gt0("ema20_50_H1") + gt0("ema20_50_H4")
    d["mom_agree"] = gt0("macd_hist_M30") + gt0("macd_hist_H1") + gt0("macd_hist_H4")
    d["px_agree"] = gt0("px_ema20_M30") + gt0("px_ema20_H1") + gt0("px_ema20_H4")
    d["rsi_agree"] = ((d.get("rsi_M30", 50) > 50).astype(int)
                      + (d.get("rsi_H1", 50) > 50).astype(int)
                      + (d.get("rsi_H4", 50) > 50).astype(int))
    d["bull_score"] = d["trend_agree"] + d["mom_agree"] + d["px_agree"] + d["rsi_agree"]
    d["rsi_spread"] = d.get("rsi_M30", 50) - d.get("rsi_H4", 50)
    return d


def build(m30_path: str, add_macro: bool = True) -> pd.DataFrame:
    m30 = load_m30(m30_path)
    feat = _enrich(_panels(m30))
    close = m30["Close"]
    pos = {ts: i for i, ts in enumerate(close.index)}
    carr = close.values
    rows = []
    for ts in feat.index:
        if ts.hour not in DEC_HOURS or ts.minute != 0:
            continue
        i = pos.get(ts)
        if i is None:
            continue
        row = feat.loc[ts].to_dict()
        row["date"] = ts.date().isoformat()
        row["dec_hour"] = ts.hour
        # forward outcomes (bar offsets)
        for hz, n in M30_PER.items():
            if i + n < len(carr) and carr[i] > 0:
                ch = (carr[i + n] - carr[i]) / carr[i] * 100
                row[f"y_{hz}"] = 1 if ch > FLAT[hz] else 0 if ch < -FLAT[hz] else np.nan
            else:
                row[f"y_{hz}"] = np.nan
        # prior-bar overnight/momentum context
        row["overnight_change"] = (carr[i] / carr[i - 16] - 1) * 100 if i >= 16 else np.nan
        rows.append(row)
    df = pd.DataFrame(rows)
    if add_macro:
        for name, load in (("dxy_chg", load_dxy_daily), ("us10y_chg", load_us10y_daily)):
            try:
                s = load()
                lag = {d.isoformat(): None for d in s.index}
                vals = s.values
                keys = [d.isoformat() for d in s.index]
                m = {}
                for j in range(1, len(keys)):
                    if vals[j - 1]:
                        m[keys[j]] = (vals[j] - vals[j - 1]) / vals[j - 1] * 100
                df[name] = df["date"].map(m)
            except Exception:
                df[name] = np.nan
    return df


# ── combo search (LONG + SHORT) ───────────────────────────────────────────────
def _cond_pool(kind: str):
    def gt(f, q):
        c = lambda x, tr: x[f] > tr[f].quantile(q); c.name = f"{f}>q{int(q*100)}"; return c
    def lt(f, q):
        c = lambda x, tr: x[f] < tr[f].quantile(q); c.name = f"{f}<q{int(q*100)}"; return c
    def ge(f, v):
        c = lambda x, tr: x[f] >= v; c.name = f"{f}≥{v}"; return c
    def le(f, v):
        c = lambda x, tr: x[f] <= v; c.name = f"{f}≤{v}"; return c
    if kind == "long":
        return [ge("bull_score", 11), ge("mom_agree", 3), ge("trend_agree", 3),
                gt("rsi_M30", 0.85), gt("px_ema20_M30", 0.8), gt("adx_H1", 0.7),
                gt("boll_z_M30", 0.8), gt("overnight_change", 0.75), gt("rsi_spread", 0.7),
                lt("dxy_chg", 0.3)]
    return [le("bull_score", 2), le("mom_agree", 0), le("trend_agree", 0),
            lt("rsi_M30", 0.15), lt("px_ema20_M30", 0.2), lt("boll_z_M30", 0.2),
            lt("overnight_change", 0.2), lt("ret6_M30", 0.25), lt("macd_hist_M30", 0.25),
            gt("dxy_chg", 0.7)]


def search(df: pd.DataFrame, split_date: str, target=0.68) -> dict:
    feats_ex = ("date", "dec_hour", "y_3h", "y_6h", "y_24h")
    res = {"long": [], "short": []}
    for side in ("long", "short"):
        pool = _cond_pool(side)
        for dh in DEC_HOURS:
            for hz in ("3h", "6h", "24h"):
                Y = f"y_{hz}"
                d = df[(df["dec_hour"] == dh)].dropna(subset=[Y]).replace([np.inf, -np.inf], np.nan)
                tr, te = d[d["date"] <= split_date], d[d["date"] > split_date]
                if len(tr) < 200 or len(te) < 150:
                    continue
                for r in (2, 3):
                    for cc in combinations(pool, r):
                        def mask(x):
                            m = pd.Series(True, index=x.index)
                            for c in cc:
                                m &= c(x, tr).fillna(False)
                            return m
                        mtr, mte = mask(tr), mask(te)
                        if mtr.sum() < 25 or mte.sum() < 15:
                            continue
                        if side == "long":
                            htr, hte = tr[Y][mtr].mean(), te[Y][mte].mean()
                        else:
                            htr, hte = 1 - tr[Y][mtr].mean(), 1 - te[Y][mte].mean()
                        cov = mte.sum() / len(te)
                        if htr >= target and hte >= target and abs(htr - hte) < 0.12 and cov >= 0.05:
                            res[side].append((round(hte, 3), round(htr, 3), round(cov, 3),
                                              int(mte.sum()), dh, hz, tuple(c.name for c in cc)))
        res[side].sort(key=lambda x: -x[0])
        seen, uniq = set(), []
        for o in res[side]:
            k = frozenset(o[6])
            if any(k <= s or s <= k for s in seen):
                continue
            seen.add(k); uniq.append(o)
        res[side] = uniq
    return res


def run(m30_path: str, label: str, split_date: str, target=0.68) -> dict:
    import json, os
    df = build(m30_path)
    os.makedirs("research/cortex_confluence", exist_ok=True)
    df.to_parquet(f"research/cortex_confluence/dataset_{label}.parquet")
    r = search(df, split_date, target)
    out = {"label": label, "rows": len(df),
           "date_range": [df["date"].min(), df["date"].max()],
           "long": r["long"][:8], "short": r["short"][:8]}
    with open(f"research/cortex_confluence/results_{label}.json", "w") as f:
        json.dump(out, f, indent=2)
    return out
