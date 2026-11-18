"""ok.py — korku sonrası ölü kedi SAT (PROTOCOL). python ok.py"""
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
RES = ROOT / "research/olu_kedi_20261118/results"
NY = "America/New_York"
ES = (0.01, 0.02)


def table(b: pd.DataFrame, step: int) -> pd.DataFrame:
    dp = G.day_prices(b, NY, [900, 960], step)
    x = G._local(b, NY)
    tw = x[(x.mn >= 570) & (x.mn < 960)].groupby("day").c.mean()
    days = [z for z in dp.index if z.weekday() < 5 and G.nyse_ok(z) and np.isfinite(dp.loc[z, "o960"])]
    p, s = dp.loc[days, "o960"].values, dp.loc[days, "s960"].values
    k1 = np.array([bool((p[i] / tw.get(days[i], np.nan) - 1) <= -0.005 and p[i] < dp.loc[days[i], "o900"]) for i in range(len(days))])
    rows = []
    for i in range(1, len(days) - 1):
        r = p[i] / p[i - 1] - 1
        net = -((p[i + 1] + s[i + 1]) / p[i] - 1) * 1e4 - kk.FIN * (days[i + 1] - days[i]).days
        rows.append({"d": days[i], "R": r, "k1_dun": bool(k1[i - 1]), "net": net})
    t = pd.DataFrame(rows)
    t["era"] = np.where(t.d <= kk.ESKI_END, "ESKI", "YENI")
    return t


def st(v: pd.Series) -> dict:
    return {"n": int(len(v)), "ort": round(float(v.mean()), 1) if len(v) else None}


def main() -> None:
    RES.mkdir(exist_ok=True)
    F = {"NDX_DUKA": (G.ndx_bars(), 60), "US30": (KD.mt5_m30("US30"), 1800), "US2000": (KD.mt5_m30("US2000"), 1800)}
    out = {}
    for nm, (b, st_) in F.items():
        t = table(b, st_)
        rec = {"taban_SAT": st(t.net)}
        for e in ES:
            ok_ = t.k1_dun & (t.R >= e)
            c1 = ~t.k1_dun & (t.R >= e)
            a, z = t[ok_], t[c1]
            rec[f"e{e}"] = {"OK": st(a.net), "K1siz_ralli": st(z.net),
                            "P": round(G.KS.diff_p(a.net.values, a.d.astype(str).values, z.net.values, z.d.astype(str).values), 4) if len(a) > 2 else None,
                            "donem": {er: {"OK": st(t[ok_ & (t.era == er)].net), "K1siz": st(t[c1 & (t.era == er)].net)} for er in ("ESKI", "YENI")}}
        out[nm] = rec
        print(nm, json.dumps(rec, ensure_ascii=False), flush=True)
    hk = {}
    for e in ES:
        D = out["NDX_DUKA"][f"e{e}"]
        nd = all(D["donem"][er]["OK"]["ort"] is not None and D["donem"][er]["OK"]["ort"] > 0 and D["donem"][er]["OK"]["ort"] > D["donem"][er]["K1siz"]["ort"]
                 for er in ("ESKI", "YENI"))
        tr = sum(out[s][f"e{e}"]["OK"]["ort"] is not None and out[s][f"e{e}"]["OK"]["ort"] > 0 for s in ("US30", "US2000"))
        hk[f"e{e}"] = "B" if nd and tr == 2 and (D["P"] or 0) >= 0.975 else ("C" if nd and tr >= 1 else "X")
    out["hukum"] = hk
    print("hüküm:", hk)
    (RES / "olu_kedi.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
