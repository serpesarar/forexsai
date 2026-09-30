"""Çıkış kuralı simülatörü (1m, sızıntısız, muhafazakâr).

R birimi: 1R = girişteki SL mesafesi. Bar içi sıra bilinmediği için:
  * aynı barda hem hedef hem stop → STOP (kötü senaryo)
  * stop taşıma (BE/trail) ancak tetikleyen barın BİR SONRAKİ barından itibaren geçerli
  * giriş dakikası barı atlanır (dakika içi giriş anı bilinmez)
Tüm kurallar pozisyon başına tek sonuç (R) döndürür; maliyet ayrıca düşülür.
"""
from __future__ import annotations
import numpy as np


def simulate(p: dict, tp_r: float, *, sl_r: float = 1.0,
             be_trig: float | None = None, be_lock: float = 0.0,
             trail_trig: float | None = None, trail_dist: float | None = None,
             partial_at: float | None = None, partial_frac: float = 0.5,
             time_stop: int | None = None, time_stop_min_r: float | None = None,
             max_bars: int | None = None, start: int = 1) -> tuple[float, int, str]:
    """Tek işlem simülasyonu → (R, çıkış_bar_idx, sebep)."""
    fav, adv, cls = p["fav"], p["adv"], p["cls"]
    n = len(fav) if max_bars is None else min(len(fav), max_bars)
    stop = -sl_r
    realized = 0.0          # kısmi kapanıştan gelen R
    size = 1.0
    peak = -1e9
    pend_stop = None        # bir sonraki bardan geçerli olacak stop
    partial_done = False
    for i in range(start, n):
        if pend_stop is not None:
            stop = max(stop, pend_stop); pend_stop = None
        f, a = fav[i], adv[i]
        # 1) stop önce (muhafazakâr)
        if a <= stop:
            return realized + size * stop, i, ("sl" if stop <= -sl_r + 1e-9 else "stop_moved")
        # 2) kısmi kâr
        if partial_at is not None and not partial_done and f >= partial_at:
            realized += partial_frac * partial_at; size -= partial_frac; partial_done = True
        # 3) hedef
        if tp_r is not None and f >= tp_r:
            return realized + size * tp_r, i, "tp"
        peak = max(peak, f)
        # 4) stop taşıma (sonraki bardan geçerli)
        new = None
        if be_trig is not None and peak >= be_trig:
            new = be_lock
        if trail_trig is not None and peak >= trail_trig:
            t = peak - trail_dist
            new = t if new is None else max(new, t)
        if new is not None and new > stop:
            pend_stop = new
        # 5) zaman stopu
        if time_stop is not None and i >= time_stop:
            if time_stop_min_r is None or peak < time_stop_min_r:
                return realized + size * cls[i], i, "time"
    return realized + size * cls[n - 1], n - 1, "open_end"


def path_stats(p: dict, tp_r: float, sl_r: float = 1.0, start: int = 1) -> dict:
    """Baseline çıkışa kadar MFE/MAE ve sıralama."""
    fav, adv = p["fav"], p["adv"]
    R, idx, why = simulate(p, tp_r, sl_r=sl_r, start=start)
    f = fav[start: idx + 1]; a = adv[start: idx + 1]
    mfe = float(np.max(f)) if len(f) else 0.0
    mae = float(np.min(a)) if len(a) else 0.0
    i_mfe = int(np.argmax(f)) + start if len(f) else start
    i_mae = int(np.argmin(a)) + start if len(a) else start
    # MFE'den önceki en kötü nokta
    a_pre = adv[start: i_mfe + 1]
    mae_before_mfe = float(np.min(a_pre)) if len(a_pre) else 0.0
    return dict(simR=R, sim_idx=idx, sim_exit=why, mfe=mfe, mae=mae, i_mfe=i_mfe,
                i_mae=i_mae, mae_before_mfe=mae_before_mfe)
