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

    def neq(self, *_args, **_kwargs):
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


def _load_learning_module(module_name: str):
    with patch.dict(
        sys.modules,
        {
            "anthropic": SimpleNamespace(Anthropic=object),
            "services.telegram_service": SimpleNamespace(telegram_notifier=SimpleNamespace()),
        },
    ):
        module_path = backend_dir / "routers" / "learning.py"
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        learning_module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(learning_module)
        return learning_module


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
    assert payload["overview"]["net_pips"] == -35.0
    assert payload["recent_signals"][0]["confidence"] == 78.0
    assert payload["recent_signals"][0]["date"] == "2026-03-06T11:00:00Z"
    assert payload["recent_signals"][0]["entry_price"] == 100.0
    assert payload["recent_signals"][1]["confidence"] == 50.0
    assert payload["recent_signals"][1]["timeframe"] == "legacy"
    assert payload["recent_signals"][1]["entry_price"] == 100.0


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
    assert payload["recent_signals"][0]["entry_price"] == 100.0


@pytest.mark.asyncio
async def test_model_detail_analytics_filters_ml_rows_by_strategy_scope():
    learning_module = _load_learning_module("test_learning_model_detail_scope_filter")
    get_model_detail_analytics = learning_module.get_model_detail_analytics

    signal_rows = [
        {
            "id": "main-win-001",
            "symbol": "NDX.INDX",
            "timeframe": "30m",
            "ml_direction": "BUY",
            "ml_confidence": 61,
            "status": "completed",
            "ml_entry_price": 100.0,
            "exit_price": 110.0,
            "stop_loss_pips": 20,
            "created_at": "2026-03-06T09:00:00Z",
            "highest_profit_pips": 10,
            "lowest_drawdown_pips": 0,
            "targets_hit": {"TP1": True},
            "model_type": "ml:main",
            "strategy": "main",
        },
        {
            "id": "aggressive-win-002",
            "symbol": "NDX.INDX",
            "timeframe": "15m",
            "ml_direction": "SELL",
            "ml_confidence": 49,
            "status": "completed",
            "ml_entry_price": 100.0,
            "exit_price": 90.0,
            "stop_loss_pips": 20,
            "created_at": "2026-03-06T10:00:00Z",
            "highest_profit_pips": 10,
            "lowest_drawdown_pips": 0,
            "targets_hit": {"TP1": True, "TP2": True},
            "model_type": "ml:aggressive",
            "strategy": "aggressive",
        },
    ]

    client = _FakeClient([[], signal_rows])

    with patch.object(learning_module, "is_db_available", return_value=True), patch.object(
        learning_module, "get_supabase_client", return_value=client
    ):
        payload = await get_model_detail_analytics(
            model="ml",
            symbol="NDX.INDX",
            days=1,
            strategy_scope="aggressive",
            timeframe="all",
        )

    assert payload["meta"]["selected_model"] == "ml"
    assert payload["meta"]["selected_scope"] == "aggressive"
    assert payload["overview"]["total_signals"] == 1
    assert payload["overview"]["completed"] == 1
    assert payload["overview"]["net_pips"] == 25.0
    assert payload["available_models"] == ["ml"]
    assert payload["available_timeframes"] == ["15m"]
    assert len(payload["recent_signals"]) == 1
    signal = payload["recent_signals"][0]
    assert signal["id"] == "aggressi"
    assert signal["date"] == "2026-03-06T10:00:00Z"
    assert signal["direction"] == "SELL"
    assert signal["confidence"] == 49.0
    assert signal["status"] == "completed"
    assert signal["pips"] == 25.0
    assert signal["timeframe"] == "15m"
    assert signal["entry_price"] == 100.0
    assert signal["exit_price"] == 75.0


