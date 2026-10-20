"""Ek (ön-kayıt eki 2026-10-20, sonuca bakmadan): USOIL canlı kapıları (POSITION_GATE, TREND_GATE) engelledikleri
sinyallerle botun AÇTIĞI MOMSR BUY girişlerini AYNI sabit geometride (TP %1,04 / SL %1,49) ve aynı dönemde
(07-29 → 10-20) kıyaslar. Kapı haklıysa engellenenlerin ortR'si açılanlardan belirgin düşük olmalı (gün-blok fark
%95 alt sınırı < 0). python3 research/usoil_hafta_20261020/kapilar.py"""
from __future__ import annotations

import numpy as np
import pandas as pd

import run as U

C = U.C


def boot_diff(a: pd.DataFrame, b: pd.DataFrame, n: int = 3000) -> tuple[float, float, float]:
    da, db = C.day_ids(a.t), C.day_ids(b.t)
    ga = {d: a.R.to_numpy()[da == d] for d in np.unique(da)}
    gb = {d: b.R.to_numpy()[db == d] for d in np.unique(db)}
    ka, kb = list(ga), list(gb)
    vals = []
    for _ in range(n):
        xa = np.concatenate([ga[k] for k in U.RNG.choice(ka, len(ka))])
        xb = np.concatenate([gb[k] for k in U.RNG.choice(kb, len(kb))])
        vals.append(xa.mean() - xb.mean())
    v = np.array(vals)
    return float(np.quantile(v, .025)), float(np.quantile(v, .975)), float((v < 0).mean())


def main() -> None:
    df = U.bars()
    sb = C.SymbolBars(U.SYM, df)
    k1 = pd.read_parquet(U.OUT / "k1.parquet")
    k2 = pd.read_parquet(U.OUT / "k2.parquet")
    lo = k2.t.min()
    taken = k1[k1.t >= lo][["t"]].copy()
    taken["R"] = U.sim(sb, taken)
    taken = taken[np.isfinite(taken.R)]
    rows = [{"küme": "bot AÇTI (MOMSR BUY, sabit geometri)", "n": len(taken), "ortR": taken.R.mean(), "WR": (taken.R > 0).mean()}]
    L = ["# USOIL canlı kapıları: engellenen vs açılan (aynı geometri, 07-29 → 10-20)"]
    for reason in ("position_gate", "trend_gate"):
        g = k2[(k2.reason == reason) & np.isfinite(k2.R)]
        lo_, hi_, p = boot_diff(g, taken)
        rows.append({"küme": f"engellenen · {reason}", "n": len(g), "ortR": g.R.mean(), "WR": (g.R > 0).mean(),
                     "fark (engel − açılan)": g.R.mean() - taken.R.mean(), "%95": f"[{lo_:+.3f}…{hi_:+.3f}]",
                     "P(engel kötü)": p})
    L.append(C.md(pd.DataFrame(rows)))
    txt = "\n".join(L)
    (U.OUT / "kapilar.md").write_text(txt, encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    main()
