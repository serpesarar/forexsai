"""eu.py — emtia uzlaşma saatinde korku → ertesi gün (PROTOCOL). python eu.py"""
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
RES = ROOT / "research/emtia_uzlasma_20261118/results"
NY = "America/New_York"
SPEC = {"XAU": (500, 810), "OIL": (540, 870)}
P_B = 1 - 0.05 / 8


def nights(d: pd.DataFrame, step: int, op: int, u: int) -> pd.DataFrame:
    dp = G.day_prices(d, NY, [u - 60, u], step)
    x = G._local(d, NY)
    tw = x[(x.mn >= op) & (x.mn < u)].groupby("day").c.mean()
    days = [z for z in dp.index if z.weekday() < 5 and np.isfinite(dp.loc[z, f"o{u}"])]
    rows = []
    for i in range(len(days) - 1):
        a, b = days[i], days[i + 1]
        if (b - a).days > 4:
            continue
        pc, p60, s = dp.loc[a, f"o{u}"], dp.loc[a, f"o{u - 60}"], dp.loc[a, f"s{u}"]
        rows.append({"d": a, "pc": pc, "p60": p60, "tw": tw.get(a, np.nan),
                     "net": (dp.loc[b, f"o{u}"] / (pc + s) - 1) * 1e4 - kk.FIN * (b - a).days})
    n = pd.DataFrame(rows).dropna(subset=["net"])
    n["era"] = np.where(n.d <= kk.ESKI_END, "ESKI", "YENI")
    return n


def masks(n: pd.DataFrame) -> dict:
    out = {}
    for e in (0.005, 0.010):
        out[f"K1_{e}"] = (((n.pc / n.tw - 1) <= -e) & (n.pc < n.p60)).values
    for e in (0.003, 0.006):
        out[f"K3_{e}"] = ((n.pc / n.p60 - 1) <= -e).values
    return out


def st(n: pd.DataFrame, m: np.ndarray) -> dict:
    a, b = n.net[m], n.net[~m]
    return {"n": int(m.sum()), "ort": round(float(a.mean()), 1) if len(a) else None, "taban": round(float(b.mean()), 1),
            "en_kotu": round(float(a.min()), 1) if len(a) else None}


def main() -> None:
    RES.mkdir(exist_ok=True)
    xd, _ = kk.load("XAU", ROOT / "research/fibo_altin_bolge_20261116/cache")
    xm = KD.mt5_m30("XAUUSD")
    xm["sp"] = xm.sp / 10
    om = KD.mt5_m30("SpotCrude")
    om["sp"] = om.sp / 100
    feeds = {"XAU": [("DUKA", xd, 60), ("MT5", xm, 1800)], "OIL": [("MT5", om, 1800)]}
    out = {}
    for asset, fl in feeds.items():
        op, u = SPEC[asset]
        N = {nm: nights(b, st_, op, u) for nm, b, st_ in fl}
        main_nm = fl[0][0]
        n = N[main_nm]
        for k, m in masks(n).items():
            rec = {e: st(n[(n.era == e).values], m[(n.era == e).values]) for e in ("ESKI", "YENI")}
            rec["TUM"] = st(n, m)
            rec["P"] = round(G.KS.diff_p(n.net[m].values, n.d[m].astype(str).values, n.net[~m].values, n.d[~m].astype(str).values), 4)
            ok1 = all(rec[e]["ort"] is not None and rec[e]["ort"] > 0 and rec[e]["ort"] > rec[e]["taban"] for e in ("ESKI", "YENI"))
            ok2 = rec["P"] >= P_B
            if asset == "XAU":
                mm = N["MT5"]
                rec["MT5_kor"] = st(mm, masks(mm)[k])
                ok3 = rec["MT5_kor"]["ort"] is not None and rec["MT5_kor"]["ort"] > rec["MT5_kor"]["taban"]
                rec["hukum"] = "B" if ok1 and ok2 and ok3 else ("C+" if ok1 and ok3 else ("C" if ok1 else "X"))
            else:
                rec["hukum"] = "C+" if ok1 and ok2 else ("C" if ok1 else "X")
            out[f"{asset}_{k}"] = rec
            print(f"{asset} {k}: {rec['hukum']} | ESKİ {rec['ESKI']} | YENİ {rec['YENI']} | P {rec['P']} | MT5 kör {rec.get('MT5_kor')}", flush=True)
    (RES / "emtia.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
