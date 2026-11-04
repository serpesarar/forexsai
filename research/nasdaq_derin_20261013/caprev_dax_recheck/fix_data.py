"""Düzeltilmiş veri kopyaları (orijinallere DOKUNMAZ) → caprev_dax_recheck/data_fixed/.

DAX (axis_dax.py / axis_volume.py kanıtı): NY standart saatindeyken etiket 60 dk ERKEN → +60 dk.
  Mekanizma: broker saati (NY+7 = UTC+2 kış / UTC+3 yaz) sabit −3 saatle UTC'ye çevrilmiş.
  NY'nin DST durumu düzeltilmiş (gerçek) zamanda değerlendirilir; geçişler hafta sonuna düştüğü için
  etiket zamanında değerlendirmek aynı sonucu verir (kontrol edilir).
NDX long_1h (axis_ndx_long.py kanıtı): NY tarihi 2017-11-05 … LATE_END arası etiket 60 dk GEÇ → −60 dk.
  İki varyant: LATE_END = 2018-02-26 (nakit kapanış eşleşmesi) ve 2018-03-02 (Pazar açılış saati kanıtı).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, "/Users/melihcanodacioglu/Desktop/panel/research/ndx_gate_forge")
from long_data import load_long  # noqa: E402

GF = Path("/Users/melihcanodacioglu/Desktop/panel/research/ndx_gate_forge/data")
FIX = Path(__file__).resolve().parent / "data_fixed"
FIX.mkdir(exist_ok=True)
HOUR = pd.Timedelta(minutes=60)


def ny_std(ts: pd.Series) -> pd.Series:
    return ~ts.dt.tz_convert("America/New_York").map(lambda t: bool(t.dst()))


def fix_dax(tf: str) -> pd.DataFrame:
    d = pd.read_parquet(GF / f"dax_{tf}.parquet").copy()
    lab_std = ny_std(d.ts)
    true_std = ny_std(d.ts + HOUR)
    if (lab_std != true_std).any():
        print(f"  uyarı {tf}: {int((lab_std != true_std).sum())} barda etiket/gerçek DST farklı → gerçek esas")
    d.loc[true_std, "ts"] = d.ts[true_std] + HOUR
    n0 = len(d)
    d = d.sort_values("ts").drop_duplicates("ts", keep="last").reset_index(drop=True)
    print(f"  DAX {tf}: {int(true_std.sum())}/{n0} bar +60 dk; çakışmadan atılan {n0 - len(d)}")
    return d


def fix_ndx_long(late_end: str) -> pd.DataFrame:
    d = load_long("1h").copy()
    nyd = d.ts.dt.tz_convert("America/New_York").dt.tz_localize(None).dt.normalize()
    m = (nyd >= "2017-11-05") & (nyd <= late_end)
    d.loc[m, "ts"] = d.ts[m] - HOUR
    n0 = len(d)
    d = d.sort_values("ts").drop_duplicates("ts", keep="first").reset_index(drop=True)
    print(f"  NDX 1h (→{late_end}): {int(m.sum())} bar −60 dk; çakışmadan atılan {n0 - len(d)}")
    return d


if __name__ == "__main__":
    for tf in ("1h", "30m", "15m"):
        fix_dax(tf).to_parquet(FIX / f"dax_{tf}.parquet")
    for tag, end in (("a", "2018-02-26"), ("b", "2018-03-02")):
        fix_ndx_long(end).to_parquet(FIX / f"ndx_long_1h_fix{tag}.parquet")
