import importlib.util
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

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


def _prediction_row(**overrides):
    row = {
        "id": "row-001",
        "symbol": "NDX.INDX",
        "strategy": None,
        "ml_confidence": 60,
        "status": "completed",
        "targets_hit": {},
        "targets": {},
        "model_type": "ml",
        "timeframe": "30m",
        "created_at": _iso(datetime.now(timezone.utc)),
        "highest_profit_pips": 10,
        "lowest_drawdown_pips": -5,
        "stop_loss_pips": 50,
        "ml_entry_price": 100.0,
        "exit_price": 105.0,
        "exit_time": _iso(datetime.now(timezone.utc)),
        "ml_direction": "BUY",
        "factors": {},
    }
    row.update(overrides)
    return row


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
    def __init__(self, prediction_rows, snapshot_rows=None):
        self._prediction_rows = list(prediction_rows)
        self._snapshot_rows = list(snapshot_rows or [])

    def table(self, name):
        if name == "prediction_logs":
            return _FilteringQuery(self._prediction_rows)
        if name == "ai_panel_signal_snapshots":
            return _FilteringQuery(self._snapshot_rows)
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
async def test_strategy_performance_uses_main_scope_and_shared_signal_classification_semantics():
    learning_module = _load_learning_module("test_learning_strategy_router")
    now = datetime.now(timezone.utc)
    rows = [
        _prediction_row(
            id="main-win-001",
            created_at=_iso(now - timedelta(hours=2)),
            exit_time=_iso(now - timedelta(minutes=60)),
            status="stopped",
            targets_hit='{"TP1": true, "TP2": false, "TP3": false, "TP4": false}',
            targets='{"TP1": 105.0, "TP2": 110.0, "TP3": 115.0, "TP4": 120.0}',
            highest_profit_pips=2,
            lowest_drawdown_pips=-10,
            exit_price=None,
        ),
        _prediction_row(
            id="main-expired-002",
            created_at=_iso(now - timedelta(hours=3)),
            exit_time=None,
            status="expired",
            highest_profit_pips=0,
            lowest_drawdown_pips=0,
            exit_price=None,
        ),
        _prediction_row(
            id="main-loss-003",
            created_at=_iso(now - timedelta(hours=4)),
            exit_time=_iso(now - timedelta(hours=3, minutes=20)),
            status="stopped",
            highest_profit_pips=0,
            lowest_drawdown_pips=-50,
            exit_price=None,
        ),
    ]
    client = _FakeClient(rows)

    with patch.object(learning_module, "is_db_available", return_value=True), patch.object(
        learning_module, "get_supabase_client", return_value=client
    ):
        payload = await learning_module.get_strategy_performance(days=1)

    stats = payload["strategies"]["NDX.INDX"]["main"]
    assert payload["outcomes_count"] == 3
    assert payload["eligible_outcomes_count"] == 2
    assert payload["ml_predictions_count"] == 3
    assert stats["total_predictions"] == 3
    assert stats["resolved_signals"] == 2
    assert stats["expired"] == 1
    assert stats["correct"] == 1
    assert stats["accuracy"] == pytest.approx(50.0, abs=0.1)
    assert stats["target_hits"] == 1
    assert stats["stop_hits"] == 1
    assert stats["target_hit_rate"] == pytest.approx(50.0, abs=0.1)
    assert stats["stop_hit_rate"] == pytest.approx(50.0, abs=0.1)
    assert stats["tp_breakdown"]["TP1"] == 1
    assert stats["tp_hit_rates"]["TP1"] == pytest.approx(50.0, abs=0.1)
    assert payload["symbols"]["NDX.INDX"]["leaders"]["quality"]["scope"] == "main"


