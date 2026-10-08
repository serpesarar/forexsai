"""Yol (giriş→çıkış) ve çıkış sonrası teşhis özellikleri + sonuç sınıfı.

Bunlar "NEDEN oldu" sorusunun cevabıdır; hiçbiri karar anında bilinemez → kapı
adayı DEĞİLDİR (yalnız ``e5_/e15_`` yönetim kuralı için izlenebilir).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import settings as S
from .features import NY_TZ, Ctx, _nanmean, vol_dir

REASON_SL, REASON_TP = 4, 5


def classify_outcome(reason: int, r_exit: float, net: float) -> str:
    """TP | SL (tam) | BE (taşınmış stop ~0) | IZ_SL (kârda iz stop) | KISMI_SL | DIGER_+/−."""
    if reason == REASON_TP:
        return "TP"
    if reason == REASON_SL:
        if not np.isfinite(r_exit):
            return "SL" if net < 0 else "IZ_SL"
        if r_exit <= S.FULL_SL_R:
            return "SL"
        if abs(r_exit) < S.BE_BAND_R:
            return "BE"
        return "IZ_SL" if r_exit > 0 else "KISMI_SL"
    return "DIGER_+" if net > 0 else "DIGER_−"


def _fav_adv(c: Ctx, w: slice) -> tuple[np.ndarray, np.ndarray]:
    a = c.sb.a
    if c.s > 0:
        return c.r(a["high"][w]), c.r(a["low"][w])
    return c.r(a["low"][w] + c.spread), c.r(a["high"][w] + c.spread)


def path_core(c: Ctx, r_exit: float) -> dict:
    """MFE/MAE, zamanlar, ilk gelen ±0,5R. Çıkış barı hariç (çıkış sonrası fiyat karışmasın)."""
    dur = (c.t1 - c.t0).total_seconds() / 60
    out = {"path_dur_min": dur}
    if not np.isfinite(c.risk):
        return out
    w = slice(c.i_in0, c.i_exit)
    fav, adv = _fav_adv(c, w)
    mfe = max(0.0, float(fav.max()) if fav.size else 0.0, r_exit)
    mae = min(0.0, float(adv.min()) if adv.size else 0.0, r_exit)
    i_mfe = c.i_in0 + int(fav.argmax()) if fav.size else c.i_in0
    i_mae = c.i_in0 + int(adv.argmin()) if adv.size else c.i_in0
    hit = np.flatnonzero((fav >= S.FIRST_HIT_R) | (adv <= -S.FIRST_HIT_R))
    first = "yok"
    if hit.size:
        k = hit[0]
        both = fav[k] >= S.FIRST_HIT_R and adv[k] <= -S.FIRST_HIT_R
        first = "belirsiz" if both else ("lehte" if fav[k] >= S.FIRST_HIT_R else "aleyhte")
    out.update({
        "path_mfe_r": mfe, "path_mae_r": mae,
        "path_t_mfe_min": float(i_mfe - c.i_in0 + 1), "path_t_mae_min": float(i_mae - c.i_in0 + 1),
        "path_mfe_frac_tp": mfe * c.risk / c.reward if np.isfinite(c.reward) else np.nan,
        "path_went_green": float(mfe >= S.WENT_GREEN_R), "path_first_hit": first,
        "_i_mfe": i_mfe, "_i_mae": i_mae,
    })
    return out


def path_volume(c: Ctx, i_mfe: int, i_mae: int, r_exit: float) -> dict:
    """Hacim dinamiği — mevsimsel düzeltilmiş (vol_seas = 1 → saatine göre normal)."""
    a, s = c.sb.a, c.s
    vs = a["vol_seas"]
    w = slice(c.i_in0, c.i_exit)
    n = c.i_exit - c.i_in0
    up = s * (a["close"][w] - a["open"][w])
    third = n // 3
    pre10 = slice(max(c.i_in0, c.i_exit - 10), c.i_exit)
    # Çıkışa götüren son bacak vs ilk bacak: kayıpta (MFE→çıkış)/(giriş→MFE), kazançta (MAE→çıkış)/(giriş→MAE)
    pivot = i_mfe if r_exit < 0 else i_mae
    leg1, leg2 = vs[c.i_in0:pivot + 1], vs[pivot + 1:c.i_exit]
    leg_ok = leg1.size >= 3 and leg2.size >= 3
    start5 = _nanmean(vs[c.i_in0:c.i_in0 + 5])
    return {
        "path_vol_seas": _nanmean(vs[w]) if n > 0 else np.nan,
        "path_vol_last_vs_first": (_nanmean(vs[c.i_exit - third:c.i_exit]) / _nanmean(vs[c.i_in0:c.i_in0 + third])
                                   if third >= 3 else np.nan),
        "path_vol_pre_exit10": _nanmean(vs[pre10]) if c.i_exit - pre10.start >= 3 else np.nan,
        "path_vol_exit_bar": float(vs[c.i_exit]) if c.i_exit < vs.size else np.nan,
        "path_vol_dir": vol_dir(vs[w], up) if n > 0 else np.nan,
        "path_final_leg_vol": _nanmean(leg2) / _nanmean(leg1) if leg_ok else np.nan,
        "path_mfe_vol_vs_start": (_nanmean(vs[max(c.i_in0, i_mfe - 2):i_mfe + 1]) / start5
                                  if n >= 8 and np.isfinite(start5) and start5 > 0 else np.nan),
    }


def _first_bar(mask: np.ndarray) -> float:
    k = np.flatnonzero(mask)
    return float(k[0] + 1) if k.size else np.nan


def path_events(c: Ctx, struct: float, atr1: float) -> dict:
    """Kırılma/uyumsuzluk olayları: yapı kırılımı, ters hacim şoku, 5m trend dönüşü."""
    a, s = c.sb.a, c.s
    w = slice(c.i_in0, c.i_exit)
    cl, op, vs = a["close"][w], a["open"][w], a["vol_seas"][w]
    t_break = _first_bar(s * (cl - struct) < 0)
    t_shock_adv = _first_bar((vs >= S.VOL_SHOCK_SEAS) & (s * (cl - op) < 0))
    t_shock_fav = _first_bar((vs >= S.VOL_SHOCK_SEAS) & (s * (cl - op) > 0))
    return {
        "path_struct_break": float(np.isfinite(t_break)), "path_t_struct_break": t_break,
        "path_vol_shock_adv": float(np.isfinite(t_shock_adv)), "path_t_vol_shock_adv": t_shock_adv,
        "path_vol_shock_fav": float(np.isfinite(t_shock_fav)),
        "path_t_flip5": _flip5(c),
        "path_overnight": float(_crosses(c.t0, c.t1, 17, 0)),
        "path_us_open_cross": float(_crosses(c.t0, c.t1, 9, 30)),
        "path_spike_stop": _spike_stop(c, atr1),
    }


def _flip5(c: Ctx) -> float:
    """Girişten sonra ilk KAPANMIŞ 5m bar: fiyat EMA20 altında(BUY) ve EMA20 eğimi ters → dk."""
    ta, s = c.sb.ta[5], c.s
    j0 = c.sb.last_closed(5, c.t0) + 1
    j1 = c.sb.last_closed(5, c.t1)
    for j in range(max(j0, 1), j1 + 1):
        if s * (ta["close"][j] - ta["ema20"][j]) < 0 and s * (ta["ema20"][j] - ta["ema20"][j - 1]) < 0:
            end = c.sb.tf[5].index[j] + pd.Timedelta(minutes=5)
            return (end - c.t0).total_seconds() / 60
    return np.nan


def _crosses(t0: pd.Timestamp, t1: pd.Timestamp, hour: int, minute: int) -> bool:
    """[t0, t1] New York saatiyle hh:mm'yi kesiyor mu (17:00 NY = günlük rollover)."""
    a, b = t0.tz_convert(NY_TZ), t1.tz_convert(NY_TZ)
    mark = a.normalize() + pd.Timedelta(hours=hour, minutes=minute)
    if mark < a:
        mark += pd.Timedelta(days=1)
    return bool(mark <= b)


