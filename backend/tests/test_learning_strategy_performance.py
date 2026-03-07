import importlib.util
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest


backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_iso(value):
    if not isinstance(value, str):
        return value
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class _FilteringQuery:
    def __init__(self, rows):
        self._rows = list(rows)
        self._eq_filters = []
        self._neq_filters = []
        self._gte_filters = []
        self._lt_filters = []
        self._limit = None
        self._order_field = None
        self._order_desc = False

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, field, value):
        self._eq_filters.append((field, value))
        return self

    def neq(self, field, value):
        self._neq_filters.append((field, value))
        return self

    def gte(self, field, value):
        self._gte_filters.append((field, value))
        return self

    def lt(self, field, value):
        self._lt_filters.append((field, value))
        return self

    def order(self, field, desc=False):
        self._order_field = field
        self._order_desc = desc
        return self

    def limit(self, value):
        self._limit = value
        return self

    def execute(self):
        rows = list(self._rows)
        for field, value in self._eq_filters:
            rows = [row for row in rows if row.get(field) == value]
        for field, value in self._neq_filters:
            rows = [row for row in rows if row.get(field) != value]
        for field, value in self._gte_filters:
            compare = _parse_iso(value)
            rows = [row for row in rows if (parsed := _parse_iso(row.get(field))) is not None and parsed >= compare]
        for field, value in self._lt_filters:
            compare = _parse_iso(value)
            rows = [row for row in rows if (parsed := _parse_iso(row.get(field))) is not None and parsed < compare]
        if self._order_field:
            rows.sort(key=lambda row: _parse_iso(row.get(self._order_field)) or row.get(self._order_field), reverse=self._order_desc)
        if self._limit is not None:
            rows = rows[: self._limit]
        return SimpleNamespace(data=rows, error=None)


class _FakeClient:
    def __init__(self, prediction_rows):
        self._prediction_rows = list(prediction_rows)

    def table(self, name):
        if name == "prediction_logs":
            return _FilteringQuery(self._prediction_rows)
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
async def test_strategy_performance_uses_shared_signal_classification_semantics():
    learning_module = _load_learning_module("test_learning_strategy_router")
    now = datetime.now(timezone.utc)
    rows = [
        {
            "id": "strategy-win-001",
            "symbol": "NDX.INDX",
            "strategy": None,
            "ml_confidence": 70,
            "status": "stopped",
            "targets_hit": '"{\\"TP1\\": true, \\"TP2\\": false, \\"TP3\\": false, \\"TP4\\": false}"',
            "targets": '"{\\"TP1\\": 105.0, \\"TP2\\": 110.0, \\"TP3\\": 115.0, \\"TP4\\": 120.0}"',
            "model_type": "ml",
            "created_at": _iso(now - timedelta(hours=2)),
            "highest_profit_pips": 2,
            "lowest_drawdown_pips": -10,
            "stop_loss_pips": 50,
            "ml_entry_price": 100.0,
            "exit_price": None,
            "ml_direction": "BUY",
        },
        {
            "id": "strategy-expired-002",
            "symbol": "NDX.INDX",
            "strategy": None,
            "ml_confidence": 72,
            "status": "expired",
            "targets_hit": {},
            "targets": {},
            "model_type": "ml",
            "created_at": _iso(now - timedelta(hours=3)),
            "highest_profit_pips": 0,
            "lowest_drawdown_pips": 0,
            "stop_loss_pips": 50,
            "ml_entry_price": 100.0,
            "exit_price": None,
            "ml_direction": "BUY",
        },
        {
            "id": "strategy-loss-003",
            "symbol": "NDX.INDX",
            "strategy": None,
            "ml_confidence": 69,
            "status": "stopped",
            "targets_hit": {},
            "targets": {},
            "model_type": "ml",
            "created_at": _iso(now - timedelta(hours=4)),
            "highest_profit_pips": 0,
            "lowest_drawdown_pips": -50,
            "stop_loss_pips": 50,
            "ml_entry_price": 100.0,
            "exit_price": None,
            "ml_direction": "BUY",
        },
    ]
    client = _FakeClient(rows)

    with patch.object(learning_module, "is_db_available", return_value=True), patch.object(
        learning_module, "get_supabase_client", return_value=client
    ):
        payload = await learning_module.get_strategy_performance(days=1)

    stats = payload["strategies"]["NDX.INDX"]["ultra_safe"]
    assert payload["outcomes_count"] == 3
    assert payload["eligible_outcomes_count"] == 2
    assert stats["total_predictions"] == 3
    assert stats["with_outcome"] == 2
    assert stats["correct"] == 1
    assert stats["accuracy"] == pytest.approx(50.0, abs=0.1)
    assert stats["target_hits"] == 1
    assert stats["stop_hits"] == 1
    assert stats["target_hit_rate"] == pytest.approx(50.0, abs=0.1)
    assert stats["stop_hit_rate"] == pytest.approx(50.0, abs=0.1)
    assert stats["tp_breakdown"]["TP1"] == 1
    assert stats["tp_hit_rates"]["TP1"] == pytest.approx(50.0, abs=0.1)
    assert stats["tp_hit_rates"]["TP2"] == 0.0


