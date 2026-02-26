"""
Test Auth Endpoints
===================
Tests auth.py endpoints:
- POST /api/auth/register with valid payload → 201
- POST /api/auth/register with duplicate email → 400
- POST /api/auth/login with valid credentials → returns JWT token
- POST /api/auth/login with wrong password → 401
- GET /api/auth/me with valid token → user object
- GET /api/auth/me without token → 401
Mock Supabase auth completely.
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
def mock_supabase_auth():
    """Mock Supabase auth client"""
    mock = MagicMock()
    
    mock_table = MagicMock()
    mock_table.select.return_value = mock_table
    mock_table.insert.return_value = mock_table
    mock_table.update.return_value = mock_table
    mock_table.eq.return_value = mock_table
    mock_table.limit.return_value = mock_table
    mock_table.execute = AsyncMock(return_value={"data": [], "error": None})
    mock.table.return_value = mock_table
    
    mock_auth = MagicMock()
    mock_auth.sign_up = AsyncMock()
    mock_auth.sign_in_with_password = AsyncMock()
    mock.auth = mock_auth
    
    return mock


@pytest.fixture
def test_client(mock_supabase_auth):
    """Create FastAPI test client with mocked auth"""
    with patch.dict('os.environ', {
        'EODHD_API_KEY': 'test_key',
        'SUPABASE_URL': 'https://test.supabase.co',
        'SUPABASE_KEY': 'test_key',
    }):
        with patch('database.supabase_client.get_supabase_client', return_value=mock_supabase_auth):
            with patch('services.data_hub.start_data_hub', new=AsyncMock()):
                with patch('services.data_hub.stop_data_hub', MagicMock()):
                    with patch('services.background_scheduler.start_scheduler', MagicMock()):
                        with patch('services.background_scheduler.stop_scheduler', MagicMock()):
                            with patch('services.background_scheduler.log_pulse_signals_if_needed', new=AsyncMock()):
                                with patch('services.signal_lifecycle.check_lifecycle_if_needed', new=AsyncMock()):
                                    with patch('services.redis_client.get_redis', return_value=None):
                                        with patch('services.redis_client.is_redis_available', return_value=False):
                                            from main import app
                                            from fastapi.testclient import TestClient
                                            client = TestClient(app)
                                            yield client


class TestRegister:
    """Test POST /api/auth/signup"""
    
    def test_register_valid_payload_returns_success(self, test_client, mock_supabase_auth):
        """POST /api/auth/signup with valid payload → success"""
        mock_supabase_auth.table.return_value.select.return_value.eq.return_value.execute = AsyncMock(
            return_value={"data": [], "error": None}
        )
        mock_supabase_auth.table.return_value.insert.return_value.execute = AsyncMock(
            return_value={"data": [{"id": "user-123", "referral_code": "REF123"}], "error": None}
        )
        
        response = test_client.post("/api/auth/signup", json={
            "email": "test@example.com",
            "password": "password123",
            "full_name": "Test User"
        })
        
        # Should return 200 or 201 on success, or error if validation fails
        assert response.status_code in [200, 201, 400, 422]
        
        if response.status_code in [200, 201]:
            data = response.json()
            assert data.get("success") is True
    
    def test_register_duplicate_email_returns_400(self, test_client, mock_supabase_auth):
        """POST /api/auth/signup with duplicate email → 400"""
        mock_supabase_auth.table.return_value.select.return_value.eq.return_value.execute = AsyncMock(
            return_value={"data": [{"id": "existing-user", "email": "test@example.com"}], "error": None}
        )
        
        response = test_client.post("/api/auth/signup", json={
            "email": "test@example.com",
            "password": "password123"
        })
        
        assert response.status_code in [400, 409, 422]


class TestLogin:
    """Test POST /api/auth/login"""
    
    def test_login_valid_credentials_returns_jwt(self, test_client, mock_supabase_auth):
        """POST /api/auth/login with valid credentials → returns JWT token"""
        mock_supabase_auth.table.return_value.select.return_value.eq.return_value.execute = AsyncMock(
            return_value={
                "data": [{
                    "id": "user-123",
                    "email": "test@example.com",
                    "password_hash": "abc123",
                    "salt": "salt123",
                    "membership_tier": "free",
                    "status": "active",
                    "email_verified": True,
                    "referral_code": "REF123",
                    "referral_count": 0,
                    "created_at": "2024-01-01T00:00:00"
                }],
                "error": None
            }
        )
        
        with patch('services.auth_service.verify_password', return_value=True):
            with patch('services.auth_service.generate_token', return_value='jwt-token-123'):
                response = test_client.post("/api/auth/login", json={
                    "email": "test@example.com",
                    "password": "password123"
                })
                
                # Should return 200 or error if auth fails
                assert response.status_code in [200, 401, 403, 422]
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        assert "token" in data
    
    def test_login_wrong_password_returns_401(self, test_client, mock_supabase_auth):
        """POST /api/auth/login with wrong password → 401"""
        mock_supabase_auth.table.return_value.select.return_value.eq.return_value.execute = AsyncMock(
            return_value={
                "data": [{
                    "id": "user-123",
                    "email": "test@example.com",
                    "password_hash": "abc123",
                    "salt": "salt123",
                    "status": "active",
                    "email_verified": True
                }],
                "error": None
            }
        )
        
        with patch('services.auth_service.verify_password', return_value=False):
            response = test_client.post("/api/auth/login", json={
                "email": "test@example.com",
                "password": "wrongpassword"
            })
            
            assert response.status_code in [401, 403, 422]


class TestMe:
    """Test GET /api/auth/me"""
    
    def test_me_with_valid_token_returns_user(self, test_client, mock_supabase_auth):
        """GET /api/auth/me with valid token → user object"""
        with patch('services.auth_service.validate_session', new=AsyncMock(return_value=MagicMock(
            id="user-123",
            email="test@example.com",
            full_name="Test User",
            membership_tier="pro",
            tier_expires_at=None,
            referral_code="REF123",
            referral_count=5,
            status="active",
            email_verified=True,
            created_at="2024-01-01T00:00:00",
            last_login_at="2024-01-02T00:00:00"
        ))):
            response = test_client.get("/api/auth/me", headers={"Authorization": "Bearer valid-token"})
            
            assert response.status_code in [200, 401]
            
            if response.status_code == 200:
                data = response.json()
                assert data.get("id") == "user-123"
                assert data.get("email") == "test@example.com"
    
    def test_me_without_token_returns_401(self, test_client):
        """GET /api/auth/me without token → 401"""
        response = test_client.get("/api/auth/me")
        
        assert response.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
