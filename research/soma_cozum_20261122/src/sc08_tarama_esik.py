"""SC-08 — model skoru üzerinde eşik × soğuma taraması; seçim KEŞİF'te min(yakalama, kesinlik) en büyük, İLERİ raporlanır."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sc08_kural as K  # noqa: E402
import sc08_tarama as TR  # noqa: E402

KOK = Path(__file__).resolve().parents[1]


def main() -> None:
    X = pd.read_parquet(KOK / "results" / f"sc08_matris{TR.EK}.parquet")
    G = pd.read_parquet(KOK / "results" / f"sc08_skor{TR.EK}.parquet")
    if TR.AN == "son":
        G = G.assign(t=G["t"] + 60)  # karar anı = dakika kapanışı
    kesim = X.loc[(X.hesap == "2268766") & (X.bolum == "ILERI"), "t_giris"].min()
    S, C = X[X.hesap == "2268766"], X[X.hesap == "2347514"]
    rows = []
    for q in (0.995, 0.997, 0.998, 0.999, 0.9995):
        e = float(np.quantile(G.skor[G.t < kesim], q))
        for sog in (0, 300, 600, 1800, 3600):
            K.SOGUMA = sog
            A = K.ateslemeler(G.assign(ok=G.skor >= e))
            r = {"q": q, "esik": e, "soguma_dk": sog // 60}
            for ad, SS, mA in (("KESIF", S[S.t_giris < kesim], A.t < kesim), ("ILERI", S[S.t_giris >= kesim], A.t >= kesim),
                               ("CWDT_ILERI", C[C.t_giris >= kesim], A.t >= kesim)):
                Aa = A[mA & (A.t >= SS.t_giris.min() - 600) & (A.t <= SS.t_giris.max() + 600)]
                m = K.eslesme(Aa, SS)
                r.update({ad + "_yak": m["yakalama"], ad + "_kes": m["kesinlik"], ad + "_gun": m["ateslenen_gunluk"]})
            rows.append(r)
    R = pd.DataFrame(rows)
    R["kesif_skor"] = R[["KESIF_yak", "KESIF_kes"]].min(axis=1)
    sec = R.loc[R["kesif_skor"].idxmax()]
    R.to_csv(KOK / "results" / f"sc08_esik_soguma{TR.EK}.csv", index=False)
    pd.set_option("display.width", 250)
    print(R.drop(columns="esik").to_string(index=False))
    print("\nKEŞİF'te seçilen:", sec[["q", "soguma_dk"]].to_dict(), "→ İLERİ yakalama", sec["ILERI_yak"], "kesinlik", sec["ILERI_kes"],
          "| CWDT", sec["CWDT_ILERI_yak"], sec["CWDT_ILERI_kes"])
    (KOK / "results" / f"sc08_secim{TR.EK}.json").write_text(json.dumps(sec.to_dict(), indent=1, default=float))


if __name__ == "__main__":
    main()
