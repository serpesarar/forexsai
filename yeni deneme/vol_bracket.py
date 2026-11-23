"""vol_bracket.py — DAYCOMBO / REENTRY için oynaklığa göre genişleyen braket + eşit $ risk (2026-11-23).

KURAL (research/ndx_sl_onleme_20261123, EK-4, defter SL-08):
    SL = max(110, k × ATR14(5m, kapanmış barlar))     k = DAYCOMBO_VOL_K (2,5)
    TP = SL × 80/110                                  (R oranı aynı)
    lot = taban lot × 110 / SL                        (işlem başı $ riski sabit)
Sakin piyasada (k×ATR5 ≤ 110) davranış BİREBİR eski 80/110 + taban lot.

KANIT (Duka 1m 2018–23 + 2024–26 broker, canlı ≈1 dk gecikme tabanı, 3.089 işlem):
    ort. R +0,061 vs taban +0,043; kart 6/6 (P %99,9, yarılar +0,043/+0,080, spread×1,5 +0,052);
    braket plasebosu (aynı genişlik dağılımı, rastgele atanmış) −31,6R medyan vs gerçek +39,4R, p=0,000;
    plato 2× / 2,5× / 3× hep artı. Zayıf yan: 2023 ve 2025 −1,5R (son 4 yılın her yılı artı DEĞİL).
    2026-11-23 canlı 10 işlemde 4 SL'nin 3'ü stopsuz kalırdı, 6 TP'nin 5'i korunurdu.

KAPATMA: config.DAYCOMBO_VOL_BRACKET = False → eski sabit 80/110 + taban lot.
"""
from __future__ import annotations

import math
from typing import Sequence

DEFAULT_SCOPES = ("NDX.INDX:BUY:DAYCOMBO", "NDX.INDX:BUY:REENTRY")
BASE_SL = 110.0
ATR_N = 14


def wilder_atr(highs: Sequence[float], lows: Sequence[float], closes: Sequence[float],
               n: int = ATR_N) -> float:
    """Wilder ATR (ewm alpha=1/n, adjust=False; ilk TR ile tohumlanır) — araştırma motoruyla aynı.

    İlk barın önceki kapanışı yoksa kendi açılışı yerine high−low kullanılır (araştırma: pc=open)."""
    if len(closes) < n + 1:
        return float("nan")
    a = 1.0 / n
    atr = None
    prev_c = None
    for h, l, c in zip(highs, lows, closes):
        tr = h - l if prev_c is None else max(h - l, abs(h - prev_c), abs(l - prev_c))
        atr = tr if atr is None else a * tr + (1 - a) * atr
        prev_c = c
    return float(atr)


def bracket(base_tp: float, base_sl: float, atr5: float, k: float) -> tuple[float, float]:
    """(tp, sl) puan. ATR geçersizse taban geometri."""
    if not (isinstance(atr5, (int, float)) and math.isfinite(atr5) and atr5 > 0):
        return base_tp, base_sl
    sl = max(base_sl, k * atr5)
    return sl * base_tp / base_sl, sl


def scaled_lot(base_lot: float, base_sl: float, sl: float, step: float, vmin: float) -> float:
    """Eşit $ risk lotu: aşağı yuvarlanır (risk tabanı aşmaz), en az vmin."""
    if sl <= base_sl or base_lot <= 0:
        return base_lot
    raw = base_lot * base_sl / sl
    if step and step > 0:
        raw = math.floor(raw / step + 1e-9) * step
    return round(max(vmin, raw), 2)


def applies(scope_key: str, cfg) -> bool:
    if not bool(getattr(cfg, "DAYCOMBO_VOL_BRACKET", True)):
        return False
    return scope_key in tuple(getattr(cfg, "DAYCOMBO_VOL_SCOPES", DEFAULT_SCOPES))


def adjust(mt5, mt5_symbol: str, scope_key: str, tp_dist: float, sl_dist: float,
           base_lot: float, cfg, log=None) -> tuple[float, float, float, str]:
    """Bot kancası: (tp_dist, sl_dist, lot, açıklama). Kapsam dışı / hata → girdiler aynen (fail-open)."""
    if not applies(scope_key, cfg):
        return tp_dist, sl_dist, base_lot, ""
    try:
        r = mt5.copy_rates_from_pos(mt5_symbol, mt5.TIMEFRAME_M5, 1, 300)
        if r is None or len(r) < ATR_N + 1:
            return tp_dist, sl_dist, base_lot, "vol_bracket: 5m veri yok"
        atr5 = wilder_atr([float(x["high"]) for x in r], [float(x["low"]) for x in r],
                          [float(x["close"]) for x in r])
        k = float(getattr(cfg, "DAYCOMBO_VOL_K", 2.5))
        tp2, sl2 = bracket(tp_dist, sl_dist, atr5, k)
        if sl2 <= sl_dist:
            return tp_dist, sl_dist, base_lot, f"vol_bracket: sakin (ATR5 {atr5:.1f}, {k}×={k * atr5:.0f} ≤ {sl_dist:.0f})"
        info = mt5.symbol_info(mt5_symbol)
        step = float(getattr(info, "volume_step", 0.01) or 0.01)
        vmin = float(getattr(info, "volume_min", 0.01) or 0.01)
        lot = scaled_lot(base_lot, sl_dist, sl2, step, vmin)
        return tp2, sl2, lot, (f"vol_bracket: ATR5 {atr5:.1f} → SL {sl2:.0f} TP {tp2:.0f} "
                               f"lot {base_lot}→{lot}")
    except Exception as exc:  # fail-open: eski geometri
        if log:
            log.warning("vol_bracket hata (eski geometri): %s", exc)
        return tp_dist, sl_dist, base_lot, ""
