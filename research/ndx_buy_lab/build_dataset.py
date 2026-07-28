"""build_dataset.py — NDX pulse sinyalleri için sızıntısız replay + özellik seti.

Çıktı: data/dataset.parquet  (her satır = bir sinyal, botun GERÇEK geometrisiyle
1m çözünürlükte çözülmüş sonuç + karar anında bilinen ~120 özellik)

Ayrıca: data/episodes.parquet — botun GERÇEK davranışını taklit eden "epizod"
seti (scope başına aynı anda 1 pozisyon; açıkken gelen sinyaller yeni işlem
AÇMAZ). İstatistik bunun üzerinden yapılır; ham sinyal seti n'i şişirir.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from engine import (DATA, Geometry, add_indicators, asof_features, load_bars,
                    replay_one, resample_from)

OUT = DATA
MODELS = ["pulse1", "pulse2", "pulse3"]
GEO = Geometry(tp=80.0, sl=110.0, friction=1.0, max_hold_min=1440)


# ─────────────────────── gün-içi / seans özellikleri ────────────────────────
def day_features(b1: pd.DataFrame) -> pd.DataFrame:
    """1m barlardan gün-içi durum. Satır i = i'inci bar KAPANDIĞINDA bilinen."""
    df = b1.copy()
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
    rng = df["day_range"].replace(0, np.nan)
    df["pos_in_day_range"] = (df["close"] - df["day_low"]) / rng

    # önceki günün kapanış/yüksek/düşük (yalnız geçmiş)
    daily = (df.groupby("et_date")
               .agg(d_open=("open", "first"), d_high=("high", "max"),
                    d_low=("low", "min"), d_close=("close", "last"))
               .reset_index())
    daily["prev_close"] = daily["d_close"].shift(1)
    daily["prev_high"] = daily["d_high"].shift(1)
    daily["prev_low"] = daily["d_low"].shift(1)
    daily["adr20"] = (daily["d_high"] - daily["d_low"]).shift(1).rolling(20).mean()
    daily["prev_ret"] = daily["d_close"].pct_change().shift(1) * 100
    daily["ret5d"] = (daily["d_close"] / daily["d_close"].shift(5) - 1).shift(1) * 100
    daily["ret20d"] = (daily["d_close"] / daily["d_close"].shift(20) - 1).shift(1) * 100
    daily["d_ema20"] = daily["d_close"].ewm(span=20, adjust=False).mean().shift(1)
    daily["d_ema50"] = daily["d_close"].ewm(span=50, adjust=False).mean().shift(1)
    daily["d_up_frac10"] = (daily["d_close"].diff() > 0).rolling(10).mean().shift(1)
    df = df.merge(daily.drop(columns=["d_open", "d_high", "d_low", "d_close"]),
                  on="et_date", how="left")

    df["gap_pct"] = (df["day_open"] / df["prev_close"] - 1) * 100
    df["day_range_vs_adr"] = df["day_range"] / df["adr20"].replace(0, np.nan)
    df["above_prev_high"] = (df["close"] > df["prev_high"]).astype(float)
    df["below_prev_low"] = (df["close"] < df["prev_low"]).astype(float)
    df["dist_d_ema20_pct"] = (df["close"] / df["d_ema20"] - 1) * 100
    df["dist_d_ema50_pct"] = (df["close"] / df["d_ema50"] - 1) * 100
    df["d_trend_up"] = (df["d_ema20"] > df["d_ema50"]).astype(float)

    cols = ["ts", "et_hour", "dow", "utc_hour", "min_since_open", "is_rth",
            "day_ret_pct", "pos_in_day_range", "day_range_vs_adr", "gap_pct",
            "above_prev_high", "below_prev_low", "prev_ret", "ret5d", "ret20d",
            "dist_d_ema20_pct", "dist_d_ema50_pct", "d_trend_up", "d_up_frac10"]
    out = df[cols].copy()
    out["known_at"] = out["ts"] + pd.Timedelta(minutes=1)
    return out


def macro_features() -> pd.DataFrame:
    """Günlük makro — SADECE önceki günün kapanışı (bugünkü kapanış bilinemez)."""
    p = DATA / "macro_daily.csv"
    if not p.exists():
        return pd.DataFrame()
    m = pd.read_csv(p, parse_dates=["date"]).sort_values("date")
    m["date"] = pd.to_datetime(m["date"], utc=True)
    f = pd.DataFrame({"date": m["date"]})
    for k in ("VIX", "DXY", "US10Y", "QQQ", "SPX", "VIX3M", "HYG", "TLT", "NDXCASH"):
        c = f"{k}_close"
        if c not in m.columns:
            continue
        f[f"mx_{k}"] = m[c]
        f[f"mx_{k}_chg1"] = m[c].pct_change() * 100
        f[f"mx_{k}_chg5"] = m[c].pct_change(5) * 100
    if "VIX_close" in m.columns and "VIX3M_close" in m.columns:
        f["mx_vix_term"] = m["VIX_close"] / m["VIX3M_close"]
    if "HYG_close" in m.columns and "TLT_close" in m.columns:
        f["mx_hyg_tlt"] = (m["HYG_close"] / m["HYG_close"].shift(5)) / \
                          (m["TLT_close"] / m["TLT_close"].shift(5))
    if "NDXCASH_close" in m.columns:
        c = m["NDXCASH_close"]
        f["mx_ndx_above_ema50d"] = (c > c.ewm(span=50, adjust=False).mean()).astype(float)
        f["mx_ndx_above_ema200d"] = (c > c.ewm(span=200, adjust=False).mean()).astype(float)
        f["mx_ndx_dd_from_ath60"] = (c / c.rolling(60).max() - 1) * 100
        f["mx_ndx_rvol20"] = c.pct_change().rolling(20).std() * 100
    # kapanış ancak ertesi gün 00:00 UTC'den itibaren "bilinen" sayılır
    f["known_at"] = f["date"] + pd.Timedelta(days=1)
    return f.drop(columns=["date"])


