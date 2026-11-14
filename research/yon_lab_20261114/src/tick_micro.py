"""Faz 6 — Dukascopy 2025 tick (bid/ask, hacim YOK) → 1m mikroyapı: kotasyon sayısı, ort. spread, tick-yönü dengesizliği
(mid artış − azalış sayısı), mid değişim mutlak toplamı. Çıktı data/tick_micro_2025.parquet (t = dakika açılışı UTC)."""
import glob
from pathlib import Path
import numpy as np
import pandas as pd

SRC = Path.home() / 'dukascopy_us100/data'
OUT = Path(__file__).resolve().parents[1] / 'data/tick_micro_2025.parquet'
parts = []
for d in sorted(SRC.iterdir()):
    for f in sorted(d.glob('*.csv')):
        if f.stat().st_size < 50:
            continue
        try:
            x = pd.read_csv(f, dtype={'timestamp': 'int64', 'askPrice': 'float64', 'bidPrice': 'float64'})
        except Exception:  # noqa: BLE001 — boş/bozuk gün dosyası
            continue
        if x.empty:
            continue
        mid = (x.askPrice + x.bidPrice) / 2
        dm = np.sign(np.diff(mid.to_numpy(), prepend=mid.iloc[0]))
        t = (x.timestamp // 60000) * 60
        g = pd.DataFrame({'t': t, 'up': dm > 0, 'dn': dm < 0, 'spr': x.askPrice - x.bidPrice,
                          'adm': np.abs(np.diff(mid.to_numpy(), prepend=mid.iloc[0]))}).groupby('t')
        parts.append(pd.DataFrame({'nq': g.size(), 'up': g.up.sum(), 'dn': g.dn.sum(), 'spr': g.spr.mean(),
                                   'path': g.adm.sum()}).reset_index())
m = pd.concat(parts).groupby('t', as_index=False).sum(numeric_only=True)
m.to_parquet(OUT, index=False)
print(len(m), pd.to_datetime(m.t.min(), unit='s'), pd.to_datetime(m.t.max(), unit='s'))
