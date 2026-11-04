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
