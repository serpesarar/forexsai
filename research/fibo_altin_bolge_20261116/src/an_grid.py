"""an_grid.py — ızgara seçimi (KEŞİF n ≥ 60) → TEST/KÖR; gerçek vs plasebo t tavanı; aile ortalamaları."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

import fblib as F

N_MIN = 60
KEYS = ["tf", "side", "pattern", "zone", "sl", "tp", "hold", "smin", "spmin", "filt"]


def main() -> None:
    g = pd.concat([pd.read_parquet(F.RESULTS / f"grid_{tf}.parquet") for tf in F.TFS_NDX], ignore_index=True)
    g["n_TK"] = g.n_TEST + g.n_KOR
    g["R_TK"] = (g.R_TEST.fillna(0) * g.n_TEST + g.R_KOR.fillna(0) * g.n_KOR) / g.n_TK.replace(0, np.nan)
    e = g[g.n_KESIF >= N_MIN].copy()
    out = {"hucre_toplam": len(g), "kesif_n60": len(e)}
    out["gercek_t_tavan"] = float(e.t_KESIF.max())
    out["plasebo_t_tavan"] = float(e.pt_KESIF.max())
    out["gercek_t>2"] = int((e.t_KESIF > 2).sum())
    out["plasebo_t>2"] = int((e.pt_KESIF > 2).sum())
    out["gercek_t<-2"] = int((e.t_KESIF < -2).sum())
    out["plasebo_t<-2"] = int((e.pt_KESIF < -2).sum())
    out["ort_R_KESIF_gercek"] = float(e.R_KESIF.mean())
    out["ort_R_KESIF_plasebo"] = float(e.pR_KESIF.mean())
    top = e.sort_values("t_KESIF", ascending=False).head(20)
    out["ilk20_TEST_arti"] = int((top.R_TEST > 0).sum())
    out["ilk20_KOR_arti"] = int((top.R_KOR > 0).sum())
    out["ilk20_ikisi_arti"] = int(((top.R_TEST > 0) & (top.R_KOR > 0)).sum())
    out["ilk20_ort_TEST"] = float(top.R_TEST.mean())
    out["ilk20_ort_KOR"] = float(top.R_KOR.mean())
    # aynı seçim plasebo ızgarasında (boş dağılım için)
    ptop = e.sort_values("pt_KESIF", ascending=False).head(20)
    out["plasebo_ilk20_TEST_arti"] = int((ptop.pR_TEST > 0).sum())
    out["plasebo_ilk20_KOR_arti"] = int((ptop.pR_KOR > 0).sum())
    # ilk 200'ün işaret tutarlılığı
    t200 = e.sort_values("t_KESIF", ascending=False).head(200)
    out["ilk200_TEST_ve_KOR_arti_oran"] = float(((t200.R_TEST > 0) & (t200.R_KOR > 0)).mean())
    out["tum_TEST_ve_KOR_arti_oran"] = float(((e.R_TEST > 0) & (e.R_KOR > 0)).mean())
    cols = KEYS + ["n_KESIF", "R_KESIF", "t_KESIF", "pR_KESIF", "n_TEST", "R_TEST", "pR_TEST", "n_KOR", "R_KOR",
                   "pR_KOR"]
    top[cols].round(4).to_csv(F.RESULTS / "grid_ilk20.csv", index=False)
    # aile ortalamaları (seçimsiz): her boyutun her değeri için tüm hücrelerin ortalama R'si, dönem bazında
    fam = []
    for k in KEYS:
        for v, gg in e.groupby(k):
            fam.append({"boyut": k, "deger": v, "hucre": len(gg), "R_KESIF": gg.R_KESIF.mean(),
                        "R_TEST": gg.R_TEST.mean(), "R_KOR": gg.R_KOR.mean(), "pR_KESIF": gg.pR_KESIF.mean(),
                        "pR_TEST": gg.pR_TEST.mean(), "pR_KOR": gg.pR_KOR.mean()})
    pd.DataFrame(fam).round(4).to_csv(F.RESULTS / "grid_aile.csv", index=False)
    # üç dönemde de artı ve plasebodan iyi hücreler (şans beklentisiyle birlikte)
    tri = g[(g.n_KESIF >= N_MIN) & (g.n_TEST >= 30) & (g.n_KOR >= 30)]
    good = tri[(tri.R_KESIF > 0) & (tri.R_TEST > 0) & (tri.R_KOR > 0) & (tri.R_KESIF > tri.pR_KESIF)
               & (tri.R_TEST > tri.pR_TEST) & (tri.R_KOR > tri.pR_KOR)]
    ptri = tri[(tri.pR_KESIF > 0) & (tri.pR_TEST > 0) & (tri.pR_KOR > 0)]
    out["uc_donem_arti_ve_plasebodan_iyi"] = int(len(good))
    out["uc_donem_hucre"] = int(len(tri))
    out["plasebo_uc_donem_arti"] = int(len(ptri))
    out["gercek_uc_donem_arti"] = int(((tri.R_KESIF > 0) & (tri.R_TEST > 0) & (tri.R_KOR > 0)).sum())
    good.sort_values("t_KESIF", ascending=False)[cols].round(4).to_csv(F.RESULTS / "grid_uc_donem.csv", index=False)
    (F.RESULTS / "grid_ozet.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))
    print(top[cols].round(3).to_string())


if __name__ == "__main__":
    main()
