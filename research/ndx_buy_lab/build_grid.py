"""build_grid.py — "evren" veri seti: her 15m bar kapanışında BUY ve SELL denemesi.

Neden: pulse epizodları n≈472 — çok-testli filtre madenciliği için ÇOK AZ.
Bu ızgara, piyasanın kendi koşullu kenarını ölçer (pulse'tan bağımsız): "NDX'te
TP80/SL110 ile LONG girmek hangi koşullarda +EV?" n ≈ 10.000 → istatistik güçlü.

Sızıntı garantileri build_dataset.py ile birebir aynı (engine.py sözleşmesi).
Karar anı = 15m barın KAPANIŞI; giriş = ondan sonraki ilk 1m barın açılışı.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from engine import (DATA, Geometry, add_indicators, asof_features, load_bars,
                    replay_one, resample_from)
from build_dataset import day_features, macro_features

GEO = Geometry(tp=80.0, sl=110.0, friction=1.0, max_hold_min=1440)
STEP_TF = "15m"


def main() -> None:
    b1 = load_bars("1m")
    print(f"1m {len(b1)}  {b1.ts.min()} → {b1.ts.max()}")

    feats = []
    for prefix, tf in (("M1", "1m"), ("M5", "5m"), ("M15", "15m"),
                       ("M30", "30m"), ("H1", "1h"), ("H4", "4h")):
        src = b1 if tf == "1m" else resample_from(b1, tf)
        feats.append(add_indicators(src, prefix))
    dayf = day_features(b1)
    mac = macro_features()

    step = resample_from(b1, STEP_TF)
    # karar anı = barın kapanışı
    pts = pd.DataFrame({"ts": step["ts"] + pd.Timedelta(minutes=15)})
    pts = pts[(pts.ts >= b1.ts.min() + pd.Timedelta(days=12)) &
              (pts.ts <= b1.ts.max() - pd.Timedelta(days=2))]
    print(f"karar noktası: {len(pts)}")

    ts1m = b1["ts"].values
    arr = b1[["open", "high", "low", "close"]].to_numpy()
    rows = []
    for t in pts.ts.values:
        for direction in ("BUY", "SELL"):
            res = replay_one(arr, ts1m, t, direction, GEO)
            if res is None:
                continue
            rows.append(dict(ts=pd.Timestamp(t, tz="UTC"), direction=direction, **res))
    g = pd.DataFrame(rows)
    print(f"çözülen deneme: {len(g)}")

    for f in feats:
        g = asof_features(g, f).drop(columns=["known_at"])
    g = asof_features(g, dayf).drop(columns=["known_at"])
    if not mac.empty:
        g = pd.merge_asof(g.sort_values("ts"), mac.sort_values("known_at"),
                          left_on="ts", right_on="known_at",
                          direction="backward").drop(columns=["known_at"])

    g["mom_filter_pass"] = ((g["M15_stoch_k"] > 70) & (g["M15_dist_ema20_atr"] > 0.8) &
                            (g["H1_sar_dist_atr"] > 0)).astype(int)
    g["mom_filter_pass_sell"] = ((g["M15_stoch_k"] < 30) & (g["M15_dist_ema20_atr"] < -0.8) &
                                 (g["H1_sar_dist_atr"] < 0)).astype(int)
    g.to_parquet(DATA / "grid.parquet", index=False)
    print(f"grid → {DATA/'grid.parquet'}  {g.shape}")
    for direction in ("BUY", "SELL"):
        x = g[g.direction == direction]
        print(f"  {direction}: n={len(x)} WR={x.outcome.mean()*100:.1f}% "
              f"EV={x.r.mean():+.4f}R  (timeout {x.get('timeout', pd.Series(dtype=float)).fillna(False).sum():.0f})")


if __name__ == "__main__":
    main()
