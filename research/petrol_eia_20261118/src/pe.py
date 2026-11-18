"""pe.py — petrol EIA tepkisi devam/dönüş (PROTOCOL). python pe.py"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
for p in ("research/korku_kuresel_20261118/src", "research/fitil_kesisim_20261118/src"):
    sys.path.insert(0, str(ROOT / p))
import kk  # noqa: E402
import ksg_dogrulama as KD  # noqa: E402

G = kk.G
RES = ROOT / "research/petrol_eia_20261118/results"
NY = "America/New_York"
ES = (0.005, 0.010)
P_B = 1 - 0.05 / 4


def u(d, hh, mm) -> int:
    return int(pd.Timestamp(datetime(d.year, d.month, d.day, hh, mm), tz=NY).timestamp())


def main() -> None:
    RES.mkdir(exist_ok=True)
    b = KD.mt5_m30("SpotCrude")
    b["sp"] = b.sp / 100
    t, o, sp = b.t.values, b.o.values, b.sp.values
    x = G._local(b, NY)
    days = sorted(z for z in set(x.day) if z.weekday() < 5)

    def at(v: int):
        i = int(np.searchsorted(t, v))
        return (o[i], sp[i]) if i < len(t) and t[i] == v else (np.nan, np.nan)

    rows = []
    for i, d in enumerate(days[:-1]):
        mon = d - pd.Timedelta(days=d.weekday())
        hol = not G.nyse_ok(mon)
        if d.weekday() == 2 and not hol:
            kind, hh, mm = "EIA", 10, 30
        elif d.weekday() == 3 and hol:
            kind, hh, mm = "EIA", 11, 0
        elif d.weekday() in (0, 1, 4):
            kind, hh, mm = "KONTROL", 10, 30
        else:
            continue
        pe, _ = at(u(d, hh, mm))
        p1, s1 = at(u(d, hh, mm) + 1800)
        x1, sx1 = at(u(d, 14, 30))
        nd = days[i + 1]
        x2, sx2 = at(u(nd, 14, 30))
        if not (np.isfinite(pe) and np.isfinite(p1)):
            continue
        r = p1 / pe - 1
        sg = np.sign(r)
        rec = {"d": d, "tur": kind, "R": r}
        for nm, px, sx in (("s1430", x1, sx1), ("n1430", x2, sx2)):
            fin = kk.FIN * (nd - d).days if nm == "n1430" else 0.0
            rec[nm] = sg * (px / p1 - 1) * 1e4 - 0.5 * (s1 + sx) / p1 * 1e4 - fin if np.isfinite(px) else np.nan
        rows.append(rec)
    df = pd.DataFrame(rows)
    df["era"] = np.where(df.d <= kk.ESKI_END, "ESKI", "YENI")
    out = {}
    rng = np.random.default_rng(5)
    for e in ES:
        for ex in ("s1430", "n1430"):
            z = df.dropna(subset=[ex])
            ev = z[(z.tur == "EIA") & (z.R.abs() >= e)]
            ko = z[(z.tur == "KONTROL") & (z.R.abs() >= e)]
            rec = {er: {"n": int((ev.era == er).sum()), "devam": round(float(ev[ev.era == er][ex].mean()), 1),
                        "kontrol": round(float(ko[ko.era == er][ex].mean()), 1)} for er in ("ESKI", "YENI")}
            v = ev[ex].values
            p = float((rng.choice(v, (10000, len(v))).mean(1) > 0).mean())
            rec["P_devam"] = round(p, 4)
            rec["TUM"] = {"n": int(len(v)), "devam": round(float(v.mean()), 1), "kontrol": round(float(ko[ex].mean()), 1)}
            sg = np.sign(rec["TUM"]["devam"])
            same = all(np.sign(rec[er]["devam"]) == sg for er in ("ESKI", "YENI"))
            pp = p if sg > 0 else 1 - p
            ctl = np.sign(rec["TUM"]["devam"] - rec["TUM"]["kontrol"]) == sg
            yon = "devam" if sg > 0 else "dönüş"
            rec["hukum"] = ("C+ " if same and pp >= P_B and ctl else ("C " if same else "X ")) + yon
            out[f"e{e}_{ex}"] = rec
            print(e, ex, rec, flush=True)
    (RES / "petrol_eia.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
