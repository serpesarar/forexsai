"""Unit tests for utils/json_helpers.py"""
import pytest
from utils.json_helpers import parse_json_field, parse_json_fields


class TestParseJsonField:
    """Tests for parse_json_field()."""

    def test_valid_json_string_dict(self):
        assert parse_json_field('{"TP1": 15, "TP2": 25}') == {"TP1": 15, "TP2": 25}

    def test_valid_json_string_list(self):
        assert parse_json_field('[1, 2, 3]') == [1, 2, 3]

    def test_valid_json_string_nested(self):
        result = parse_json_field('{"TP1": true, "TP2": false}')
        assert result == {"TP1": True, "TP2": False}

    def test_invalid_json_string_returns_default(self):
        assert parse_json_field("not valid json", {}) == {}

    def test_invalid_json_string_custom_default(self):
        assert parse_json_field("broken", {"fallback": True}) == {"fallback": True}

    def test_dict_input_passthrough(self):
        d = {"already": "parsed"}
        assert parse_json_field(d) is d

    def test_list_input_passthrough(self):
        lst = [1, 2, 3]
        assert parse_json_field(lst) is lst

    def test_none_returns_default(self):
        assert parse_json_field(None, {}) == {}
        assert parse_json_field(None, []) == []
        assert parse_json_field(None) == {}

    def test_empty_string_returns_default(self):
        assert parse_json_field("", {}) == {}
        assert parse_json_field("   ", {}) == {}

    def test_json_scalar_returns_default(self):
        # JSON "42" is valid JSON but not dict/list
        assert parse_json_field("42", {}) == {}
        assert parse_json_field("true", {}) == {}

    def test_unexpected_type_returns_default(self):
        assert parse_json_field(42, {}) == {}
        assert parse_json_field(True, {}) == {}


class TestParseJsonFields:
    """Tests for parse_json_fields() in-place mutation."""

    def test_parses_multiple_fields(self):
        record = {
            "id": "abc",
            "targets": '{"TP1": 15}',
            "targets_hit": '{"TP1": false}',
            "factors": '{"rsi": 55}',
        }
        parse_json_fields(record, ["targets", "targets_hit", "factors"])
        assert record["targets"] == {"TP1": 15}
        assert record["targets_hit"] == {"TP1": False}
        assert record["factors"] == {"rsi": 55}
        assert record["id"] == "abc"  # untouched

    def test_missing_field_no_error(self):
        record = {"id": "abc"}
        parse_json_fields(record, ["targets", "nonexistent"])
        assert record == {"id": "abc"}

    def test_already_parsed_fields(self):
        record = {"targets": {"TP1": 15}, "targets_hit": {"TP1": True}}
        parse_json_fields(record, ["targets", "targets_hit"])
        assert record["targets"] == {"TP1": 15}
        assert record["targets_hit"] == {"TP1": True}
