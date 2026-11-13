"""FX-01 EK-3 H5: benzer ekonomili çapraz çiftte ortalamaya dönüş. Çalıştır: ../../.venv/bin/python -I h5.py"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fx_core as f  # noqa: E402
import hyp  # noqa: E402
from h4 import daily, swap_cost  # noqa: E402

SEEN = ["AUDCAD", "EURGBP", "GBPCHF", "EURAUD"]
BLIND = ["AUDNZD", "EURCHF", "NZDCAD", "CADCHF", "AUDCHF"]
Z, N_SMA, MAX_DAYS, N_PLACEBO = 2.0, 20, 10, 300
START, END = "2010-10-12", "2026-11-02"


def prep(pair: str) -> pd.DataFrame:
    d = daily(pair)
    d["sma"] = d.c.rolling(N_SMA).mean()
    d["z"] = (d.c - d.sma) / d.c.rolling(N_SMA).std()
    return d


def run(pair: str, d: pd.DataFrame, sig: list[tuple[pd.Timestamp, int]], hold: list[int] | None = None) -> list[dict]:
    out, busy = [], pd.Timestamp.min
    days = d.index
    for k, (s, side) in enumerate(sig):
        if s <= busy:
            continue
        i = days.get_loc(s)
        if hold is None:
            e = None
            for j in range(i + 1, min(i + 1 + MAX_DAYS, len(days))):
                e = days[j]
                if (side > 0 and d.c.iloc[j] >= d.sma.iloc[j]) or (side < 0 and d.c.iloc[j] <= d.sma.iloc[j]):
                    break
        else:
            j = min(i + hold[k % len(hold)], len(days) - 1)
            e = days[j]
        if e is None or e <= s:
            continue
        r = hyp.trade(pair, hyp.ny(s, 18), hyp.ny(e, 18), side)
        if r is None:
            continue
        nights = list(days[i:days.get_loc(e)])
        sc = swap_cost(pair, side, nights, d.c.iloc[i])
        r.update(net=r["net"] - sc, net15=r["net15"] - sc, gun=len(nights), swap=sc)
        out.append(r)
        busy = e
    return out


def main() -> list[dict]:
    res = []
    for pair in SEEN + BLIND:
        if not (f.FX / f"{pair}_D1.csv.gz").exists() or not (f.FX / f"{pair}_H1.csv.gz").exists():
            res.append({"hucre": f"H5 {pair}", "n": 0, "not": "veri yok"})
            continue
        d = prep(pair)
        w = d[(d.index >= START) & (d.index < END)]
        sig = [(s, +1) for s in w[w.z <= -Z].index] + [(s, -1) for s in w[w.z >= Z].index]
        sig.sort()
        rows = run(pair, d, sig)
        rep = hyp.report(rows, f"H5 {pair} {'gorulen' if pair in SEEN else 'KOR'}")
        if rows:
            holds = [r["gun"] for r in rows]
            sides = [1 if r["gross"] == r["gross"] else 1 for r in rows]
            rng = np.random.default_rng(9)
            pool = w.index
            pl = []
            side_mix = [s for _, s in sig]
            for _ in range(N_PLACEBO):
                picks = sorted(pd.DatetimeIndex(rng.choice(pool, len(rows), replace=False)))
                ps = [(p, int(rng.choice(side_mix))) for p in picks]
                pr = run(pair, d, ps, holds)
                pl.append(np.mean([x["net"] for x in pr]) if pr else np.nan)
            pl = np.array(pl)
            rep.update(plasebo_ort=round(float(np.nanmean(pl)), 2), plasebo_yuzdelik=round(float((pl < rep["ort"]).mean()), 3),
                       ort_gun=round(float(np.mean(holds)), 2), ort_swap=round(float(np.mean([r["swap"] for r in rows])), 2))
            _ = sides
        res.append(rep)
        print(json.dumps(rep, ensure_ascii=False, default=str), flush=True)
    (f.RES / "h5.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str))
    return res


if __name__ == "__main__":
    main()
