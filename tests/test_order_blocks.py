from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_detect_order_blocks():
    response = client.post(
        "/api/order-blocks/detect",
        json={
            "symbol": "NDX.INDX",
            "timeframe": "5m",
            "limit": 200,
            "config": {
                "fractal_period": 2,
                "min_displacement_atr": 1.0,
                "min_score": 30.0,
                "zone_type": "wick",
                "max_tests": 2,
            },
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert "order_blocks" in payload
    assert payload["timeframe"] == "5m"


def test_check_entry_returns_shape():
    response = client.post(
        "/api/order-blocks/check-entry",
        json={"symbol": "NDX.INDX", "timeframe": "5m", "order_block_index": 0},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "has_signal" in payload


def test_backtest_response():
    response = client.post(
        "/api/order-blocks/backtest",
        json={
            "symbol": "NDX.INDX",
            "timeframe": "5m",
            "start_date": "2025-01-01",
            "end_date": "2025-01-20",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["total_trades"] >= 0
