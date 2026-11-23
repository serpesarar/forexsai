"""SC-15 — E2X3'ün dondurulmuş taşınması: DAX / CAC / STOXX50 1m 2018→2026 (PROTOCOL SC-15). Çıktı: results/sc15_sonuc.json"""
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
import sc_degerlendir as D  # noqa: E402
import sc_sim as S  # noqa: E402
import sc_veri as V  # noqa: E402

R = S13.R
FIBO = V.ROOT / "research" / "fibo_altin_bolge_20261116" / "cache"
PIYASA = ("DAX", "CAC", "STOXX")
A, Bt = "2018-01-15", "2026-11-14"


def bar_yukle(ad: str) -> tuple[V.Bar, np.ndarray]:
    d = pd.read_parquet(FIBO / f"{ad}_1m_raw.parquet").sort_values("t").drop_duplicates("t").reset_index(drop=True)
    d = d[(d[["open", "high", "low", "close"]] > 0).all(axis=1)].reset_index(drop=True)
    ask = d.dropna(subset=["ask_open"])[["t", "ask_open"]]
    tablo = V.spread_modeli(d, ask)
    spr = V._spread_uygula(d, tablo)
    t = d["t"].to_numpy("int64")
    assert (np.diff(t) > 0).all() and np.isfinite(spr).all() and (spr > 0).all()
    o = d["open"].to_numpy(float)
    return V.Bar(t, o, d["high"].to_numpy(float), d["low"].to_numpy(float), d["close"].to_numpy(float), spr * o / 1e4), \
        d["vol"].to_numpy(float)


def sim0(M: F.Motor, i0: np.ndarray, sl: np.ndarray, sk: float = 1.0) -> pd.DataFrame:
    bar = M.bar
    m = (i0 < len(bar) - 2) & np.isfinite(sl) & (sl > 0)
    e = S.Emir.yeni(int(m.sum()))
    e.i0[:], e.yon[:], e.sl_d[:] = i0[m], 1, sl[m]
    e.t_cik[:] = bar.t[i0[m]] + 480 * 60
    return S.simule(bar, e, sk=sk, komisyon_usd=0.0)


def main() -> None:
    model, oz, q = B.model_ve_esik()
    esik = q[0.998]
    rng = np.random.default_rng(D.TOHUM)
    sonuc, havuz_r, havuz_tb, havuz_s = {"esik": esik}, [], [], []
    for ad in PIYASA:
        bar, vol = bar_yukle(ad)
        M = F.Motor(bar, vol)
        G = C10.skorla(M, model, oz, A, Bt)
        k = B.alis_ates(G, esik)
        sl = S13.atr_h1(M, k)
        r, rs = sim0(M, k + 1, sl), sim0(M, k + 1, sl, 1.5)
        kt = B.rastgele(M, k, A, Bt, rng)
        tb = np.mean([sim0(M, x + 1, S13.atr_h1(M, x))["bp"].to_numpy() for x in kt], axis=0)
        h = B.degerle(r, rs, tb, A, Bt)
        h["gunluk_ates"] = round(len(k) / ((D.ts(Bt) - D.ts(A)) / 86400 * 5 / 7), 3)
        h["spread_med_bp"] = round(float(np.median(bar.s / bar.o * 1e4)), 3)
        sonuc[ad] = h
        D.kaydet("SC-15", "TASIMA", {"piyasa": ad}, h)
        print(ad, {x: h.get(x) for x in ("n", "ort_bp", "taban", "fark", "fark_P", "yari1", "yari2", "stres", "yillik", "gunluk_ates",
                                         "spread_med_bp")}, flush=True)
        n = min(len(r), len(tb))
        havuz_r.append(r.iloc[:n].assign(piyasa=ad))
        havuz_tb.append(tb[:n])
        havuz_s.append(rs.iloc[:n])
    Rr = pd.concat(havuz_r, ignore_index=True)
    tb = np.concatenate(havuz_tb)
    o = np.argsort(Rr["t0"].to_numpy(), kind="stable")
    Rr, tb = Rr.iloc[o].reset_index(drop=True), tb[o]
    x = Rr["bp"].to_numpy()
    yari = len(x) // 2
    hv = {"n": len(x), "ort_bp": round(float(x.mean()), 3), "taban": round(float(tb.mean()), 3),
          "fark": round(float(x.mean() - tb.mean()), 3), "fark_P": round(D.fark_P(x, tb, Rr["t0"].to_numpy() // 86400), 4),
          "yari1_fark": round(float((x[:yari] - tb[:yari]).mean()), 3), "yari2_fark": round(float((x[yari:] - tb[yari:]).mean()), 3),
          "yari1": round(float(x[:yari].mean()), 3), "yari2": round(float(x[yari:].mean()), 3),
          "stres": round(float(pd.concat(havuz_s)["bp"].mean()), 3)}
    sonuc["HAVUZ"] = hv
    arti = sum(sonuc[p]["fark"] > 0 for p in PIYASA)
    sonuc["hukum"] = "B" if (hv["fark"] > 0 and hv["fark_P"] >= 0.95 and hv["yari1"] > 0 and hv["yari2"] > 0 and hv["stres"] > 0
                             and arti >= 2) else "X"
    print("HAVUZ", hv, "HÜKÜM", sonuc["hukum"])
    (R / "sc15_sonuc.json").write_text(json.dumps(sonuc, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
