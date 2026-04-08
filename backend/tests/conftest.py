"""
Pytest Configuration and Shared Fixtures for ForexSAI Backend Tests
"""
import pytest
import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock

# Add backend to path BEFORE any imports
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import asyncio
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List


# =============================================================================
# Fake Data Fixtures
# =============================================================================

@pytest.fixture
def fake_ohlcv():
    """100 candles of synthetic OHLCV data"""
    dates = pd.date_range('2024-01-01', periods=100, freq='5min')
    np.random.seed(42)  # Reproducible
    
    # Generate realistic price movement (random walk with trend)
    base_price = 2000.0
    returns = np.random.normal(0.0001, 0.001, 100)  # Small random returns
    prices = base_price * np.exp(np.cumsum(returns))
    
    # Generate OHLC from close prices
    opens = prices * (1 + np.random.uniform(-0.001, 0.001, 100))
    highs = np.maximum(opens, prices) * (1 + np.random.uniform(0, 0.002, 100))
    lows = np.minimum(opens, prices) * (1 - np.random.uniform(0, 0.002, 100))
    closes = prices
    volumes = np.random.randint(1000, 10000, 100)
    
    return pd.DataFrame({
        'open': opens,
        'high': highs,
        'low': lows,
        'close': closes,
        'volume': volumes
    }, index=dates)


@pytest.fixture
def fake_ohlcv_flat():
    """50 candles of flat market (for edge case testing)"""
    dates = pd.date_range('2024-01-01', periods=50, freq='5min')
    base = 2000.0
    return pd.DataFrame({
        'open': np.full(50, base),
        'high': np.full(50, base + 0.5),
        'low': np.full(50, base - 0.5),
        'close': np.full(50, base),
        'volume': np.random.randint(1000, 2000, 50)
    }, index=dates)


@pytest.fixture
def fake_ohlcv_volatile():
    """50 candles of extreme volatility"""
    dates = pd.date_range('2024-01-01', periods=50, freq='5min')
    np.random.seed(123)
    
    base = 2000.0
    volatility = 0.05  # 5% moves
    
    opens = base + np.random.normal(0, base * volatility * 0.3, 50)
    closes = opens + np.random.normal(0, base * volatility, 50)
    highs = np.maximum(opens, closes) + np.random.uniform(0, base * volatility * 0.5, 50)
    lows = np.minimum(opens, closes) - np.random.uniform(0, base * volatility * 0.5, 50)
    
    return pd.DataFrame({
        'open': opens,
        'high': highs,
        'low': lows,
        'close': closes,
        'volume': np.random.randint(50000, 200000, 50)
    }, index=dates)


@pytest.fixture
def fake_ohlcv_insufficient():
    """Only 10 candles (insufficient for most indicators)"""
    dates = pd.date_range('2024-01-01', periods=10, freq='5min')
    return pd.DataFrame({
        'open': np.random.uniform(1900, 2100, 10),
        'high': np.random.uniform(1950, 2150, 10),
        'low': np.random.uniform(1850, 2050, 10),
        'close': np.random.uniform(1900, 2100, 10),
        'volume': np.random.randint(1000, 10000, 10)
    }, index=dates)


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for database operations"""
    mock = MagicMock()
    
    # Mock table operations
    mock_table = MagicMock()
    mock_table.select.return_value = mock_table
    mock_table.insert.return_value = mock_table
    mock_table.update.return_value = mock_table
    mock_table.delete.return_value = mock_table
    mock_table.eq.return_value = mock_table
    mock_table.limit.return_value = mock_table
    mock_table.order.return_value = mock_table
    mock_table.execute = MagicMock(return_value={
        "data": [],
        "error": None
    })
    
    mock.table.return_value = mock_table
    
    # Mock auth operations
    mock_auth = MagicMock()
    mock_auth.sign_up = AsyncMock()
    mock_auth.sign_in_with_password = AsyncMock()
    mock_auth.sign_out = AsyncMock()
    mock_auth.get_user = AsyncMock()
    mock.auth = mock_auth
    
    return mock


@pytest.fixture
def mock_data_hub():
    """Mock DataHub for market data operations"""
    mock = MagicMock()
    mock.get_price = MagicMock(return_value=2050.0)
    mock.get_candles = MagicMock(return_value=None)
    mock.is_ready = MagicMock(return_value=True)
    return mock


@pytest.fixture
def mock_ml_model():
    """Mock ML model for prediction tests"""
    mock = MagicMock()
    mock.predict = MagicMock(return_value=np.array([0]))  # Class prediction
    mock.predict_proba = MagicMock(return_value=np.array([[0.1, 0.7, 0.2]]))  # BUY
    mock.n_features_in_ = 150
    return mock


# =============================================================================
# Event Loop Fixture for Async Tests
# =============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# =============================================================================
# Pytest Configuration
# =============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names"""
    for item in items:
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        elif "test_" in item.nodeid:
            item.add_marker(pytest.mark.unit)
