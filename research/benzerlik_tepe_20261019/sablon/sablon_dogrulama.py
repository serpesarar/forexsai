"""ME-09 adım 1 — üç şablon bu ölçüyle birbirine benziyor mu? (sonuç/ileri getiri YOK; yalnız şekil)
Çalıştır: nice python3.13 research/benzerlik_tepe_20261019/sablon/sablon_dogrulama.py
"""
from __future__ import annotations

import json
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from ortak import (DEV_END, OUT, P, QUERY_HOUR, TEMPL, TEMPL_ALT, dist_matrix, load_ndx, r_from_d, shapes,  # noqa: E402
                   tpl_index, tpl_shape, window_lengths)


def zigzag_legs(x: np.ndarray, thr: float) -> list[tuple[int, float]]:
    """Kapanışlarda thr (oran) geri dönüşlü zigzag; dönüş noktaları (indeks, fiyat)."""
    piv = [(0, x[0])]
    hi_i, lo_i = 0, 0
    trend = 0
    for i in range(1, len(x)):
        if trend >= 0 and x[i] > x[hi_i]:
            hi_i = i
        if trend <= 0 and x[i] < x[lo_i]:
            lo_i = i
        if trend >= 0 and x[i] <= x[hi_i] * (1 - thr) and hi_i != piv[-1][0]:
            piv.append((hi_i, x[hi_i])); trend = -1; lo_i = i
        elif trend <= 0 and x[i] >= x[lo_i] * (1 + thr) and lo_i != piv[-1][0]:
            piv.append((lo_i, x[lo_i])); trend = 1; hi_i = i
    last = hi_i if trend > 0 else lo_i
    if last != piv[-1][0]:
        piv.append((last, x[last]))
    return piv


def features(d: pd.DataFrame, a: int, b: int) -> dict:
    s = d.iloc[a:b + 1]
    cl = s.close.to_numpy()
    pre = d.iloc[max(0, a - 20 * 23):a]  # şablondan ÖNCEKİ ~20 işlem günü (yalnız geçmiş)
    pre_day = pre.groupby(pre.ts.dt.date).agg(h=("high", "max"), l=("low", "min"))
    adr = float(((pre_day.h - pre_day.l) / pre_day.l).mean())
    hr = np.diff(np.log(cl))
    out = {
        "baslangic": str(s.ts.iloc[0]), "bitis": str(s.ts.iloc[-1]), "bar": int(len(s)),
        "islem_gunu": int(s.ts.dt.date.nunique()),
        "net_%": 100 * float(cl[-1] / cl[0] - 1),
        "aralik_%": 100 * float(s.high.max() / s.low.min() - 1),
        "aralik_/_onceki_gunluk_aralik": float((s.high.max() / s.low.min() - 1) / adr),
        "tepe_konum": float(np.argmax(s.high.to_numpy()) / (len(s) - 1)),
        "dip_konum": float(np.argmin(s.low.to_numpy()) / (len(s) - 1)),
        "maks_dusus_%": 100 * float((cl / np.maximum.accumulate(cl) - 1).min()),
        "1s_oynaklik_bp": 1e4 * float(hr.std()),
        "onceki_20g_tepeye_uzaklik_%": 100 * float(s.high.max() / d.iloc[max(0, a - 20 * 23):a].high.max() - 1),
    }
    for thr in (0.005, 0.01):
        pv = zigzag_legs(cl, thr)
        highs = [p for j, p in enumerate(pv[1:-1], 1) if p[1] > pv[j - 1][1]]
        out[f"zigzag_{thr*100:.1f}%_bacak"] = len(pv) - 1
        hv = [h[1] for h in highs]
        out[f"zigzag_{thr*100:.1f}%_tepeler_%"] = [round(100 * (v / cl[0] - 1), 2) for v in hv]
    return out


