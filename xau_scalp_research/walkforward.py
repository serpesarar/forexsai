"""Rigorous walk-forward + bootstrap to characterize the real WR ceiling.

Expanding-window walk-forward across the working 40% slice. For each fold:
train on all prior working data, predict next block, collect realized outcomes.
Report pooled WR by confidence threshold WITH a minimum-volume floor and a
bootstrap 95% CI, plus spread-cost sensitivity.
"""
import numpy as np
import engine as E
import ml_model as M
from sklearn.ensemble import GradientBoostingClassifier

rng = np.random.default_rng(42)


def boot_ci(wins, n, iters=2000):
    if n == 0:
        return (0, 0)
    p = wins / n
    draws = rng.binomial(n, p, iters) / n
    return (np.percentile(draws, 2.5), np.percentile(draws, 97.5))


def main():
    t, o, h, l, c, v = E.load()
    n = len(o)
    ws, ts = E.slices(n)
    X, names = M.build_features(t, o, h, l, c, v)
    y = M.build_labels(t, o, h, l, c)
    resolved = y >= 0

    # Expanding walk-forward across working slice [ws, n)
    work_end = n - E.MAX_HOLD - 1
    folds = 6
    bounds = np.linspace(ws, work_end, folds + 1).astype(int)
    min_train = bounds[1]  # first fold trains on [ws,bounds[1]) predict next

    pooled = {thr: {"w": 0, "n": 0} for thr in (0.55, 0.60, 0.65, 0.70)}
    # for spread sensitivity at thr=0.60
    spread_pooled = {0.0: {"w":0,"n":0}, 0.3: {"w":0,"n":0}}

    for f in range(1, folds):
        tr_lo, tr_hi = ws, bounds[f]
        te_lo, te_hi = bounds[f], bounds[f+1]
        tr = np.zeros(n, bool); tr[tr_lo:tr_hi] = True; tr &= resolved
        te = np.zeros(n, bool); te[te_lo:te_hi] = True; te &= resolved
        if tr.sum() < 500 or te.sum() < 50:
            continue
        model = GradientBoostingClassifier(n_estimators=200, max_depth=3,
                                           learning_rate=0.05, subsample=0.8,
                                           random_state=0)
        model.fit(X[tr], y[tr])
        p = model.predict_proba(X[te])[:, 1]
        te_idx = np.where(te)[0]
        for thr in pooled:
            sel = (p >= thr) | (p <= 1-thr)
            idxs = te_idx[sel]; dirs = np.where(p[sel] >= 0.5, "BUY", "SELL")
            for i, d in zip(idxs, dirs):
                out, _ = E.simulate_trade(o, h, l, c, t, i+1, d)
                if out in ("win", "loss"):
                    pooled[thr]["n"] += 1
                    if out == "win": pooled[thr]["w"] += 1
        # spread sensitivity at thr 0.60
        sel = (p >= 0.60) | (p <= 0.40)
        idxs = te_idx[sel]; dirs = np.where(p[sel] >= 0.5, "BUY", "SELL")
        for sp in spread_pooled:
            for i, d in zip(idxs, dirs):
                out, _ = E.simulate_trade(o, h, l, c, t, i+1, d, spread=sp)
                if out in ("win","loss"):
                    spread_pooled[sp]["n"] += 1
                    if out == "win": spread_pooled[sp]["w"] += 1

    print("\n===== EXPANDING WALK-FORWARD (GBM, pooled over folds) =====")
    print(f"{'thr':>5} {'trades':>8} {'WR':>7}   95% CI")
    for thr in sorted(pooled):
        w, nn = pooled[thr]["w"], pooled[thr]["n"]
        wr = w/nn if nn else 0
        lo, hi = boot_ci(w, nn)
        flag = "  <-- meaningful vol" if nn >= 100 else "  (low vol, ignore)"
        print(f"{thr:>5} {nn:>8} {wr:>6.1%}   [{lo:.1%}, {hi:.1%}]{flag}")

    print("\n===== SPREAD COST SENSITIVITY (thr=0.60) =====")
    for sp in sorted(spread_pooled):
        w, nn = spread_pooled[sp]["w"], spread_pooled[sp]["n"]
        wr = w/nn if nn else 0
        print(f"  spread=${sp:.2f}: WR={wr:.1%} ({w}/{nn})")


if __name__ == "__main__":
    main()
