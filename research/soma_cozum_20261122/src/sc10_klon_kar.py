"""SC-10 — SC-08 model ateşlemelerinin kârı (PROTOCOL.md SC-10). SC08_AN=son ile koşulur."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("SC08_AN", "son")
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sc03_itki as I  # noqa: E402
import sc08_kural as K  # noqa: E402
import sc08_model as SM  # noqa: E402
import sc08_ozellik as F  # noqa: E402
import sc_degerlendir as D  # noqa: E402
import sc_ozellik as F1  # noqa: E402
import sc_veri as V  # noqa: E402

KOK = Path(__file__).resolve().parents[1]
Q = 0.998
TS = [60, 240, 480]


def skorla(M: F.Motor, model, oz, a: str, b: str) -> pd.DataFrame:
    j = np.flatnonzero((M.bar.t >= D.ts(a)) & (M.bar.t < D.ts(b)))
    j = j[j > 2000]
    e1440 = pd.Series(M.bar.c).ewm(span=1440, adjust=False).mean().to_numpy()
    y = np.where(M.bar.c[j] > e1440[j], 1, -1)
    sk = np.empty(len(j))
    for s in range(0, len(j), 100_000):
        jj = j[s:s + 100_000]
        X = M.ozellik(jj, M.bar.c[jj], y[s:s + 100_000], M.bar.t[jj] + 60)
        sk[s:s + 100_000] = model.predict_proba(X[oz].to_numpy(np.float32))[:, 1]
    return pd.DataFrame({"j": j, "t": M.bar.t[j] + 60, "y": y, "skor": sk})


def main() -> None:
    X = pd.read_parquet(KOK / "results" / "sc08_matris_son.parquet")
    oz = SM.ozellik_listesi(X)
    tr = X[(X["bolum"] == "KESIF") & X["hesap"].isin(["2268766", "karsi"])]
    model = HistGradientBoostingClassifier(max_depth=4, max_iter=300, learning_rate=0.05, class_weight="balanced",
                                           l2_regularization=1.0, random_state=0).fit(tr[oz].to_numpy(np.float32),
                                                                                       (tr["hesap"] == "2268766").to_numpy())
    G0 = pd.read_parquet(KOK / "results" / "sc08_skor_son.parquet").assign(t=lambda d: d["t"] + 60)
    kesim = X.loc[(X.hesap == "2268766") & (X.bolum == "ILERI"), "t_giris"].min()
    esik = float(np.quantile(G0.loc[G0.t < kesim, "skor"], Q))
    K.SOGUMA = 0
    bar = V.barlar()
    oz1 = F1.hesapla(bar)
    rng = np.random.default_rng(D.TOHUM)
    donemler = {"HESAP_ILERI": None, "GELISTIRME": ("2018-01-01", "2022-01-01")}
    sonuc = {"esik": esik}
    for ad, aralik in donemler.items():
        if aralik is None:
            G = G0[G0.t >= kesim]
        else:
            M = F.yukle("2017-01-01")
            G = skorla(M, model, oz, *aralik)
        A = K.ateslemeler(G.assign(ok=G.skor >= esik))
        k = np.searchsorted(bar.t, A["t"].to_numpy() - 60)          # kararın verildiği dakika barı (tam bar dizisinde)
        y = A["y"].to_numpy().astype(np.int32)
        dm = (bar.t >= A["t"].min() - 86400) & (bar.t <= A["t"].max() + 86400)
        tabanlar = [I.taban_k(bar, oz1, k, dm, rng) for _ in range(5)]
        for T in TS:
            r = I.zaman_sim(bar, k, y, T)
            rs = I.zaman_sim(bar, k, y, T, sk=1.5)
            tb = np.mean([I.zaman_sim(bar, kk, yy, T)["bp"].to_numpy() for kk, yy in tabanlar], axis=0)
            o = D.ozet(r)
            kay = {**o, "taban": round(float(tb.mean()), 3), "fark": round(float(r["bp"].mean() - tb.mean()), 3),
                   "fark_P": round(D.fark_P(r["bp"].to_numpy(), tb, r["t0"].to_numpy() // 86400), 4),
                   "stres": round(float(rs["bp"].mean()), 3), "tek_poz": round(float(D.tek_pozisyon(r)["bp"].mean()), 3),
                   "gunluk_ates": round(len(A) / max((A.t.max() - A.t.min()) / 86400 * 5 / 7, 1), 2)}
            sonuc[f"{ad}_T{T}"] = kay
            D.kaydet("SC-10", "HESAP" if ad == "HESAP_ILERI" else ad, {"T": T, "q": Q}, kay)
            print(ad, T, {kk: kay[kk] for kk in ("n", "ort_bp", "taban", "fark", "fark_P", "yari1", "yari2", "stres", "tek_poz", "yillik", "gunluk_ates")})
    b = sonuc["GELISTIRME_T240"]
    sonuc["hukum"] = "B" if (b["ort_bp"] > 0 and b["fark"] > 0 and b["fark_P"] >= 0.95 and b["yari1"] > 0 and b["yari2"] > 0
                             and b["stres"] > 0) else "X"
    print("HÜKÜM:", sonuc["hukum"])
    (KOK / "results" / "sc10_sonuc.json").write_text(json.dumps(sonuc, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
