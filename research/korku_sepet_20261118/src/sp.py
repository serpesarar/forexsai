"""sp.py — K1 korku gecesi sepeti (PROTOCOL). python sp.py"""
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

RES = ROOT / "research/korku_sepet_20261118/results"


def met(s: pd.Series) -> dict:
    cs = s.cumsum()
    return {"sharpe": round(float(s.mean() / s.std() * np.sqrt(252)), 3), "yillik": round(float(s.mean() * 252), 2),
            "maxDD": round(float((cs - cs.cummax()).min()), 2)}


def main() -> None:
    RES.mkdir(exist_ok=True)
    cols = {}
    for sym, since in (("NAS100", None), ("US30", None), ("US2000", None), ("US500", "2021-01-01")):
        n = gn.nts(KD.mt5_m30(sym, since), 1800)
        k = n[n.K1]
        cols[sym] = (k.set_index("d").net / k.net.std())
    days = sorted(set().union(*[set(gn.nts(KD.mt5_m30("NAS100"), 1800).d)]))
    P = pd.DataFrame({s: c.reindex(days).fillna(0.0) for s, c in cols.items()}, index=pd.to_datetime(days))
    P = P[P.index >= pd.Timestamp("2018-05-15")]
    tek = P["NAS100"]
    sep = P[["NAS100", "US30", "US2000"]].sum(1) / 3
    s4 = P[["NAS100", "US30", "US2000", "US500"]].sum(1) / 4
    E = pd.Timestamp(gn.kk.ESKI_END)
    out = {}
    for nm, s in (("tek_NAS100", tek), ("sepet_3", sep)):
        out[nm] = {"TUM": met(s), "ESKI": met(s[s.index <= E]), "YENI": met(s[s.index > E])}
    m21 = P.index >= pd.Timestamp("2021-01-01")
    out["bilgi_2021_sonrasi"] = {"tek": met(tek[m21]), "sepet_3": met(sep[m21]), "sepet_4": met(s4[m21])}
    act = P.replace(0, np.nan)
    out["korelasyon_ortak_gun"] = act.corr(min_periods=10).round(2).to_dict()
    out["tetik_sayisi"] = {s: int((P[s] != 0).sum()) for s in P}
    out["katki_toplam"] = {s: round(float(P[s].sum() / 3), 1) for s in ("NAS100", "US30", "US2000")}
    a, b = out["sepet_3"], out["tek_NAS100"]
    ok = all(a[e]["sharpe"] > b[e]["sharpe"] for e in ("ESKI", "YENI"))
    one = any(a[e]["sharpe"] > b[e]["sharpe"] for e in ("ESKI", "YENI"))
    out["hukum"] = "B" if ok and a["TUM"]["maxDD"] >= b["TUM"]["maxDD"] else ("C" if one else "X")
    print(json.dumps(out, indent=1, ensure_ascii=False, default=str))
    (RES / "sepet.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
