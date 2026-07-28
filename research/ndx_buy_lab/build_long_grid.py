"""build_long_grid.py — UZUN GEÇMİŞ ızgarası (2023-03 → 2026-07), rejim sağlamlığı için.

Neden gerekli: birincil çalışma (1m çözünürlük) yalnız 2026-02→07 arasını kapsıyor
ve bu pencerede TEK bir büyük rejim dönüşü var. Orada bulunan her kural "tek
rejimde çalıştı" olur. Bu ızgara 3.5 yıl ve 4+ rejim içerir.

İKİ FARK ve nedenleri (ikisi de dürüstlük gereği):
1. ÇÖZÜNÜRLÜK 15m (1m yok). Aynı barda TP+SL → SL önce (konservatif). Bu, hem
   tabanı hem kuralı AYNI yönde bozar; kıyas adil kalır. `calibrate.py` bu
   sapmayı çakışan dönemde ölçer.
2. GEOMETRİ YÜZDESEL. 2023'te NDX ~12.000, bugün ~28.500. Sabit 80/110 PUAN
   2023'te bugünkünün 2.4 katı bir hareket demektir — yıllar arası kıyas
   anlamsız olurdu. Bu yüzden bugünün oranı sabitlenir:
       tp = %0.2759 (=80/29000),  sl = %0.3793 (=110/29000),  sürtünme %0.0034
   Böylece "aynı işlem" her yılda aynı zorlukta olur.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from engine import DATA, add_indicators, asof_features, parabolic_sar
from build_dataset import macro_features

REF_PRICE = 29000.0
TP_PCT = 80.0 / REF_PRICE
SL_PCT = 110.0 / REF_PRICE
FRIC_PCT = 1.0 / REF_PRICE
MAX_HOLD_BARS = 96          # 96 × 15m = 24 saat piyasa zamanı (1m'deki 1440 dk ile aynı)


def load_long(tf: str) -> pd.DataFrame:
    d = pd.read_csv(DATA / f"long_{tf}.csv", parse_dates=["ts"])
    d["ts"] = pd.to_datetime(d["ts"], utc=True)
    return d.sort_values("ts").drop_duplicates("ts").reset_index(drop=True)


def resample_from_15m(d15: pd.DataFrame, rule: str) -> pd.DataFrame:
    g = (d15.set_index("ts").resample(rule, label="left", closed="left")
         .agg({"open": "first", "high": "max", "low": "min",
               "close": "last", "volume": "sum"}).dropna(subset=["open"]))
    return g.reset_index()


def replay_pct(bars: np.ndarray, i: int, direction: str) -> dict | None:
    """15m barlarla yüzdesel geometri replay'i. Giriş = i. barın AÇILIŞI."""
    if i >= len(bars):
        return None
    sgn = 1.0 if direction == "BUY" else -1.0
    entry = bars[i, 0] * (1 + sgn * FRIC_PCT)
    tp_px = entry * (1 + sgn * TP_PCT)
    sl_px = entry * (1 - sgn * SL_PCT)
    end = min(len(bars), i + MAX_HOLD_BARS + 1)
    for j in range(i, end):
        hi, lo = bars[j, 1], bars[j, 2]
        hit_sl = (lo <= sl_px) if direction == "BUY" else (hi >= sl_px)
        hit_tp = (hi >= tp_px) if direction == "BUY" else (lo <= tp_px)
        if hit_sl:            # aynı barda ikisi de → SL önce (konservatif)
            return dict(outcome=0, r=-(SL_PCT + FRIC_PCT) / SL_PCT, bars_held=j - i,
                        ambiguous=bool(hit_tp))
        if hit_tp:
            return dict(outcome=1, r=(TP_PCT - FRIC_PCT) / SL_PCT, bars_held=j - i,
                        ambiguous=False)
        if (j - i) >= MAX_HOLD_BARS:
            px = bars[j, 3]
            ret = sgn * (px - entry) / entry - FRIC_PCT
            return dict(outcome=int(ret > 0), r=ret / SL_PCT, bars_held=j - i,
                        ambiguous=False)
    return None


