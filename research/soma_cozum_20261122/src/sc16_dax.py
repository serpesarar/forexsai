"""SC-16 — DAX dondurulmuş E2X3 sağlamlık sınamaları (PROTOCOL SC-16). Çıktı: results/sc16_dax.json"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("SC08_AN", "son")
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sc08_kural as K  # noqa: E402
import sc08_ozellik as F  # noqa: E402
import sc10_klon_kar as C10  # noqa: E402
import sc13_strateji as S13  # noqa: E402
import sc14_bakis as B  # noqa: E402
import sc15_tasima as T15  # noqa: E402
import sc_degerlendir as D  # noqa: E402
import sc_sim as S  # noqa: E402

R = S13.R
A, Bt = T15.A, T15.Bt


def sim(M, i0, y, sl, T, sk=1.0):
    bar = M.bar
    m = (i0 < len(bar) - 2) & np.isfinite(sl) & (sl > 0)
    e = S.Emir.yeni(int(m.sum()))
    e.i0[:], e.yon[:], e.sl_d[:] = i0[m], y[m], sl[m]
    e.t_cik[:] = bar.t[i0[m]] + T * 60
    r = S.simule(bar, e, sk=sk, komisyon_usd=0.0)
    r["src"] = np.flatnonzero(m)
    return r


def hucre(M, k, y, kt, yt, kat, T, rng=None):
    a = S13.atr_h1(M, k)
    r, rs = sim(M, k + 1, y, kat * a, T), sim(M, k + 1, y, kat * a, T, 1.5)
    tb = np.mean([sim(M, x + 1, yy, kat * S13.atr_h1(M, x), T)["bp"].to_numpy() for x, yy in zip(kt, yt)], axis=0)
    h = B.degerle(r, rs, tb, A, Bt)
    h["P_EV"] = D.ozet(r)["P"]
    return h, r


def main() -> None:
    model, oz, q = B.model_ve_esik()
    bar, vol = T15.bar_yukle("DAX")
    M = F.Motor(bar, vol)
    G = C10.skorla(M, model, oz, A, Bt)
    G.to_parquet(R / "sc16_dax_skor.parquet")
    X = pd.read_parquet(R / "sc08_matris_son.parquet")
    G0 = pd.read_parquet(R / "sc08_skor_son.parquet").assign(t=lambda d: d["t"] + 60)
    kesim = X.loc[(X.hesap == "2268766") & (X.bolum == "ILERI"), "t_giris"].min()
    rng = np.random.default_rng(D.TOHUM)
    out: dict = {}
    k = B.alis_ates(G, q[0.998])
    kt = B.rastgele(M, k, A, Bt, rng)
    bir = [np.ones(len(x), np.int32) for x in kt]
    y1 = np.ones(len(k), np.int32)
    h, r = hucre(M, k, y1, kt, bir, 1.0, 480)
    out["a_kart"] = h
    out["a_gecer"] = bool(h["n"] >= 150 and h["ort_bp"] > 0 and h["P_EV"] >= 0.90 and h["yari1"] >= 0 and h["yari2"] >= 0
                          and h["stres"] > 0 and h["tek_poz"] > 0)
    print("a", h, flush=True)
    plato = {}
    for kat in (0.75, 1.0, 1.5):
        for T in (240, 480, 960):
            hh, _ = hucre(M, k, y1, kt, bir, kat, T)
            plato[f"k{kat}_T{T}"] = {x: hh[x] for x in ("ort_bp", "fark", "fark_P", "yari1", "yari2")}
            print("b", kat, T, plato[f"k{kat}_T{T}"], flush=True)
    out["b_plato"] = plato
    out["b_gecer"] = sum(plato[c]["fark"] > 0 and plato[c]["fark_P"] >= 0.90
                         for c in ("k0.75_T480", "k0.75_T960", "k1.0_T480", "k1.0_T960")) >= 3
    K.SOGUMA = 0
    Aall = K.ateslemeler(G.assign(ok=G["skor"] >= q[0.998]))
    ks = Aall.loc[Aall["y"] < 0, "j"].to_numpy()
    kts = B.rastgele(M, ks, A, Bt, rng)
    hs, _ = hucre(M, ks, -np.ones(len(ks), np.int32), kts, [-np.ones(len(x), np.int32) for x in kts], 1.0, 480)
    out["c_ayna_satis"] = hs
    print("c", hs, flush=True)
    dd = {}
    for qq in (0.997, 0.999):
        e = float(np.quantile(G0.loc[G0.t < kesim, "skor"], qq))
        kq = B.alis_ates(G, e)
        ktq = B.rastgele(M, kq, A, Bt, rng)
        hq, _ = hucre(M, kq, np.ones(len(kq), np.int32), ktq, [np.ones(len(x), np.int32) for x in ktq], 1.0, 480)
        dd[str(qq)] = {x: hq[x] for x in ("n", "ort_bp", "fark", "fark_P")}
        print("d", qq, dd[str(qq)], flush=True)
    out["d_esik"] = dd
    out["d_gecer"] = all(v["fark"] > 0 for v in dd.values())
    gun0 = r["t0"] // 86400
    ayni = (r["t1"] // 86400 == gun0).to_numpy()
    tbr = np.mean([sim(M, x + 1, np.ones(len(x), np.int32), S13.atr_h1(M, x), 480)["bp"].to_numpy() for x in kt], axis=0)
    out["e_gece"] = {"ayni_gun_n": int(ayni.sum()), "ayni_gun_ort": round(float(r["bp"][ayni].mean()), 3),
                     "ayni_gun_taban": round(float(tbr[r["src"].to_numpy()][ayni].mean()), 3),
                     "gece_n": int((~ayni).sum()), "gece_ort": round(float(r["bp"][~ayni].mean()), 3)}
    out["e_gecer"] = out["e_gece"]["ayni_gun_ort"] > out["e_gece"]["ayni_gun_taban"]
    print("e", out["e_gece"], flush=True)
    gunluk = r.groupby(gun0)["bp"].sum().sort_values(ascending=False)
    kalan = r[~gun0.isin(gunluk.index[:10])]
    out["f_en_iyi10_haric_ort"] = round(float(kalan["bp"].mean()), 3)
    out["f_gecer"] = out["f_en_iyi10_haric_ort"] > 0
    saat = pd.to_datetime(r["t0"], unit="s").dt.hour
    out["saat"] = r.groupby(saat)["bp"].agg(["size", "mean"]).round(2).to_dict("index")
    out["hukum"] = "B+" if all(out[x] for x in ("a_gecer", "b_gecer", "d_gecer", "e_gecer", "f_gecer")) else "C"
    print({x: out[x] for x in ("a_gecer", "b_gecer", "d_gecer", "e_gecer", "f_gecer", "f_en_iyi10_haric_ort", "hukum")})
    print("saat", out["saat"])
    D.kaydet("SC-16", "TASIMA", {"piyasa": "DAX"}, {x: out[x] for x in ("a_kart", "hukum")})
    (R / "sc16_dax.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
