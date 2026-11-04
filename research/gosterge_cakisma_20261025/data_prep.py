"""EK-5: ilk envanterde atlanan 1m kaynaklarını UTC'ye hizalayıp data/ altına sabitle.

- DAX 1m  ← ndx_buy_lab/data/bars_1m_gdaxi.csv (candle_cache, 07-28 dökümü). 2026-04-24 öncesi broker sunucu saatinde:
            2026-03-01 öncesi −2 s (UTC+2), sonrası −3 s (UTC+3). Doğrulama: Xetra açılış oynaklık tepesi haftalık mod
            kışın 08, yazın 07 UTC'ye oturuyor (düzeltme öncesi 10–11).
- XAU 1m  ← decider_xau_ileri_20261021/data/xau_1m_utc.csv.gz (indicator_snapshots broker barları, satır bazlı
            created_at gecikmesiyle UTC'ye çevrilmiş; Yahoo yok).
- USOIL 1m ← wti_transfer_20261002/data/clean_1m.parquet (temizlenmiş broker 1m; açılış tepesi 13–14 UTC).
"""
import numpy as np
import pandas as pd

import config as C

OUT = C.HERE / "data"


def dax_1m() -> pd.DataFrame:
    d = pd.read_csv(C.R / "ndx_buy_lab/data/bars_1m_gdaxi.csv")
    d["ts"] = pd.to_datetime(d.ts, utc=True)
    a, b = pd.Timestamp("2026-03-01", tz="UTC"), pd.Timestamp("2026-04-24", tz="UTC")
    off = np.where(d.ts < a, 2, np.where(d.ts < b, 3, 0))
    d["ts"] = d.ts - pd.to_timedelta(off, unit="h")
    return d.sort_values("ts").drop_duplicates("ts")[["ts", "open", "high", "low", "close", "volume"]]


def xau_1m() -> pd.DataFrame:
    d = pd.read_csv(C.R / "decider_xau_ileri_20261021/data/xau_1m_utc.csv.gz").rename(columns={"t_utc": "ts"})
    d["ts"] = pd.to_datetime(d.ts, utc=True)
    return d.sort_values("ts").drop_duplicates("ts")[["ts", "open", "high", "low", "close", "volume"]]


def usoil_1m() -> pd.DataFrame:
    d = pd.read_parquet(C.R / "wti_transfer_20261002/data/clean_1m.parquet")
    d["ts"] = pd.to_datetime(d.ts, utc=True)
    return d.sort_values("ts").drop_duplicates("ts")[["ts", "open", "high", "low", "close", "volume"]]


def main() -> None:
    OUT.mkdir(exist_ok=True)
    for name, fn in (("DAX_1m", dax_1m), ("XAU_1m", xau_1m), ("USOIL_1m", usoil_1m)):
        d = fn()
        d.to_parquet(OUT / f"{name}.parquet", index=False)
        print(name, len(d), d.ts.min(), d.ts.max())


if __name__ == "__main__":
    main()