@pytest.mark.asyncio
async def test_model_detail_analytics_uses_canonical_fixed_hourly_geometry_when_stored_targets_are_inflated():
    learning_module = _load_learning_module("test_learning_hourly_fixed_geometry")
    get_model_detail_analytics = learning_module.get_model_detail_analytics

    signal_rows = [
        {
            "id": "dax-hourly-win-001",
            "symbol": "GDAXI.INDX",
            "timeframe": "1h",
            "ml_direction": "BUY",
            "ml_confidence": 74,
            "status": "completed",
            "resolution_reason": "tp4_hit",
            "ml_entry_price": 23591.8,
            "exit_price": 23736.1562,
            "stop_loss_pips": 144.4,
            "created_at": "2026-03-19T07:21:10.530689Z",
            "highest_profit_pips": 144.4,
            "lowest_drawdown_pips": -12,
            "targets_hit": {"TP1": True, "TP2": True, "TP3": True, "TP4": True},
            "targets": {"TP1": 23656.1562, "TP2": 23666.1562, "TP3": 23676.1562, "TP4": 23736.1562},
            "model_type": "emel",
            "strategy": "EMEL",
        },
    ]

    client = _FakeClient([[], signal_rows])

    with patch.object(learning_module, "is_db_available", return_value=True), patch.object(
        learning_module, "get_supabase_client", return_value=client
    ):
        payload = await get_model_detail_analytics(model="emel", symbol="GDAXI.INDX", days=1, timeframe="1h")

    assert payload["overview"]["completed"] == 1
    assert payload["overview"]["net_pips"] == 50.0
    assert payload["timeframe_comparison"] == [
        {"tf": "1h", "total": 1, "active": 0, "win_rate": 100.0, "net_pips": 50.0, "avg_pips": 50.0}
    ]
    assert payload["recent_signals"][0]["pips"] == 50.0
    assert payload["recent_signals"][0]["exit_price"] == 23641.8


