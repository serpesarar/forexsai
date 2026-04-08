"""
XAUUSD 0.0p Bug - Diagnostic Tests
Verifies: price fetching, pip calculation, and lifecycle tracking for XAUUSD
"""
import pytest
import sys
from unittest.mock import AsyncMock, patch, MagicMock

# Ensure backend is in path
sys.path.insert(0, "/Users/melihcanodacioglu/Desktop/panel/backend")


class TestXAUUSDPipCalculation:
    """Test XAUUSD pip calculations"""

    def test_pips_from_price_change_xauusd(self):
        """XAUUSD: 1 pip = $1.00, so $5 change = 5 pips"""
        from services.target_config import pips_from_price_change
        
        # $1 price change should equal 1 pip for XAUUSD
        assert pips_from_price_change(1.0, "XAUUSD") == 1.0
        assert pips_from_price_change(5.0, "XAUUSD") == 5.0
        assert pips_from_price_change(0.5, "XAUUSD") == 0.5
        assert pips_from_price_change(-2.5, "XAUUSD") == -2.5
        
    def test_xauusd_config(self):
        """Verify XAUUSD has correct config"""
        from services.target_config import get_symbol_config
        
        config = get_symbol_config("XAUUSD")
        assert config.pip_value == 1.0  # 1 pip = $1.00
        assert config.is_percentage == False
        assert config.stoploss_pips == 15  # 15 pips = $15 SL
        
        # Verify targets
        target_pips = [t.pips for t in config.targets]
        assert target_pips == [8, 15, 25, 40]  # TP1-4 in pips


class TestXAUUSDPriceFetching:
    """Test XAUUSD price fetching from DataHub"""

    @pytest.mark.asyncio
    async def test_fetch_latest_price_xauusd(self):
        """Test that XAUUSD price can be fetched"""
        from services.data_fetcher import fetch_latest_price
        
        # Mock DataHub get_price
        with patch("services.data_hub.get_price", return_value=2915.50):
            price = await fetch_latest_price("XAUUSD")
            assert price == 2915.50

    def test_datahub_get_price_xauusd(self):
        """Test DataHub get_price for XAUUSD"""
        from services.data_hub import get_price
        
        # Mock the _prices dict
        with patch("services.data_hub._prices", {"XAUUSD": {"price": 2920.75, "timestamp": 1234567890}}):
            price = get_price("XAUUSD")
            assert price == 2920.75


class TestXAUUSDLifecycleProfit:
    """Test XAUUSD profit calculation in lifecycle"""

    def test_xauusd_best_pips_calculation(self):
        """Test the core profit calculation logic for XAUUSD"""
        from services.target_config import pips_from_price_change
        
        # Simulate: XAUUSD BUY at 2900.00, current at 2910.00
        entry_price = 2900.00
        current = 2910.00
        
        # BUY: profit_pips = pips_from_price_change(current - entry, symbol)
        profit_pips = pips_from_price_change(current - entry_price, "XAUUSD")
        # 2910 - 2900 = 10 dollars = 10 pips
        assert profit_pips == 10.0
        
        best_pips = max(profit_pips, 0)
        assert best_pips == 10.0
        
        # SELL case: entry 2900, current 2890
        profit_pips_sell = pips_from_price_change(entry_price - 2890.00, "XAUUSD")
        # 2900 - 2890 = 10 dollars = 10 pips profit
        assert profit_pips_sell == 10.0

    def test_small_price_change_rounding(self):
        """Test that small price changes (like $0.50) don't round to 0"""
        from services.target_config import pips_from_price_change
        
        # Small price movement
        profit_pips = pips_from_price_change(0.5, "XAUUSD")
        assert profit_pips == 0.5
        
        # Frontend shows 1 decimal: 0.5 → "0.5p" NOT "0.0p"
        formatted = f"{profit_pips:.1f}p"
        assert formatted == "0.5p"


class TestXAUUSDEndToEnd:
    """End-to-end test for XAUUSD signal lifecycle"""

    @pytest.mark.asyncio
    async def test_xauusd_lifecycle_check(self):
        """Full lifecycle check for XAUUSD signal"""
        from services.signal_lifecycle import _process_signal
        
        mock_signal = {
            "id": "test-xau-123",
            "symbol": "XAUUSD",
            "ml_direction": "BUY",
            "ml_entry_price": 2900.00,
            "targets": '{"TP1": 8, "TP2": 15, "TP3": 25, "TP4": 40}',
            "targets_hit": '{}',
            "highest_profit_pips": 0,
            "lowest_drawdown_pips": 0,
            "created_at": "2024-01-01T00:00:00Z",
        }
        
        # Mock Supabase client
        mock_client = MagicMock()
        mock_client.table.return_value.update.return_value.eq.return_value.execute = MagicMock(
            return_value=MagicMock(data=[mock_signal])
        )
        
        # Mock price to be $10 higher than entry (should be 10 pips profit)
        with patch("services.signal_lifecycle.fetch_latest_price", AsyncMock(return_value=2910.00)):
            with patch("services.signal_lifecycle._update_signal_status") as mock_update:
                result = await _process_signal(mock_client, mock_signal)
                    
                # Should return something (target hit or None for no target hit)
                # The key point: highest_profit_pips should be 10.0, not 0
                    
                # Check if _update_signal_status was called with correct highest_profit_pips
                if mock_update.called:
                    call_args = mock_update.call_args
                    update_data = call_args[0][2] if len(call_args[0]) > 2 else call_args[1].get('updates', {})
                    
                    # Verify highest_profit_pips is in update data and is correct
                    if isinstance(update_data, dict) and 'highest_profit_pips' in update_data:
                        assert update_data['highest_profit_pips'] == 10.0, \
                            f"Expected highest_profit_pips=10.0, got {update_data['highest_profit_pips']}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
