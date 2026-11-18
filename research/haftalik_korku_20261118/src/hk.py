"""hk.py — haftalık korku (PROTOCOL). python hk.py"""
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
RES = ROOT / "research/haftalik_korku_20261118/results"
NY = "America/New_York"
P_B = 1 - 0.05 / 4


def table(b: pd.DataFrame, step: int) -> pd.DataFrame:
    dp = G.day_prices(b, NY, [900, 960], step)
    x = G._local(b, NY)
    r = x[(x.mn >= 570) & (x.mn < 960)]
    dsum = r.groupby("day").c.agg(["sum", "count"])
    dtw = r.groupby("day").c.mean()
    days = [z for z in dp.index if z.weekday() < 5 and G.nyse_ok(z) and np.isfinite(dp.loc[z, "o960"]) and z in dsum.index]
    t = pd.DataFrame({"d": days, "p": dp.loc[days, "o960"].values, "s": dp.loc[days, "s960"].values, "p15": dp.loc[days, "o900"].values,
                      "sm": dsum.loc[days, "sum"].values, "cn": dsum.loc[days, "count"].values, "tw": dtw.loc[days].values})
    iso = pd.to_datetime(t.d).dt.isocalendar()
    t["wk"] = iso.year.astype(str) + "-" + iso.week.astype(str)
    last = t.groupby("wk").d.transform("max") == t.d
    wtw = t.groupby("wk").sm.transform("sum") / t.groupby("wk").cn.transform("sum")
    t["wtw"] = wtw
    t["K1"] = ((t.p / t.tw - 1) <= -0.005) & (t.p < t.p15)
    idx = np.flatnonzero(last.values)
    rows = []
    for j, i in enumerate(idx[1:-1], start=1):
        pin = t.p[i] + t.s[i]
        nx, nf = i + 1, idx[j + 1]
        rows.append({"d": t.d[i], "W1": bool(t.p[i] <= t.wtw[i] * 0.99 and t.p[i] < t.p15[i]), "W2": bool(t.p[i] / t.p[idx[j - 1]] - 1 <= -0.03),
                     "K1": bool(t.K1[i]),
                     "pzt": (t.p[nx] / pin - 1) * 1e4 - kk.FIN * (t.d[nx] - t.d[i]).days,
                     "hafta": (t.p[nf] / pin - 1) * 1e4 - kk.FIN * (t.d[nf] - t.d[i]).days})
    w = pd.DataFrame(rows)
    w["era"] = np.where(w.d <= kk.ESKI_END, "ESKI", "YENI")
    return w


def st(w: pd.DataFrame, m: np.ndarray, col: str) -> dict:
    a, b = w[col][m], w[col][~m]
    return {"n": int(m.sum()), "ort": round(float(a.mean()), 1) if len(a) else None, "taban": round(float(b.mean()), 1),
            "en_kotu": round(float(a.min()), 1) if len(a) else None}


def main() -> None:
    RES.mkdir(exist_ok=True)
    T = {"NDX_DUKA": table(G.ndx_bars(), 60), "NAS100_MT5": table(KD.mt5_m30("NAS100"), 1800),
         "US30": table(KD.mt5_m30("US30"), 1800), "US2000": table(KD.mt5_m30("US2000"), 1800)}
    out = {}
    for sig in ("W1", "W2"):
        for col in ("pzt", "hafta"):
            N = T["NDX_DUKA"]
            m = N[sig].values
            rec = {e: st(N[(N.era == e).values], m[(N.era == e).values], col) for e in ("ESKI", "YENI")}
            rec["TUM"] = st(N, m, col)
            rec["P"] = round(G.KS.diff_p(N[col][m].values, N.d[m].astype(str).values, N[col][~m].values, N.d[~m].astype(str).values), 4)
            rec["K1siz"] = st(N, m & ~N.K1.values, col)
            for nm in ("NAS100_MT5", "US30", "US2000"):
                rec[nm] = st(T[nm], T[nm][sig].values, col)
            ok1 = all(rec[e]["ort"] is not None and rec[e]["ort"] > 0 and rec[e]["ort"] > rec[e]["taban"] for e in ("ESKI", "YENI"))
            ok2 = all(rec[nm]["ort"] is not None and rec[nm]["ort"] > rec[nm]["taban"] for nm in ("NAS100_MT5", "US30", "US2000"))
            rec["hukum"] = "B" if ok1 and ok2 and rec["P"] >= P_B else ("C+" if ok1 and ok2 else ("C" if ok1 else "X"))
            out[f"{sig}_{col}"] = rec
            print(f"{sig} {col}: {rec['hukum']} | ESKİ {rec['ESKI']} | YENİ {rec['YENI']} | P {rec['P']} | K1'siz {rec['K1siz']} | "
                  + " ".join(f"{nm} {rec[nm]['ort']}/{rec[nm]['taban']}(n{rec[nm]['n']})" for nm in ("NAS100_MT5", "US30", "US2000")), flush=True)
    (RES / "haftalik.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
