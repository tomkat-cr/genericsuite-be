"""
DbAbstractor: Database abstraction layer for MongoDb and DynamoDb
"""

from __future__ import annotations
from werkzeug.local import LocalProxy


from genericsuite.config.config import Config
from genericsuite.util.request_handler import RequestHandler
from genericsuite.util.app_logger import log_debug

from genericsuite.util.db_abstractor_super import ObjectFactory
from genericsuite.util.db_abstractor_mongodb import MongodbServiceBuilder
from genericsuite.util.db_abstractor_dynamodb import DynamodbServiceBuilder
from genericsuite.util.db_abstractor_postgresql import PostgresqlServiceBuilder
from genericsuite.util.db_abstractor_mysql import MysqlServiceBuilder
from genericsuite.util.db_abstractor_supabase import SupabaseServiceBuilder

# ----------------------- Db General -----------------------

DEBUG = False

# Create a single instance of RequestHandler
# to be used throughout the module
request_handler = RequestHandler()


def set_db_request(request):
    """
    Set the request object for the database.
    This is used to get the current Request object.

    Args:
        request: The request object.

    Returns
        None.
    """
    request_handler.set_request(request)


def get_db_factory():
    """
    Get the database factory for the current database engine.

    Returns
        The database factory.

    Raises
        Exception: If the database engine is not supported.
    """
    settings = Config()
    factory = ObjectFactory()
    current_db_engine = settings.DB_ENGINE
    if DEBUG:
        log_debug(f">>>--> current_db_engine = {current_db_engine}")
        # log_debug(f'>>>--> settings.DB_CONFIG = {settings.DB_CONFIG}')
    factory.register_builder("DYNAMODB", DynamodbServiceBuilder())
    factory.register_builder("MONGODB", MongodbServiceBuilder())
    factory.register_builder("POSTGRES", PostgresqlServiceBuilder())
    factory.register_builder("MYSQL", MysqlServiceBuilder())
    factory.register_builder("SUPABASE", SupabaseServiceBuilder())
    return factory.create(current_db_engine, app_config=settings)


db_factory = LocalProxy(get_db_factory)


def get_db_engine():
    """
    Get the current database engine.
    """
    _ = DEBUG and log_debug(
        "db_abstractor SUPER | get_db_engine"
        + "\n | Starting..."
    )
    return db_factory.get_db()


db = LocalProxy(get_db_engine)


def test_connection():
    """
    Test database connection
    """
    return db_factory.test_connection()


# DB utilities


def verify_required_fields(
    fields: dict,
    required_fields: list,
    error_code: str
):
    """
    Verify if all the required fields are present in the fields dictionary.

    Args:
        fields (dict): The dictionary containing the fields.
        required_fields (list): The list of required fields.
        error_code (str): The error code to be returned.

    Returns:
        The resultset dictionary containing the error, error_message,
        and resultset. If there are no errors, the resultset will be empty
        and error = False. If there are errors, error = True and error_message
        will contain the missing fields.
    """
    resultset = dict({"error": False, "error_message": "", "resultset": {}})
    error = ""
    for element in required_fields:
        if element not in fields:
            error += f"{', ' if error != '' else ''}{element}"
    if error:
        resultset["error_message"] = (
            "Missing mandatory elements:"
            + f" {error} {error_code}."
        )
        resultset["error"] = True
    return resultset


def get_order_direction(direction: str):
    """
    Get the order direction.

    Args:
        direction (str): The direction to be returned.

    Returns:
        The order direction with the MongoDb constants.
    """
    return db_factory.get_order_direction(direction)
