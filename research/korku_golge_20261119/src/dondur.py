"""dondur.py — K1 + XP kaybeden vetosu (kanal ∪ GBM) nesnelerini YALNIZ KEŞİF verisiyle üretir ve dondurur.

Girdi: research/xp_kaybeden_20261119/results/ozellikler_kanal.parquet (117 özellik + z80 + net).
Çıktı: model/gbm_kesif.joblib, model/dondurulmus.json, results/yeniden_uretim.json.
python dondur.py
"""
from __future__ import annotations

import hashlib
import json
import platform
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import roc_auc_score

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]
SRC = ROOT / "research/xp_kaybeden_20261119"
sys.path.insert(0, str(SRC / "src"))
import analiz as A  # noqa: E402  (FEATS, imputed, veto_eval — aynı tanım)

MODEL_DIR, RES = HERE / "model", HERE / "results"
PRIM = A.PRIM
FEEDS = PRIM + ["DUKA_NDX"]
KESIF_SON = "2021-10-31"
GBM_PARAMS = dict(n_estimators=200, max_depth=2, learning_rate=0.05, subsample=0.8, random_state=0)
GBM_Q, KANAL_Q, KANAL_COL = 0.85, 0.20, "T_1sa_z"


def feed_stats(M: pd.DataFrame, feats: list[str]) -> dict:
    """Besleme başına KEŞİF medyan / ortalama / std (std=0 → 1), analiz.imputed ile aynı."""
    out = {}
    for f in FEEDS:
        ref = M[(M.besleme == f) & (M.donem == "KESIF")][feats]
        out[f] = {"med": ref.median().tolist(), "mu": ref.mean().tolist(), "sd": ref.std().replace(0, 1).tolist(),
                  "kanal_esik": float(M[(M.besleme == f) & (M.donem == "KESIF")][KANAL_COL].quantile(KANAL_Q))}
    return out


def transform(z: pd.DataFrame, st: dict, feats: list[str]) -> np.ndarray:
    med, mu, sd = (pd.Series(st[k], index=feats) for k in ("med", "mu", "sd"))
    return ((z[feats].astype(float).fillna(med) - mu) / sd).fillna(0).values


def stack(M: pd.DataFrame, era: str, st: dict, feats: list[str], feeds=PRIM) -> tuple[np.ndarray, pd.DataFrame]:
    zs = [M[(M.besleme == f) & (M.donem == era)] for f in feeds]
    return np.vstack([transform(z, st[f], feats) for z, f in zip(zs, feeds)]), pd.concat(zs)


def oof_threshold(XK: np.ndarray, zk: pd.DataFrame) -> tuple[float, float]:
    yk = zk.y.values
    folds = np.array_split(np.argsort(pd.to_datetime(zk.d).values), 5)
    oof = np.full(len(yk), np.nan)
    for i, te in enumerate(folds):
        tr = np.concatenate([folds[j] for j in range(5) if j != i])
        if yk[tr].sum() < 5:
            continue
        oof[te] = GradientBoostingClassifier(**GBM_PARAMS).fit(XK[tr], yk[tr]).predict_proba(XK[te])[:, 1]
    ok = np.isfinite(oof)
    return float(np.quantile(oof[ok], GBM_Q)), float(roc_auc_score(yk[ok], oof[ok]))


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def label(z: pd.DataFrame, p: np.ndarray, st: dict, thr: float) -> pd.DataFrame:
    kan = np.array([np.isfinite(v) and v <= st[f]["kanal_esik"] for v, f in zip(z[KANAL_COL].values, z.besleme.values)])
    return z.assign(p_gbm=p, veto_gbm=p >= thr, veto_kanal=kan, veto=(p >= thr) | kan)


