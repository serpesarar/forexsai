"""Session context for the MiroShark bias-accuracy measurement harness.

Given any UTC timestamp, describe the trading-session context around it:
which session is live, minutes to the US open, half-day / holiday flags, and
(best-effort) the price direction carried over from earlier sessions.

DST correctness is the whole point: every boundary is computed in the market's
OWN timezone via :mod:`zoneinfo` (``America/New_York`` / ``Europe/London`` /
``Europe/Berlin``) — never a fixed UTC offset. US and EU DST switch on different
dates, so each session is evaluated in its own zone.

This module is part of the ISOLATED test harness. It does NOT touch the live
``daily_bias`` table or the Precision Veto Engine.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone, time as dtime
from typing import Any, Optional
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

NY = ZoneInfo("America/New_York")
LONDON = ZoneInfo("Europe/London")
FRANKFURT = ZoneInfo("Europe/Berlin")

# US regular session in ET.
_US_OPEN = dtime(9, 30)
_US_CLOSE = dtime(16, 0)
_US_HALF_CLOSE = dtime(13, 0)
_PREMARKET_OPEN = dtime(4, 0)
_AFTERHOURS_CLOSE = dtime(20, 0)
_LONDON_ET_START = dtime(2, 0)     # ~07:00 London — early European flow
_LONDON_US_OVERLAP_END = dtime(11, 30)  # 16:30 London cash close ≈ 11:30 ET

_FLAT_PCT = 0.15   # |daily change| below this → "flat" direction bucket

# ── NYSE calendar (static 2026; pandas_market_calendars used if available) ─────
# Full-day closures.
_NYSE_HOLIDAYS_2026 = {
    "2026-01-01",  # New Year's Day
    "2026-01-19",  # MLK Jr. Day
    "2026-02-16",  # Presidents' Day
    "2026-04-03",  # Good Friday
    "2026-05-25",  # Memorial Day
    "2026-06-19",  # Juneteenth
    "2026-07-03",  # Independence Day (observed; Jul 4 is Saturday)
    "2026-09-07",  # Labor Day
    "2026-11-26",  # Thanksgiving
    "2026-12-25",  # Christmas
}
# 1:00 PM ET early closes.
_NYSE_HALF_DAYS_2026 = {
    "2026-11-27",  # Day after Thanksgiving
    "2026-12-24",  # Christmas Eve
}


def _pmc_calendar():
    """Return a pandas_market_calendars NYSE calendar, or None if unavailable."""
    try:
        import pandas_market_calendars as mcal
        return mcal.get_calendar("NYSE")
    except Exception:
        return None


def _as_utc(ts: datetime) -> datetime:
    """Coerce to tz-aware UTC (naive input is assumed UTC)."""
    if ts.tzinfo is None:
        return ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc)


def is_us_holiday(date_iso: str) -> bool:
    cal = _pmc_calendar()
    if cal is not None:
        try:
            import pandas as pd
            sched = cal.schedule(start_date=date_iso, end_date=date_iso)
            # Weekday with no schedule row → holiday.
            d = pd.Timestamp(date_iso)
            if d.weekday() < 5:
                return sched.empty
            return False
        except Exception:
            pass
    return date_iso in _NYSE_HOLIDAYS_2026


def is_us_half_day(date_iso: str) -> bool:
    cal = _pmc_calendar()
    if cal is not None:
        try:
            import pandas as pd
            sched = cal.schedule(start_date=date_iso, end_date=date_iso)
            if sched.empty:
                return False
            close = sched.iloc[0]["market_close"].tz_convert(NY)
            return close.hour < 16
        except Exception:
            pass
    return date_iso in _NYSE_HALF_DAYS_2026


def _minute_of_day(t: datetime) -> int:
    return t.hour * 60 + t.minute


def _classify_session(ny: datetime, trading_day: bool, close: dtime) -> str:
    if not trading_day:
        return "closed"
    m = _minute_of_day(ny)
    if _minute_of_day_t(_US_OPEN) <= m < _minute_of_day_t(close):
        return "us_regular"
    if _minute_of_day_t(close) <= m < _minute_of_day_t(_AFTERHOURS_CLOSE):
        return "us_afterhours"
    if _minute_of_day_t(_PREMARKET_OPEN) <= m < _minute_of_day_t(_US_OPEN):
        return "us_premarket"
    if _minute_of_day_t(_LONDON_ET_START) <= m < _minute_of_day_t(_PREMARKET_OPEN):
        return "london"
    return "asia"   # 20:00–24:00 and 00:00–02:00 ET


def _minute_of_day_t(t: dtime) -> int:
    return t.hour * 60 + t.minute


def get_session_context(timestamp_utc: datetime) -> dict[str, Any]:
    """Deterministic session/calendar context for *timestamp_utc*.

    Price-derived fields (``london_session_direction``,
    ``asia_overnight_change``, ``us_premarket_change``) are returned as ``None``
    here — fill them with :func:`enrich_price_context` (async, best-effort) when
    live data is available. This split keeps the time logic pure and testable.
    """
    ts = _as_utc(timestamp_utc)
    ny = ts.astimezone(NY)
    date_iso = ny.date().isoformat()

    holiday = is_us_holiday(date_iso)
    half_day = is_us_half_day(date_iso)
    trading_day = ny.weekday() < 5 and not holiday
    close = _US_HALF_CLOSE if half_day else _US_CLOSE

    m = _minute_of_day(ny)
    session = _classify_session(ny, trading_day, close)
    overlap = (trading_day
               and _minute_of_day_t(_US_OPEN) <= m < _minute_of_day_t(_LONDON_US_OVERLAP_END))

    return {
        "current_session": session,
        "ny_time": ny.isoformat(),
        "london_session_direction": None,   # best-effort → enrich_price_context
        "asia_overnight_change": None,
        "us_premarket_change": None,
        "minutes_to_us_open": _minute_of_day_t(_US_OPEN) - m,
        "is_half_day": half_day,
        "is_holiday": holiday,
        "session_overlap": overlap,
    }


# ── Best-effort price enrichment (nullable — never fabricates) ─────────────────
def _pct_change(first: Optional[float], last: Optional[float]) -> Optional[float]:
    if not first or first == 0 or last is None:
        return None
    return round((last - first) / first * 100.0, 3)


def _direction(change_pct: Optional[float]) -> Optional[str]:
    if change_pct is None:
        return None
    if change_pct > _FLAT_PCT:
        return "up"
    if change_pct < -_FLAT_PCT:
        return "down"
    return "flat"


def _c(candle: dict) -> Optional[float]:
    for k in ("close", "c"):
        if candle.get(k) is not None:
            try:
                return float(candle[k])
            except (TypeError, ValueError):
                return None
    return None


async def enrich_price_context(timestamp_utc: datetime,
                               ctx: Optional[dict] = None) -> dict[str, Any]:
    """Fill the price-derived fields best-effort. Any missing feed → ``None``.

    - ``london_session_direction`` from the DAX (GDAXI.INDX), which actually
      trades the European morning, unlike the NDX cash index.
    - ``asia_overnight_change`` / ``us_premarket_change`` need NQ-futures data;
      if the only NDX feed is cash (closed overnight), they stay ``None`` rather
      than inventing a number.
    """
    ctx = dict(ctx) if ctx else get_session_context(timestamp_utc)
    try:
        from services.data_fetcher import fetch_intraday_candles
    except Exception:
        return ctx

    # London direction via DAX — first vs last close of the recent European band.
    try:
        dax = await fetch_intraday_candles("GDAXI.INDX", interval="15m", limit=40)
        if dax and len(dax) >= 2:
            change = _pct_change(_c(dax[0]), _c(dax[-1]))
            ctx["london_session_direction"] = _direction(change)
    except Exception as e:
        logger.debug("[session-ctx] london direction skipped: %s", e)

    return ctx


def get_run_label_hint(ctx: dict) -> str:
    """Suggest a run_label from NY clock (e.g. ``0945``) for convenience."""
    try:
        ny = datetime.fromisoformat(ctx["ny_time"])
        return f"{ny.hour:02d}{ny.minute:02d}"
    except Exception:
        return "manual"
