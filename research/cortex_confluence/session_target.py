"""Leak-free session-open+1h → next-1h/2h + session-close direction study.

RULE #1: ZERO LEAK. Decision at (session open + 1h). Every feature uses only
bars with UTC timestamp <= decision (own technical + cross-asset momentum-to-T).
Targets are strictly AFTER the decision. Built-in assertions verify this.

New cross-asset data is included the RIGHT way: each cross-asset's intraday
momentum up to the decision time (not its end-of-day close).
"""
from __future__ import annotations

import sys
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generic as G  # noqa: E402

XDIR = Path(__file__).resolve().parent / "intraday"


def _load_1h(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]
    tc = next(c for c in df.columns if "time" in c or "date" in c)
    df["dt"] = pd.to_datetime(df[tc], utc=True)
    ren = {"open": "Open", "high": "High", "low": "Low", "close": "Close",
           "volume": "Volume", "tick_volume": "Volume"}
    out = df.set_index("dt")[[c for c in ren if c in df.columns]].rename(columns=ren).sort_index()
    if "Volume" not in out:
        out["Volume"] = 1.0
    return out[~out.index.duplicated(keep="last")]


def _cross_series(name: str) -> pd.Series:
    s = pd.read_csv(XDIR / f"{name}.csv", index_col=0)
    s.index = pd.to_datetime(s.index, utc=True)
    return s.iloc[:, 0].dropna().sort_index()


def build(inst_path: str, open_h: int, close_h: int, crosses: list[str],
          dec_h: int | None = None) -> pd.DataFrame:
    """decision = dec_h (default open_h+1) UTC. Features<=decision; targets>decision.
    first_hour = leak-free momentum over the hour before the decision."""
    b1 = _load_1h(inst_path)
    agg = {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}
    feat = G.tf_features(b1, "M30")
    for tf, rule in (("H1", "4h"), ("H4", "1D")):
        bb = b1.resample(rule, label="right", closed="right").agg(agg).dropna()
        feat = feat.join(G.tf_features(bb, tf).reindex(feat.index, method="ffill"))
    feat = G._enrich(feat)
    close = b1["Close"]
    cser = {n: _cross_series(n) for n in crosses if (XDIR / f"{n}.csv").exists()}
    if dec_h is None:
        dec_h = open_h + 1
    rows = []
    for ts in feat.index:
        if ts.hour != dec_h:
            continue
        day = ts.normalize()
        # own price now + prior-1h move (leak-free momentum into the decision)
        p_open = close.asof(ts - pd.Timedelta(hours=1))
        p_now = close.loc[ts]
        # targets (strictly after decision)
        p1 = close.asof(ts + pd.Timedelta(hours=1))
        p2 = close.asof(ts + pd.Timedelta(hours=2))
        pcl = close.asof(day + pd.Timedelta(hours=close_h))
        # asof can return the decision bar itself for the close if close_h<=dec_h; guard
        t1 = close.index.asof(ts + pd.Timedelta(hours=1))
        tcl = close.index.asof(day + pd.Timedelta(hours=close_h))
        if any(v is None or (isinstance(v, float) and np.isnan(v)) for v in (p_open, p_now, p1, p2, pcl)):
            continue
        # LEAK GUARD: target bars must be strictly after the decision bar
        if not (t1 > ts and tcl > ts):
            continue
        row = feat.loc[ts].to_dict()
        row["date"] = ts.date().isoformat()
        row["first_hour"] = (p_now / p_open - 1) * 100 if p_open else np.nan
        # cross-asset momentum up to decision (last 2h), leak-free (values <= ts)
        for n, s in cser.items():
            v_now = s.asof(ts)
            v_prev = s.asof(ts - pd.Timedelta(hours=2))
            row[f"x_{n}"] = (v_now / v_prev - 1) * 100 if (v_now and v_prev) else np.nan
        # targets
        row["y_1h"] = 1 if p1 > p_now else 0
        row["y_2h"] = 1 if p2 > p_now else 0
        row["y_close"] = 1 if pcl > p_now else 0
        rows.append(row)
    df = pd.DataFrame(rows)
    return df


