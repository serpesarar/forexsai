"""Comprehensive confluence collector — sweeps a broad filter pool across an
instrument's intraday data, collects EVERY stable ≥target OOS combo (LONG &
SHORT), and persists them to the rules JSON so the agents know them all.

Self-contained (reuses generic.tf_features/_enrich). Base timeframe is the
file's native bar; mid/slow are resamples. Macro filters: DXY, US10Y, VIX.
"""
from __future__ import annotations

import sys
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generic as G  # noqa: E402

VIX_CSV = "/Users/melihcanodacioglu/Desktop/XAUUSDDATA/fundamental/vix-daily.csv"


def _daily_chg_map(kind: str) -> dict:
    if kind == "vix":
        df = pd.read_csv(VIX_CSV); df.columns = [c.strip().upper() for c in df.columns]
        dcol = "OBSERVATION_DATE" if "OBSERVATION_DATE" in df.columns else df.columns[0]
        df[dcol] = pd.to_datetime(df[dcol], format="%m/%d/%Y", errors="coerce")
        s = pd.to_numeric(df["CLOSE"], errors="coerce"); s.index = df[dcol].dt.date
        s = s.dropna().sort_index()
    else:
        s = G.load_dxy_daily() if kind == "dxy" else G.load_us10y_daily()
    # LEAK-FREE: map day D → the change of the PRIOR completed day (D-1 vs D-2),
    # which is known before D opens. Using same-day (to daily close) would leak
    # future info into an intraday decision — that inflated earlier macro combos.
    k = [d.isoformat() for d in s.index]; v = s.values
    return {k[t]: (v[t - 1] - v[t - 2]) / v[t - 2] * 100 for t in range(2, len(k)) if v[t - 2]}


def build_dataset(path: str, base_min: int, dec_hours: list[int],
                  horizons: dict[str, int], flat: dict[str, float]) -> pd.DataFrame:
    base = G.load_m30(path)   # loads any intraday OHLCV, tz-aware
    agg = {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}
    feat = G.tf_features(base, "M30")
    for tf, mult in (("H1", 4), ("H4", 16)):
        rule = f"{base_min * mult}min"
        bb = base.resample(rule, label="right", closed="right").agg(agg).dropna()
        feat = feat.join(G.tf_features(bb, tf).reindex(feat.index, method="ffill"))
    feat = G._enrich(feat)
    carr = base["Close"].values
    pos = {ts: i for i, ts in enumerate(base["Close"].index)}
    on_lag = max(1, int(round(8 * 60 / base_min)))   # ~8h overnight proxy
    rows = []
    for ts in feat.index:
        if ts.hour not in dec_hours or ts.minute != 0:
            continue
        i = pos.get(ts)
        if i is None:
            continue
        row = feat.loc[ts].to_dict(); row["date"] = ts.date().isoformat(); row["dh"] = ts.hour
        for hz, n in horizons.items():
            ch = (carr[i + n] - carr[i]) / carr[i] * 100 if i + n < len(carr) else None
            row[f"y_{hz}"] = np.nan if ch is None else (1 if ch > flat[hz] else 0 if ch < -flat[hz] else np.nan)
        row["overnight_change"] = (carr[i] / carr[i - on_lag] - 1) * 100 if i >= on_lag else np.nan
        rows.append(row)
    df = pd.DataFrame(rows)
    for kind in ("dxy", "us10y", "vix"):
        try:
            df[f"{kind}_chg"] = df["date"].map(_daily_chg_map(kind))
        except Exception:
            df[f"{kind}_chg"] = np.nan
    return df


