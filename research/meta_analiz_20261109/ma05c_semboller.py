"""MA-05 C: tüm sembollerde aile başına risk payı (betimsel, salt-okuma). Ön kayıt: PROTOCOL.md EK-2."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(ROOT))
from scripts.islem_otopsi import data  # noqa: E402
OUT = Path(__file__).resolve().parent / "results"
tr = data.load_trades(data.get_client(), pd.Timestamp("2026-06-29", tz="UTC"))
tr = tr[(tr.sl0 > 0) & (tr.volume > 0)].copy(); tr["sgn"] = np.where(tr.direction == "BUY", 1, -1)
mv = (tr.close_price - tr.open_price) * tr.sgn * tr.volume
k = (tr.net - tr.swap.fillna(0))[mv.abs() > 0] / mv[mv.abs() > 0]; tr["k"] = k
K = tr[(mv.abs() / tr.volume) > (tr.open_price * 0.0005)].groupby("symbol").k.median(); print("$/fiyat birimi/lot:", K.round(3).to_dict())
tr["risk"] = (tr.open_price - tr.sl0).abs() * tr.volume * tr.symbol.map(K); tr["gun"] = tr.open_raw.dt.date
tr["dk"] = tr.open_raw.dt.floor("min")
d = tr.groupby(["symbol", "family", "direction", "dk"]).agg(lot=("volume", "sum"), risk=("risk", "sum"), net=("net", "sum")).reset_index(); d["R"] = d.net / d.risk
g = d.groupby(["symbol", "family", "direction"])
tab = pd.DataFrame({"karar": g.size(), "ort_lot": g.lot.mean().round(2), "top_risk": g.risk.sum().round(0), "net": g.net.sum().round(0), "ortR": g.R.mean().round(3), "isabet": g.R.apply(lambda x: (x > 0).mean()).round(2)})
tab["risk_payi_%"] = (100 * tab.top_risk / tab.top_risk.sum()).round(1); tab = tab[tab.karar >= 5].sort_values("top_risk", ascending=False)
print(tab.to_string()); tab.to_csv(OUT / "ma05c_semboller.csv")
for s, x in tr.groupby("symbol"):
    day = x.groupby("gun").net.sum(); print(f"{s}: işlem {len(x)} gün {len(day)} net {day.sum():.0f} en kötü 5 gün {day.nsmallest(5).sum():.0f} en iyi gün {day.max():.0f} ilk {x.open_raw.min().date()} son {x.open_raw.max().date()}")
day = tr.groupby("gun").net.sum(); print(f"TÜMÜ: işlem {len(tr)} gün {len(day)} net {day.sum():.0f} en kötü 5 gün {day.nsmallest(5).sum():.0f} en iyi 5 gün {day.nlargest(5).sum():.0f} günlük SR {day.mean()/day.std():.3f}")
