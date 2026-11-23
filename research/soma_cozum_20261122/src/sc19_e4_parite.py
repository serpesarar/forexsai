"""SC-19c — E4X3 canlı kodu (yeni deneme/soma_e4x3_live.evaluate) ↔ araştırma (sc13_strateji.soma_tetik) paritesi.
Son 60 gün XAU: araştırmanın TÜM koşul-sağlayan dakikaları + yeni-gün-tepesi olup koşulu sağlamayan 400 dakika.
Canlı fonksiyona yalnız o ana kadarki barlar (sunucu saatinde 1m, H4, H1 — 1m'den toplanmış) verilir. Çıktı: results/sc19_e4_parite.json
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("SC08_AN", "son")
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sc08_ozellik as F  # noqa: E402
import sc13_strateji as S13  # noqa: E402
import sc_veri as V  # noqa: E402

sys.path.insert(0, str(V.ROOT / "yeni deneme"))
import soma_e4x3_live as L  # noqa: E402

R = Path(__file__).resolve().parents[1] / "results"


def topla(t_srv: np.ndarray, o, h, l, c, sec: int) -> dict:
    s = t_srv // sec
    u, ilk = np.unique(s, return_index=True)
    son = np.r_[ilk[1:], len(s)] - 1
    return {"t": (u * sec).astype(float), "o": o[ilk], "h": np.maximum.reduceat(h, ilk), "l": np.minimum.reduceat(l, ilk),
            "c": c[son]}


def main() -> None:
    M = F.yukle("2017-01-01")
    bar = M.bar
    t_srv = bar.t + M.sun
    a = str(pd.to_datetime(bar.t[-1] - 60 * 86400, unit="s").date())
    b = "2026-11-14"
    # araştırma: tüm koşul-sağlayan dakikalar (ilk-olay elemesi ÖNCESİ) — soma_tetik içini yeniden kur
    c = bar.c
    e1440 = pd.Series(c).ewm(span=1440, adjust=False).mean().to_numpy()
    D1 = M.tf["D1"]
    ayni = np.r_[False, D1.kova_1m[1:] == D1.kova_1m[:-1]]
    yeni = ayni & (bar.h > np.r_[np.nan, D1.kumh[:-1]]) & (c > e1440)
    ilk_olay = S13.soma_tetik(M, a, b)
    ilk_olay = set(ilk_olay.loc[ilk_olay["y"] > 0, "k"])
    aday = np.flatnonzero(yeni & (bar.t >= pd.Timestamp(a).timestamp()))
    rng = np.random.default_rng(0)
    H4 = topla(t_srv, bar.o, bar.h, bar.l, c, 4 * 3600)
    H1 = topla(t_srv, bar.o, bar.h, bar.l, c, 3600)
    # tam koşulu vektörel kur (soma_tetik ile aynı satırlar)
    e240 = pd.Series(c).ewm(span=240, adjust=False).mean().to_numpy()
    H4t = M.tf["H4"]
    bc = np.clip(np.searchsorted(H4t.kova, H4t.kova_1m) - 1, 0, len(H4t.C) - 1)
    kanal = c >= H4t.g["hh20"][bc] - S13.KANAL_ATR * H4t.g["atr"][bc]
    govde = (c - bar.o) / np.maximum(bar.h - bar.l, 1e-12) >= S13.GOVDE_MIN
    full = yeni & (c > e240) & kanal & govde
    pos = [k for k in aday if full[k]]
    neg = [k for k in aday if not full[k]]
    neg = list(rng.choice(neg, min(400, len(neg)), replace=False)) if neg else []
    uyum, hata = 0, []
    for k in pos + neg:
        w0 = k - L.FETCH_M1 + 1
        m1 = {"t": t_srv[w0:k + 1].astype(float), "o": bar.o[w0:k + 1], "h": bar.h[w0:k + 1], "l": bar.l[w0:k + 1],
              "c": c[w0:k + 1]}
        h4 = {x: v[L.before_bucket(H4["t"], t_srv[k], 4 * 3600)][-L.FETCH_H:] for x, v in H4.items()}
        h1 = {x: v[L.before_bucket(H1["t"], t_srv[k], 3600)][-L.FETCH_H:] for x, v in H1.items()}
        s = L.evaluate(m1, h4, h1)
        ok = (s is not None) == bool(full[k])
        uyum += ok
        if not ok:
            hata.append({"t": str(pd.to_datetime(bar.t[k], unit="s")), "arastirma": bool(full[k]), "canli": s is not None})
    out = {"donem": [a, b], "pozitif": len(pos), "negatif_ornek": len(neg), "uyum": uyum, "toplam": len(pos) + len(neg),
           "ilk_olay_sayisi": len(ilk_olay), "uyumsuz": hata[:20]}
    print(out)
    (R / "sc19_e4_parite.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
