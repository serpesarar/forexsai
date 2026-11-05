"""Zaman Makinesi (trader-timemachine uyarlaması) testleri."""
from datetime import datetime, timezone

import numpy as np
import pytest

from services import time_machine_service as tm


def _bars(days: int = 40, seed: int = 3) -> tm.Bars:
    """NY 17:00'den başlayan, 23 saatlik (276 bar) sentetik broker günleri, hafta sonu boşluklu değil."""
    rng = np.random.default_rng(seed)
    start = int(datetime(2026, 3, 2, 22, 0, tzinfo=timezone.utc).timestamp())   # NY 17:00 (EST)
    ts, c = [], [100.0]
    for d in range(days):
        base = start + d * 86400
        for k in range(276):
            ts.append(base + k * 300)
    n = len(ts)
    r = rng.normal(0, 4e-4, n)
    close = 100 * np.exp(np.cumsum(r))
    op = np.r_[100.0, close[:-1]]
    hi = np.maximum(op, close) * (1 + np.abs(rng.normal(0, 3e-4, n)))
    lo = np.minimum(op, close) * (1 - np.abs(rng.normal(0, 3e-4, n)))
    return tm.Bars(np.array(ts, dtype=np.int64), op, hi, lo, close)


def test_day_and_slot_ny_boundary_and_dst():
    est = int(datetime(2026, 3, 2, 22, 0, tzinfo=timezone.utc).timestamp())      # 17:00 EST → slot 0
    edt = int(datetime(2026, 3, 9, 21, 0, tzinfo=timezone.utc).timestamp())      # 17:00 EDT (DST sonrası) → slot 0
    d, s = tm.day_and_slot(np.array([est, est + 300, est - 300, edt], dtype=np.int64))
    assert list(s) == [0, 1, 287, 0]
    assert d[0] == d[1] and d[2] == d[0] - 1 and d[3] == d[0] + 7


def test_stop_checked_before_target_in_same_bar():
    pool = [[(1.0, 1.02, 0.98, 1.0)] for _ in range(tm.SLOTS)]       # her bar iki tarafa da değer
    mc = tm.simulate(pool, 100.0, 99.0, 101.0, 10, 20, replays=200, seed=1, side="buy")
    assert mc["p_stop"] == 1.0 and mc["p_target"] == 0.0 and mc["avg_R"] == -1.0
    mc = tm.simulate(pool, 100.0, 101.0, 99.0, 10, 20, replays=200, seed=1, side="sell")
    assert mc["p_stop"] == 1.0


def test_verdict_thresholds():
    assert tm.verdict({"p_target": 0.40, "p_stop": 0.38, "r_at_target": 1.0}).startswith("Yazı-tura")
    assert tm.verdict({"p_target": 0.45, "p_stop": 0.35, "r_at_target": 1.0}).startswith("Hedefe meyilli")
    assert tm.verdict({"p_target": 0.20, "p_stop": 0.60, "r_at_target": 1.0}).startswith("Güçlü biçimde stopa")
    assert tm.verdict({"p_target": 0.24, "p_stop": 0.50, "r_at_target": 2.0}).startswith("Başabaşa yakın")
    assert tm.verdict({"p_target": 0.0, "p_stop": 0.0, "r_at_target": 1.0}).startswith("Hiçbir")


