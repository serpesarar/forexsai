import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest


backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))


class _SequenceQuery:
    def __init__(self, responses):
        self._responses = list(responses)

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, *_args, **_kwargs):
        return self

    def gte(self, *_args, **_kwargs):
        return self

    def lt(self, *_args, **_kwargs):
        return self

    def order(self, *_args, **_kwargs):
        return self

    def limit(self, *_args, **_kwargs):
        return self

    def execute(self):
        return SimpleNamespace(data=self._responses.pop(0) if self._responses else [], error=None)


class _FakeClient:
    def __init__(self, prediction_responses):
        self._prediction_logs = _SequenceQuery(prediction_responses)

    def table(self, name):
        if name == "prediction_logs":
            return self._prediction_logs
        raise AssertionError(f"Unexpected table requested: {name}")


@pytest.mark.asyncio
async def test_model_detail_analytics_ignores_legacy_timeframes_and_uses_realized_pnl():
    with patch.dict(
        sys.modules,
        {
            "anthropic": SimpleNamespace(Anthropic=object),
            "services.telegram_service": SimpleNamespace(telegram_notifier=SimpleNamespace()),
        },
    ):
        module_path = backend_dir / "routers" / "learning.py"
        spec = importlib.util.spec_from_file_location("test_learning_router", module_path)
        learning_module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(learning_module)
        get_model_detail_analytics = learning_module.get_model_detail_analytics

    signal_rows = [
        {
            "id": "legacy-stop-001",
            "symbol": "NDX.INDX",
            "timeframe": None,
            "ml_direction": "BUY",
            "ml_confidence": "oops",
            "status": "stopped",
            "ml_entry_price": 100.0,
            "exit_price": None,
            "stop_loss_pips": 25,
            "created_at": "2026-03-06T10:00:00Z",
            "highest_profit_pips": 12,
            "lowest_drawdown_pips": 300,
            "targets_hit": {},
            "model_type": "ml",
            "strategy": None,
        },
        {
            "id": "fifteen-win-002",
            "symbol": "NDX.INDX",
            "timeframe": "15m",
            "ml_direction": "BUY",
            "ml_confidence": 78,
            "status": "completed",
            "ml_entry_price": 100.0,
            "exit_price": 110.0,
            "stop_loss_pips": None,
            "created_at": "2026-03-06T11:00:00Z",
            "highest_profit_pips": 99,
            "lowest_drawdown_pips": 0,
            "targets_hit": {"TP1": True},
            "model_type": "ml",
            "strategy": None,
        },
    ]

    client = _FakeClient([[], signal_rows])

    with patch.object(learning_module, "is_db_available", return_value=True), patch.object(
        learning_module, "get_supabase_client", return_value=client
    ):
        payload = await get_model_detail_analytics(model="ml", symbol="NDX.INDX", days=1, timeframe="all")

    assert payload["available_timeframes"] == ["15m"]
    assert [row["tf"] for row in payload["timeframe_comparison"]] == ["15m"]
    assert payload["overview"]["net_pips"] == -15.0
    assert payload["recent_signals"][0]["confidence"] == 78.0
    assert payload["recent_signals"][1]["confidence"] == 50.0
    assert payload["recent_signals"][1]["timeframe"] == "legacy"


