"""MA-03: botun NDX işlemlerinde aile başına risk bütçesi ve sonuç (betimsel). Ön kayıt: PROTOCOL.md."""
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / "results"; OUT.mkdir(exist_ok=True)
t = pd.read_parquet(ROOT / "tp_sonrasi_ters_20261109/data/ndx_trades.parquet")
t["risk"] = (t.open_price - t.sl0).abs() * t.volume          # NAS100: 1 lot = 1 $/puan
t = t[(t.sl0 > 0) & (t.risk > 0)]
t["gun"] = t.entry_utc.dt.date
d = t.groupby(["family", "direction", "decision"]).agg(lot=("volume", "sum"), risk=("risk", "sum"), net=("net", "sum"), gun=("gun", "first"), t0=("entry_utc", "first")).reset_index()
d["R"] = d.net / d.risk
def boot(x, n=4000, rng=np.random.default_rng(5)):
    x = np.asarray(x); return float((rng.choice(x, (n, len(x))).mean(1) > 0).mean()) if len(x) > 4 else np.nan
g = d.groupby(["family", "direction"])
tab = pd.DataFrame({"karar": g.size(), "ort_lot": g.lot.mean().round(1), "ort_risk_$": g.risk.mean().round(0), "top_risk_$": g.risk.sum().round(0),
                    "net_$": g.net.sum().round(0), "ort_R": g.R.mean().round(3), "isabet": g.R.apply(lambda x: (x > 0).mean()).round(3),
                    "P_R>0": g.R.apply(boot).round(3), "ilk": g.t0.min().dt.date, "son": g.t0.max().dt.date})
tab["risk_payi_%"] = (100 * tab["top_risk_$"] / tab["top_risk_$"].sum()).round(1)
print(tab.sort_values("top_risk_$", ascending=False).to_string()); tab.to_csv(OUT / "ma03_aile.csv")
print("\nTOPLAM karar", len(d), "net $", round(d.net.sum()), "ort R", round(d.R.mean(), 3), "toplam risk $", round(d.risk.sum()))
day = t.groupby("gun").net.sum(); print("gün", len(day), "en kötü 5 gün:", day.nsmallest(5).round(0).to_dict()); print("en iyi 5 gün:", day.nlargest(5).round(0).to_dict())
print("en kötü 5 gün toplamı", round(day.nsmallest(5).sum()), "| tüm net", round(day.sum()))
m = t.assign(ay=t.entry_utc.dt.to_period("M").astype(str)).groupby(["ay", "family"]).net.sum().unstack().round(0); print(m.to_string()); m.to_csv(OUT / "ma03_ay.csv")
lot = t.assign(ay=t.entry_utc.dt.to_period("M").astype(str)).groupby(["ay", "family"]).volume.median().unstack(); print(lot.to_string())
