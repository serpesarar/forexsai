"""Nedensel özellikler: her satır = bar i KAPANIŞINDA bilinenler.

Bar-başı damgalı 1m barlardan. tf>1 ise koşullar tamamlanmış tf-barlarından
hesaplanıp 1m karar anlarına 'son tamamlanmış tf barı' olarak eşlenir.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from common import atr


def _last_complete(b: pd.DataFrame, tf: int) -> pd.DataFrame:
    """1m → tf dk barları (yalnız tam barlar), 'avail' = bar bitişi (s)."""
    g = b.set_index("ts")
    agg = g.resample(f"{tf}min", label="left", closed="left").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum", "t": "count"})
    agg = agg[agg.t >= max(1, int(tf * 0.8))].dropna().reset_index()
    agg["avail"] = agg.ts.astype("int64") // 10**9 + tf * 60
    return agg


def map_asof(dec_t: np.ndarray, avail: np.ndarray, values: np.ndarray, max_age_s: int | None = None) -> np.ndarray:
    k = np.searchsorted(avail, dec_t, side="right") - 1
    out = np.where(k >= 0, values[np.maximum(k, 0)], np.nan).astype(float)
    if max_age_s is not None:
        age = dec_t - avail[np.maximum(k, 0)]
        out[(k < 0) | (age > max_age_s)] = np.nan
    return out


def rolling_vr(ret: np.ndarray, q: int, win: int) -> np.ndarray:
    """Varyans oranı VR(q) = Var(q-dk getiri)/(q·Var(1dk)) son `win` dk üzerinden (örtüşen)."""
    r = pd.Series(ret)
    rq = r.rolling(q).sum()
    v1 = r.rolling(win).var()
    vq = rq.rolling(win - q + 1).var()
    return (vq / (q * v1)).to_numpy()


def build(b: pd.DataFrame, tf: int = 1) -> pd.DataFrame:
    """Tüm hipotez koşulları. tf: özelliklerin hesaplandığı bar boyu (1/5/15)."""
    f = pd.DataFrame(index=b.index)
    dec = b.t.to_numpy() + 60
    c = b.close.to_numpy()
    f["price"] = c
    # ---- tf-bar tabanlı hareket/volatilite özellikleri ----
    if tf == 1:
        src = b[["t", "open", "high", "low", "close", "volume"]].copy()
        src["avail"] = src.t + 60
    else:
        src = _last_complete(b[["ts", "t", "open", "high", "low", "close", "volume"]], tf)
    sh, sl_, sc, sv = (src[k].to_numpy(float) for k in ["high", "low", "close", "volume"])
    s_atr = atr(sh, sl_, sc, max(14, 70 // tf))
    lr = np.r_[np.nan, np.diff(np.log(sc))]
    lr[np.r_[False, np.diff(src.avail.to_numpy()) > 3 * tf * 60]] = np.nan
    q = max(3, 15 // tf)
    win = max(16, 240 // tf)
    vr = rolling_vr(np.nan_to_num(lr), q, win)
    skew = pd.Series(lr).rolling(max(24, 120 // tf)).skew().to_numpy()
    rv = pd.Series(lr).pow(2).rolling(max(2, 30 // tf)).sum().pow(.5).to_numpy()
    nvol = max(1, 15 // tf)
    v15 = pd.Series(sv).rolling(nvol).sum().to_numpy()
    rng15 = (pd.Series(sh).rolling(nvol).max() - pd.Series(sl_).rolling(nvol).min()).to_numpy()
    tr60 = sc - np.r_[np.full(max(1, 60 // tf), np.nan), sc[:-max(1, 60 // tf)]]
    # dalga konumu (POSITION_GATE): son 4 saat aralığında konum
    n4 = max(4, 240 // tf)
    hi4 = pd.Series(sh).rolling(n4).max().to_numpy()
    lo4 = pd.Series(sl_).rolling(n4).min().to_numpy()
    pos4 = (sc - lo4) / np.where(hi4 - lo4 > 0, hi4 - lo4, np.nan)
    av = src.avail.to_numpy()
    for name, arr in [("atr_tf", s_atr), ("vr15", vr), ("skew120", skew), ("rv30", rv), ("v15", v15),
                      ("rng15", rng15), ("tr60", tr60), ("pos4", pos4)]:
        f[name] = map_asof(dec, av, arr, max_age_s=tf * 60 * 3)
    f["atr70"] = atr(b.high.to_numpy(), b.low.to_numpy(), c, 70)
    # ---- saat/oturum alanları ----
    for k in ["ny_min", "tday", "ny_date", "wd", "utc_h", "utc_min", "period"]:
        f[k] = b[k].to_numpy()
    nym = b.ny_min.to_numpy()
    # dakika-başına normalizasyon (aynı NY dakikası, önceki 20 işlem günü medyanı; bugün hariç)
    for col in ["rv30", "v15", "rng15"]:
        piv = pd.DataFrame({"d": f.tday, "m": nym, "x": f[col]}).pivot_table(index="d", columns="m", values="x", aggfunc="last")
        med = piv.shift(1).rolling(20, min_periods=10).median()
        st = med.stack()
        st.index.names = ["d", "m"]
        key = pd.MultiIndex.from_arrays([f.tday, nym], names=["d", "m"])
        f[col + "_rel"] = f[col].to_numpy() / st.reindex(key).to_numpy()
    # ---- RTH seviyeleri (NY takvim günü) ----
    ny_date = f.ny_date.to_numpy()
    rth = (nym >= 571) & (nym <= 960)          # karar 09:31..16:00 → bar 09:30..15:59
    day = pd.DataFrame({"d": ny_date, "h": b.high.to_numpy(), "l": b.low.to_numpy(), "c": c, "o": b.open.to_numpy(),
                        "rth": rth, "m": nym})
    r = day[day.rth]
    rth_day = r.groupby("d").agg(H=("h", "max"), L=("l", "min"), C=("c", "last"), n=("c", "size"))
    rth_day = rth_day[rth_day.n > 300]
    prev = rth_day.shift(1)
    # önceki RTH gününün değerleri: takvim gününe göre bir önceki tam RTH günü
    dates = rth_day.index.to_numpy()
    k = np.searchsorted(dates, ny_date, side="left") - 1
    valid = k >= 0
    for col, name in [("H", "pdh"), ("L", "pdl"), ("C", "pdc")]:
        v = rth_day[col].to_numpy()
        f[name] = np.where(valid, v[np.maximum(k, 0)], np.nan)
    # önceki günün RTH getirisi
    pr = (rth_day.C / prev.C - 1).to_numpy()
    f["prev_day_ret"] = np.where(valid, pr[np.maximum(k, 0)], np.nan)
    # bugünün 09:30 açılışı (09:31 kararından itibaren bilinir)
    op = day[day.m == 571].groupby("d").o.first()
    f["rth_open"] = pd.Series(ny_date).map(op).to_numpy()
    f.loc[nym < 571, "rth_open"] = np.nan
    # 10:00 fiyatı (10:00 kararı = 09:59 barının kapanışı)
    p10 = day[day.m == 600].groupby("d").c.last()
    f["p1000"] = pd.Series(ny_date).map(p10).to_numpy()
    f.loc[nym < 600, "p1000"] = np.nan
    p04 = day[day.m == 240].groupby("d").c.last()
    f["p0400"] = pd.Series(ny_date).map(p04).to_numpy()
    f.loc[nym < 240, "p0400"] = np.nan
    f["ret_prevclose"] = c / f.pdc - 1
    f["gap"] = f.rth_open / f.pdc - 1
    # ---- işlem-günü (18:00 ET) aralığı ve ADR20 ----
    td = pd.DataFrame({"d": f.tday, "h": b.high.to_numpy(), "l": b.low.to_numpy()})
    f["day_hi"] = td.groupby("d").h.cummax().to_numpy()
    f["day_lo"] = td.groupby("d").l.cummin().to_numpy()
    dr = td.groupby("d").agg(H=("h", "max"), L=("l", "min"), n=("h", "size"))
    dr = dr[dr.n > 600]
    adr = (dr.H - dr.L).rolling(20, min_periods=10).mean().shift(1)
    f["adr20"] = f.tday.map(adr).to_numpy()
    f["day_pos"] = (c - f.day_lo) / (f.day_hi - f.day_lo).replace(0, np.nan)
    f["range_used"] = (f.day_hi - f.day_lo) / f.adr20
    # ---- RTH VWAP (tick hacmi ağırlıklı) + σ ----
    tp_ = (b.high + b.low + b.close).to_numpy() / 3
    v = b.volume.to_numpy(float) * rth
    g = pd.Series(ny_date)
    cv = pd.Series(v).groupby(g).cumsum().to_numpy()
    cpv = pd.Series(v * tp_).groupby(g).cumsum().to_numpy()
    cpv2 = pd.Series(v * tp_ * tp_).groupby(g).cumsum().to_numpy()
    with np.errstate(invalid="ignore", divide="ignore"):
        vw = cpv / cv
        sd = np.sqrt(np.maximum(cpv2 / cv - vw * vw, 0))
    f["vwap"] = np.where(rth & (cv > 0), vw, np.nan)
    f["vwap_sd"] = np.where(rth & (cv > 0), sd, np.nan)
    # ---- mevcut kapılar (bot) ----
    h1 = _last_complete(b[["ts", "t", "open", "high", "low", "close", "volume"]], 60)
    h1["ema50"] = h1.close.ewm(span=50, adjust=False, min_periods=50).mean()
    f["h1_trend"] = np.sign(map_asof(dec, h1.avail.to_numpy(), (h1.close - h1.ema50).to_numpy(), 3 * 3600))
    return f
