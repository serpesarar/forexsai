"""Sızıntısız bar çekimi — 'şu ana kadar KAPANMIŞ son n bar'.

⚠️ TUZAK: mt5.copy_rates_from(sym, tf, date_from, n) verilen tarihten İLERİYE
doğru n bar döndürür (geriye değil). Geçmiş bir karar anını yeniden kurarken
kullanılırsa GELECEĞE BAKAR. 2026-08-11'de entry_gate doğrulaması ilk turda
tam bu yüzden geçersizdi. Doğrusu copy_rates_range ile pencere çekip karar
anından SONRAKİ barları atmaktır — bu modül onu yapar.
"""
from __future__ import annotations

import calendar
from datetime import datetime, timedelta

import MetaTrader5 as mt5

TF_MIN = {mt5.TIMEFRAME_M1: 1, mt5.TIMEFRAME_M5: 5, mt5.TIMEFRAME_M15: 15,
          mt5.TIMEFRAME_M30: 30, mt5.TIMEFRAME_H1: 60, mt5.TIMEFRAME_H4: 240}


def rates_upto(symbol: str, tf: int, when: datetime, n: int, gap_factor: float = 3.0):
    """Karar anı `when`'de (sunucu saati) KAPANMIŞ son n barı döndür.

    Bar `t` ancak `t + periyot <= when` ise kapanmıştır — koşan bar dahil edilmez.
    """
    per = TF_MIN[tf]
    span = timedelta(minutes=per * n * gap_factor + 4 * 24 * 60)   # hafta sonu payı
    r = mt5.copy_rates_range(symbol, tf, when - span, when + timedelta(minutes=per))
    if r is None or len(r) == 0:
        return None
    # naive `when` = SUNUCU saati (mt5 bar time'larıyla aynı eksen) → timegm
    cutoff = calendar.timegm(when.timetuple()) - per * 60
    r = r[r["time"] <= cutoff]                       # sızıntı kesimi
    return r[-n:] if len(r) >= 30 else None


def candles_upto(symbol: str, tf: int, when: datetime, n: int):
    """entry_gate/bot formatında ({high,low,close,volume}) kapalı mumlar."""
    r = rates_upto(symbol, tf, when, n)
    if r is None:
        return None
    return [{"high": float(x["high"]), "low": float(x["low"]),
             "close": float(x["close"]), "volume": float(x["tick_volume"])} for x in r]
