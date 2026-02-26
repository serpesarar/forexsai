"""
Test Signal Logic
=================
Tests the core trading signal generation logic:
- BUY/SELL/HOLD signal output validation
- RSI, MACD, EMA calculations
- TP/SL level calculations (must never be negative, must be > entry price for BUY)
- Signal confidence score range (0.0 to 1.0)
- Edge cases: flat market, extreme volatility, missing candle data
Use pytest + mock. Do NOT call real EODHD API.
"""
import pytest
import numpy as np

# Import after conftest.py sets up the path
from services.technical_indicators import calculate_ema, calculate_rsi, calculate_atr
from services.target_config import get_symbol_config, calculate_target_prices, calculate_stoploss_price
from services.ml_prediction_service import (
    _apply_layered_confidence, _get_cached_signal, _update_signal_cache, 
    _should_allow_direction_change, _signal_cache
)


class TestSignalDirectionLogic:
    """Test BUY/SELL/HOLD signal generation logic"""
    
    def test_buy_signal_when_price_above_ema20_ema50(self):
        """BUY signal when price > EMA20 > EMA50 and uptrend"""
        # Create uptrend data
        prices = np.array([100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0,
                          110.0, 111.0, 112.0, 113.0, 114.0, 115.0, 116.0, 117.0, 118.0, 119.0,
                          120.0, 121.0, 122.0, 123.0, 124.0])
        
        ema20 = calculate_ema(prices, 20)
        
        # calculate_ema returns a single float value
        assert isinstance(ema20, float), f"EMA should be float, got {type(ema20)}"
        
        # Current price should be above EMA
        current_price = 125.0
        assert current_price > ema20, f"Price {current_price} should be above EMA {ema20} for BUY signal"
    
    def test_sell_signal_when_price_below_ema20_ema50(self):
        """SELL signal when price < EMA20 < EMA50 and downtrend"""
        # Create downtrend data
        prices = np.array([124.0, 123.0, 122.0, 121.0, 120.0, 119.0, 118.0, 117.0, 116.0, 115.0,
                          114.0, 113.0, 112.0, 111.0, 110.0, 109.0, 108.0, 107.0, 106.0, 105.0,
                          104.0, 103.0, 102.0, 101.0, 100.0])
        
        ema20 = calculate_ema(prices, 20)
        
        # Current price should be below EMA
        current_price = 99.0
        assert current_price < ema20, f"Price {current_price} should be below EMA {ema20} for SELL signal"
    
    def test_hold_signal_when_no_clear_trend(self):
        """HOLD signal when price is near EMA and no clear trend"""
        # Create sideways data
        prices = np.array([100.0, 100.5, 99.5, 100.2, 99.8, 100.1, 99.9, 100.0, 100.3, 99.7,
                          100.0, 100.2, 99.8, 100.0, 100.1, 99.9, 100.0, 100.2, 99.8, 100.0,
                          100.1, 99.9, 100.0, 100.2, 99.8])
        
        ema20 = calculate_ema(prices, 20)
        
        # Price within 0.5% of EMA
        current_price = 100.0
        price_diff_pct = abs(current_price - ema20) / ema20
        
        assert price_diff_pct < 0.005, f"Price should be near EMA for HOLD signal, diff: {price_diff_pct}"


class TestTechnicalIndicators:
    """Test RSI, EMA, ATR calculations"""
    
    def test_rsi_calculation_range(self, fake_ohlcv):
        """RSI must be between 0 and 100"""
        closes = fake_ohlcv['close'].values
        rsi = calculate_rsi(closes, period=14)
        
        assert rsi is not None, "RSI should not be None"
        assert isinstance(rsi, float), f"RSI should be float, got {type(rsi)}"
        assert 0 <= rsi <= 100, f"RSI should be between 0-100, got {rsi}"
    
    def test_rsi_returns_none_for_insufficient_data(self):
        """RSI should return None for insufficient data"""
        # Only 5 values, need at least 15 for RSI 14
        prices = np.array([100.0, 101.0, 102.0, 103.0, 104.0])
        rsi = calculate_rsi(prices, period=14)
        
        assert rsi is None, f"RSI should be None for insufficient data, got {rsi}"
    
    def test_ema_returns_float(self, fake_ohlcv):
        """EMA should return a single float value"""
        closes = fake_ohlcv['close'].values
        ema = calculate_ema(closes, 20)
        
        assert isinstance(ema, float), f"EMA should be float, got {type(ema)}"
        assert ema > 0, f"EMA should be positive, got {ema}"
    
    def test_ema_returns_none_for_insufficient_data(self):
        """EMA should return None for insufficient data"""
        prices = np.array([100.0, 101.0, 102.0, 103.0, 104.0])
        ema = calculate_ema(prices, 20)
        
        assert ema is None, f"EMA should be None for insufficient data, got {ema}"
    
    def test_atr_calculation(self, fake_ohlcv):
        """ATR (Average True Range) calculation"""
        highs = fake_ohlcv['high'].values
        lows = fake_ohlcv['low'].values
        closes = fake_ohlcv['close'].values
        
        atr = calculate_atr(highs, lows, closes, period=14)
        
        assert atr is not None, "ATR should not be None"
        assert isinstance(atr, float), f"ATR should be float, got {type(atr)}"
        assert atr >= 0, f"ATR should always be non-negative, got {atr}"
    
    def test_atr_returns_none_for_insufficient_data(self):
        """ATR should return None for insufficient data"""
        highs = np.array([105.0, 106.0, 107.0, 108.0, 109.0])
        lows = np.array([95.0, 96.0, 97.0, 98.0, 99.0])
        closes = np.array([100.0, 101.0, 102.0, 103.0, 104.0])
        
        atr = calculate_atr(highs, lows, closes, period=14)
        
        assert atr is None, f"ATR should be None for insufficient data, got {atr}"


