"""hb.py — habere dayanan / habersiz korku gecesi (PROTOCOL). python hb.py"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
for p in ("research/korku_genislik_20261118/src", "research/fitil_kesisim_20261118/src"):
    sys.path.insert(0, str(ROOT / p))
import gn  # noqa: E402
import ksg_dogrulama as KD  # noqa: E402

RES = ROOT / "research/haber_korku_20261118/results"
END = date(2026, 10, 2)


def main() -> None:
    RES.mkdir(exist_ok=True)
    c = pd.read_csv(ROOT / "research/xau_best_days_20261015/makro/out/calendar.csv")
    ev = set(pd.to_datetime(c.date).dt.date)
    out = {}
    F = {"NDX_DUKA": (gn.G.ndx_bars(), 60), "NAS100_MT5": (KD.mt5_m30("NAS100"), 1800), "US30": (KD.mt5_m30("US30"), 1800),
         "US2000": (KD.mt5_m30("US2000"), 1800)}
    for nm, (b, st) in F.items():
        n = gn.nts(b, st)
        n = n[n.d <= END].copy()
        n["olay"] = n.d.isin(ev)
        rec = {}
        for e in ("ESKI", "YENI", None):
            x = n[n.era == e] if e else n
            g = {}
            for grp, m in (("olay", x.olay), ("habersiz", ~x.olay)):
                y = x[m]
                g[grp] = {"n": int(y.K1.sum()), "K1": round(float(y.net[y.K1].mean()), 1), "taban": round(float(y.net[~y.K1].mean()), 1)}
                g[grp]["fark"] = round(g[grp]["K1"] - g[grp]["taban"], 1)
            g["DD"] = round(g["habersiz"]["fark"] - g["olay"]["fark"], 1)
            rec[e or "TUM"] = g
        out[nm] = rec
        print(nm, json.dumps(rec, ensure_ascii=False), flush=True)
    N = out["NDX_DUKA"]
    sg = np.sign(N["TUM"]["DD"])
    ok = all(np.sign(N[e]["DD"]) == sg for e in ("ESKI", "YENI")) and all(np.sign(out[s]["TUM"]["DD"]) == sg for s in ("US30", "US2000"))
    out["hukum"] = ("C+ " if ok else "X ") + ("habersiz korku daha güçlü" if sg > 0 else "olay günü korkusu daha güçlü")
    print(out["hukum"])
    (RES / "haber_korku.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
