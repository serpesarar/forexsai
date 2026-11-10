"""Broker M30 gün tablosu (seans 09:30–16:00 ET) ve gece getirisi. Sunucu saati = New York + 7."""
import json
from pathlib import Path
import numpy as np, pandas as pd
MT5 = Path(__file__).resolve().parents[1] / "c1_turev_20261105/data/mt5"
def meta():
    m = {}
    for f in ("meta.json", "meta2.json"): m.update({k: v for k, v in json.loads((MT5 / f).read_text()).items() if isinstance(v, dict)})
    return m
def gun_tablosu(sym: str) -> pd.DataFrame:
    x = pd.read_csv(MT5 / f"{sym}_M30.csv.gz"); pt = meta()[sym]["point"]
    x["et"] = pd.to_datetime(x.t, unit="s") - pd.Timedelta(hours=7); x = x[x.et.dt.dayofweek < 5].reset_index(drop=True)
    x["d"] = x.et.dt.normalize(); x["m"] = x.et.dt.hour * 60 + x.et.dt.minute; x["sp"] = x.sp * pt
    ses = x[(x.m >= 570) & (x.m < 960)]; g = ses.groupby("d")
    t = pd.DataFrame({"hi": g.h.max(), "lo": g.l.min(), "nbar": g.size()})
    for nm, mm in (("o930", 570), ("o1500", 900), ("o1530", 930), ("o1600", 960), ("o1630", 990)):
        b = x[x.m == mm].drop_duplicates("d").set_index("d"); t[nm] = b.o; t["sp_" + nm] = b.sp
    t = t[t.nbar >= 12].dropna(subset=["o930", "o1500", "o1600"]); t["c"] = t.o1600                      # seans kapanışı ≈ 16:00 barının açılışı
    t["r"] = np.log(t.c / t.c.shift(1)); t["ibs"] = (t.c - t.lo) / (t.hi - t.lo); t["son_saat"] = (t.c / t.o1500 - 1) * 1e4; t["son_yarim"] = (t.c / t.o1530 - 1) * 1e4
    nx = t.shift(-1); gap = (pd.Series(t.index, index=t.index).shift(-1) - pd.Series(t.index, index=t.index)).dt.days
    t["gece_n"] = gap.clip(upper=3)                                                                    # swap gecesi (Cuma→Pzt 3)
    t["y_brut"] = (nx.o930 / t.c - 1) * 1e4
    t["maliyet"] = ((t.sp_o1600.fillna(t.sp_o1600.median()) * 1.5) / t.c) * 1e4 + 1.8 * t.gece_n          # spread×1,5 (girişte ask) + swap
    t["y_net"] = t.y_brut - t.maliyet; t["y_gunduz"] = (nx.o1600 / nx.o930 - 1) * 1e4
    return t[gap <= 4]
