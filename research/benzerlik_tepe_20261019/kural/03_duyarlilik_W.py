"""ME-10 adım 3 — AİLE DIŞI duyarlılık (PROTOCOL §4 son madde): W = 6 ve 12'de aynı yöntemle yeniden türetilmiş K1.

Başarı ailesine girmez; yalnız "W seçimi sonucu değiştiriyor mu?" sorusu için tanımlayıcı.
Çalıştır: nice -n 10 python3.13 research/benzerlik_tepe_20261019/kural/03_duyarlilik_W.py | tee results/03_stdout.txt
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("kt02", HERE / "02_kural_testi.py")
kt02 = importlib.util.module_from_spec(spec); spec.loader.exec_module(kt02)  # type: ignore[union-attr]
from tepe_ozellik import load_dax, load_ndx  # noqa: E402


def main() -> None:
    rows = []
    for Wx in (6, 12):
        kt02.W = Wx
        nd = kt02.Market("NDX", load_ndx(), 20, False, ("2016-01-01", "2021-01-01"))
        dx = kt02.Market("DAX", load_dax(), 19, True, ("2020-01-01", "2023-01-01"))
        qd = pd.Series(nd.ts.dt.date.to_numpy())
        kt = {nm: int(np.flatnonzero((qd == pd.Timestamp(v).date()).to_numpy())[0]) for nm, v in kt02.TEMPL_END.items()}
        k1 = kt02.derive_k1(nd.f, kt, ("T1_incel", "T2", "T3"))
        for mk in (nd, dx):
            fire = kt02.rule(mk.f, k1); ev = kt02.events(fire)
            for hn in mk.H:
                base = mk.base(hn, fire)
                for et in ("olusum", "tamamlanma"):
                    st = kt02.cell_stats(mk, ev[et], hn, base, "gelistirme")
                    rows.append({"W": Wx, "piyasa": mk.name, "olay": et, "ufuk": hn, **st})
    c = pd.DataFrame(rows)
    c.to_csv(HERE / "results/03_duyarlilik_W.csv", index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
    print(c[["W", "piyasa", "olay", "ufuk", "n_olay", "ort_bp", "fark_esli_bp", "fark_esli_medyan_bp", "fark_esli_negatif_pay_%",
             "P_fark<0", "P_fark>0", "fark_esli_yari1_bp", "fark_esli_yari2_bp", "plasebo_yuzdelik_%"]].round(2).to_string(index=False))


if __name__ == "__main__":
    main()
