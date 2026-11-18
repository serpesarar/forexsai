"""os_.py — olay günü gün içi sert düşüş SAT (PROTOCOL). python os_.py"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
for p in ("research/habersiz_gunici_20261118/src", "research/fitil_kesisim_20261118/src"):
    sys.path.insert(0, str(ROOT / p))
import hg  # noqa: E402
import ksg_dogrulama as KD  # noqa: E402


def main() -> None:
    cal = pd.read_csv(ROOT / "research/xau_best_days_20261015/makro/out/calendar.csv")
    ev = set(pd.to_datetime(cal.date).dt.date)
    F = {"NDX_DUKA": (hg.G.ndx_bars(), 60), "US30": (KD.mt5_m30("US30"), 1800), "US2000": (KD.mt5_m30("US2000"), 1800)}
    out = {}
    for nm, (b, st) in F.items():
        df = hg.table(b, st, ev)
        df = df[df.olay].copy()
        fin = hg.kk.FIN * 1.0
        df["sat"] = -(df.xn16 + fin) - fin        # uzun net'ten kısa net: işaret çevir, uzun finansmanı geri ekle, kısa finansmanı düş
        rec = {}
        for e in hg.ES:
            a, z = df[df.tag == f"e{e}"], df[df.tag == "rnd"]
            rr = {er: {"n": int((a.era == er).sum()), "ort": round(float(a[a.era == er].sat.mean()), 1), "taban": round(float(z[z.era == er].sat.mean()), 1)}
                  for er in ("ESKI", "YENI")}
            rr["TUM"] = {"n": int(len(a)), "ort": round(float(a.sat.mean()), 1), "taban": round(float(z.sat.mean()), 1),
                         "P": round(hg.G.KS.diff_p(a.sat.values, a.d.astype(str).values, z.sat.values, z.d.astype(str).values), 4) if len(a) > 2 else None,
                         "en_kotu": round(float(a.sat.min()), 1) if len(a) else None}
            rr["yil"] = {int(y): [int(len(g)), round(float(g.sat.mean()), 1)] for y, g in a.groupby(pd.to_datetime(a.d).dt.year)}
            rec[f"e{e}"] = rr
        out[nm] = rec
        print(nm, json.dumps(rec, ensure_ascii=False), flush=True)
    hk = {}
    for e in hg.ES:
        N = out["NDX_DUKA"][f"e{e}"]
        ok1 = all(N[er]["ort"] > 0 and N[er]["ort"] > N[er]["taban"] for er in ("ESKI", "YENI"))
        ok2 = all(out[s][f"e{e}"]["TUM"]["ort"] > 0 and out[s][f"e{e}"]["TUM"]["ort"] > out[s][f"e{e}"]["TUM"]["taban"] for s in ("US30", "US2000"))
        hk[f"e{e}"] = "B" if ok1 and ok2 and (N["TUM"]["P"] or 0) >= 0.975 else ("C+" if ok1 and ok2 else ("C" if ok1 else "X"))
    out["hukum"] = hk
    print(hk)
    (ROOT / "research/olay_sat_20261118/results").mkdir(exist_ok=True)
    (ROOT / "research/olay_sat_20261118/results/olay_sat.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
