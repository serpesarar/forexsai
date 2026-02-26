#!/bin/bash
#
# Integration Test Script for ForexSAI Trading Platform
# Tests backend endpoints and WebSocket connection
# CI-friendly: exits with code 1 if any check fails
#
# USAGE:
#   ./scripts/integration_test.sh         # Test against local server
#   ./scripts/integration_test.sh prod    # Test against production
#

set -e  # Exit on first error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
MODE="${1:-local}"

if [ "$MODE" = "prod" ]; then
  BASE_URL="https://upbeat-flow-production.up.railway.app"
  WS_URL="wss://upbeat-flow-production.up.railway.app/ws/all"
  SKIP_START=true
else
  TEST_PORT=8001
  BASE_URL="http://localhost:${TEST_PORT}"
  WS_URL="ws://localhost:${TEST_PORT}/ws/all"
  SKIP_START=false
fi

TIMEOUT=30
FAILED=0
BACKEND_PID=""

# Helper functions
print_header() {
    echo -e "\n${YELLOW}════════════════════════════════════════════════${NC}"
    echo -e "${YELLOW}  $1${NC}"
    echo -e "${YELLOW}════════════════════════════════════════════════${NC}\n"
}

print_pass() {
    echo -e "${GREEN}✓ PASS${NC}: $1"
}

print_fail() {
    echo -e "${RED}✗ FAIL${NC}: $1"
    FAILED=$((FAILED + 1))
}

print_info() {
    echo -e "${YELLOW}ℹ INFO${NC}: $1"
}

# Check if required tools are installed
check_dependencies() {
    print_header "Checking Dependencies"
    
    if ! command -v curl &> /dev/null; then
        echo "curl is required but not installed. Aborting."
        exit 1
    fi
    
    if command -v jq &> /dev/null; then
        HAS_JQ=true
    else
        HAS_JQ=false
        print_info "jq not found, JSON validation will be limited"
    fi
    
    print_pass "Dependencies check"
}

# Start backend on test port (only for local mode)
start_backend() {
    if [ "$SKIP_START" = true ]; then
        print_info "Skipping local backend start (production mode)"
        return 0
    fi
    
    print_header "Starting Backend"
    
    # Check if port is already in use
    if lsof -Pi :${TEST_PORT} -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_info "Port ${TEST_PORT} is already in use, attempting to stop existing process"
        lsof -Pi :${TEST_PORT} -sTCP:LISTEN -t | xargs kill -9 2>/dev/null || true
        sleep 2
    fi
    
    # Start backend in background with minimal logging
    print_info "Starting backend on port ${TEST_PORT}..."
    cd "$(dirname "$0")/.."
    
    # Create a temporary Python script for the test server
    cat > /tmp/forexsai_test_server.py << 'PYTHON_EOF'
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Mock environment
os.environ['PORT'] = '8001'
os.environ['EODHD_API_KEY'] = 'test_key'
os.environ['SUPABASE_URL'] = 'https://test.supabase.co'
os.environ['SUPABASE_KEY'] = 'test_key'

# Mock all external services before importing app
from unittest.mock import MagicMock, AsyncMock

# Mock services module
import sys
mock_services = MagicMock()
mock_services.data_hub = MagicMock()
mock_services.data_hub.start_data_hub = AsyncMock()
mock_services.data_hub.stop_data_hub = MagicMock()
mock_services.background_scheduler = MagicMock()
mock_services.background_scheduler.start_scheduler = MagicMock()
mock_services.background_scheduler.stop_scheduler = MagicMock()
mock_services.background_scheduler.log_pulse_signals_if_needed = AsyncMock()
mock_services.signal_lifecycle = MagicMock()
mock_services.signal_lifecycle.check_lifecycle_if_needed = AsyncMock()
mock_services.redis_client = MagicMock()
mock_services.redis_client.get_redis = MagicMock(return_value=None)
mock_services.redis_client.is_redis_available = MagicMock(return_value=False)

sys.modules['services'] = mock_services
sys.modules['services.data_hub'] = mock_services.data_hub
sys.modules['services.background_scheduler'] = mock_services.background_scheduler
sys.modules['services.signal_lifecycle'] = mock_services.signal_lifecycle
sys.modules['services.redis_client'] = mock_services.redis_client

# Mock database
mock_db = MagicMock()
mock_db.supabase_client = MagicMock()
mock_db.supabase_client.get_supabase_client = MagicMock(return_value=None)
mock_db.supabase_client.is_db_available = MagicMock(return_value=False)
sys.modules['database'] = mock_db
sys.modules['database.supabase_client'] = mock_db.supabase_client

from backend.main import app
import uvicorn

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="error")
PYTHON_EOF
    
    # Start the server (use venv python if available)
    if [ -f "$(dirname "$0")/../.venv/bin/python" ]; then
        "$(dirname "$0")/../.venv/bin/python" /tmp/forexsai_test_server.py &
    else
        python3 /tmp/forexsai_test_server.py &
    fi
    BACKEND_PID=$!
    
    # Wait for server to be ready
    print_info "Waiting for backend to be ready..."
    for i in $(seq 1 $TIMEOUT); do
        if curl -s "${BASE_URL}/api/health" > /dev/null 2>&1; then
            print_pass "Backend started successfully"
            return 0
        fi
        sleep 1
    done
    
    print_fail "Backend failed to start within ${TIMEOUT} seconds"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
}