@pytest.mark.asyncio
async def test_strategy_performance_tp_rates_are_independent_and_exclude_expired_from_denominator():
    learning_module = _load_learning_module("test_learning_strategy_router_independent_tp")
    now = datetime.now(timezone.utc)
    rows = [
        {
            "id": "balanced-win-001",
            "symbol": "XAUUSD",
            "strategy": None,
            "ml_confidence": 60,
            "status": "completed",
            "targets_hit": {"TP1": True, "TP2": True, "TP3": True, "TP4": False},
            "targets": {},
            "model_type": "ml",
            "created_at": _iso(now - timedelta(hours=1)),
            "highest_profit_pips": 25,
            "lowest_drawdown_pips": -5,
            "stop_loss_pips": 50,
            "ml_entry_price": 100.0,
            "exit_price": 103.0,
            "ml_direction": "BUY",
        },
        {
            "id": "balanced-win-002",
            "symbol": "XAUUSD",
            "strategy": None,
            "ml_confidence": 60,
            "status": "completed",
            "targets_hit": {"TP1": True, "TP2": True, "TP3": False, "TP4": False},
            "targets": {},
            "model_type": "ml",
            "created_at": _iso(now - timedelta(hours=2)),
            "highest_profit_pips": 20,
            "lowest_drawdown_pips": -4,
            "stop_loss_pips": 50,
            "ml_entry_price": 100.0,
            "exit_price": 102.0,
            "ml_direction": "BUY",
        },
        {
            "id": "balanced-win-003",
            "symbol": "XAUUSD",
            "strategy": None,
            "ml_confidence": 60,
            "status": "completed",
            "targets_hit": {"TP1": True, "TP2": False, "TP3": False, "TP4": False},
            "targets": {},
            "model_type": "ml",
            "created_at": _iso(now - timedelta(hours=3)),
            "highest_profit_pips": 10,
            "lowest_drawdown_pips": -3,
            "stop_loss_pips": 50,
            "ml_entry_price": 100.0,
            "exit_price": 101.0,
            "ml_direction": "BUY",
        },
        {
            "id": "balanced-loss-004",
            "symbol": "XAUUSD",
            "strategy": None,
            "ml_confidence": 60,
            "status": "stopped",
            "targets_hit": {},
            "targets": {},
            "model_type": "ml",
            "created_at": _iso(now - timedelta(hours=4)),
            "highest_profit_pips": 0,
            "lowest_drawdown_pips": -50,
            "stop_loss_pips": 50,
            "ml_entry_price": 100.0,
            "exit_price": None,
            "ml_direction": "BUY",
        },
        {
            "id": "balanced-expired-005",
            "symbol": "XAUUSD",
            "strategy": None,
            "ml_confidence": 60,
            "status": "expired",
            "targets_hit": {"TP1": True, "TP2": True, "TP3": True, "TP4": True},
            "targets": {},
            "model_type": "ml",
            "created_at": _iso(now - timedelta(hours=5)),
            "highest_profit_pips": 0,
            "lowest_drawdown_pips": 0,
            "stop_loss_pips": 50,
            "ml_entry_price": 100.0,
            "exit_price": None,
            "ml_direction": "BUY",
        },
    ]
    client = _FakeClient(rows)

    with patch.object(learning_module, "is_db_available", return_value=True), patch.object(
        learning_module, "get_supabase_client", return_value=client
    ):
        payload = await learning_module.get_strategy_performance(days=1)

    stats = payload["strategies"]["XAUUSD"]["balanced"]
    assert stats["with_outcome"] == 4
    assert stats["target_hits"] == 3
    assert stats["stop_hits"] == 1
    assert stats["target_hit_rate"] == pytest.approx(75.0, abs=0.1)
    assert stats["stop_hit_rate"] == pytest.approx(25.0, abs=0.1)
    assert stats["tp_breakdown"] == {"TP1": 3, "TP2": 2, "TP3": 1, "TP4": 0}
    assert stats["tp_hit_rates"] == {
        "TP1": pytest.approx(75.0, abs=0.1),
        "TP2": pytest.approx(50.0, abs=0.1),
        "TP3": pytest.approx(25.0, abs=0.1),
        "TP4": pytest.approx(0.0, abs=0.1),
    }


