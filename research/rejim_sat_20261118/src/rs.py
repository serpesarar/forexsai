"""rs.py — rejime bağlı SAT ve coşku devamı (PROTOCOL). python rs.py"""
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
RES = ROOT / "research/rejim_sat_20261118/results"
NY = "America/New_York"
P_B = 1 - 0.05 / 6


def table(b: pd.DataFrame, step: int) -> pd.DataFrame:
    dp = G.day_prices(b, NY, [900, 960], step)
    x = G._local(b, NY)
    tw = x[(x.mn >= 570) & (x.mn < 960)].groupby("day").c.mean()
    days = [z for z in dp.index if z.weekday() < 5 and G.nyse_ok(z) and np.isfinite(dp.loc[z, "o960"])]
    p, s, p15 = dp.loc[days, "o960"].values, dp.loc[days, "s960"].values, dp.loc[days, "o900"].values
    t = pd.DataFrame({"d": days, "p": p, "s": s, "p15": p15, "tw": tw.reindex(days).values})
    t["sma"] = t.p.rolling(200, min_periods=200).mean()
    t["ayi"] = t.p < t.sma
    t["K1"] = ((t.p / t.tw - 1) <= -0.005) & (t.p < t.p15)
    t["C1"] = ((t.p / t.tw - 1) >= 0.005) & (t.p > t.p15)
    t["C3"] = (t.p / t.p15 - 1) >= 0.003
    t["OK"] = t.K1.shift(1).fillna(False).astype(bool) & ((t.p / t.p.shift(1) - 1) >= 0.01)
    nd = pd.Series(days).shift(-1)
    nights = (pd.to_datetime(nd) - pd.to_datetime(pd.Series(days))).dt.days.values
    fin = kk.FIN * nights
    pn, sn = t.p.shift(-1).values, t.s.shift(-1).values
    t["long"] = (pn / (t.p + t.s) - 1) * 1e4 - fin
    t["short"] = -((pn + sn) / t.p - 1) * 1e4 - fin
    t = t.dropna(subset=["sma", "long"]).reset_index(drop=True)
    t["era"] = np.where(t.d <= kk.ESKI_END, "ESKI", "YENI")
    return t


def cell(t: pd.DataFrame, sig: str, reg: str, side: str, era: str | None) -> dict:
    r = t.ayi.values if reg == "AYI" else ~t.ayi.values
    if era:
        r = r & (t.era == era).values
    m = r & t[sig].values
    a, b = t[side][m], t[side][r & ~t[sig].values]
    out = {"n": int(m.sum()), "ort": round(float(a.mean()), 1) if len(a) else None, "taban": round(float(b.mean()), 1) if len(b) else None,
           "sd": round(float(a.std()), 1) if len(a) > 1 else None, "en_kotu": round(float(a.min()), 1) if len(a) else None}
    if len(a) > 2 and len(b) > 2:
        out["P"] = round(G.KS.diff_p(a.values, t.d[m].astype(str).values, b.values, t.d[r & ~t[sig].values].astype(str).values, n=3000), 4)
    return out


def main() -> None:
    RES.mkdir(exist_ok=True)
    T = {"NDX": table(G.ndx_bars(), 60), "US30": table(KD.mt5_m30("US30"), 1800), "US2000": table(KD.mt5_m30("US2000"), 1800)}
    out = {}
    for sig in ("C1", "C3", "OK"):
        for reg, side in (("AYI", "short"), ("BOGA", "long")):
            N = T["NDX"]
            rec = {e: cell(N, sig, reg, side, e) for e in ("ESKI", "YENI")}
            rec["TUM"] = cell(N, sig, reg, side, None)
            rec["US30"] = cell(T["US30"], sig, reg, side, None)
            rec["US2000"] = cell(T["US2000"], sig, reg, side, None)
            ok1 = all(rec[e]["ort"] is not None and rec[e]["ort"] > 0 and rec[e]["ort"] > rec[e]["taban"] for e in ("ESKI", "YENI"))
            ok2 = all(rec[s]["ort"] is not None and rec[s]["ort"] > rec[s]["taban"] for s in ("US30", "US2000"))
            ok3 = rec["TUM"].get("P", 0) >= P_B
            rec["hukum"] = "B" if ok1 and ok2 and ok3 else ("C+" if ok1 and ok2 else ("C" if ok1 else "X"))
            yrs = N[(N.ayi if reg == "AYI" else ~N.ayi) & N[sig]]
            rec["yillar"] = {int(y): [int(len(g)), round(float(g[side].mean()), 1)] for y, g in yrs.groupby(pd.to_datetime(yrs.d).dt.year)}
            out[f"{sig}_{reg}_{side}"] = rec
            print(f"{sig} {reg} {side}: {rec['hukum']} | ESKİ {rec['ESKI']} | YENİ {rec['YENI']} | US30 {rec['US30']['ort']}/{rec['US30']['taban']} "
                  f"US2000 {rec['US2000']['ort']}/{rec['US2000']['taban']} | P {rec['TUM'].get('P')} | yıllar {rec['yillar']}", flush=True)
    out["ayi_gun_orani"] = {k: round(float(v.ayi.mean()), 3) for k, v in T.items()}
    (RES / "rejim_sat.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
