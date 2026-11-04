"""EK-1 (veri; sonuçtan önce): Binance spot arşivinde iki blok dakika-dışı açılış damgası taşıyor
(2017-12-04 06:00:20.799 → 2017-12-18 10:00:20.799, 20.401 bar, +20,799 s; 2018-02-09 09:59:14.789 → 2018-02-10 05:59:14.789,
1.201 bar, +14,789 s). Orijinal hat (2021+) bu durumla hiç karşılaşmadı. lt.tmin ve resample bu damgaları zaten dakikaya
TABANLAR (floor); burada aynı tabanlamayı btc_1m.parquet'e açıkça uygularız ki 1m ızgara birleştirmeleri (assemble) de tutarlı olsun.
Tek çakışma (2017-12-04 06:00: gerçek bar + sıfır-hacimli kaymış bar) → dakika-hizalı gerçek bar tutulur (resample zaten aynı kovaya topluyordu).
Kullanım: python -I -B 02b_floor_offgrid.py <data_dir>
"""
import json
import sys
from pathlib import Path

import pandas as pd

d = Path(sys.argv[1])
m = pd.read_parquet(d / "btc_1m.parquet")
off = m["ts"] != m["ts"].dt.floor("1min")
rep = {"offgrid_rows": int(off.sum()),
       "offsets_s": (m.loc[off, "ts"] - m.loc[off, "ts"].dt.floor("1min")).dt.total_seconds().round(3).value_counts().to_dict()}
m["ts"] = m["ts"].dt.floor("1min")
rep["dup_after_floor"] = int(m["ts"].duplicated().sum())
rep["dup_rows_dropped_keep_first_ongrid"] = m.loc[m["ts"].duplicated(keep=False)].astype(str).to_dict("records")
m = m.drop_duplicates("ts", keep="first").reset_index(drop=True)
assert rep["dup_after_floor"] <= 1 and not m["ts"].duplicated().any()
assert m["ts"].is_monotonic_increasing
m.to_parquet(d / "btc_1m.parquet", index=False)
(d / "offgrid_fix_report.json").write_text(json.dumps(rep, indent=1, default=str))
print(rep)
# üst TF'leri tabanlanmış 1m'den yeniden üret (build_spot.resample aynen)
sys.path.insert(0, str(Path(__file__).resolve().parent / "port"))
import build_spot as BS  # noqa: E402

for k, rule in BS.TFS.items():
    old = pd.read_parquet(d / f"btc_{k}.parquet")
    new = BS.resample(m, rule)
    cols = ["open", "high", "low", "close"]
    same = len(old) == len(new) and (old["ts"].values == new["ts"].values).all() and all(
        (old[c].values == new[c].values).all() for c in cols)
    new.to_parquet(d / f"btc_{k}.parquet", index=False)
    print(k, "satır", len(new), "OHLC eski ile aynı:", bool(same))