@pytest.mark.asyncio
async def test_historical_signals_endpoint_includes_scoped_ml_records_for_ml_filter():
    learning_module = _load_learning_module("test_learning_historical_scoped_ml")
    get_historical_signals_endpoint = learning_module.get_historical_signals_endpoint

    signal_rows = [
        {
            "id": "scoped-ml-001",
            "symbol": "NDX.INDX",
            "timeframe": "15m",
            "ml_direction": "BUY",
            "ml_confidence": 77,
            "ml_entry_price": 100.0,
            "strategy": "balanced",
            "status": "completed",
            "targets_hit": {"TP1": True},
            "targets": {},
            "highest_profit_pips": 12,
            "lowest_drawdown_pips": 0,
            "stop_loss_pips": 50.0,
            "created_at": "2026-03-06T11:00:00Z",
            "model_type": "ml:balanced",
            "exit_price": 110.0,
            "exit_time": "2026-03-06T12:00:00Z",
            "resolution_reason": None,
        },
        {
            "id": "pulse-row-002",
            "symbol": "NDX.INDX",
            "timeframe": "15m",
            "ml_direction": "BUY",
            "ml_confidence": 61,
            "ml_entry_price": 100.0,
            "strategy": "PULSE_ML",
            "status": "completed",
            "targets_hit": {"TP1": True},
            "targets": {},
            "highest_profit_pips": 8,
            "lowest_drawdown_pips": 0,
            "stop_loss_pips": 50.0,
            "created_at": "2026-03-06T10:00:00Z",
            "model_type": "pulse2",
            "exit_price": 108.0,
            "exit_time": "2026-03-06T10:30:00Z",
            "resolution_reason": None,
        },
        {
            "id": "invalid-history-003",
            "symbol": "NDX.INDX",
            "timeframe": "15m",
            "ml_direction": "SELL",
            "ml_confidence": 95,
            "ml_entry_price": 100.0,
            "strategy": "balanced",
            "status": "expired",
            "targets_hit": {},
            "targets": {},
            "highest_profit_pips": 0,
            "lowest_drawdown_pips": 0,
            "stop_loss_pips": 50.0,
            "created_at": "2026-03-06T13:00:00Z",
            "model_type": "ml:balanced",
            "exit_price": None,
            "exit_time": "2026-03-06T13:00:00Z",
            "resolution_reason": "market_closed_invalid",
        },
    ]

    client = _FakeClient([signal_rows])

    with patch.object(learning_module, "is_db_available", return_value=True), patch.object(
        learning_module, "get_supabase_client", return_value=client
    ):
        payload = await get_historical_signals_endpoint(symbol="NDX.INDX", model="ml", days=30)

    assert payload["totalSignals"] == 1
    assert payload["recentSignals"][0]["id"] == "scoped-ml-001"
    assert payload["modelId"] == "ml_core"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("symbol", "row", "expected_profit"),
    [
        (
            "XAUUSD",
            {
                "id": "xau-hourly-win-001",
                "symbol": "XAUUSD",
                "timeframe": "1h",
                "ml_direction": "BUY",
                "ml_confidence": 74,
                "ml_entry_price": 2900.0,
                "strategy": "balanced",
                "status": "completed",
                "targets_hit": {"TP1": True, "TP2": True, "TP3": True, "TP4": True},
                "targets": {"TP1": 2919.6, "TP2": 2926.6, "TP3": 2936.6, "TP4": 2951.6},
                "highest_profit_pips": 51.6,
                "lowest_drawdown_pips": -4.0,
                "stop_loss_pips": 26.6,
                "created_at": "2026-03-19T07:21:10.530689Z",
                "model_type": "ml:balanced",
                "exit_price": 2951.6,
                "exit_time": "2026-03-19T08:21:10.530689Z",
                "resolution_reason": "tp4_hit",
            },
            40.0,
        ),
        (
            "USOIL.FOREX",
            {
                "id": "oil-hourly-win-001",
                "symbol": "USOIL.FOREX",
                "timeframe": "1h",
                "ml_direction": "BUY",
                "ml_confidence": 74,
                "ml_entry_price": 70.0,
                "strategy": "balanced",
                "status": "completed",
                "targets_hit": {"TP1": True, "TP2": True, "TP3": True, "TP4": True},
                "targets": {"TP1": 70.294, "TP2": 70.308, "TP3": 70.322, "TP4": 70.35},
                "highest_profit_pips": 0.35,
                "lowest_drawdown_pips": -0.01,
                "stop_loss_pips": 0.315,
                "created_at": "2026-03-19T07:21:10.530689Z",
                "model_type": "ml:balanced",
                "exit_price": 70.35,
                "exit_time": "2026-03-19T08:21:10.530689Z",
                "resolution_reason": "tp4_hit",
            },
            0.07,
        ),
    ],
)
async def test_historical_signals_endpoint_uses_canonical_fixed_hourly_geometry_for_all_symbols(symbol, row, expected_profit):
    learning_module = _load_learning_module(f"test_learning_historical_fixed_geometry_{symbol.lower().replace('.', '_')}")
    get_historical_signals_endpoint = learning_module.get_historical_signals_endpoint

    client = _FakeClient([[row]])

    with patch.object(learning_module, "is_db_available", return_value=True), patch.object(
        learning_module, "get_supabase_client", return_value=client
    ):
        payload = await get_historical_signals_endpoint(symbol=symbol, model="ml", days=30)

    assert payload["totalSignals"] == 1
    assert payload["recentSignals"][0]["profit"] == pytest.approx(expected_profit, abs=0.0001)
    assert payload["recentSignals"][0]["result"] == "win"


