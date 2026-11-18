"""ar.py — art arda korku gecesi (PROTOCOL). python ar.py"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
for p in ("research/korku_kuresel_20261118/src", "research/fitil_kesisim_20261118/src"):
    sys.path.insert(0, str(ROOT / p))
import kk  # noqa: E402
import ksg_dogrulama as KD  # noqa: E402

G = kk.G
RES = ROOT / "research/korku_ardisik_20261118/results"
NY = "America/New_York"


def nts(b: pd.DataFrame, step: int) -> pd.DataFrame:
    dp = G.day_prices(b, NY, [570, 900, 960], step)
    x = G._local(b, NY)
    tw = x[(x.mn >= 570) & (x.mn < 960)].groupby("day").c.mean()
    days = [z for z in dp.index if z.weekday() < 5 and G.nyse_ok(z) and np.isfinite(dp.loc[z, "o960"])]
    rows = []
    for i in range(len(days) - 1):
        a, c = days[i], days[i + 1]
        pc, p60, s, po = dp.loc[a, "o960"], dp.loc[a, "o900"], dp.loc[a, "s960"], dp.loc[a, "o570"]
        rows.append({"d": a, "net": (dp.loc[c, "o960"] / (pc + s) - 1) * 1e4 - kk.FIN * (c - a).days,
                     "K1": bool((pc / tw.get(a, np.nan) - 1) <= -0.005 and pc < p60), "rth": pc / po - 1})
    n = pd.DataFrame(rows)
    n["prev"] = (n.K1.shift(1).fillna(False).astype(bool) | (n.rth.shift(1) <= -0.01))
    n["era"] = np.where(n.d <= kk.ESKI_END, "ESKI", "YENI")
    return n[n.K1].reset_index(drop=True)


def st(v: pd.Series) -> dict:
    return {"n": int(len(v)), "ort": round(float(v.mean()), 1), "sd": round(float(v.std()), 1), "en_kotu": round(float(v.min()), 1)}


def main() -> None:
    RES.mkdir(exist_ok=True)
    out, pool = {}, []
    feeds = {"US30": (KD.mt5_m30("US30"), 1800), "US2000": (KD.mt5_m30("US2000"), 1800), "US500": (KD.mt5_m30("US500", "2021-01-01"), 1800),
             "NDX_DUKA_betimleme": (G.ndx_bars(), 60), "NAS100_MT5_betimleme": (KD.mt5_m30("NAS100"), 1800)}
    for nm, (b, step) in feeds.items():
        n = nts(b, step)
        a, z = n[n.prev], n[~n.prev]
        rec = {"ardisik": st(a.net), "degil": st(z.net),
               "P": round(G.KS.diff_p(a.net.values, a.d.astype(str).values, z.net.values, z.d.astype(str).values), 4),
               "donem": {e: {"ardisik": st(n[n.prev & (n.era == e)].net), "degil": st(n[~n.prev & (n.era == e)].net)} for e in ("ESKI", "YENI")}}
        rec["gecti"] = bool(rec["ardisik"]["ort"] > rec["degil"]["ort"] and rec["ardisik"]["ort"] > 0)
        out[nm] = rec
        if "betimleme" not in nm:
            pool.append(n.assign(sym=nm))
        print(nm, json.dumps(rec, ensure_ascii=False), flush=True)
    p = pd.concat(pool)
    a, z = p[p.prev], p[~p.prev]
    P = G.KS.diff_p(a.net.values, a.d.astype(str).values, z.net.values, z.d.astype(str).values)
    k = sum(out[s]["gecti"] for s in ("US30", "US2000", "US500"))
    hk = "B" if k == 3 and P >= 0.95 else ("C+" if k >= 2 and P >= 0.90 else "X")
    out["ozet"] = {"kor_gecen": int(k), "havuz_ardisik": round(float(a.net.mean()), 1), "havuz_degil": round(float(z.net.mean()), 1),
                   "havuz_P": round(float(P), 4), "hukum": hk}
    print(out["ozet"])
    (RES / "ardisik.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
