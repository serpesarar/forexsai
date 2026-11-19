"""tur23.py — Tur 2 (gün içi 30 dk–4 sa + gün/hafta, MT5 KEŞİF → TEST) ve Tur 3 (+ XK'nin 117 özelliği). Kümeleme dahil.
python tur23.py
"""
from __future__ import annotations

import json
import warnings
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import silhouette_score

import ortak as K

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]
RES = HERE / "results"
P = pd.read_parquet(RES / "paket_ozellik.parquet")
XK = pd.read_parquet(ROOT / "research/xp_kaybeden_20261119/results/ozellikler_kanal.parquet")
OLD = [c for c in XK.columns if c[:2] in ("m3", "h1", "U_", "F_", "D_", "S_", "T_", "H_", "X_") or c in (
    "gun_ret", "seans_ret", "son_saat", "son_yarim", "ilk_yarim_saat", "twap_uz", "bosluk", "aralik", "kapanis_konum", "dip_saati", "r5",
    "r20", "rsi2", "sma20_uz", "sma50_uz", "sma200_uz", "rv20", "aralik_oran", "zirve_uz", "vix", "vix_deg", "vix_vix3m",
    "qqq_hacim_oran", "mt5_hacim_oran", "gun", "ay", "opex_k", "opex_a", "olay", "sess_dun", "K1_dun", "K1_son10")]
XK = XK[["besleme", "d"] + OLD].rename(columns={c: "XK_" + c for c in OLD})
P = P.merge(XK, on=["besleme", "d"], how="left")
P["y"] = (P.net < 0).astype(int)
P["y2"] = (P.net <= -150).astype(int)


def feats_for(tur: int) -> list[str]:
    pre = ("m30_", "h1_", "h2_", "h4_", "D_", "W_", "H_") + (("XK_",) if tur == 3 else ())
    f = [c for c in P.columns if c.startswith(pre)]
    m = P[P.besleme.isin(K.MT5) & (P.donem == "KESIF")]
    return [c for c in f if m[c].notna().mean() > 0.7 and m[c].nunique() > 2]


def mats(feats, era, feeds=K.MT5):
    Xs, zs = [], []
    for f in feeds:
        z = P[(P.besleme == f) & (P.donem == era)]
        if len(z):
            Xs.append(K.standardize(z, P[(P.besleme == f) & (P.donem == "KESIF")], feats))
            zs.append(z)
    return np.vstack(Xs), pd.concat(zs)


def univariate(feats, label) -> dict:
    parts = []
    for f in K.MT5:
        X, z = mats(feats, "KESIF", [f])
        parts.append((X, z[label].values))
    a = K.pooled_auc(parts)
    thr = K.fwer_threshold(parts, 1000)
    tparts = []
    for f in K.MT5:
        X, z = mats(feats, "TEST", [f])
        tparts.append((X, z[label].values))
    at = K.pooled_auc(tparts)
    XD, ZD = mats(feats, "TEST", ["DUKA_NDX"])
    ad = K.auc_cols(XD, ZD[label].values)
    df = pd.DataFrame({"ozellik": feats, "kesif_auc": a, "test_auc": at, "duka_test_auc": ad})
    df["sapma"] = (df.kesif_auc - 0.5).abs()
    df["test_ayni_yon"] = np.sign(df.kesif_auc - 0.5) == np.sign(df.test_auc - 0.5)
    df = df.sort_values("sapma", ascending=False)
    gec = df[df.sapma >= thr]
    # TEST'te en güçlü (bilgi amaçlı, seçim değil): KEŞİF yönüyle tutarlı olanlar
    tt = df.assign(ts=(df.test_auc - 0.5).abs()).sort_values("ts", ascending=False)
    return {"ozellik_say": len(feats), "aile_esik": round(thr, 4), "esigi_gecen": gec.ozellik.tolist(),
            "esigi_gecen_test_ayni_yon_%": round(float(gec.test_ayni_yon.mean() * 100), 1) if len(gec) else None,
            "kesif_test_auc_r": round(float(np.corrcoef(df.kesif_auc, df.test_auc)[0, 1]), 3),
            "ilk20_test_ayni_yon_%": round(float(df.head(20).test_ayni_yon.mean() * 100), 1),
            "ilk25": df.head(25).round(3).to_dict("records"),
            "test_en_guclu_bilgi": tt.head(15).round(3).to_dict("records")}


