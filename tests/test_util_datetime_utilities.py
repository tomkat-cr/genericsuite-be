"""
Tests for genericsuite/util/datetime_utilities.py.
"""
import sys
from unittest.mock import MagicMock
from datetime import datetime, timezone

sys.modules.setdefault("genericsuite.util.app_logger", MagicMock())

# This module needs the REAL implementation, not the plain MagicMock some
# other test files install (via setdefault) if they are collected first in
# the same pytest session. Force a fresh import so this file's own tests
# never run against a stubbed-out version.
sys.modules.pop("genericsuite.util.datetime_utilities", None)

from genericsuite.util.datetime_utilities import (
    current_datetime_timestamp,
    get_datetime_utc,
    ts_to_ymd,
    get_date_zero_hour,
    get_date_eod,
    interpret_any_date,
)


def test_current_datetime_timestamp_is_float():
    ts = current_datetime_timestamp()
    assert isinstance(ts, float)
    assert ts > 0


def test_get_datetime_utc_returns_datetime():
    ts = 1_700_000_000.0
    dt = get_datetime_utc(ts)
    assert isinstance(dt, datetime)


def test_ts_to_ymd_format():
    ts = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc).timestamp()
    result = ts_to_ymd(ts)
    assert result.startswith("2024-01-15")


def test_ts_to_ymd_date_only():
    ts = datetime(2024, 6, 1, tzinfo=timezone.utc).timestamp()
    result = ts_to_ymd(ts, only_date=True)
    assert result == "2024-06-01"


def test_get_date_zero_hour_is_midnight():
    ts = datetime(2024, 3, 10, 15, 30, 0, tzinfo=timezone.utc).timestamp()
    zero = get_date_zero_hour(ts)
    assert ts_to_ymd(zero, only_date=True) == "2024-03-10"
    # Zero hour should be before the original timestamp
    assert zero <= ts


def test_get_date_eod_is_end_of_day():
    ts = datetime(2024, 3, 10, 6, 0, 0, tzinfo=timezone.utc).timestamp()
    eod = get_date_eod(ts)
    assert ts_to_ymd(eod, only_date=True) == "2024-03-10"
    assert eod >= ts


def test_interpret_any_date_float():
    ts = 1_700_000_000.0
    assert interpret_any_date(ts) == ts


def test_interpret_any_date_ymd_string():
    result = interpret_any_date("2024-01-15")
    assert isinstance(result, float)
    assert result > 0


def test_interpret_any_date_month_day_year():
    result = interpret_any_date("January 15, 2024")
    assert isinstance(result, float)
    assert result > 0


def test_interpret_any_date_invalid_returns_negative_one():
    result = interpret_any_date("not-a-date")
    assert result == -1
