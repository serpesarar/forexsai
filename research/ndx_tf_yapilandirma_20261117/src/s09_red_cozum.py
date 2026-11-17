"""Adım 9 — MT5 kökenli kopyaların REDDEDİLEN her günü, son çıktılardan hangisinin o günü kapsadığına bağlanır.

Bir kopya günü reddedildiyse o günün verisi kaybolmuş olmamalı: ya (a) son MT5 1 dk birleşimi o günü MT5'in yerli M5
barlarıyla birebir kapsıyordur (2/3/90/210 dk o günden üretildi), ya (b) gün USTEC beslemesinin günüdür ve USTEC json'u
o günü birebir taşır, ya (c) MT5 90/210 dk o gün yerli M5/M15/M30'dan üretilmiştir (yalnız 2/3 dk eksik kalır).
Hiçbirine girmeyen gün `kapsanmadi` olarak listelenir.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import kaynak as K  # noqa: E402
import s03_uret as U  # noqa: E402
import s05_ek_kaynak as S  # noqa: E402

BASE = Path(__file__).resolve().parents[1]


def main() -> None:
    g = pd.read_csv(BASE / "results/s05_gun_hukumleri.csv", parse_dates=["gun"])
    srcs = U.mt5_sources()
    m1_all, _ = U.mt5_m1_with_copies(srcs["M1"])
    natives = {5: srcs["M5"], 15: srcs["M15"], 30: srcs["M30"]}
    full_m1 = S.day_verdicts(m1_all, 1, natives)
    m1_days = set(full_m1.index[full_m1["kabul"]])
    mt5_90 = pd.read_parquet(BASE / "out/MT5/NDX_MT5_90m.parquet")
    d90 = set(S.trading_day(mt5_90["t"].to_numpy()))
    us = U.ustec_1m()
    us_days = set(np.unique(S.trading_day(us["t"].to_numpy())))
    red = g[~g["nas100_kabul"]].copy()
    gun = red["gun"].to_numpy(dtype="datetime64[ns]")

    def status(d: np.datetime64, ustec_ok: bool) -> str:
        if d in m1_days:
            return "MT5_1dk_birlesiminde_tam (2/3/90/210 o günden)"
        if ustec_ok and d in us_days:
            return "USTEC_beslemesinde (json birebir)"
        if d in us_days and d in d90:
            return "USTEC_beslemesinde + MT5_90/210 (kopya kaymış/eksikti)"
        if d in d90:
            return "MT5_90/210_yerli_barlardan (2/3 dk yok: o gün NAS100 1 dk yok)"
        return "kapsanmadi"
    red["cozum"] = [status(d, u) for d, u in zip(gun, red["ustec_kabul"])]
    red.to_csv(BASE / "results/s09_red_gun_cozumu.csv", index=False)
    summ = red.groupby(["dosya", "cozum"]).size().unstack(fill_value=0)
    rep = {"red_gun_toplam": int(len(red)), "cozum_dagilimi": red["cozum"].value_counts().to_dict(),
           "dosya_bazinda": {k: {c: int(v) for c, v in row.items() if v} for k, row in summ.iterrows()},
           "kapsanmadi_ornek": red[red["cozum"] == "kapsanmadi"][["dosya", "gun"]].astype(str).head(40).to_dict("records")}
    (BASE / "results/s09_red_gun_cozumu.json").write_text(json.dumps(rep, indent=1, ensure_ascii=False))
    print(json.dumps({k: rep[k] for k in ("red_gun_toplam", "cozum_dagilimi", "kapsanmadi_ornek")}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
