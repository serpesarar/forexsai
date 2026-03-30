import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from services.smc_calculator_service import determine_market_structure


def test_determine_market_structure_detects_down_choch_after_prior_bullish_trend():
    swing_highs = [
        {"index": 1, "price": 100.0},
        {"index": 5, "price": 105.0},
        {"index": 9, "price": 110.0},
    ]
    swing_lows = [
        {"index": 2, "price": 90.0},
        {"index": 6, "price": 95.0},
        {"index": 10, "price": 92.0},
    ]

    result = determine_market_structure(swing_highs, swing_lows, 101.0)

    assert result["current_trend"] == "ranging"
    assert result["last_bos"] == {"direction": "up", "price": 110.0, "confirmed": True}
    assert result["last_choch"] == {"direction": "down", "price": 92.0, "confirmed": True}


def test_determine_market_structure_detects_up_choch_after_prior_bearish_trend():
    swing_highs = [
        {"index": 1, "price": 110.0},
        {"index": 5, "price": 105.0},
        {"index": 9, "price": 108.0},
    ]
    swing_lows = [
        {"index": 2, "price": 100.0},
        {"index": 6, "price": 95.0},
        {"index": 10, "price": 92.0},
    ]

    result = determine_market_structure(swing_highs, swing_lows, 101.0)

    assert result["current_trend"] == "ranging"
    assert result["last_bos"] == {"direction": "up", "price": 108.0, "confirmed": True}
    assert result["last_choch"] == {"direction": "up", "price": 108.0, "confirmed": True}