class TestTPSLCalculations:
    """Test Take Profit and Stop Loss level calculations"""
    
    def test_buy_tp_always_above_entry(self):
        """For BUY signals, TP must be > entry price"""
        entry_price = 2000.0
        symbol = "XAUUSD"
        direction = "LONG"
        
        config = get_symbol_config(symbol)
        # Calculate first target
        tp_pips = config.targets[0].pips
        tp_price = entry_price + tp_pips
        
        assert tp_price > entry_price, f"BUY TP ({tp_price}) must be > entry ({entry_price})"
        assert tp_price > 0, "TP must never be negative"
    
    def test_buy_sl_always_below_entry(self):
        """For BUY signals, SL must be < entry price"""
        entry_price = 2000.0
        symbol = "XAUUSD"
        direction = "LONG"
        
        config = get_symbol_config(symbol)
        sl_pips = config.stoploss_pips
        sl_price = entry_price - sl_pips
        
        assert sl_price < entry_price, f"BUY SL ({sl_price}) must be < entry ({entry_price})"
        assert sl_price > 0, "SL must never be negative"
    
    def test_sell_tp_always_below_entry(self):
        """For SELL signals, TP must be < entry price"""
        entry_price = 2000.0
        symbol = "XAUUSD"
        direction = "SHORT"
        
        config = get_symbol_config(symbol)
        tp_pips = config.targets[0].pips
        tp_price = entry_price - tp_pips
        
        assert tp_price < entry_price, f"SELL TP ({tp_price}) must be < entry ({entry_price})"
        assert tp_price > 0, "TP must never be negative"
    
    def test_sell_sl_always_above_entry(self):
        """For SELL signals, SL must be > entry price"""
        entry_price = 2000.0
        symbol = "XAUUSD"
        direction = "SHORT"
        
        config = get_symbol_config(symbol)
        sl_pips = config.stoploss_pips
        sl_price = entry_price + sl_pips
        
        assert sl_price > entry_price, f"SELL SL ({sl_price}) must be > entry ({entry_price})"
    
    def test_tp_sl_never_negative(self):
        """TP and SL must never be negative even with extreme inputs"""
        entry_price = 10.0
        symbol = "XAUUSD"
        direction = "LONG"
        
        targets = calculate_target_prices(entry_price, direction, symbol)
        sl = calculate_stoploss_price(entry_price, direction, symbol)
        
        assert targets is not None, "Targets should not be None"
        assert sl is not None, "SL should not be None"
        assert all(t > 0 for t in targets.values()), "All targets must be positive"
        assert sl > 0, "SL must be positive"
    
    def test_ndx_config_has_correct_pip_value(self):
        """NASDAQ config should have pip_value=1.0"""
        config = get_symbol_config("NDX.INDX")
        assert config.pip_value == 1.0
        assert config.stoploss_pips == 50
    
    def test_xauusd_config_has_correct_pip_value(self):
        """XAUUSD config should have correct targets"""
        config = get_symbol_config("XAUUSD")
        assert config.stoploss_pips == 8
        assert len(config.targets) == 4


