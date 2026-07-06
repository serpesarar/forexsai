"""CORTEX backfill (forward target) — leak-freedom, TZ solving, forward outcomes."""
import sys
from datetime import date
from pathlib import Path

import pandas as pd
import pytest

backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import services.cortex_backfill as bf  # noqa: E402


def _nq(bars: dict) -> pd.DataFrame:
    """bars = {('YYYY-MM-DD','HH:MM'): close} → ET NQ frame."""
    from zoneinfo import ZoneInfo
    rows = []
    for (d, hm), px in bars.items():
        h, m = map(int, hm.split(":"))
        ts = pd.Timestamp(f"{d} {h:02d}:{m:02d}", tz=ZoneInfo("America/New_York"))
        rows.append({"et": ts, "Open": px, "High": px, "Low": px, "Close": px, "Volume": 100})
    return pd.DataFrame(rows).sort_values("et").reset_index(drop=True)


def _daily(days):
    df = pd.DataFrame(days, columns=["Date", "Open", "High", "Low", "Close"])
    df["Date"] = pd.to_datetime(df["Date"]).dt.date
    return df.set_index("Date").sort_index()


# ── nq_close_at ───────────────────────────────────────────────────────────────
def test_nq_close_at_last_before_minute():
    nq = _nq({("2024-03-06", "09:30"): 100.0, ("2024-03-06", "09:35"): 101.0,
              ("2024-03-06", "09:45"): 102.0})
    assert bf.nq_close_at(nq, date(2024, 3, 6), 9 * 60 + 35) == 101.0   # 09:35
    assert bf.nq_close_at(nq, date(2024, 3, 6), 9 * 60 + 40) == 101.0   # nearest prior within tol
    assert bf.nq_close_at(nq, date(2024, 3, 6), 8 * 60) is None          # nothing before


def test_prev_next_td():
    tds = [date(2024, 3, 4), date(2024, 3, 5), date(2024, 3, 6)]
    assert bf._prev_td(tds, date(2024, 3, 6)) == date(2024, 3, 5)
    assert bf._next_td(tds, date(2024, 3, 5)) == date(2024, 3, 6)
    assert bf._next_td(tds, date(2024, 3, 6)) is None


# ── build_day_episodes: forward outcome + leak-freedom ────────────────────────
def _sources(future_6h_px: float, future_24h_px: float) -> bf.Sources:
    ndx = _daily([("2024-03-05", 20000, 20100, 19900, 20080),
                  ("2024-03-06", 20000, 20500, 19500, 20050),
                  ("2024-03-07", 20000, 20100, 19900, 20050)])
    tds = sorted(ndx.index.tolist())
    idx = [date(2024, 3, 4), date(2024, 3, 5)]
    nq = _nq({
        ("2024-03-05", "16:00"): 20000.0,                 # prev cash close
        ("2024-03-06", "09:30"): 20100.0,                 # today open (overnight +0.5%)
        ("2024-03-06", "10:00"): 20150.0,                 # first-hour move
        ("2024-03-06", "11:00"): 20200.0,
        ("2024-03-06", "15:30"): future_6h_px,            # 09:30 + 6h
        ("2024-03-07", "09:30"): future_24h_px,           # next day same T (24h)
    })
    return bf.Sources(ndx=ndx,
                      vix=pd.Series([22.0, 23.0], index=idx),
                      dxy=pd.Series([104.0, 104.5], index=idx),
                      us10y=pd.Series([4.2, 4.3], index=idx),
                      nq_et=nq, trading_days=tds)


def test_forward_outcome_and_situation_leakfree():
    up = bf.build_day_episodes(_sources(future_6h_px=20400.0, future_24h_px=20600.0), date(2024, 3, 6))
    dn = bf.build_day_episodes(_sources(future_6h_px=19800.0, future_24h_px=19700.0), date(2024, 3, 6))
    e_up = next(e for e in up if e["decision_time"] == "0930")
    e_dn = next(e for e in dn if e["decision_time"] == "0930")

    # forward outcomes react to future price...
    assert e_up["out_6h_dir"] == "positive" and e_dn["out_6h_dir"] == "negative"
    assert e_up["out_24h_dir"] == "positive" and e_dn["out_24h_dir"] == "negative"
    # ...but the SITUATION is identical (no leak of the future into inputs).
    sit_keys = [k for k in e_up if not k.startswith("out_") and k != "px_at_T"]
    assert {k: e_up[k] for k in sit_keys} == {k: e_dn[k] for k in sit_keys}
    assert e_up["overnight_change"] == pytest.approx((20100 - 20000) / 20000 * 100, abs=0.01)
    assert e_up["vix_regime"] == "ELEVATED"       # D-1 VIX 23
    assert e_up["prior_day_dir"] == "up"          # 03-05: 20000→20080


