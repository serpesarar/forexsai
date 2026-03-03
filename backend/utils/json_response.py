"""
Numpy-safe JSON serialization for FastAPI.

FastAPI's default jsonable_encoder can't handle numpy types (np.bool_, np.int64, np.float64).
This module provides NumpySafeEncoder and NumpySafeJSONResponse that handle all numpy types.
"""

import json
import math

import numpy as np
from fastapi.responses import JSONResponse


class NumpySafeEncoder(json.JSONEncoder):
    """JSON encoder that handles numpy types."""
    def default(self, obj):
        if isinstance(obj, np.bool_):
            return bool(obj)
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            val = float(obj)
            if math.isnan(val) or math.isinf(val):
                return 0.0
            return val
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


def _sanitize_for_json(obj):
    """Recursively replace NaN/Infinity float values with 0.0 or None.
    This prevents json.dumps(allow_nan=False) from crashing."""
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return 0.0
        return obj
    if isinstance(obj, dict):
        return {k: _sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitize_for_json(v) for v in obj]
    return obj


class NumpySafeJSONResponse(JSONResponse):
    """JSONResponse that uses NumpySafeEncoder for numpy type serialization."""
    def render(self, content) -> bytes:
        sanitized = _sanitize_for_json(content)
        return json.dumps(
            sanitized,
            ensure_ascii=False,
            allow_nan=False,
            cls=NumpySafeEncoder,
        ).encode("utf-8")

