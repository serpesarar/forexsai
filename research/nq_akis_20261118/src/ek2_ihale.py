"""EK-2: ihale etkisi × faiz rejimi (TNX 60 gün)."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
import ihale as I
ROOT = I.ROOT
sys.path.insert(0, str(ROOT / "research/moc_pencere_20261118/src"))
import moc
t = pd.read_parquet(ROOT / "research/qs03_akis_takvim_20261111/data/TNX.parquet")
if isinstance(t.columns, pd.MultiIndex): t.columns = t.columns.get_level_values(0)
t.index = pd.to_datetime(t.index).tz_localize(None).normalize()
tc = t.Close.astype(float)
up = (tc - tc.shift(60) > 0).shift(1)
a = I.auctions()
a = a[a.closing_time_comp.fillna("01:00 PM").eq("01:00 PM")]
out = {}
for src, (b, st) in {"duka": (I.G.ndx_bars(), 60), "mt5": moc.mt5_2m()}.items():
    D = I.intraday(b, st, a)
    D["up"] = [bool(up.asof(pd.Timestamp(z))) if pd.Timestamp(z) >= up.index[61] else False for z in D.index]
    for e in ("ESKI", "KESIF", "TEST"):
        z = D[D.era == e]
        non = ~z.ihale.values
        for rg, rm in (("yukselen", z.up.values), ("dusen", ~z.up.values)):
            out[f"{src}_{e}_{rg}"] = {"HI1_SAT": I.cmp(z, z.ihale.values & rm, "S780", non & rm),
                                     "HI2_zayif_SAT": I.cmp(z, z.zayif.values & rm, "S782", non & rm),
                                     "HI2_guclu_AL": I.cmp(z, z.guclu.values & rm, "L782", non & rm)}
            print(src, e, rg, {k: (v.get("n"), v.get("tetik"), v.get("fark"), v.get("P")) for k, v in out[f"{src}_{e}_{rg}"].items()})
I.U.RES.joinpath("ek2_ihale.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
