"""caprev_shadow.py birim testleri (MT5 gerekmez).
Çalıştır:  cd 'yeni deneme' && python3 test_caprev_shadow.py"""
from datetime import date, datetime, timedelta, timezone

import numpy as np
import pandas as pd

import caprev_shadow as cs

NDX = cs.PROFILES["NDX.INDX"]


def utc(y, m, d, h=0, mi=0):
    return datetime(y, m, d, h, mi, tzinfo=timezone.utc).timestamp()


def test_dst_us_and_eu():
    assert cs.tz_offset_min(datetime(2026, 3, 8, 6, 59, tzinfo=timezone.utc), "US") == -300
    assert cs.tz_offset_min(datetime(2026, 3, 8, 7, 0, tzinfo=timezone.utc), "US") == -240
    assert cs.tz_offset_min(datetime(2026, 11, 1, 5, 59, tzinfo=timezone.utc), "US") == -240
    assert cs.tz_offset_min(datetime(2026, 11, 1, 6, 0, tzinfo=timezone.utc), "US") == -300
    assert cs.tz_offset_min(datetime(2026, 3, 29, 0, 59, tzinfo=timezone.utc), "EU") == 60
    assert cs.tz_offset_min(datetime(2026, 3, 29, 1, 0, tzinfo=timezone.utc), "EU") == 120
    assert cs.tz_offset_min(datetime(2026, 10, 25, 1, 0, tzinfo=timezone.utc), "EU") == 60


def test_local_roundtrip_and_open_time():
    # NY 09:30 yaz (EDT) = 13:30Z, kış (EST) = 14:30Z
    assert cs.local_to_utc(date(2026, 10, 5), 570, "US") == utc(2026, 10, 5, 13, 30)
    assert cs.local_to_utc(date(2026, 12, 7), 570, "US") == utc(2026, 12, 7, 14, 30)
    d, m, wd = cs.to_local(utc(2026, 10, 5, 13, 30), "US")
    assert (d, m, wd) == (date(2026, 10, 5), 570, 0)
    # Berlin 17:30 yaz = 15:30Z
    assert cs.local_to_utc(date(2026, 10, 5), 1050, "EU") == utc(2026, 10, 5, 15, 30)


def test_next_trading_date_skips_weekend():
    assert cs.next_trading_date(date(2026, 10, 1)) == date(2026, 10, 2)      # Per → Cum
    assert cs.next_trading_date(date(2026, 10, 2)) == date(2026, 10, 5)      # Cum → Pzt


def _make_session(day: date, base: float, low_dip=0.0, close_to=None):
    """NY RTH günü için tam M15 barları (26 adet). close_to: gün kapanışı."""
    bars = []
    n = (NDX["close"] - NDX["open"]) // 15
    close_to = base if close_to is None else close_to
    for i in range(n):
        t = cs.local_to_utc(day, NDX["open"] + 15 * i, "US")
        px = base + (close_to - base) * i / max(n - 1, 1)
        lo = px - 1 - (low_dip if i == 5 else 0)
        bars.append({"t": t, "open": px, "high": px + 1, "low": lo, "close": px})
    return bars


def _history(n_days=26, start=date(2026, 8, 24), drift=0.0003, last_drop=0.0, base=20000.0):
    bars, px = [], base
    d = start
    days = []
    while len(days) < n_days:
        if d.weekday() < 5:
            days.append(d)
        d += timedelta(days=1)
    for i, d in enumerate(days):
        nxt = px * (1 + drift + (last_drop if i == len(days) - 1 else 0))
        bars += _make_session(d, px, close_to=nxt)
        px = nxt
    return bars, days


def test_rth_days_and_context_stress():
    bars, days = _history(last_drop=-0.02)
    rd = cs.rth_days(bars, NDX)
    assert len(rd) == len(days)
    today = cs.next_trading_date(days[-1])
    ctx = cs.daily_context(rd, today)
    assert ctx["prev_day"] == str(days[-1])
    assert ctx["stress"] and ctx["r1"] < -0.015
    # düşüş yoksa stres yok
    bars2, days2 = _history(last_drop=0.0)
    ctx2 = cs.daily_context(cs.rth_days(bars2, NDX), cs.next_trading_date(days2[-1]))
    assert not ctx2["stress"]


def test_context_matches_pandas_reference():
    bars, days = _history(last_drop=-0.02)
    rd = cs.rth_days(bars, NDX)
    ctx = cs.daily_context(rd, cs.next_trading_date(days[-1]))
    s = pd.Series([rd[d]["close"] for d in sorted(rd)])
    r = s.pct_change()
    assert abs(ctx["dvol"] - r.rolling(20).std().iloc[-1]) < 1e-12
    assert abs(ctx["r5"] - s.pct_change(5).iloc[-1]) < 1e-12


