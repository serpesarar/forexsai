"""tur1.py — Gün/hafta imzası: 1993–2017 ETF çağında öğren, dondur, 2018–26 paket işlemlerinde (MT5 + Duka) kör sına.
python tur1.py
"""
from __future__ import annotations

import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression

import ortak as K

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parents[1]
RES = HERE / "results"
C = pd.read_parquet(RES / "cag_ozellik.parquet")
P = pd.read_parquet(RES / "paket_ozellik.parquet")
for z in (C, P):
    z["y"] = (z.net < 0).astype(int)
    z["y2"] = (z.net <= -150).astype(int)
VOL = ("volume_", "pvo")
FEATS = [c for c in C.columns if c[:2] in ("D_", "W_") and not any(v in c for v in VOL)
         and C[c].notna().mean() > 0.8 and C[c].nunique() > 2 and c in P.columns and P[c].notna().mean() > 0.8]
ETFS = sorted(C.besleme.unique())


def cag_parts(label: str) -> list:
    return [(K.standardize(C[C.besleme == s], C[C.besleme == s], FEATS), C[C.besleme == s][label].values) for s in ETFS]


def blind_matrix() -> tuple[np.ndarray, pd.DataFrame]:
    """Kör beslemeler kendi KEŞİF dönemi özellik dağılımıyla ölçeklenir (etiket kullanılmaz)."""
    Xs, zs = [], []
    for f in sorted(P.besleme.unique()):
        z = P[P.besleme == f]
        Xs.append(K.standardize(z, z[z.donem == "KESIF"], FEATS))
        zs.append(z)
    return np.vstack(Xs), pd.concat(zs)


def univariate(label: str) -> dict:
    parts = cag_parts(label)
    a = K.pooled_auc(parts)
    thr = K.fwer_threshold(parts, 1000)
    XB, ZB = blind_matrix()
    bparts = [(XB[(ZB.besleme == f).values], ZB[ZB.besleme == f][label].values) for f in K.MT5]
    ab = K.pooled_auc(bparts)
    dk = (ZB.besleme == "DUKA_NDX").values
    ad = K.auc_cols(XB[dk], ZB[dk][label].values)
    df = pd.DataFrame({"ozellik": FEATS, "cag_auc": a, "kor_mt5_auc": ab, "kor_duka_auc": ad})
    df["sapma"] = (df.cag_auc - 0.5).abs()
    df["kor_ayni_yon"] = np.sign(df.cag_auc - 0.5) == np.sign(df.kor_mt5_auc - 0.5)
    df = df.sort_values("sapma", ascending=False)
    gec = df[df.sapma >= thr]
    return {"ozellik_say": len(FEATS), "aile_esik": round(thr, 4), "esigi_gecen_say": len(gec),
            "esigi_gecen_kor_ayni_yon_%": round(float(gec.kor_ayni_yon.mean() * 100), 1) if len(gec) else None,
            "cag_kor_auc_korelasyon": round(float(np.corrcoef(df.cag_auc, df.kor_mt5_auc)[0, 1]), 3),
            "ilk25": df.head(25).round(3).to_dict("records")}


def models(label: str) -> dict:
    XC = np.vstack([K.standardize(C[C.besleme == s], C[C.besleme == s], FEATS) for s in ETFS])
    ZC = pd.concat([C[C.besleme == s] for s in ETFS])
    yc = ZC[label].values
    XB, ZB = blind_matrix()
    mk = {"l1_lojistik": lambda: LogisticRegression(penalty="l1", C=0.02, solver="liblinear", class_weight="balanced"),
          "gbm": lambda: GradientBoostingClassifier(n_estimators=200, max_depth=2, learning_rate=0.05, subsample=0.8, random_state=0)}
    out = {}
    for nm, ctor in mk.items():
        oof = K.oof_scores(ctor, XC, yc, ZC.d)
        ok = np.isfinite(oof)
        thr = float(np.quantile(oof[ok], 0.85))
        m = ctor().fit(XC, yc)
        pb = m.predict_proba(XB)[:, 1]
        rec = {"cag_oof_auc": K.safe_auc(yc[ok], oof[ok]), "esik": round(thr, 4),
               "kor_2018_26": K.blind_report(ZB, pb, thr, label),
               "kor_TEST": K.blind_report(ZB[ZB.donem == "TEST"], pb[(ZB.donem == "TEST").values], thr, label)}
        if nm == "l1_lojistik":
            co = pd.Series(m.coef_[0], index=FEATS)
            rec["katsayi"] = co[co != 0].sort_values(key=np.abs, ascending=False).head(20).round(3).to_dict()
        else:
            rec["onem"] = pd.Series(m.feature_importances_, index=FEATS).sort_values(ascending=False).head(20).round(3).to_dict()
        out[nm] = rec
    return out


def main() -> None:
    res = {"veri": {"cag_islem": len(C), "cag_kaybeden": int(C.y.sum()), "cag_ort": round(float(C.net.mean()), 1),
                    "cag_etf": C.groupby("besleme").net.agg(["size", "mean"]).round(1).to_dict(),
                    "paket_islem": len(P), "ozellik": len(FEATS)}}
    print(res["veri"], flush=True)
    for lab in ("y", "y2"):
        res[f"tek_{lab}"] = u = univariate(lab)
        print(f"[{lab}] eşik {u['aile_esik']} geçen {u['esigi_gecen_say']} kör aynı yön % {u['esigi_gecen_kor_ayni_yon_%']} "
              f"ÇAĞ↔kör AUC r {u['cag_kor_auc_korelasyon']}", flush=True)
        for r in u["ilk25"][:12]:
            print("   ", r)
        res[f"model_{lab}"] = mo = models(lab)
        for nm, r in mo.items():
            k, t = r["kor_2018_26"], r["kor_TEST"]
            print(f"  {nm}: ÇAĞ OOF {r['cag_oof_auc']} | kör MT5 AUC {k['MT5_HAVUZ']['auc']} Duka {k['DUKA_NDX']['auc']} "
                  f"piyasa>0,55 {k['auc_ust_055']}/4 | veto {k['MT5_HAVUZ']['veto_ort']} vs {k['MT5_HAVUZ']['kalan_ort']} "
                  f"kâr× {k['MT5_HAVUZ']['kar_x']} zarar× {k['MT5_HAVUZ']['zarar_x']} → {k['hukum']} | TEST {t['MT5_HAVUZ']['auc']} {t['hukum']}", flush=True)
        (RES / "tur1.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
