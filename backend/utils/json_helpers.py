"""
JSON field helpers for production safety.
Supabase stores JSONB columns as strings when read via REST API.
These helpers normalize them consistently.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Union, overload

logger = logging.getLogger(__name__)


def parse_json_field(value: Any, default: Any = None) -> Any:
    """
    Safely parse a value that might be a JSON string, dict, list, or None.

    Args:
        value: The raw value from DB (str | dict | list | None)
        default: Fallback if parsing fails or value is None.
                 If None, returns {} for str/dict-like, [] for list-like.

    Returns:
        Parsed dict/list, or the default.

    Examples:
        >>> parse_json_field('{"a": 1}')
        {'a': 1}
        >>> parse_json_field('invalid json', {})
        {}
        >>> parse_json_field(None, {})
        {}
        >>> parse_json_field({"already": "dict"})
        {'already': 'dict'}
        >>> parse_json_field('[1,2,3]')
        [1, 2, 3]
    """
    if value is None:
        return default if default is not None else {}

    if isinstance(value, (dict, list)):
        return value

    if isinstance(value, str):
        if not value.strip():
            return default if default is not None else {}
        try:
            parsed = json.loads(value)
            if isinstance(parsed, (dict, list)):
                return parsed
            # JSON scalar (int, float, bool) — return as-is in default wrapper
            return default if default is not None else {}
        except (json.JSONDecodeError, TypeError, ValueError) as e:
            logger.debug(f"parse_json_field: invalid JSON ({len(value)} chars): {e}")
            return default if default is not None else {}

    # Unexpected type — return default
    logger.debug(f"parse_json_field: unexpected type {type(value).__name__}")
    return default if default is not None else {}


def parse_json_fields(record: Dict[str, Any], fields: List[str], default: Any = None) -> None:
    """
    In-place parse multiple JSON string fields on a record dict.

    Args:
        record: The DB row dict to mutate.
        fields: List of field names to parse.
        default: Default value for each field if parsing fails.
    """
    for field in fields:
        if field in record:
            record[field] = parse_json_field(record[field], default if default is not None else {})
