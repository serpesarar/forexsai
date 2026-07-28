"""final_signal_test.py — SAAT DÜZELTİLMİŞ nihai sinyal testi.

Üç soru, adil kıyasla (saat-eşitlenmiş taban + gün-bloklu bootstrap):
  S1  pulse BUY / SELL sinyalleri rastgele girişe göre değer katıyor mu?
  S2  botun momentum filtresi NDX BUY'da ne yapıyor?
  S3  K1 kapısı (H1 güçlü ayı trendi DEĞİL) ne yapıyor?

Kıyas tabanı: aynı SAAT kovalarında ağırlıklandırılmış ızgara EV'si — çünkü
pulse sinyalleri seans saatlerinde yoğunlaşır, ızgara ise 24 saate eşit dağılır;
NDX'in gece yukarı sürüklenmesi eşitlenmezse tek başına sahte asimetri üretir.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from engine import DATA, add_indicators, asof_features, resample_from
from fix_time import correct

SPREAD = 1.3
MAX_HOLD = 1440
RNG = np.random.default_rng(2026)


def load_bars_fixed() -> pd.DataFrame:
    df = pd.read_csv(DATA / "bars_1m.csv", parse_dates=["ts"])
    df["ts"] = pd.to_datetime(df["ts"], utc=True)
    return correct(df)


def replay(bars, ts1m, t, direction, tp_d, sl_d):
    i = np.searchsorted(ts1m, t, side="right")
    if i >= len(ts1m) or not np.isfinite(tp_d) or tp_d <= 0:
        return None
    sgn = 1.0 if direction == "BUY" else -1.0
    entry = bars[i, 0] + sgn * SPREAD
    tp_px, sl_px = entry + sgn * tp_d, entry - sgn * sl_d
    end = min(len(ts1m), i + MAX_HOLD + 2)
    for j in range(i, end):
        hi, lo = bars[j, 1], bars[j, 2]
        if (lo <= sl_px) if direction == "BUY" else (hi >= sl_px):
            return dict(outcome=0, r=-(sl_d + SPREAD) / sl_d, exit_i=j)
        if (hi >= tp_px) if direction == "BUY" else (lo <= tp_px):
            return dict(outcome=1, r=(tp_d - SPREAD) / sl_d, exit_i=j)
        if (j - i) >= MAX_HOLD:
            pnl = sgn * (bars[j, 3] - entry) - SPREAD
            return dict(outcome=int(pnl > 0), r=pnl / sl_d, exit_i=j)
    return None


def episodes(d, b1):
    out, open_until = [], None
    for r in d.sort_values("ts").itertuples(index=False):
        if open_until is not None and r.ts < open_until:
            continue
        open_until = b1["ts"].iloc[int(r.exit_i)]
        out.append(r._asdict())
    return pd.DataFrame(out)


def day_boot(x, B=4000):
    if len(x) == 0:
        return np.nan, np.nan, np.nan
    days = x.day.unique()
    by = {d: x.r.values[x.day.values == d] for d in days}
    o = np.empty(B)
    for i in range(B):
        pick = RNG.choice(days, size=len(days), replace=True)
        o[i] = np.concatenate([by[d] for d in pick]).mean()
    return float(np.quantile(o, .05)), float(np.quantile(o, .95)), float((o > 0).mean())


def hour_matched(rule_df, grid_df):
    w = rule_df.hour.value_counts(normalize=True)
    base = grid_df.groupby("hour").r.mean()
    c = w.index.intersection(base.index)
    return float((w[c] * base[c]).sum() / w[c].sum())


def main():
    pd.set_option("display.width", 230)
    b1 = load_bars_fixed()
    print(f"saat düzeltilmiş 1m barlar: {len(b1)}  {b1.ts.min()} → {b1.ts.max()}")
    prof = b1.assign(h=b1.ts.dt.hour, rng=b1.high - b1.low).groupby("h").rng.mean()
    print(f"doğrulama — en yüksek 1m aralık saati (13-14 UTC olmalı): {prof.idxmax()}\n")

    ts1m = b1["ts"].values
    arr = b1[["open", "high", "low", "close"]].to_numpy()
    f1h = add_indicators(resample_from(b1, "1h"), "H1")[
        ["known_at", "H1_atr", "H1_adx", "H1_di_diff", "H1_sar_dist_atr"]]
    f15 = add_indicators(resample_from(b1, "15m"), "M15")[
        ["known_at", "M15_stoch_k", "M15_dist_ema20_atr"]]

    s = pd.read_csv(DATA / "signals.csv")
    s["ts"] = pd.to_datetime(s["created_at"], utc=True, format="mixed")
    s = s[s.model_type.isin(["pulse1", "pulse2", "pulse3"]) & s.ml_direction.isin(["BUY", "SELL"])]
    s = s[(s.ts >= b1.ts.min() + pd.Timedelta(days=12)) & (s.ts <= b1.ts.max() - pd.Timedelta(days=2))]
    s = s[["id", "ts", "model_type", "ml_direction"]].sort_values("ts")

    step = resample_from(b1, "15m")
    g = pd.DataFrame({"ts": step["ts"] + pd.Timedelta(minutes=15)})
    g = g[(g.ts >= s.ts.min()) & (g.ts <= s.ts.max())]

    for src in (s, g):
        for f in (f1h, f15):
            src_idx = src.index
            merged = asof_features(src.reset_index(drop=True), f.assign(ts=f["known_at"]))
            src[list(f.columns.difference(["known_at", "ts"]))] = \
                merged[list(f.columns.difference(["known_at", "ts"]))].to_numpy()
    s = s[np.isfinite(s.H1_atr) & (s.H1_atr > 0)]
    g = g[np.isfinite(g.H1_atr) & (g.H1_atr > 0)]
    print(f"pulse sinyali: {len(s)} · ızgara noktası: {len(g)}\n")

    GEOMS = [("bot bugün 80/110", lambda a: (80.0, 110.0)),
             ("ATR 2.0/1.0", lambda a: (2.0 * a, 1.0 * a)),
             ("ATR 3.0/1.0", lambda a: (3.0 * a, 1.0 * a))]

    for gname, geo in GEOMS:
        print(f"══════ {gname} ══════")
        # ızgara (her iki yön)
        grows = []
        for r in g.itertuples(index=False):
            tp, sl = geo(r.H1_atr)
            for direction in ("BUY", "SELL"):
                res = replay(arr, ts1m, np.datetime64(r.ts), direction, tp, sl)
                if res:
                    grows.append(dict(ts=r.ts, direction=direction, **res))
        gd = pd.DataFrame(grows)
        gd["hour"] = gd.ts.dt.hour
        gd["day"] = gd.ts.dt.tz_convert("America/New_York").dt.date

        prows = []
        for r in s.itertuples(index=False):
            tp, sl = geo(r.H1_atr)
            res = replay(arr, ts1m, np.datetime64(r.ts), r.ml_direction, tp, sl)
            if res:
                prows.append(dict(ts=r.ts, direction=r.ml_direction, model=r.model_type,
                                  adx=r.H1_adx, di=r.H1_di_diff, stoch=r.M15_stoch_k,
                                  dist=r.M15_dist_ema20_atr, sar=r.H1_sar_dist_atr, **res))
        pd_all = pd.DataFrame(prows)
        rows = []
        for direction in ("BUY", "SELL"):
            gdd = gd[gd.direction == direction]
            ep = episodes(pd_all[pd_all.direction == direction], b1)
            ep["hour"] = ep.ts.dt.hour
            ep["day"] = ep.ts.dt.tz_convert("America/New_York").dt.date
            ep["MOM"] = ((ep.stoch > 70) & (ep.dist > 0.8) & (ep.sar > 0)) if direction == "BUY" \
                else ((ep.stoch < 30) & (ep.dist < -0.8) & (ep.sar < 0))
            ep["K1"] = ~((ep.adx > 25) & ((ep.di < 0) if direction == "BUY" else (ep.di > 0)))
            subsets = {"tümü": ep.index == ep.index, "MOM geçen": ep.MOM.to_numpy(),
                       "MOM elenen": ~ep.MOM.to_numpy(), "K1": ep.K1.to_numpy()}
            for nm, m in subsets.items():
                x = ep[m]
                if len(x) < 25:
                    continue
                hb = hour_matched(x, gdd)
                lo, hi, p = day_boot(x)
                rows.append(dict(yön=direction, küme=nm, n=len(x), gün=x.day.nunique(),
                                 WR=round(x.outcome.mean(), 3), EV=round(x.r.mean(), 4),
                                 ci5=round(lo, 3), ci95=round(hi, 3), P_poz=round(p, 3),
                                 saat_esit_taban=round(hb, 4),
                                 seçim_değeri=round(x.r.mean() - hb, 4)))
            rows.append(dict(yön=direction, küme="IZGARA (taban)", n=len(gdd),
                             gün=gdd.day.nunique(), WR=round(gdd.outcome.mean(), 3),
                             EV=round(gdd.r.mean(), 4), ci5=np.nan, ci95=np.nan,
                             P_poz=np.nan, saat_esit_taban=np.nan, seçim_değeri=np.nan))
        print(pd.DataFrame(rows).to_string(index=False))
        print()


if __name__ == "__main__":
    main()
