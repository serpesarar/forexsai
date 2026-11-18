"""af.py — altın LBMA fiks dönüşü (PROTOCOL). python af.py"""
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
RES = ROOT / "research/altin_fiks_20261118/results"
LON = "Europe/London"
FIX = {"AM": (10, 30), "PM": (15, 0)}
ES, HS = (0.0015, 0.0030), (30, 60)
P_B = 1 - 0.05 / 8


def events(b: pd.DataFrame, tol: int) -> pd.DataFrame:
    t, o = b.t.values, b.o.values
    sp = b.sp.values
    x = G._local(b, LON)
    days = sorted(set(x.day))
    rows = []

    def at(u: int):
        i = int(np.searchsorted(t, u))
        return (o[i], sp[i]) if i < len(t) and t[i] - u <= tol else (np.nan, np.nan)

    for d in days:
        if d.weekday() >= 5:
            continue
        for f, (hh, mm) in FIX.items():
            u = int(pd.Timestamp(datetime(d.year, d.month, d.day, hh, mm), tz=LON).timestamp())
            pf, sf = at(u)
            p0, _ = at(u - 1800)
            if not (np.isfinite(pf) and np.isfinite(p0)):
                continue
            r = pf / p0 - 1
            rec = {"d": d, "fix": f, "r": r}
            for h in HS:
                px, sx = at(u + h * 60)
                side = -np.sign(r)
                rec[f"h{h}"] = side * (px / pf - 1) * 1e4 - 0.5 * (sf + sx) / pf * 1e4 if np.isfinite(px) else np.nan
            rows.append(rec)
    e = pd.DataFrame(rows)
    e["era"] = np.where(e.d <= kk.ESKI_END, "ESKI", "YENI")
    return e


def boot(a: np.ndarray, n: int = 10000) -> float:
    rng = np.random.default_rng(3)
    return float((rng.choice(a, (n, len(a))).mean(1) > 0).mean())


def main() -> None:
    RES.mkdir(exist_ok=True)
    xd, _ = kk.load("XAU", ROOT / "research/fibo_altin_bolge_20261116/cache")
    xm = KD.mt5_m30("XAUUSD")
    xm["sp"] = xm.sp / 10
    E, M = events(xd, 300), events(xm, 0)
    out = {}
    for f in FIX:
        for e in ES:
            for h in HS:
                x = E[(E.fix == f)].dropna(subset=[f"h{h}"])
                m = (x.r.abs() >= e).values
                v = x[f"h{h}"].values
                rec = {er: {"n": int((m & (x.era == er).values).sum()), "ort": round(float(v[m & (x.era == er).values].mean()), 1),
                            "taban": round(float(v[~m & (x.era == er).values].mean()), 1)} for er in ("ESKI", "YENI")}
                rec["P"] = round(boot(v[m]), 4)
                rec["korku_AL"] = round(float(v[m & (x.r < 0).values].mean()), 1)
                rec["cosku_SAT"] = round(float(v[m & (x.r > 0).values].mean()), 1)
                if h == 60:
                    y = M[(M.fix == f)].dropna(subset=["h60"])
                    rec["MT5"] = round(float(y.h60[(y.r.abs() >= e).values].mean()), 1)
                ok1 = all(rec[er]["ort"] > 0 for er in ("ESKI", "YENI"))
                ok3 = rec.get("MT5", 1) > 0
                rec["hukum"] = "B" if ok1 and rec["P"] >= P_B and ok3 else ("C+" if ok1 and ok3 else ("C" if ok1 else "X"))
                out[f"{f}_e{e}_h{h}"] = rec
                print(f, e, h, rec, flush=True)
    (RES / "altin_fiks.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