@pytest.mark.asyncio
async def test_model_detail_analytics_repairs_target_hit_rows_with_bad_exit_prices():
    with patch.dict(
        sys.modules,
        {
            "anthropic": SimpleNamespace(Anthropic=object),
            "services.telegram_service": SimpleNamespace(telegram_notifier=SimpleNamespace()),
        },
    ):
        module_path = backend_dir / "routers" / "learning.py"
        spec = importlib.util.spec_from_file_location("test_learning_router_repaired", module_path)
        learning_module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(learning_module)
        get_model_detail_analytics = learning_module.get_model_detail_analytics

    signal_rows = [
        {
            "id": "repaired-win-001",
            "symbol": "NDX.INDX",
            "timeframe": "30m",
            "ml_direction": "BUY",
            "ml_confidence": 81,
            "status": "completed",
            "ml_entry_price": 100.0,
            "exit_price": 80.0,
            "stop_loss_pips": 50,
            "created_at": "2026-03-06T12:00:00Z",
            "highest_profit_pips": 3,
            "lowest_drawdown_pips": -20,
            "targets_hit": '"{\\"TP1\\": true, \\"TP2\\": true, \\"TP3\\": false, \\"TP4\\": false}"',
            "targets": '"{\\"TP1\\": 115.0, \\"TP2\\": 125.0, \\"TP3\\": 135.0, \\"TP4\\": 150.0}"',
            "model_type": "ml",
            "strategy": None,
        },
    ]

    client = _FakeClient([[], signal_rows])

    with patch.object(learning_module, "is_db_available", return_value=True), patch.object(
        learning_module, "get_supabase_client", return_value=client
    ):
        payload = await get_model_detail_analytics(model="ml", symbol="NDX.INDX", days=1, timeframe="all")

    assert payload["overview"]["completed"] == 1
    assert payload["overview"]["net_pips"] == 25.0
    assert payload["timeframe_comparison"] == [
        {"tf": "30m", "total": 1, "active": 0, "win_rate": 100.0, "net_pips": 25.0, "avg_pips": 25.0}
    ]
    assert payload["recent_signals"][0]["status"] == "completed"
    assert payload["recent_signals"][0]["pips"] == 25.0


