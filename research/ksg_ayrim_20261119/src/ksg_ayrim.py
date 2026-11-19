"""ksg_ayrim.py — KSG gecelerinde kaybeden/kazanan ayrımı (PROTOCOL). python ksg_ayrim.py ozellik | analiz"""
from __future__ import annotations

import json
import sys
import warnings
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]
RES = HERE / "results"
for p in ("research/xp_paket_ayrim_20261119/src", "research/ksg_opex_canli_20261119/src"):
    sys.path.insert(0, str(ROOT / p))
FEEDS = ["MT5_NAS100", "DUKA_NDX", "MT5_US500", "MT5_US30", "MT5_US2000"]
KESIF_SON = pd.Timestamp("2021-10-31")


def _job(name: str) -> pd.DataFrame:
    import motor as Mo
    import oynat as Oy
    Oy.kl.ay.NYSE_HOLIDAYS = set(Oy.kl.ay.NYSE_HOLIDAYS) | Oy.holidays()
    n = Oy.nights(name)
    if name == "MT5_US500":
        n = n[n.d >= "2018-06-01"]
    b, hv = Mo.load_feed(name)
    daily = Mo.rth_daily(b)
    rows = []
    for r in n.itertuples():
        f = Mo.feed_trade_feats(b, daily, pd.Timestamp(r.d), hv)
        rows.append({"besleme": name, "d": r.d, "net": r.net, "vix_prev": r.vix_prev, "vadeye": r.vadeye, "gun": r.d.dayofweek, **f})
    return pd.DataFrame(rows)


def ozellik() -> None:
    RES.mkdir(exist_ok=True)
    with ProcessPoolExecutor(max_workers=5) as ex:
        parts = list(ex.map(_job, FEEDS))
    A = pd.concat(parts, ignore_index=True)
    A["donem"] = np.where(A.d <= KESIF_SON, "KESIF", "TEST")
    A.to_parquet(RES / "ksg_ozellik.parquet")
    print(A.groupby(["besleme", "donem"]).agg(n=("net", "size"), ort=("net", "mean"), kayb=("net", lambda x: (x < 0).mean())).round(2))


