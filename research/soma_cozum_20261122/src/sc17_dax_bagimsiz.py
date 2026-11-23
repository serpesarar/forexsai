"""SC-17 — DAX E2X3 bağımsız dönem (Dukascopy DEUIDXEUR ilk ay → 2017-12). Kural SC-16 ile birebir. Çıktı: results/sc17_dax.json"""
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
import sc10_klon_kar as C10  # noqa: E402
import sc13_strateji as S13  # noqa: E402
import sc14_bakis as B  # noqa: E402
import sc16_dax as S16  # noqa: E402
import sc_degerlendir as D  # noqa: E402
import sc_veri as V  # noqa: E402

R = S13.R
CH = S13.KOK / "data" / "chunks" / "DAX"
ISINMA = 120  # gün: EMA1440 / D1 EMA200 için ilk dönem değerlendirme dışı


def bar_kur() -> tuple[V.Bar, np.ndarray, str]:
    satir = []
    for f in sorted(CH.glob("*_BID.bi5")):
        satir.extend(V._bi5_satirlar(f))
    d = pd.DataFrame(satir, columns=["t", "open", "high", "low", "close", "vol"]).drop_duplicates("t").sort_values("t")
    d = d[(d[["open", "high", "low", "close"]] > 0).all(axis=1)].reset_index(drop=True)
    ask = []
    for f in sorted(CH.glob("*_ASK.bi5")):
        ask.extend(V._bi5_satirlar(f))
    a = pd.DataFrame(ask, columns=["t", "ask_open", "h", "l", "c", "v"])[["t", "ask_open"]]
    tablo = V.spread_modeli(d, a)
    spr = V._spread_uygula(d, tablo)
    t = d["t"].to_numpy("int64")
    assert (np.diff(t) > 0).all() and np.isfinite(spr).all() and (spr > 0).all()
    o = d["open"].to_numpy(float)
    ilk = pd.to_datetime(t[0], unit="s").normalize() + pd.Timedelta(days=ISINMA)
    return (V.Bar(t, o, d["high"].to_numpy(float), d["low"].to_numpy(float), d["close"].to_numpy(float), spr * o / 1e4),
            d["vol"].to_numpy(float), str(ilk.date()))


def main() -> None:
    model, oz, q = B.model_ve_esik()
    bar, vol, a = bar_kur()
    b = "2018-01-01"
    S16.A, S16.Bt = a, b
    M = F.Motor(bar, vol)
    G = C10.skorla(M, model, oz, a, b)
    rng = np.random.default_rng(D.TOHUM)
    k = B.alis_ates(G, q[0.998])
    kt = B.rastgele(M, k, a, b, rng)
    h, r = S16.hucre(M, k, np.ones(len(k), np.int32), kt, [np.ones(len(x), np.int32) for x in kt], 1.0, 480)
    yil = h.get("yillik", {})
    h["donem"] = [a, b]
    h["ilk_veri"] = str(pd.to_datetime(bar.t[0], unit="s"))
    h["spread_med_bp"] = round(float(np.median(bar.s / bar.o * 1e4)), 3)
    h["hukum"] = "B" if (h["ort_bp"] > 0 and h["fark"] > 0 and h["fark_P"] >= 0.95 and h["yari1"] > 0 and h["yari2"] > 0
                         and h["stres"] > 0 and sum(v > 0 for v in yil.values()) >= len(yil) / 2) else "X"
    print(h)
    D.kaydet("SC-17", "TASIMA_BAGIMSIZ", {"piyasa": "DAX", "donem": [a, b]}, h)
    (R / "sc17_dax.json").write_text(json.dumps(h, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
