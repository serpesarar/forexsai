"""KSG canlı modülü birim testleri (MT5 gerekmez). Çalıştır: cd 'yeni deneme' && python3 test_ksg_live.py (pytest de olur).
Araştırma motoruyla sadakat: research/ndx_kapi_20261110/ksg_sadakat.py (1.039/1.039 gece)."""
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import kural_katalogu as kk
import ksg_live as ks

NY = ZoneInfo("America/New_York")


def utc_epoch(d: date, hh: int, mm: int) -> int:
    return int(datetime(d.year, d.month, d.day, hh, mm, tzinfo=NY).astimezone(timezone.utc).timestamp())


def day_bars(d: date, o15: float, o16: float, start=(9, 30), end=(16, 0)) -> list[dict]:
    bars, cur = [], datetime(d.year, d.month, d.day, *start, tzinfo=NY)
    stop = datetime(d.year, d.month, d.day, *end, tzinfo=NY)
    while cur <= stop:                                   # 09:30 … 16:00 (16:00 barı dahil)
        t = int(cur.astimezone(timezone.utc).timestamp())
        o = o15 if (cur.hour, cur.minute) == (15, 0) else o16 if (cur.hour, cur.minute) == (16, 0) else 100.0
        bars.append({"t": t, "open": o, "high": o + 1, "low": o - 1, "close": o})
        cur += timedelta(minutes=30)
    return bars


def test_signal_when_last_hour_down():
    d = date(2026, 11, 10)                                # Salı, EST
    sig = ks.find_signal(day_bars(d, 100.0, 99.5), d)
    assert sig and abs(sig["ret_bp"] - (-50.0)) < 1e-6 and sig["o16"] == 99.5


def test_no_signal_when_up_or_flat():
    d = date(2026, 11, 10)
    assert ks.find_signal(day_bars(d, 100.0, 100.5), d) is None
    assert ks.find_signal(day_bars(d, 100.0, 100.0), d) is None        # sıfır → sinyal yok (araştırma: strict < 0)


def test_dst_summer_same_result():
    d = date(2026, 7, 14)                                 # EDT
    sig = ks.find_signal(day_bars(d, 200.0, 199.0), d)
    assert sig and sig["ret_bp"] < 0


def test_no_signal_before_1600_bar_or_short_session():
    d = date(2026, 11, 10)
    assert ks.find_signal(day_bars(d, 100.0, 99.0, end=(15, 30)), d) is None          # 16:00 barı yok
    assert ks.find_signal(day_bars(d, 100.0, 99.0, start=(13, 0)), d) is None          # kısa gün (13:00'e kadar seans)


def test_weekend_and_other_day_ignored():
    sat = date(2026, 11, 7)
    assert ks.find_signal(day_bars(sat, 100.0, 99.0), sat) is None
    d = date(2026, 11, 10)
    assert ks.find_signal(day_bars(d, 100.0, 99.0), date(2026, 11, 11)) is None


def test_exit_due_next_trading_day_0930():
    tue, wed, fri, mon = date(2026, 11, 10), date(2026, 11, 11), date(2026, 11, 13), date(2026, 11, 16)
    assert not ks.exit_due(tue, tue, 16 * 60 + 30, 1)                 # aynı gün: tutulur
    assert not ks.exit_due(tue, wed, 9 * 60 + 29, 2)                  # ertesi gün 09:29: erken
    assert ks.exit_due(tue, wed, 9 * 60 + 30, 2)                      # 09:30: çık
    assert not ks.exit_due(fri, date(2026, 11, 14), 11 * 60, 5)       # Cumartesi: kapanma yok
    assert not ks.exit_due(fri, mon, 9 * 60, 0)                       # Pazartesi 09:00 erken
    assert ks.exit_due(fri, mon, 9 * 60 + 30, 0)                      # Cuma girişi Pazartesi 09:30'da kapanır
    assert ks.exit_due(tue, mon, 10 * 60, 0)                          # bot kapalıydı: geç de olsa çık


def test_emergency_stop_and_catalog():
    assert ks.stop_price(28000.0, 1) == 26320.0
    r = kk.RULES["KSG"]
    assert r["magic_offset"] == 11 and r["lot"] == 0.5 and r["live_key"] == "KSG_LIVE"
    assert kk.RULES["KSG"]["magic_offset"] not in {v["magic_offset"] for k, v in kk.RULES.items() if k != "KSG"}
    assert len(kk.banner("KSG", "x")) >= 5


if __name__ == "__main__":
    n = 0
    for k, f in sorted(globals().items()):
        if k.startswith("test_") and callable(f):
            f(); n += 1
    print(f"{n} test geçti")