@pytest.mark.asyncio
async def test_strategy_performance_resolves_real_strategy_scopes_from_strategy_and_factors():
    learning_module = _load_learning_module("test_learning_strategy_router_scope_resolution")
    now = datetime.now(timezone.utc)
    rows = [
        _prediction_row(
            id="main-001",
            created_at=_iso(now - timedelta(hours=1)),
            exit_time=_iso(now - timedelta(minutes=20)),
        ),
        _prediction_row(
            id="balanced-001",
            strategy="balanced",
            created_at=_iso(now - timedelta(hours=2)),
            exit_time=_iso(now - timedelta(hours=1, minutes=20)),
        ),
        _prediction_row(
            id="precision-001",
            strategy=None,
            factors='{"selected_strategy": "nasdaq_precision"}',
            created_at=_iso(now - timedelta(hours=3)),
            exit_time=_iso(now - timedelta(hours=2, minutes=15)),
        ),
        _prediction_row(
            id="aggressive-001",
            strategy=None,
            model_type="ml:aggressive",
            factors={},
            created_at=_iso(now - timedelta(hours=3, minutes=30)),
            exit_time=_iso(now - timedelta(hours=2, minutes=45)),
        ),
        _prediction_row(
            id="ignored-non-ml-001",
            model_type="pulse2",
            strategy="balanced",
            created_at=_iso(now - timedelta(hours=4)),
        ),
    ]
    client = _FakeClient(rows)

    with patch.object(learning_module, "is_db_available", return_value=True), patch.object(
        learning_module, "get_supabase_client", return_value=client
    ):
        payload = await learning_module.get_strategy_performance(days=1)

    ndx_scopes = payload["strategies"]["NDX.INDX"]
    assert payload["predictions_count"] == 5
    assert payload["ml_predictions_count"] == 4
    assert ndx_scopes["main"]["total_predictions"] == 1
    assert ndx_scopes["balanced"]["total_predictions"] == 1
    assert ndx_scopes["aggressive"]["total_predictions"] == 1
    assert ndx_scopes["nasdaq_precision"]["total_predictions"] == 1
    assert payload["symbols"]["NDX.INDX"]["available_scopes"] == ["main", "balanced", "aggressive", "nasdaq_precision"]


@pytest.mark.asyncio
async def test_strategy_performance_excludes_low_confidence_scoped_ml_rows_from_scope_metrics():
    learning_module = _load_learning_module("test_learning_strategy_router_scope_thresholds")
    now = datetime.now(timezone.utc)
    rows = [
        _prediction_row(
            id="main-001",
            strategy=None,
            model_type="ml:main",
            ml_confidence=51,
            created_at=_iso(now - timedelta(hours=1)),
            exit_time=_iso(now - timedelta(minutes=20)),
        ),
        _prediction_row(
            id="balanced-low-001",
            strategy="balanced",
            model_type="ml:balanced",
            ml_confidence=54.9,
            created_at=_iso(now - timedelta(hours=2)),
            exit_time=_iso(now - timedelta(hours=1, minutes=20)),
        ),
        _prediction_row(
            id="balanced-good-002",
            strategy="balanced",
            model_type="ml:balanced",
            ml_confidence=55.0,
            created_at=_iso(now - timedelta(hours=3)),
            exit_time=_iso(now - timedelta(hours=2, minutes=20)),
        ),
    ]
    client = _FakeClient(rows)

    with patch.object(learning_module, "is_db_available", return_value=True), patch.object(
        learning_module, "get_supabase_client", return_value=client
    ):
        payload = await learning_module.get_strategy_performance(days=1)

    ndx_scopes = payload["strategies"]["NDX.INDX"]
    assert payload["predictions_count"] == 3
    assert payload["ml_predictions_count"] == 2
    assert ndx_scopes["main"]["total_predictions"] == 1
    assert ndx_scopes["balanced"]["total_predictions"] == 1
    assert payload["symbols"]["NDX.INDX"]["available_scopes"] == ["main", "balanced"]


