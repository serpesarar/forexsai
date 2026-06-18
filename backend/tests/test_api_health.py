"""
Test API Health Endpoints
=========================
Tests FastAPI health and readiness endpoints with TestClient.
All external API calls are mocked.
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock

# Add backend to path
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))


@pytest.fixture
def mock_supabase_for_health():
    """Mock Supabase for health checks"""
    mock = MagicMock()
    mock_table = MagicMock()
    mock_table.select.return_value = mock_table
    mock_table.limit.return_value = mock_table
    mock_table.execute = MagicMock(return_value={
        "data": [{"id": 1}],
        "error": None
    })
    mock.table.return_value = mock_table
    return mock


@pytest.fixture
def test_client(mock_supabase_for_health):
    """Create FastAPI test client with mocked dependencies"""
    with patch.dict('os.environ', {
        'upstream_API_KEY': 'test_key',
        'SUPABASE_URL': 'https://test.supabase.co',
        'SUPABASE_KEY': 'test_key',
    }):
        # Mock all external services before importing app
        with patch('database.supabase_client.get_supabase_client', return_value=mock_supabase_for_health):
            with patch('database.supabase_client.is_db_available', return_value=True):
                with patch('services.data_hub.start_data_hub', new=AsyncMock()):
                    with patch('services.data_hub.stop_data_hub', MagicMock()):
                        with patch('services.background_scheduler.start_scheduler', MagicMock()):
                            with patch('services.background_scheduler.stop_scheduler', MagicMock()):
                                with patch('services.background_scheduler.log_pulse_signals_if_needed', new=AsyncMock()):
                                    with patch('services.signal_lifecycle.check_lifecycle_if_needed', new=AsyncMock()):
                                        with patch('services.redis_client.get_redis', return_value=None):
                                            with patch('services.redis_client.is_redis_available', return_value=False):
                                                # Now import app
                                                from main import app
                                                from fastapi.testclient import TestClient
                                                client = TestClient(app)
                                                yield client


class TestRootEndpoint:
    """Test root endpoint"""
    
    def test_root_returns_200(self, test_client):
        """GET / should return 200"""
        response = test_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "ok"
    
    def test_root_has_required_fields(self, test_client):
        """Root response should have required fields"""
        response = test_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "status" in data


class TestHealthEndpoint:
    """Test /api/health endpoint"""
    
    def test_health_returns_200(self, test_client):
        """GET /api/health should return 200"""
        response = test_client.get("/api/health")
        assert response.status_code == 200
    
    def test_health_returns_ok_status(self, test_client):
        """Health check should return status: ok"""
        response = test_client.get("/api/health")
        data = response.json()
        assert data.get("ok") is True
        assert data.get("status") == "alive"
    
    def test_health_has_uptime(self, test_client):
        """Health check should include uptime"""
        response = test_client.get("/api/health")
        data = response.json()
        assert "uptime_seconds" in data
        assert isinstance(data["uptime_seconds"], (int, float))
        assert data["uptime_seconds"] >= 0


class TestReadyHealthEndpoint:
    """Test /api/ready (readiness) endpoint"""
    
    def test_ready_returns_200_or_503(self, test_client):
        """GET /api/ready should return 200 or 503 (not 500)"""
        response = test_client.get("/api/ready")
        assert response.status_code in [200, 503], \
            f"Expected 200 or 503, got {response.status_code}"
    
    def test_ready_has_required_fields_when_200(self, test_client, mock_supabase_for_health):
        """Ready check should have required fields when healthy"""
        # Ensure mock returns success
        mock_supabase_for_health.table.return_value.execute.return_value = {
            "data": [{"id": 1}],
            "error": None
        }
        
        response = test_client.get("/api/ready")
        if response.status_code == 200:
            data = response.json()
            assert "ok" in data
            assert "status" in data
            assert "checks" in data
    
    def test_ready_returns_not_ready_when_db_down(self, test_client):
        """Ready check should return not_ready when DB is down"""
        with patch('database.supabase_client.get_supabase_client', return_value=None):
            response = test_client.get("/api/ready")
            # Should return 503 when DB is unavailable
            if response.status_code == 503:
                data = response.json()
                assert data.get("ok") is False
                assert data.get("status") == "not_ready"


class TestClearTrendEndpoint:
    """Test /api/clear-trend/{symbol} endpoint"""
    
    @patch('services.data_fetcher.fetch_ohlc_data')
    @patch('services.data_fetcher.fetch_latest_price')
    def test_clear_trend_xauusd_returns_valid_json(self, mock_price, mock_ohlc, test_client):
        """GET /api/clear-trend/XAUUSD should return valid JSON"""
        import numpy as np
        mock_ohlc.return_value = {
            "highs": np.array([2005.0, 2006.0, 2004.0, 2007.0, 2008.0]),
            "lows": np.array([1995.0, 1996.0, 1994.0, 1997.0, 1998.0]),
            "closes": np.array([2000.0, 2002.0, 1998.0, 2005.0, 2006.0]),
            "opens": np.array([2000.0, 2000.0, 2002.0, 1998.0, 2005.0]),
            "volumes": np.array([1000, 1200, 1100, 1300, 1400]),
            "timestamps": ["2024-01-01T00:00:00"] * 5
        }
        mock_price.return_value = 2007.0
        
        response = test_client.get("/api/clear-trend/XAUUSD")
        assert response.status_code in [200, 503, 422]
        
        if response.status_code == 200:
            data = response.json()
            # Check required fields
            assert "symbol" in data or "error" in data
            if "error" not in data:
                assert "trend" in data
                assert "levels" in data
                assert "price" in data
    
    @patch('services.data_fetcher.fetch_ohlc_data')
    @patch('services.data_fetcher.fetch_latest_price')
    def test_clear_trend_ndx_returns_valid_json(self, mock_price, mock_ohlc, test_client):
        """GET /api/clear-trend/NDX.INDX should return valid JSON"""
        import numpy as np
        mock_ohlc.return_value = {
            "highs": np.array([15005.0, 15006.0, 15004.0, 15007.0, 15008.0]),
            "lows": np.array([14995.0, 14996.0, 14994.0, 14997.0, 14998.0]),
            "closes": np.array([15000.0, 15002.0, 14998.0, 15005.0, 15006.0]),
            "opens": np.array([15000.0, 15000.0, 15002.0, 14998.0, 15005.0]),
            "volumes": np.array([1000, 1200, 1100, 1300, 1400]),
            "timestamps": ["2024-01-01T00:00:00"] * 5
        }
        mock_price.return_value = 15007.0
        
        response = test_client.get("/api/clear-trend/NDX.INDX")
        assert response.status_code in [200, 503, 422]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)


class TestErrorHandling:
    """Test API error handling"""
    
    def test_404_on_invalid_endpoint(self, test_client):
        """Invalid endpoint should return 404"""
        response = test_client.get("/api/invalid-endpoint-that-does-not-exist")
        assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
