"""
DbAbstractorMysql: Database abstraction layer for MySQL
"""

from typing import Dict
from functools import lru_cache
from urllib.parse import urlparse

from genericsuite.util.db_abstractor_sql import (
    SqlUtilities,
    SqlFindIterator,
    SqlTable,
    SqlService,
    SqlServiceBuilder,
)
from genericsuite.util.app_logger import log_debug, log_error

DEBUG = False


class MysqlUtilities(SqlUtilities):
    """
    MySQL Utilities class
    """

    def get_cursor(self):
        """
        Return cursor object for the specific database connection.
        """
        cursor = self._db.cursor(dictionary=True)
        _ = DEBUG and log_debug(
            ">> MysqlTable.get_cursor"
            + f"\n | cursor: {cursor}")
        return cursor


class MysqlFindIterator(SqlFindIterator):
    """
    MySQL find iterator
    """


class MysqlTable(SqlTable, MysqlUtilities):
    """
    MySQL Table abstraction
    """


class MysqlService(SqlService, MysqlUtilities):
    """
    MySQL Service class
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
            ">> MysqlService.get_specific_db_connection")
        import mysql.connector

        # Parse the URI
        # Format: mysql://user:password@host:port
        parsed_uri = urlparse(db_uri)
        config = {
            'user': parsed_uri.username,
            'password': parsed_uri.password,
            'host': parsed_uri.hostname,
            'port': parsed_uri.port or 3306,
            'database': db_name
        }
        if other_params:
            config.update(other_params)

        db_connector = mysql.connector.connect(**config)

        _ = DEBUG and log_debug(
            "MysqlService.get_specific_db_connection"
            f" | db_connector: {db_connector}")
        return db_connector

    def get_table_class(self):
        """
        Returns the table class.

        Returns:
            The table class.
        """
        return MysqlTable

    def get_iterator_class(self):
        """
        Returns the iterator class.

        Returns:
            The iterator class.
        """
        return MysqlFindIterator

    @lru_cache(maxsize=32)
    def set_tables_and_structures(self):
        """
        Sets the tables and structures in the database.
        """
        try:
            cursor = self.get_cursor()
            sql = "SELECT TABLE_NAME as table_name," \
                + " COLUMN_NAME as column_name," \
                + " DATA_TYPE as data_type" \
                + f" FROM {self.info_schema_table_names()['columns']}" \
                + f" WHERE TABLE_SCHEMA = '{self.db_name}'" \
                + " ORDER BY TABLE_NAME"
            _ = DEBUG and log_debug(
                "MysqlService set_tables_and_structures"
                f" | sql: {sql}")
            cursor.execute(sql)
            resultset = cursor.fetchall()
            cursor.close()
            _ = DEBUG and log_debug(
                "MysqlService set_tables_and_structures"
                f" | resultset: {resultset}")
        except Exception as e:
            log_error(
                f"MySqlService.set_tables_and_structures error: {e}")
            raise e
        self.assign_tables_and_structures(resultset)

    @lru_cache(maxsize=32)
    def set_primary_keys(self):
        """
        Sets the primary keys in the database.
        """
        try:
            sql = f"""SELECT
  TABLE_NAME as table_name,
  COLUMN_NAME as primary_key
FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
WHERE
  TABLE_SCHEMA = '{self.db_name}'
  AND CONSTRAINT_NAME = 'PRIMARY'
  ORDER BY TABLE_NAME;
"""
            _ = DEBUG and log_debug(
                "MysqlService set_primary_keys"
                f" | sql: {sql}")
            resultset = self.cursor_execute(sql)
        except Exception as e:
            log_error(
                "SqlService.set_primary_keys |" +
                f" Error: {e}")
            raise e

        self.assign_primary_keys(resultset)

    # def list_collection_names(self) -> list:
    #     """
    #     Returns a list of MySQL table names
    #     """
    #     try:
    #         cursor = self.get_cursor()
    #         cursor.execute(
    #             "SELECT TABLE_NAME as table_name"
    #             f" FROM {self.info_schema_table_names()['tables']}"
    #             f" WHERE TABLE_SCHEMA = '{self.db_name}';"
    #         )
    #         table_names = cursor.fetchall()
    #         cursor.close()
    #         _ = DEBUG and log_debug(
    #             "MysqlService list_collection_names"
    #             f" | table_names: {table_names}")
    #     except Exception as e:
    #         log_error(f"MysqlService list_collection_names error: {e}")
    #         raise e
    #     try:
    #         table_names = map(
    #             lambda table_name: table_name["table_name"], table_names)
    #         _ = DEBUG and log_debug(
    #             "MysqlService list_collection_names.map"
    #             f" | FINAL table_names: {table_names}")
    #         return table_names
    #     except Exception as e:
    #         log_error(f"MysqlService list_collection_names.map error: {e}")
    #         raise e

    # def table_structure(self, table_name: str) -> dict:
    #     """
    #     Returns a dictionary with the MySQL table structure
    #     """
    #     try:
    #         cursor = self.get_cursor()
    #         sql = "SELECT COLUMN_NAME as column_name," \
    #             + " DATA_TYPE as data_type" \
    #             + f" FROM {self.info_schema_table_names()['columns']}" \
    #             + f" WHERE TABLE_SCHEMA = '{self.db_name}' AND" \
    #             + f" TABLE_NAME = '{table_name}'"
    #         _ = DEBUG and log_debug(
    #             "MysqlService table_structure"
    #             f" | sql: {sql}")
    #         cursor.execute(sql)
    #         result = cursor.fetchall()
    #         cursor.close()
    #         _ = DEBUG and log_debug(
    #             "MysqlService table_structure"
    #             f" | result: {result}")
    #     except Exception as e:
    #         log_error(f"MysqlService table_structure error: {e}")
    #         return {}

    #     try:
    #         table_structure = {
    #             column["column_name"]: column["data_type"]
    #             for column in result
    #         }
    #         return table_structure
    #     except Exception as e:
    #         log_error(f"SqlService table_structure.map error: {e}")
    #         raise e


class MysqlServiceBuilder(SqlServiceBuilder):
    """
    Builder class for MySQL.
    """

    def __init__(self):
        super().__init__(MysqlService)
