"""VR (varyans oranı) — geometri pürüzlülük kapısı: 1m 5 dönem + 30m/15m uzun veri.
Tahmin: VR>1 (kalıcı yol) → TP<SL braketi (80/110) kötü, TP>SL braketi iyi; yön-bağımsız S=(B+S)/2."""
import numpy as np, pandas as pd
from evaluate import load, PER
from common import block_boot
from features import rolling_vr
from long_data import load_long
import daylevel_trades as dt
pd.set_option("display.width", 250)
d = load(1)
for g in ["G80", "GS", "GR"]:
    d[f"S_{g}"] = (d[f"R_{g}_B"] + d[f"R_{g}_S"]) / 2
    d[f"y_{g}"] = d[f"S_{g}"] - d.groupby(["period", "utc_h"])[f"S_{g}"].transform("mean")
q = pd.cut(d.vr15, [0, .6, .8, 1.0, 1.2, 10], labels=["<.6", ".6-.8", ".8-1", "1-1.2", ">1.2"])
for g in ["G80", "GR"]:
    t = d.groupby([q, "period"], observed=True)[f"y_{g}"].mean().unstack()[PER]
    print(f"\n1m S_{g} (yapı) − saat tabanı, VR15(240dk) kovası"); print(t.round(3).to_string())
# 30m / 15m: VR(q=4 bar) son 48 bar; yüzde braket B+S ortalaması
for tf, q_, win in [("30m", 4, 48), ("15m", 4, 64)]:
    T = dt.long_trades(tf)
    L = load_long(tf)
    lr = np.log(L.close).diff().to_numpy()
    vr = rolling_vr(np.nan_to_num(lr), q_, win)
    L["vr"] = vr
    T = T.merge(L[["ts", "vr"]], on="ts", how="left")
    T["S"] = (T.R_B + T.R_S) / 2
    T["y"] = T.S - T.groupby(["grp", "utc_h"]).S.transform("mean")
    qq = pd.cut(T.vr, [0, .6, .8, 1.0, 1.2, 10], labels=["<.6", ".6-.8", ".8-1", "1-1.2", ">1.2"])
    t = T.groupby([qq, "grp"], observed=True).y.mean().unstack()
    t["n"] = T.groupby(qq, observed=True).size()
    print(f"\n{tf} S_%80/110 (yapı) − yıl×saat tabanı, VR kovası"); print(t.round(3).to_string())