@pytest.mark.asyncio
async def test_model_detail_analytics_uses_session_hours_and_tp_sl_only_weekday_buckets():
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
        "net_pips": -5.0,
        "avg_profit_pips": 15.0,
        "avg_loss_pips": 50.0,
        "risk_reward": 0.3,
        "sharpe_ratio": pytest.approx(-0.61, rel=1e-3),
        "max_drawdown_pips": 50.0,
        "profit_factor": 0.9,
    }

    assert payload["meta"]["hourly_visible_hours"] == [9, 10, 11, 12, 13, 14, 15, 16, 17]
    assert payload["meta"]["hourly_window_label"] == "09:00–17:00"
    assert payload["meta"]["hourly_session_key"] == "us_cash"

    hourly_rows = {row["hour"]: row for row in payload["hourly_heatmap"]}
    assert list(hourly_rows.keys()) == [9, 10, 11, 12, 13, 14, 15, 16, 17]
    assert hourly_rows[9] == {"hour": 9, "total": 3, "wins": 2, "win_rate": 66.7, "avg_pips": -6.7}
    assert hourly_rows[12] == {"hour": 12, "total": 1, "wins": 1, "win_rate": 100.0, "avg_pips": 15.0}
    assert hourly_rows[10] == {"hour": 10, "total": 0, "wins": 0, "win_rate": 0, "avg_pips": 0}

    weekday_rows = {row["day"]: row for row in payload["day_of_week"]}
    assert weekday_rows["Monday"] == {
        "day": "Monday",
        "day_short": "Mon",
        "total": 3,
        "wins": 2,
        "win_rate": 75.0,
        "avg_pips": -10.0,
    }
    assert weekday_rows["Tuesday"] == {
        "day": "Tuesday",
        "day_short": "Tue",
        "total": 1,
        "wins": 1,
        "win_rate": 100.0,
        "avg_pips": 15.0,
    }
    assert weekday_rows["Wednesday"]["total"] == 0

    assert any(row["status"] == "active" and row["pips"] == 0.0 for row in payload["recent_signals"])


@pytest.mark.asyncio
async def test_model_detail_analytics_tp_rates_use_common_resolved_denominator():
    learning_module = _load_learning_module("test_learning_router_tp_rates")
    get_model_detail_analytics = learning_module.get_model_detail_analytics
    fixed_now = datetime(2026, 3, 7, 12, 0, tzinfo=timezone.utc)

    signal_rows = [
        {
            "id": "tp-win-001",
            "symbol": "NDX.INDX",
            "timeframe": "15m",
            "ml_direction": "BUY",
            "ml_confidence": 70,
            "status": "completed",
            "ml_entry_price": 100.0,
            "exit_price": 110.0,
            "stop_loss_pips": None,
            "created_at": "2026-03-07T09:00:00Z",
            "highest_profit_pips": 10,
            "lowest_drawdown_pips": -1,
            "targets_hit": {"TP1": True, "TP2": True},
            "model_type": "ml",
            "strategy": None,
        },
        {
            "id": "tp-win-002",
            "symbol": "NDX.INDX",
            "timeframe": "15m",
            "ml_direction": "BUY",
            "ml_confidence": 68,
            "status": "completed",
            "ml_entry_price": 100.0,
            "exit_price": 108.0,
            "stop_loss_pips": None,
            "created_at": "2026-03-07T10:00:00Z",
            "highest_profit_pips": 8,
            "lowest_drawdown_pips": -2,
            "targets_hit": {"TP1": True},
            "model_type": "ml",
            "strategy": None,
        },
        {
            "id": "tp-win-003",
            "symbol": "NDX.INDX",
            "timeframe": "15m",
            "ml_direction": "BUY",
            "ml_confidence": 65,
            "status": "completed",
            "ml_entry_price": 100.0,
            "exit_price": 106.0,
            "stop_loss_pips": None,
            "created_at": "2026-03-07T11:00:00Z",
            "highest_profit_pips": 6,
            "lowest_drawdown_pips": -2,
            "targets_hit": {},
            "model_type": "ml",
            "strategy": None,
        },
        {
            "id": "tp-stop-004",
            "symbol": "NDX.INDX",
            "timeframe": "15m",
            "ml_direction": "BUY",
            "ml_confidence": 55,
            "status": "stopped",
            "ml_entry_price": 100.0,
            "exit_price": None,
            "stop_loss_pips": 10,
            "created_at": "2026-03-07T12:00:00Z",
            "highest_profit_pips": 2,
            "lowest_drawdown_pips": -10,
            "targets_hit": {},
            "model_type": "ml",
            "strategy": None,
        },
        {
            "id": "tp-expired-005",
            "symbol": "NDX.INDX",
            "timeframe": "15m",
            "ml_direction": "BUY",
            "ml_confidence": 50,
            "status": "expired",
            "ml_entry_price": 100.0,
            "exit_price": None,
            "stop_loss_pips": None,
            "created_at": "2026-03-07T13:00:00Z",
            "highest_profit_pips": 1,
            "lowest_drawdown_pips": -1,
            "targets_hit": {},
            "model_type": "ml",
            "strategy": None,
        },
        {
            "id": "tp-active-006",
            "symbol": "NDX.INDX",
            "timeframe": "15m",
            "ml_direction": "BUY",
            "ml_confidence": 49,
            "status": "active",
            "ml_entry_price": 100.0,
            "exit_price": None,
            "stop_loss_pips": None,
            "created_at": "2026-03-07T14:00:00Z",
            "highest_profit_pips": 0,
            "lowest_drawdown_pips": 0,
            "targets_hit": {},
            "model_type": "ml",
            "strategy": None,
        },
    ]

    client = _FakeClient([[], signal_rows])

    def _classify(sig, default_symbol=None):
        status = sig.get("status")
        if status == "completed":
            return status, True, 10.0
        if status == "stopped":
            return status, False, -10.0
        if status == "expired":
            return status, False, 0.0
        if status == "active":
            return status, False, 0.0
        return None, False, 0.0

    with patch.object(learning_module, "is_db_available", return_value=True), patch.object(
        learning_module, "get_supabase_client", return_value=client
    ), patch.object(learning_module, "_utc_now", return_value=fixed_now), patch.object(
        learning_module, "classify_signal", side_effect=_classify
    ):
        payload = await get_model_detail_analytics(model="ml", symbol="NDX.INDX", days=1, timeframe="all")

    assert payload["overview"]["completed"] == 3
    assert payload["overview"]["stopped"] == 1
    assert payload["overview"]["expired"] == 1
    assert payload["overview"]["active"] == 1
    assert payload["tp_hit_rates"] == {"TP1": 50.0, "TP2": 25.0, "TP3": 0, "TP4": 0}


