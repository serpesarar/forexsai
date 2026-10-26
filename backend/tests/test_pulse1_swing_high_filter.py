"""Issue #17 boundaries, failure paths and shared gate integration (no I/O)."""
import asyncio
import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from services import signal_gates as sg
from services.pulse1_swing_high_filter import DISTANCE_FIELD, SWING_HIGH_GATE, would_block
from research.evaluate_issue17 import evaluate


def factors(regime="transition", distance=0.36):
    return {"regime_label": regime, DISTANCE_FIELD: distance}


@pytest.mark.parametrize("regime", ["transition", "unknown"])
@pytest.mark.parametrize("distance,blocked", [(-0.1, True), (0, True), (0.36, True),
                                           (1.999, True), (2.0, False), (2.001, False)])
def test_strict_threshold(regime, distance, blocked):
    assert would_block("XAUUSD", "BUY", "pulse1", factors(regime, distance)) is blocked


@pytest.mark.parametrize("value", [None, "", "bad", True, False, float("nan"),
                                  float("inf"), float("-inf"), {}, []])
def test_invalid_distance_fails_open(value):
    assert not would_block("XAUUSD", "BUY", "pulse1", factors(distance=value))


@pytest.mark.parametrize("snapshot", [None, {}, [], {DISTANCE_FIELD: 0.1},
                                     {"regime_label": "transition"}])
def test_missing_features_are_not_unknown_or_zero(snapshot):
    assert not would_block("XAUUSD", "BUY", "pulse1", snapshot)


@pytest.mark.parametrize("regime", ["ranging", "strong_trend_up", "strong_trend_down",
                                    "uptrend", "downtrend", None, ""])
def test_other_regimes_pass(regime):
    assert not would_block("XAUUSD", "BUY", "pulse1", factors(regime))


@pytest.mark.parametrize("symbol,direction,model", [
    ("NDX.INDX", "BUY", "pulse1"), ("XAUUSD", "SELL", "pulse1"),
    ("XAUUSD", "HOLD", "pulse1"), ("XAUUSD", "BUY", "pulse2"),
    ("XAUUSD", "BUY", "pulse3"), ("XAUUSD", "BUY", "ml"),
    ("XAUUSD", "BUY", "pulse1_inv"),
])
def test_scope(symbol, direction, model):
    assert not would_block(symbol, direction, model, factors())


def test_alias_and_numeric_string():
    assert would_block("xauusd.forex", "BUY", "PULSE1", factors("UNKNOWN", "0.36"))


@pytest.fixture
def snapshot(monkeypatch):
    module = ModuleType("services.signal_feature_snapshot")
    module.build_signal_feature_snapshot = AsyncMock(return_value=factors())
    monkeypatch.setitem(sys.modules, module.__name__, module)
    monkeypatch.delenv("PULSE1_SWING_HIGH_GATE_BLOCK", raising=False)
    monkeypatch.delenv("PULSE1_SWING_HIGH_GATE_ENABLED", raising=False)
    return module.build_signal_feature_snapshot


@pytest.fixture
def other_gates(monkeypatch):
    """Only this gate uses snapshot I/O; isolate all unrelated gate decisions."""
    monkeypatch.setattr(sg, "pulse1_symbol_enabled", lambda _: True)
    for name in ("xau_trend_sell_gate", "ndx_smc_sell_gate", "calendar_gate",
                 "entry_score_gate", "trend_align_gate", "wave_position_gate",
                 "vix_regime_gate", "fakeout_gate", "debate_bias_gate"):
        monkeypatch.setattr(sg, name, AsyncMock(return_value=(True, None)))
    for name in ("xau_scalp_gate", "session_gate", "time_quality_gate"):
        monkeypatch.setattr(sg, name, lambda *a, **kw: (True, None))


def run_gate():
    return asyncio.run(sg.apply_signal_gates_ex("XAUUSD", "BUY", "pulse1", confidence=80))


def test_default_shadow_is_measurable(snapshot, other_gates):
    signal, notes, shadow = run_gate()
    assert signal == "BUY" and notes == []
    assert [v["gate"] for v in shadow] == [SWING_HIGH_GATE]
    assert "0.360 < 2.0" in shadow[0]["reason"]
    snapshot.assert_awaited_once_with("XAUUSD")


def test_explicit_block_returns_hold(snapshot, other_gates, monkeypatch):
    monkeypatch.setenv("PULSE1_SWING_HIGH_GATE_BLOCK", "1")
    signal, notes, shadow = run_gate()
    assert signal == "HOLD" and "issue #17" in notes[0] and shadow == []


@pytest.mark.parametrize("value", ["0", "true", "typo", ""])
def test_only_literal_one_can_activate(snapshot, other_gates, monkeypatch, value):
    monkeypatch.setenv("PULSE1_SWING_HIGH_GATE_BLOCK", value)
    assert run_gate()[0] == "BUY"


def test_off_and_out_of_scope_do_not_fetch(snapshot, monkeypatch):
    assert asyncio.run(sg.pulse1_swing_high_gate("XAUUSD", "SELL", "pulse1")) == (True, None)
    monkeypatch.setenv("PULSE1_SWING_HIGH_GATE_ENABLED", "0")
    assert asyncio.run(sg.pulse1_swing_high_gate("XAUUSD", "BUY", "pulse1")) == (True, None)
    snapshot.assert_not_awaited()


