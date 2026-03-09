import sys
from pathlib import Path


backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from services.signal_analytics import classify_signal, normalize_model_type, parse_targets_hit


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
        "highest_profit_pips": 4.0,
        "targets_hit": '"{\\"TP1\\": true, \\"TP2\\": true, \\"TP3\\": false, \\"TP4\\": false}"',
        "targets": '"{\\"TP1\\": 115.0, \\"TP2\\": 125.0, \\"TP3\\": 135.0, \\"TP4\\": 150.0}"',
    }

    assert classify_signal(signal) == ("completed", True, 25.0)


def test_normalize_model_type_maps_smart_money_strategy_to_smc():
    signal = {"model_type": "ml", "strategy": "SMART_MONEY_ZONES"}

    assert normalize_model_type(signal) == "smc"


def test_normalize_model_type_maps_order_block_aliases_to_smc():
    signal = {"model_type": "order_blocks", "strategy": None}

    assert normalize_model_type(signal) == "smc"


def test_normalize_model_type_collapses_scoped_ml_model_types_to_ml():
    assert normalize_model_type({"model_type": "ml:main", "strategy": "main"}) == "ml"
    assert normalize_model_type({"model_type": "ml:balanced", "strategy": "balanced"}) == "ml"