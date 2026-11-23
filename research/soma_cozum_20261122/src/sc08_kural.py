"""SC-08 — zorunlu koşulların açgözlü birleşimi (KEŞİF) + tüm dakika ızgarasında ateşleme kesinliği/yakalaması (KEŞİF ve İLERİ).

Ateşleme: kural dakika başında doğru ∧ bir önceki dakikada yanlış (yükselen kenar), aynı yönde 60 dk soğuma.
Eşleşme: ateşleme ile Soma ilk bacağı arasında |Δt| ≤ 10 dk ve aynı yön.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sc08_ozellik as F  # noqa: E402
import sc_degerlendir as D  # noqa: E402
import sc_veri as V  # noqa: E402

KOK = Path(__file__).resolve().parents[1]
import os
KAPSAMA_MIN = float(os.getenv("SC08_KAPSAMA", "0.80"))
MAKS_KOSUL = int(os.getenv("SC08_MAKS", "8"))
QS = (0.02, 0.05, 0.10, 0.15, 0.20)
PENCERE = 600
SOGUMA = 3600


def acgozlu(X: pd.DataFrame, tekli: pd.DataFrame) -> list[tuple[str, str, float]]:
    pos = X[X["hesap"] == "2268766"]
    neg = X[X["hesap"] == "karsi"]
    aday = tekli[tekli["AUC"] >= 0.60]
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
                esik = np.nanquantile(a[mp], q if yon == "≥" else 1 - q)
                ga = (a >= esik) if yon == "≥" else (a <= esik)
                gb = (b >= esik) if yon == "≥" else (b <= esik)
                kap = (mp & ga).mean()
                if kap < KAPSAMA_MIN:
                    continue
                skor = (mn & gb).mean()
                if en is None or skor < en[0]:
                    en = (skor, c, yon, float(esik), kap)
        if en is None or (kural and en[0] > 0.97 * (mn.mean())):
            break
        skor, c, yon, esik, kap = en
        kural.append((c, yon, esik))
        a, b = pos[c].to_numpy(float), neg[c].to_numpy(float)
        mp &= (a >= esik) if yon == "≥" else (a <= esik)
        mn &= (b >= esik) if yon == "≥" else (b <= esik)
        print(f"+ {c} {yon} {esik:.3f}  kapsama %{mp.mean() * 100:.1f}  karşı geçme %{mn.mean() * 100:.3f}")
    return kural


def izgara(M: F.Motor, kural: list, donem: str = "HESAP") -> pd.DataFrame:
    """HESAP'ın TÜM dakikalarında kural değeri (dakika başı ölçümü, yön EMA1440)."""
    a, b = D.DONEM[donem]
    j = np.flatnonzero((M.bar.t >= D.ts(a)) & (M.bar.t < D.ts(b)))
    j = j[j > 2000]
    e1440 = pd.Series(M.bar.c).ewm(span=1440, adjust=False).mean().to_numpy()
    y = np.where(M.bar.c[j - 1] > e1440[j - 1], 1, -1)
    parca = []
    for s in range(0, len(j), 100_000):
        jj, yy = j[s:s + 100_000], y[s:s + 100_000]
        X = M.ozellik(jj - 1, M.bar.o[jj], yy, M.bar.t[jj])
        ok = np.ones(len(jj), bool)
        for c, yon, esik in kural:
            v = X[c].to_numpy(float)
            ok &= (v >= esik) if yon == "≥" else (v <= esik)
        parca.append(pd.DataFrame({"j": jj, "t": M.bar.t[jj], "y": yy, "ok": ok}))
    return pd.concat(parca, ignore_index=True)


def ateslemeler(G: pd.DataFrame) -> pd.DataFrame:
    onceki = np.r_[False, G["ok"].to_numpy()[:-1]]
    ard = np.r_[False, np.diff(G["j"].to_numpy()) == 1]
    kenar = G["ok"].to_numpy() & ~(onceki & ard)
    A = G[kenar]
    tut, son = [], {1: -10**12, -1: -10**12}
    for t, y in zip(A["t"].to_numpy(), A["y"].to_numpy()):
        tut.append(t - son[y] >= SOGUMA)
        if tut[-1]:
            son[y] = t
    return A[np.array(tut, bool)]


def eslesme(A: pd.DataFrame, S: pd.DataFrame) -> dict:
    ta, ya = A["t"].to_numpy(), A["y"].to_numpy()
    ts_, ys = S["t_giris"].to_numpy(), S["y"].to_numpy()
    yak = np.array([np.any((np.abs(ta - t) <= PENCERE) & (ya == y)) for t, y in zip(ts_, ys)])
    kes = np.array([np.any((np.abs(ts_ - t) <= PENCERE) & (ys == y)) for t, y in zip(ta, ya)])
    gun = max((S["t_giris"].max() - S["t_giris"].min()) / 86400, 1)
    return {"soma_n": len(S), "ateslenen": len(A), "yakalama": round(float(yak.mean()), 3) if len(yak) else None,
            "kesinlik": round(float(kes.mean()), 3) if len(kes) else None, "ateslenen_gunluk": round(len(A) / gun * 7 / 5, 2)}


def main() -> None:
    X = pd.read_parquet(KOK / "results" / "sc08_matris.parquet")
    tek = pd.read_csv(KOK / "results" / "sc08_tekli.csv")
    kural = acgozlu(X[X["bolum"] == "KESIF"], tek)
    M = F.yukle("2023-01-01")
    G = izgara(M, kural)
    A = ateslemeler(G)
    kesim = X.loc[(X["hesap"] == "2268766") & (X["bolum"] == "ILERI"), "t_giris"].min()
    sonuc = {"kural": kural}
    for hesap in ("2268766", "2347514"):
        S = X[X["hesap"] == hesap]
        for bol, m_s, m_a in (("KESIF", S["t_giris"] < kesim, A["t"] < kesim), ("ILERI", S["t_giris"] >= kesim, A["t"] >= kesim)):
            Ss, Aa = S[m_s], A[m_a & (A["t"] >= S["t_giris"].min() - PENCERE) & (A["t"] <= S["t_giris"].max() + PENCERE)]
            if len(Ss):
                sonuc[f"{hesap}_{bol}"] = eslesme(Aa, Ss)
    print(json.dumps(sonuc, indent=1, ensure_ascii=False, default=str))
    (KOK / "results" / "sc08_kural.json").write_text(json.dumps(sonuc, indent=1, ensure_ascii=False, default=str))
    A.to_parquet(KOK / "results" / "sc08_ateslemeler.parquet")


if __name__ == "__main__":
    main()
