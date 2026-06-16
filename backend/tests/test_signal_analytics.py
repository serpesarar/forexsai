import sys
from pathlib import Path

import pytest


backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from services.signal_analytics import classify_signal, normalize_model_type, parse_targets_hit, resolved_exit_price, summarize_scope


def test_parse_targets_hit_decodes_stringified_jsonb_payload():
    raw_targets_hit = '"{\\"TP1\\": true, \\"TP2\\": false, \\"TP3\\": false}"'

    assert parse_targets_hit(raw_targets_hit) == {"TP1": True, "TP2": False, "TP3": False}


def test_classify_signal_uses_hit_target_floor_when_realized_exit_is_negative():
    signal = {
        "symbol": "NDX.INDX",
        "ml_direction": "BUY",
        "status": "completed",
        "ml_entry_price": 100.0,
        "exit_price": 85.0,
        "highest_profit_pips": 30.0,
        "targets_hit": '"{\\"TP1\\": true, \\"TP2\\": true, \\"TP3\\": false, \\"TP4\\": false}"',
        "targets": '"{\\"TP1\\": 115.0, \\"TP2\\": 125.0, \\"TP3\\": 135.0, \\"TP4\\": 150.0}"',
    }

    # Canonical NDX geometry is a flat 30-pip ladder; stored targets are ignored.
    assert classify_signal(signal) == ("completed", True, 30.0)


def test_classify_signal_prefers_realized_exit_over_peak_excursion_for_completed_rows():
    signal = {
        "symbol": "NDX.INDX",
        "ml_direction": "BUY",
        "status": "completed",
        "ml_entry_price": 100.0,
        "exit_price": 110.0,
        "highest_profit_pips": 150.0,
        "targets_hit": {},
        "targets": {},
    }

    assert classify_signal(signal) == ("completed", True, 10.0)


def test_classify_signal_uses_highest_hit_target_floor_for_completed_target_rows():
    signal = {
        "symbol": "GDAXI.INDX",
        "ml_direction": "BUY",
        "status": "completed",
        "ml_entry_price": 23000.0,
        "exit_price": 23703.3,
        "highest_profit_pips": 703.3,
        "targets_hit": {"TP1": True, "TP2": True, "TP3": False, "TP4": False},
        "targets": {"TP1": 23015.0, "TP2": 23025.0, "TP3": 23035.0, "TP4": 23050.0},
    }

    assert classify_signal(signal) == ("completed", True, 30.0)


def test_resolved_exit_price_prefers_highest_hit_target_for_completed_rows():
    signal = {
        "symbol": "GDAXI.INDX",
        "ml_direction": "BUY",
        "status": "completed",
        "ml_entry_price": 23000.0,
        "exit_price": 23703.3,
        "highest_profit_pips": 703.3,
        "targets_hit": {"TP1": True, "TP2": True, "TP3": False, "TP4": False},
        "targets": {"TP1": 23015.0, "TP2": 23025.0, "TP3": 23035.0, "TP4": 23050.0},
    }

    # Canonical GDAXI ladder is flat +30 → highest hit (TP2) resolves to 23030.0.
    assert resolved_exit_price(signal) == pytest.approx(23030.0, abs=0.0001)


def test_hourly_completed_rows_use_canonical_fixed_targets_when_stored_geometry_is_inflated():
    signal = {
        "symbol": "GDAXI.INDX",
        "timeframe": "1h",
        "ml_direction": "BUY",
        "status": "completed",
        "resolution_reason": "tp4_hit",
        "ml_entry_price": 23591.8,
        "exit_price": 23736.1562,
        "highest_profit_pips": 144.4,
        "targets_hit": {"TP1": True, "TP2": True, "TP3": True, "TP4": True},
        "targets": {"TP1": 23656.1562, "TP2": 23666.1562, "TP3": 23676.1562, "TP4": 23736.1562},
    }

    assert classify_signal(signal) == ("completed", True, 30.0)
    assert resolved_exit_price(signal) == pytest.approx(23621.8, abs=0.0001)


def test_hourly_stopped_rows_use_canonical_fixed_stop_loss_when_stored_loss_is_inflated():
    signal = {
        "symbol": "GDAXI.INDX",
        "timeframe": "1h",
        "ml_direction": "BUY",
        "status": "stopped",
        "ml_entry_price": 23591.8,
        "exit_price": 23447.4328,
        "stop_loss_pips": 144.4,
        "highest_profit_pips": 0.0,
        "lowest_drawdown_pips": -144.4,
        "targets_hit": {},
        "targets": {"TP1": 23656.1562, "TP2": 23666.1562, "TP3": 23676.1562, "TP4": 23736.1562},
    }

    assert classify_signal(signal) == ("stopped", False, -50.0)
    assert resolved_exit_price(signal) == pytest.approx(23541.8, abs=0.0001)


