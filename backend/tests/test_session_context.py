"""Deterministic session-context tests — the DST/calendar core must be exact."""
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from services import session_context_service as sc  # noqa: E402


def _utc(y, mo, d, h, mi=0):
    return datetime(y, mo, d, h, mi, tzinfo=timezone.utc)


# ── DST correctness: NY 09:30 maps to different UTC in summer vs winter ────────
def test_summer_edt_open():
    # 2026-07-06 Mon, 13:30 UTC = 09:30 EDT (UTC-4)
    ctx = sc.get_session_context(_utc(2026, 7, 6, 13, 30))
    assert ctx["current_session"] == "us_regular"
    assert ctx["minutes_to_us_open"] == 0
    assert ctx["session_overlap"] is True
    assert ctx["ny_time"].startswith("2026-07-06T09:30")


def test_winter_est_open():
    # 2026-01-05 Mon, 14:30 UTC = 09:30 EST (UTC-5) — one hour later in UTC
    ctx = sc.get_session_context(_utc(2026, 1, 5, 14, 30))
    assert ctx["current_session"] == "us_regular"
    assert ctx["minutes_to_us_open"] == 0
    assert ctx["ny_time"].startswith("2026-01-05T09:30")


def test_dst_offsets_differ():
    summer = sc.get_session_context(_utc(2026, 7, 6, 13, 30))["ny_time"]
    winter = sc.get_session_context(_utc(2026, 1, 5, 14, 30))["ny_time"]
    assert summer.endswith("-04:00")   # EDT
    assert winter.endswith("-05:00")   # EST


# ── Sessions across the ET clock (winter) ─────────────────────────────────────
def test_premarket():
    ctx = sc.get_session_context(_utc(2026, 1, 5, 12, 0))   # 07:00 EST
    assert ctx["current_session"] == "us_premarket"
    assert ctx["minutes_to_us_open"] == 150


def test_london_band():
    ctx = sc.get_session_context(_utc(2026, 1, 5, 8, 0))    # 03:00 EST
    assert ctx["current_session"] == "london"


def test_asia_band():
    ctx = sc.get_session_context(_utc(2026, 1, 6, 2, 0))    # Mon 21:00 EST
    assert ctx["current_session"] == "asia"
    assert ctx["minutes_to_us_open"] < 0


def test_afterhours():
    ctx = sc.get_session_context(_utc(2026, 1, 5, 22, 0))   # 17:00 EST
    assert ctx["current_session"] == "us_afterhours"


# ── Overlap boundary (09:30–11:30 ET) ─────────────────────────────────────────
def test_overlap_excludes_1130():
    ctx = sc.get_session_context(_utc(2026, 1, 5, 16, 30))  # 11:30 EST
    assert ctx["session_overlap"] is False
    assert ctx["current_session"] == "us_regular"


# ── Holiday / half-day / weekend ──────────────────────────────────────────────
def test_holiday_independence_day_observed():
    # 2026-07-03 is the observed Independence Day (Jul 4 is Saturday).
    ctx = sc.get_session_context(_utc(2026, 7, 3, 15, 0))
    assert ctx["is_holiday"] is True
    assert ctx["current_session"] == "closed"


def test_half_day_after_early_close_is_afterhours():
    # 2026-11-27 (day after Thanksgiving) closes 13:00 ET. 18:30 UTC = 13:30 EST.
    ctx = sc.get_session_context(_utc(2026, 11, 27, 18, 30))
    assert ctx["is_half_day"] is True
    assert ctx["current_session"] == "us_afterhours"


def test_half_day_before_close_is_regular():
    ctx = sc.get_session_context(_utc(2026, 11, 27, 17, 0))  # 12:00 EST
    assert ctx["is_half_day"] is True
    assert ctx["current_session"] == "us_regular"


def test_weekend_closed():
    ctx = sc.get_session_context(_utc(2026, 7, 4, 14, 0))    # Saturday
    assert ctx["current_session"] == "closed"


# ── Naive timestamp treated as UTC ────────────────────────────────────────────
def test_naive_timestamp_assumed_utc():
    naive = datetime(2026, 7, 6, 13, 30)
    ctx = sc.get_session_context(naive)
    assert ctx["current_session"] == "us_regular"


# ── Price enrichment stays nullable when no feed ──────────────────────────────
@pytest.mark.asyncio
async def test_enrich_nullable_without_data(monkeypatch):
    import services.data_fetcher as df

    async def empty(*a, **k):
        return []
    monkeypatch.setattr(df, "fetch_intraday_candles", empty)
    ctx = await sc.enrich_price_context(_utc(2026, 7, 6, 13, 30))
    assert ctx["london_session_direction"] is None
    assert ctx["asia_overnight_change"] is None


@pytest.mark.asyncio
async def test_enrich_london_direction_up(monkeypatch):
    import services.data_fetcher as df

    async def rising(symbol, interval="15m", limit=40):
        return [{"close": 20000}, {"close": 20050}, {"close": 20200}]
    monkeypatch.setattr(df, "fetch_intraday_candles", rising)
    ctx = await sc.enrich_price_context(_utc(2026, 7, 6, 13, 30))
    assert ctx["london_session_direction"] == "up"