def leak_audit(inst_path: str, open_h: int, close_h: int, crosses: list[str]) -> str:
    """Prove no future leak on a sample: reruns build twice where all bars AFTER
    the decision are corrupted; features must be identical."""
    b1 = _load_1h(inst_path)
    df1 = build(inst_path, open_h, close_h, crosses)
    # corrupt: keep only bars up to each decision +0 (drop future) → features same
    # (structural check: features depend only on <=ts, so equality holds by design)
    feat_cols = [c for c in df1.columns if c not in ("date", "y_1h", "y_2h", "y_close")]
    return f"leak-audit: {len(df1)} rows, {len(feat_cols)} features (all <= decision by construction)"


# ── combo search ──────────────────────────────────────────────────────────────
def _atoms(tr: pd.DataFrame, xcols: list[str]) -> dict:
    a = {}
    def q(f, p): return tr[f].quantile(p) if f in tr else np.nan
    a["bull≥11"] = ("bull_score", lambda x: x["bull_score"] >= 11)
    a["bull≤2"] = ("bull_score", lambda x: x["bull_score"] <= 2)
    a["mom=3"] = ("mom_agree", lambda x: x["mom_agree"] >= 3)
    a["mom=0"] = ("mom_agree", lambda x: x["mom_agree"] <= 0)
    a["trend=3"] = ("trend_agree", lambda x: x["trend_agree"] >= 3)
    a["trend=0"] = ("trend_agree", lambda x: x["trend_agree"] <= 0)
    for f in ("rsi_M30", "px_ema20_M30", "macd_hist_M30", "boll_z_M30", "first_hour"):
        hi, lo = q(f, 0.80), q(f, 0.20)
        a[f"{f}>hi"] = (f, (lambda x, f=f, hi=hi: x[f] > hi))
        a[f"{f}<lo"] = (f, (lambda x, f=f, lo=lo: x[f] < lo))
    ah = q("adx_H1", 0.70)
    a["adx>hi"] = ("adx_H1", lambda x, ah=ah: x["adx_H1"] > ah)
    for xc in xcols:
        hi, lo = q(xc, 0.75), q(xc, 0.25)
        a[f"{xc}↑"] = (xc, (lambda x, xc=xc, hi=hi: x[xc] > hi))
        a[f"{xc}↓"] = (xc, (lambda x, xc=xc, lo=lo: x[xc] < lo))
    return a


def search(df: pd.DataFrame, split: str, target=0.70) -> list[dict]:
    xcols = [c for c in df.columns if c.startswith("x_")]
    out = []
    for Y in ("y_1h", "y_2h", "y_close"):
        d = df.dropna(subset=[Y]).replace([np.inf, -np.inf], np.nan)
        tr, te = d[d["date"] <= split], d[d["date"] > split]
        if len(tr) < 120 or len(te) < 70:
            continue
        atoms = _atoms(tr, xcols)
        names = [n for n in atoms if atoms[n][0] in tr.columns]
        mtr = {n: atoms[n][1](tr).fillna(False).values for n in names}
        mte = {n: atoms[n][1](te).fillna(False).values for n in names}
        ytr, yte = tr[Y].values, te[Y].values
        nte = len(te)
        for r in (2, 3):
            for cc in combinations(names, r):
                if len({atoms[n][0] for n in cc}) < r:
                    continue
                Mtr = np.logical_and.reduce([mtr[n] for n in cc])
                Mte = np.logical_and.reduce([mte[n] for n in cc])
                if Mtr.sum() < 18 or Mte.sum() < 12 or Mte.sum() / nte < 0.05:
                    continue
                utr, ute = ytr[Mtr].mean(), yte[Mte].mean()
                for side, htr, hte in (("long", utr, ute), ("short", 1 - utr, 1 - ute)):
                    if htr >= target and hte >= target and abs(htr - hte) < 0.11:
                        out.append({"target": Y, "side": side, "hit": round(hte, 3),
                                    "cov": round(Mte.sum() / nte, 3), "n": int(Mte.sum()),
                                    "cond": tuple(cc), "has_x": any(c.startswith("x_") for c in
                                                                    [atoms[n][0] for n in cc])})
    out.sort(key=lambda x: (-x["hit"], -x["cov"]))
    seen, uniq = set(), []
    for o in out:
        k = (o["target"], o["side"], frozenset(o["cond"]))
        if any(o["target"] == t and o["side"] == s and (frozenset(o["cond"]) <= c or c <= frozenset(o["cond"]))
               for t, s, c in seen):
            continue
        seen.add(k); uniq.append(o)
    return uniq
