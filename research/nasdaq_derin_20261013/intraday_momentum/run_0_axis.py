"""Adım 0: saat ekseni testi (sonuçlara bakmadan). Medyan aralığın tepe dakikası."""
import json
from imcore import load_ndx, load_dax, axis_check, RES
out = {}
for tf, step in [("1m", 1), ("30m", 30), ("1h", 60)]:
    pk = axis_check(load_ndx(tf), "America/New_York", step)
    out[f"NDX_{tf}"] = pk.values.tolist(); print("NDX", tf); print(pk.to_string(index=False))
for tf, step in [("30m", 30), ("15m", 15)]:
    pk = axis_check(load_dax(tf), "Europe/Berlin", step)
    out[f"DAX_{tf}"] = pk.values.tolist(); print("DAX", tf); print(pk.to_string(index=False))
json.dump(out, open(RES / "axis_check.json", "w"), default=str, indent=1)
