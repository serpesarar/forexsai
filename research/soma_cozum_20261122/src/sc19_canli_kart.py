"""SC-19 — canlıya alma kartı (2. KURAL, 6 ölçüt) + NASDAQ ve diğer piyasalara dondurulmuş taşıma.

Hücreler (SC-13 tanımı, DEĞİŞMEDİ): E4X3 = modelsiz tetik AL, E2X3 = model AL; çıkış SL 1,0×ATR_H1 + 480 dk.
Kart penceresi = son 4 yıl (2022-11-14 → 2026-11-14; kullanıcı ölçütü 2026-11-23). Eski yıllar betimleyici.
Ölçütler: (1) n ≥ 150 (2) ort R > 0 ∧ P(EV>0) ≥ 0,90 (3) iki kronolojik yarı ≥ 0 (4) spread ×1,5 > 0
(5) icra: gerçek (sonraki 1m açılışı + spread) ile iyimser (spread yok) farkı ≤ ort R / 2 (6) tek pozisyon > 0.
Ek (kullanıcı ölçütü): 2023, 2024, 2025, 2026 yıllarının her biri > 0.
Çıktı: results/sc19_kart.json
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
import sc10_klon_kar as C10  # noqa: E402
import sc13_strateji as S13  # noqa: E402
import sc14_bakis as B  # noqa: E402
import sc15_tasima as S15  # noqa: E402
import sc_degerlendir as D  # noqa: E402
import sc_sim as S  # noqa: E402
import sc_veri as V  # noqa: E402

R = S13.R
ARS = V.ROOT / "research"
A, Bt = "2018-01-15", "2026-11-14"
KART_A = "2022-11-14"
SON_YILLAR = (2023, 2024, 2025, 2026)
SL_KAT, T_DK = 1.0, 480
NDX_PARQ = ARS / "nom_20261113" / "data" / "ndx_1m_v3_duka.parquet"
NDX_BI5 = [ARS / "nom_20261113/data/duka_m1", ARS / "ndx_seans_tasima_20261103/denetim/data/duka_m1",
           ARS / "ndx_tf_yapilandirma_20261117/out/duka_m1_2025", ARS / "ndx_tf_yapilandirma_20261117/out/duka_m1_ek"]
KORKU_CH = ARS / "korku_kuresel_20261118" / "data" / "chunks"


# ───────────────────────── veri ─────────────────────────
def ndx_bar() -> tuple[V.Bar, np.ndarray, float]:
    d = pd.read_parquet(NDX_PARQ, columns=["t", "open", "high", "low", "close", "spr"]).sort_values("t").drop_duplicates("t")
    vol: dict[int, float] = {}
    for kl in NDX_BI5:
        for f in sorted(kl.glob("*_BID.bi5")):
            for s in V._bi5_satirlar(f):
                vol[int(s[0])] = s[5]
    v = d["t"].map(vol).to_numpy(float)                              # eksik → NaN (model eksik değeri kendi dalına yollar)
    t = d["t"].to_numpy("int64")
    assert (np.diff(t) > 0).all()
    bar = V.Bar(t, d["open"].to_numpy(float), d["high"].to_numpy(float), d["low"].to_numpy(float),
                d["close"].to_numpy(float), d["spr"].to_numpy(float))
    return bar, v, float(np.isfinite(v[t >= D.ts(KART_A)]).mean())


def chunk_bar(ad: str) -> tuple[V.Bar, np.ndarray]:
    satir = [s for f in sorted((KORKU_CH / ad).glob("*_BID.bi5")) for s in V._bi5_satirlar(f)]
    d = pd.DataFrame(satir, columns=["t", "open", "high", "low", "close", "vol"]).drop_duplicates("t").sort_values("t")
    d = d[(d[["open", "high", "low", "close"]] > 0).all(axis=1)].reset_index(drop=True)
    ask = [s for f in sorted((KORKU_CH / ad).glob("*_ASK.bi5")) for s in V._bi5_satirlar(f)]
    a = pd.DataFrame(ask, columns=["t", "ask_open", "h", "l", "c", "v"])[["t", "ask_open"]]
    m = d[["t", "open"]].merge(a, on="t")
    bp = ((m["ask_open"] - m["open"]) / m["open"] * 1e4)
    bp = bp[(bp > 0) & (bp < 50)]
    sp_bp = float(bp.median())                                       # ASK örneği az → tek medyan (yıl×saat yok); betimleyici
    o = d["open"].to_numpy(float)
    return (V.Bar(d["t"].to_numpy("int64"), o, d["high"].to_numpy(float), d["low"].to_numpy(float), d["close"].to_numpy(float),
                  np.full(len(o), sp_bp) * o / 1e4), d["vol"].to_numpy(float))


# ───────────────────────── simülasyon ─────────────────────────
def sim(M: F.Motor, k: np.ndarray, sk: float, kom: float) -> pd.DataFrame:
    bar = M.bar
    i0 = k + 1
    sl = SL_KAT * S13.atr_h1(M, k)
    m = (i0 < len(bar) - 2) & np.isfinite(sl) & (sl > 0)
    e = S.Emir.yeni(int(m.sum()))
    e.i0[:], e.yon[:], e.sl_d[:] = i0[m], 1, sl[m]
    e.t_cik[:] = bar.t[i0[m]] + T_DK * 60
    r = S.simule(bar, e, sk=sk, komisyon_usd=kom)
    r["R"] = r["bp"] / (sl[m] / bar.o[i0[m]] * 1e4)
    return r


def yillik(r: pd.DataFrame, kol: str) -> dict:
    y = pd.to_datetime(r["t0"], unit="s").dt.year
    return {int(a): round(float(b), 3) for a, b in r.groupby(y)[kol].mean().items()}


def kart(M: F.Motor, k_tum: np.ndarray, kom: float, rng) -> dict:
    bar = M.bar
    k = k_tum[(bar.t[k_tum] >= D.ts(A)) & (bar.t[k_tum] < D.ts(Bt))]
    r_tum = sim(M, k, 1.0, kom)
    kw = bar.t[k] >= D.ts(KART_A)
    kk = k[kw]
    r, rs, ro = sim(M, kk, 1.0, kom), sim(M, kk, 1.5, kom), sim(M, kk, 0.0, kom)
    x, gun = r["R"].to_numpy(), r["t0"].to_numpy() // 86400
    yari = len(x) // 2
    tek = D.tek_pozisyon(r)
    kt = B.rastgele(M, kk, KART_A, Bt, rng)
    tbl = [sim(M, z, 1.0, kom)["bp"].to_numpy() for z in kt]
    n_tb = min([len(r)] + [len(z) for z in tbl])
    tb = np.mean([z[:n_tb] for z in tbl], axis=0)
    ortR, optR = float(x.mean()), float(ro["R"].mean())
    yr = yillik(r_tum, "R")
    olc = {
        "1_hacim": {"n": len(x), "gecti": len(x) >= 150},
        "2_beklenti": {"ort_R": round(ortR, 4), "P_EV_pos": round(D.gun_blok_P(x, gun), 4),
                       "gecti": ortR > 0 and D.gun_blok_P(x, gun) >= 0.90},
        "3_kararlilik": {"yari1_R": round(float(x[:yari].mean()), 4), "yari2_R": round(float(x[yari:].mean()), 4),
                         "gecti": x[:yari].mean() >= 0 and x[yari:].mean() >= 0},
        "4_surtunme": {"stres_R": round(float(rs["R"].mean()), 4), "gecti": rs["R"].mean() > 0},
        "5_icra": {"iyimser_R": round(optR, 4), "gercek_R": round(ortR, 4), "fark": round(optR - ortR, 4),
                   "gecti": ortR > 0 and (optR - ortR) <= ortR / 2},
        "6_tek_pozisyon": {"n": len(tek), "ort_R": round(float(tek["R"].mean()), 4), "gecti": tek["R"].mean() > 0},
    }
    son = {y: yr.get(y) for y in SON_YILLAR}
    gecen = sum(v["gecti"] for v in olc.values())
    son_ok = all(v is not None and v > 0 for v in son.values())
    return {"olcutler": olc, "gecen": f"{gecen}/6", "son4_yil_R": son, "son4_her_yil_arti": son_ok,
            "tum_yillar_R": yr, "tum_yillar_n": {int(a): int(b) for a, b in
                                                 pd.to_datetime(r_tum["t0"], unit="s").dt.year.value_counts().sort_index().items()},
            "ort_bp": round(float(r["bp"].mean()), 3), "taban_bp": round(float(tb.mean()), 3),
            "fark_bp": round(float(r["bp"].mean() - tb.mean()), 3),
            "fark_P": round(D.fark_P(r["bp"].to_numpy()[:n_tb], tb, gun[:n_tb]), 4),
            "isabet": round(float((x > 0).mean()), 3), "maks_dusus_R": round(float((np.maximum.accumulate(np.cumsum(x)) -
                                                                                    np.cumsum(x)).max()), 2),
            "yilda_islem": round(len(x) / 4.0, 1),
            "verdikt": "LIVE" if gecen == 6 and son_ok else ("SHADOW" if son_ok or gecen >= 4 else "RED")}


def piyasa(ad: str, M: F.Motor, kom: float, model, oz, q, notu: str = "") -> dict:
    rng = np.random.default_rng(D.TOHUM)
    e4 = S13.soma_tetik(M, A, Bt)
    e4 = e4.loc[e4["y"] > 0, "k"].to_numpy()
    out = {"not": notu, "E4X3": kart(M, e4, kom, rng)}
    G = C10.skorla(M, model, oz, A, Bt)
    out["E2X3"] = kart(M, B.alis_ates(G, q[0.998]), kom, rng)
    for h in ("E4X3", "E2X3"):
        c = out[h]
        print(ad, h, c["gecen"], c["verdikt"], "son4", c["son4_yil_R"], "fark", c["fark_bp"], c["fark_P"], flush=True)
        D.kaydet("SC-19", "KART", {"piyasa": ad, "hucre": h}, {k: v for k, v in c.items() if k != "olcutler"})
    return out


def main() -> None:
    sadece = set(sys.argv[1:])
    model, oz, q = B.model_ve_esik()
    yol = R / "sc19_kart.json"
    sonuc = json.loads(yol.read_text()) if yol.exists() else {}
    isler = [("XAU", lambda: (F.yukle("2017-01-01"), V.KOMISYON_USD_OZ, "kendi küpü (eğitim piyasası; 2025 model eğitimiyle kısmen çakışır)")),
             ("NDX", None), ("DAX", None), ("CAC", None), ("STOXX", None), ("UK100", None), ("JPN225", None)]
    for ad, f in isler:
        if sadece and ad not in sadece:
            continue
        try:
            if ad == "XAU":
                M, kom, notu = f()
            elif ad == "NDX":
                bar, vol, kap = ndx_bar()
                M, kom, notu = F.Motor(bar, vol), 0.0, f"hacim kapsamı son 4 yıl %{kap * 100:.0f} (eksik → NaN; E2 yaklaşık)"
            elif ad in S15.PIYASA:
                bar, vol = S15.bar_yukle(ad)
                M, kom, notu = F.Motor(bar, vol), 0.0, "fibo önbelleği, yıl×saat spread"
            else:
                bar, vol = chunk_bar(ad)
                M, kom, notu = F.Motor(bar, vol), 0.0, "korku_kuresel parçaları, tek medyan spread (ASK örneği az)"
            sonuc[ad] = piyasa(ad, M, kom, model, oz, q, notu)
        except Exception as e:  # noqa: BLE001
            sonuc[ad] = {"hata": repr(e)}
            print(ad, "HATA", repr(e), flush=True)
        yol.write_text(json.dumps(sonuc, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
