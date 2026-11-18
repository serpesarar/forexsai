"""fk.py — K1 gecesinde korkunun kaynağı: 10y getiri değişimi (PROTOCOL). python fk.py"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
for p in ("research/korku_genislik_20261118/src", "research/fitil_kesisim_20261118/src"):
    sys.path.insert(0, str(ROOT / p))
import gn  # noqa: E402
import ksg_dogrulama as KD  # noqa: E402

G = gn.kk.G
RES = ROOT / "research/faiz_korku_20261118/results"


def tnx() -> pd.Series:
    d = pd.read_parquet(ROOT / "research/qs03_akis_takvim_20261111/data/TNX.parquet")
    c = d.Close.copy()
    c.index = pd.to_datetime(c.index).date
    return (c.diff() * 100).dropna()


def st(v: pd.Series) -> dict:
    return {"n": int(len(v)), "ort": round(float(v.mean()), 1) if len(v) else None, "sd": round(float(v.std()), 1) if len(v) > 1 else None,
            "en_kotu": round(float(v.min()), 1) if len(v) else None}


def main() -> None:
    RES.mkdir(exist_ok=True)
    dy = tnx()
    out = {}
    for nm, (b, step) in {"NDX_DUKA": (G.ndx_bars(), 60), "US30": (KD.mt5_m30("US30"), 1800), "US2000": (KD.mt5_m30("US2000"), 1800)}.items():
        n = gn.nts(b, step)
        n = n[n.K1 & n.d.isin(dy.index)].copy()
        n["dy"] = dy.reindex(n.d).values
        n["kova"] = np.where(n.dy >= 5, "F+", np.where(n.dy <= -5, "F-", "F0"))
        rec = {e or "TUM": {k: st((n[n.era == e] if e else n)[lambda x: x.kova == k].net) for k in ("F+", "F0", "F-")} for e in ("ESKI", "YENI", None)}
        a, z = n[n.kova == "F-"], n[n.kova == "F+"]
        p = G.KS.diff_p(a.net.values, a.d.astype(str).values, z.net.values, z.d.astype(str).values)
        rec["P_Fminus_gt_Fplus"] = round(float(p), 4)
        rec["D"] = {e: round(rec[e]["F-"]["ort"] - rec[e]["F+"]["ort"], 1) for e in ("ESKI", "YENI", "TUM")}
        out[nm] = rec
        print(nm, json.dumps(rec, ensure_ascii=False), flush=True)
    N = out["NDX_DUKA"]
    sg = np.sign(N["D"]["TUM"])
    same = np.sign(N["D"]["ESKI"]) == sg == np.sign(N["D"]["YENI"])
    pp = N["P_Fminus_gt_Fplus"] if sg > 0 else 1 - N["P_Fminus_gt_Fplus"]
    tr = all(np.sign(out[s]["D"]["TUM"]) == sg for s in ("US30", "US2000"))
    out["hukum"] = "C+" if same and pp >= 0.95 and tr else ("C" if same else "X")
    out["yon"] = "güvenliğe kaçış korkusu daha iyi" if sg > 0 else "faiz korkusu daha iyi"
    print(out["hukum"], out["yon"])
    (RES / "faiz_korku.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
