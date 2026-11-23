"""SC-08 — okunabilir "kanal sınırı + M1 itki" kuralı. Eşikler YALNIZ KEŞİF Soma girişlerinden (alt sınır p10, üst sınır p95).
Ölçüm dakika kapanışında (1 dk gecikmeli klon). Ateşleme = kural doğru ∧ önceki dakika yanlış, soğuma SC08_SOGUMA sn.
Not: özellik seçimi model önemine (İLERİ permütasyonu) bakılarak yapıldı → İLERİ hafif kirli; CWDT yarı bağımsız tekrar.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sc08_kural as K  # noqa: E402
import sc08_ozellik as F  # noqa: E402
import sc_degerlendir as D  # noqa: E402

KOK = Path(__file__).resolve().parents[1]
ALT = ["H4_a_kir20", "H1_a_kir55", "SV_gun_konum", "M1_c_govde", "D1_a_stoch", "M15_a_ema20"]
UST = ["H4_a_kir20", "H1_adx"]


def esikler(X: pd.DataFrame, q_alt: float, q_ust: float) -> list[tuple[str, str, float]]:
    P = X[(X.hesap == "2268766") & (X.bolum == "KESIF")]
    return [(c, "≥", float(P[c].quantile(q_alt))) for c in ALT] + [(c, "≤", float(P[c].quantile(q_ust))) for c in UST]


def izgara_son(M: F.Motor, kural) -> pd.DataFrame:
    a, b = D.DONEM["HESAP"]
    j = np.flatnonzero((M.bar.t >= D.ts(a)) & (M.bar.t < D.ts(b)))
    j = j[j > 2000]
    e1440 = pd.Series(M.bar.c).ewm(span=1440, adjust=False).mean().to_numpy()
    e240 = pd.Series(M.bar.c).ewm(span=240, adjust=False).mean().to_numpy()
    y = np.where(M.bar.c[j] > e1440[j], 1, -1)
    trend_ok = np.sign(M.bar.c[j] - e240[j]) == y
    parca = []
    for s in range(0, len(j), 100_000):
        jj, yy = j[s:s + 100_000], y[s:s + 100_000]
        X = M.ozellik(jj, M.bar.c[jj], yy, M.bar.t[jj] + 60)
        ok = trend_ok[s:s + 100_000].copy()
        for c, yon, e in kural:
            v = X[c].to_numpy(float)
            ok &= (v >= e) if yon == "≥" else (v <= e)
        parca.append(pd.DataFrame({"j": jj, "t": M.bar.t[jj] + 60, "y": yy, "ok": ok}))
    return pd.concat(parca, ignore_index=True)


def main() -> None:
    X = pd.read_parquet(KOK / "results" / "sc08_matris_son.parquet")
    kesim = X.loc[(X.hesap == "2268766") & (X.bolum == "ILERI"), "t_giris"].min()
    M = F.yukle("2023-01-01")
    S, C = X[X.hesap == "2268766"], X[X.hesap == "2347514"]
    rows, kurallar = [], {}
    for q_alt, q_ust in ((0.05, 0.95), (0.10, 0.95), (0.15, 0.90), (0.20, 0.90)):
        kural = esikler(X, q_alt, q_ust)
        G = izgara_son(M, kural)
        for sog in (0, 600, 1800):
            K.SOGUMA = sog
            A = K.ateslemeler(G)
            r = {"q_alt": q_alt, "q_ust": q_ust, "soguma_dk": sog // 60}
            for ad, SS, mA in (("KESIF", S[S.t_giris < kesim], A.t < kesim), ("ILERI", S[S.t_giris >= kesim], A.t >= kesim),
                               ("CWDT_ILERI", C[C.t_giris >= kesim], A.t >= kesim)):
                Aa = A[mA & (A.t >= SS.t_giris.min() - 600) & (A.t <= SS.t_giris.max() + 600)]
                m = K.eslesme(Aa, SS)
                r.update({ad + "_yak": m["yakalama"], ad + "_kes": m["kesinlik"], ad + "_gun": m["ateslenen_gunluk"]})
            rows.append(r)
        kurallar[f"{q_alt}/{q_ust}"] = kural
    R = pd.DataFrame(rows)
    R["kesif_skor"] = R[["KESIF_yak", "KESIF_kes"]].min(axis=1)
    sec = R.loc[R["kesif_skor"].idxmax()]
    pd.set_option("display.width", 250)
    print(R.to_string(index=False))
    anahtar = f"{sec['q_alt']}/{sec['q_ust']}"
    print("\nKEŞİF'te seçilen:", anahtar, "soğuma", sec["soguma_dk"], "→ İLERİ", sec["ILERI_yak"], sec["ILERI_kes"],
          "| CWDT", sec["CWDT_ILERI_yak"], sec["CWDT_ILERI_kes"])
    for c, yon, e in kurallar[anahtar]:
        print(f"   {c} {yon} {e:.3f}")
    (KOK / "results" / "sc08_acik_kural.json").write_text(json.dumps(
        {"secim": sec.to_dict(), "kural": kurallar[anahtar], "tablo": rows}, indent=1, default=float, ensure_ascii=False))


if __name__ == "__main__":
    main()
