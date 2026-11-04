"""Aylık premium/mark/index 1m dosyalarındaki TAM-GÜN boşluklarını günlük zip'lerle yamala.

Kullanım: python -I 01b_patch_daily.py <raw_dir> <out_dir>
out_dir/{premium,mark,index}_1m.parquet içinde 1440 dakikanın tamamı eksik olan
günleri bulur, günlük zip'i (SHA256 doğrulamalı) <raw>/<ad>/ altına indirir.
"""
from __future__ import annotations
import sys
from pathlib import Path
import importlib.util
import pandas as pd

spec = importlib.util.spec_from_file_location("dl", str(Path(__file__).with_name("01_download.py")))
dl = importlib.util.module_from_spec(spec); spec.loader.exec_module(dl)

MAP = {"premium_1m": ("um_premium", "premiumIndexKlines"), "mark_1m": ("um_mark", "markPriceKlines"),
       "index_1m": ("um_index", "indexPriceKlines")}


def main() -> None:
    raw, out = Path(sys.argv[1]), Path(sys.argv[2])
    for fn, (d, kind) in MAP.items():
        df = pd.read_parquet(out / f"{fn}.parquet", columns=["ts"])
        cnt = df["ts"].dt.floor("D").value_counts()
        days = pd.date_range("2021-06-01", "2026-10-20", tz="UTC")
        miss = [x for x in days if cnt.get(x, 0) < 1440]
        for day in miss:
            s = day.strftime("%Y-%m-%d")
            key = f"data/futures/um/daily/{kind}/BTCUSDT/1m/BTCUSDT-1m-{s}.zip"
            st = dl.get(key, raw / d / key.rsplit("/", 1)[-1])
            print(fn, s, cnt.get(day, 0), st, flush=True)


if __name__ == "__main__":
    main()