def reproduce(L: pd.DataFrame) -> dict:
    """§2.99 sayılarıyla kıyas: GBM (80 / 1,005 / 0,719), birleşik (160 / 0,956 / 0,46)."""
    T = L[L.besleme.isin(PRIM) & (L.donem == "TEST")]
    D = L[(L.besleme == "DUKA_NDX") & (L.donem == "TEST")]
    out = {}
    for col in ("veto_gbm", "veto_kanal", "veto"):
        out[col] = {"MT5_HAVUZ": A.veto_eval(T, T[col].values), "DUKA_NDX": A.veto_eval(D, D[col].values),
                    "piyasa": {f: A.veto_eval(T[T.besleme == f], T[T.besleme == f][col].values) for f in PRIM}}
    g, u = out["veto_gbm"]["MT5_HAVUZ"], out["veto"]["MT5_HAVUZ"]
    out["kapi"] = {
        "gbm_80_1005_0719": g["veto_n"] == 80 and g["kar_orani"] == 1.005 and g["zarar_orani"] == 0.719,
        "birlesik_160_0956_046": u["veto_n"] == 160 and abs(u["kar_orani"] - 0.956) < 0.0015 and abs(u["zarar_orani"] - 0.46) < 0.005,
    }
    return out


def main() -> None:
    MODEL_DIR.mkdir(exist_ok=True)
    RES.mkdir(exist_ok=True)
    src = SRC / "results/ozellikler_kanal.parquet"
    M = pd.read_parquet(src)
    M["y"] = (M.net < 0).astype(int)
    M["ay_blok"] = pd.to_datetime(M.d).dt.to_period("M").astype(str)
    feats = list(A.FEATS)
    assert (M.d[M.donem == "KESIF"] <= pd.Timestamp(KESIF_SON)).all()
    st = feed_stats(M, feats)
    XK, zk = stack(M, "KESIF", st, feats)
    # analiz.imputed ile birebir aynı dönüşüm mü?
    XK_a = np.vstack([A.imputed(M[(M.besleme == f) & (M.donem == "KESIF")], M[(M.besleme == f) & (M.donem == "KESIF")]) for f in PRIM])
    assert np.allclose(XK, XK_a, equal_nan=True), "dönüşüm analiz.imputed'den farklı"
    thr, oof_auc = oof_threshold(XK, zk)
    gbm = GradientBoostingClassifier(**GBM_PARAMS).fit(XK, zk.y.values)
    joblib.dump(gbm, MODEL_DIR / "gbm_kesif.joblib")
    parts = []
    for f in FEEDS:
        z = M[M.besleme == f]
        parts.append(label(z, gbm.predict_proba(transform(z, st[f], feats))[:, 1], st, thr))
    L = pd.concat(parts)
    rep = reproduce(L)
    XT, zt = stack(M, "TEST", st, feats)
    rep["auc"] = {"kesif_oof": round(oof_auc, 3), "test_mt5": round(float(roc_auc_score(zt.y, gbm.predict_proba(XT)[:, 1])), 3)}
    meta = {"olusturma": "2026-11-19", "kaynak": str(src.relative_to(ROOT)), "kaynak_sha256": sha(src),
            "kesif_son": KESIF_SON, "egitim_beslemeleri": PRIM, "etiket": "net < 0", "gbm_params": GBM_PARAMS,
            "gbm_esik": thr, "gbm_esik_tanim": f"KEŞİF 5 kat zaman bloklu OOF %{int(GBM_Q * 100)}'liği",
            "kanal_ozellik": KANAL_COL, "kanal_tanim": "son 80 adet 1 sa kapanış (15:00 mumu dahil) regresyon kalıntı z'si",
            "kanal_q": KANAL_Q, "ozellikler": feats, "besleme_istatistik": st,
            "model_sha256": sha(MODEL_DIR / "gbm_kesif.joblib"),
            "surumler": {"python": platform.python_version(), "sklearn": sklearn.__version__, "numpy": np.__version__,
                         "pandas": pd.__version__, "joblib": joblib.__version__},
            "ileri_baslangic": "2026-11-06"}
    (MODEL_DIR / "dondurulmus.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False))
    (RES / "yeniden_uretim.json").write_text(json.dumps(rep, indent=1, ensure_ascii=False, default=str))
    L[["besleme", "d", "donem", "net", KANAL_COL, "p_gbm", "veto_gbm", "veto_kanal", "veto"]].to_csv(RES / "tarihsel_etiketler.csv", index=False)
    print("GBM eşik", round(thr, 4), "AUC", rep["auc"])
    for col in ("veto_gbm", "veto_kanal", "veto"):
        print(col, rep[col]["MT5_HAVUZ"], "| Duka", rep[col]["DUKA_NDX"])
    print("kapı", rep["kapi"])


if __name__ == "__main__":
    main()
