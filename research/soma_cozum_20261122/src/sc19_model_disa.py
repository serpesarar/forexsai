"""SC-19b — E2X3 modelini canlıya aktar + canlı yapım paritesi.

1) Model (sc14_bakis.model_ve_esik, birebir) → yeni deneme/models/soma_e2_model.joblib {model, oz, esik, ...}.
2) Parite: canlı yapım = son 99.000 gerçek 1m + öncesi H1'den sentetik dakika (soma_e2x3_live.build_series) + yeni deneme/soma_motor.
   Araştırma = tam geçmişli Motor (C10.skorla). Pencerenin son 30 gününde AL ateşlemeleri (kenar, skor ≥ eşik) karşılaştırılır.
Çıktı: results/sc19_parite.json
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("SC08_AN", "son")
import joblib
import numpy as np
import pandas as pd
import sklearn

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sc08_ozellik as F  # noqa: E402
import sc10_klon_kar as C10  # noqa: E402
import sc14_bakis as B  # noqa: E402
import sc19_canli_kart as K19  # noqa: E402
import sc_veri as V  # noqa: E402

BOT = V.ROOT / "yeni deneme"
sys.path.insert(0, str(BOT))
import soma_e2x3_live as L  # noqa: E402
import soma_motor as SMO  # noqa: E402

R = Path(__file__).resolve().parents[1] / "results"
N_M1, GUN = 99_000, 30


def h1_topla(bar: V.Bar, vol: np.ndarray) -> dict:
    s = bar.t // 3600
    u, ilk = np.unique(s, return_index=True)
    son = np.r_[ilk[1:], len(s)] - 1
    return {"t": (u * 3600).astype(float), "o": bar.o[ilk], "h": np.maximum.reduceat(bar.h, ilk),
            "l": np.minimum.reduceat(bar.l, ilk), "c": bar.c[son], "v": np.add.reduceat(np.nan_to_num(vol), ilk)}


def parite(ad: str, M: F.Motor, mdl: dict) -> dict:
    bar, vol = M.bar, M.vol
    n = len(bar)
    a = n - N_M1
    m1 = {"t": bar.t[a:].astype(float), "o": bar.o[a:], "h": bar.h[a:], "l": bar.l[a:], "c": bar.c[a:], "v": np.nan_to_num(vol[a:])}
    h1 = h1_topla(bar.dilim(0, a), vol[:a])
    seri = L.build_series(m1, h1)
    nn = len(seri["t"])
    b2 = SMO.Bar(seri["t"].astype(np.int64), seri["o"], seri["h"], seri["l"], seri["c"], np.zeros(nn))
    M2 = SMO.Motor(b2, seri["v"].astype(float))
    t_bas = bar.t[-1] - GUN * 86400
    j2 = np.flatnonzero(b2.t >= t_bas)
    e2 = pd.Series(b2.c).ewm(span=1440, adjust=False).mean().to_numpy()
    y2 = np.where(b2.c[j2] > e2[j2], 1, -1)
    X2 = M2.ozellik(j2, b2.c[j2], y2, b2.t[j2] + 60)
    sk2 = mdl["model"].predict_proba(X2[mdl["oz"]].to_numpy(np.float32))[:, 1]
    a_s = str(pd.to_datetime(t_bas, unit="s"))
    G = C10.skorla(M, mdl["model"], mdl["oz"], a_s, str(pd.to_datetime(bar.t[-1] + 60, unit="s")))
    G = G[G["t"] - 60 >= t_bas].reset_index(drop=True)
    G2 = pd.DataFrame({"t": b2.t[j2] + 60, "skor2": sk2, "y2": y2})
    m = G.merge(G2, on="t", how="inner")
    es = mdl["esik"]

    def ates(sk, y):
        ok = (sk >= es) & (y > 0)
        return ok & ~np.r_[False, ok[:-1]]
    f1, f2 = ates(m["skor"].to_numpy(), m["y"].to_numpy()), ates(m["skor2"].to_numpy(), m["y2"].to_numpy())
    t1, t2 = set(m.loc[f1, "t"]), set(m.loc[f2, "t"])
    yak = lambda A, Bs: np.mean([any(abs(x - z) <= 120 for z in Bs) for x in A]) if A else None
    out = {"n_dakika": len(m), "skor_korelasyon": round(float(np.corrcoef(m["skor"], m["skor2"])[0, 1]), 4),
           "skor_mutlak_fark_medyan": round(float(np.median(np.abs(m["skor"] - m["skor2"]))), 5),
           "y_uyum": round(float((m["y"] == m["y2"]).mean()), 4), "ates_arastirma": len(t1), "ates_canli": len(t2),
           "ortak_tam": len(t1 & t2), "arastirma_canlida_2dk": yak(sorted(t1), sorted(t2)),
           "canli_arastirmada_2dk": yak(sorted(t2), sorted(t1)), "n_sentetik": seri["n_sentetik"]}
    print(ad, out, flush=True)
    return out


def main() -> None:
    model, oz, q = B.model_ve_esik()
    mdl = {"model": model, "oz": list(oz), "esik": float(q[0.998]), "kaynak": "research/soma_cozum_20261122 SC-08/SC-13/SC-19",
           "sklearn": sklearn.__version__, "uretim": pd.Timestamp.utcnow().isoformat()}
    (BOT / "models").mkdir(exist_ok=True)
    joblib.dump(mdl, BOT / "models" / "soma_e2_model.joblib", compress=3)
    sonuc = {"esik": mdl["esik"], "n_oz": len(oz)}
    sonuc["XAU"] = parite("XAU", F.yukle("2017-01-01"), mdl)
    bar, vol, _ = K19.ndx_bar()
    sonuc["NDX"] = parite("NDX", F.Motor(bar, vol), mdl)
    (R / "sc19_parite.json").write_text(json.dumps(sonuc, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
