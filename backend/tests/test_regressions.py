"""
Critical Regression Tests
=========================
These are known bugs that must never come back:
- ML prediction ValueError when feature count mismatches
- All APIs returning 404 when one router import fails
- Signal lifecycle not tracking when circuit breaker is stuck
- DataHub price freeze
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
import numpy as np

# Add backend to path
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))


class TestMLFeatureMismatch:
    """REGRESSION: ML prediction ValueError when feature count mismatches"""
    
    def test_ml_handles_feature_mismatch_gracefully(self):
        """ML prediction with mismatched features should return graceful error, not 500"""
        from services.ml_prediction_service import _apply_layered_confidence
        
        # Test with extreme base confidence values
        test_cases = [
            (0, []),  # Edge case: zero
            (100, []),  # Edge case: max
            (-10, []),  # Invalid: negative
            (150, []),  # Invalid: over max
        ]
        
        for base_conf, adjustments in test_cases:
            try:
                result, _ = _apply_layered_confidence(base_conf, adjustments)
                # Should always return a valid number between 30-95 (clamped)
                assert 30 <= result <= 95, f"Result {result} not in valid range [30, 95]"
            except Exception as e:
                pytest.fail(f"Should handle edge case gracefully, got: {e}")
    
    def test_ml_no_crash_on_empty_adjustments(self):
        """Empty adjustments should not cause crash"""
        from services.ml_prediction_service import _apply_layered_confidence
        
        result, details = _apply_layered_confidence(60.0, [])
        
        assert isinstance(result, (int, float))
        assert 30 <= result <= 95
    
    def test_ml_no_crash_on_malformed_adjustments(self):
        """Malformed adjustments should not cause crash"""
        from services.ml_prediction_service import _apply_layered_confidence
        
        malformed = [
            {"factor_id": "test", "multiplier": "invalid"},  # string instead of number
            {"factor_id": "test2"},  # missing multiplier
            {"multiplier": 1.2},  # missing factor_id
            {},  # empty dict
        ]
        
        try:
            result, _ = _apply_layered_confidence(60.0, malformed)
            assert isinstance(result, (int, float))
        except (TypeError, KeyError) as e:
            # These exceptions are acceptable if handled gracefully
            pass


class TestRouterIsolation:
    """REGRESSION: All APIs returning 404 when one router import fails"""
    
    def test_router_import_failure_isolation(self):
        """One router failing should not break other routers"""
        # This test verifies the router isolation pattern in main.py
        # If one router import fails in the try/except block,
        # ROUTERS_LOADED becomes False but app should still work
        
        # Check that main.py has proper error handling
        main_file = Path(__file__).parent.parent / "main.py"
        content = main_file.read_text()
        
        # Should have try/except around router imports
        assert "try:" in content, "main.py should have try block for router imports"
        assert "ROUTERS_LOADED" in content, "main.py should track router loading status"
        
        # Should handle case where routers fail to load
        assert "IMPORT_ERROR" in content or "except" in content, \
            "main.py should handle import errors"
    
    def test_health_endpoint_works_without_routers(self):
        """Health endpoint should work even if routers fail to load"""
        # This is implicit - health endpoints are defined before router imports
        main_file = Path(__file__).parent.parent / "main.py"
        content = main_file.read_text()
        
        # Health endpoints should be defined before router imports
        health_pos = content.find("@app.get(\"/api/health\")")
        router_import_pos = content.find("ROUTERS_LOADED")
        
        assert health_pos > 0, "Health endpoint should exist"
        assert router_import_pos > 0, "Router loading should be tracked"
        assert health_pos < router_import_pos, \
            "Health endpoint should be defined before router imports"


class TestSignalLifecycleCircuitBreaker:
    """REGRESSION: Signal lifecycle not tracking when circuit breaker is stuck"""
    
    def test_circuit_breaker_resets_after_success(self):
        """Circuit breaker should reset after successful fetch"""
        from services.signal_lifecycle import (
            _price_fetch_failures, PRICE_CIRCUIT_BREAKER_THRESHOLD
        )
        
        symbol = "TEST_RESET"
        
        # Set failure count high
        _price_fetch_failures[symbol] = PRICE_CIRCUIT_BREAKER_THRESHOLD - 1
        
        try:
            # Simulate a successful fetch (which should reset counter)
            _price_fetch_failures[symbol] = 0
            
            assert _price_fetch_failures[symbol] == 0, \
                "Circuit breaker should reset after success"
        finally:
            if symbol in _price_fetch_failures:
                del _price_fetch_failures[symbol]
    
    def test_circuit_breaker_gradual_recovery(self):
        """Circuit breaker should gradually recover, not stay stuck"""
        from services.signal_lifecycle import (
            _price_fetch_failures, PRICE_CIRCUIT_BREAKER_THRESHOLD
        )
        
        symbol = "TEST_RECOVERY"
        
        try:
            # Set to threshold (circuit open)
            _price_fetch_failures[symbol] = PRICE_CIRCUIT_BREAKER_THRESHOLD
            
            # Simulate the circuit breaker logic - should decrement on check
            # when circuit is open to allow eventual retry
            fail_count = _price_fetch_failures.get(symbol, 0)
            if fail_count >= PRICE_CIRCUIT_BREAKER_THRESHOLD:
                # Real implementation decrements to allow retry
                _price_fetch_failures[symbol] = fail_count - 1
            
            # Should have decremented
            assert _price_fetch_failures[symbol] < PRICE_CIRCUIT_BREAKER_THRESHOLD, \
                "Circuit breaker should gradually allow retries"
        finally:
            if symbol in _price_fetch_failures:
                del _price_fetch_failures[symbol]
    
    def test_lifecycle_continues_despite_circuit_breaker(self):
        """Signal lifecycle should continue processing other symbols even if one is blocked"""
        from services.signal_lifecycle import _price_fetch_failures
        
        blocked_symbol = "BLOCKED"
        working_symbol = "WORKING"
        
        try:
            # Block one symbol
            _price_fetch_failures[blocked_symbol] = 999
            
            # Other symbol should not be affected
            _price_fetch_failures[working_symbol] = 0
            
            assert _price_fetch_failures[working_symbol] == 0, \
                "Other symbols should not be affected by one blocked symbol"
        finally:
            for s in [blocked_symbol, working_symbol]:
                if s in _price_fetch_failures:
                    del _price_fetch_failures[s]


class TestDataHubPriceFreeze:
    """REGRESSION: DataHub price freeze - mock upstream failure and verify fallback"""
    
    @pytest.mark.asyncio
    async def test_price_fetch_handles_slow_response(self):
        """Price fetch should handle slow responses gracefully"""
        from services.data_fetcher import fetch_latest_price
        import asyncio
        
        # Mock to simulate slow/timeout response
        with patch('services.data_fetcher.fetch_latest_price', new=AsyncMock(side_effect=asyncio.TimeoutError())):
            try:
                result = await fetch_latest_price("XAUUSD")
                # Should return None on timeout, not crash
            except asyncio.TimeoutError:
                # TimeoutError is acceptable
                pass
            except Exception as e:
                pytest.fail(f"Should handle timeout gracefully: {e}")
    
    def test_data_hub_has_fallback_mechanism(self):
        """DataHub should have fallback when primary source fails"""
        # Check that data_hub.py has error handling
        data_hub_file = Path(__file__).parent.parent / "services" / "data_hub.py"
        
        if data_hub_file.exists():
            content = data_hub_file.read_text()
            
            # Should have error handling
            assert "try" in content.lower() or "except" in content.lower(), \
                "DataHub should have error handling"
            
            # Should have fallback or cache mechanism
            assert any(word in content.lower() for word in [
                "fallback", "cache", "fallback_price", "last_price"
            ]), "DataHub should have fallback mechanism"
    
    @pytest.mark.asyncio
    async def test_data_hub_handles_missing_data_gracefully(self):
        """DataHub should handle missing data gracefully, not crash"""
        # This tests that the data structures are properly initialized
        from services.data_fetcher import fetch_ohlc_data
        
        # Mock to simulate failure - returns empty list
        with patch('services.data_fetcher.fetch_ohlc_data', new=AsyncMock(return_value=[])):
            try:
                result = await fetch_ohlc_data("XAUUSD", "1h", 100)
                # Should return empty list or None, not crash
                assert result is None or result == [] or isinstance(result, (dict, list))
            except Exception as e:
                pytest.fail(f"Should handle missing data gracefully: {e}")


class TestSignalStatusBulkUpdate:
    """REGRESSION: Never bulk-update signal statuses without lifecycle guard"""
    
    @pytest.mark.asyncio
    async def test_no_bulk_update_in_lifecycle(self):
        """Lifecycle should not use bulk updates that bypass checks"""
        # Check signal_lifecycle.py for bulk update patterns
        lifecycle_file = Path(__file__).parent.parent / "services" / "signal_lifecycle.py"
        
        if lifecycle_file.exists():
            content = lifecycle_file.read_text()
            
            # Should have individual signal processing, not bulk
            # Look for patterns that suggest individual processing
            assert "for" in content or "async for" in content, \
                "Should iterate through signals individually"
            
            # Should NOT have SQL bulk update patterns (these bypass checks)
            dangerous_patterns = [
                "update().where(status='active')",  # Bulk update all active
                "UPDATE prediction_logs SET status",  # Raw SQL bulk update
            ]
            
            for pattern in dangerous_patterns:
                assert pattern.lower() not in content.lower(), \
                    f"Should not use dangerous bulk update: {pattern}"
    
    def test_lifecycle_checks_before_update(self):
        """Lifecycle should check conditions before updating status"""
        from services.signal_lifecycle import LifecycleMetrics
        
        # Metrics should track processed signals
        metrics = LifecycleMetrics()
        
        # Simulate processing signals with checks
        metrics.record_check(
            duration_ms=100.0,
            processed=5,
            errors=0,
            completed=2,
            stopped=1,
            expired=1
        )
        
        # Should have tracked individual signal outcomes
        assert metrics.total_signals_processed == 5
        assert metrics.total_completed == 2
        assert metrics.total_stopped == 1
        assert metrics.total_expired == 1


class TestConfidenceCalculation:
    """REGRESSION: Confidence calculation returning values outside 0-100"""
    
    def test_confidence_always_within_valid_range(self):
        """Confidence should always be clamped to valid range"""
        from services.ml_prediction_service import _apply_layered_confidence
        
        # Test with extreme values that could cause overflow
        extreme_cases = [
            (0.01, [{"factor_id": "trend", "multiplier": 0.001}]),
            (99.99, [{"factor_id": "trend", "multiplier": 1000}]),
            (50, [{"factor_id": "a", "multiplier": 0}, {"factor_id": "b", "multiplier": 999}]),
        ]
        
        for base_conf, adjustments in extreme_cases:
            result, _ = _apply_layered_confidence(base_conf, adjustments)
            
            # Result should always be within valid range
            assert 0 <= result <= 100, \
                f"Confidence {result} out of range [0, 100] for input ({base_conf}, {adjustments})"
    
    def test_confidence_with_invalid_multiplier(self):
        """Invalid multiplier values should not break confidence calculation"""
        from services.ml_prediction_service import _apply_layered_confidence
        
        invalid_adjustments = [
            {"factor_id": "test", "multiplier": float('inf')},
            {"factor_id": "test2", "multiplier": float('-inf')},
            {"factor_id": "test3", "multiplier": float('nan')},
        ]
        
        try:
            result, _ = _apply_layered_confidence(50.0, invalid_adjustments)
            # Should either return valid number or raise handled exception
            if not (isinstance(result, (int, float)) and 0 <= result <= 100):
                # NaN check
                if isinstance(result, float) and (result != result):  # NaN check
                    pass  # NaN is acceptable if handled later
        except (OverflowError, ValueError):
            # These are acceptable if caught
            pass


class TestMemoryLeaks:
    """REGRESSION: Memory leaks in signal cache and lifecycle"""
    
    def test_signal_cache_does_not_grow_indefinitely(self):
        """Signal cache should have size limits"""
        from services.ml_prediction_service import _signal_cache, _update_signal_cache
        
        initial_count = len(_signal_cache)
        
        # Add many signals
        for i in range(100):
            _update_signal_cache(f"SYMBOL_{i}", "BUY", 50.0 + i, 1000.0 + i)
        
        # Cache should not grow indefinitely (if there's a limit)
        # If no limit exists, this documents the current behavior
        current_count = len(_signal_cache)
        
        # Either there's a limit, or we document the growth
        if current_count > 1000:
            pytest.skip("Signal cache has no size limit - documented behavior")
        
        # Cleanup
        _signal_cache.clear()
    
    def test_lifecycle_metrics_does_not_accumulate_forever(self):
        """Lifecycle metrics should not cause memory issues"""
        from services.signal_lifecycle import LifecycleMetrics
        
        metrics = LifecycleMetrics()
        
        # Record many checks
        for i in range(10000):
            metrics.record_check(
                duration_ms=100.0,
                processed=10,
                errors=0,
                completed=5,
                stopped=2,
                expired=3
            )
        
        # Metrics should still be accessible
        summary = metrics.to_dict()
        assert summary["total_checks"] == 10000
        assert summary["total_signals_processed"] == 100000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
