"""ZA-05 EK-1: bağımsız 2016–17 + besleme teyidi."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
for p in ("research/habersiz_gunici_20261118/src", "research/fitil_kesisim_20261118/src", "research/fitil_gece_20261118/src"):
    sys.path.insert(0, str(ROOT / p))
import hg  # noqa: E402
import ksg_ek2 as E  # noqa: E402
import ksg_dogrulama as KD  # noqa: E402
import gece_run as GR  # noqa: E402


def main() -> None:
    cal = pd.read_csv(ROOT / "research/xau_best_days_20261015/makro/out/calendar.csv")
    ev = set(pd.to_datetime(cal.date).dt.date)
    feeds = {"DUKA_M30_2016_17": E.bars("DUKA_M30_2016_17"), "EET30_2016_17": E.bars("EET30"), "MT5_NAS100": (KD.mt5_m30("NAS100"), 1800),
             "NQ_5m": E.bars("NQ"), "MT5_US500": (KD.mt5_m30("US500", "2021-01-01"), 1800)}
    out = {}
    for nm, (b, st) in feeds.items():
        df = hg.table(b, st, ev)
        if nm.endswith("2016_17"):
            df = df[df.d <= pd.Timestamp("2017-12-31").date()]
        rec = {}
        for e in hg.ES:
            for grp, gm in (("habersiz", ~df.olay), ("olay", df.olay)):
                a, z = df[gm & (df.tag == f"e{e}")], df[gm & (df.tag == "rnd")]
                rec[f"e{e}_{grp}"] = {"n": int(len(a)), "ort": round(float(a.xn16.mean()), 1) if len(a) else None, "taban": round(float(z.xn16.mean()), 1)}
        out[nm] = rec
        print(nm, json.dumps(rec, ensure_ascii=False), flush=True)
    ok = {}
    for e in hg.ES:
        k = f"e{e}_habersiz"
        old = all(out[f][k]["ort"] is not None and out[f][k]["ort"] > out[f][k]["taban"] for f in ("DUKA_M30_2016_17", "EET30_2016_17"))
        fd = all(out[f][k]["ort"] is not None and out[f][k]["ort"] > out[f][k]["taban"] for f in ("MT5_NAS100", "NQ_5m"))
        ok[f"e{e}"] = "B (bağımsız dönem teyitli)" if old and fd else ("C+ kalır" if fd else "C+ / zayıf")
    out["hukum"] = ok
    print(ok)
    (ROOT / "research/habersiz_gunici_20261118/results/ek1.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
