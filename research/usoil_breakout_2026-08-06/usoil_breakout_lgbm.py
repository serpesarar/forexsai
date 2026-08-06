"""
USOIL kirilim GERCEK/SAHTE siniflandirmasi — LightGBM, yon-bazli, kronolojik
train/val/test + esik val'de secilir + test'te OOS dogrulanir (fakeout_lab
metodolojisiyle tutarli).
"""
import json
import numpy as np
import lightgbm as lgb
from sklearn.metrics import roc_auc_score

SC = "/private/tmp/claude-501/-Users-melihcanodacioglu-Desktop-panel/7df45e44-1b5f-4bfc-bd93-c236cdbc275f/scratchpad"
with open(f"{SC}/usoil_breakout_events.json") as f:
    events = json.load(f)
events = [e for e in events if e["outcome"] in ("GENUINE", "FAKE")]
events.sort(key=lambda e: e["time"])

FEATS = ["adx", "plus_di", "minus_di", "rsi14", "macd_hist", "dist_ema20_atr",
         "vol_ratio", "breakout_bar_range_atr", "breakout_body_ratio", "atr14"]


def run_direction(direction):
    ev = [e for e in events if e["direction"] == direction]
    n = len(ev)
    n_tr = int(n * 0.6); n_val = int(n * 0.8)
    train, val, test = ev[:n_tr], ev[n_tr:n_val], ev[n_val:]
    print(f"\n===== {direction} (n={n}: train={len(train)} val={len(val)} test={len(test)}) =====")
    print(f"donem: train {train[0]['time'][:10]}->{train[-1]['time'][:10]} | "
          f"val {val[0]['time'][:10]}->{val[-1]['time'][:10]} | "
          f"test {test[0]['time'][:10]}->{test[-1]['time'][:10]}")

    def xy(rows):
        X = np.array([[r[f] for f in FEATS] for r in rows], dtype=float)
        y = np.array([1 if r["outcome"] == "GENUINE" else 0 for r in rows])
        return X, y

    Xtr, ytr = xy(train); Xval, yval = xy(val); Xte, yte = xy(test)
    print(f"taban GENUINE orani: train={ytr.mean()*100:.1f}% val={yval.mean()*100:.1f}% test={yte.mean()*100:.1f}%")

    model = lgb.LGBMClassifier(n_estimators=200, max_depth=3, num_leaves=7,
                                learning_rate=0.03, min_child_samples=25,
                                subsample=0.8, colsample_bytree=0.8,
                                reg_alpha=1.0, reg_lambda=1.0, verbose=-1)
    model.fit(Xtr, ytr, eval_set=[(Xval, yval)],
              callbacks=[lgb.early_stopping(20, verbose=False)])

    p_tr = model.predict_proba(Xtr)[:, 1]
    p_val = model.predict_proba(Xval)[:, 1]
    p_te = model.predict_proba(Xte)[:, 1]
    print(f"AUC: train={roc_auc_score(ytr,p_tr):.3f}  val={roc_auc_score(yval,p_val):.3f}  "
          f"test={roc_auc_score(yte,p_te):.3f}")

    print("\nonem sirasi (gain):")
    for f, imp in sorted(zip(FEATS, model.feature_importances_), key=lambda x: -x[1]):
        print(f"  {f:<24s} {imp}")

    # esik val'de ara: GENUINE cagrisi icin kesinlik-hedefli (>=%75 precision, n>=15)
    print("\n=== VAL'de esik taramasi (GENUINE cagrisi icin) ===")
    best = None
    for thr in np.arange(0.50, 0.90, 0.02):
        mask = p_val >= thr
        if mask.sum() < 15:
            continue
        prec = yval[mask].mean()
        if best is None or (prec >= 0.70 and mask.sum() > best[2]):
            best = (thr, prec, mask.sum())
    if best:
        thr, prec, cov = best
        print(f"secilen esik (VAL): p>={thr:.2f}  kesinlik={100*prec:.1f}%  kapsam n={cov}/{len(val)}")
        mask_te = p_te >= thr
        if mask_te.sum() > 0:
            prec_te = yte[mask_te].mean()
            print(f"AYNI ESIK TEST/OOS: kesinlik={100*prec_te:.1f}%  n={mask_te.sum()}/{len(test)}")
        else:
            print("TEST'te bu esigi gecen olay YOK.")
    else:
        print("VAL'de %70+ kesinlikte n>=15 esik bulunamadi.")

    # SAHTE cagrisi icin de ayni (dusuk p -> FAKE guveni)
    print("\n=== VAL'de esik taramasi (SAHTE/FAKE cagrisi icin, dusuk p) ===")
    bestF = None
    for thr in np.arange(0.50, 0.10, -0.02):
        mask = p_val <= thr
        if mask.sum() < 15:
            continue
        prec = 1 - yval[mask].mean()
        if bestF is None or (prec >= 0.70 and mask.sum() > bestF[2]):
            bestF = (thr, prec, mask.sum())
    if bestF:
        thr, prec, cov = bestF
        print(f"secilen esik (VAL): p<={thr:.2f}  FAKE-kesinligi={100*prec:.1f}%  kapsam n={cov}/{len(val)}")
        mask_te = p_te <= thr
        if mask_te.sum() > 0:
            prec_te = 1 - yte[mask_te].mean()
            print(f"AYNI ESIK TEST/OOS: FAKE-kesinligi={100*prec_te:.1f}%  n={mask_te.sum()}/{len(test)}")
        else:
            print("TEST'te bu esigi gecen olay YOK.")
    else:
        print("VAL'de %70+ kesinlikte n>=15 esik bulunamadi.")

    return model, FEATS


m_buy, feats_buy = run_direction("BUY")
m_sell, feats_sell = run_direction("SELL")