@pytest.mark.parametrize(
    ("signal", "expected_profit", "expected_exit_price"),
    [
        (
            {
                "symbol": "NDX.INDX",
                "timeframe": "1h",
                "ml_direction": "BUY",
                "status": "completed",
                "resolution_reason": "tp4_hit",
                "ml_entry_price": 25000.0,
                "exit_price": 25150.0,
                "highest_profit_pips": 150.0,
                "targets_hit": {"TP1": True, "TP2": True, "TP3": True, "TP4": True},
                "targets": {"TP1": 25115.0, "TP2": 25125.0, "TP3": 25135.0, "TP4": 25150.0},
            },
            30.0,
            25030.0,
        ),
        (
            {
                "symbol": "XAUUSD",
                "timeframe": "1h",
                "ml_direction": "BUY",
                "status": "completed",
                "resolution_reason": "tp4_hit",
                "ml_entry_price": 2900.0,
                "exit_price": 2951.6,
                "highest_profit_pips": 51.6,
                "targets_hit": {"TP1": True, "TP2": True, "TP3": True, "TP4": True},
                "targets": {"TP1": 2919.6, "TP2": 2926.6, "TP3": 2936.6, "TP4": 2951.6},
            },
            40.0,
            2940.0,
        ),
        (
            {
                "symbol": "USOIL.FOREX",
                "timeframe": "1h",
                "ml_direction": "BUY",
                "status": "completed",
                "resolution_reason": "tp4_hit",
                "ml_entry_price": 70.0,
                "exit_price": 70.35,
                "highest_profit_pips": 0.35,
                "targets_hit": {"TP1": True, "TP2": True, "TP3": True, "TP4": True},
                "targets": {"TP1": 70.294, "TP2": 70.308, "TP3": 70.322, "TP4": 70.35},
            },
            0.35,
            70.35,
        ),
    ],
)
def test_hourly_completed_rows_use_canonical_fixed_targets_for_all_symbols(signal, expected_profit, expected_exit_price):
    classified_status, win, pnl = classify_signal(signal)

    assert (classified_status, win) == ("completed", True)
    assert pnl == pytest.approx(expected_profit, abs=0.0001)
    assert resolved_exit_price(signal) == pytest.approx(expected_exit_price, abs=0.0001)


@pytest.mark.parametrize(
    ("signal", "expected_loss", "expected_exit_price"),
    [
        (
            {
                "symbol": "NDX.INDX",
                "timeframe": "1h",
                "ml_direction": "BUY",
                "status": "stopped",
                "ml_entry_price": 25000.0,
                "exit_price": 24850.0,
                "stop_loss_pips": 150.0,
                "highest_profit_pips": 0.0,
                "lowest_drawdown_pips": -150.0,
                "targets_hit": {},
                "targets": {"TP1": 25115.0, "TP2": 25125.0, "TP3": 25135.0, "TP4": 25150.0},
            },
            -50.0,
            24950.0,
        ),
        (
            {
                "symbol": "XAUUSD",
                "timeframe": "1h",
                "ml_direction": "BUY",
                "status": "stopped",
                "ml_entry_price": 2900.0,
                "exit_price": 2873.4,
                "stop_loss_pips": 26.6,
                "highest_profit_pips": 0.0,
                "lowest_drawdown_pips": -26.6,
                "targets_hit": {},
                "targets": {"TP1": 2919.6, "TP2": 2926.6, "TP3": 2936.6, "TP4": 2951.6},
            },
            -15.0,
            2885.0,
        ),
        (
            {
                "symbol": "USOIL.FOREX",
                "timeframe": "1h",
                "ml_direction": "BUY",
                "status": "stopped",
                "ml_entry_price": 70.0,
                "exit_price": 69.685,
                "stop_loss_pips": 0.315,
                "highest_profit_pips": 0.0,
                "lowest_drawdown_pips": -0.315,
                "targets_hit": {},
                "targets": {"TP1": 70.294, "TP2": 70.308, "TP3": 70.322, "TP4": 70.35},
            },
            -0.21,
            69.79,
        ),
    ],
)
def test_hourly_stopped_rows_use_canonical_fixed_stop_loss_for_all_symbols(signal, expected_loss, expected_exit_price):
    classified_status, win, pnl = classify_signal(signal)

    assert (classified_status, win) == ("stopped", False)
    assert pnl == pytest.approx(expected_loss, abs=0.0001)
    assert resolved_exit_price(signal) == pytest.approx(expected_exit_price, abs=0.0001)


def test_summarize_scope_excludes_expired_rows_from_scored_outcomes():
    rows = [
        {
            "symbol": "NDX.INDX",
            "ml_direction": "BUY",
            "status": "completed",
            "ml_entry_price": 100.0,
            "exit_price": 110.0,
            "highest_profit_pips": 10.0,
            "targets_hit": {},
            "targets": {},
        },
        {
            "symbol": "NDX.INDX",
            "ml_direction": "BUY",
            "status": "expired",
            "ml_entry_price": 100.0,
            "exit_price": None,
            "highest_profit_pips": 0.0,
            "targets_hit": {},
            "targets": {},
        },
    ]

    summary = summarize_scope(rows)

    assert summary["scored_signals"] == 1
    assert summary["completed"] == 1
    assert summary["expired"] == 1
    assert summary["net_pips"] == pytest.approx(10.0, abs=0.1)


def test_normalize_model_type_maps_smart_money_strategy_to_smc():
    signal = {"model_type": "ml", "strategy": "SMART_MONEY_ZONES"}

    assert normalize_model_type(signal) == "smc"


def test_normalize_model_type_maps_order_block_aliases_to_smc():
    signal = {"model_type": "order_blocks", "strategy": None}

    assert normalize_model_type(signal) == "smc"


def test_normalize_model_type_collapses_scoped_ml_model_types_to_ml():
    assert normalize_model_type({"model_type": "ml:main", "strategy": "main"}) == "ml"
    assert normalize_model_type({"model_type": "ml:balanced", "strategy": "balanced"}) == "ml"