def day_features_long(d15: pd.DataFrame) -> pd.DataFrame:
    df = d15.copy()
    et = df["ts"].dt.tz_convert("America/New_York")
    df["et_date"] = et.dt.date
    df["et_hour"] = et.dt.hour + et.dt.minute / 60.0
    df["dow"] = et.dt.dayofweek
    df["utc_hour"] = df["ts"].dt.hour
    df["min_since_open"] = (df["et_hour"] - 9.5) * 60
    df["is_rth"] = ((df["et_hour"] >= 9.5) & (df["et_hour"] < 16.0)).astype(int)
    g = df.groupby("et_date", sort=False)
    df["day_open"] = g["open"].transform("first")
    df["day_high"] = g["high"].cummax()
    df["day_low"] = g["low"].cummin()
    df["day_range"] = df["day_high"] - df["day_low"]
    df["day_ret_pct"] = (df["close"] / df["day_open"] - 1) * 100
    df["pos_in_day_range"] = (df["close"] - df["day_low"]) / df["day_range"].replace(0, np.nan)
    daily = (df.groupby("et_date").agg(d_high=("high", "max"), d_low=("low", "min"),
                                       d_close=("close", "last")).reset_index())
    daily["prev_close"] = daily["d_close"].shift(1)
    daily["prev_high"] = daily["d_high"].shift(1)
    daily["prev_low"] = daily["d_low"].shift(1)
    daily["adr20"] = (daily["d_high"] - daily["d_low"]).shift(1).rolling(20).mean()
    daily["prev_ret"] = daily["d_close"].pct_change(fill_method=None).shift(1) * 100
    daily["ret5d"] = (daily["d_close"] / daily["d_close"].shift(5) - 1).shift(1) * 100
    daily["ret20d"] = (daily["d_close"] / daily["d_close"].shift(20) - 1).shift(1) * 100
    dc = daily["d_close"]
    daily["d_ema20"] = dc.ewm(span=20, adjust=False).mean().shift(1)
    daily["d_ema50"] = dc.ewm(span=50, adjust=False).mean().shift(1)
    daily["d_ema200"] = dc.ewm(span=200, adjust=False).mean().shift(1)
    daily["d_up_frac10"] = (dc.diff() > 0).rolling(10).mean().shift(1)
    daily["d_rvol20"] = dc.pct_change(fill_method=None).rolling(20).std().shift(1) * 100
    daily["d_dd_from_ath60"] = (dc / dc.rolling(60).max() - 1).shift(1) * 100
    df = df.merge(daily.drop(columns=["d_high", "d_low", "d_close"]), on="et_date", how="left")
    df["gap_pct"] = (df["day_open"] / df["prev_close"] - 1) * 100
    df["day_range_vs_adr"] = df["day_range"] / df["adr20"].replace(0, np.nan)
    df["above_prev_high"] = (df["close"] > df["prev_high"]).astype(float)
    df["below_prev_low"] = (df["close"] < df["prev_low"]).astype(float)
    df["dist_d_ema20_pct"] = (df["close"] / df["d_ema20"] - 1) * 100
    df["dist_d_ema50_pct"] = (df["close"] / df["d_ema50"] - 1) * 100
    df["dist_d_ema200_pct"] = (df["close"] / df["d_ema200"] - 1) * 100
    df["d_trend_up"] = (df["d_ema20"] > df["d_ema50"]).astype(float)
    df["above_d_ema50"] = (df["close"] > df["d_ema50"]).astype(float)
    df["above_d_ema200"] = (df["close"] > df["d_ema200"]).astype(float)
    cols = ["ts", "et_hour", "dow", "utc_hour", "min_since_open", "is_rth",
            "day_ret_pct", "pos_in_day_range", "day_range_vs_adr", "gap_pct",
            "above_prev_high", "below_prev_low", "prev_ret", "ret5d", "ret20d",
            "dist_d_ema20_pct", "dist_d_ema50_pct", "dist_d_ema200_pct",
            "d_trend_up", "d_up_frac10", "above_d_ema50", "above_d_ema200",
            "d_rvol20", "d_dd_from_ath60"]
    out = df[cols].copy()
    out["known_at"] = out["ts"] + pd.Timedelta(minutes=15)
    return out


def main() -> None:
    d15 = load_long("15m")
    print(f"15m {len(d15)}  {d15.ts.min()} → {d15.ts.max()}")
    feats = [add_indicators(d15, "M15")]
    for prefix, rule in (("M30", "30min"), ("H1", "1h"), ("H4", "4h")):
        feats.append(add_indicators(resample_from_15m(d15, rule), prefix))
    dayf = day_features_long(d15)
    mac = macro_features()

    bars = d15[["open", "high", "low", "close"]].to_numpy()
    rows = []
    start = 300                      # gösterge ısınması
    for i in range(start, len(d15) - MAX_HOLD_BARS - 1):
        for direction in ("BUY", "SELL"):
            # karar anı = (i-1). barın kapanışı = i. barın açılışı
            res = replay_pct(bars, i, direction)
            if res is None:
                continue
            rows.append(dict(ts=d15.ts.iloc[i], direction=direction, **res))
    g = pd.DataFrame(rows)
    print(f"deneme: {len(g)}")

    for f in feats:
        g = asof_features(g, f).drop(columns=["known_at"])
    g = asof_features(g, dayf).drop(columns=["known_at"])
    if not mac.empty:
        g = pd.merge_asof(g.sort_values("ts"), mac.sort_values("known_at"),
                          left_on="ts", right_on="known_at",
                          direction="backward").drop(columns=["known_at"])
    g["mom_filter_pass"] = ((g["M15_stoch_k"] > 70) & (g["M15_dist_ema20_atr"] > 0.8) &
                            (g["H1_sar_dist_atr"] > 0)).astype(int)
    g.to_parquet(DATA / "long_grid.parquet", index=False)
    print(f"long_grid → {g.shape}")
    for direction in ("BUY", "SELL"):
        x = g[g.direction == direction]
        print(f"  {direction}: n={len(x)} WR={x.outcome.mean()*100:.1f}% EV={x.r.mean():+.4f}R")
    g["yil"] = g.ts.dt.year
    print(g[g.direction == "BUY"].groupby("yil").agg(
        n=("r", "size"), wr=("outcome", "mean"), ev=("r", "mean")).round(3).to_string())


if __name__ == "__main__":
    main()
