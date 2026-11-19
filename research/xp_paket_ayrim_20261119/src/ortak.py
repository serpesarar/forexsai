"""ortak.py — standartlaştırma, AUC, permütasyon eşiği, veto değerlendirmesi ve hüküm (tüm turlar aynı)."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

MT5 = ["MT5_NAS100", "MT5_US500", "MT5_US30", "MT5_US2000"]
RNG = np.random.default_rng(19)


def standardize(z: pd.DataFrame, ref: pd.DataFrame, feats: list[str]) -> np.ndarray:
    """Referansın (yalnız özellik dağılımı, etiket yok) medyanıyla doldur, ortalama/std ile ölçekle."""
    med, mu, sd = ref[feats].median(), ref[feats].mean(), ref[feats].std().replace(0, 1).fillna(1)
    return ((z[feats].astype(float).fillna(med) - mu) / sd).fillna(0).clip(-8, 8).values


def auc_cols(X: np.ndarray, y: np.ndarray) -> np.ndarray:
    R = pd.DataFrame(X).rank().values
    n1, n0 = y.sum(), len(y) - y.sum()
    return (R[y == 1].sum(0) - n1 * (n1 + 1) / 2) / (n1 * n0)


def pooled_auc(parts: list[tuple[np.ndarray, np.ndarray]]) -> np.ndarray:
    w = np.array([y.sum() * (len(y) - y.sum()) for _, y in parts], float)
    return (np.array([auc_cols(X, y) for X, y in parts]) * w[:, None]).sum(0) / w.sum()


def fwer_threshold(parts, nperm: int = 1000) -> float:
    mx = [np.abs(pooled_auc([(X, RNG.permutation(y)) for X, y in parts]) - 0.5).max() for _ in range(nperm)]
    return float(np.quantile(mx, 0.95))


def veto_eval(z: pd.DataFrame, mask: np.ndarray) -> dict:
    net = z.net.values
    keep = ~mask
    base_tot, base_loss = net.sum(), net[net < 0].sum()
    v = net[mask]
    boot = []
    if mask.sum() >= 3:
        bl = pd.to_datetime(z.d).dt.to_period("M").astype(str).values[mask]
        ub = np.unique(bl)
        for _ in range(1000):
            pick = RNG.choice(ub, len(ub))
            boot.append(np.concatenate([v[bl == u] for u in pick]).mean())
    return {"n": int(len(z)), "veto_n": int(mask.sum()), "veto_ort": round(float(v.mean()), 1) if mask.any() else None,
            "kalan_ort": round(float(net[keep].mean()), 1) if keep.any() else None, "taban_ort": round(float(net.mean()), 1),
            "kar_x": round(float(net[keep].sum() / base_tot), 3) if base_tot else None,
            "zarar_x": round(float(net[keep][net[keep] < 0].sum() / base_loss), 3) if base_loss else None,
            "veto_kaybeden_%": round(float((v < 0).mean() * 100), 1) if mask.any() else None,
            "P_veto_ort_eksi": round(float((np.array(boot) < 0).mean()), 3) if boot else None}


def safe_auc(y, p) -> float | None:
    return round(float(roc_auc_score(y, p)), 3) if 0 < y.sum() < len(y) else None


def blind_report(Z: pd.DataFrame, p: np.ndarray, thr: float, label: str = "y") -> dict:
    """Kör küme: MT5 havuzu + piyasa piyasa + Duka; AUC ve veto."""
    Z = Z.assign(_p=p)
    out = {"piyasa": {}}
    m = Z[Z.besleme.isin(MT5)]
    out["MT5_HAVUZ"] = {"auc": safe_auc(m[label].values, m._p.values), **veto_eval(m, (m._p >= thr).values)}
    for f in MT5 + ["DUKA_NDX"]:
        a = Z[Z.besleme == f]
        if len(a):
            out["piyasa"][f] = {"auc": safe_auc(a[label].values, a._p.values), **veto_eval(a, (a._p >= thr).values)}
    out["DUKA_NDX"] = out["piyasa"].get("DUKA_NDX")
    out["yon_tutan"] = sum(1 for f in MT5 if f in out["piyasa"] and out["piyasa"][f]["veto_ort"] is not None
                           and out["piyasa"][f]["kalan_ort"] is not None and out["piyasa"][f]["veto_ort"] < out["piyasa"][f]["kalan_ort"])
    out["auc_ust_055"] = sum(1 for f in MT5 if f in out["piyasa"] and (out["piyasa"][f]["auc"] or 0) > 0.55)
    out["hukum"] = verdict(out)
    return out


def verdict(r: dict) -> dict:
    p, d = r["MT5_HAVUZ"], r["DUKA_NDX"] or {}
    ayr = (p["auc"] or 0) >= 0.62 and r["auc_ust_055"] >= 3 and (d.get("auc") or 0) >= 0.60
    duka_yon = d.get("veto_ort") is not None and d.get("kalan_ort") is not None and d["veto_ort"] < d["kalan_ort"]
    if p["veto_n"] < 5:
        v = "yetersiz"
    elif (p["veto_ort"] < 0 and (p["P_veto_ort_eksi"] or 0) >= 0.9 and p["kar_x"] >= 0.95 and p["zarar_x"] <= 0.80
          and r["yon_tutan"] >= 3 and duka_yon):
        v = "B"
    elif p["kalan_ort"] is not None and p["veto_ort"] <= p["kalan_ort"] - 30 and r["yon_tutan"] >= 3:
        v = "C"
    else:
        v = "X"
    return {"ayrisma": bool(ayr), "veto": v}


def time_folds(dates: pd.Series, k: int = 5) -> list[np.ndarray]:
    return np.array_split(np.argsort(pd.to_datetime(dates).values, kind="stable"), k)


def oof_scores(ctor, X: np.ndarray, y: np.ndarray, dates: pd.Series) -> np.ndarray:
    folds = time_folds(dates)
    oof = np.full(len(y), np.nan)
    for i, te in enumerate(folds):
        tr = np.concatenate([folds[j] for j in range(len(folds)) if j != i])
        if y[tr].sum() >= 5:
            oof[te] = ctor().fit(X[tr], y[tr]).predict_proba(X[te])[:, 1]
    return oof
