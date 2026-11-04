"""NDX long_1h saat ekseni: 16:00 ET kapanışı NDXCASH günlük kapanışıyla eşleştirme (gün bazında), kayma ∈ {−60,0,+60}.

Her gün için: etiket NY dakikası (900+s) başlayan barın kapanışı ile NDXCASH_close arasındaki |fark|; en küçük
farkı veren s günün oyu. Ay bazında oy dağılımı + 0'dan farklı oyların ardışık bölütleri.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, "/Users/melihcanodacioglu/Desktop/panel/research/ndx_gate_forge")
from long_data import load_long, macro  # noqa: E402

OUT = Path(__file__).resolve().parent / "results"

d = load_long("1h")
ny = d.ts.dt.tz_convert("America/New_York")
d["date"] = pd.to_datetime(ny.dt.date.values)
d["m"] = (ny.dt.hour * 60 + ny.dt.minute).values
cash = macro().NDXCASH_close.dropna()
piv = d.pivot_table(index="date", columns="m", values="close", aggfunc="last")
rows = []
for s in (-60, 0, 60):
    col = 900 + s
    if col in piv.columns:
        rows.append((s, (piv[col] - cash.reindex(piv.index)).abs() / cash.reindex(piv.index)))
err = pd.concat({s: e for s, e in rows}, axis=1).dropna()
vote = err.idxmin(axis=1)
marg = err.apply(lambda r: np.sort(r.to_numpy())[1] - r.min(), axis=1)
v = pd.DataFrame({"oy": vote, "marj_bp": (marg * 1e4).round(1)})
v["ay"] = v.index.strftime("%Y-%m")
tab = v.groupby("ay").oy.value_counts(normalize=True).unstack(fill_value=0).round(2)
tab["n"] = v.groupby("ay").size()
odd = tab[tab.get(0, 0) < 0.6]
print("0-oyu < %60 olan aylar:")
print(odd.to_string())
strong = v[(v.oy != 0) & (v.marj_bp >= 5)]
print(f"\nGüçlü (marj ≥5 bp) sıfır-dışı günler: {len(strong)} / {len(v)}")
print(strong.groupby(strong.ay).oy.agg(["size", lambda s: s.value_counts().to_dict()]).to_string())
w = v.loc["2017-10-15":"2018-03-31"]
print("\n2017-10-15 → 2018-03-31 gün bazında:")
print(w.to_string())
v.to_csv(OUT / "axis_ndx_long_1h_days.csv")