def test_context_ignores_today_and_incomplete_days():
    bars, days = _history()
    today = cs.next_trading_date(days[-1])
    bars += _make_session(today, 99999.0)[:5]                # bugün: eksik bar → atılır, zaten bugün
    rd = cs.rth_days(bars, NDX)
    assert today not in rd
    ctx = cs.daily_context(rd, today)
    assert ctx["prev_day"] == str(days[-1])


def test_tier2_first_close_below_pdl_causal():
    day = date(2026, 10, 5)
    bars = _make_session(day, 20000.0)
    # dip: 5. barın kapanışı pdl altı → o ilk bar
    pdl = 19990.0
    for i, b in enumerate(bars):
        b["close"] = 19985.0 if i in (5, 9) else 20000.0
    trig = cs.tier2_trigger(bars, NDX, day, pdl)
    assert trig["t"] == bars[5]["t"]
    # sadece 5. bara kadar görülen veride aynı sonuç (gelecek barlar kararı değiştirmez)
    assert cs.tier2_trigger(bars[:6], NDX, day, pdl)["t"] == bars[5]["t"]
    # 4. bara kadar görülen veride tetik yok
    assert cs.tier2_trigger(bars[:5], NDX, day, pdl) is None
    # pencere dışı (15:00 sonrası bar) tetiklemez
    late = [dict(b, close=20000.0) for b in bars]
    late[-1]["close"] = 19000.0
    assert cs.tier2_trigger(late, NDX, day, pdl) is None


def _event(entry_t, ask=20000.0, dvol=0.012):
    ctx = {"dvol": dvol, "r1": -0.02, "r5": -0.03, "pdl": 19900.0}
    ev = cs.make_event("NDX.INDX", "k2", date(2026, 10, 5), ctx, 22.0, ask, ask - 1.3, entry_t, entry_t - 960, NDX)
    return ev


def _m1(start_t, n, price_fn):
    out = []
    for i in range(n):
        p = price_fn(i)
        out.append({"t": start_t + 60 * i, "open": p, "high": p + 2, "low": p - 2, "close": p})
    return out


def test_resolve_hits_stop_and_horizons():
    entry_t = cs.local_to_utc(date(2026, 10, 5), 600, "US")
    ev = _event(entry_t)                                      # stop ≈ 20000×(1−0.012)
    assert abs(ev["stop"] - 20000 * 0.988) < 1e-9
    # fiyat sabit → stop yok; aynı gün kapanış çıkışı R ≈ −2×kayma/stop_dist
    m1 = _m1(entry_t - 60, 3 * 24 * 60, lambda i: 20000.0)
    now = ev["d1_t"] + 3600
    r = cs.resolve_event(ev, m1, now)
    assert r["status"] == "done" and not r["stopped_d0"] and not r["stopped_d1"]
    assert abs(r["R_d0"] - (-0.4 / ev["stop_dist"])) < 1e-3
    # stop ertesi sabah vurulur → d0 serbest kalır, d1 = −1R civarı
    stop_t = cs.local_to_utc(date(2026, 10, 6), 600, "US")
    m1b = [dict(b) for b in m1]
    for b in m1b:
        if b["t"] >= stop_t:
            b.update(open=19700.0, high=19702.0, low=19698.0, close=19700.0)
    r2 = cs.resolve_event(ev, m1b, now)
    assert r2["stopped_d1"] and not r2["stopped_d0"]
    assert r2["R_d1"] < -1.0 and r2["R_d0"] > -0.1               # boşluk → açılıştan dolum, −1R'den kötü


def test_resolve_waits_when_horizon_not_reached():
    entry_t = cs.local_to_utc(date(2026, 10, 5), 600, "US")
    ev = _event(entry_t)
    m1 = _m1(entry_t - 60, 200, lambda i: 20000.0)
    r = cs.resolve_event(ev, m1, entry_t + 200 * 60)          # 13:20 NY: 16:00 çıkışına daha var
    assert r["status"] == "open" and r.get("R_d0") is None


def test_k5b_check_requires_fresh_stress_context():
    import time as _t
    cs._K5B["NDX.INDX"] = {"t": _t.time(), "stress": True, "pdl": 20000.0, "r1": -0.02, "r5": -0.05, "dvol": 0.012}
    assert cs.k5b_check("NDX.INDX", 19990.0)[0] is True
    assert cs.k5b_check("NDX.INDX", 20010.0)[0] is False
    cs._K5B["NDX.INDX"]["stress"] = False
    assert cs.k5b_check("NDX.INDX", 19990.0)[0] is False
    cs._K5B["NDX.INDX"].update(stress=True, t=_t.time() - 1000)
    assert cs.k5b_check("NDX.INDX", 19990.0)[0] is False        # bayat bağlam → fail-open (bloklamaz)


if __name__ == "__main__":
    n = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            n += 1
            print("OK", name)
    print(f"{n} test geçti")
