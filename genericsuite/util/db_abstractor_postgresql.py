"""
DbAbstractorPostgresql: Database abstraction layer for PostgreSQL
"""

from typing import Dict
from genericsuite.util.db_abstractor_sql import (
    SqlUtilities,
    SqlFindIterator,
    SqlTable,
    SqlService,
    SqlServiceBuilder,
)
from genericsuite.util.app_logger import log_debug

DEBUG = False


class PostgresqlUtilities(SqlUtilities):
    """
    PostgreSQL Utilities class
    """

    def get_cursor(self):
        """
        Return cursor object for the specific database connection.
        """
        _ = DEBUG and log_debug(">> PostgresqlTable.get_cursor")
        from psycopg2.extras import RealDictCursor
        try:
            cursor = self._db.cursor(cursor_factory=RealDictCursor)
        except Exception as e:
            _ = DEBUG and log_debug(
                "PostgresqlTable.get_cursor | e: " + str(e))
            raise e
        _ = DEBUG and log_debug(
            f"PostgresqlTable.get_cursor | cursor: {cursor}")
        return cursor


class PostgresqlFindIterator(SqlFindIterator):
    """
    PostgreSQL find iterator
    """


class PostgresqlTable(SqlTable, PostgresqlUtilities):
    """
    PostgreSQL Table abstraction
    """


class PostgresqlService(SqlService, PostgresqlUtilities):
    """
    PostgreSQL Service class
    """

    def get_specific_db_connection(self, db_uri: str, db_name: str,
                                   other_params: Dict = None):
        """
        Returns the specific database connection object.

        Args:
            db_uri (str): The database URI.
            db_name (str): The database name.
            other_params (Dict, optional): Other parameters for the database
                connection.

        Returns:
            object: The database connection object.
        """
        _ = DEBUG and log_debug(
            ">> PostgresqlService.get_specific_db_connection")
        import psycopg2
        try:
            db_conector = psycopg2.connect(f"{db_uri}/{db_name}")
        except Exception as e:
            _ = DEBUG and log_debug(
                "PostgresqlService.get_specific_db_connection | e: "
                + str(e))
            raise e
        _ = DEBUG and log_debug(
            "PostgresqlService.get_specific_db_connection | db_conector: "
            + str(db_conector))
        return db_conector

    def get_table_class(self):
        """
        Returns the table class.

        Returns:
            The table class.
        """
        return PostgresqlTable

    def get_iterator_class(self):
        """
        Returns the iterator class.

        Returns:
            The iterator class.
        """
        return PostgresqlFindIterator


class PostgresqlServiceBuilder(SqlServiceBuilder):
    """
    Builder class for PostgreSQL.
    """

    def __init__(self):
        super().__init__(PostgresqlService)
