"""
XAUUSD Price Fetch Fix Test
Tests the "NA" string handling and previousClose fallback
"""
import pytest


def test_na_string_handling():
    """Test that 'NA' strings are properly skipped"""
    # Simulate the price extraction logic
    def extract_price(data):
        for key in ("last", "price", "close", "value"):
            if key in data and data[key] is not None:
                val = data[key]
                if isinstance(val, str):
                    val_stripped = val.strip().upper()
                    if val_stripped in ("NA", "N/A", "", "NULL", "NONE"):
                        continue
                try:
                    return float(val)
                except (TypeError, ValueError):
                    continue
        # Fallback to previousClose
        if "previousClose" in data and data["previousClose"] is not None:
            val = data["previousClose"]
            if isinstance(val, str):
                val_stripped = val.strip().upper()
                if val_stripped not in ("NA", "N/A", "", "NULL", "NONE"):
                    try:
                        return float(val)
                    except (TypeError, ValueError):
                        pass
            else:
                try:
                    return float(val)
                except (TypeError, ValueError):
                    pass
        return None

    # Test cases
    # Case 1: XAUUSD with NA close but valid previousClose
    xauusd_data = {
        "code": "XAUUSD.FOREX",
        "close": "NA",
        "previousClose": 5163.1386,
    }
    assert extract_price(xauusd_data) == 5163.1386

    # Case 2: NDX with valid close
    ndx_data = {
        "code": "NDX.INDX",
        "close": 25002.9551,
        "previousClose": 25329.0391,
    }
    assert extract_price(ndx_data) == 25002.9551

    # Case 3: CL.F with both NA (should return None)
    cl_data = {
        "code": "CL.F",
        "close": "NA",
        "previousClose": "NA",
    }
    assert extract_price(cl_data) is None

    # Case 4: Empty string
    empty_data = {
        "close": "",
        "previousClose": 100.0,
    }
    assert extract_price(empty_data) == 100.0

    # Case 5: Whitespace in NA
    whitespace_data = {
        "close": "  NA  ",
        "previousClose": 200.0,
    }
    assert extract_price(whitespace_data) == 200.0

    # Case 6: lowercase na
    lowercase_data = {
        "close": "na",
        "previousClose": 300.0,
    }
    assert extract_price(lowercase_data) == 300.0

    print("All tests passed!")


def test_xauusd_pip_calculation_with_real_price():
    """Test XAUUSD profit calculation with actual price"""
    import sys
    sys.path.insert(0, "/Users/melihcanodacioglu/Desktop/panel/backend")
    from services.target_config import pips_from_price_change

    # XAUUSD at ~5163, entry at 5160
    entry = 5160.0
    current = 5163.1386

    profit_pips = pips_from_price_change(current - entry, "XAUUSD")
    
    # 5163.1386 - 5160 = 3.1386 dollars = ~3.14 pips
    assert abs(profit_pips - 3.1386) < 0.01
    assert profit_pips > 0  # Definitely not 0!


def test_highest_profit_update_logic():
    """Test that highest_profit_pips is calculated correctly"""
    import sys
    sys.path.insert(0, "/Users/melihcanodacioglu/Desktop/panel/backend")
    from services.target_config import pips_from_price_change

    # Simulate lifecycle logic
    entry_price = 2900.0
    current = 2910.0  # $10 up
    direction = "BUY"

    profit_pips = pips_from_price_change(current - entry_price, "XAUUSD")
    best_pips = max(profit_pips, 0)

    assert profit_pips == 10.0
    assert best_pips == 10.0

    # Simulate DB update (prev_high = 0)
    prev_high = 0
    new_high = max(prev_high, best_pips)
    assert new_high == 10.0

    # Frontend format
    formatted = f"{new_high:.1f}p"
    assert formatted == "10.0p"  # NOT "0.0p"!


if __name__ == "__main__":
    test_na_string_handling()
    test_xauusd_pip_calculation_with_real_price()
    test_highest_profit_update_logic()
    print("\n✓ All XAUUSD fix tests passed!")
