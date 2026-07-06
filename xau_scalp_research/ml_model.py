"""Step 3 — lean ML for XAUUSD 5-pip scalping. Leak-free, walk-forward.

Label: BUY entered at next-bar open; y=1 if +$5 hit before -$5 within 30 bars
       (win), y=0 if -$5 first (loss). Timeouts/gaps excluded from training.
At inference: P(buy_win) high -> take BUY, low -> take SELL. Selected trades'
realized WR measured with the SAME engine (pessimistic tie-break).
"""
import numpy as np
import engine as E
import strategies as S
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

EPS = 1e-9


def rsi(c, n=14):
    d = np.diff(c, prepend=c[0])
    up = np.where(d > 0, d, 0.0)
    dn = np.where(d < 0, -d, 0.0)
    ru = np.copy(up); rd = np.copy(dn)
    # Wilder smoothing
    au = np.zeros_like(c); ad = np.zeros_like(c)
    au[n] = up[1:n+1].mean(); ad[n] = dn[1:n+1].mean()
    for i in range(n+1, len(c)):
        au[i] = (au[i-1]*(n-1) + up[i]) / n
        ad[i] = (ad[i-1]*(n-1) + dn[i]) / n
    rs = au / (ad + EPS)
    return 100 - 100/(1+rs)


def atr(h, l, c, n=14):
    tr = np.maximum(h - l, np.maximum(np.abs(h - np.roll(c, 1)),
                                      np.abs(l - np.roll(c, 1))))
    tr[0] = h[0] - l[0]
    out = np.zeros_like(c)
    out[n] = tr[1:n+1].mean()
    for i in range(n+1, len(c)):
        out[i] = (out[i-1]*(n-1) + tr[i]) / n
    return out


def build_features(t, o, h, l, c, v):
    """Return feature matrix X (n x F) and feature names. Row i uses only <= i."""
    n = len(c)
    r1 = np.zeros(n); r5 = np.zeros(n); r15 = np.zeros(n); r30 = np.zeros(n)
    r1[1:] = c[1:]/c[:-1]-1
    r5[5:] = c[5:]/c[:-5]-1
    r15[15:] = c[15:]/c[:-15]-1
    r30[30:] = c[30:]/c[:-30]-1
    rsi14 = rsi(c, 14)
    atr14 = atr(h, l, c, 14)
    atr_n = atr14 / (c + EPS)
    body = (c - o) / (h - l + EPS)
    rng = h - l
    rng_mean = np.convolve(rng, np.ones(20)/20, mode="full")[:n]
    rng_z = rng / (rng_mean + EPS)
    v_mean = np.convolve(v, np.ones(20)/20, mode="full")[:n]
    v_z = v / (v_mean + EPS)

    # higher-TF 5m EMA trend + S/R + channel
    htf5 = S.resample(t, o, h, l, c, v, 300)
    ct, _, hh5, ll5, cc5 = htf5
    ef = S._ema(cc5, 20); es = S._ema(cc5, 50)
    ema_spread5 = (ef - es) / (cc5 + EPS)
    sup5, res5 = S.build_levels(htf5, 20)
    htf15 = S.resample(t, o, h, l, c, v, 900)
    sup15, res15 = S.build_levels(htf15, 12)
    # channel on 5m
    n5 = len(cc5); ch_mid = np.full(n5, np.nan); ch_w = np.full(n5, np.nan); ch_sl = np.full(n5, np.nan)
    W = 20
    for i in range(W, n5):
        y = cc5[i-W:i]; x = np.arange(W)
        a, b = np.polyfit(x, y, 1); fit = a*x+b; sd = (y-fit).std()
        ch_mid[i] = a*W+b; ch_w[i] = sd; ch_sl[i] = a

    j5 = np.searchsorted(ct, t, side="right") - 1
    j15 = np.searchsorted(htf15[0], t, side="right") - 1

    feats = {}
    feats["r1"] = r1; feats["r5"] = r5; feats["r15"] = r15; feats["r30"] = r30
    feats["rsi14"] = (rsi14 - 50)/50
    feats["atr_n"] = atr_n
    feats["body"] = body
    feats["rng_z"] = rng_z
    feats["v_z"] = v_z

    es5 = np.where(j5 >= 0, ema_spread5[np.clip(j5, 0, n5-1)], 0.0)
    feats["ema_spread5"] = es5
    a14 = atr14 + EPS
    s5v = np.where(j5 >= 0, sup5[np.clip(j5, 0, n5-1)], np.nan)
    r5v = np.where(j5 >= 0, res5[np.clip(j5, 0, n5-1)], np.nan)
    s15v = np.where(j15 >= 0, sup15[np.clip(j15, 0, len(sup15)-1)], np.nan)
    r15v = np.where(j15 >= 0, res15[np.clip(j15, 0, len(res15)-1)], np.nan)
    feats["dist_sup5"] = np.nan_to_num((c - s5v)/a14, nan=0.0)
    feats["dist_res5"] = np.nan_to_num((r5v - c)/a14, nan=0.0)
    feats["dist_sup15"] = np.nan_to_num((c - s15v)/a14, nan=0.0)
    feats["dist_res15"] = np.nan_to_num((r15v - c)/a14, nan=0.0)
    midv = np.where(j5 >= 0, ch_mid[np.clip(j5, 0, n5-1)], np.nan)
    wv = np.where(j5 >= 0, ch_w[np.clip(j5, 0, n5-1)], np.nan)
    slv = np.where(j5 >= 0, ch_sl[np.clip(j5, 0, n5-1)], np.nan)
    feats["ch_pos"] = np.nan_to_num((c - midv)/(wv+EPS), nan=0.0)
    feats["ch_slope"] = np.nan_to_num(slv/(c+EPS)*1000, nan=0.0)
    hr = ((t % 86400) / 3600.0)
    feats["hour_sin"] = np.sin(2*np.pi*hr/24)
    feats["hour_cos"] = np.cos(2*np.pi*hr/24)

    names = list(feats.keys())
    X = np.column_stack([feats[k] for k in names])
    return X, names


