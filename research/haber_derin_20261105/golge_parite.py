"""Gölge modülünün saf çekirdeği, kart işlemleriyle birebir mi? Dukascopy 5m 2024-26 tüm günler, spread 1,3."""
import sys
from pathlib import Path
import pandas as pd
H = Path(__file__).parent; sys.path.insert(0, str(H.parents[1] / "yeni deneme"))
import caprev_shadow as cs, orb_vix_shadow as ov
d = pd.read_parquet(H / "data/NDX_1m.parquet"); d = d.assign(ts=pd.to_datetime(d.t, unit="s", utc=True)).set_index("ts")
m = d.resample("5min", label="left", closed="left").agg(open=("open", "first"), high=("high", "max"), low=("low", "min"), close=("close", "last")).dropna().reset_index()
m["t"] = m.ts.astype("int64") // 10**9
byday = {}
for r in m[["t", "open", "high", "low", "close"]].to_dict("records"):
    dd, mm, _ = cs.to_local(r["t"], "US")
    if 570 <= mm < 955: byday.setdefault(dd, []).append({**r, "t": int(r["t"])})
rows = []
for dd, bars in sorted(byday.items()):
    tr = ov.find_trigger(ov.session_bars(bars, dd))
    if not tr or tr["entry_open"] is None: continue
    ev = {"id": str(dd), "day": str(dd), "arm": "?", "stop": tr["stop"], "entry_model": None, "fill": None, "detect_t": tr["trig_t"] + 300, "spread": 1.3, "status": "open"}
    o = ov.resolve_event(ev, bars, [], cs.local_to_utc(dd, 1000, "US"))
    if o.get("R_model") is not None: rows.append({"d": pd.Timestamp(dd), "R_g": o["R_model"]})
g = pd.DataFrame(rows)
c = pd.read_csv(H / "results_c1_islemler_5m.csv", parse_dates=["d"])
c["d"] = c.d.dt.tz_localize(None).dt.normalize()
j = c.merge(g, on="d", how="left")
print("kart C1", len(c), "gölgede eşleşen", int(j.R_g.notna().sum()), "|fark|>0,005:", int(((j.R - j.R_g).abs() > 0.005).sum()), "ort kart", round(j.R.mean(), 4), "ort gölge", round(j.R_g.mean(), 4))
print(j[(j.R - j.R_g).abs() > 0.005].head(8).to_string())
