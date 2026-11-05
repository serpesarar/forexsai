"""DTS-07 ön koşulu — 15m arşiv saat ekseni denetimi (E78). Her ay, beklenen olay dakikasında |getiri| tepesi var mı."""
import numpy as np
import pandas as pd
from common import load

# sembol: (yerel saat dilimi, beklenen yerel bar açılışı, haftanın günleri filtresi)
EXP = {"NDX": ("America/New_York", "09:30", None), "GDAXI": ("Europe/Berlin", "09:00", None),
       "USOIL": ("America/New_York", "10:30", {2}), "XAUUSD": ("America/New_York", "08:30", None)}

rows = []
for sym, (tz, hhmm, dows) in EXP.items():
    d = load(sym, "15m")
    d["r"] = np.log(d.close / d.close.shift(1)).abs()
    d = d[(d.ts.diff().dt.total_seconds() == 900)]
    loc = d.ts.dt.tz_convert(tz)
    d = d.assign(m=loc.dt.strftime("%Y-%m"), t=loc.dt.strftime("%H:%M"), dow=loc.dt.dayofweek)
    if dows:
        d = d[d.dow.isin(dows)]
    else:
        d = d[d.dow < 5]
    for m, g in d.groupby("m"):
        prof = g.groupby("t").r.mean()
        if len(prof) < 20:
            continue
        top = prof.idxmax()
        exp_v = prof.get(hhmm, np.nan)
        rank = int((prof > exp_v).sum()) if np.isfinite(exp_v) else -1
        off = (pd.Timestamp("2000-01-01 " + top) - pd.Timestamp("2000-01-01 " + hhmm)).total_seconds() / 60
        rows.append({"sym": sym, "ay": m, "tepe": top, "kayma_dk": off, "beklenen_sira": rank})
df = pd.DataFrame(rows)
df["temiz"] = df.beklenen_sira.between(0, 2)        # beklenen bar ayın en oynak ilk 3 barından biri
df.to_csv("eksen_denetimi.csv", index=False)
for sym, g in df.groupby("sym"):
    bad = g[~g.temiz]
    print(f"{sym}: {g.temiz.sum()}/{len(g)} ay temiz; kirli aylar: " + ", ".join(f"{r.ay}({r.tepe},{r.kayma_dk:+.0f})" for r in bad.itertuples()))
