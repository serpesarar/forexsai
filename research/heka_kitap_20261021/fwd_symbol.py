"""Sembol bazında öne çıkan hücrelerin ileri dönem kontrolü (SONRADAN; broker 15m → 30m/1h)."""
import pandas as pd

from common import OUT, SPREAD, day_boot, run_with_placebo, simulate
from fwd_test import END, fwd_bars, prep
from hk4_divergence import events

df = pd.read_csv(OUT / "ozet_sembol.csv")
print("Holm geçen:", df[df.holm].loc[:, ["hyp", "sym", "cell", "n", "ortR", "fark", "P", "fark_dev", "fark_test", "ortR_ex5"]]
      .round(3).to_string(index=False))

cases = [("XAU", "1h", 1, "V2", "X2"), ("XAU", "1h", 1, "V2", "X3"), ("XAU", "30m", -1, "V1", "X2")]
for sym, tf, dr, var, x in cases:
    d = prep(fwd_bars(sym, tf), tf)
    ev = events(d)
    if var == "V2":
        ev = ev[ev.extreme_prev]
    sig = ev[(ev.kind == "div") & (ev.dir == dr)][["i", "dir"]]
    a, sp = d.atr.values, SPREAD[sym]
    mk = (lambda i, di, ref: simulate(d, i, di, 1.5 * a[i], 3 * a[i], 60, sp)) if x == "X2" else \
         (lambda i, di, ref: simulate(d, i, di, 3 * a[i], None, 20, sp))
    t = run_with_placebo(d, sig, sym, mk)
    t = t[t.ts > pd.Timestamp(END[sym], tz="UTC")].dropna(subset=["d"]) if len(t) else t
    print(sym, tf, "BOĞA" if dr > 0 else "AYI", var, x, "ileri n", len(t),
          "" if not len(t) else f"ortR {t.r.mean():.3f} fark {t.d.mean():.3f} P {day_boot(t):.2f}")
f = pd.read_csv(OUT / "fwd_hk1_trades.csv")
g = f[(f.sym == "XAU") & (f.tf == "30m") & (f.dir == 1)]
print("XAU 30m BUY X1 ileri n", len(g), f"ortR {g.r.mean():.3f} fark {g.d.mean():.3f}")
