"""
Date/time utilities
"""
from typing import Union, Any
from datetime import timedelta
from datetime import timezone
from datetime import datetime

from genericsuite.util.app_logger import log_debug, log_error

DEBUG = False


def current_datetime_timestamp() -> float:
    """Getting the current UTC date and time as a timestamp"""
    dt = datetime.now(timezone.utc)
    utc_time = dt.replace(tzinfo=timezone.utc)
    utc_timestamp = utc_time.timestamp()
    return utc_timestamp


def get_datetime_utc(float_timestamp: float):
    """
    Returns the given timestamp as UTC
    (Coordinated Universal Time) timestamp
    """
    utc_dt = datetime.utcfromtimestamp(float_timestamp)
    return utc_dt

def ts_to_ymd(tstamp: float, only_date: bool = False) -> str:
    """
    Converts a timestamp to a string in the format YYYY-MM-DD
    """
    utc_dt = get_datetime_utc(tstamp)
    if only_date:
        return utc_dt.strftime('%Y-%m-%d')
    return utc_dt.strftime('%Y-%m-%d %H:%M:%S')


def get_date_zero_hour(input_ts: Union[float, str]) -> float:
    """
    Returns the given timestamp as a zero hour timestamp
    """
    if isinstance(input_ts, str):
        tstamp = float(input_ts)
    else:
        tstamp = input_ts
    # Get the UTC datetime object from the given timestamp
    # utc_dt = datetime.utcfromtimestamp(tstamp)
    # return utc_dt.replace(hour=0, minute=0, second=0,
    #                       microsecond=0).timestamp()
    # return tstamp - (tstamp % 3600)
    ts_ymd = ts_to_ymd(tstamp, only_date=True) + " 00:00:00"
    return datetime.strptime(ts_ymd, '%Y-%m-%d %H:%M:%S').replace(
        tzinfo=timezone.utc).timestamp()


def get_date_eod(input_ts: Union[float, str]) -> float:
    """
    Returns the given timestamp as a zero hour timestamp
    """
    if isinstance(input_ts, str):
        tstamp = float(input_ts)
    else:
        tstamp = input_ts
    ts_ymd = ts_to_ymd(tstamp, only_date=True) + " 23:59:59"
    return datetime.strptime(ts_ymd, '%Y-%m-%d %H:%M:%S').replace(
        tzinfo=timezone.utc).timestamp()


def get_date_range_filter(v: str, other_entries: dict = None
                          ) -> dict:
    """
    Generates a date range filter for MongoDB queries.

    Args:
        v (str): A string containing either a single timestamp or two
                    timestamps separated by a comma, representing the start
                    and end dates for the filter.

    Returns:
        dict: A dictionary with '$lte' and '$gte' keys for the MongoDB
                query, representing the range of dates to filter by.
    """
    dates = [None, None]
    if "," in v:
        # Date range separated by comma
        date_filter = {}
        dates = v.split(",")
        # The first date is the start date
        if dates[0].strip() != '':
            date_filter['$gte'] = get_date_zero_hour(dates[0])
        # The second date is the end date
        if len(dates) > 1 and dates[1].strip() != '':
            end_date = get_date_zero_hour(dates[1])
        else:
            end_date = datetime.utcnow().timestamp()
        # date_filter['$lte'] = (get_datetime_utc(end_date) +
        #                        timedelta(hours=24)).timestamp()
        date_filter['$lte'] = get_date_eod(end_date)
    else:
        date_filter = {
            # Same day
            # '$lte': (get_datetime_utc(get_date_zero_hour(v)) +
            #          timedelta(hours=24)).replace(
            #          tzinfo=timezone.utc).timestamp(),
            '$lte': get_date_eod(v),
            '$gte': get_date_zero_hour(v),
        }
    if not other_entries:
        other_entries = {}
    date_filter.update(other_entries)
    # if DEBUG:
    log_debug(f"GET_DATE_RANGE_FILTER | v: {v}" +
        f"\n | dates: {dates}" +
        f"\n | dates[0]: {dates[0]}" +
        f"\n | dates[1]: {dates[1]}" +
        f"\n | date_filter: {date_filter}" +
        f"\n | date_filter['$gte']: {ts_to_ymd(date_filter['$gte'])}" +
        f"\n | date_filter['$lte']: {ts_to_ymd(date_filter['$lte'])}" +
        "\n")
    return date_filter


def interpret_any_date(any_date: Any) -> float:
    """
    Convert date to timestamp from .

    Args:
        any_date (Any): the date as timestamp, or string with
            format "Month day, year" or "YYYY-MM-DD"

    Returns:
        float: date timestamp or -1 if ValueError error.
    """
    if isinstance(any_date, float):
        date_timestamp = any_date
    else:
        if "-" in any_date:
            date_fmt = '%Y-%m-%d'
        else:
            date_fmt = '%B %d, %Y'
        try:
            date_timestamp = \
                datetime.strptime(any_date, date_fmt).replace(
                    hour=0, minute=0, second=0, microsecond=0
                ).timestamp()
        except ValueError as err:
            log_error(f"Failed to convert {any_date} to" +
                      f" timestamp: {str(err)}")
            date_timestamp = -1
    return date_timestamp