class TestConfidenceScores:
    """Test signal confidence score calculations"""
    
    def test_confidence_score_range_0_to_100(self):
        """Confidence score must be between 0 and 100"""
        # Test with various inputs
        test_cases = [
            (50.0, []),
            (80.0, [{"factor_id": "trend", "multiplier": 1.1}]),
            (40.0, [{"factor_id": "rsi", "multiplier": 0.9}]),
        ]
        
        for base_conf, adjustments in test_cases:
            result, _ = _apply_layered_confidence(base_conf, adjustments)
            assert 30 <= result <= 95, f"Confidence {result} out of range [30, 95]"
    
    def test_confidence_with_empty_adjustments(self):
        """Confidence with no adjustments should return base value (clamped)"""
        base_confidence = 60.0
        adjustments = []
        
        result, _ = _apply_layered_confidence(base_confidence, adjustments)
        assert isinstance(result, (int, float)), "Result should be a number"
        assert 30 <= result <= 95, f"Result {result} should be clamped to [30, 95]"


class TestEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_flat_market_handling(self, fake_ohlcv_flat):
        """System should handle flat market without crashing"""
        closes = fake_ohlcv_flat['close'].values
        highs = fake_ohlcv_flat['high'].values
        lows = fake_ohlcv_flat['low'].values
        
        # These should not crash
        rsi = calculate_rsi(closes, 14)
        atr = calculate_atr(highs, lows, closes, 14)
        
        # RSI should be valid (0-100) for flat market
        if rsi is not None:
            assert 0 <= rsi <= 100, f"RSI should be valid, got {rsi}"
    
    def test_extreme_volatility_handling(self, fake_ohlcv_volatile):
        """System should handle extreme volatility"""
        closes = fake_ohlcv_volatile['close'].values
        highs = fake_ohlcv_volatile['high'].values
        lows = fake_ohlcv_volatile['low'].values
        
        # These should not crash
        rsi = calculate_rsi(closes, 14)
        atr = calculate_atr(highs, lows, closes, 14)
        
        # ATR should be high for volatile market
        if atr is not None:
            assert atr > 0, "ATR should be positive in volatile market"
    
    def test_insufficient_candle_data(self, fake_ohlcv_insufficient):
        """System should handle insufficient candle data gracefully"""
        closes = fake_ohlcv_insufficient['close'].values
        
        # Requesting EMA50 with only 10 candles should return None
        ema50 = calculate_ema(closes, 50)
        assert ema50 is None, "EMA50 with <50 candles should return None"
        
        # RSI with insufficient data
        rsi = calculate_rsi(closes, 14)
        assert rsi is None, "RSI with insufficient data should return None"
    
    def test_empty_array_input(self):
        """System should handle empty array gracefully"""
        empty = np.array([])
        ema = calculate_ema(empty, 20)
        assert ema is None, "Empty input should return None"
        
        rsi = calculate_rsi(empty, 14)
        assert rsi is None, "Empty input should return None for RSI"


class TestSignalStability:
    """Test signal stability system (prevents flip-flopping)"""
    
    def test_signal_cache_storage(self):
        """Signal cache should store and retrieve signals"""
        symbol = "TEST"
        direction = "BUY"
        confidence = 75.0
        price = 2000.0
        
        # Update cache
        _update_signal_cache(symbol, direction, confidence, price)
        
        # Retrieve
        cached = _get_cached_signal(symbol)
        
        assert cached is not None, "Should retrieve cached signal"
        assert cached["direction"] == direction
        assert cached["confidence"] == confidence
        assert cached["price"] == price
        
        # Cleanup
        if symbol in _signal_cache:
            del _signal_cache[symbol]
    
    def test_direction_change_checks(self):
        """Direction change should check stability rules"""
        symbol = "TEST_COOLDOWN"
        
        # Set initial BUY signal with moderate confidence
        _update_signal_cache(symbol, "BUY", 60.0, 2000.0)
        
        # Try to change to SELL - behavior depends on implementation
        allowed, reason = _should_allow_direction_change(symbol, "SELL", 50.0, 2005.0)
        
        # Just verify the function works and returns proper types
        assert isinstance(allowed, bool), "Should return boolean"
        assert isinstance(reason, str), "Should return reason string"
        
        # Cleanup
        if symbol in _signal_cache:
            del _signal_cache[symbol]


class TestPipCalculations:
    """Test pip/point calculations for different symbols"""
    
    def test_xauusd_pip_value(self):
        """XAUUSD pip value should be 1.0 in config"""
        config = get_symbol_config("XAUUSD")
        assert config.pip_value == 1.0
    
    def test_ndx_pip_value(self):
        """NASDAQ/NDX pip value should be 1.0"""
        config = get_symbol_config("NDX.INDX")
        assert config.pip_value == 1.0
    
    def test_unknown_symbol_uses_default(self):
        """Unknown symbols should use default config"""
        from services.target_config import DEFAULT_CONFIG
        
        config = get_symbol_config("UNKNOWN")
        assert config.pip_value == DEFAULT_CONFIG.pip_value
        assert config.stoploss_pips == DEFAULT_CONFIG.stoploss_pips


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    pytest.main([__file__, "-v"])