@pytest.mark.asyncio
async def test_model_analysis_target_rates_use_common_resolved_denominator_per_symbol():
    learning_module = _load_learning_module("test_learning_model_analysis_rates")
    get_model_timeframe_analysis = learning_module.get_model_timeframe_analysis
    fixed_now = datetime(2026, 3, 7, 12, 0, tzinfo=timezone.utc)

    signal_rows = [
        {
            "id": "ndx-win-001",
            "symbol": "NDX.INDX",
            "timeframe": "15m",
            "ml_direction": "BUY",
            "status": "completed",
            "targets_hit": {"TP1": True, "TP2": True},
            "model_type": "ml",
            "strategy": None,
            "created_at": "2026-03-07T09:00:00Z",
        },
        {
            "id": "ndx-win-002",
            "symbol": "NDX.INDX",
            "timeframe": "15m",
            "ml_direction": "BUY",
            "status": "completed",
            "targets_hit": {"TP1": True},
            "model_type": "ml",
            "strategy": None,
            "created_at": "2026-03-07T10:00:00Z",
        },
        {
            "id": "ndx-stop-003",
            "symbol": "NDX.INDX",
            "timeframe": "15m",
            "ml_direction": "SELL",
            "status": "stopped",
            "targets_hit": {},
            "model_type": "ml",
            "strategy": None,
            "created_at": "2026-03-07T11:00:00Z",
        },
        {
            "id": "xau-win-004",
            "symbol": "XAUUSD",
            "timeframe": "15m",
            "ml_direction": "BUY",
            "status": "completed",
            "targets_hit": {"TP2": True},
            "model_type": "ml",
            "strategy": None,
            "created_at": "2026-03-07T12:00:00Z",
        },
        {
            "id": "xau-expired-005",
            "symbol": "XAUUSD",
            "timeframe": "15m",
            "ml_direction": "BUY",
            "status": "expired",
            "targets_hit": {},
            "model_type": "ml",
            "strategy": None,
            "created_at": "2026-03-07T13:00:00Z",
        },
        {
            "id": "pulse-win-006",
            "symbol": "NDX.INDX",
            "timeframe": "15m",
            "ml_direction": "BUY",
            "status": "completed",
            "targets_hit": {"TP1": True},
            "model_type": "pulse1",
            "strategy": None,
            "created_at": "2026-03-07T14:00:00Z",
        },
        {
            "id": "invalid-ml-007",
            "symbol": "NDX.INDX",
            "timeframe": "15m",
            "ml_direction": "SELL",
            "status": "expired",
            "targets_hit": {},
            "model_type": "ml",
            "strategy": None,
            "created_at": "2026-03-08T00:00:00Z",
            "resolution_reason": "market_closed_invalid",
        },
    ]

    client = _FakeClient([signal_rows])

    def _classify(sig, default_symbol=None):
        status = sig.get("status")
        if status == "completed":
            return status, True, 12.0
        if status == "stopped":
            return status, False, -8.0
        if status == "expired":
            return status, False, 0.0
        return None, False, 0.0

    with patch.object(learning_module, "is_db_available", return_value=True), patch.object(
        learning_module, "get_supabase_client", return_value=client
    ), patch.object(learning_module, "_utc_now", return_value=fixed_now), patch.object(
        learning_module, "classify_signal", side_effect=_classify
    ):
        payload = await get_model_timeframe_analysis(model="ml", symbol=None, timeframe=None, days=30)

    assert payload["completed"] == 3
    assert payload["stopped"] == 1
    assert payload["expired"] == 1
    assert payload["total_signals"] == 5
    assert payload["target_rates"] == {"TP1": 75.0, "TP2": 50.0, "TP3": 0.0, "TP4": 0.0}
    assert payload["by_symbol"]["NDX.INDX"]["target_rates"] == {
        "TP1": 66.7,
        "TP2": 33.3,
        "TP3": 0.0,
        "TP4": 0.0,
    }
    assert payload["by_symbol"]["XAUUSD"]["target_rates"] == {
        "TP1": 100.0,
        "TP2": 100.0,
        "TP3": 0.0,
        "TP4": 0.0,
    }
    assert all(sig.get("resolution_reason") != "market_closed_invalid" for sig in payload["signals"])


