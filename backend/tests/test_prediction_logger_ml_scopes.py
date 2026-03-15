import os
import sys
from types import SimpleNamespace
from unittest.mock import patch

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
    from services.prediction_logger import _resolve_logging_identity


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
