"""SONRADAN (post-hoc) duyarlılık — prereg.md Değişiklik 1. Verdikti değiştirmez; yalnız plato/yapı bilgisi."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_stres as rs  # noqa: E402
from engine import OUT, stats  # noqa: E402

D = rs.D
s30 = D.r.shift(1).rolling(30).std()


def rv(q: float) -> pd.Series:
    thr = s30.rolling(365, min_periods=120).quantile(q)
    return (s30 > thr) & thr.notna()


def rv_lo(q: float) -> pd.Series:
    thr = s30.rolling(365, min_periods=120).quantile(q)
    return (s30 <= thr) & thr.notna()


def row(name, t, c, **spec):
    spec.setdefault("hold", 0)
    df = rs.run_events(t, c, spec)
    out = {"hucre": name}
    for s in ("KESIF", "OOS", "KOR"):
        out[s] = {k: stats(df[df.seg == s]).get(k) for k in ("n", "ortR", "P_EV", "ort_ret_bp")}
    a = stats(df)
    out["TUM"] = {k: a.get(k) for k in ("n", "wr", "ortR", "ci95", "P_EV", "yari1", "yari2", "ort_ret_bp")}
    return out


res = []
cap = dict(exit="D0", stop="sig", fac=1.0, side=1)
for k in (0.75, 1.0, 1.25, 1.5, 2.0):
    st = rs.day_flags(k, "")
    for q in (0.4, 0.5, 0.6):
        t, c = rs.caprev_events(st & rv(q), "UTC")
        res.append(row(f"stres_k{k}_RV>q{q}_UTC_D0", t, c, **cap))
    t, c = rs.caprev_events(st & rv_lo(0.5), "UTC")
    res.append(row(f"stres_k{k}_RV<=q0.5_UTC_D0", t, c, **cap))
t, c = rs.caprev_events(~rs.day_flags(1.0, "") & D.sig20.notna() & rv(0.5), "UTC")
res.append(row("stressiz_RV>q0.5_UTC_D0", t, c, **cap))
t, c = rs.caprev_events(D.sig20.notna() & rv(0.5), "UTC")
res.append(row("tetik_RVyuksek_hepsi_UTC_D0", t, c, **cap))
# yukarı şok → BUY devam (G5 aynasının tersi; başka ailelerin alanı — yalnız not)
for z in (2.5, 3.5):
    t, c = rs.shock_events(z, -1)
    for hold in (1, 4):
        res.append(row(f"yukari_sok_z{z}_BUY_devam_s1_h{hold}", t, c, exit="H", hold=hold, stop="atr", fac=1.0,
                       side=1))
(OUT / "posthoc_g2.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str))
for r in res:
    print(f"{r['hucre']:38} TUM n={r['TUM']['n']:4} R={r['TUM']['ortR']} P={r['TUM']['P_EV']} | "
          + " ".join(f"{s}:{r[s]['n']}/{r[s]['ortR']}" for s in ("KESIF", "OOS", "KOR")))
