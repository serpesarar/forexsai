"""R0B_G1 tek-pozisyon işlemleri (mekanik/ kodunu SALT-OKUNUR yeniden kullanır) + gün listeleri.
Gün = işlemin GİRİŞ barının UTC takvim günü. Çıktı: out/trades.csv, out/days.csv, out/best20/best50/worst20."""
import os, sys
import numpy as np, pandas as pd
MK = "/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/mekanik"
sys.path.insert(0, MK)
sys.dont_write_bytecode = True
from run_main import load_main, sim_cell
from rules import events, GEOM
from mech import one_position
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
d = load_main(); ev = events(d, "R0", +1); tp, sl, hold = GEOM["R0"][0]
R, xi, code, hl = sim_cell(d, ev, tp, sl, hold, +1, 0.12); m = np.isfinite(R)
k = one_position(ev.ent.to_numpy()[m], xi[m])
e = ev[m][k].copy(); e["R"] = R[m][k]; e["xi"] = xi[m][k]; e["code"] = code[m][k]
ts = d.ts.to_numpy()
e["sig_ts"] = d.ts.values[e.sig]; e["ent_ts"] = d.ts.values[e.ent]; e["exit_ts"] = d.ts.values[e.xi]
e["ent_day"] = pd.to_datetime(e.ent_ts).dt.strftime("%Y-%m-%d")
e["entry_px"] = d.o.values[e.ent] + 0.12
e["ent_utc_h"] = pd.to_datetime(e.ent_ts).dt.hour
e.to_csv(os.path.join(OUT, "trades.csv"), index=False)
print("n", len(e), "toplamR", round(e.R.sum(), 1))
g = e.groupby("ent_day").agg(R=("R", "sum"), n=("R", "size"), maxR=("R", "max"),
                             first_ent=("ent_ts", "min"), px=("entry_px", "first")).sort_values("R", ascending=False)
g["rank"] = np.arange(1, len(g) + 1)
g.to_csv(os.path.join(OUT, "days.csv"))
tot = e.R.sum()
for nm, sub in [("best20", g.head(20)), ("best50", g.head(50)), ("worst20", g.tail(20).iloc[::-1])]:
    sub.to_csv(os.path.join(OUT, f"{nm}.csv"))
print("işlem günü", len(g), "en iyi 20 pay", round(g.head(20).R.sum() / tot, 3), "en iyi 50 pay", round(g.head(50).R.sum() / tot, 3))
print(g.head(50).to_string())
print(g.tail(20).to_string())
