"""HK-1 X1 ek kontrolü (SONRADAN eklendi, ön kayıtta YOK): kenar giriş anında mı, yoksa çıkış kuralında mı?
C1: aynı yıl×saat rastgele giriş + AYNI EMA10/25 ters-kesişim çıkışı (+2×ATR koruma).
C2: C1 ama yalnız dizilimin zaten aynı yönde olduğu barlardan (10>25>50 BUY / 10<25<50 SELL) → "kesişim ANI" katkısı."""
from __future__ import annotations

import numpy as np
import pandas as pd

from common import OUT, SPREAD, SYMS, day_boot, ema, load, run_with_placebo, simulate
from hk1_ema import signals


def main() -> None:
    rows = []
    for tf in ["30m", "1h"]:
        for sym in SYMS:
            d = load(sym, tf)
            sig, e10, e25 = signals(d)
            e50 = ema(d.close, 50)
            a, sp = d.atr.values, SPREAD[sym]
            state = {1: (e10 > e25) & (e25 > e50), -1: (e10 < e25) & (e25 < e50)}

            def mk_factory(restrict: bool):
                def mk(i, direction, ref):
                    if ref is not None and restrict and not state[direction][i]:
                        return None
                    fn = (lambda j: e10[j] < e25[j]) if direction > 0 else (lambda j: e10[j] > e25[j])
                    return simulate(d, i, direction, 2 * a[i], None, 500, sp, exit_fn=fn)
                return mk
            for ctl, restrict in (("C1", False), ("C2", True)):
                t = run_with_placebo(d, sig, sym, mk_factory(restrict))
                t["tf"], t["ctl"] = tf, ctl
                rows.append(t)
    t = pd.concat(rows)
    t.to_parquet(OUT / "hk1_x1_check.parquet")
    for (tf, ctl, dr), g in t.dropna(subset=["d"]).groupby(["tf", "ctl", "dir"]):
        per = g.groupby("period").d.mean().round(3).to_dict()
        sp = (g.groupby("sym").d.mean() > 0).sum()
        print(tf, ctl, "BUY" if dr > 0 else "SELL", "n", len(g), "R", round(g.r.mean(), 3), "plc", round(g.plc.mean(), 3),
              "fark", round(g.d.mean(), 3), "P", round(day_boot(g), 3), per, f"sym+ {sp}/4")


if __name__ == "__main__":
    main()