@pytest.mark.asyncio
async def test_strategy_performance_tp_rates_are_independent_and_exclude_expired_from_denominator():
    learning_module = _load_learning_module("test_learning_strategy_router_independent_tp")
    now = datetime.now(timezone.utc)
    rows = [
        _prediction_row(
            id="balanced-win-001",
            symbol="XAUUSD",
            strategy="balanced",
            created_at=_iso(now - timedelta(hours=1)),
            exit_time=_iso(now - timedelta(minutes=10)),
            targets_hit={"TP1": True, "TP2": True, "TP3": True, "TP4": False},
            highest_profit_pips=25,
            lowest_drawdown_pips=-5,
            exit_price=103.0,
        ),
        _prediction_row(
            id="balanced-win-002",
            symbol="XAUUSD",
            strategy="balanced",
            created_at=_iso(now - timedelta(hours=2)),
            exit_time=_iso(now - timedelta(hours=1, minutes=10)),
            targets_hit={"TP1": True, "TP2": True, "TP3": False, "TP4": False},
            highest_profit_pips=20,
            lowest_drawdown_pips=-4,
            exit_price=102.0,
        ),
        _prediction_row(
            id="balanced-win-003",
            symbol="XAUUSD",
            strategy="balanced",
            created_at=_iso(now - timedelta(hours=3)),
            exit_time=_iso(now - timedelta(hours=2, minutes=20)),
            targets_hit={"TP1": True, "TP2": False, "TP3": False, "TP4": False},
            highest_profit_pips=10,
            lowest_drawdown_pips=-3,
            exit_price=101.0,
        ),
        _prediction_row(
            id="balanced-loss-004",
            symbol="XAUUSD",
            strategy="balanced",
            created_at=_iso(now - timedelta(hours=4)),
            exit_time=_iso(now - timedelta(hours=3, minutes=20)),
            status="stopped",
            targets_hit={},
            highest_profit_pips=0,
            lowest_drawdown_pips=-50,
            exit_price=None,
        ),
        _prediction_row(
            id="balanced-expired-005",
            symbol="XAUUSD",
            strategy="balanced",
            created_at=_iso(now - timedelta(hours=5)),
            exit_time=None,
            status="expired",
            targets_hit={"TP1": True, "TP2": True, "TP3": True, "TP4": True},
            highest_profit_pips=0,
            lowest_drawdown_pips=0,
            exit_price=None,
        ),
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
async def test_strategy_performance_infers_missing_tp1_from_profit_excursion():
    learning_module = _load_learning_module("test_learning_strategy_router_inferred_tp1")
    now = datetime.now(timezone.utc)
    rows = [
        _prediction_row(
            id="balanced-inferred-win-001",
            symbol="XAUUSD",
            strategy="balanced",
            created_at=_iso(now - timedelta(hours=1)),
            exit_time=_iso(now - timedelta(minutes=15)),
            status="stopped",
            targets_hit={},
            highest_profit_pips=8.3,
            lowest_drawdown_pips=-15,
            stop_loss_pips=15,
            exit_price=None,
        ),
        _prediction_row(
            id="balanced-plain-loss-002",
            symbol="XAUUSD",
            strategy="balanced",
            created_at=_iso(now - timedelta(hours=2)),
            exit_time=_iso(now - timedelta(hours=1, minutes=20)),
            status="stopped",
            targets_hit={},
            highest_profit_pips=3.0,
            lowest_drawdown_pips=-15,
            stop_loss_pips=15,
            exit_price=None,
        ),
    ]
    client = _FakeClient(rows)

    with patch.object(learning_module, "is_db_available", return_value=True), patch.object(
        learning_module, "get_supabase_client", return_value=client
    ):
        payload = await learning_module.get_strategy_performance(days=1)

    stats = payload["strategies"]["XAUUSD"]["balanced"]
    assert stats["with_outcome"] == 2
    assert stats["correct"] == 1
    assert stats["target_hits"] == 1
    assert stats["stop_hits"] == 1
    assert stats["accuracy"] == pytest.approx(50.0, abs=0.1)
    assert stats["target_hit_rate"] == pytest.approx(50.0, abs=0.1)
    assert stats["stop_hit_rate"] == pytest.approx(50.0, abs=0.1)
    assert stats["tp_breakdown"] == {"TP1": 1, "TP2": 0, "TP3": 0, "TP4": 0}


@pytest.mark.asyncio
async def test_smc_performance_includes_smart_money_zone_rows_in_timeframe_analytics():
    learning_module = _load_learning_module("test_learning_smc_performance")
    now = datetime.now(timezone.utc)
    rows = [
        _prediction_row(
            id="smc-win-001",
            symbol="NDX.INDX",
            strategy="SMART_MONEY_ZONES",
            model_type="smc",
            timeframe="5m",
            created_at=_iso(now - timedelta(hours=1)),
            exit_time=_iso(now - timedelta(minutes=35)),
            highest_profit_pips=12,
            lowest_drawdown_pips=-3,
            stop_loss_pips=8,
            exit_price=110.0,
            targets_hit={"TP1": True},
        ),
        _prediction_row(
            id="smc-expired-002",
            symbol="NDX.INDX",
            strategy="SMART_MONEY_ZONES",
            model_type="order_block",
            timeframe="15m",
            created_at=_iso(now - timedelta(hours=2)),
            exit_time=None,
            status="expired",
            highest_profit_pips=4,
            lowest_drawdown_pips=-2,
            stop_loss_pips=8,
            exit_price=None,
            targets_hit={},
        ),
        _prediction_row(
            id="non-smc-003",
            symbol="NDX.INDX",
            strategy=None,
            model_type="ml",
            timeframe="1h",
            created_at=_iso(now - timedelta(hours=3)),
            exit_time=_iso(now - timedelta(hours=2, minutes=20)),
            status="stopped",
            highest_profit_pips=1,
            lowest_drawdown_pips=-6,
            stop_loss_pips=6,
            exit_price=None,
            targets_hit={},
        ),
    ]
    client = _FakeClient(rows)

    with patch.object(learning_module, "is_db_available", return_value=True), patch.object(
        learning_module, "get_supabase_client", return_value=client
    ):
        payload = await learning_module.get_smc_performance(days=7)

    assert payload["smc_predictions_count"] == 2
    assert payload["eligible_outcomes_count"] == 1
    assert payload["timeframes"]["NDX.INDX"]["5m"]["completed"] == 1
    assert payload["timeframes"]["NDX.INDX"]["15m"]["expired"] == 1
    assert payload["symbols"]["NDX.INDX"]["total_predictions"] == 2
    assert payload["overall_summary"]["resolved_signals"] == 1


@pytest.mark.asyncio
async def test_smc_performance_bootstraps_when_database_has_no_smc_history():
    learning_module = _load_learning_module("test_learning_smc_performance_bootstrap")
    now = datetime.now(timezone.utc)
    bootstrap_rows = [
        _prediction_row(
            id="smc-bootstrap-001",
            symbol="XAUUSD",
            strategy="SMART_MONEY_ZONES",
            model_type="smc",
            timeframe="1h",
            created_at=_iso(now - timedelta(minutes=20)),
            exit_time=None,
            status="active",
            highest_profit_pips=0,
            lowest_drawdown_pips=0,
            targets_hit={},
        )
    ]
    client = _FakeClient([])

    with patch.object(learning_module, "is_db_available", return_value=True), patch.object(
        learning_module, "get_supabase_client", return_value=client
    ), patch.object(
        learning_module,
        "_fetch_prediction_logs_window",
        side_effect=[[], bootstrap_rows],
    ) as mock_fetch, patch.object(
        learning_module,
        "_bootstrap_smc_predictions_if_empty",
        new_callable=AsyncMock,
    ) as mock_bootstrap:
        payload = await learning_module.get_smc_performance(days=7)

    assert mock_fetch.await_count == 2
    mock_bootstrap.assert_awaited_once()
    assert payload["smc_predictions_count"] == 1
    assert payload["timeframes"]["XAUUSD"]["1h"]["active"] == 1
    assert payload["symbols"]["XAUUSD"]["total_predictions"] == 1


@pytest.mark.asyncio
async def test_ai_panel_performance_aggregates_hourly_panel_signals_and_snapshots():
    learning_module = _load_learning_module("test_learning_ai_panel_performance")
    now = datetime.now(timezone.utc)
    rows = [
        _prediction_row(
            id="ai-panel-win-001",
            symbol="NDX.INDX",
            strategy="AI_PANEL_HOURLY",
            model_type="ai_panel",
            timeframe="1h",
            created_at=_iso(now - timedelta(hours=3)),
            exit_time=_iso(now - timedelta(hours=2, minutes=10)),
            status="completed",
            highest_profit_pips=18,
            lowest_drawdown_pips=-4,
            stop_loss_pips=9,
            exit_price=110.0,
            targets_hit={"TP1": True, "TP2": False, "TP3": False, "TP4": False},
        ),
        _prediction_row(
            id="ai-panel-loss-002",
            symbol="NDX.INDX",
            strategy="AI_PANEL_HOURLY",
            model_type="ai_panel",
            timeframe="1h",
            created_at=_iso(now - timedelta(hours=2)),
            exit_time=_iso(now - timedelta(hours=1, minutes=5)),
            status="stopped",
            highest_profit_pips=3,
            lowest_drawdown_pips=-11,
            stop_loss_pips=9,
            exit_price=None,
            targets_hit={},
        ),
        _prediction_row(
            id="non-ai-panel-003",
            symbol="NDX.INDX",
            strategy="balanced",
            model_type="ml:balanced",
            timeframe="30m",
            created_at=_iso(now - timedelta(hours=1)),
            exit_time=_iso(now - timedelta(minutes=20)),
        ),
    ]
    snapshots = [
        {"id": 1, "symbol": "NDX.INDX", "created_at": _iso(now - timedelta(hours=3))},
        {"id": 2, "symbol": "NDX.INDX", "created_at": _iso(now - timedelta(hours=2))},
        {"id": 3, "symbol": "XAUUSD", "created_at": _iso(now - timedelta(hours=1))},
    ]
    client = _FakeClient(rows, snapshots)

    with patch.object(learning_module, "is_db_available", return_value=True), patch.object(
        learning_module, "get_supabase_client", return_value=client
    ):
        payload = await learning_module.get_ai_panel_performance(days=1)

    assert payload["ai_panel_predictions_count"] == 2
    assert payload["ai_panel_snapshots_count"] == 3
    assert payload["eligible_outcomes_count"] == 2
    ndx_scope = payload["strategies"]["NDX.INDX"]["hourly_panel"]
    assert ndx_scope["total_predictions"] == 2
    assert ndx_scope["resolved_signals"] == 2
    assert ndx_scope["completed"] == 1
    assert ndx_scope["stopped"] == 1
    assert ndx_scope["target_hits"] == 1
    assert ndx_scope["stop_hits"] == 1
    assert ndx_scope["accuracy"] == pytest.approx(50.0, abs=0.1)
    assert payload["symbols"]["NDX.INDX"]["snapshot_count"] == 2
    assert payload["symbols"]["NDX.INDX"]["available_scopes"] == ["hourly_panel"]
    assert payload["overall_summary"]["leaders"]["quality"]["scope"] == "hourly_panel"


@pytest.mark.asyncio
async def test_recent_signals_applies_days_filter_and_returns_normalized_model_and_scope():
    learning_module = _load_learning_module("test_learning_recent_signals_router")
    now = datetime.now(timezone.utc)
    rows = [
        _prediction_row(
            id="recent-win-001",
            strategy="balanced",
            created_at=_iso(now - timedelta(hours=1)),
            exit_time=_iso(now - timedelta(minutes=30)),
            status="stopped",
            targets_hit='{"TP1": true, "TP2": false, "TP3": false, "TP4": false}',
            targets='{"TP1": 105.0, "TP2": 110.0, "TP3": 115.0, "TP4": 120.0}',
            highest_profit_pips=2,
            lowest_drawdown_pips=-10,
            exit_price=None,
            ml_target_price=105.0,
            ml_stop_price=50.0,
            ml_confidence=67,
        ),
        _prediction_row(
            id="stale-loss-002",
            strategy="aggressive",
            created_at=_iso(now - timedelta(days=2, hours=1)),
            exit_time=_iso(now - timedelta(days=2, minutes=10)),
            status="stopped",
            targets_hit={},
            highest_profit_pips=0,
            lowest_drawdown_pips=-50,
            exit_price=50.0,
            ml_target_price=110.0,
            ml_stop_price=50.0,
            ml_confidence=40,
        ),
    ]
    client = _FakeClient(rows)

    with patch.object(learning_module, "is_db_available", return_value=True), patch.object(
        learning_module, "get_supabase_client", return_value=client
    ):
        payload = await learning_module.get_recent_signals_endpoint(days=1, limit=10, include_active=True, model="ml")

    assert payload["count"] == 1
    signal = payload["signals"][0]
    assert signal["id"] == "recent-win-001"
    assert signal["status"] == "completed"
    assert signal["pnl_pips"] == 5.0
    assert signal["duration_minutes"] == pytest.approx(30.0, abs=0.1)
    assert signal["normalized_model"] == "ml"
    assert signal["strategy_scope"] == "balanced"


@pytest.mark.asyncio
async def test_recent_signals_filters_by_strategy_scope_and_preserves_main_scope():
    learning_module = _load_learning_module("test_learning_recent_signals_router_strategy_scope")
    now = datetime.now(timezone.utc)
    rows = [
        _prediction_row(
            id="main-001",
            strategy=None,
            created_at=_iso(now - timedelta(hours=1)),
            exit_time=_iso(now - timedelta(minutes=20)),
        ),
        _prediction_row(
            id="aggressive-001",
            strategy="aggressive",
            created_at=_iso(now - timedelta(hours=2)),
            exit_time=_iso(now - timedelta(hours=1, minutes=10)),
        ),
        _prediction_row(
            id="ignored-non-ml-001",
            model_type="pulse3",
            strategy="aggressive",
            created_at=_iso(now - timedelta(hours=3)),
        ),
    ]
    client = _FakeClient(rows)

    with patch.object(learning_module, "is_db_available", return_value=True), patch.object(
        learning_module, "get_supabase_client", return_value=client
    ):
        payload = await learning_module.get_recent_signals_endpoint(
            days=1,
            limit=10,
            include_active=True,
            model="ml",
            strategy_scope="main",
        )

    assert payload["count"] == 1
    assert payload["strategy_scope"] == "main"
    signal = payload["signals"][0]
    assert signal["id"] == "main-001"
    assert signal["strategy_scope"] == "main"
    assert signal["normalized_model"] == "ml"