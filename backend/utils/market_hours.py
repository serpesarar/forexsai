from __future__ import annotations

from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo

NEW_YORK_TZ = ZoneInfo("America/New_York")
BERLIN_TZ = ZoneInfo("Europe/Berlin")
UTC_TZ = ZoneInfo("UTC")
MARKET_OPEN = time(9, 30)
MARKET_CLOSE = time(16, 0)


def get_new_york_now() -> datetime:
    return datetime.now(NEW_YORK_TZ)


def is_new_york_market_open(now: datetime | None = None) -> bool:
    current = now.astimezone(NEW_YORK_TZ) if now is not None else get_new_york_now()
    if current.weekday() >= 5:
        return False
    current_time = current.time().replace(tzinfo=None)
    return MARKET_OPEN <= current_time < MARKET_CLOSE


def get_new_york_market_hours_label() -> str:
    return "Mon-Fri 09:30-16:00 America/New_York"


def _coerce_datetime(now: datetime | None, tz: ZoneInfo) -> datetime:
    if now is None:
        return datetime.now(tz)
    if now.tzinfo is None:
        return now.replace(tzinfo=timezone.utc).astimezone(tz)
    return now.astimezone(tz)


def is_symbol_market_open(symbol: str, now: datetime | None = None) -> bool:
    normalized = (symbol or "").upper().strip()

    if normalized in {"NDX.INDX", "NDX", "NASDAQ"}:
        current = _coerce_datetime(now, NEW_YORK_TZ)
        if current.weekday() >= 5:
            return False
        current_time = current.time().replace(tzinfo=None)
        return MARKET_OPEN <= current_time < MARKET_CLOSE

    if normalized in {"GDAXI.INDX", "GDAXI", "DAX"}:
        current = _coerce_datetime(now, BERLIN_TZ)
        if current.weekday() >= 5:
            return False
        current_time = current.time().replace(tzinfo=None)
        return time(9, 0) <= current_time < time(17, 30)

    if normalized in {"XAUUSD", "XAUUSD.FOREX", "USOIL.FOREX", "USOIL", "CL", "CL.F", "CL.COMM"}:
        current = _coerce_datetime(now, UTC_TZ)
        weekday = current.weekday()
        current_time = current.time().replace(tzinfo=None)
        if weekday == 5:
            return False
        if weekday == 6:
            return current_time >= time(22, 0)
        if weekday == 4:
            return current_time < time(22, 0)
        return True

    current = _coerce_datetime(now, UTC_TZ)
    return current.weekday() < 5


def get_symbol_market_hours_label(symbol: str) -> str:
    normalized = (symbol or "").upper().strip()
    if normalized in {"NDX.INDX", "NDX", "NASDAQ"}:
        return get_new_york_market_hours_label()
    if normalized in {"GDAXI.INDX", "GDAXI", "DAX"}:
        return "Mon-Fri 09:00-17:30 Europe/Berlin"
    if normalized in {"XAUUSD", "XAUUSD.FOREX"}:
        return "Sun 22:00 - Fri 22:00 UTC"
    if normalized in {"USOIL.FOREX", "USOIL", "CL", "CL.F", "CL.COMM"}:
        return "Sun 22:00 - Fri 22:00 UTC"
    return "Mon-Fri trading hours"
