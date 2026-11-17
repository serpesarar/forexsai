"""run_ek3b.py — EK-3b: donmuş DAX1 + DAX Avrupa ailesi (15m UZUN AVRUPA, eng/engf) CAC 40 ve Euro Stoxx 50'de."""
from __future__ import annotations

import itertools
import json

import numpy as np
import pandas as pd

import fblib as F
from run_ek1 import diff_p
from run_ek3 import market_eval
from run_grid import placebo_map, placebo_trades

DAX1 = {"tf": "15m", "side": 1, "pattern": "eng", "zone": "altin", "sl": "inv", "tp": "x1272", "hold": 300, "smin": 3.0,
        "spmin": 0.0, "filt": "ses:AVRUPA"}
OUT = F.HERE / "results" / "ek3b"


def family(p: F.Path1) -> pd.DataFrame:
    bars = F.build_bars(p, 15, 0, "15m")
    cand = F.detect(bars, 1)
    sigs = {(pt, z): F.signals(cand, pt, z, 3.0, 0.0) for pt in ["eng", "engf"] for z in ["altin", "sig382", "derin"]}
    pmap = placebo_map(np.concatenate([s.t.values for s in sigs.values()]), bars, p, seed=12)
    rows = []
    for (pt, z), sig in sigs.items():
        for sl, tp, hold in itertools.product(["L", "inv", "pat"], ["H", "x1272", "x1618", "2R"], [100, 300]):
            tr = F.resolve(F.setup_trades(sig, bars, p, sl, tp, hold, z), p)
            if tr.empty:
                continue
            pl = placebo_trades(tr, pmap, bars, p, hold)
            eu = tr.session.values == "AVRUPA"
            for smin, spmin in itertools.product([3.0, 4.0, 6.0], [0.0, 0.5, 1.0]):
                m = eu & (tr.S.values >= smin) & (tr.speed.values >= spmin)
                mp = m & ~np.isnan(pl.R.values)
                if m.sum() < 20:
                    continue
                rows.append({"pattern": pt, "zone": z, "sl": sl, "tp": tp, "hold": hold, "smin": smin, "spmin": spmin,
                             "n": int(m.sum()), "R": float(tr.R.values[m].mean()), "pR": float(pl.R.values[mp].mean())})
    return pd.DataFrame(rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    res, pooled, pooled_pl = {}, [], []
    for sym in ["CAC", "STOXX"]:
        p = F.load_duka(sym)
        bars = F.build_bars(p, 15, 0, "15m")
        ev, tr = market_eval(DAX1, bars, p)
        pl = F.placebo(tr, bars, p, 300, draws=5)
        pl = pl[pl.session == "AVRUPA"] if len(pl) else pl
        fam = family(p)
        fam.round(4).to_csv(OUT / f"aile_{sym.lower()}.csv", index=False)
        res[sym] = {"DAX1": ev, "aile": {"hucre": len(fam), "plasebodan_iyi_oran": float((fam.R > fam.pR).mean()),
                                         "arti_oran": float((fam.R > 0).mean()), "ort_R": float(fam.R.mean()),
                                         "ort_pR": float(fam.pR.mean())}}
        pooled.append(tr.assign(date=sym + "|" + tr.date.astype(str)))
        pooled_pl.append(pl.assign(date=sym + "|" + pl.date.astype(str)))
        print(sym, "DAX1", ev, "\n  aile", res[sym]["aile"], flush=True)
    a, b = pd.concat(pooled), pd.concat(pooled_pl)
    res["havuz"] = {**F.summarize(a, boot=True), "plasebo": F.summarize(b).get("ortR"), "fark_P": diff_p(a, b)}
    print("havuz", res["havuz"], flush=True)
    (OUT / "ek3b.json").write_text(json.dumps(res, indent=1, default=lambda o: None if o != o else str(o)))


if __name__ == "__main__":
    main()
