"""SC-08 — tüm çok zaman dilimli özelliklerle model (KEŞİF'te eğitim), tüm dakika ızgarasında ateşleme düzeyinde sınama.

Pozitif: Soma ilk bacak dakikaları (KEŞİF). Negatif: karşı küme (KEŞİF). Model HistGradientBoosting.
Eşik: KEŞİF ızgarasında günde ~1,5 ateşleme verecek skor (Soma ~0,9/gün). Ateşleme = eşiği yukarı kesme, 60 dk soğuma.
Çıktı: results/sc08_model.json, results/sc08_onem.csv, results/sc08_skor.parquet (ızgara skoru).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.inspection import permutation_importance
from sklearn.metrics import roc_auc_score

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sc08_kural as K  # noqa: E402
import sc08_ozellik as F  # noqa: E402
import sc_degerlendir as D  # noqa: E402

KOK = Path(__file__).resolve().parents[1]
HEDEF_GUNLUK = 1.5
import sc08_tarama as TR
EK = TR.EK


def ozellik_listesi(X: pd.DataFrame) -> list[str]:
    return [c for c in X.columns if c[:3] in ("M1_", "M5_", "M15", "M30", "H1_", "H4_", "D1_", "SV_", "HC_")
            or c in ("Z_saat", "Z_gun")]


def izgara_skor(M: F.Motor, model, oz: list[str]) -> pd.DataFrame:
    a, b = D.DONEM["HESAP"]
    j = np.flatnonzero((M.bar.t >= D.ts(a)) & (M.bar.t < D.ts(b)))
    j = j[j > 2000]
    e1440 = pd.Series(M.bar.c).ewm(span=1440, adjust=False).mean().to_numpy()
    kk = j if TR.AN == "son" else j - 1
    y = np.where(M.bar.c[kk] > e1440[kk], 1, -1)
    skor = np.empty(len(j))
    for s in range(0, len(j), 100_000):
        jj = j[s:s + 100_000]
        if TR.AN == "son":
            X = M.ozellik(jj, M.bar.c[jj], y[s:s + 100_000], M.bar.t[jj] + 60)
        else:
            X = M.ozellik(jj - 1, M.bar.o[jj], y[s:s + 100_000], M.bar.t[jj])
        skor[s:s + 100_000] = model.predict_proba(X[oz].to_numpy(np.float32))[:, 1]
    return pd.DataFrame({"j": j, "t": M.bar.t[j], "y": y, "skor": skor})


def main() -> None:
    X = pd.read_parquet(KOK / "results" / f"sc08_matris{EK}.parquet")
    oz = ozellik_listesi(X)
    tr = X[(X["bolum"] == "KESIF") & X["hesap"].isin(["2268766", "karsi"])]
    model = HistGradientBoostingClassifier(max_depth=4, max_iter=300, learning_rate=0.05, class_weight="balanced",
                                           l2_regularization=1.0, random_state=0)
    model.fit(tr[oz].to_numpy(np.float32), (tr["hesap"] == "2268766").to_numpy())
    te = X[(X["bolum"] == "ILERI") & X["hesap"].isin(["2268766", "karsi"])]
    auc = roc_auc_score(te["hesap"] == "2268766", model.predict_proba(te[oz].to_numpy(np.float32))[:, 1])
    te2 = X[(X["bolum"] == "ILERI") & X["hesap"].isin(["2347514", "karsi"])]
    auc2 = roc_auc_score(te2["hesap"] == "2347514", model.predict_proba(te2[oz].to_numpy(np.float32))[:, 1])
    pi = permutation_importance(model, te[oz].to_numpy(np.float32), (te["hesap"] == "2268766").to_numpy(),
                                scoring="roc_auc", n_repeats=3, random_state=0, max_samples=20000)
    onem = pd.DataFrame({"ozellik": oz, "onem": pi.importances_mean}).sort_values("onem", ascending=False)
    onem.to_csv(KOK / "results" / f"sc08_onem{EK}.csv", index=False)

    M = F.yukle("2023-01-01")
    G = izgara_skor(M, model, oz)
    G.to_parquet(KOK / "results" / f"sc08_skor{EK}.parquet")
    kesim = X.loc[(X["hesap"] == "2268766") & (X["bolum"] == "ILERI"), "t_giris"].min()
    gk = G[G["t"] < kesim]
    gun_k = (gk["t"].max() - gk["t"].min()) / 86400 * 5 / 7
    # eşik: KEŞİF'te günde HEDEF_GUNLUK ateşleme
    sonuc = {"AUC_ileri_soma": round(auc, 3), "AUC_ileri_cwdt": round(auc2, 3), "ozellik_n": len(oz)}
    en = None
    for q in np.linspace(0.990, 0.99995, 60):
        e = float(np.quantile(gk["skor"], q))
        A = K.ateslemeler(gk.assign(ok=gk["skor"] >= e))
        if en is None or abs(len(A) / gun_k - HEDEF_GUNLUK) < abs(en[1] - HEDEF_GUNLUK):
            en = (e, len(A) / gun_k)
    esik = en[0]
    sonuc["esik"] = esik
    A = K.ateslemeler(G.assign(ok=G["skor"] >= esik))
    for hesap in ("2268766", "2347514"):
        S = X[X["hesap"] == hesap]
        for bol, ms, ma in (("KESIF", S["t_giris"] < kesim, A["t"] < kesim), ("ILERI", S["t_giris"] >= kesim, A["t"] >= kesim)):
            Ss = S[ms]
            Aa = A[ma & (A["t"] >= Ss["t_giris"].min() - K.PENCERE) & (A["t"] <= Ss["t_giris"].max() + K.PENCERE)] if len(Ss) else A[:0]
            if len(Ss):
                sonuc[f"{hesap}_{bol}"] = K.eslesme(Aa, Ss)
    print(json.dumps(sonuc, indent=1, ensure_ascii=False))
    print(onem.head(25).to_string(index=False))
    (KOK / "results" / f"sc08_model{EK}.json").write_text(json.dumps(sonuc, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