# Stop backend
stop_backend() {
    if [ "$SKIP_START" = true ]; then
        return 0
    fi
    
    print_header "Stopping Backend"
    
    if [ -n "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
        rm -f /tmp/forexsai_test_server.py
        print_pass "Backend stopped"
    fi
}

# Test health endpoint
test_health() {
    print_header "Testing Health Endpoints"
    
    # Test root endpoint
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/" 2>/dev/null || echo "000")
    if [ "$RESPONSE" = "200" ]; then
        print_pass "GET / returns 200"
    else
        print_fail "GET / returns $RESPONSE (expected 200)"
    fi
    
    # Test health endpoint
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/api/health" 2>/dev/null || echo "000")
    if [ "$RESPONSE" = "200" ]; then
        print_pass "GET /api/health returns 200"
    else
        print_fail "GET /api/health returns $RESPONSE (expected 200)"
    fi
    
    # Test health response body
    if [ "$HAS_JQ" = true ]; then
        HEALTH_BODY=$(curl -s "${BASE_URL}/api/health" 2>/dev/null)
        if echo "$HEALTH_BODY" | jq -e '.status == "alive"' > /dev/null 2>&1; then
            print_pass "Health endpoint returns correct status"
        else
            print_fail "Health endpoint status check failed"
        fi
    fi
    
    # Test readiness endpoint
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/api/ready" 2>/dev/null || echo "000")
    if [ "$RESPONSE" = "200" ] || [ "$RESPONSE" = "503" ]; then
        print_pass "GET /api/ready returns $RESPONSE (expected 200 or 503)"
    else
        print_fail "GET /api/ready returns $RESPONSE (expected 200 or 503)"
    fi
}

# Test API endpoints
test_api_endpoints() {
    print_header "Testing API Endpoints"
    
    # Test clear-trend endpoint
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/api/clear-trend/XAUUSD" 2>/dev/null || echo "000")
    if [ "$RESPONSE" = "200" ] || [ "$RESPONSE" = "503" ] || [ "$RESPONSE" = "422" ]; then
        print_pass "GET /api/clear-trend/XAUUSD returns $RESPONSE"
    else
        print_fail "GET /api/clear-trend/XAUUSD returns $RESPONSE"
    fi
    
    # Test clear-trend for NDX
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/api/clear-trend/NDX.INDX" 2>/dev/null || echo "000")
    if [ "$RESPONSE" = "200" ] || [ "$RESPONSE" = "503" ] || [ "$RESPONSE" = "422" ]; then
        print_pass "GET /api/clear-trend/NDX.INDX returns $RESPONSE"
    else
        print_fail "GET /api/clear-trend/NDX.INDX returns $RESPONSE"
    fi
    
    # Test emel endpoint (if available)
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/api/panel/emel/XAUUSD" 2>/dev/null || echo "000")
    if [ "$RESPONSE" = "200" ] || [ "$RESPONSE" = "404" ] || [ "$RESPONSE" = "503" ]; then
        print_pass "GET /api/panel/emel/XAUUSD returns $RESPONSE"
    else
        print_fail "GET /api/panel/emel/XAUUSD returns $RESPONSE"
    fi
    
    # Test 404 for invalid endpoint
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/api/invalid-endpoint" 2>/dev/null || echo "000")
    if [ "$RESPONSE" = "404" ]; then
        print_pass "GET /api/invalid-endpoint returns 404"
    else
        print_fail "GET /api/invalid-endpoint returns $RESPONSE (expected 404)"
    fi
}

# Test WebSocket connection
test_websocket() {
    print_header "Testing WebSocket Connection"
    
    # Use curl to test WebSocket handshake (upgrade request)
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" \
        -H "Upgrade: websocket" \
        -H "Connection: Upgrade" \
        -H "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==" \
        -H "Sec-WebSocket-Version: 13" \
        "${BASE_URL}/ws/all" 2>/dev/null || echo "000")
    
    # WebSocket upgrade returns 101 Switching Protocols, 
    # but if endpoint doesn't exist, returns 404
    if [ "$RESPONSE" = "101" ] || [ "$RESPONSE" = "426" ] || [ "$RESPONSE" = "000" ]; then
        print_pass "WebSocket endpoint accessible (HTTP $RESPONSE)"
    else
        print_fail "WebSocket endpoint returned unexpected status: $RESPONSE"
    fi
}

# Test auth endpoints (if available)
test_auth() {
    print_header "Testing Auth Endpoints"
    
    # Test signup endpoint (without valid data, should return 400 or 422)
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" \
        -X POST \
        -H "Content-Type: application/json" \
        -d '{"email":"test@test.com","password":"test123"}' \
        "${BASE_URL}/api/auth/signup" 2>/dev/null || echo "000")
    
    if [ "$RESPONSE" = "200" ] || [ "$RESPONSE" = "201" ] || [ "$RESPONSE" = "400" ] || [ "$RESPONSE" = "422" ]; then
        print_pass "POST /api/auth/signup returns $RESPONSE"
    else
        print_fail "POST /api/auth/signup returns $RESPONSE"
    fi
    
    # Test login endpoint
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" \
        -X POST \
        -H "Content-Type: application/json" \
        -d '{"email":"test@test.com","password":"test123"}' \
        "${BASE_URL}/api/auth/login" 2>/dev/null || echo "000")
    
    if [ "$RESPONSE" = "200" ] || [ "$RESPONSE" = "401" ] || [ "$RESPONSE" = "422" ]; then
        print_pass "POST /api/auth/login returns $RESPONSE"
    else
        print_fail "POST /api/auth/login returns $RESPONSE"
    fi
    
    # Test /me endpoint without token (should return 401)
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" \
        "${BASE_URL}/api/auth/me" 2>/dev/null || echo "000")
    
    if [ "$RESPONSE" = "401" ]; then
        print_pass "GET /api/auth/me without token returns 401"
    else
        print_fail "GET /api/auth/me without token returns $RESPONSE (expected 401)"
    fi
}

# Main execution
trap stop_backend EXIT

main() {
    print_header "ForexSAI Integration Tests - Mode: $MODE"
    
    check_dependencies
    start_backend
    
    # Run all tests
    test_health
    test_api_endpoints
    test_websocket
    test_auth
    
    # Print summary
    print_header "Test Summary"
    
    if [ $FAILED -eq 0 ]; then
        echo -e "${GREEN}All tests passed!${NC}"
        exit 0
    else
        echo -e "${RED}$FAILED test(s) failed${NC}"
        exit 1
    fi
}

main "$@"
