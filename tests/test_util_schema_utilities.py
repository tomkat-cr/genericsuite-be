"""
Tests for genericsuite/util/schema_utilities.py — schema_verification.
"""
from unittest.mock import MagicMock
from pydantic import BaseModel
from genericsuite.util.schema_utilities import schema_verification


class _SampleSchema(BaseModel):
    name: str
    age: int


def test_schema_verification_valid_input():
    logger = MagicMock()
    result = schema_verification({"name": "Alice", "age": 30}, _SampleSchema, logger)
    assert result is not None
    assert result["name"] == "Alice"
    assert result["age"] == 30
    logger.error.assert_not_called()


def test_schema_verification_invalid_input_returns_none():
    logger = MagicMock()
    result = schema_verification({"name": "Alice", "age": "not-an-int"}, _SampleSchema, logger)
    assert result is None
    logger.error.assert_called_once()


def test_schema_verification_missing_field_returns_none():
    logger = MagicMock()
    result = schema_verification({"name": "Alice"}, _SampleSchema, logger)
    assert result is None


def test_schema_verification_empty_dict_returns_none():
    logger = MagicMock()
    result = schema_verification({}, _SampleSchema, logger)
    assert result is None


def test_schema_verification_returns_dict():
    logger = MagicMock()
    result = schema_verification({"name": "Bob", "age": 25}, _SampleSchema, logger)
    assert isinstance(result, dict)