@pytest.mark.asyncio
async def test_model_detail_analytics_uses_session_hours_and_averages_weekdays_by_date_bucket():
    with patch.dict(
        sys.modules,
        {
            "anthropic": SimpleNamespace(Anthropic=object),
            "services.telegram_service": SimpleNamespace(telegram_notifier=SimpleNamespace()),
        },
    ):
        module_path = backend_dir / "routers" / "learning.py"
        spec = importlib.util.spec_from_file_location("test_learning_router_hourly", module_path)
        learning_module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(learning_module)
        get_model_detail_analytics = learning_module.get_model_detail_analytics

    fixed_now = datetime(2026, 3, 11, 0, 0, tzinfo=timezone.utc)
    monday_rows = [
        {
            "id": "older-monday-win-000",
            "symbol": "NDX.INDX",
            "timeframe": "15m",
            "ml_direction": "BUY",
            "ml_confidence": 73,
            "status": "completed",
            "ml_entry_price": 100.0,
            "exit_price": None,
            "stop_loss_pips": None,
            "created_at": "2026-02-23T09:40:00Z",
            "highest_profit_pips": 12,
            "lowest_drawdown_pips": -2,
            "targets_hit": {},
            "model_type": "ml",
            "strategy": None,
        },
        {
            "id": "monday-win-001",
            "symbol": "NDX.INDX",
            "timeframe": "15m",
            "ml_direction": "BUY",
            "ml_confidence": 81,
            "status": "completed",
            "ml_entry_price": 100.0,
            "exit_price": None,
            "stop_loss_pips": None,
            "created_at": "2026-03-02T09:45:00Z",
            "highest_profit_pips": 18,
            "lowest_drawdown_pips": -4,
            "targets_hit": {},
            "model_type": "ml",
            "strategy": None,
        },
        {
            "id": "monday-loss-002",
            "symbol": "NDX.INDX",
            "timeframe": "15m",
            "ml_direction": "BUY",
            "ml_confidence": 64,
            "status": "stopped",
            "ml_entry_price": 100.0,
            "exit_price": None,
            "stop_loss_pips": 10,
            "created_at": "2026-03-02T09:55:00Z",
            "highest_profit_pips": 3,
            "lowest_drawdown_pips": -10,
            "targets_hit": {},
            "model_type": "ml",
            "strategy": None,
        },
    ]
    tuesday_rows = [
        {
            "id": "tuesday-target-003",
            "symbol": "NDX.INDX",
            "timeframe": "15m",
            "ml_direction": "BUY",
            "ml_confidence": 77,
            "status": "stopped",
            "ml_entry_price": 100.0,
            "exit_price": None,
            "stop_loss_pips": 20,
            "created_at": "2026-03-03T12:10:00Z",
            "highest_profit_pips": 12,
            "lowest_drawdown_pips": -6,
            "targets_hit": {"TP1": True},
            "model_type": "ml",
            "strategy": None,
        },
        {
            "id": "tuesday-expired-004",
            "symbol": "NDX.INDX",
            "timeframe": "15m",
            "ml_direction": "BUY",
            "ml_confidence": 58,
            "status": "expired",
            "ml_entry_price": 100.0,
            "exit_price": None,
            "stop_loss_pips": None,
            "created_at": "2026-03-03T12:25:00Z",
            "highest_profit_pips": 6,
            "lowest_drawdown_pips": -2,
            "targets_hit": {},
            "model_type": "ml",
            "strategy": None,
        },
        {
            "id": "tuesday-active-005",
            "symbol": "NDX.INDX",
            "timeframe": "15m",
            "ml_direction": "BUY",
            "ml_confidence": 54,
            "status": "active",
            "ml_entry_price": 100.0,
            "exit_price": None,
            "stop_loss_pips": None,
            "created_at": "2026-03-03T12:40:00Z",
            "highest_profit_pips": 0,
            "lowest_drawdown_pips": 0,
            "targets_hit": {},
            "model_type": "ml",
            "strategy": None,
        },
    ]

    client = _FakeClient([monday_rows, tuesday_rows])

    with patch.object(learning_module, "is_db_available", return_value=True), patch.object(
        learning_module, "get_supabase_client", return_value=client
    ), patch.object(learning_module, "_utc_now", return_value=fixed_now):
        payload = await get_model_detail_analytics(model="ml", symbol="NDX.INDX", days=20, timeframe="all")

    assert payload["overview"] == {
        "total_signals": 6,
        "win_rate": 75.0,
        "completed": 3,
        "stopped": 1,
        "expired": 1,
        "active": 1,
        "net_pips": 32.0,
        "avg_profit_pips": 14.0,
        "avg_loss_pips": 10.0,
        "risk_reward": 1.4,
        "sharpe_ratio": pytest.approx(10.3, rel=1e-3),
        "max_drawdown_pips": 10.0,
        "profit_factor": 4.2,
    }

    assert payload["meta"]["hourly_visible_hours"] == [9, 10, 11, 12, 13, 14, 15, 16, 17]
    assert payload["meta"]["hourly_window_label"] == "09:00–17:00"
    assert payload["meta"]["hourly_session_key"] == "us_cash"

    hourly_rows = {row["hour"]: row for row in payload["hourly_heatmap"]}
    assert list(hourly_rows.keys()) == [9, 10, 11, 12, 13, 14, 15, 16, 17]
    assert hourly_rows[9] == {"hour": 9, "total": 3, "wins": 2, "win_rate": 66.7, "avg_pips": 6.7}
    assert hourly_rows[12] == {"hour": 12, "total": 2, "wins": 1, "win_rate": 50.0, "avg_pips": 6.0}
    assert hourly_rows[10] == {"hour": 10, "total": 0, "wins": 0, "win_rate": 0, "avg_pips": 0}

    weekday_rows = {row["day"]: row for row in payload["day_of_week"]}
    assert weekday_rows["Monday"] == {
        "day": "Monday",
        "day_short": "Mon",
        "total": 3,
        "wins": 2,
        "win_rate": 75.0,
        "avg_pips": 10.0,
    }
    assert weekday_rows["Tuesday"] == {
        "day": "Tuesday",
        "day_short": "Tue",
        "total": 2,
        "wins": 1,
        "win_rate": 50.0,
        "avg_pips": 12.0,
    }
    assert weekday_rows["Wednesday"]["total"] == 0

    assert any(row["status"] == "active" and row["pips"] == 0.0 for row in payload["recent_signals"])