def build_labels(t, o, h, l, c):
    """y per bar i: 1 if BUY (entry i+1 open) wins, 0 loss, -1 timeout/gap."""
    n = len(c)
    y = np.full(n, -1, dtype=np.int8)
    for i in range(n-1):
        out, _ = E.simulate_trade(o, h, l, c, t, i+1, "BUY")
        if out == "win": y[i] = 1
        elif out == "loss": y[i] = 0
    return y


def realized_wr(t, o, h, l, c, idxs, dirs, label):
    trades = []
    n = len(o)
    for i, d in zip(idxs, dirs):
        if i+1 >= n: continue
        out, hold = E.simulate_trade(o, h, l, c, t, i+1, d)
        if out: trades.append((out, hold, t[i+1]))
    return E.report(trades, label)


def main():
    t, o, h, l, c, v = E.load()
    n = len(o)
    ws, ts = E.slices(n)
    print("Building features...")
    X, names = build_features(t, o, h, l, c, v)
    print(f"  {len(names)} features: {names}")
    print("Building labels (BUY win/loss)...")
    y = build_labels(t, o, h, l, c)

    # valid rows: in working slice, resolved label, enough warmup
    warm = ws  # features need history but ws=57800 >> warmup, fine
    train_mask = np.zeros(n, bool); test_mask = np.zeros(n, bool)
    train_mask[ws:ts] = True
    test_mask[ts:n-E.MAX_HOLD-1] = True
    resolved = y >= 0

    tr = train_mask & resolved
    te = test_mask & resolved
    Xtr, ytr = X[tr], y[tr]
    Xte, yte = X[te], y[te]
    te_idx = np.where(te)[0]
    print(f"\ntrain rows={tr.sum()} (win rate base {ytr.mean():.3f})")
    print(f"test  rows={te.sum()} (win rate base {yte.mean():.3f})")

    sc = StandardScaler().fit(Xtr)
    Xtr_s = sc.transform(Xtr); Xte_s = sc.transform(Xte)

    for name, model in [
        ("LogReg", LogisticRegression(max_iter=2000, C=0.5)),
        ("GBM", GradientBoostingClassifier(n_estimators=200, max_depth=3, learning_rate=0.05, subsample=0.8)),
    ]:
        print(f"\n################ {name} ################")
        model.fit(Xtr_s if name=="LogReg" else Xtr, ytr)
        p = model.predict_proba(Xte_s if name=="LogReg" else Xte)[:, 1]
        # direction from prob; select by confidence threshold
        for thr in (0.55, 0.60, 0.65, 0.70):
            sel = (p >= thr) | (p <= 1-thr)
            if sel.sum() == 0:
                print(f"  thr={thr}: no trades"); continue
            idxs = te_idx[sel]
            dirs = np.where(p[sel] >= 0.5, "BUY", "SELL")
            print(f"\n  --- confidence thr={thr} | selected {sel.sum()} of {len(p)} ---")
            realized_wr(t, o, h, l, c, idxs, dirs, f"{name} thr={thr} TEST(held-out)")


if __name__ == "__main__":
    main()
