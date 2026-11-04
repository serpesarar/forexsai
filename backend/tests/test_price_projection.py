"""Price Projection Service — hedef-seviye matematiği testleri.

Kullanıcının verdiği ders örnekleriyle birebir doğrulanır:
  * 20.000 → 19.000 düşüşünde %61.8 geri alma = 19.618
  * Measured move: 500 puanlık düşüş → C'den 500 puan daha aşağı
"""
from __future__ import annotations

import pytest

from services.price_projection_service import (
    compute_adr, compute_fib, compute_market_profile, compute_mean_reversion,
    compute_orb, compute_vol_state, projection_prompt_block,
)


def _bar(ts, o, h, l, c, v=100.0):
    return {"ts": ts, "open": o, "high": h, "low": l, "close": c, "volume": v}


def _flat_bars(n, price=20000.0, day="2026-07-01"):
    return [_bar(f"{day}T{i % 24:02d}:00:00", price, price + 1, price - 1, price)
            for i in range(n)]


# ── Fibonacci: kullanıcının örneği birebir ────────────────────────────────────
def test_fib_retracement_matches_textbook_example():
    """20.000 tepe → 19.000 dip: %61.8 retr = 19.618, %50 = 19.500."""
    bars = _flat_bars(40, 19500.0)
    bars.append(_bar("2026-07-02T01:00:00", 19950, 20000, 19900, 19950))   # tepe
    bars += [_bar(f"2026-07-02T{h:02d}:00:00", 19800 - h * 50, 19850 - h * 50,
                  19750 - h * 50, 19800 - h * 50) for h in range(2, 12)]
    bars.append(_bar("2026-07-02T13:00:00", 19050, 19100, 19000, 19050))   # dip
    f = compute_fib(bars, current_price=19200.0)
    assert f is not None and f["impulse"] == "down"
    assert f["swing_high"] == 20000.0 and f["swing_low"] == 19000.0
    assert f["impulse_size"] == 1000.0
    assert f["retracements"]["0.618"] == 19618.0        # ders örneği
    assert f["retracements"]["0.500"] == 19500.0
    assert f["golden_618"] == 19618.0
    # extension: dip altı hedef → 20000 - 1000×1.618 = 18382
    assert f["extensions"]["1.618"] == 18382.0


def test_measured_move_down_projects_impulse_from_current():
    """Ders örneği: 500 puanlık düşüş → C'den 500 puan daha (19.500-500=19.000)."""
    bars = _flat_bars(40, 19800.0)
    bars.append(_bar("2026-07-02T01:00:00", 19990, 20000, 19980, 19990))
    bars.append(_bar("2026-07-02T02:00:00", 19600, 19650, 19500, 19550))
    f = compute_fib(bars, current_price=19500.0)
    assert f["impulse"] == "down" and f["impulse_size"] == 500.0
    assert f["measured_move_target"] == 19000.0


def test_fib_up_impulse_retraces_down_and_extends_up():
    bars = _flat_bars(40, 19100.0)
    bars.append(_bar("2026-07-02T01:00:00", 19010, 19050, 19000, 19010))   # dip
    bars.append(_bar("2026-07-02T02:00:00", 19900, 20000, 19850, 19950))   # tepe
    f = compute_fib(bars, current_price=19900.0)
    assert f["impulse"] == "up"
    assert f["retracements"]["0.618"] == 19382.0        # 20000 - 618
    assert f["extensions"]["1.618"] == 20618.0          # 19000 + 1618
    assert f["measured_move_target"] == 20900.0         # 19900 + 1000


# ── ADR ───────────────────────────────────────────────────────────────────────
def test_adr_average_and_exhaustion():
    bars = []
    for d in range(1, 11):                    # 10 gün × 200 puan range
        day = f"2026-07-{d:02d}"
        bars.append(_bar(f"{day}T10:00:00", 20000, 20100, 19900, 20000))
        bars.append(_bar(f"{day}T11:00:00", 20000, 20050, 19950, 20000))
    # bugün: 190 puanlık range → used ≈ %95 → exhausted
    bars.append(_bar("2026-07-11T10:00:00", 20000, 20190, 20000, 20100))
    a = compute_adr(bars, current_price=20100.0)
    assert a is not None
    assert a["adr_points"] == 200.0
    assert a["today_used_pct"] == 95.0 and a["exhausted"] is True
    assert a["projected_high_from_low"] == 20200.0     # low 20000 + ADR 200


