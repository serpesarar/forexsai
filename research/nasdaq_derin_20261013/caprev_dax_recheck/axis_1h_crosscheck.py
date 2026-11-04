"""1h dosyasının hizası: (a) 30m→1h toplamı ile etiket-eşleşmesi (2021-03+), (b) yaz/kış saatlik profil kıyası (2019+)."""
from pathlib import Path
import numpy as np, pandas as pd
GF = Path("/Users/melihcanodacioglu/Desktop/panel/research/ndx_gate_forge/data")
h = pd.read_parquet(GF / "dax_1h.parquet"); m = pd.read_parquet(GF / "dax_30m.parquet")
m["hts"] = m.ts.dt.floor("h")
agg = m.groupby("hts").agg(o=("open", "first"), hi=("high", "max"), lo=("low", "min"), c=("close", "last"), n=("ts", "size"))
agg = agg[agg.n == 2]
for sh in (-60, 0, 60):
    x = h.assign(k=h.ts + pd.Timedelta(minutes=sh)).merge(agg, left_on="k", right_index=True)
    ok = (np.isclose(x.high, x.hi, atol=0.05) & np.isclose(x.low, x.lo, atol=0.05))
    print(f"1h etiketi + {sh:+d} dk = 30m toplamı: eşleşme {ok.mean():.3f} (n={len(x)})")
# yıl × yaz/kış: medyan aralığın saatlik profili, tepe UTC saati ve 2. tepe
h = h[(h.ts >= "2019-01-01") & (h.ts.dt.weekday <= 4)].copy()
h["u"] = h.ts.dt.hour; h["rng"] = h.high - h.low
h["ny_dst"] = h.ts.dt.tz_convert("America/New_York").map(lambda t: bool(t.dst()))
h["y"] = h.ts.dt.year
p = h.groupby(["y", "ny_dst", "u"]).rng.median().unstack("u")
print((p[[4, 5, 6, 7, 8, 9]].div(p[[4, 5, 6, 7, 8, 9]].max(axis=1), axis=0)).round(2).to_string())
