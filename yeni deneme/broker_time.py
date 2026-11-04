"""MT5 sunucu saati → gerçek UTC kuralı.

Pepperstone sunucu saati = New York + 7 saat: ABD yaz saatinde UTC+3, kışın UTC+2.
Kanıt (2026-11-04, kutu, NAS100 M5): 09:30 ET açılışının en yüksek hacimli barı
2026'nın her haftasında sunucu saatiyle 16:30; 8-29 Mart'ta da (ABD geçti, AB
geçmedi) kaymıyor. MT5 geçmiş barları kendi döneminin sunucu saatinde tutar, bu
yüzden derin geçmiş tek bir ölçülen offset'le çevrilemez.

Geçiş Pazar günü olur ve piyasa o anda kapalıdır; sınır sunucu saatiyle Pazar 00:00.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

SUMMER_OFFSET_SEC = 3 * 3600
WINTER_OFFSET_SEC = 2 * 3600
_SUNDAY = 6
_DST_START_MONTH, _DST_START_NTH_SUNDAY = 3, 2
_DST_END_MONTH, _DST_END_NTH_SUNDAY = 11, 1


def _nth_sunday(year: int, month: int, nth: int) -> datetime:
    first = datetime(year, month, 1, tzinfo=timezone.utc)
    days_to_sunday = (_SUNDAY - first.weekday()) % 7
    return first + timedelta(days=days_to_sunday + 7 * (nth - 1))


def rule_offset_sec(server_epoch: int) -> int:
    """Sunucu saati epoch'unun döneminde geçerli sunucu−UTC farkı (saniye)."""
    wall = datetime.fromtimestamp(server_epoch, tz=timezone.utc)
    start = _nth_sunday(wall.year, _DST_START_MONTH, _DST_START_NTH_SUNDAY)
    end = _nth_sunday(wall.year, _DST_END_MONTH, _DST_END_NTH_SUNDAY)
    return SUMMER_OFFSET_SEC if start <= wall < end else WINTER_OFFSET_SEC


def rule_matches_measured(measured_offset_sec: int, now_utc_epoch: float) -> bool:
    """Canlı ölçüm kurala uyuyor mu? Uymuyorsa broker kuralı değişmiş demektir."""
    return rule_offset_sec(int(now_utc_epoch + measured_offset_sec)) == measured_offset_sec
