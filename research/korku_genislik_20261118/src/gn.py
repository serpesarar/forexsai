"""gn.py — NDX K1 gecesinde korku genişliği dozu (PROTOCOL). python gn.py"""
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
RES = ROOT / "research/korku_genislik_20261118/results"
NY = "America/New_York"


def nts(b: pd.DataFrame, step: int) -> pd.DataFrame:
    dp = G.day_prices(b, NY, [900, 960], step)
    x = G._local(b, NY)
    tw = x[(x.mn >= 570) & (x.mn < 960)].groupby("day").c.mean()
    days = [z for z in dp.index if z.weekday() < 5 and G.nyse_ok(z) and np.isfinite(dp.loc[z, "o960"])]
    rows = []
    for i in range(len(days) - 1):
        a, c = days[i], days[i + 1]
        pc, p60, s = dp.loc[a, "o960"], dp.loc[a, "o900"], dp.loc[a, "s960"]
        pin = pc + s
        rows.append({"d": a, "net": (dp.loc[c, "o960"] / pin - 1) * 1e4 - kk.FIN * (c - a).days,
                     "K1": bool((pc / tw.get(a, np.nan) - 1) <= -0.005 and pc < p60)})
    n = pd.DataFrame(rows)
    n["era"] = np.where(n.d <= kk.ESKI_END, "ESKI", "YENI")
    return n


def st(v: pd.Series) -> dict:
    return {"n": int(len(v)), "ort": round(float(v.mean()), 1) if len(v) else None, "sd": round(float(v.std()), 1) if len(v) > 1 else None,
            "en_kotu": round(float(v.min()), 1) if len(v) else None}


def main() -> None:
    RES.mkdir(exist_ok=True)
    br = {}
    for sym in ("US30", "US2000"):
        n = nts(KD.mt5_m30(sym), 1800)
        br[sym] = n.set_index("d").K1
    out = {}
    for feed, (b, step) in {"DUKA": (G.ndx_bars(), 60), "MT5_NAS100": (KD.mt5_m30("NAS100"), 1800)}.items():
        n = nts(b, step)
        n = n[n.K1].copy()
        n = n[n.d.isin(br["US30"].index) & n.d.isin(br["US2000"].index)]
        n["g"] = br["US30"].reindex(n.d).values.astype(int) + br["US2000"].reindex(n.d).values.astype(int)
        rec = {}
        for e in ("ESKI", "YENI", None):
            x = n[n.era == e] if e else n
            rec[e or "TUM"] = {f"g{g}": st(x[x.g == g].net) for g in (0, 1, 2)}
        a, z = n[n.g == 2], n[n.g == 0]
        rec["P_g2_gt_g0"] = round(G.KS.diff_p(a.net.values, a.d.astype(str).values, z.net.values, z.d.astype(str).values), 4)
        rec["yil_g2_eksi_g0"] = {int(y): round(float(n[(n.g == 2) & (pd.to_datetime(n.d).dt.year == y)].net.mean()
                                                       - n[(n.g == 0) & (pd.to_datetime(n.d).dt.year == y)].net.mean()), 1)
                                 for y in sorted(pd.to_datetime(n.d).dt.year.unique())}
        out[feed] = rec
        print(feed, json.dumps(rec, ensure_ascii=False))
    D, M = out["DUKA"], out["MT5_NAS100"]
    up = all(D[e]["g2"]["ort"] > D[e]["g0"]["ort"] for e in ("ESKI", "YENI"))
    dn = all(D[e]["g2"]["ort"] < D[e]["g0"]["ort"] for e in ("ESKI", "YENI"))
    md = M["TUM"]["g2"]["ort"] - M["TUM"]["g0"]["ort"]
    if up:
        hk = "B" if D["P_g2_gt_g0"] >= 0.95 and md > 0 else "C+ (geniş korku daha iyi)"
    elif dn:
        hk = "C+ (dar korku daha iyi)" if 1 - D["P_g2_gt_g0"] >= 0.95 and md < 0 else "C (dar korku eğilimi)"
    else:
        hk = "X"
    out["hukum"] = hk
    print("hüküm:", hk)
    (RES / "genislik.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
