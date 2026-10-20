"""xau_swing_shadow saf çekirdek testleri. Çalıştır: python -m pytest test_xau_swing_shadow.py -q"""
import xau_swing_shadow as xs

DAY = 86400


def _d1(n, last_close=None, base=100.0):
    bars = [{"t": i * DAY, "o": base, "h": base + 1, "l": base - 1, "c": base} for i in range(n)]
    if last_close is not None:
        bars[-2]["c"] = last_close; bars[-2]["h"] = last_close + 0.5
    return bars


def test_signal_new_high_above_ema():
    d1 = _d1(260, last_close=105.0)
    ema = xs.ema_series([b["c"] for b in d1[:-1]])
    assert xs.is_signal(d1, len(d1) - 2, ema)


def test_no_signal_below_high():
    d1 = _d1(260, last_close=100.5)
    ema = xs.ema_series([b["c"] for b in d1[:-1]])
    assert not xs.is_signal(d1, len(d1) - 2, ema)


def test_open_then_sl_first_same_bar():
    d1 = _d1(260, last_close=105.0)
    st = {"open": [], "last_checked": None}
    recs = xs.step(st, d1, [])
    assert recs[0]["kind"] == "open" and st["open"]
    ev = st["open"][0]
    h1 = [{"t": ev["entry_t"], "o": 100, "h": ev["tp"] + 1, "l": ev["sl"] - 1, "c": 100}]
    recs = xs.step(st, d1, h1)
    assert recs[0]["kind"] == "close" and recs[0]["status"] == "sl" and recs[0]["R"] < -1.0
    assert st["open"] == []


def test_time_stop_and_dedup():
    d1 = _d1(260, last_close=105.0)
    st = {"open": [], "last_checked": None}
    xs.step(st, d1, [])
    assert xs.step(st, d1, []) == []           # aynı bar ikinci kez değerlendirilmez
    ev = st["open"][0]
    h1 = [{"t": ev["entry_t"] + k * 3600, "o": ev["entry"], "h": ev["entry"] + 0.1, "l": ev["entry"] - 0.1,
           "c": ev["entry"] + 0.05} for k in range(xs.HOLD_H1 + 5)]
    recs = xs.step(st, d1, h1)
    assert recs[0]["status"] == "time"


def test_busy_skips_new_signal():
    d1 = _d1(260, last_close=105.0)
    st = {"open": [], "last_checked": None}
    xs.step(st, d1, [])
    d2 = d1[:-1] + [dict(d1[-1], c=106.0, h=106.5), {"t": 260 * DAY, "o": 106, "h": 107, "l": 105, "c": 106}]
    recs = xs.step(st, d2, [])
    assert recs and recs[-1]["kind"] == "skip_busy"