@pytest.mark.asyncio
async def test_recent_signals_applies_days_filter_and_normalizes_status_and_pnl():
    learning_module = _load_learning_module("test_learning_recent_signals_router")
    now = datetime.now(timezone.utc)
    rows = [
        {
            "id": "recent-win-001",
            "symbol": "NDX.INDX",
            "timeframe": "30m",
            "ml_direction": "BUY",
            "ml_confidence": 67,
            "ml_entry_price": 100.0,
            "ml_target_price": 105.0,
            "ml_stop_price": 50.0,
            "model_type": "ml",
            "strategy": "balanced",
            "status": "stopped",
            "targets_hit": '"{\\"TP1\\": true, \\"TP2\\": false, \\"TP3\\": false, \\"TP4\\": false}"',
            "targets": '"{\\"TP1\\": 105.0, \\"TP2\\": 110.0, \\"TP3\\": 115.0, \\"TP4\\": 120.0}"',
            "highest_profit_pips": 2,
            "lowest_drawdown_pips": -10,
            "stop_loss_pips": 50,
            "exit_price": None,
            "exit_time": _iso(now - timedelta(minutes=30)),
            "created_at": _iso(now - timedelta(hours=1)),
        },
        {
            "id": "stale-loss-002",
            "symbol": "NDX.INDX",
            "timeframe": "30m",
            "ml_direction": "BUY",
            "ml_confidence": 40,
            "ml_entry_price": 100.0,
            "ml_target_price": 110.0,
            "ml_stop_price": 50.0,
            "model_type": "ml",
            "strategy": "aggressive",
            "status": "stopped",
            "targets_hit": {},
            "targets": {},
            "highest_profit_pips": 0,
            "lowest_drawdown_pips": -50,
            "stop_loss_pips": 50,
            "exit_price": 50.0,
            "exit_time": _iso(now - timedelta(days=2, minutes=10)),
            "created_at": _iso(now - timedelta(days=2, hours=1)),
        },
    ]
    client = _FakeClient(rows)

    with patch.object(learning_module, "is_db_available", return_value=True), patch.object(
        learning_module, "get_supabase_client", return_value=client
    ):
        payload = await learning_module.get_recent_signals_endpoint(days=1, limit=10, include_active=True)

    assert payload["count"] == 1
    signal = payload["signals"][0]
    assert signal["id"] == "recent-win-001"
    assert signal["status"] == "completed"
    assert signal["pnl_pips"] == 5.0
    assert signal["duration_minutes"] == pytest.approx(30.0, abs=0.1)


@pytest.mark.asyncio
async def test_recent_signals_keeps_plain_stopped_losses_negative():
    learning_module = _load_learning_module("test_learning_recent_signals_router_stopped")
    now = datetime.now(timezone.utc)
    rows = [
        {
            "id": "recent-loss-001",
            "symbol": "NDX.INDX",
            "timeframe": "30m",
            "ml_direction": "BUY",
            "ml_confidence": 44,
            "ml_entry_price": 100.0,
            "ml_target_price": 110.0,
            "ml_stop_price": 95.0,
            "model_type": "ml",
            "strategy": "aggressive",
            "status": "stopped",
            "targets_hit": {},
            "targets": {},
            "highest_profit_pips": 0,
            "lowest_drawdown_pips": -50,
            "stop_loss_pips": 50,
            "exit_price": None,
            "exit_time": _iso(now - timedelta(minutes=10)),
            "created_at": _iso(now - timedelta(hours=1)),
        },
    ]
    client = _FakeClient(rows)

    with patch.object(learning_module, "is_db_available", return_value=True), patch.object(
        learning_module, "get_supabase_client", return_value=client
    ):
        payload = await learning_module.get_recent_signals_endpoint(days=1, limit=10, include_active=True)

    assert payload["count"] == 1
    signal = payload["signals"][0]
    assert signal["status"] == "stopped"
    assert signal["pnl_pips"] == -50.0