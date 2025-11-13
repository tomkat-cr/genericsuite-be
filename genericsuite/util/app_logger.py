"""
Logging utilities
"""

from typing import Any, Union
import os
import sys
import logging
import datetime

from genericsuite.config.config import Config, is_local_service


settings = Config()
app_logs: Union[logging.Logger, None] = None


def log_config(log_file: str = None) -> logging:
    """ Logging configuration """
    logger = logging.getLogger(settings.APP_NAME)
    logger.propagate = False
    if settings.DEBUG:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    if log_file:
        handler = logging.FileHandler(log_file)
    formatter = logging.Formatter('%(name)s-%(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


def set_app_logs(log_file: str = None) -> None:
    global app_logs
    app_logs = log_config(log_file)


def db_stamp() -> str:
    db_engine = os.environ['APP_DB_ENGINE']
    if db_engine == 'DYNAMO_DB':
        response = f"{db_engine}|" + \
            f"{os.environ.get('DYNAMDB_PREFIX', 'No-Prefix')}"
    else:
        response = f"{db_engine}|{os.environ['APP_DB_NAME']}"
    if is_local_service():
        response += "|LOCAL"
    else:
        response += "|CLOUD"
    return response


def formatted_message(message: Any) -> str:
    """ Returns a formatted message with database name and date/time """
    return f"[{db_stamp()}]" + \
        f" {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}" + \
        f" | {message}"


def log_debug(message: Any) -> str:
    """Register a Debug log"""
    global app_logs
    if not app_logs:
        set_app_logs()
    fmt_msg = formatted_message(message)
    app_logs.debug("%s", fmt_msg)
    return fmt_msg


def log_info(message: Any) -> str:
    """Register an Info log"""
    global app_logs
    if not app_logs:
        set_app_logs()
    fmt_msg = formatted_message(message)
    app_logs.info("%s", fmt_msg)
    return fmt_msg


def log_warning(message: Any) -> str:
    """Register a Warning log"""
    global app_logs
    if not app_logs:
        set_app_logs()
    fmt_msg = formatted_message(message)
    app_logs.warning("%s", fmt_msg)
    return fmt_msg


def log_error(message: Any) -> str:
    """Register an Error log"""
    global app_logs
    if not app_logs:
        set_app_logs()
    fmt_msg = formatted_message(message)
    app_logs.error("%s", fmt_msg)
    return fmt_msg