def models(feats, label) -> dict:
    XK_, zk = mats(feats, "KESIF")
    XT, zt = mats(feats, "TEST", K.MT5 + ["DUKA_NDX"])
    yk = zk[label].values
    mk = {"l1_lojistik": lambda: LogisticRegression(penalty="l1", C=0.02, solver="liblinear", class_weight="balanced"),
          "gbm": lambda: GradientBoostingClassifier(n_estimators=200, max_depth=2, learning_rate=0.05, subsample=0.8, random_state=0),
          "lgbm": lambda: lgb.LGBMClassifier(n_estimators=300, learning_rate=0.02, num_leaves=4, min_child_samples=20, subsample=0.7,
                                             subsample_freq=1, colsample_bytree=0.3, reg_lambda=5.0, random_state=0, verbose=-1)}
    out = {}
    for nm, ctor in mk.items():
        oof = K.oof_scores(ctor, XK_, yk, zk.d)
        ok = np.isfinite(oof)
        thr = float(np.quantile(oof[ok], 0.85))
        m = ctor().fit(XK_, yk)
        pt = m.predict_proba(XT)[:, 1]
        rec = {"kesif_oof_auc": K.safe_auc(yk[ok], oof[ok]), "esik": round(thr, 4), "TEST": K.blind_report(zt, pt, thr, label)}
        if hasattr(m, "coef_"):
            co = pd.Series(m.coef_[0], index=feats)
            rec["katsayi"] = co[co != 0].sort_values(key=np.abs, ascending=False).head(20).round(3).to_dict()
        else:
            rec["onem"] = pd.Series(m.feature_importances_, index=feats).sort_values(ascending=False).head(20).round(4).to_dict()
        out[nm] = rec
    return out


def cluster(feats) -> dict:
    XK_, zk = mats(feats, "KESIF")
    XT, zt = mats(feats, "TEST")
    pca = PCA(n_components=10, random_state=0).fit(XK_)
    PK, PT = pca.transform(XK_), pca.transform(XT)
    sil = {k: float(silhouette_score(PK, KMeans(k, n_init=20, random_state=0).fit_predict(PK))) for k in range(2, 7)}
    kb = max(sil, key=sil.get)
    km = KMeans(kb, n_init=20, random_state=0).fit(PK)
    lk, lt = km.labels_, km.predict(PT)
    rows = [{"kume": c, "kesif_n": int((lk == c).sum()), "kesif_kayb_%": round(float(zk.y.values[lk == c].mean() * 100), 1),
             "kesif_ort": round(float(zk.net.values[lk == c].mean()), 1), "test_n": int((lt == c).sum()),
             "test_kayb_%": round(float(zt.y.values[lt == c].mean() * 100), 1) if (lt == c).any() else None,
             "test_ort": round(float(zt.net.values[lt == c].mean()), 1) if (lt == c).any() else None} for c in range(kb)]
    # yalnız kaybedenlerin kümelenmesi: kaybeden alt tipleri girişte ayrı bölgede mi? (k=2..5, merkezlere uzaklıkla tüm işlemleri sınıfla)
    L = XK_[zk.y.values == 1]
    sl = {k: float(silhouette_score(L, KMeans(k, n_init=20, random_state=0).fit_predict(L))) for k in range(2, 6)}
    kl = max(sl, key=sl.get)
    kml = KMeans(kl, n_init=20, random_state=0).fit(L)
    W = XK_[zk.y.values == 0]
    dl = np.min(kml.transform(L), 1)
    dw = np.min(kml.transform(W), 1)
    rad = float(np.quantile(dl, 0.5))
    tin = np.min(kml.transform(XT), 1) <= rad
    return {"siluet": {k: round(v, 3) for k, v in sil.items()}, "k": kb, "kumeler": rows,
            "kaybeden_alt_tip_k": kl, "kesif_kazanan_kaybeden_bolgesinde_%": round(float((dw <= rad).mean() * 100), 1),
            "test_bolge_ici": K.veto_eval(zt, tin)}


def main() -> None:
    res = {}
    for tur in (2, 3):
        feats = feats_for(tur)
        res[f"tur{tur}"] = R = {"ozellik_say": len(feats)}
        print(f"=== Tur {tur}: {len(feats)} özellik", flush=True)
        for lab in ("y", "y2"):
            R[f"tek_{lab}"] = u = univariate(feats, lab)
            print(f"[{lab}] eşik {u['aile_esik']} geçen {len(u['esigi_gecen'])} {u['esigi_gecen'][:6]} TEST aynı yön % "
                  f"{u['esigi_gecen_test_ayni_yon_%']} | KEŞİF↔TEST r {u['kesif_test_auc_r']} ilk20 aynı yön % {u['ilk20_test_ayni_yon_%']}", flush=True)
            for r in u["ilk25"][:8]:
                print("   ", {k: r[k] for k in ("ozellik", "kesif_auc", "test_auc", "duka_test_auc")})
            R[f"model_{lab}"] = mo = models(feats, lab)
            for nm, r in mo.items():
                t = r["TEST"]
                print(f"  {nm}: KEŞİF OOF {r['kesif_oof_auc']} | TEST MT5 AUC {t['MT5_HAVUZ']['auc']} Duka {t['DUKA_NDX']['auc']} "
                      f">0,55 {t['auc_ust_055']}/4 | veto {t['MT5_HAVUZ']['veto_ort']} vs {t['MT5_HAVUZ']['kalan_ort']} kâr× "
                      f"{t['MT5_HAVUZ']['kar_x']} zarar× {t['MT5_HAVUZ']['zarar_x']} → {t['hukum']}", flush=True)
        R["kume"] = c = cluster(feats)
        print("  küme:", c["kumeler"], "| kaybeden bölgesinde kazanan %", c["kesif_kazanan_kaybeden_bolgesinde_%"], "TEST bölge içi", c["test_bolge_ici"], flush=True)
        (RES / "tur23.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