def test_run_plan_end_to_end_and_no_lookahead():
    b = _bars()
    q = len(b.ts) - 100
    res = tm.run_plan(b, "buy", 1.0, 1.0, 24, replays=800, seed=19, query_index=q)
    mc = res["mc"]
    assert abs(mc["p_target"] + mc["p_stop"] + mc["p_neither"] - 1) < 1e-6
    assert res["plan"]["stop"] < res["plan"]["entry"] < res["plan"]["target"]
    assert res["plan"]["pool_sessions"] == tm.POOL_SESSIONS or res["plan"]["pool_sessions"] >= tm.MIN_SESSIONS
    # havuz yalnız sorgu gününden ÖNCEKİ günler: gelecekteki barları bozmak sonucu değiştirmemeli
    b2 = tm.Bars(b.ts.copy(), b.o.copy(), b.h.copy(), b.l.copy(), b.c.copy())
    b2.c[q + 1:] *= 1.5; b2.h[q + 1:] *= 1.5; b2.l[q + 1:] *= 1.5; b2.o[q + 1:] *= 1.5
    res2 = tm.run_plan(b2, "buy", 1.0, 1.0, 24, replays=800, seed=19, query_index=q)
    assert res2["mc"]["p_target"] == mc["p_target"] and res2["mc"]["avg_R"] == mc["avg_R"]


def test_history_replay_counts():
    b = _bars()
    res = tm.run_plan(b, "sell", 1.5, 2.0, 30, replays=500, seed=5)
    h = res["history"]
    assert h["target"] + h["stop"] + h["close"] == h["trades"] and h["trades"] <= h["sessions"]


def test_too_few_sessions_refused():
    b = _bars(days=10)
    with pytest.raises(tm.TMError):
        tm.run_plan(b, "buy")


def test_range_band_monotone_and_relative():
    b = _bars()
    band = tm.range_band(b, n_bars=12, bar_min=5, replays=400)
    assert band["p5"] < band["p25"] < band["p50"] < band["p75"] < band["p95"]
    assert abs(band["p50"] / band["price"] - band["rel_p50"]) < 1e-9 and band["horizon_min"] == 60


def test_level_check_uses_own_entry_and_side():
    band = {"rel_p5": 0.99, "rel_p25": 0.997, "rel_p75": 1.003, "rel_p95": 1.01}
    lc = tm.level_check(band, entry=200.0, tp=203.0, sl=199.5, side="buy")      # p95 = 202 → TP dışarıda; SL 199.5 ∈ [199.4, 200.6]
    assert lc["tp_outside_p90"] is True and lc["sl_inside_p50"] is True
    ls = tm.level_check(band, entry=200.0, tp=199.0, sl=203.0, side="sell")     # p5 = 198 → TP içeride
    assert ls["tp_outside_p90"] is False and ls["sl_inside_p50"] is False


def test_bars_from_mt5_rates_subtracts_broker_offset():
    rates = [{"time": 1_000_000 + 10800, "open": 1.0, "high": 1.1, "low": 0.9, "close": 1.05}]
    b = tm.bars_from_mt5_rates(rates, 10800)
    assert int(b.ts[0]) == 1_000_000 and b.c[0] == 1.05


def test_broker_offset_from_tick():
    assert tm.broker_offset_from_tick(1_000_000 + 10800 + 5, now=1_000_000) == 10800
    assert tm.broker_offset_from_tick(1_000_000 - 7200, now=1_000_000) == -7200
    assert tm.broker_offset_from_tick(1_000_000 + 10800 + 3000, now=1_000_000) is None   # bayat/uyumsuz tick


def test_range_band_mt5_with_fake_terminal():
    b = _bars()
    off = 10800
    rates = [{"time": int(t) + off, "open": o, "high": h, "low": l, "close": c} for t, o, h, l, c in zip(b.ts, b.o, b.h, b.l, b.c)]

    class FakeMT5:
        TIMEFRAME_M5, TIMEFRAME_M15, TIMEFRAME_H1 = 5, 15, 16385
        def symbol_info_tick(self, s):
            return None
        def copy_rates_from_pos(self, s, tf, pos, n):
            return rates
    tm._mt5_band_cache.clear()
    band = tm.range_band_mt5(FakeMT5(), "NAS100", broker_offset_s=off)
    assert band and band["p5"] < band["p95"] and band["broker_offset_s"] == off
    assert tm.range_band_mt5(FakeMT5(), "OTHER") is None          # tick yok → offset bilinmez → None (fail-open)
