"""NOM — statik NYSE tatil + yarım gün takvimi (2018-2026).

`pandas_market_calendars` ortamda yok; tarihler NYSE resmi takviminden elle girildi
(milli yas günleri dahil: 2018-12-05 Bush, 2025-01-09 Carter). Yarım günlerde nakit kapanış 13:00 ET.
Kapsam dışı yıl → `in_coverage()` False; çağıran taraf bunu raporlamalı (uydurma tarih yok).
"""
from __future__ import annotations

from datetime import date

COVER_YEARS = range(2018, 2027)

_H = """2018-01-01 2018-01-15 2018-02-19 2018-03-30 2018-05-28 2018-07-04 2018-09-03 2018-11-22 2018-12-05 2018-12-25
2019-01-01 2019-01-21 2019-02-18 2019-04-19 2019-05-27 2019-07-04 2019-09-02 2019-11-28 2019-12-25
2020-01-01 2020-01-20 2020-02-17 2020-04-10 2020-05-25 2020-07-03 2020-09-07 2020-11-26 2020-12-25
2021-01-01 2021-01-18 2021-02-15 2021-04-02 2021-05-31 2021-07-05 2021-09-06 2021-11-25 2021-12-24
2022-01-17 2022-02-21 2022-04-15 2022-05-30 2022-06-20 2022-07-04 2022-09-05 2022-11-24 2022-12-26
2023-01-02 2023-01-16 2023-02-20 2023-04-07 2023-05-29 2023-06-19 2023-07-04 2023-09-04 2023-11-23 2023-12-25
2024-01-01 2024-01-15 2024-02-19 2024-03-29 2024-05-27 2024-06-19 2024-07-04 2024-09-02 2024-11-28 2024-12-25
2025-01-01 2025-01-09 2025-01-20 2025-02-17 2025-04-18 2025-05-26 2025-06-19 2025-07-04 2025-09-01 2025-11-27 2025-12-25
2026-01-01 2026-01-19 2026-02-16 2026-04-03 2026-05-25 2026-06-19 2026-07-03 2026-09-07 2026-11-26 2026-12-25"""
_E = """2018-07-03 2018-11-23 2018-12-24 2019-07-03 2019-11-29 2019-12-24 2020-11-27 2020-12-24 2021-11-26
2022-11-25 2023-07-03 2023-11-24 2024-07-03 2024-11-29 2024-12-24 2025-07-03 2025-11-28 2025-12-24
2026-11-27 2026-12-24"""

HOLIDAYS: frozenset[date] = frozenset(date.fromisoformat(x) for x in _H.split())
EARLY_CLOSE: frozenset[date] = frozenset(date.fromisoformat(x) for x in _E.split())


def in_coverage(d: date) -> bool:
    return d.year in COVER_YEARS


def is_holiday(d: date) -> bool:
    return d in HOLIDAYS


def is_early_close(d: date) -> bool:
    return d in EARLY_CLOSE


def cash_close_minutes(d: date) -> int:
    """NY nakit kapanışı (gece yarısından dakika): 16:00 → 960, yarım gün 13:00 → 780."""
    return 780 if d in EARLY_CLOSE else 960