@pytest.mark.asyncio
async def test_model_detail_analytics_includes_smc_in_available_models_and_comparison():
    learning_module = _load_learning_module("test_learning_router_smc")
    get_model_detail_analytics = learning_module.get_model_detail_analytics

    signal_rows = [
        {
            "id": "smc-win-001",
            "symbol": "NDX.INDX",
            "timeframe": "5m",
            "ml_direction": "BUY",
            "ml_confidence": 78,
            "status": "completed",
            "ml_entry_price": 100.0,
            "exit_price": 110.0,
            "stop_loss_pips": 10,
            "created_at": "2026-03-06T12:00:00Z",
            "highest_profit_pips": 12,
            "lowest_drawdown_pips": -2,
            "targets_hit": {"TP1": True},
            "model_type": "order_block",
            "strategy": "SMART_MONEY_ZONES",
        },
        {
            "id": "ml-stop-002",
            "symbol": "NDX.INDX",
            "timeframe": "1h",
            "ml_direction": "SELL",
            "ml_confidence": 65,
            "status": "stopped",
            "ml_entry_price": 100.0,
            "exit_price": 106.0,
            "stop_loss_pips": 6,
            "created_at": "2026-03-06T11:00:00Z",
            "highest_profit_pips": 1,
            "lowest_drawdown_pips": -6,
            "targets_hit": {},
            "model_type": "ml",
            "strategy": None,
        },
    ]

    client = _FakeClient([[], signal_rows])

    with patch.object(learning_module, "is_db_available", return_value=True), patch.object(
        learning_module, "get_supabase_client", return_value=client
    ):
        payload = await get_model_detail_analytics(model="smc", symbol="NDX.INDX", days=1, timeframe="all")

    assert payload["meta"]["selected_model"] == "smc"
    assert payload["available_models"] == ["ml", "smc"]
    assert payload["available_timeframes"] == ["5m"]
    assert [row["model"] for row in payload["model_comparison"]] == ["ml", "smc"]
    assert payload["recent_signals"][0]["timeframe"] == "5m"