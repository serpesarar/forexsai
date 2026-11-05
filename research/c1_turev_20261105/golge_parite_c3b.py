"""c3b_shadow çekirdeği, kart işlemleriyle birebir mi? Broker M30 2018-05→."""
import sys
from pathlib import Path
import pandas as pd
H = Path(__file__).parent; sys.path.insert(0, str(H.parents[1] / "yeni deneme"))
import c3b_shadow as c3
x = pd.read_csv(H / "data/mt5/NAS100_M30.csv.gz")
et = pd.to_datetime(x.t, unit="s") - pd.Timedelta(hours=7); x = x[et >= "2018-05-15"]; et = et[et >= "2018-05-15"]
u = et.dt.tz_localize("America/New_York", ambiguous="NaT", nonexistent="NaT").dt.tz_convert("UTC"); x = x[u.notna()]; u = u.dropna()
bars = [{"t": int(t), "open": o, "high": h, "low": l, "close": c} for t, o, h, l, c in zip(u.astype("int64") // 10**9, x.o, x.h, x.l, x.c)]
tr = c3.replay(c3.daily_series(bars)); g = pd.DataFrame(tr); g["d"] = pd.to_datetime(g.entry_d)
k = pd.read_csv(H / "results/c3b_islemler.csv", names=["d", "bp"], header=0, parse_dates=["d"])
j = k.merge(g, on="d", how="outer", indicator=True)
print("kart", len(k), "gölge", len(g), "eşleşen", int((j._merge == "both").sum()), "yalnız kart", int((j._merge == "left_only").sum()), "yalnız gölge", int((j._merge == "right_only").sum()))
b = j[j._merge == "both"]; print("|fark|>0,5 bp:", int(((b.bp - b.bp_model).abs() > .5).sum()), "ort kart", round(k.bp.mean(), 2), "ort gölge", round(g.bp_model.mean(), 2))
print(j[j._merge != "both"][["d", "bp", "bp_model", "_merge"]].head(12).to_string()); print(b[(b.bp - b.bp_model).abs() > .5][["d", "bp", "bp_model", "exit_d"]].head(8).to_string())
