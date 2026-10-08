"""İşlem başına özellikler — dört ZAMAN AİLESİ, karıştırılmaz:

  pre_* / geo_* / zaman  KARAR ANI: yalnız girişten önce kapanmış barlar. Filtre/kapı
                         adayı olabilecek TEK aile.
  e5_* / e15_*           ERKEN: girişten sonraki ilk 5/15 dk (o an izlenebilir) →
                         yalnız yönetim kuralı adayı; hayatta-kalma koşullu okunur.
  path_*                 TÜM YOL: giriş→çıkış. Teşhis ("neden oldu"), filtre DEĞİL.
  post_*                 ÇIKIŞ SONRASI: karşı-olgu ("yön doğru muydu"). Geleceğe bakar —
                         asla karar özelliği olarak kullanılmaz.

Fiyat birimi R = |giriş − ilk SL|. Mumlar BID; SELL bariyerleri ASK = BID + spread.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import settings as S
from .indicators import SymbolBars

NY_TZ = "America/New_York"


@dataclass
class Ctx:
    sb: SymbolBars
    s: int                 # +1 BUY, −1 SELL
    entry: float
    exit: float
    t0: pd.Timestamp
    t1: pd.Timestamp
    sl0: float
    tp0: float
    risk: float            # NaN → R hesaplanamaz
    reward: float
    spread: float
    i_pre: int             # girişten önce kapanmış son 1m bar
    i_in0: int             # giriş dakikasından SONRAKİ ilk bar
    i_exit: int            # çıkış dakikasının barı

    def r(self, price: np.ndarray | float) -> np.ndarray | float:
        return self.s * (np.asarray(price) - self.entry) / self.risk


def _nanmean(x: np.ndarray) -> float:
    x = x[np.isfinite(x)]
    return float(x.mean()) if x.size else np.nan


def _log2_ratio(a: float, b: float) -> float:
    return float(np.log2((a + 1.0) / (b + 1.0)))


MIN_SIDE_BARS = 3


def vol_dir(v: np.ndarray, signed_body: np.ndarray) -> float:
    """log2(lehte bar BAŞINA hacim / aleyhte bar BAŞINA hacim).

    Toplam hacim oranı KULLANILMAZ: kaybeden işlemde aleyhte bar SAYISI fazladır →
    toplam oran fiyat yönünü tekrar eder (tanım gereği ayrım). Bar başına ortalama
    "aleyhte hareket hacimli mi" sorusunu sayıdan bağımsız sorar.
    """
    up, dn = v[signed_body > 0], v[signed_body < 0]
    if up.size < MIN_SIDE_BARS or dn.size < MIN_SIDE_BARS:
        return np.nan
    return _log2_ratio(float(up.mean()), float(dn.mean()))


def make_ctx(row: pd.Series, sb: SymbolBars) -> Ctx | None:
    s = 1 if row["direction"] == "BUY" else -1
    e, sl0, tp0 = float(row["open_price"]), float(row["sl0"] or np.nan), float(row["tp0"] or np.nan)
    risk = abs(e - sl0) if np.isfinite(sl0) and s * (e - sl0) > 0 else np.nan
    reward = abs(tp0 - e) if np.isfinite(tp0) and s * (tp0 - e) > 0 else np.nan
    t0, t1 = row["entry_utc"], row["exit_utc"]
    i_pre = sb.last_closed(1, t0)
    if i_pre < S.RANGE_LOOKBACK:
        return None
    return Ctx(sb, s, e, float(row["close_price"]), t0, t1, sl0, tp0, risk, reward,
               S.TYPICAL_SPREAD.get(sb.symbol, 0.0), i_pre, sb.pos_at(t0) + 1, sb.pos_at(t1))


# ── KARAR ANI ────────────────────────────────────────────────────────────────

def _tf_val(c: Ctx, tf: int, col: str, back: int = 0) -> float:
    j = c.sb.last_closed(tf, c.t0) - back
    return float(c.sb.ta[tf][col][j]) if j >= 0 else np.nan


def pre_trend(c: Ctx) -> dict:
    a, i, s = c.sb.a, c.i_pre, c.s
    px, atr1 = a["close"][i], a["atr"][i]
    atr5, atr60 = _tf_val(c, 5, "atr"), _tf_val(c, 60, "atr")
    agree = int(s * (a["ema20"][i] - a["ema50"][i]) > 0)
    for tf in (5, 15, 60):
        agree += int(s * (_tf_val(c, tf, "ema20") - _tf_val(c, tf, "ema50")) > 0)
    rsi5 = _tf_val(c, 5, "rsi")
    pctb = _tf_val(c, 5, "bb_pctb")
    return {
        "pre_dist_ema20_1m": s * (px - a["ema20"][i]) / atr1,
        "pre_dist_ema50_5m": s * (px - _tf_val(c, 5, "ema50")) / atr5,
        "pre_dist_ema50_1h": s * (px - _tf_val(c, 60, "ema50")) / atr60,
        "pre_slope_ema50_1h": s * (_tf_val(c, 60, "ema50") - _tf_val(c, 60, "ema50", 3)) / atr60,
        "pre_trend_align_1h": float(s * (px - _tf_val(c, 60, "ema50")) > 0),
        "pre_mtf_agree": float(agree),
        "pre_rsi1": a["rsi"][i] if s > 0 else 100 - a["rsi"][i],
        "pre_rsi5": rsi5 if s > 0 else 100 - rsi5,
        "pre_adx5": _tf_val(c, 5, "adx"),
        "pre_di_align5": s * (_tf_val(c, 5, "plus_di") - _tf_val(c, 5, "minus_di")),
        "pre_bbpos5": pctb if s > 0 else 1 - pctb,
        "pre_atr_regime": atr5 / _tf_val(c, 5, "atr_med"),
        "pre_bbw_pct5": _tf_val(c, 5, "bbw_pct"),
        "_atr1": atr1, "_atr5": atr5, "_atr60": atr60,
    }


def pre_momentum(c: Ctx, atr1: float, atr5: float) -> dict:
    a, i, s = c.sb.a, c.i_pre, c.s
    cl, op, hi, lo = a["close"], a["open"], a["high"], a["low"]
    rng = slice(i - S.RANGE_LOOKBACK + 1, i + 1)
    H, L = hi[rng].max(), lo[rng].min()
    pos = (cl[i] - L) / (H - L) if H > L else 0.5
    st = slice(i - S.STRUCT_LOOKBACK + 1, i + 1)
    struct = lo[st].min() if s > 0 else hi[st].max()
    consec, k = 0, i
    sign0 = np.sign(s * (cl[i] - op[i]))
    while k > i - S.STRUCT_LOOKBACK and sign0 != 0 and np.sign(s * (cl[k] - op[k])) == sign0:
        consec += 1
        k -= 1
    bar_rng = np.maximum(hi[i - 2:i + 1] - lo[i - 2:i + 1], 1e-12)
    wick = (hi - np.maximum(op, cl)) if s > 0 else (np.minimum(op, cl) - lo)
    dh, dl, pdc = a["day_high"][i], a["day_low"][i], a["prev_day_close"][i]
    sl_margin = s * (struct - c.sl0) / atr1 if np.isfinite(c.sl0) else np.nan
    return {
        "pre_ret_5": s * (cl[i] - cl[i - 5]) / atr5,
        "pre_ret_15": s * (cl[i] - cl[i - 15]) / atr5,
        "pre_ret_60": s * (cl[i] - cl[i - 60]) / atr5,
        "pre_consec": float(consec * sign0),
        "pre_wick_against3": float(np.mean(wick[i - 2:i + 1] / bar_rng)),
        "pre_range_pos_4h": pos if s > 0 else 1 - pos,
        "pre_day_move_pct": s * (cl[i] / pdc - 1) * 100 if pdc > 0 else np.nan,
        "pre_day_range_pos": ((cl[i] - dl) / (dh - dl) if s > 0 else (dh - cl[i]) / (dh - dl)) if dh > dl else 0.5,
        "pre_room_struct_atr": s * (cl[i] - struct) / atr1,
        "pre_sl_beyond_struct": float(sl_margin > 0) if np.isfinite(sl_margin) else np.nan,
        "pre_sl_struct_margin": sl_margin,
        "_struct": struct,
    }


def pre_volume(c: Ctx) -> dict:
    a, i, s = c.sb.a, c.i_pre, c.s
    v, vs = a["volume"], a["vol_seas"]
    base = v[i - S.VOL_BASE_BARS - 4:i - 4].mean()
    y = v[i - 29:i + 1]
    slope = np.polyfit(np.arange(y.size), y, 1)[0] if y.size >= 10 and y.mean() > 0 else np.nan
    w = slice(i - 29, i + 1)
    up = s * (a["close"][w] - a["open"][w])
    return {
        "pre_vol_seas_5": _nanmean(vs[i - 4:i + 1]),
        "pre_vol_seas_15": _nanmean(vs[i - 14:i + 1]),
        "pre_vol_ratio_5_60": v[i - 4:i + 1].mean() / base if base > 0 else np.nan,
        "pre_vol_slope_30": slope * y.size / y.mean() if np.isfinite(slope) else np.nan,
        "pre_vol_dir_30": vol_dir(vs[w], up),
    }


def pre_divergence(c: Ctx) -> dict:
    """RSI ve hacim diverjansı: eski pencere A=[t−60,t−20), yeni B=[t−20,t]."""
    a, i, s = c.sb.a, c.i_pre, c.s
    A = slice(i - S.DIV_WINDOW_A[0] + 1, i - S.DIV_WINDOW_A[1] + 1)
    B = slice(i - S.DIV_WINDOW_A[1] + 1, i + 1)
    hi, lo, r, vs = a["high"], a["low"], a["rsi"], a["vol_seas"]
    new_hi, new_lo = hi[B].max() > hi[A].max(), lo[B].min() < lo[A].min()
    bear = new_hi and r[B].max() < r[A].max() - S.DIV_RSI_MARGIN
    bull = new_lo and r[B].min() > r[A].min() + S.DIV_RSI_MARGIN
    fading = _nanmean(vs[B]) < S.VOLDIV_FRAC * _nanmean(vs[A])
    against, support = (bear, bull) if s > 0 else (bull, bear)
    vol_against = (new_hi if s > 0 else new_lo) and fading   # lehte uç, sönen hacim
    vol_for = (new_lo if s > 0 else new_hi) and fading       # aleyhte uç, sönen hacim (tükenme)
    return {"pre_div_rsi_against": float(against), "pre_div_rsi_for": float(support),
            "pre_voldiv_against": float(vol_against), "pre_voldiv_for": float(vol_for)}


def geometry(c: Ctx, atr5: float, atr60: float) -> dict:
    a, i = c.sb.a, c.i_pre
    sigma = float(np.std(np.diff(a["close"][i - 60:i + 1])))
    ok = np.isfinite(c.risk) and np.isfinite(c.reward)
    return {
        "geo_sl_atr5": c.risk / atr5, "geo_tp_atr5": c.reward / atr5, "geo_sl_atr1h": c.risk / atr60,
        "geo_rr": c.reward / c.risk if ok else np.nan,
        "geo_be_wr": c.risk / (c.risk + c.reward) if ok else np.nan,
        "geo_sl_sigma": c.risk / sigma if sigma > 0 else np.nan,
        "geo_exp_tau_min": c.risk * c.reward / sigma ** 2 if ok and sigma > 0 else np.nan,
    }


def time_features(t0: pd.Timestamp) -> dict:
    ny = t0.tz_convert(NY_TZ)
    us_open = ny.normalize() + pd.Timedelta(hours=9, minutes=30)
    us_close = ny.normalize() + pd.Timedelta(hours=16)
    m_open = (ny - us_open).total_seconds() / 60
    if t0.hour >= 22 or t0.hour < 7:
        sess = "ASYA"
    elif ny < us_open:
        sess = "AVRUPA"
    elif m_open < 90:
        sess = "ABD_ACILIS"
    elif ny < us_close:
        sess = "ABD"
    else:
        sess = "ABD_KAPANIS_SONRASI"
    return {"hour_utc": float(t0.hour), "dow": float(t0.dayofweek), "session": sess,
            "min_from_us_open": m_open}


# ── ERKEN (ilk 5/15 dk) ──────────────────────────────────────────────────────

def early(c: Ctx, k: int) -> dict:
    a, s = c.sb.a, c.s
    last = c.i_in0 + k - 1
    open_at_k = last < c.i_exit
    j1 = min(last, c.i_exit - 1)
    p = f"e{k}_"
    if j1 < c.i_in0 or not np.isfinite(c.risk):
        return {p + "open": float(open_at_k)}
    w = slice(c.i_in0, j1 + 1)
    fav = c.r(a["high"][w] if s > 0 else a["low"][w])
    adv = c.r(a["low"][w] if s > 0 else a["high"][w])
    up = s * (a["close"][w] - a["open"][w])
    return {p + "open": float(open_at_k), p + "mfe_r": max(0.0, float(fav.max())),
            p + "mae_r": min(0.0, float(adv.min())),
            p + "close_r": float(c.r(a["close"][j1])) if open_at_k else np.nan,
            p + "vol_seas": _nanmean(a["vol_seas"][w]),
            p + "vol_dir": vol_dir(a["vol_seas"][w], up)}
