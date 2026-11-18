"""es.py — K1 ertesi seans 09:30→16:00 AL (PROTOCOL). python es.py"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
for p in ("research/korku_kuresel_20261118/src", "research/fitil_gece_20261118/src", "research/fitil_kesisim_20261118/src"):
    sys.path.insert(0, str(ROOT / p))
import kk  # noqa: E402
import gece_run as GR  # noqa: E402
import ksg_dogrulama as KD  # noqa: E402

G = kk.G
RES = ROOT / "research/korku_ertesi_seans_20261118/results"
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
        o9, s9, c16 = dp.loc[c, "o570"], dp.loc[c, "s570"], dp.loc[c, "o960"]
        if not (np.isfinite(o9) and np.isfinite(c16)):
            continue
        rows.append({"d": a, "K1": bool((pc / tw.get(a, np.nan) - 1) <= -0.005 and pc < p60),
                     "seans": (c16 / (o9 + s9) - 1) * 1e4, "gece": (c16 / (pc + s) - 1) * 1e4})
    t = pd.DataFrame(rows)
    t["era"] = np.where(t.d <= kk.ESKI_END, "ESKI", "YENI")
    return t


def st(t: pd.DataFrame) -> dict:
    a, b = t.seans[t.K1], t.seans[~t.K1]
    return {"n": int(len(a)), "ort": round(float(a.mean()), 1), "taban": round(float(b.mean()), 1), "sd": round(float(a.std()), 1),
            "en_kotu": round(float(a.min()), 1), "isabet": round(float((a > 0).mean()), 3)}


def main() -> None:
    RES.mkdir(exist_ok=True)
    F = {"NDX_DUKA": (G.ndx_bars(), 60), **GR.feeds(), "US30": (KD.mt5_m30("US30"), 1800), "US2000": (KD.mt5_m30("US2000"), 1800),
         "US500": (KD.mt5_m30("US500", "2021-01-01"), 1800)}
    out = {}
    for nm, (b, step) in F.items():
        t = table(b, step)
        rec = {e or "TUM": st(t[t.era == e] if e else t) for e in ("ESKI", "YENI", None)}
        rec["P"] = round(G.KS.diff_p(t.seans[t.K1].values, t.d[t.K1].astype(str).values, t.seans[~t.K1].values, t.d[~t.K1].astype(str).values), 4)
        k = t[t.K1]
        rec["gece_ile_korelasyon"] = round(float(np.corrcoef(k.seans, k.gece)[0, 1]), 2)
        out[nm] = rec
        print(nm, json.dumps(rec, ensure_ascii=False), flush=True)
    N = out["NDX_DUKA"]
    ok1 = all(N[e]["ort"] > 0 and N[e]["ort"] > N[e]["taban"] for e in ("ESKI", "YENI"))
    kor = sum(out[s]["TUM"]["ort"] > 0 and out[s]["TUM"]["ort"] > out[s]["TUM"]["taban"] for s in ("US30", "US2000", "US500"))
    out["hukum"] = "B" if ok1 and kor >= 2 and N["P"] >= 0.99 else ("C+" if ok1 and kor >= 2 else ("C" if ok1 else "X"))
    print("hüküm:", out["hukum"], "kör geçen", kor)
    (RES / "ertesi_seans.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
