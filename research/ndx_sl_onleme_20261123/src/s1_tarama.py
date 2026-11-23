"""Aday tarama — PROTOCOL.md §Adaylar + EK-1. Normal + stres koşusu, dönem başına ölçüler."""
from __future__ import annotations

import json
import pickle
import sys

import numpy as np
import pandas as pd

from eng import CORE, HERE, PERIODS, run2, skip_cf

RES = HERE.parent / "results"
M, SIG = pickle.load(open(RES / "mkt.pkl", "rb"))
Q = json.load(open(RES / "thresholds.json"))
MK = ["eski", "y24", "y25", "y26"]
SLR = -0.99


def mkt(*_):
    return {"kind": "mkt"}


def skip_if(fn):
    def r(m, k, f, c):
        return None if fn(m, k, f, c) else {"kind": "mkt"}
    return r


def stp(x, w):
    def r(m, k, f, c):
        a = f["atr5"]
        if not np.isfinite(a):
            return {"kind": "mkt"}
        return {"kind": "stp", "level": f["c"] + 1.5 * c["sc"] + x * a, "wait": w}
    return r


def reclaim(fr, w):
    def r(m, k, f, c):
        p = c.get("prev")
        if c["fam"] == "RE" and p and p["why"] == "SL":
            return {"kind": "conf", "level": p["e"] - (1 - fr) * p["sl"], "wait": w}
        return {"kind": "mkt"}
    return r


def lock(X):
    return lambda L: sum(L) >= X


def slcount(N):
    return lambda L: sum(1 for r in L if r <= SLR) >= N


def giveback(Y):
    def g(L):
        if not L:
            return False
        cs = np.cumsum(L)
        pk = max(0.0, cs.max())
        return pk > 0 and pk - cs[-1] >= Y
    return g


def pv_lim(m, k, f, c):
    if f["reg"] >= 1.8 and np.isfinite(f["atr5"]):
        return {"kind": "lim", "level": f["c"] - f["atr5"], "wait": 120}
    return {"kind": "mkt"}


C: dict[str, dict] = {}
for X in (2, 3, 4):
    C[f"A kâr kilidi ≥+{X}R"] = dict(day_rule=lock(X))
for N in (1, 2, 3):
    C[f"B gün {N}. SL sonrası dur"] = dict(day_rule=slcount(N))
for Y in (1.5, 2, 3):
    C[f"C geri verme ≥{Y}R"] = dict(day_rule=giveback(Y))
for x in (0.25, 0.5, 1.0):
    for w in (15, 30):
        C[f"D buy-stop +{x}ATR5 {w}dk"] = dict(rule=stp(x, w))
for n in (10, 15):
    C[f"E probasyon {n} bar"] = dict(prob_n=n)
for n in (5, 10):
    C[f"E0 probasyon {n} bar + kayıpsız"] = dict(prob_n=n, prob_nonneg=True)
for cap in (0.5, 1.0):
    C[f"E-cap bant ≤{cap}×SL"] = dict(prob_cap=cap)
for fr in (0.5, 1.0):
    for w in (30, 60):
        C[f"F SL sonrası RE geri alma {fr} {w}dk"] = dict(rule=reclaim(fr, w))
for n in (60, 120):
    for p in ("10", "20", "33"):
        q = Q[f"er{n}"][p]
        C[f"G ER{n} < q{p}"] = dict(rule=skip_if(lambda m, k, f, c, n=n, q=q: m.er[n][k - 1] < q))
for kk in (3, 4, 6):
    C[f"H şok ≥{kk}× (180dk)"] = dict(rule=skip_if(lambda m, k, f, c, kk=kk: m.shock_at(k) >= kk))
for p in ("10", "20", "33"):
    q = Q["noise"][p]
    C[f"I gürültü < q{p}"] = dict(rule=skip_if(lambda m, k, f, c, q=q: m.noise_at(k) < q))
for x in (30, 50, 100):
    C[f"R G8 probasyon kaçışı ≥{x}p"] = dict(rule=skip_if(
        lambda m, k, f, c, x=x: c["sig_px"] is not None and f["c"] - c["sig_px"] >= x * c["sc"]))