def test_snapshot_failure_fails_open(snapshot, other_gates, monkeypatch):
    monkeypatch.setenv("PULSE1_SWING_HIGH_GATE_BLOCK", "1")
    snapshot.side_effect = RuntimeError("unavailable")
    assert run_gate() == ("BUY", [], [])


def test_prior_gate_block_remains_authoritative(snapshot, other_gates, monkeypatch):
    monkeypatch.setattr(sg, "session_gate", lambda _: (False, "session blocked"))
    monkeypatch.setattr(sg, "tq_session_exception", lambda *a: False)
    assert run_gate() == ("HOLD", ["session blocked"], [])
    snapshot.assert_not_awaited()


def row(status, snapshot=None, **kwargs):
    return dict(symbol="XAUUSD", model_type="pulse1", ml_direction="BUY",
                status=status, factors=snapshot if snapshot is not None else factors(), **kwargs)


def test_history_exposes_blocked_winners_and_missing_data():
    rows = [row("completed"), row("stopped"), row("completed", factors(distance=2.0)),
            row("completed", {}), row("active"), row("expired")]
    report = evaluate(rows)
    result = report["all_resolved_candidates"]
    assert result["before"]["wins"] == 3
    assert result["would_block"]["resolved"] == 2
    assert result["would_block"]["wins"] == 1
    assert result["would_block"]["losses"] == 1
    assert result["would_block"]["win_rate_pct"] == 50.0
    assert result["historical_winners_blocked_pct"] == 33.3333
    assert result["missing_feature_rows"] == 1
    assert report["excluded_statuses"] == {"active": 1, "expired": 1}
    assert report["pnl"] is None


def test_history_no_data_is_not_zero_winner_impact():
    result = evaluate([])
    assert result["status"] == "no_resolved_candidates"
    assert result["all_resolved_candidates"]["historical_winners_blocked_pct"] is None


def test_history_json_factors_and_geometry_epochs():
    report = evaluate([row("completed", '{"regime_label":"unknown","M30_dist_swing_high_30_atr":1.5}'),
                       row("stopped", dict(factors(), target_type="atr_ladder_v1"))])
    assert report["by_regime"]["unknown"]["would_block"]["wins"] == 1
    assert report["by_target_type"]["atr_ladder_v1"]["would_block"]["losses"] == 1


@pytest.mark.parametrize("mode,expected", [("0", "BUY"), ("1", "HOLD")])
def test_panel_signal_type_and_logging_stay_consistent(
    snapshot, other_gates, monkeypatch, mode, expected,
):
    """Exercise the real route: a blocked candidate must never reach logging."""
    from routers import emel_pulse as panel

    def stub(name, **attrs):
        module = ModuleType(name)
        module.__dict__.update(attrs)
        monkeypatch.setitem(sys.modules, name, module)

    monkeypatch.setenv("PULSE1_SWING_HIGH_GATE_BLOCK", mode)
    monkeypatch.setattr(panel, "_resolve_signal_timestamp", lambda *a: "2026-10-26T12:00:00Z")
    monkeypatch.setattr(panel, "_set_cached_panel_analysis", lambda *a: None)
    monkeypatch.setattr(panel, "_scalp_tp_sl", lambda *a: (2200, 2000, 100, 100))
    candles = [{"open": 2000 + i, "high": 2002 + i, "low": 1999 + i,
                "close": 2001 + i, "volume": 100} for i in range(100)]
    regime = SimpleNamespace(model_weights={"pulse1": 0.2}, regime="TRANSITION",
                             is_ath_zone=False, min_rr=0.5, adx=20, session="london",
                             rsi_trend_boost=False, allowed_directions=["BUY", "SELL"])
    stub("services.ml_prediction_service", _compute_technical_indicators=lambda *a: {
        "rsi_14": 65, "macd_hist": 1, "atr_14": 10, "ema_20": 2050})
    stub("services.market_data_service", get_ohlcv_data=AsyncMock(return_value=candles))
    stub("services.data_fetcher", fetch_latest_price=AsyncMock(return_value=2100))
    stub("services.harmonic_pattern_service", get_pattern_adjustment=AsyncMock(return_value={"patterns": []}))
    stub("services.market_regime_service", detect_regime=AsyncMock(return_value=regime),
         check_fake_signal_timeout=AsyncMock(return_value=(False, None, None)),
         filter_signal_by_regime=lambda signal, _: (signal, False, None),
         interpret_rsi=lambda *a: {"action": "none"})
    log = AsyncMock()
    stub("services.prediction_logger", log_prediction=log)
    stub("services.rebound_filter_service", analyze_rebound=AsyncMock(return_value=None))
    stub("services.macro_context_service", commentary_lines=lambda *a, **kw: [])

    result = asyncio.run(panel.get_pulse_analysis("XAUUSD", refresh=True))
    assert "error" not in result, result
    assert result["signal"] == expected
    if expected == "HOLD":
        assert result["signal_type"] == "HOLD"
        assert any("issue #17" in note for note in result["decision_notes"])
        log.assert_not_awaited()
    else:
        assert result["signal_type"] == "CONFIRM"
        log.assert_awaited_once()


def test_canonical_same_bar_ambiguity_is_not_a_winner():
    report = evaluate([row("completed", dict(factors(), same_bar_tp_sl=True))])
    blocked = report["all_resolved_candidates"]["would_block"]
    assert blocked["wins"] == 0 and blocked["losses"] == 1
    assert blocked["canonical"]["ambiguous"] == 1
