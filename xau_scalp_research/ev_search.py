"""Positive-EV hunt, net of spread. Expanding walk-forward.

Director: GBM trained on 5/5 BUY-win labels = generic P(up). prob>=0.5+m -> BUY,
<=0.5-m -> SELL. Applied across a grid of SYMMETRIC barrier sizes (bigger barriers
dilute the fixed spread). Reports mean net $ PnL/trade with bootstrap 95% CI
(success = CI lower bound > 0) and total PnL, at spread=$0.30.
"""
import numpy as np
import engine as E
import ml_model as M
from sklearn.ensemble import GradientBoostingClassifier

rng = np.random.default_rng(7)
SPREAD = 0.30
BARRIERS = [5, 10, 15, 20, 30]      # symmetric tp=sl in $ (pips)
MARGINS = [0.05, 0.10, 0.15]        # |prob-0.5| selection margin


def maxhold(b):
    return int(np.clip(b/5 * 30, 30, 180))


def boot_mean_ci(x, iters=2000):
    x = np.asarray(x)
    if len(x) == 0:
        return (0, 0)
    means = [rng.choice(x, len(x), replace=True).mean() for _ in range(iters)]
    return (np.percentile(means, 2.5), np.percentile(means, 97.5))


def main():
    t, o, h, l, c, v = E.load()
    n = len(o)
    ws, ts = E.slices(n)
    X, names = M.build_features(t, o, h, l, c, v)
    y = M.build_labels(t, o, h, l, c)        # 5/5 BUY win labels
    resolved = y >= 0

    work_end = n - maxhold(max(BARRIERS)) - 1
    folds = 6
    bounds = np.linspace(ws, work_end, folds + 1).astype(int)

    # results[(barrier,margin)] = list of net pnl per trade
    results = {(b, m): [] for b in BARRIERS for m in MARGINS}

    for f in range(1, folds):
        tr = np.zeros(n, bool); tr[ws:bounds[f]] = True; tr &= resolved
        te = np.zeros(n, bool); te[bounds[f]:bounds[f+1]] = True
        if tr.sum() < 500:
            continue
        model = GradientBoostingClassifier(n_estimators=200, max_depth=3,
                                           learning_rate=0.05, subsample=0.8,
                                           random_state=0)
        model.fit(X[tr], y[tr])
        te_idx = np.where(te)[0]
        p = model.predict_proba(X[te_idx])[:, 1]
        for m in MARGINS:
            sel = (p >= 0.5 + m) | (p <= 0.5 - m)
            idxs = te_idx[sel]
            dirs = np.where(p[sel] >= 0.5, "BUY", "SELL")
            for b in BARRIERS:
                mh = maxhold(b)
                for i, d in zip(idxs, dirs):
                    pnl, res_, _ = E.simulate_pnl(o, h, l, c, t, i+1, d, b, b, mh, SPREAD)
                    results[(b, m)].append(pnl)

    print(f"\n===== POSITIVE-EV SEARCH (GBM director, spread=${SPREAD}) =====")
    print(f"{'barrier':>7} {'margin':>6} {'trades':>7} {'meanPnL$':>9} {'EV(R)':>7}   95% CI mean PnL    total$")
    best = None
    for b in BARRIERS:
        for m in MARGINS:
            x = np.array(results[(b, m)])
            if len(x) < 50:
                continue
            mean = x.mean(); lo, hi = boot_mean_ci(x)
            ev_r = mean / b
            tag = "  +EV*" if lo > 0 else ""
            print(f"{b:>7} {m:>6.2f} {len(x):>7} {mean:>9.3f} {ev_r:>7.3f}   [{lo:+.3f},{hi:+.3f}] {x.sum():>9.0f}{tag}")
            if best is None or mean > best[0]:
                best = (mean, b, m, lo, hi, len(x), x.sum())
    print("\nBest by mean PnL/trade:", best)
    print("(+EV* = bootstrap 95% CI lower bound > 0, i.e. statistically profitable)")


if __name__ == "__main__":
    main()
