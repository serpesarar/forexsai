"""geometry_apply.py — yeni geometriyi GERÇEK pulse sinyalleri üzerinde test et.

Soru: "TP/SL'yi ATR-ölçekli ve yüksek RR yaparsak NDX BUY +EV olur mu, ve pulse
sinyali bu geometride bir SEÇİM DEĞERİ katıyor mu (yoksa rastgele giriş kadar mı)?"

Her şey 1m çözünürlükte, sızıntısız, botun gerçek akışıyla (scope başına 1 poz).
Karşılaştırma tabanı: AYNI geometriyle her 15m barda açılan ızgara işlemleri.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from engine import DATA, add_indicators, asof_features, load_bars, resample_from

FRICTION = 1.0
MAX_HOLD = 2880          # 2 gün piyasa dakikası (geniş TP'ler için yer aç)
MODELS = ["pulse1", "pulse2", "pulse3"]

SPLIT_TRAIN_END = pd.Timestamp("2026-05-05", tz="UTC")
SPLIT_VAL_END = pd.Timestamp("2026-06-12", tz="UTC")


def replay_atr(bars: np.ndarray, ts1m: np.ndarray, t: np.datetime64, direction: str,
               tp_dist: float, sl_dist: float) -> dict | None:
    i = np.searchsorted(ts1m, t, side="right")
    if i >= len(ts1m) or not np.isfinite(tp_dist) or tp_dist <= 0 or sl_dist <= 0:
        return None
    sgn = 1.0 if direction == "BUY" else -1.0
    entry = bars[i, 0] + sgn * FRICTION
    tp_px, sl_px = entry + sgn * tp_dist, entry - sgn * sl_dist
    end = min(len(ts1m), i + MAX_HOLD + 2)
    for j in range(i, end):
        hi, lo = bars[j, 1], bars[j, 2]
        hit_sl = (lo <= sl_px) if direction == "BUY" else (hi >= sl_px)
        hit_tp = (hi >= tp_px) if direction == "BUY" else (lo <= tp_px)
        if hit_sl:
            return dict(outcome=0, exit_i=j, r=-(sl_dist + FRICTION) / sl_dist,
                        bars_held=j - i, ambiguous=bool(hit_tp))
        if hit_tp:
            return dict(outcome=1, exit_i=j, r=(tp_dist - FRICTION) / sl_dist,
                        bars_held=j - i, ambiguous=False)
        if (j - i) >= MAX_HOLD:
            pnl = sgn * (bars[j, 3] - entry) - FRICTION
            return dict(outcome=int(pnl > 0), exit_i=j, r=pnl / sl_dist,
                        bars_held=j - i, ambiguous=False)
    return None


def atr_series(b1: pd.DataFrame) -> pd.DataFrame:
    h1 = resample_from(b1, "1h")
    f = add_indicators(h1, "H1")[["known_at", "H1_atr", "H1_stoch_k",
                                  "H1_sar_dist_atr", "H1_rsi", "H1_dist_ema200_atr"]]
    return f


def split_of(ts: pd.Series) -> pd.Series:
    p = pd.Timedelta(days=2)
    return np.where(ts < SPLIT_TRAIN_END - p, "train",
                    np.where(ts < SPLIT_TRAIN_END, "purge",
                             np.where(ts < SPLIT_VAL_END - p, "val",
                                      np.where(ts < SPLIT_VAL_END, "purge", "test"))))


def episodes(d: pd.DataFrame, b1: pd.DataFrame) -> pd.DataFrame:
    out = []
    for direction in ("BUY", "SELL"):
        sub = d[d.direction == direction].sort_values("ts")
        open_until = None
        for r in sub.itertuples(index=False):
            if open_until is not None and r.ts < open_until:
                continue
            open_until = b1["ts"].iloc[int(r.exit_i)]
            out.append(r._asdict())
    return pd.DataFrame(out)


def line(x: pd.DataFrame, label: str) -> str:
    if len(x) == 0:
        return f"    {label:44s} n=0"
    return (f"    {label:44s} n={len(x):5d}  WR={x.outcome.mean()*100:5.1f}%  "
            f"EV={x.r.mean():+.4f}R  tot={x.r.sum():+7.1f}R")


def main() -> None:
    b1 = load_bars("1m")
    ts1m = b1["ts"].values
    arr = b1[["open", "high", "low", "close"]].to_numpy()
    af = atr_series(b1)

    s = pd.read_csv(DATA / "signals.csv")
    s["ts"] = pd.to_datetime(s["created_at"], utc=True, format="mixed")
    s = s[s.model_type.isin(MODELS) & s.ml_direction.isin(["BUY", "SELL"])]
    s = s[(s.ts >= b1.ts.min()) & (s.ts <= b1.ts.max() - pd.Timedelta(days=2))]
    s = s[["id", "ts", "model_type", "ml_direction", "ml_confidence"]].sort_values("ts")
    s = asof_features(s, af.assign(ts=af["known_at"])).drop(columns=["known_at"])

    step = resample_from(b1, "15m")
    grid = pd.DataFrame({"ts": step["ts"] + pd.Timedelta(minutes=15)})
    grid = grid[(grid.ts >= b1.ts.min() + pd.Timedelta(days=12)) &
                (grid.ts <= b1.ts.max() - pd.Timedelta(days=2))]
    grid = asof_features(grid, af.assign(ts=af["known_at"])).drop(columns=["known_at"])

    GEOMS = [("bot (80/110 sabit)", None, None),
             ("ATR 1.5 / 1.0", 1.5, 1.0),
             ("ATR 2.0 / 1.0", 2.0, 1.0),
             ("ATR 2.5 / 1.0", 2.5, 1.0),
             ("ATR 2.0 / 0.75", 2.0, 0.75),
             ("ATR 3.0 / 0.75", 3.0, 0.75)]

    print(f"H1 ATR medyanı (son 30 gün): "
          f"{af[af.known_at > af.known_at.max() - pd.Timedelta(days=30)].H1_atr.median():.1f} puan\n")

    for gname, ktp, ksl in GEOMS:
        print(f"══════ GEOMETRİ: {gname} ══════")
        for name, src in (("IZGARA (rastgele giriş)", grid), ("PULSE sinyali", s)):
            rows = []
            for r in src.itertuples(index=False):
                atr = getattr(r, "H1_atr", np.nan)
                if ktp is None:
                    tp, sl = 80.0, 110.0
                else:
                    if not np.isfinite(atr) or atr <= 0:
                        continue
                    tp, sl = ktp * atr, ksl * atr
                dirs = ("BUY", "SELL") if name.startswith("IZGARA") else (r.ml_direction,)
                for direction in dirs:
                    res = replay_atr(arr, ts1m, np.datetime64(r.ts), direction, tp, sl)
                    if res is None:
                        continue
                    rows.append(dict(ts=r.ts, direction=direction,
                                     model=getattr(r, "model_type", "grid"),
                                     H1_stoch_k=getattr(r, "H1_stoch_k", np.nan),
                                     H1_sar_dist_atr=getattr(r, "H1_sar_dist_atr", np.nan),
                                     H1_rsi=getattr(r, "H1_rsi", np.nan),
                                     H1_dist_ema200_atr=getattr(r, "H1_dist_ema200_atr", np.nan),
                                     **res))
            d = pd.DataFrame(rows)
            if d.empty:
                continue
            d["split"] = split_of(d.ts)
            if name.startswith("PULSE"):
                d = episodes(d, b1)
                d["split"] = split_of(d.ts)
            for direction in ("BUY", "SELL"):
                x = d[d.direction == direction]
                print(line(x, f"{name} · {direction} · TÜM"))
                for sp in ("train", "val", "test"):
                    y = x[x.split == sp]
                    print(line(y, f"      {sp}"))
        print()


if __name__ == "__main__":
    main()
