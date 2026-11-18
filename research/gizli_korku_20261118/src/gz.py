"""gz.py — gizli korku: VIX ↑ ama NDX nakit seansı düşmedi (PROTOCOL). python gz.py"""
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
RES = ROOT / "research/gizli_korku_20261118/results"
NY = "America/New_York"
VS = (0.08, 0.12)
P_B = 1 - 0.05 / 4


def vix() -> pd.Series:
    m = pd.read_parquet(G.lib.MACRO)[["date", "VIX_close"]].dropna()
    s = pd.Series(m.VIX_close.values, index=pd.to_datetime(m.date).dt.date)
    return s.pct_change()


def table(b: pd.DataFrame, step: int) -> pd.DataFrame:
    dp = G.day_prices(b, NY, [570, 960], step)
    days = [z for z in dp.index if z.weekday() < 5 and G.nyse_ok(z) and np.isfinite(dp.loc[z, "o960"]) and np.isfinite(dp.loc[z, "o570"])]
    vc = vix()
    rows = []
    for i in range(len(days) - 2):
        d, d1, d2 = days[i], days[i + 1], days[i + 2]
        pin = dp.loc[d1, "o570"] + dp.loc[d1, "s570"]
        rows.append({"d": d, "rth": dp.loc[d, "o960"] / dp.loc[d, "o570"] - 1, "dv": vc.get(d, np.nan),
                     "x1": (dp.loc[d1, "o960"] / pin - 1) * 1e4,
                     "x2": (dp.loc[d2, "o960"] / pin - 1) * 1e4 - kk.FIN * (d2 - d1).days})
    t = pd.DataFrame(rows).dropna(subset=["dv"])
    t["era"] = np.where(t.d <= kk.ESKI_END, "ESKI", "YENI")
    return t


def st(t: pd.DataFrame, m: np.ndarray, col: str) -> dict:
    a, b = t[col][m], t[col][~m]
    return {"n": int(m.sum()), "ort": round(float(a.mean()), 1) if len(a) else None, "taban": round(float(b.mean()), 1),
            "D": round(float(a.mean() - b.mean()), 1) if len(a) else None}


def main() -> None:
    RES.mkdir(exist_ok=True)
    T = {"NDX_DUKA": table(G.ndx_bars(), 60), "NAS100_MT5": table(KD.mt5_m30("NAS100"), 1800),
         "US30": table(KD.mt5_m30("US30"), 1800), "US2000": table(KD.mt5_m30("US2000"), 1800)}
    out = {}
    for v in VS:
        for col in ("x1", "x2"):
            rec = {}
            N = T["NDX_DUKA"]
            gz = ((N.dv >= v) & (N.rth > -0.003)).values
            ac = ((N.dv >= v) & (N.rth <= -0.003)).values
            for e in ("ESKI", "YENI"):
                s = (N.era == e).values
                rec[e] = st(N[s], gz[s], col)
                rec[e + "_acik_korku"] = st(N[s], ac[s], col)
            rec["TUM"] = st(N, gz, col)
            a, b = N[col][gz], N[col][~gz]
            p = G.KS.diff_p(a.values, N.d[gz].astype(str).values, b.values, N.d[~gz].astype(str).values)
            rec["P_D_pozitif"] = round(float(p), 4)
            for nm in ("NAS100_MT5", "US30", "US2000"):
                X = T[nm]
                rec[nm] = st(X, ((X.dv >= v) & (X.rth > -0.003)).values, col)
            sg = np.sign(rec["TUM"]["D"])
            same = np.sign(rec["ESKI"]["D"]) == sg == np.sign(rec["YENI"]["D"])
            feeds = all(np.sign(rec[nm]["D"]) == sg for nm in ("NAS100_MT5", "US30", "US2000"))
            pp = p if sg > 0 else 1 - p
            rec["hukum"] = ("B" if same and feeds and pp >= P_B else ("C+" if same and feeds else ("C" if same else "X"))) + (" AL" if sg > 0 else " SAT")
            out[f"v{v}_{col}"] = rec
            print(f"v{v} {col}: {rec['hukum']} | ESKİ {rec['ESKI']} açık {rec['ESKI_acik_korku']} | YENİ {rec['YENI']} açık {rec['YENI_acik_korku']} | P+ {p:.3f} | "
                  + " ".join(f"{nm} {rec[nm]['D']}(n{rec[nm]['n']})" for nm in ("NAS100_MT5", "US30", "US2000")), flush=True)
    (RES / "gizli_korku.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
