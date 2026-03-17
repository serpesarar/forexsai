import os
import sys
from types import SimpleNamespace
from unittest.mock import patch

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
    from services.prediction_logger import _resolve_logging_identity, log_prediction


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
async def test_log_prediction_skips_low_confidence_balanced_scope_before_insert():
    class _Client:
        def table(self, _name):
            raise AssertionError("DB insert path should not be reached for low-confidence scoped ML signals")

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

    with patch("services.prediction_logger.is_db_available", return_value=True), patch(
        "services.prediction_logger.get_supabase_client",
        return_value=_Client(),
    ):
        prediction_id = await log_prediction(
            "XAUUSD",
            context,
            analysis={},
            timeframe="30m",
            strategy="balanced",
            model_type="ml:balanced",
        )

    assert prediction_id is None
