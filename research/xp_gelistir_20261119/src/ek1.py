import json
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
import kural as KR
HERE = Path(__file__).resolve().parents[1]
D = KR.D.copy()
FE = ["gun_ret", "seans_ret", "son_saat", "son_yarim", "ilk_yarim_saat", "twap_uz", "bosluk", "aralik", "kapanis_konum", "dip_saati", "r5", "r20",
      "rsi2", "sma20_uz", "sma50_uz", "sma200_uz", "rv20", "aralik_oran", "zirve_uz", "vix", "vix_deg", "vix_vix3m", "qqq_hacim_oran", "gun",
      "opex_k", "opex_a", "olay", "sess_dun", "K1_dun", "K1_son10"]
for c in FE: D[c] = D[c].astype(float)
def m_(v, w, d):
    vv = v * w; eq = pd.Series(vv, index=pd.to_datetime(d)).sort_index().cumsum()
    return {"toplam": float(vv.sum()), "zarar": float(vv[vv < 0].sum()), "DD": float((eq - eq.cummax()).min()), "n": int((w > 0).sum())}
def rel(m, b):
    return {"kar×": round(m["toplam"] / b["toplam"], 2), "zarar×": round(m["zarar"] / b["zarar"], 2), "DD×": round(m["DD"] / b["DD"], 2), "n": m["n"]}
out = {}
# (a) seri kuralları — her besleme kendi sırasıyla
for f in ["DUKA_NDX", "MT5_NAS100", "MT5_US500", "MT5_US30", "MT5_US2000"]:
    for e in ("KESIF", "TEST"):
        z = D[(D.besleme == f) & (D.donem == e)].sort_values("d").reset_index(drop=True)
        v = z.net.values; d = z.d.values; ex = z.cikis.values
        def prev_closed(i):  # i'nin girişinden önce kapanmış son işlemler
            return [j for j in range(i) if ex[j] < d[i]]
        w1 = np.ones(len(z)); w2 = np.ones(len(z)); w3 = np.ones(len(z))
        for i in range(len(z)):
            pc = prev_closed(i)
            if pc and v[pc[-1]] < 0: w1[i] = 0.5; w2[i] = 0.0
            if len(pc) >= 3 and v[pc[-3:]].sum() < 0: w3[i] = 0.5
        b = m_(v, np.ones(len(z)), d)
        out[f"seri_{f}_{e}"] = {"S1_yarim": rel(m_(v, w1, d), b), "S2_atla": rel(m_(v, w2, d), b), "S3_egri": rel(m_(v, w3, d), b)}
# (b) sınıflandırıcı
K = D[(D.donem == "KESIF") & D.besleme.isin(["DUKA_NDX", "MT5_US500", "MT5_US30", "MT5_US2000"])]
y = (K.net < 0).astype(int).values
models = {"lojistik": make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), LogisticRegression(C=0.3, max_iter=2000)),
          "gbm": make_pipeline(SimpleImputer(strategy="median"), GradientBoostingClassifier(max_depth=2, n_estimators=100, learning_rate=0.05, subsample=0.8, random_state=1))}
for mn, mdl in models.items():
    mdl.fit(K[FE].values, y)
    pk = mdl.predict_proba(K[FE].values)[:, 1]
    th80, th33, th67 = np.quantile(pk, 0.8), np.quantile(pk, 1 / 3), np.quantile(pk, 2 / 3)
    for f in ["DUKA_NDX", "MT5_NAS100", "MT5_US500", "MT5_US30", "MT5_US2000"]:
        z = D[(D.besleme == f) & (D.donem == "TEST")]
        p = mdl.predict_proba(z[FE].values)[:, 1]; v = z.net.values; d = z.d.values
        b = m_(v, np.ones(len(z)), d)
        wv = np.where(p > th80, 0.0, 1.0); ws = np.where(p > th67, 0.5, np.where(p < th33, 1.5, 1.0))
        auc_like = float(np.mean([(p[v < 0][:, None] > p[v > 0][None, :]).mean()])) if (v < 0).any() else None
        out[f"{mn}_{f}_TEST"] = {"veto_en_riskli_%20": rel(m_(v, wv, d), b), "lot_olasiliga_gore": rel(m_(v, ws, d), b), "AUC": round(auc_like, 3)}
(HERE / "results/ek1.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
for k, v in out.items(): print(k, v)
