"""SC-08 — Soma giriş anı taraması (PROTOCOL.md SC-08).

Ölçüm anı her iki kümede AYNI: giriş dakikasının başı (son tamamlanmış 1m bar = giriş dakikasından önceki bar, anlık fiyat = giriş
dakikasının açılışı). Böylece "oluşan mum" özellikleri iki kümede eşit tanımlı.
Çıktı: results/sc08_matris.parquet, results/sc08_tekli.csv (KEŞİF), results/sc08_ozet.md
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sc08_ozellik as F  # noqa: E402
import sc_degerlendir as D  # noqa: E402
import sc_veri as V  # noqa: E402

KOK = Path(__file__).resolve().parents[1]
N_KARSI = 200_000
KESIF_PAY = 0.60
import os
AN = os.getenv("SC08_AN", "bas")  # "bas": dakika başı; "son": giriş dakikası kapanışı (1 dk gecikmeli klon)
EK = "" if AN == "bas" else "_son"


def pozitifler(M: F.Motor, hesap: str) -> pd.DataFrame:
    p = V.islemler(hesap, sessiz=True)
    a, b = D.DONEM["HESAP"]
    p = p[p["bar_var"] & (p["t_giris"] >= D.ts(a)) & (p["t_giris"] < D.ts(b))]
    ilk = p.sort_values("t_giris").groupby("sinyal").first().reset_index()
    dk = ilk["t_giris"].to_numpy() // 60 * 60
    j = np.searchsorted(M.bar.t, dk)                         # giriş dakikasının barı
    ok = (j < len(M.bar)) & (M.bar.t[np.minimum(j, len(M.bar) - 1)] == dk) & (j > 0)
    ilk, j = ilk[ok].reset_index(drop=True), j[ok]
    return pd.DataFrame({"k": j - 1, "j": j, "y": ilk["yon"].to_numpy(), "t_giris": ilk["t_giris"].to_numpy(),
                         "fiyat_bid": ilk["open_price"].to_numpy() - ilk["taban"].to_numpy()
                         - np.where(ilk["yon"] > 0, M.bar.s[j], 0.0),
                         "sinyal": ilk["sinyal"].to_numpy(), "bacak_n": p.groupby("sinyal").size().reindex(ilk["sinyal"]).to_numpy(),
                         "hesap": hesap})


def karsi(M: F.Motor, rng) -> pd.DataFrame:
    a, b = D.DONEM["HESAP"]
    aday = np.flatnonzero((M.bar.t >= D.ts(a)) & (M.bar.t < D.ts(b)))
    j = np.sort(rng.choice(aday[aday > 2000], N_KARSI, replace=False))
    e1440 = pd.Series(M.bar.c).ewm(span=1440, adjust=False).mean().to_numpy()
    kk = j if AN == "son" else j - 1
    y = np.where(M.bar.c[kk] > e1440[kk], 1, -1)
    return pd.DataFrame({"k": j - 1, "j": j, "y": y, "t_giris": M.bar.t[j], "hesap": "karsi"})


def matris(M: F.Motor, q: pd.DataFrame) -> pd.DataFrame:
    k, j = q["k"].to_numpy(), q["j"].to_numpy()
    if AN == "son":
        X = M.ozellik(j, M.bar.c[j], q["y"].to_numpy(), M.bar.t[j] + 60)
    else:
        X = M.ozellik(k, M.bar.o[j], q["y"].to_numpy(), M.bar.t[j])
    return pd.concat([q.reset_index(drop=True), X], axis=1)


def tekli(X: pd.DataFrame, oz: list[str]) -> pd.DataFrame:
    pos, neg = X[X["hesap"] == "2268766"], X[X["hesap"] == "karsi"]
    satir = []
    for c in oz:
        a, b = pos[c].to_numpy(float), neg[c].to_numpy(float)
        a, b = a[np.isfinite(a)], b[np.isfinite(b)]
        if len(a) < 50 or np.nanstd(b) == 0:
            continue
        auc = roc_auc_score(np.r_[np.ones(len(a)), np.zeros(len(b))], np.r_[a, b])
        if auc >= 0.5:
            esik = np.quantile(a, 0.05)
            gec = float((b >= esik).mean())
            yon = "≥"
        else:
            esik = np.quantile(a, 0.95)
            gec = float((b <= esik).mean())
            yon = "≤"
        satir.append({"ozellik": c, "AUC": round(max(auc, 1 - auc), 3), "yon": yon, "esik_p95kapsama": round(float(esik), 3),
                      "karsi_gecme": round(gec, 4), "kaldirac": round(0.95 / max(gec, 1e-6), 2),
                      "poz_p05": round(float(np.quantile(a, .05)), 2), "poz_med": round(float(np.median(a)), 2),
                      "poz_p95": round(float(np.quantile(a, .95)), 2), "karsi_med": round(float(np.median(b)), 2)})
    return pd.DataFrame(satir).sort_values("karsi_gecme")


def main() -> None:
    rng = np.random.default_rng(D.TOHUM)
    M = F.yukle("2023-01-01")
    poz = pd.concat([pozitifler(M, "2268766"), pozitifler(M, "2347514")], ignore_index=True)
    X = matris(M, pd.concat([poz, karsi(M, rng)], ignore_index=True))
    soma_t = np.sort(X.loc[X["hesap"] == "2268766", "t_giris"].to_numpy())
    kesim = soma_t[int(len(soma_t) * KESIF_PAY)]
    X["bolum"] = np.where(X["t_giris"] < kesim, "KESIF", "ILERI")
    X.to_parquet(KOK / "results" / f"sc08_matris{EK}.parquet")
    oz = [c for c in X.columns if c[:3] in ("M1_", "M5_", "M15", "M30", "H1_", "H4_", "D1_", "SV_", "Z_s", "Z_d", "Z_g", "HC_")]
    T = tekli(X[X["bolum"] == "KESIF"], oz)
    T.to_csv(KOK / "results" / f"sc08_tekli{EK}.csv", index=False)
    print("kesim", pd.to_datetime(kesim, unit="s"), "KEŞİF Soma", int(((X.hesap == "2268766") & (X.bolum == "KESIF")).sum()),
          "karşı", int(((X.hesap == "karsi") & (X.bolum == "KESIF")).sum()))
    pd.set_option("display.width", 250)
    print(T.head(60).to_string(index=False))


if __name__ == "__main__":
    main()