def main() -> None:
    d = load_ndx(); ts = d.ts; c = np.log(d.close.to_numpy())
    res: dict = {}
    for tag, templ in (("birincil", TEMPL), ("alternatif_gorsel", TEMPL_ALT)):
        tpl = tpl_index(ts, templ)
        LS = window_lengths(tpl)
        names = list(tpl)
        vec = {k: tpl_shape(c, a, b) for k, (a, b) in tpl.items()}
        Q = np.flatnonzero((ts.dt.hour == QUERY_HOUR).to_numpy())
        Q = Q[Q >= max(LS)]
        dev = (ts.iloc[Q] <= DEV_END).to_numpy()
        Qd = Q[dev]
        Di = {k: dist_matrix(c, Qd, LS, [vec[k]], 1.0) for k in names}
        # tüm (sorgu, L) pencereleri — min almadan
        allw = {}
        for k in names:
            arr = []
            for L in LS:
                S = shapes(c, Qd - L + 1, L)
                arr.append(np.sqrt(((S - vec[k]) ** 2).sum(1)))
            allw[k] = np.concatenate(arr)
        Dall = np.minimum.reduce([Di[k] for k in names])
        thr2, thr5 = np.percentile(Dall, 2), np.percentile(Dall, 5)
        pair = []
        for i in names:
            for j in names:
                if i >= j:
                    continue
                dij = float(np.sqrt(((vec[i] - vec[j]) ** 2).sum()))
                a_j, b_j = tpl[j]; a_i, b_i = tpl[i]
                # dedektör tarzı: Tj'nin son barında LS pencereleri, yalnız Ti şablonu
                det_ij = float(dist_matrix(c, np.array([b_j]), LS, [vec[i]], 1.0)[0])
                det_ji = float(dist_matrix(c, np.array([b_i]), LS, [vec[j]], 1.0)[0])
                pair.append({
                    "cift": f"{i}-{j}", "d_tam_aralik": round(dij, 3), "r": round(float(r_from_d(dij)), 3),
                    f"yuzdelik_%_{i}_dagiliminda": round(100 * float((Di[i] <= dij).mean()), 2),
                    f"yuzdelik_%_{j}_dagiliminda": round(100 * float((Di[j] <= dij).mean()), 2),
                    f"yuzdelik_%_{i}_tum_pencereler": round(100 * float((allw[i] <= dij).mean()), 2),
                    f"dedektor_{j}_sonunda_{i}_ile": {"D": round(det_ij, 3), "r": round(float(r_from_d(det_ij)), 3),
                                                      "yuzdelik_%": round(100 * float((Di[i] <= det_ij).mean()), 2)},
                    f"dedektor_{i}_sonunda_{j}_ile": {"D": round(det_ji, 3), "r": round(float(r_from_d(det_ji)), 3),
                                                      "yuzdelik_%": round(100 * float((Di[j] <= det_ji).mean()), 2)},
                })
        # her şablonun kendi sonunda, KENDİSİ HARİÇ diğer iki şablonla birleşik D'nin yüzdeliği
        loo = {}
        for k in names:
            others = [vec[o] for o in names if o != k]
            Dm = np.minimum.reduce([Di[o] for o in names if o != k])
            dk = float(dist_matrix(c, np.array([tpl[k][1]]), LS, others, 1.0)[0])
            loo[k] = {"D": round(dk, 3), "r": round(float(r_from_d(dk)), 3), "yuzdelik_%": round(100 * float((Dm <= dk).mean()), 2)}
        # ölçek: rastgele (sorgu) penceresinin şablona en yakın uzaklık dağılımı
        dist_summary = {k: {f"p{q}": round(float(np.percentile(Di[k], q)), 3) for q in (1, 2, 5, 25, 50)} for k in names}
        res[tag] = {
            "sablon_aralik_bar": {k: [str(ts.iloc[a]), str(ts.iloc[b]), b - a + 1] for k, (a, b) in tpl.items()},
            "pencere_uzunluklari": LS, "gelistirme_sorgu_gunu": int(len(Qd)),
            "birlesik_esik_%2": round(float(thr2), 3), "birlesik_esik_%5": round(float(thr5), 3),
            "esik_%2_r": round(float(r_from_d(thr2)), 3), "esik_%5_r": round(float(r_from_d(thr5)), 3),
            "ciftler": pair, "kendisi_haric_digerleriyle": loo, "sablon_basina_D_dagilimi": dist_summary,
            "ozellikler": {k: features(d, a, b) for k, (a, b) in tpl.items()},
        }
        if tag == "birincil":
            fig, ax = plt.subplots(1, 2, figsize=(13, 4.2))
            for k in names:
                ax[0].plot(vec[k], label=f"{k} ({tpl[k][1]-tpl[k][0]+1} bar)")
                a, b = tpl[k]
                ax[1].plot(np.arange(b - a + 1), 100 * (d.close.iloc[a:b + 1].to_numpy() / d.close.iloc[a] - 1), label=k)
            ax[0].set_title("64 noktaya örneklenmiş z-normalize şekiller (ölçünün gördüğü)")
            ax[1].set_title("Ham yol: başlangıca göre % (1h bar)")
            for x_ in ax:
                x_.legend(); x_.grid(alpha=.3)
            fig.tight_layout(); fig.savefig(OUT / "sablon_sekilleri.png", dpi=110); plt.close(fig)
    (OUT / "sablon_dogrulama.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str))
    print(json.dumps(res, ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    main()
