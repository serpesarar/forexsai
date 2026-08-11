"""USOIL BREAKOUT scope — sizintisiz olay cikarimi + durust TP/SL cozumleme.

Giris kurali botun KENDI kodundan birebir (check_usoil_breakout):
  Donchian(48) taze kirilim + 5m EMA200 ustu, karar SON KAPALI 5m barda.
Giris fiyati: bar kapanisindan sonraki ilk 1m barin acilisi + SPREAD (ask'ten alim).
Cozumleme: 1m bid barlariyla (yoksa 5m), ayni barda iki taraf da vurulursa
konservatif KAYIP. TP/SL mutlak fiyat → spread maliyeti dogal olarak icerde.
"""
from __future__ import annotations
import numpy as np, pandas as pd
from pathlib import Path

D = Path(__file__).resolve().parent / "data"
SPREAD = 0.028          # MT5 symbol_info('SpotCrude').spread=28 point × 0.001
N_DON, N_EMA, N_ATR = 48, 200, 14
MAX_HOLD_MIN = 24 * 60  # cozulmezse 24 saat sonra "acik" say (nadir)


def _ema(x, span):
    return pd.Series(x).ewm(span=span, adjust=False).mean().to_numpy()


def _rsi(c, n=14):
    d = np.diff(c, prepend=c[0])
    up = pd.Series(np.where(d > 0, d, 0.0)).ewm(alpha=1/n, adjust=False).mean()
    dn = pd.Series(np.where(d < 0, -d, 0.0)).ewm(alpha=1/n, adjust=False).mean()
    return (100 - 100 / (1 + up / dn.replace(0, np.nan))).fillna(50).to_numpy()


def _adx(h, l, c, n=14):
    up, dn = np.diff(h, prepend=h[0]), -np.diff(l, prepend=l[0])
    plus = np.where((up > dn) & (up > 0), up, 0.0)
    minus = np.where((dn > up) & (dn > 0), dn, 0.0)
    tr = np.maximum(h - l, np.maximum(abs(h - np.roll(c, 1)), abs(l - np.roll(c, 1))))
    tr[0] = h[0] - l[0]
    atr = pd.Series(tr).ewm(alpha=1/n, adjust=False).mean()
    pdi = 100 * pd.Series(plus).ewm(alpha=1/n, adjust=False).mean() / atr
    mdi = 100 * pd.Series(minus).ewm(alpha=1/n, adjust=False).mean() / atr
    dx = 100 * (pdi - mdi).abs() / (pdi + mdi).replace(0, np.nan)
    return dx.ewm(alpha=1/n, adjust=False).mean().fillna(0).to_numpy()


def load():
    b5 = pd.read_parquet(D / "USOIL_FOREX_5m.parquet")
    b1 = pd.read_parquet(D / "USOIL_FOREX_1m.parquet")
    return b5, b1


def build_events(b5: pd.DataFrame) -> pd.DataFrame:
    o, h, l, c = (b5[k].to_numpy() for k in ("open", "high", "low", "close"))
    v = b5.volume.to_numpy()
    t = b5.candle_time
    ema200, ema20, ema50 = _ema(c, N_EMA), _ema(c, 20), _ema(c, 50)
    tr = np.full(len(c), np.nan)
    tr[1:] = np.maximum(h[1:] - l[1:], np.maximum(abs(h[1:] - c[:-1]), abs(l[1:] - c[:-1])))
    atr = pd.Series(tr).rolling(N_ATR).mean().to_numpy()          # bot ile ayni (duz TR ort.)
    atr_slow = pd.Series(tr).rolling(100).mean().to_numpy()
    roll_max = pd.Series(h).rolling(N_DON).max().to_numpy()
    roll_min = pd.Series(l).rolling(N_DON).min().to_numpy()
    rsi, adx = _rsi(c), _adx(h, l, c)
    vol_ma = pd.Series(v).rolling(20).mean().to_numpy()
    day = t.dt.floor("D").to_numpy()
    dhigh = pd.Series(h).groupby(day).cummax().to_numpy()
    dlow = pd.Series(l).groupby(day).cummin().to_numpy()

    rows, prev_i = [], None
    for i in range(N_EMA + N_DON + 5, len(c)):
        lvl, lvl_prev = roll_max[i - 1], roll_max[i - 2]
        if not (c[i] > lvl and c[i - 1] <= lvl_prev and c[i] > ema200[i]):
            continue
        a = atr[i]
        if not np.isfinite(a) or a <= 0:
            continue
        rng = max(dhigh[i] - dlow[i], 1e-9)
        rows.append(dict(
            i=i, bar_time=t.iloc[i], level=lvl, close=c[i], atr=a,
            overshoot=(c[i] - lvl) / a,
            bar_range=(h[i] - l[i]) / a,
            body=(c[i] - o[i]) / a,
            upper_wick=(h[i] - c[i]) / a,
            ext_ema20=(c[i] - ema20[i]) / a,
            ext_ema50=(c[i] - ema50[i]) / a,
            ext_ema200=(c[i] - ema200[i]) / a,
            run12=(c[i] - c[i - 12]) / a,
            run36=(c[i] - c[i - 36]) / a,
            don_width=(lvl - roll_min[i - 1]) / a,
            day_pos=(c[i] - dlow[i]) / rng,
            day_rng_atr=rng / a,
            hour=int(pd.Timestamp(t.iloc[i]).hour),
            dow=int(pd.Timestamp(t.iloc[i]).dayofweek),
            rsi=rsi[i], adx=adx[i],
            vol_ratio=v[i] / vol_ma[i] if vol_ma[i] > 0 else np.nan,
            atr_pct=a / c[i] * 100,
            atr_ratio=a / atr_slow[i] if np.isfinite(atr_slow[i]) and atr_slow[i] > 0 else np.nan,
            bars_since_prev=(i - prev_i) if prev_i else 999,
        ))
        prev_i = i
    return pd.DataFrame(rows)