def analiz() -> None:
    import ortak as K
    from sklearn.linear_model import LogisticRegression
    from sklearn.cluster import KMeans
    from sklearn.decomposition import PCA
    from sklearn.metrics import silhouette_score
    A = pd.read_parquet(RES / "ksg_ozellik.parquet")
    A["y"] = (A.net < 0).astype(int)
    pre = ("m30_", "h1_", "h2_", "h4_", "D_", "W_", "H_")
    tr = (A.besleme == "MT5_NAS100") & (A.donem == "KESIF")
    feats = [c for c in A.columns if (c.startswith(pre) or c in ("vix_prev", "vadeye", "gun"))
             and A[tr][c].notna().mean() > 0.7 and A[tr][c].nunique() > 2]
    X = np.zeros((len(A), len(feats)))
    for f in FEEDS:
        ix = (A.besleme == f).values
        X[ix] = K.standardize(A[ix], A[ix & (A.donem == "KESIF").values], feats)
    trm = tr.values
    res = {"veri": A.groupby(["besleme", "donem"]).agg(n=("net", "size"), ort=("net", "mean"), kayb=("y", "mean")).round(3)
           .reset_index().to_dict("records"), "ozellik": len(feats)}
    # 1. tek tek
    a = K.auc_cols(X[trm], A.y.values[trm])
    thr = K.fwer_threshold([(X[trm], A.y.values[trm])], 1000)
    te = ((A.besleme == "MT5_NAS100") & (A.donem == "TEST")).values
    du = ((A.besleme == "DUKA_NDX") & (A.donem == "TEST")).values
    at, ad = K.auc_cols(X[te], A.y.values[te]), K.auc_cols(X[du], A.y.values[du])
    df = pd.DataFrame({"ozellik": feats, "kesif": a, "test": at, "duka_test": ad})
    df["sapma"] = (df.kesif - 0.5).abs()
    df = df.sort_values("sapma", ascending=False)
    gec = df[df.sapma >= thr]
    res["tek"] = {"aile_esik": round(thr, 4), "gecen": gec.round(3).to_dict("records"),
                  "kesif_test_r": round(float(np.corrcoef(df.kesif, df.test)[0, 1]), 3), "ilk15": df.head(15).round(3).to_dict("records")}
    print("tek tek: eşik", round(thr, 3), "geçen", gec.ozellik.tolist()[:8], "KEŞİF↔TEST r", res["tek"]["kesif_test_r"], flush=True)
    for r in df.head(8).itertuples():
        print(f"   {r.ozellik:32s} KEŞİF {r.kesif:.3f} TEST {r.test:.3f} Duka {r.duka_test:.3f}")
    # 2. modeller
    yk, dk = A.y.values[trm], A.d[trm]
    lo, hi = np.quantile(A.net[trm], [0.025, 0.975])
    nk = A.net.clip(lo, hi).values[trm]
    best, cs = None, {}
    for C in (0.005, 0.01, 0.03, 0.1, 0.3, 1.0):
        oof = K.oof_scores(lambda: LogisticRegression(penalty="l1", C=C, solver="liblinear", class_weight="balanced"), X[trm], yk, dk)
        ok = np.isfinite(oof)
        cs[C] = K.safe_auc(yk[ok], oof[ok]) or 0
        best = C if best is None or cs[C] > cs[best] else best
    models = {"l1": ("clf", lambda: LogisticRegression(penalty="l1", C=best, solver="liblinear", class_weight="balanced")),
              "lgbm": ("clf", lambda: lgb.LGBMClassifier(n_estimators=300, learning_rate=0.02, num_leaves=4, min_child_samples=30, subsample=0.7,
                                                        subsample_freq=1, colsample_bytree=0.3, reg_lambda=5.0, random_state=0, verbose=-1)),
              "lgbm_reg": ("reg", lambda: lgb.LGBMRegressor(n_estimators=300, learning_rate=0.02, num_leaves=4, min_child_samples=30, subsample=0.7,
                                                           subsample_freq=1, colsample_bytree=0.3, reg_lambda=5.0, random_state=0, verbose=-1))}
    res["l1_C"] = cs
    for nm, (kind, ctor) in models.items():
        folds = K.time_folds(dk)
        oof = np.full(trm.sum(), np.nan)
        for i, t in enumerate(folds):
            trn = np.concatenate([folds[j] for j in range(len(folds)) if j != i])
            m = ctor().fit(X[trm][trn], (yk if kind == "clf" else nk)[trn])
            oof[t] = m.predict_proba(X[trm][t])[:, 1] if kind == "clf" else -m.predict(X[trm][t])
        m = ctor().fit(X[trm], yk if kind == "clf" else nk)
        p = m.predict_proba(X)[:, 1] if kind == "clf" else -m.predict(X)
        rec = {"kesif_oof_auc": K.safe_auc(yk, oof)}
        for q in (0.15, 0.30):
            th = float(np.quantile(oof, 1 - q))
            cell = {}
            for f in FEEDS:
                z = A[(A.besleme == f) & (A.donem == "TEST")]
                pv = p[z.index]
                ve = K.veto_eval(z, pv >= th)
                ve["auc"] = K.safe_auc(z.y.values, pv)
                cell[f] = ve
            days = pd.bdate_range("2021-11-01", "2026-11-05")
            z = A[(A.besleme == "MT5_NAS100") & (A.donem == "TEST")]
            keep = p[z.index] < th

            def sh(s):
                s = s.groupby(z.d).sum().reindex(days).fillna(0)
                return round(float(s.mean() / s.std() * np.sqrt(252)), 3)
            cell["sharpe_NAS100_TEST"] = {"vetosuz": sh(z.net), "vetolu": sh(z.net.where(keep, 0))}
            kor = sum(1 for f in ("MT5_US500", "MT5_US30", "MT5_US2000") if cell[f]["veto_ort"] is not None and cell[f]["veto_ort"] < cell[f]["kalan_ort"])
            n_, d_ = cell["MT5_NAS100"], cell["DUKA_NDX"]
            if (n_["veto_ort"] < 0 and (n_["P_veto_ort_eksi"] or 0) >= 0.9 and d_["veto_ort"] < 0 and (d_["P_veto_ort_eksi"] or 0) >= 0.9
                    and kor >= 2 and cell["sharpe_NAS100_TEST"]["vetolu"] > cell["sharpe_NAS100_TEST"]["vetosuz"]):
                h = "B"
            elif n_["veto_ort"] <= n_["kalan_ort"] - 15 and d_["veto_ort"] < d_["kalan_ort"]:
                h = "C"
            else:
                h = "X"
            cell["kor_yon"], cell["hukum"] = f"{kor}/3", h
            rec[f"veto_{int(q * 100)}"] = cell
            print(f"{nm} veto%{int(q*100)}: KEŞİF OOF {rec['kesif_oof_auc']} | NAS100 TEST AUC {n_['auc']} veto {n_['veto_ort']} vs {n_['kalan_ort']} "
                  f"P {n_['P_veto_ort_eksi']} | Duka {d_['auc']} {d_['veto_ort']} vs {d_['kalan_ort']} | kör {kor}/3 | Sharpe {cell['sharpe_NAS100_TEST']} → {h}", flush=True)
        if hasattr(m, "feature_importances_"):
            rec["onem"] = pd.Series(m.feature_importances_, index=feats).sort_values(ascending=False).head(12).to_dict()
        res[nm] = rec
    # 3. kümeleme
    XK = X[trm]
    pca = PCA(n_components=10, random_state=0).fit(XK)
    PK = pca.transform(XK)
    sil = {k: float(silhouette_score(PK, KMeans(k, n_init=10, random_state=0).fit_predict(PK))) for k in range(2, 7)}
    kb = max(sil, key=sil.get)
    km = KMeans(kb, n_init=10, random_state=0).fit(PK)
    lt = km.predict(pca.transform(X[te]))
    res["kume"] = [{"kume": c, "kesif_n": int((km.labels_ == c).sum()), "kesif_kayb": round(float(yk[km.labels_ == c].mean()), 3),
                    "kesif_ort": round(float(A.net.values[trm][km.labels_ == c].mean()), 1), "test_n": int((lt == c).sum()),
                    "test_kayb": round(float(A.y.values[te][lt == c].mean()), 3) if (lt == c).any() else None,
                    "test_ort": round(float(A.net.values[te][lt == c].mean()), 1) if (lt == c).any() else None} for c in range(kb)]
    print("kümeler:", res["kume"])
    (RES / "ksg_ayrim.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    ozellik() if sys.argv[1] == "ozellik" else analiz()
