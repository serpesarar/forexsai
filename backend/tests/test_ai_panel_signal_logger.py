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


class _SnapshotTable:
    def __init__(self, client):
        self._client = client
        self._eq_filters = []
        self._order_field = None
        self._order_desc = False
        self._limit = None

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, field, value):
        self._eq_filters.append((field, value))
        return self

    def order(self, field, desc=False):
        self._order_field = field
        self._order_desc = desc
        return self

    def limit(self, value):
        self._limit = value
        return self

    def execute(self):
        rows = list(self._client.snapshot_rows)
        for field, value in self._eq_filters:
            rows = [row for row in rows if row.get(field) == value]
        if self._order_field:
            rows.sort(key=lambda row: row.get(self._order_field), reverse=self._order_desc)
        if self._limit is not None:
            rows = rows[: self._limit]
        return {"data": rows, "error": None}

    def insert(self, data):
        self._client.insert_calls.append(data)
        if self._client.insert_error:
            return {"data": None, "error": self._client.insert_error}
        stored = dict(data)
        stored.setdefault("created_at", self._client.inserted_created_at)
        self._client.snapshot_rows.append(stored)
        return {"data": [stored], "error": None}


class _FakeClient:
    def __init__(self, snapshot_rows=None, insert_error=None, inserted_created_at=None):
        self.snapshot_rows = list(snapshot_rows or [])
        self.insert_error = insert_error
        self.insert_calls = []
        self.inserted_created_at = inserted_created_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def table(self, name):
        if name == "ai_panel_signal_snapshots":
            return _SnapshotTable(self)
        raise AssertionError(f"Unexpected table requested: {name}")


def _sample_result(direction: str = "HOLD"):
    return {
        "claude_analysis": {
            "claude_direction": direction,
            "claude_confidence": 12,
            "recommended_entry": None,
            "recommended_sl": None,
            "recommended_tp": None,
            "panel_signal": {"event_risk": {"level": "LOW", "events": []}},
            "market_context": {},
            "analysis_meta": {
                "market_session": "closed",
                "market_open": False,
                "generated_at": "2026-03-18T12:00:00Z",
                "model": "test-model",
                "prompt_version": "v-test",
            },
            "model_used": "test-model",
        },
        "ml_prediction": {},
        "ta_snapshot": {},
    }


def _load_logger_module(module_name: str):
    analysis_module = SimpleNamespace(get_ai_panel_analysis=AsyncMock())
    prediction_module = SimpleNamespace(log_prediction=AsyncMock())

    with patch.dict(
        sys.modules,
        {
            "services.ai_panel_analysis_service": analysis_module,
            "services.prediction_logger": prediction_module,
        },
    ):
        module_path = backend_dir / "services" / "ai_panel_signal_logger.py"
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        logger_module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(logger_module)
        return logger_module, analysis_module.get_ai_panel_analysis, prediction_module.log_prediction


@pytest.mark.asyncio
async def test_hourly_logger_skips_symbols_with_recent_persisted_snapshot():
    logger_module, mock_get_analysis, _mock_log_prediction = _load_logger_module("test_ai_panel_signal_logger_skip")
    now = datetime(2026, 3, 18, 13, 0, tzinfo=timezone.utc)
    recent_snapshot = (now - timedelta(minutes=20)).isoformat().replace("+00:00", "Z")
    client = _FakeClient(snapshot_rows=[{"symbol": "NDX.INDX", "created_at": recent_snapshot}])

    mock_get_analysis.return_value = _sample_result()

    with patch.object(logger_module, "AI_PANEL_TRACKED_SYMBOLS", ["NDX.INDX"]), patch.object(
        logger_module, "is_db_available", return_value=True
    ), patch.object(logger_module, "get_supabase_client", return_value=client), patch.object(
        logger_module, "_utc_now", return_value=now
    ):
        await logger_module.log_ai_panel_signals_if_needed()

    mock_get_analysis.assert_not_awaited()
    assert client.insert_calls == []


@pytest.mark.asyncio
async def test_hourly_logger_retries_immediately_after_snapshot_persist_failure():
    logger_module, mock_get_analysis, _mock_log_prediction = _load_logger_module("test_ai_panel_signal_logger_retry")
    now = datetime(2026, 3, 18, 13, 0, tzinfo=timezone.utc)
    client = _FakeClient(insert_error="boom", inserted_created_at=now.isoformat().replace("+00:00", "Z"))

    mock_get_analysis.return_value = _sample_result()

    with patch.object(logger_module, "AI_PANEL_TRACKED_SYMBOLS", ["NDX.INDX"]), patch.object(
        logger_module, "is_db_available", return_value=True
    ), patch.object(logger_module, "get_supabase_client", return_value=client), patch.object(
        logger_module, "_utc_now", return_value=now
    ):
        await logger_module.log_ai_panel_signals_if_needed()
        assert "NDX.INDX" not in logger_module._last_ai_panel_log
        assert mock_get_analysis.await_count == 1

        client.insert_error = None
        await logger_module.log_ai_panel_signals_if_needed()

    assert mock_get_analysis.await_count == 2
    assert len(client.insert_calls) == 2
    assert logger_module._last_ai_panel_log["NDX.INDX"] == now