# ── Atomic condition pool (both directions, human-labelled) ───────────────────
def _atoms(tr: pd.DataFrame) -> dict:
    a = {}
    def q(f, p): return tr[f].quantile(p) if f in tr else np.nan
    # alignment
    a["bull_score≥11"] = ("bull_score", lambda x: x["bull_score"] >= 11)
    a["bull_score≤2"] = ("bull_score", lambda x: x["bull_score"] <= 2)
    a["mom_agree=3"] = ("mom_agree", lambda x: x["mom_agree"] >= 3)
    a["mom_agree=0"] = ("mom_agree", lambda x: x["mom_agree"] <= 0)
    a["trend_agree=3"] = ("trend_agree", lambda x: x["trend_agree"] >= 3)
    a["trend_agree=0"] = ("trend_agree", lambda x: x["trend_agree"] <= 0)
    # momentum / extension (train-quantile thresholds)
    for f in ("rsi_M30", "px_ema20_M30", "macd_hist_M30", "ret6_M30", "boll_z_M30"):
        hi, lo = q(f, 0.82), q(f, 0.18)
        a[f"{f}>hi"] = (f, (lambda x, f=f, hi=hi: x[f] > hi))
        a[f"{f}<lo"] = (f, (lambda x, f=f, lo=lo: x[f] < lo))
    ah = q("adx_H1", 0.70)
    a["adx_H1>hi"] = ("adx_H1", lambda x, ah=ah: x["adx_H1"] > ah)
    # session
    oh, ol = q("overnight_change", 0.75), q("overnight_change", 0.25)
    a["overnight>hi"] = ("overnight_change", lambda x, oh=oh: x["overnight_change"] > oh)
    a["overnight<lo"] = ("overnight_change", lambda x, ol=ol: x["overnight_change"] < ol)
    # macro (both directions)
    for m in ("dxy_chg", "us10y_chg", "vix_chg"):
        hi, lo = q(m, 0.70), q(m, 0.30)
        a[f"{m}↑"] = (m, (lambda x, m=m, hi=hi: x[m] > hi))
        a[f"{m}↓"] = (m, (lambda x, m=m, lo=lo: x[m] < lo))
    return a


def collect(df: pd.DataFrame, split: str, dec_hours: list[int], horizons: list[str],
            target: float = 0.70, min_cov: float = 0.05) -> list[dict]:
    found = []
    for dh in dec_hours:
        for hz in horizons:
            Y = f"y_{hz}"
            d = df[df["dh"] == dh].dropna(subset=[Y]).replace([np.inf, -np.inf], np.nan)
            tr, te = d[d["date"] <= split], d[d["date"] > split]
            if len(tr) < 120 or len(te) < 70:
                continue
            atoms = _atoms(tr)
            names = [n for n in atoms if atoms[n][0] in tr.columns]
            # precompute masks
            mtr = {n: atoms[n][1](tr).fillna(False) for n in names}
            mte = {n: atoms[n][1](te).fillna(False) for n in names}
            ytr, yte = tr[Y].values, te[Y].values
            ntr, nte = len(tr), len(te)
            for r in (2, 3):
                for cc in combinations(names, r):
                    # avoid same-feature contradictions
                    if len({atoms[n][0] for n in cc}) < r:
                        continue
                    Mtr = np.logical_and.reduce([mtr[n].values for n in cc])
                    Mte = np.logical_and.reduce([mte[n].values for n in cc])
                    ktr, kte = Mtr.sum(), Mte.sum()
                    if ktr < 18 or kte < 12 or kte / nte < min_cov:
                        continue
                    up_tr, up_te = ytr[Mtr].mean(), yte[Mte].mean()
                    for side, htr, hte in (("long", up_tr, up_te), ("short", 1 - up_tr, 1 - up_te)):
                        if htr >= target and hte >= target and abs(htr - hte) < 0.11:
                            found.append({"side": side, "hit": round(hte, 3),
                                          "cov": round(kte / nte, 3), "n": int(kte),
                                          "dh": dh, "hz": hz, "cond": tuple(cc)})
    # dedup by (side, condition-set), keep highest hit
    found.sort(key=lambda x: (-x["hit"], -x["cov"]))
    seen, uniq = set(), []
    for f in found:
        key = (f["side"], frozenset(f["cond"]))
        if any(f["side"] == s and (frozenset(f["cond"]) <= c or c <= frozenset(f["cond"])) for s, c in seen):
            continue
        seen.add((f["side"], frozenset(f["cond"]))); uniq.append(f)
    return uniq