# ─────────────────────────── ana akış ────────────────────────────────────────
def main() -> None:
    print("bar yükleniyor…", flush=True)
    b1 = load_bars("1m")
    print(f"  1m {len(b1)}  {b1.ts.min()} → {b1.ts.max()}")

    feats = []
    for prefix, tf in (("M1", "1m"), ("M5", "5m"), ("M15", "15m"),
                       ("M30", "30m"), ("H1", "1h"), ("H4", "4h")):
        src = b1 if tf == "1m" else resample_from(b1, tf)
        f = add_indicators(src, prefix)
        feats.append(f)
        print(f"  özellik {prefix}: {len(f)} bar")
    dayf = day_features(b1)
    mac = macro_features()

    print("sinyaller…", flush=True)
    s = pd.read_csv(DATA / "signals.csv")
    s["ts"] = pd.to_datetime(s["created_at"], utc=True, format="mixed")
    s = s[s.model_type.isin(MODELS) & s.ml_direction.isin(["BUY", "SELL"])]
    s = s[(s.ts >= b1.ts.min()) & (s.ts <= b1.ts.max())].sort_values("ts")
    print(f"  {len(s)} pulse sinyali  {s.ts.min()} → {s.ts.max()}")

    # ── replay ──
    ts1m = b1["ts"].values
    arr = b1[["open", "high", "low", "close"]].to_numpy()
    recs = []
    for r in s.itertuples(index=False):
        res = replay_one(arr, ts1m, np.datetime64(r.ts), r.ml_direction, GEO)
        if res is None:
            continue
        recs.append(dict(sig_id=r.id, ts=r.ts, model=r.model_type,
                         direction=r.ml_direction, conf=r.ml_confidence,
                         backend_status=r.status, **res))
    d = pd.DataFrame(recs)
    d["entry_ts"] = d["ts"]
    print(f"  çözülen: {len(d)}  (timeout {d.get('timeout', pd.Series(dtype=float)).fillna(False).sum():.0f})")

    # ── özellikleri iliştir (hepsi asof: açık bar sızmaz) ──
    for f in feats:
        d = asof_features(d, f).drop(columns=["known_at"])
    d = asof_features(d, dayf).drop(columns=["known_at"])
    if not mac.empty:
        d = pd.merge_asof(d.sort_values("ts"), mac.sort_values("known_at"),
                          left_on="ts", right_on="known_at",
                          direction="backward").drop(columns=["known_at"])

    # botun canlı kapıları (yeniden hesaplanan, aynı tanım)
    d["mom_filter_pass"] = ((d["M15_stoch_k"] > 70) &
                            (d["M15_dist_ema20_atr"] > 0.8) &
                            (d["H1_sar_dist_atr"] > 0)).astype(int)
    d["mom_filter_pass_sell"] = ((d["M15_stoch_k"] < 30) &
                                 (d["M15_dist_ema20_atr"] < -0.8) &
                                 (d["H1_sar_dist_atr"] < 0)).astype(int)
    d["vix_regime_buy_ok"] = (d.get("mx_VIX", pd.Series(np.nan, index=d.index)) >= 18.4).astype(float)
    d["session_blocked"] = d["utc_hour"].isin([3, 4, 18, 22]).astype(int)

    d.to_parquet(OUT / "dataset.parquet", index=False)
    print(f"dataset → {OUT/'dataset.parquet'}  {d.shape}")

    # ── epizodlar: scope başına aynı anda 1 pozisyon (botun gerçeği) ──
    eps = []
    for direction in ("BUY", "SELL"):
        sub = d[d.direction == direction].sort_values("ts").reset_index(drop=True)
        open_until = None
        for r in sub.itertuples(index=False):
            if open_until is not None and r.ts < open_until:
                continue
            exit_ts = b1["ts"].iloc[int(r.exit_i)]
            open_until = exit_ts
            eps.append({**r._asdict()})
    e = pd.DataFrame(eps)
    e.to_parquet(OUT / "episodes.parquet", index=False)
    print(f"episodes → {len(e)}  BUY {int((e.direction=='BUY').sum())} / "
          f"SELL {int((e.direction=='SELL').sum())}")

    for name, frame in (("TÜM SİNYAL", d), ("EPİZOD", e)):
        for direction in ("BUY", "SELL"):
            x = frame[frame.direction == direction]
            if len(x) == 0:
                continue
            print(f"  {name:10s} {direction}: n={len(x):5d} WR={x.outcome.mean()*100:5.1f}% "
                  f"totalR={x.r.sum():+7.1f} EV/işlem={x.r.mean():+.3f}R")


if __name__ == "__main__":
    main()
