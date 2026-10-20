"""ME-09 ek tanılama — ön-kayıtlı koşumdan SONRA (sonuç görüldükten sonra). Hiçbiri başarı ailesini değiştirmez.
(a) %5 eşik (ön-kayıtta 'tanımlayıcı'), (b) aile düzeyi plasebo (kaç hücre plasebonun %95 dışında — seçim düzeltmesi),
(c) şablonların kendi sonunda kendini tanıma, (d) DAX benzer günlerinin NDX ile tarih örtüşmesi,
(e) görsel sınırlarla (TEMPL_ALT) duyarlılık.
Çalıştır: nice python3.13 research/benzerlik_tepe_20261019/sablon/ek_tanilama.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sonuc_testi as st  # noqa: E402
from ortak import FS, OUT, SPLIT, TEMPL, TEMPL_ALT, load_dax, load_ndx, r_from_d, tpl_index, tpl_shape, window_lengths  # noqa: E402

COLS = ["f", "ufuk", "benzer_gun", "olay", "fark_esli_bp", "P_esli_asagi", "P_esli_yukari", "fark_esli_yari1_bp",
        "fark_esli_yari2_bp", "olay_medyan_bp", "olay_negatif_%"]


def main() -> None:
    out: dict = {}
    d = load_ndx(); ts = d.ts; c = np.log(d.close.to_numpy())
    tpl = tpl_index(ts); LS = window_lengths(tpl)
    tvec = {f: [tpl_shape(c, a, b, f) for a, b in tpl.values()] for f in FS}
    tpl_ts = {k: (ts.iloc[a], ts.iloc[b]) for k, (a, b) in tpl.items()}
    M = st.Market("NDX", d, tpl_ts, LS, tvec, SPLIT)
    spans = list(M.tpl.values())
    # (a) %5 eşik
    c5, _ = st.run_cells(M, M.D, spans, ("gelistirme",), pct_sim=5, pct_non=10)
    a = pd.DataFrame(c5)[COLS]; a.to_csv(OUT / "ek_esik5_ndx.csv", index=False)
    print("(a) %5 eşik (benzer olmayan > %10)\n", a.round(3).to_string(index=False))
    # (b) aile düzeyi plasebo
    real = pd.read_csv(OUT / "hucreler_ndx.csv"); real = real[real.donem == "gelistirme"]
    pl = pd.read_csv(OUT / "plasebo_hucreler.csv")
    piv = pl.pivot_table(index="p", columns=["f", "ufuk"], values="fark_esli_bp")
    pivm = pl.pivot_table(index="p", columns=["f", "ufuk"], values="olay_medyan_bp")
    res_b = {}
    for nm, pv, col in (("fark", piv, "fark_esli_bp"), ("olay_medyan", pivm, "olay_medyan_bp")):
        rk = pv.rank(pct=True)  # her plasebo setinin hücre içi yüzdeliği
        up = (rk >= 0.95).sum(1); dn = (rk <= 0.05).sum(1)
        rv = real.set_index(["f", "ufuk"])[col]
        rpct = {k: float((pv[k] <= rv[k]).mean()) for k in pv.columns}
        k_up = sum(v >= 0.95 for v in rpct.values()); k_dn = sum(v <= 0.05 for v in rpct.values())
        res_b[nm] = {"gercek_ust_%5_hucre": int(k_up), "gercek_alt_%5_hucre": int(k_dn),
                     "plasebo_ort_ust": float(up.mean()), "P(plasebo_ust>=gercek)": float((up >= k_up).mean()),
                     "P(plasebo_alt>=gercek)": float((dn >= k_dn).mean()),
                     "maks_yuzdelik_gercek": float(max(rpct.values())),
                     "P(plasebo_maks>=gercek_maks)": float((rk.max(1) >= max(rpct.values())).mean())}
    out["b_aile_plasebo"] = res_b
    print("(b)", json.dumps(res_b, ensure_ascii=False, indent=1))
    # (c) kendini tanıma
    thr = {f: np.percentile(M.D[f][M.dev_q & np.isfinite(M.D[f])], 2) for f in FS}
    selfrec = {}
    for k, (a_, b_) in tpl.items():
        qi = int(np.searchsorted(M.Q, b_, side="right")) - 1  # şablon bitişinde/öncesindeki son 20:00 sorgusu
        D1 = M.D[1.0][qi]
        selfrec[k] = {"sorgu": str(M.tq.iloc[qi]), "D": float(D1), "r": float(r_from_d(D1)),
                      "yuzdelik_%": 100 * float((M.D[1.0][M.dev_q] <= D1).mean()), "%2_benzer": bool(D1 <= thr[1.0]),
                      "en_yakin": list(tpl)[int(M.argt[1.0][qi])], "L": int(M.argL[1.0][qi])}
    out["c_kendini_tanima_f1"] = selfrec
    print("(c)", json.dumps(selfrec, ensure_ascii=False, indent=1))
    # (d) DAX–NDX tarih örtüşmesi (f=1 ve f=1/3, geliştirme, %2)
    dax = load_dax(); MD = st.Market("DAX", dax, tpl_ts, LS, tvec, st.DAX_SPLIT)
    ov = {}
    for f in (1 / 3, 1.0):
        tn = np.percentile(M.D[f][M.dev_q & np.isfinite(M.D[f])], 2)
        td = np.percentile(MD.D[f][MD.dev_q & np.isfinite(MD.D[f])], 2)
        nd = pd.to_datetime(M.tq[(M.D[f] <= tn) & M.dev_q & (M.tq >= pd.Timestamp("2020-01-01", tz="UTC")).to_numpy()].dt.date)
        dd = pd.to_datetime(MD.tq[(MD.D[f] <= td) & MD.dev_q].dt.date)
        near = [bool((abs((nd - x).dt.days) <= 3).any()) for x in dd]
        ov[f"f={f:.2f}"] = {"dax_benzer_gun": int(len(dd)), "ndx_2020+_benzer_gun": int(len(nd)),
                            "dax_gunlerinin_ndx_±3g_icinde_payi_%": 100 * float(np.mean(near)) if near else np.nan}
    out["d_dax_ndx_ortusme"] = ov
    print("(d)", json.dumps(ov, ensure_ascii=False, indent=1))
    # (e) görsel sınırlarla duyarlılık
    tpl2 = tpl_index(ts, TEMPL_ALT); LS2 = window_lengths(tpl2)
    tvec2 = {f: [tpl_shape(c, a, b, f) for a, b in tpl2.values()] for f in FS}
    tpl_ts2 = {k: (ts.iloc[a], ts.iloc[b]) for k, (a, b) in tpl2.items()}
    M2 = st.Market("NDX", d, tpl_ts2, LS2, tvec2, SPLIT)
    c2, _ = st.run_cells(M2, M2.D, list(M2.tpl.values()), ("gelistirme",))
    e = pd.DataFrame(c2)[COLS]; e.to_csv(OUT / "ek_gorsel_sinir_ndx.csv", index=False)
    print("(e) görsel sınırlar LS", LS2, "\n", e.round(3).to_string(index=False))
    (OUT / "ek_tanilama.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    main()