C["R PV −1ATR5 limit (oynak)"] = dict(rule=pv_lim)
C["R G7 rejim ≥1,8 atla"] = dict(rule=skip_if(lambda m, k, f, c: f["reg"] >= 1.8))


def run_all(kw: dict, stress: bool = False):
    ts, ss = [], []
    extra = dict(spread=2.25, slip=0.2, lag=1) if stress else {}
    for k in MK:
        t, s = run2(M[k], SIG[k], **kw, **extra)
        if not stress:
            s = skip_cf(M[k], s)
        ts.append(t)
        ss.append(s)
    t = pd.concat(ts)
    s = pd.concat(ss)
    return t[t.period != "-"], s[s.period != "-"] if len(s) else s


def stats(t: pd.DataFrame, b: pd.DataFrame, s: pd.DataFrame, p: str) -> dict:
    x, y = t[t.period == p], b[b.period == p]
    sl0, tp0 = int((y.why == "SL").sum()), int((y.why == "TP").sum())
    sl1, tp1 = int((x.why == "SL").sum()), int((x.why == "TP").sum())
    sk = s[s.period == p] if len(s) else s
    return dict(n=len(x), TP=tp1, SL=sl1, SR=float(x.R.sum()), mR=float(x.R.mean()) if len(x) else np.nan,
                dSR=float(x.R.sum() - y.R.sum()), dmR=float((x.R.mean() if len(x) else 0) - y.R.mean()),
                sl_engel=1 - sl1 / sl0 if sl0 else np.nan, tp_kayip=1 - tp1 / tp0 if tp0 else np.nan,
                atlanan_n=len(sk), atlanan_R=float(sk.R.mean()) if len(sk) and "R" in sk else np.nan)


def day_boot(t: pd.DataFrame, b: pd.DataFrame, reps: int = 2000, seed: int = 7) -> float:
    t, b = t[t.period.isin(CORE)], b[b.period.isin(CORE)]
    d = pd.concat([t.groupby("day").R.sum().rename("r"), b.groupby("day").R.sum().rename("b")], axis=1).fillna(0)
    diff = (d.r - d.b).to_numpy()
    rng = np.random.default_rng(seed)
    m = diff[rng.integers(0, len(diff), (reps, len(diff)))].mean(1)
    return float((m > 0).mean())


def main():
    only = sys.argv[1:] or None
    b, _ = run_all({})
    bs, _ = run_all({}, stress=True)
    b.to_pickle(RES / "base_full.pkl")
    out = []
    for name, kw in C.items():
        if only and not any(o in name for o in only):
            continue
        t, s = run_all(kw)
        tst, _ = run_all(kw, stress=True)
        row = {"aday": name}
        for p in PERIODS:
            for kx, v in stats(t, b, s, p).items():
                row[f"{p}|{kx}"] = v
        row["boot_P"] = day_boot(t, b)
        core_t, core_b = tst[tst.period.isin(CORE)], bs[bs.period.isin(CORE)]
        row["stres_dSR"] = float(core_t.R.sum() - core_b.R.sum())
        row["krit1"] = all(row[f"{p}|dSR"] > 0 and row[f"{p}|dmR"] > 0 for p in CORE)
        out.append(row)
        t.to_pickle(RES / f"t_{abs(hash(name)) % 10**8}.pkl")
        print(f"{name:34s} " + " ".join(f"{p}:{row[p + '|dSR']:+6.1f}" for p in CORE)
              + f" Y26b:{row['Y26b|dSR']:+5.1f} VAKA SL-engel {row['VAKA|sl_engel']:.0%} TP-kayıp {row['VAKA|tp_kayip']:.0%}"
              + f" | P {row['boot_P']:.2f} stres {row['stres_dSR']:+.1f} {'K1✓' if row['krit1'] else ''}", flush=True)
    pd.DataFrame(out).to_csv(RES / "tarama.csv", index=False)


if __name__ == "__main__":
    main()