def resolve(ev: pd.DataFrame, b5: pd.DataFrame, b1: pd.DataFrame,
            tp_atr=1.0, sl_atr=1.0, spread=SPREAD) -> pd.DataFrame:
    """Her olay icin TP/SL yarisi — 1m varsa 1m, yoksa 5m; ayni bar → KAYIP."""
    t5 = b5.candle_time.dt.tz_localize(None).to_numpy()
    o5, h5, l5 = b5.open.to_numpy(), b5.high.to_numpy(), b5.low.to_numpy()
    t1 = b1.candle_time.dt.tz_localize(None).to_numpy()
    o1, h1, l1 = b1.open.to_numpy(), b1.high.to_numpy(), b1.low.to_numpy()
    t1_start = t1[0]
    out = []
    for r in ev.itertuples():
        close_time = np.datetime64((pd.Timestamp(r.bar_time) + pd.Timedelta(minutes=5)).tz_localize(None))
        use1 = close_time >= t1_start
        if use1:
            k = np.searchsorted(t1, close_time)
            if k >= len(t1):
                out.append((np.nan, np.nan, np.nan, np.nan)); continue
            entry = o1[k] + spread
            tp, sl = entry + tp_atr * r.atr, entry - sl_atr * r.atr
            hh, ll, tt = h1[k:], l1[k:], t1[k:]
            step = 1
        else:
            k = np.searchsorted(t5, close_time)
            if k >= len(t5):
                out.append((np.nan, np.nan, np.nan, np.nan)); continue
            entry = o5[k] + spread
            tp, sl = entry + tp_atr * r.atr, entry - sl_atr * r.atr
            hh, ll, tt = h5[k:], l5[k:], t5[k:]
            step = 5
        lim = min(len(hh), MAX_HOLD_MIN // step)
        win, mins = np.nan, np.nan
        for j in range(lim):
            hit_tp, hit_sl = hh[j] >= tp, ll[j] <= sl
            if hit_tp and hit_sl:
                win, mins = 0, (j + 1) * step; break        # konservatif
            if hit_sl:
                win, mins = 0, (j + 1) * step; break
            if hit_tp:
                win, mins = 1, (j + 1) * step; break
        out.append((entry, win, mins, 1 if use1 else 0))
    res = pd.DataFrame(out, columns=["entry", "win", "hold_min", "res_1m"], index=ev.index)
    ev = pd.concat([ev, res], axis=1)
    ev["slip"] = (ev.entry - ev.close) / ev.atr
    ev["R"] = np.where(ev.win == 1, tp_atr / sl_atr, -1.0)
    return ev.dropna(subset=["win"])


if __name__ == "__main__":
    b5, b1 = load()
    ev = build_events(b5)
    print(f"olay: {len(ev)}  {ev.bar_time.iloc[0]} → {ev.bar_time.iloc[-1]}")
    ev = resolve(ev, b5, b1)
    ev.to_parquet(D / "events.parquet")
    n, w = len(ev), int(ev.win.sum())
    print(f"cozulen: {n}  WR={100*w/n:.1f}%  ort.R={ev.R.mean():+.3f}  toplam={ev.R.sum():+.1f}R")
    print(f"ort. slip (ATR): {ev.slip.mean():+.3f}  medyan hold: {ev.hold_min.median():.0f} dk")
    sub = ev[ev.res_1m == 1]
    print(f"1m-cozulen alt kume: n={len(sub)} WR={100*sub.win.mean():.1f}% ort.R={sub.R.mean():+.3f}")
    sub5 = ev[ev.res_1m == 0]
    print(f"5m-cozulen alt kume: n={len(sub5)} WR={100*sub5.win.mean():.1f}% ort.R={sub5.R.mean():+.3f}")