def _spike_stop(c: Ctx, atr1: float) -> float:
    if not np.isfinite(c.sl0) or c.i_exit >= c.sb.a["close"].size:
        return np.nan
    a, i = c.sb.a, c.i_exit
    wide = (a["high"][i] - a["low"][i]) >= S.SPIKE_STOP_RANGE_ATR * atr1
    back = c.s * (a["close"][i] - c.sl0) > 0
    return float(wide and back)


def post_exit(c: Ctx, r_exit: float, now: pd.Timestamp, horizon: int) -> dict:
    """Çıkıştan sonraki ``horizon`` dk: TP'ye gitti mi, girişe döndü mü, ne kadar devam etti."""
    p = f"post{horizon}_"
    if not np.isfinite(c.risk):
        return {}
    j0 = c.i_exit + 1
    j1 = c.sb.pos_at(c.t1 + pd.Timedelta(minutes=horizon))
    out = {p + "complete": float((now - c.t1).total_seconds() / 60 >= horizon)}
    if j1 <= j0:
        return out
    fav, adv = _fav_adv(c, slice(j0, j1))
    rr = c.reward / c.risk if np.isfinite(c.reward) else np.nan
    hit_tp = np.flatnonzero(fav >= rr) if np.isfinite(rr) else np.array([], dtype=int)
    out.update({
        p + "max_fav_r": float(fav.max()), p + "max_adv_r": float(adv.min()),
        p + "hit_tp0": float(hit_tp.size > 0), p + "back_entry": float((fav >= 0).any()),
        p + "hit_sl0": float((adv <= -1.0).any()),
        p + "run_beyond_tp_r": float(fav.max() - rr) if np.isfinite(rr) else np.nan,
    })
    if hit_tp.size:
        _, adv_all = _fav_adv(c, slice(c.i_in0, j0 + int(hit_tp[0]) + 1))
        out[p + "needed_sl_r"] = float(adv_all.min())
    return out


def sl_verdict(outcome: str, r_exit: float, post: dict) -> str:
    """Kayıp çıkışlarda: YON_DOGRU (TP'ye sonradan gitti) | YON_YANLIS | KARARSIZ."""
    if outcome not in ("SL", "KISMI_SL", "BE", "DIGER_−") or "post240_max_adv_r" not in post:
        return ""
    if post.get("post240_hit_tp0") == 1.0:
        return "YON_DOGRU"
    if post["post240_max_adv_r"] <= r_exit - S.WRONG_DIR_EXTRA_R and post.get("post240_back_entry") != 1.0:
        return "YON_YANLIS"
    return "KARARSIZ"
