import importlib.util
import sys
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