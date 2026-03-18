from __future__ import annotations

from datetime import datetime, time
from zoneinfo import ZoneInfo

NEW_YORK_TZ = ZoneInfo("America/New_York")
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
