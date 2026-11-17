"""Adım 7 — ~/dukascopy_us100 (2025 Dukascopy tikleri, dukascopy-node) → 1 dk BID OHLC.

Dukascopy'nin kendi 1 dk mumu BID tiklerinden kurulur: dakikanın ilk/en yüksek/en düşük/son bid'i. Aynı kuralla kurulan
mumun ana 1 dk dosyasıyla ortak dakikalarda birebir olduğu s03'te dayatılır; tutarsa ana dosyada eksik olan dakikalar
(2025'te dakikaların ~%26'sı) bu tiklerden doldurulur. Çıktı: out/ek/duka_2025_tik_1m.parquet (git dışı).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parents[1]
TICK_DIR = Path.home() / "dukascopy_us100/data"
OUT = BASE / "out/ek/duka_2025_tik_1m.parquet"


def day_to_1m(f: Path) -> pd.DataFrame:
    if f.stat().st_size == 0:  # tatil / hafta sonu: boş dosya
        return pd.DataFrame()
    x = pd.read_csv(f, usecols=["timestamp", "bidPrice"])
    if x.empty:
        return x
    x = x.sort_values("timestamp", kind="stable")
    m = (x["timestamp"] // 60000) * 60
    g = x.groupby(m.to_numpy())["bidPrice"]
    return pd.DataFrame({"t": g.first().index.astype(np.int64), "open": g.first().to_numpy(), "high": g.max().to_numpy(),
                         "low": g.min().to_numpy(), "close": g.last().to_numpy(), "n_tik": g.size().to_numpy()})


def main() -> None:
    files = sorted(TICK_DIR.glob("*/usatechidxusd-tick-*.csv"))
    parts = [day_to_1m(f) for f in files]
    out = pd.concat([p for p in parts if len(p)]).drop_duplicates("t").sort_values("t").reset_index(drop=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(OUT, index=False)
    print(len(files), "gün dosyası →", len(out), "dk", pd.to_datetime(out.t.min(), unit="s"), pd.to_datetime(out.t.max(), unit="s"))


if __name__ == "__main__":
    main()
