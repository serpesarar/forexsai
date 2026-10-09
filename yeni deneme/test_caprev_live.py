"""caprev_live.py birim testleri (MT5 gerekmez). Çalıştır: cd 'yeni deneme' && python3 test_caprev_live.py
Kartla tam sadakat (10 yıl, NDX 103/107 aynı tetik mumu, DAX 54/54): research/canli_kart_20261009/caprev_live_fidelity.py"""
from datetime import date, datetime, timedelta, timezone
import caprev_live as cl

NDX, DAX = cl.PROFILES["NDX.INDX"], cl.PROFILES["GDAXI.INDX"]


def bar(y, m, d, h, o, hi, lo, c):
    return {"t": datetime(y, m, d, h, tzinfo=timezone.utc).timestamp(), "open": o, "high": hi, "low": lo, "close": c}


def ndx_days(n=25, start=date(2026, 9, 1), drop_last=0.0):
    """n işlem günü, NY 09:00–16:00 (EDT → 13–19 UTC) yedi 1h bar; son gün kapanışı drop_last kadar düşer."""
    bars, d, px = [], start, 20000.0
    while len([b for b in bars if b["_h"] == 19]) < n:
        if d.weekday() < 5:
            last = len([b for b in bars if b["_h"] == 19]) == n - 1
            for h in range(13, 20):
                c = px * (1 + (drop_last if (last and h == 19) else 0.001 * (1 if h % 2 else -1)))
                bars.append({**bar(d.year, d.month, d.day, h, px, max(px, c) + 5, min(px, c) - 5, c), "_h": h})
                px = c
        d += timedelta(days=1)
    return bars, d


def test_stress_context_and_pdl():
    bars, nxt = ndx_days(25, drop_last=-0.02)
    ctx = cl.daily_context(cl.rth_days(bars, NDX), nxt)
    assert ctx is not None and ctx["stress"] and ctx["r1"] < -0.015
    last_day = max(cl.rth_days(bars, NDX))
    assert ctx["pdl"] == cl.rth_days(bars, NDX)[last_day]["low"]
    assert 0 < ctx["dvol"] < 0.05


def test_no_stress_on_normal_days():
    bars, nxt = ndx_days(25, drop_last=0.0)
    ctx = cl.daily_context(cl.rth_days(bars, NDX), nxt)
    assert ctx is not None and not ctx["stress"]


def test_trigger_window_ndx():
    today = date(2026, 10, 6)                       # Salı, EDT: NY 03:00 = 07:00Z, 15:00 = 19:00Z
    early = bar(2026, 10, 6, 6, 100, 101, 90, 95)   # NY 02:00 başlangıç → pencere dışı
    inwin = bar(2026, 10, 6, 8, 100, 101, 90, 95)   # NY 04:00
    late = bar(2026, 10, 6, 19, 100, 101, 90, 95)   # NY 15:00 başlangıç, bitiş 16:00 > 15:00 → dışı
    assert cl.trigger([early, inwin, late], NDX, today, 97) is inwin
    assert cl.trigger([early, late], NDX, today, 97) is None
    assert cl.trigger([inwin], NDX, today, 90) is None          # kapanış dibin altında değil


def test_trigger_window_dax_and_session_close():
    today = date(2026, 10, 6)                       # CEST: Berlin 08:00 = 06:00Z, 16:30 = 14:30Z
    b0 = bar(2026, 10, 6, 6, 100, 101, 90, 95)      # 08:00 → içinde
    b1 = bar(2026, 10, 6, 14, 100, 101, 90, 95)     # 16:00 başlangıç, bitiş 17:00 > 16:30 → dışı
    assert cl.trigger([b0, b1], DAX, today, 97) is b0
    assert cl.trigger([b1], DAX, today, 97) is None
    assert cl.session_close_utc(today, DAX) == datetime(2026, 10, 6, 16, 0, tzinfo=timezone.utc).timestamp()
    assert cl.session_close_utc(today, NDX) == datetime(2026, 10, 6, 20, 0, tzinfo=timezone.utc).timestamp()


def test_prev_day_vix_uses_strictly_earlier_day():
    h = {"2026-10-02": 19.0, "2026-10-05": 17.0, "2026-10-06": 25.0}
    assert cl.prev_day_vix(h, date(2026, 10, 6)) == 17.0
    assert cl.prev_day_vix(h, date(2026, 10, 5)) == 19.0
    assert cl.prev_day_vix({}, date(2026, 10, 5)) is None


if __name__ == "__main__":
    n = 0
    for k, f in list(globals().items()):
        if k.startswith("test_"):
            f(); n += 1
    print(f"{n} test geçti")