# ── Volatility squeeze ────────────────────────────────────────────────────────
def test_vol_state_detects_squeeze_after_quiet_period():
    bars = []
    for i in range(150):                       # geniş range dönemi
        bars.append(_bar(f"2026-07-01T{i % 24:02d}:00:00", 20000, 20080, 19920, 20000 + (i % 5)))
    for i in range(60):                        # sıkışma
        bars.append(_bar(f"2026-07-08T{i % 24:02d}:00:00", 20000, 20004, 19996, 20000 + (i % 2) * 0.5))
    v = compute_vol_state(bars)
    assert v is not None and v["state"] == "squeeze"
    assert v["atr_percentile"] <= 25


# ── Mean reversion ────────────────────────────────────────────────────────────
def test_mean_reversion_stretch_flags_far_price():
    bars = []
    for d in range(1, 30):
        day = f"2026-06-{d:02d}"
        bars.append(_bar(f"{day}T10:00:00", 20000, 20050, 19950, 20000))
    bars.append(_bar("2026-07-01T10:00:00", 19000, 19050, 18980, 19000))   # sert kopuş
    m = compute_mean_reversion(bars, current_price=19000.0)
    assert m is not None
    assert m["stretched"] is True and m["stretch_atr"] < -2.0


# ── ORB ───────────────────────────────────────────────────────────────────────
def test_orb_breakout_up_and_context_note():
    m5 = [_bar(f"2026-07-10T13:{mm:02d}:00", 20000, 20040 + mm, 19960, 20010, 50)
          for mm in (30, 35, 40, 45, 50)]
    o = compute_orb(m5, current_price=20120.0)
    assert o is not None
    assert o["or15_high"] == 20080.0 and o["status"] == "broken_up"   # max(high[:3])
    assert "edge" in o["note"]                 # dürüst context-only etiketi


# ── Market Profile ────────────────────────────────────────────────────────────
def test_market_profile_poc_at_heaviest_price():
    m5 = []
    for d in ("2026-07-08", "2026-07-09", "2026-07-10"):
        for i in range(40):                    # 19900-20000 value bölgesi, ağır hacim
            m5.append(_bar(f"{d}T{10 + i // 12:02d}:{(i * 5) % 60:02d}:00",
                           19950, 19960, 19940, 19950, v=1000))
        for i in range(8):                     # 20200 kabul edilmeyen bölge, cılız
            m5.append(_bar(f"{d}T16:{(i * 5) % 60:02d}:00",
                           20200, 20210, 20190, 20200, v=50))
    mp = compute_market_profile(m5, current_price=20200.0)
    assert mp is not None
    assert abs(mp["poc"] - 19950) < 30         # POC ağır işlem bölgesinde
    assert mp["price_vs_value"] == "above_value"   # 'piyasa bu fiyatı kabul etmedi'
    assert mp["val"] <= 19950 <= mp["vah"]


# ── prompt block ──────────────────────────────────────────────────────────────
def test_prompt_block_renders_all_sections():
    snap = {
        "fib": {"impulse": "down", "swing_high": 20000.0, "swing_low": 19000.0,
                "impulse_size": 1000.0,
                "retracements": {"0.236": 19236.0, "0.382": 19382.0, "0.500": 19500.0,
                                 "0.618": 19618.0, "0.786": 19786.0},
                "extensions": {"1.272": 18728.0, "1.618": 18382.0, "2.000": 18000.0},
                "golden_618": 19618.0, "measured_move_target": 18500.0},
        "adr": {"adr_points": 240.0, "adr_pct": 1.2, "today_range": 250.0,
                "today_used_pct": 104.0, "exhausted": True,
                "projected_high_from_low": 20240.0, "projected_low_from_high": 19760.0},
        "vol": {"atr14_1h": 35.0, "atr_percentile": 15.0, "bb_width_percentile": 10.0,
                "state": "squeeze"},
        "mean_reversion": {"ema20_daily": 20000.0, "stretch_atr": -2.4,
                           "rsi14_1h": 28.0, "stretched": True},
        "orb": {"or15_high": 20050.0, "or15_low": 19900.0, "status": "inside",
                "note": "context-only: no proven edge"},
        "market_profile": {"poc": 19950.0, "vah": 20010.0, "val": 19890.0,
                           "price_vs_value": "inside_value", "days": 5},
    }
    block = projection_prompt_block(snap)
    assert "19618" in block and "measured-move target=18500" in block
    assert "EXHAUSTED" in block and "SQUEEZE" in block
    assert "STRETCHED" in block and "POC=19950" in block
    assert "no proven edge" in block


def test_all_sections_fail_open_on_empty_data():
    assert compute_fib([], 100.0) is None
    assert compute_adr([], 100.0) is None
    assert compute_vol_state([]) is None
    assert compute_mean_reversion([], 100.0) is None
    assert compute_orb([], 100.0) is None
    assert compute_market_profile([], 100.0) is None
    assert projection_prompt_block({}) == ""
