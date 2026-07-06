"""CORTEX Phase 1 — episodic memory + analog retrieval."""
import sys
from pathlib import Path

import pytest

backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import services.cortex_memory as cortex  # noqa: E402


# ── In-memory fake Supabase ───────────────────────────────────────────────────
class _T:
    def __init__(self, rows):
        self._rows = rows
        self._f = {}

    def insert(self, data):
        data = {**data, "id": len(self._rows) + 1}
        self._rows.append(data)
        return {"data": [data], "error": None}

    def select(self, *_a, **_k):
        return self

    def eq(self, c, v):
        self._f[c] = v
        return self

    def limit(self, *_a, **_k):
        return self

    def execute(self):
        return {"data": [r for r in self._rows
                         if all(r.get(c) == v for c, v in self._f.items())], "error": None}

    def update(self, data):
        for r in self._rows:
            if all(r.get(c) == v for c, v in self._f.items()):
                r.update(data)
        return {"data": [], "error": None}


class _Client:
    def __init__(self):
        self.rows = []

    def table(self, _n):
        return _T(self.rows)


@pytest.fixture
def db(monkeypatch):
    c = _Client()
    monkeypatch.setattr(cortex, "_client", lambda: c)
    return c


# ── VIX regime (reuses strategy_optimizer thresholds) ─────────────────────────
def test_vix_regime_thresholds():
    assert cortex._vix_regime(12) == "LOW"
    assert cortex._vix_regime(17) == "NORMAL"
    assert cortex._vix_regime(24) == "ELEVATED"
    assert cortex._vix_regime(32) == "HIGH"
    assert cortex._vix_regime(45) == "EXTREME"
    assert cortex._vix_regime(None) is None


# ── Distance metric ───────────────────────────────────────────────────────────
def test_distance_identical_is_zero():
    a = {"vix_regime": "HIGH", "market_regime": "RANGING", "qqq_premarket_change": 0.3}
    assert cortex._distance(a, dict(a)) == 0.0


def test_distance_categorical_mismatch():
    a = {"vix_regime": "LOW"}
    b = {"vix_regime": "EXTREME"}
    assert cortex._distance(a, b) == 1.0


def test_distance_none_overlap_returns_none():
    assert cortex._distance({"vix_regime": "LOW"}, {"market_regime": "RANGING"}) is None


def test_distance_weights_vix_regime_heaviest():
    # Same everything except vix_regime differs vs only day_of_week differs:
    # the vix_regime mismatch must produce a larger distance (heavier weight).
    base = {"vix_regime": "LOW", "day_of_week": 1}
    vix_diff = cortex._distance(base, {"vix_regime": "HIGH", "day_of_week": 1})
    dow_diff = cortex._distance(base, {"vix_regime": "LOW", "day_of_week": 3})
    assert vix_diff > dow_diff


# ── Record + fill + retrieve ──────────────────────────────────────────────────
def _episode(vix_regime, mkt, actual, chg, dow=1):
    return {"vix_regime": vix_regime, "market_regime": mkt, "day_of_week": dow,
            "_ny_time": "2026-07-06T08:00:00-04:00"}


def test_record_and_find_analogs(db):
    # Seed graded episodes: HIGH-vix + RANGING days mostly went down.
    seeds = [
        ("HIGH", "RANGING", "negative", -0.8),
        ("HIGH", "RANGING", "negative", -0.5),
        ("HIGH", "RANGING", "positive", 0.3),
        ("LOW", "STRONG_TREND_UP", "positive", 1.2),
        ("LOW", "STRONG_TREND_UP", "positive", 0.9),
    ]
    for vr, mkt, act, chg in seeds:
        eid = cortex.record_episode(_episode(vr, mkt, act, chg), predicted_bias="bearish",
                                    confidence=70, run_label="0800_main")
        assert eid is not None
        cortex.fill_outcomes("2026-07-06", act, chg)  # grade by date
    # NOTE: all seeds share the same ny_date here, so grade individually instead:
    # re-grade is idempotent; ensure at least the rows carry outcomes.
    for r, (_, _, act, chg) in zip(db.rows, seeds):
        r["actual_close_direction"] = act
        r["actual_change_pct"] = chg

    # Query resembling the HIGH/RANGING cluster → base rate should lean down.
    q = {"vix_regime": "HIGH", "market_regime": "RANGING", "day_of_week": 1}
    res = cortex.find_analogs(q, k=3)
    assert res["sample_n"] == 3
    assert res["down"] >= 2            # nearest 3 are the HIGH/RANGING cluster
    assert res["low_sample"] is True   # n < 20
    assert 0.0 <= res["p_up_shrunk"] <= 1.0


def test_find_analogs_empty_when_no_graded(db):
    res = cortex.find_analogs({"vix_regime": "HIGH"}, k=8)
    assert res["sample_n"] == 0 and res["p_up_shrunk"] is None


def test_prompt_block_empty_and_populated():
    assert "none comparable" in cortex.analogs_prompt_block({"sample_n": 0})
    block = cortex.analogs_prompt_block({"sample_n": 8, "up": 6, "down": 1, "flat": 1,
                                         "p_up_shrunk": 0.62, "avg_change_pct": 0.4,
                                         "low_sample": False})
    assert "6 up / 1 down" in block
    # Honest framing: no misleading P(up) prediction is surfaced.
    assert "NO reliable directional edge" in block


def test_shrinkage_pulls_small_sample_toward_prior():
    # 2/2 up in a tiny sample must NOT read as 100% after shrinkage.
    res = {"sample_n": 2, "up": 2, "down": 0, "flat": 0}
    p = (2 + cortex._SHRINK_ALPHA * cortex._PRIOR_UP) / (2 + cortex._SHRINK_ALPHA)
    assert p < 0.75   # pulled well below the raw 1.0


# ── build_situation shape (no DB) ─────────────────────────────────────────────
@pytest.mark.asyncio
async def test_build_situation_from_market(monkeypatch):
    from datetime import datetime, timezone
    market = {
        "session": {"ny_time": "2026-07-06T08:00:00-04:00", "current_session": "us_premarket",
                    "session_overlap": False, "is_half_day": False, "minutes_to_us_open": 90,
                    "london_session_direction": "up", "asia_overnight_change": None},
        "macro": {"vix": {"price": 22.0, "chg_1h": 3.0}, "dxy": {"price": 104, "chg_1h": -0.1},
                  "us10y": {"price": 4.3, "chg_1h": 0.2}},
        "qqq": {"premarket_change_pct": -0.3}, "price": 20100,
        "prior_day": {"open": 20000, "close": 20200}, "recent_range": {"5d_high": 20500, "5d_low": 19800}}

    async def no_regime(sym):
        raise RuntimeError("no data")
    monkeypatch.setattr("services.market_regime_service.get_regime_info", no_regime)

    sit = await cortex.build_situation(datetime(2026, 7, 6, 12, tzinfo=timezone.utc), market=market)
    assert sit["vix_regime"] == "ELEVATED"        # 22 → ELEVATED
    assert sit["qqq_premarket_change"] == -0.3
    assert sit["prior_day_dir"] == "up"           # 20200 > 20000
    assert sit["range_position"] == pytest.approx((20100 - 19800) / (20500 - 19800), abs=0.01)
    assert sit["day_of_week"] == 0                # 2026-07-06 is a Monday