def test_first_hour_move_zero_at_open():
    eps = bf.build_day_episodes(_sources(20400.0, 20600.0), date(2024, 3, 6))
    e0930 = next(e for e in eps if e["decision_time"] == "0930")
    e1100 = next(e for e in eps if e["decision_time"] == "1100")
    assert e0930["first_hour_move"] == 0.0                              # nothing since open
    assert e1100["first_hour_move"] == pytest.approx((20200 - 20100) / 20100 * 100, abs=0.01)


def test_three_decision_times_produced():
    eps = bf.build_day_episodes(_sources(20400.0, 20600.0), date(2024, 3, 6))
    assert {e["decision_time"] for e in eps} == {"0930", "1000", "1100"}


# ── distance ──────────────────────────────────────────────────────────────────
def test_distance_fwd_identical_zero_and_overnight_weight():
    a = {"vix_regime": "HIGH", "overnight_change": 0.5, "prior_day_dir": "up"}
    assert bf.distance_fwd(a, dict(a)) == 0.0
    base = {"vix_regime": "LOW", "day_of_week": 1}
    vix = bf.distance_fwd(base, {"vix_regime": "HIGH", "day_of_week": 1})
    dow = bf.distance_fwd(base, {"vix_regime": "LOW", "day_of_week": 3})
    assert vix > dow                                                    # vix weight heavier


# ── walk-forward integrity ────────────────────────────────────────────────────
def test_walk_forward_needs_min_pool_and_reports():
    eps = []
    for i in range(200):
        d = f"2024-{(i//20)+1:02d}-{(i%20)+1:02d}"
        # overnight up → 6h up (perfect momentum) for half, noise for rest
        up = (i % 2 == 0)
        eps.append({"ny_date": d, "decision_time": "0930",
                    "vix_regime": "LOW" if up else "HIGH", "overnight_change": 0.5 if up else -0.5,
                    "prior_day_dir": "up", "first_hour_move": 0.0, "market_regime": "RANGING",
                    "out_6h_dir": "positive" if up else "negative", "out_6h_pct": 0.4 if up else -0.4,
                    "out_24h_dir": None, "out_24h_pct": None, "day_of_week": 1})
    rep = bf.walk_forward(eps, "6h", "0930", k=5, min_pool=40)
    assert rep["n"] >= 100
    assert rep["calibration_spread_pp"] > 20         # clean separable signal
    assert rep["momentum_baseline_acc_pct"] == 100.0  # overnight sign == outcome by construction


def test_walk_forward_insufficient_flagged():
    eps = [{"ny_date": f"2024-01-{d:02d}", "decision_time": "1000", "vix_regime": "LOW",
            "overnight_change": 0.2, "prior_day_dir": "up", "out_6h_dir": "positive",
            "out_6h_pct": 0.3, "day_of_week": 1} for d in range(1, 20)]
    assert bf.walk_forward(eps, "6h", "1000", min_pool=5).get("insufficient") is True


# ── TZ solver (unchanged core) ────────────────────────────────────────────────
def test_offset_solver_recovers_known_offset():
    from zoneinfo import ZoneInfo
    import numpy as np
    rows = []
    rng = np.random.default_rng(7)
    for day in pd.date_range("2024-03-04", "2024-03-28", freq="B"):
        for minute in range(0, 24 * 60, 5):
            et = (pd.Timestamp(day) + pd.Timedelta(minutes=minute)).tz_localize(ZoneInfo("America/New_York"))
            mod = et.hour * 60 + et.minute
            vol = 10000 if mod in (570, 575) else 8000 if mod in (955, 960) else 100 + rng.integers(0, 50)
            file_time = et.tz_convert("UTC").tz_localize(None) + pd.Timedelta(hours=3)
            rows.append({"Time": file_time, "Open": 1, "High": 1, "Low": 1, "Close": 1, "Volume": vol})
    nq = pd.DataFrame(rows).sort_values("Time").reset_index(drop=True)
    assert bf.solve_monthly_offsets(nq).get("2024-03") == 3
