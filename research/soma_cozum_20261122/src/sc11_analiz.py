"""SC-11 — tik düzeyinde son seçim: özellik pencereleri, ayrım (KEŞİF), açgözlü tetik, İLERİ taraması (PROTOCOL SC-11 + ekler).

Adımlar (env SC11_ADIM): pencere → results/sc11_pencere.parquet; analiz → results/sc11_sonuc.json, sc11_tekli.csv.
Saatler: Soma/CWDT girişleri sc11_saat.json'daki ay L'siyle Duka saatine çevrilir (t_d = t + L).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sc08_kural as K  # noqa: E402
import sc08_ozellik as F  # noqa: E402
import sc11_saat as SA  # noqa: E402
import sc11_tik_ozellik as O  # noqa: E402
import sc_degerlendir as D  # noqa: E402
import sc_tick as TK  # noqa: E402

KOK = Path(__file__).resolve().parents[1]
R = KOK / "results"
PEN = 600
N_ORNEK = 5
KAPSAMA_MIN = 0.80
AUC_MIN = 0.60
QS = (0.02, 0.05, 0.10, 0.15, 0.20)
MAKS_KOSUL = 4


def olaylar_d() -> pd.DataFrame:
    E = TK.olaylar().copy()
    saat = json.loads((R / "sc11_saat.json").read_text())
    E["t_d"] = E["t"]
    for h in ("2268766", "2347514"):
        m = E["hesap"] == h
        E.loc[m, "t_d"] = E.loc[m, "t"] + SA.L_ay(saat[h], E.loc[m, "t"].to_numpy())
    E["olay"] = np.arange(len(E))
    return E


def _var(a: int, b: int) -> bool:
    return all(TK.yol(h).exists() for h in range((a - O.GERI) // 3600 * 3600, b // 3600 * 3600 + 1, 3600))


def pencere_kur() -> None:
    E = olaylar_d()
    M = F.yukle("2024-06-01")
    parca, eksik = [], 0
    for r in E.itertuples():
        a, b = (r.t_d - PEN, r.t_d) if r.tur == "P" else (r.t_d - PEN, r.t_d + PEN)
        if not _var(a, b):
            eksik += 1
            continue
        X = O.pencere(M, int(a), int(b), int(r.y))
        X["olay"] = r.olay
        parca.append(X.astype({c: np.float32 for c in O.OZELLIKLER if c in X}))
    W = pd.concat(parca, ignore_index=True)
    G = pd.read_parquet(R / "sc08_skor_son.parquet")[["t", "skor"]]  # t = dakika başı, karar = t + 60
    W["skor"] = G.set_index("t")["skor"].reindex(W["s"] // 60 * 60 - 60).to_numpy(np.float32)
    W.to_parquet(R / "sc11_pencere.parquet")
    print("pencere satır", len(W), "olay", W["olay"].nunique(), "eksik saatli olay", eksik)


def ornekler(W: pd.DataFrame, E: pd.DataFrame, rng) -> pd.DataFrame:
    Ei = E.set_index("olay")
    W = W.join(Ei[["tur", "t_d", "y", "hesap", "bolum", "iska"]], on="olay")
    P = W[(W["tur"] == "P") & (W["s"] == W["t_d"])].assign(kume="P")
    n2 = W[(W["tur"] == "P") & (W["s"] <= W["t_d"] - 60)]
    N2 = n2.groupby("olay", group_keys=False).apply(lambda g: g.sample(min(N_ORNEK, len(g)), random_state=int(rng.integers(1e9))))
    n1 = W[(W["tur"] == "F") & (W["iska"] == True)]  # noqa: E712
    N1 = n1.groupby("olay", group_keys=False).apply(lambda g: g.sample(min(N_ORNEK, len(g)), random_state=int(rng.integers(1e9))))
    return pd.concat([P, N1.assign(kume="N1"), N2.assign(kume="N2")], ignore_index=True)


def tekli(S: pd.DataFrame, oz: list[str]) -> pd.DataFrame:
    pos = S[S["kume"] == "P"]
    satir = []
    for c in oz:
        a = pos[c].to_numpy(float)
        a = a[np.isfinite(a)]
        r = {"ozellik": c}
        for ad, neg in (("N", S[S["kume"] != "P"]), ("N1", S[S["kume"] == "N1"]), ("N2", S[S["kume"] == "N2"])):
            b = neg[c].to_numpy(float)
            b = b[np.isfinite(b)]
            if len(a) < 30 or len(b) < 30:
                continue
            auc = roc_auc_score(np.r_[np.ones(len(a)), np.zeros(len(b))], np.r_[a, b])
            r[f"AUC_{ad}"] = round(max(auc, 1 - auc), 3)
            if ad == "N":
                r["yon"] = "≥" if auc >= 0.5 else "≤"
                r["poz_med"], r["neg_med"] = round(float(np.median(a)), 3), round(float(np.median(b)), 3)
        satir.append(r)
    return pd.DataFrame(satir).sort_values("AUC_N", ascending=False)


def acgozlu(S: pd.DataFrame, T: pd.DataFrame) -> list[tuple[str, str, float]]:
    pos, neg = S[S["kume"] == "P"], S[S["kume"] != "P"]
    aday = T[T["AUC_N"] >= AUC_MIN]
    mp, mn = np.ones(len(pos), bool), np.ones(len(neg), bool)
    kural: list[tuple[str, str, float]] = []
    for _ in range(MAKS_KOSUL):
        en = None
        for _, r in aday.iterrows():
            c, yon = r["ozellik"], r["yon"]
            if any(c == k[0] for k in kural):
                continue
            a, b = pos[c].to_numpy(float), neg[c].to_numpy(float)
            for q in QS:
                esik = float(np.nanquantile(a[mp], q if yon == "≥" else 1 - q))
                ga, gb = (a >= esik, b >= esik) if yon == "≥" else (a <= esik, b <= esik)
                if (mp & ga).mean() < KAPSAMA_MIN:
                    continue
                skor = (mn & gb).mean()
                if en is None or skor < en[0]:
                    en = (skor, c, yon, esik)
        if en is None or (kural and en[0] > 0.97 * mn.mean()):
            break
        _, c, yon, esik = en
        kural.append((c, yon, esik))
        a, b = pos[c].to_numpy(float), neg[c].to_numpy(float)
        mp &= (a >= esik) if yon == "≥" else (a <= esik)
        mn &= (b >= esik) if yon == "≥" else (b <= esik)
        print(f"+ {c} {yon} {esik:.4f}  P kapsama %{mp.mean() * 100:.1f}  N geçme %{mn.mean() * 100:.2f}")
    return kural


def kural_ok(X: pd.DataFrame, kural: list) -> np.ndarray:
    ok = np.ones(len(X), bool)
    for c, yon, esik in kural:
        v = X[c].to_numpy(float)
        ok &= (v >= esik) if yon == "≥" else (v <= esik)
    return ok


def tara(W: pd.DataFrame, E: pd.DataFrame, ok: np.ndarray, nedensel: bool = True) -> pd.DataFrame:
    """Her F ateşlemesi en çok bir tetik: penceresinde (nedensel: [t, t+10 dk]) kuralın ilk doğru olduğu saniye."""
    Ef = E[E["tur"] == "F"].set_index("olay")
    W = W.assign(ok=ok).join(Ef[["t_d", "y"]], on="olay", how="inner")
    if nedensel:
        W = W[W["s"] >= W["t_d"]]
    W = W[W["ok"]]
    ilk = W.groupby("olay")["s"].min()
    return pd.DataFrame({"t": ilk.to_numpy(), "y": Ef.loc[ilk.index, "y"].to_numpy(), "olay": ilk.index.to_numpy()})


def degerlendir(A: pd.DataFrame, E: pd.DataFrame, kesim: int) -> dict:
    out = {}
    for ad, hesap, bol in (("KESIF", "2268766", "KESIF"), ("ILERI", "2268766", "ILERI"), ("CWDT_ILERI", "2347514", "ILERI")):
        S = E[(E["tur"] == "P") & (E["hesap"] == hesap) & (E["bolum"] == bol)]
        S = pd.DataFrame({"t_giris": S["t_d"].to_numpy(), "y": S["y"].to_numpy()})
        mA = (A["t"] >= kesim) if bol == "ILERI" else (A["t"] < kesim)
        Aa = A[mA & (A["t"] >= S["t_giris"].min() - K.PENCERE) & (A["t"] <= S["t_giris"].max() + K.PENCERE)]
        m = K.eslesme(Aa, S)
        dt = [np.min(np.abs(S["t_giris"].to_numpy()[S["y"].to_numpy() == y] - t)) for t, y in zip(Aa["t"], Aa["y"])
              if np.any((np.abs(S["t_giris"].to_numpy() - t) <= K.PENCERE) & (S["y"].to_numpy() == y))]
        m["medyan_dt_sn"] = float(np.median(dt)) if dt else None
        out[ad] = m
    return out


def model_egrisi(E: pd.DataFrame, kesim: int) -> dict:
    sonuc = {}
    for q in (0.995, 0.997, 0.998, 0.999, 0.9995):
        A = TK.ateslemeler(q)[["t", "y"]]
        sonuc[str(q)] = degerlendir(A, E, kesim)
    return sonuc


def analiz() -> None:
    E = olaylar_d()
    W = pd.read_parquet(R / "sc11_pencere.parquet")
    kesim = TK.kesim()
    rng = np.random.default_rng(D.TOHUM)
    S = ornekler(W, E, rng)
    Sk = S[S["bolum"] == "KESIF"]
    oz = O.OZELLIKLER
    T = tekli(Sk, oz)
    T.to_csv(R / "sc11_tekli.csv", index=False)
    pd.set_option("display.width", 250)
    print(T.to_string(index=False))
    kural = acgozlu(Sk, T)
    sonuc: dict = {"kural": kural, "n": S.groupby(["bolum", "kume"]).size().to_dict().__repr__()}
    sonuc["model_tek"] = model_egrisi(E, kesim)
    ok = kural_ok(W, kural)
    sonuc["kural_nedensel"] = degerlendir(tara(W, E, ok, True), E, kesim)
    sonuc["kural_pm10"] = degerlendir(tara(W, E, ok, False), E, kesim)
    # betimleyici: HistGB (tik + model skoru)
    oz2 = oz + ["skor"]
    hg = HistGradientBoostingClassifier(max_depth=3, max_iter=200, learning_rate=0.05, class_weight="balanced",
                                        l2_regularization=1.0, random_state=0)
    hg.fit(Sk[oz2].to_numpy(np.float32), (Sk["kume"] == "P").to_numpy())
    Si = S[S["bolum"] == "ILERI"]
    sonuc["hgb_AUC_ileri"] = round(float(roc_auc_score(Si["kume"] == "P", hg.predict_proba(Si[oz2].to_numpy(np.float32))[:, 1])), 3)
    p = hg.predict_proba(W[oz2].to_numpy(np.float32))[:, 1]
    en = None
    for q in (0.05, 0.10, 0.20, 0.30, 0.40, 0.50):
        e = float(np.quantile(hg.predict_proba(Sk.loc[Sk["kume"] == "P", oz2].to_numpy(np.float32))[:, 1], q))
        d = degerlendir(tara(W, E, p >= e, True), E, kesim)
        k = min(d["KESIF"]["yakalama"] or 0, d["KESIF"]["kesinlik"] or 0)
        if en is None or k > en[0]:
            en = (k, q, d)
    sonuc["hgb_nedensel"] = {"P_yuzdelik": en[1], **en[2]}
    print(json.dumps(sonuc, indent=1, ensure_ascii=False, default=str))
    (R / "sc11_sonuc.json").write_text(json.dumps(sonuc, indent=1, ensure_ascii=False, default=str))
    D.kaydet("SC-11", "HESAP", {"kural": kural}, {k: sonuc[k] for k in ("kural_nedensel", "hgb_nedensel")})


if __name__ == "__main__":
    {"pencere": pencere_kur, "analiz": analiz}[os.getenv("SC11_ADIM", sys.argv[1] if len(sys.argv) > 1 else "analiz")]()
