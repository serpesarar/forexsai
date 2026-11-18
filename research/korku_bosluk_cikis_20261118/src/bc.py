"""bc.py — K1 gecesinde boşluğa bağlı 09:30 çıkışı (PROTOCOL). python bc.py"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
for p in ("research/korku_kuresel_20261118/src", "research/fitil_gece_20261118/src"):
    sys.path.insert(0, str(ROOT / p))
import kk  # noqa: E402
import gece_run as GR  # noqa: E402

G = kk.G
RES = ROOT / "research/korku_bosluk_cikis_20261118/results"
NY = "America/New_York"


def table(b: pd.DataFrame, step: int) -> pd.DataFrame:
    dp = G.day_prices(b, NY, [570, 900, 960], step)
    x = G._local(b, NY)
    tw = x[(x.mn >= 570) & (x.mn < 960)].groupby("day").c.mean()
    days = [z for z in dp.index if z.weekday() < 5 and G.nyse_ok(z) and np.isfinite(dp.loc[z, "o960"])]
    rows = []
    for i in range(len(days) - 1):
        a, c = days[i], days[i + 1]
        pc, p60, s = dp.loc[a, "o960"], dp.loc[a, "o900"], dp.loc[a, "s960"]
        if not ((pc / tw.get(a, np.nan) - 1) <= -0.005 and pc < p60):
            continue
        o9, s9 = dp.loc[c, "o570"], dp.loc[c, "s570"]
        if not np.isfinite(o9):
            continue
        pin = pc + s
        fin = kk.FIN * (c - a).days
        rows.append({"d": a, "gap": o9 / pc - 1, "x930": (o9 / pin - 1) * 1e4 - fin, "x16": (dp.loc[c, "o960"] / pin - 1) * 1e4 - fin,
                     "gun": (dp.loc[c, "o960"] / o9 - 1) * 1e4})
    t = pd.DataFrame(rows)
    t["era"] = np.where(t.d <= kk.ESKI_END, "ESKI", "YENI")
    return t


def st(v: pd.Series) -> dict:
    return {"n": int(len(v)), "ort": round(float(v.mean()), 1), "sh": round(float(v.mean() / v.std()), 3)}


def main() -> None:
    RES.mkdir(exist_ok=True)
    F = {"NDX_DUKA": (G.ndx_bars(), 60)}
    F.update({k: v for k, v in GR.feeds().items()})
    T = {nm: table(b, s) for nm, (b, s) in F.items()}
    out = {}
    for g in (0.005, 0.010):
        rec = {}
        for nm, t in T.items():
            gx = np.where(t.gap >= g, t.x930, t.x16)
            t = t.assign(gx=gx)
            rec[nm] = {e or "TUM": {"X1": st((t[t.era == e] if e else t).x16), "GX": st((t[t.era == e] if e else t).gx)} for e in ("ESKI", "YENI", None)}
            rec[nm]["bosluk_kova_gun_ici"] = {"yukari": st(t[t.gap >= g].gun), "diger": st(t[t.gap < g].gun)}
        D = rec["NDX_DUKA"]
        ok1 = all(D[e]["GX"]["ort"] > D[e]["X1"]["ort"] and D[e]["GX"]["sh"] > D[e]["X1"]["sh"] for e in ("ESKI", "YENI"))
        ok2 = sum(rec[nm]["TUM"]["GX"]["ort"] > rec[nm]["TUM"]["X1"]["ort"] and rec[nm]["TUM"]["GX"]["sh"] > rec[nm]["TUM"]["X1"]["sh"]
                  for nm in T if nm != "NDX_DUKA") >= 2
        rec["hukum"] = "B" if ok1 and ok2 else ("C" if ok1 else "X")
        out[f"g{g}"] = rec
        print(f"g{g}: {rec['hukum']}")
        for nm in T:
            print(f"  {nm}: " + " | ".join(f"{e} X1 {rec[nm][e]['X1']} GX {rec[nm][e]['GX']}" for e in ("ESKI", "YENI", "TUM")) + f" | gün içi {rec[nm]['bosluk_kova_gun_ici']}")
    (RES / "bosluk_cikis.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
