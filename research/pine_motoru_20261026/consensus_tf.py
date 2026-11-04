"""EK-P7 tekrarı: tüm scriptleri 5m/15m/4h son 12.000 barında koştur, konsensüs kuralını aynı tanımla ölç.

Çıktı: results/konsensus_tf.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import consensus_test as CT  # noqa: E402
import replicate_pine as RP  # noqa: E402

RP.WORKERS = 6                           # madenciye bir çekirdek bırak
WINDOWS = ("tf_15m",)                 # kullanıcı kararı 2026-10-28: yalnız 15m


def main():
    import pine_src
    excl = CT.EV.lookahead_sids()
    sids = {r["sid"] for r in pine_src.iter_sources(True)} - excl
    rows = []
    for win in WINDOWS:
        RP.run_window(win, sids)
        tf = CT.EV.window_tf(win)
        for sym in CT.SYMS:
            d = CT.EV.window_frame(sym, win)
            c = CT.consensus_dir(sym, len(d), excl, HERE / "data/runs" / win)
            disc = np.flatnonzero(d.split.values == 0)
            for h in CT.HS:
                L = CT.E.labels(d, CT.data.bucket(d, tf), h, CT.GC.SPREAD[sym])
                W = CT.E.weights(L)
                for dr, T in CT.triggers(c, disc).items():
                    rows.append(dict(window=win, sym=sym, h=h, dir=dr,
                                     **CT.cell(T, h, L, W, 1.0 if dr == "BUY" else -1.0)))
        out = pd.DataFrame(rows)
        out.to_csv(HERE / "results/konsensus_tf.csv", index=False)
        o = out[out.window == win]
        print(win, "kanıtlı", int(o.kanitli.sum()), "/", len(o), "; DAX h16 AL:",
              o[(o.sym == "DAX") & (o.h == 16) & (o.dir == "BUY")][["KASA_n", "KASA_z", "kanitli"]].to_dict("records"),
              flush=True)


if __name__ == "__main__":
    main()
