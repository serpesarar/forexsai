"""Haftalık açılış kapısı saf çekirdeği (MT5 gerekmez). cd 'yeni deneme' && python3 -m pytest -q test_weekly_open.py"""
import phase_rules as pr

FRI_CLOSE = 1_000_000_000          # keyfi broker zamanı (sn)
OPEN = FRI_CLOSE + 48 * 3600       # 48 s sonra açılış


def _bars(n_before=30, n_after=10):
    before = [FRI_CLOSE - 60 * (n_before - 1 - i) for i in range(n_before)]
    after = [OPEN + 60 * i for i in range(n_after)]
    return before + after


def test_minutes_since_open_found():
    m = pr.minutes_since_weekly_open(_bars(), OPEN + 9 * 60)
    assert abs(m - 9.0) < 1e-9
    assert pr.weekly_open_blocks(m, 60) is True


def test_after_window_not_blocked():
    m = pr.minutes_since_weekly_open(_bars(n_after=80), OPEN + 75 * 60)
    assert not pr.weekly_open_blocks(m, 60)


def test_daily_maintenance_gap_ignored():
    bars = [0, 60, 120, 120 + 3600, 120 + 3660]          # 1 s'lik günlük ara
    assert pr.minutes_since_weekly_open(bars, 120 + 3720) is None
    assert pr.weekly_open_blocks(None, 60) is False


def test_no_gap_in_window_is_none():
    assert pr.minutes_since_weekly_open([60 * i for i in range(100)], 6000) is None
