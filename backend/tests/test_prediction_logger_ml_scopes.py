import os
import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

backend_dir = os.path.join(os.path.dirname(__file__), '..')
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

with patch.dict(
    sys.modules,
    {
        "anthropic": SimpleNamespace(Anthropic=object),
        "services.error_analysis_service": SimpleNamespace(save_candle_snapshot=None),
    },
):
    import services.prediction_logger as prediction_logger
    from services.prediction_logger import _resolve_logging_identity, log_prediction, log_smc_prediction


def test_resolve_logging_identity_maps_strategy_only_ml_scope_to_scoped_model_type():
    model_type, strategy = _resolve_logging_identity(None, "balanced")

    assert model_type == "ml:balanced"
    assert strategy == "balanced"


def test_resolve_logging_identity_preserves_explicit_scoped_ml_model_type():
    model_type, strategy = _resolve_logging_identity("ml:aggressive", None)

    assert model_type == "ml:aggressive"
    assert strategy == "aggressive"


def test_resolve_logging_identity_keeps_non_ml_model_types_unchanged():
    model_type, strategy = _resolve_logging_identity("pulse2", "PULSE_ML")

    assert model_type == "pulse2"
    assert strategy == "PULSE_ML"


@pytest.mark.asyncio
async def test_log_prediction_persists_low_confidence_balanced_scope_once_generated():
    inserted_records = []

    class _PredictionLogsTable:
        def insert_ignore(self, record):
            inserted_records.append(record)
            return {"data": [{"id": "ml-001"}], "error": None, "duplicate": False}

    class _Client:
        def table(self, name):
            assert name == "prediction_logs"
            return _PredictionLogsTable()

    context = {
        "ml_prediction": {
            "direction": "BUY",
            "confidence": 54.9,
            "probability_up": 54.9,
            "probability_down": 45.1,
            "entry_price": 2000.0,
            "target_price": 2012.0,
            "stop_price": 1981.0,
        }
    }

    with patch.object(prediction_logger, "is_db_available", return_value=True), patch.object(
        prediction_logger,
        "get_supabase_client",
        return_value=_Client(),
    ), patch.object(prediction_logger, "_has_active_signal", return_value=(False, None, None)), patch.dict(
        sys.modules,
        {"services.mtf_confirmation": SimpleNamespace(confirm_signal_mtf=AsyncMock(return_value=(True, "", {})))},
    ):
        prediction_id = await log_prediction(
            "XAUUSD",
            context,
            analysis={},
            timeframe="30m",
            strategy="balanced",
            model_type="ml:balanced",
        )

    assert prediction_id == "ml-001"
    assert len(inserted_records) == 1
    record = inserted_records[0]
    assert record["strategy"] == "balanced"
    assert record["model_type"] == "ml:balanced"
    assert record["ml_confidence"] == 54.9


@pytest.mark.asyncio
async def test_log_smc_prediction_inserts_without_ml_scope_filtering():
    inserted_records = []

    class _PredictionLogsTable:
        def insert_ignore(self, record):
            inserted_records.append(record)
            return {"data": [{"id": "smc-001"}], "error": None, "duplicate": False}

    class _Client:
        def table(self, name):
            assert name == "prediction_logs"
            return _PredictionLogsTable()

    with patch.object(prediction_logger, "is_db_available", return_value=True), patch.object(
        prediction_logger,
        "get_supabase_client",
        return_value=_Client(),
    ), patch.object(prediction_logger, "_has_active_signal", return_value=(False, None, None)):
        prediction_id = await log_smc_prediction(
            symbol="NDX.INDX",
            timeframe="5m",
            direction="BUY",
            confidence=73.4,
            entry_price=21500.0,
            reasoning=["Bullish structure", "Liquidity sweep"],
        )

    assert prediction_id == "smc-001"
    assert len(inserted_records) == 1
    record = inserted_records[0]
    assert record["model_type"] == "smc"
    assert record["strategy"] == "SMART_MONEY_ZONES"
    assert record["timeframe"] == "5m"
    assert record["ml_direction"] == "BUY"
    assert record["status"] == "active"
    assert record["factors"]["source"] == "SMART_MONEY_ZONES"
    assert record["factors"]["signal_reasoning"] == ["Bullish structure", "Liquidity sweep"]
