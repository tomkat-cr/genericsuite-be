"""
DbAbstractorMongodb: Database abstraction layer for MongoDb
"""

from bson.json_util import dumps

from genericsuite.util.db_abstractor_super import DbAbstract
from genericsuite.util.app_logger import log_debug


DEBUG = False


# ----------------------- MongoDb  -----------------------


class MongodbService(DbAbstract):
    """
    MongoDb service class
    """

    def get_db_connection(self):
        """
        Returns the database connection object.

        Returns:
            Object: The database connection object.
        """
        import pymongo

        _ = DEBUG and log_debug(
            "MongodbService | get_db_connection"
            + f"\n | DB_CONFIG: {self._app_config.DB_CONFIG}"
            + " | Starting..."
        )
        client = pymongo.MongoClient(self._app_config.DB_CONFIG["app_db_uri"])
        _ = DEBUG and log_debug(
            "MongodbService | get_db_connection"
            + f"\n | client: {client}"
            + "\n | DB Client OK..."
        )
        self._db = client.get_database(
            self._app_config.DB_CONFIG["app_db_name"])

        _ = DEBUG and log_debug(
            "MongodbService | get_db_connection"
            + f"\n | self._db: {self._db}"
            + "\n | DB Connector OK..."
        )
        return

    def get_db(self):
        """
        Returns the database object.

        Returns:
            Object: The database object. For DynamoDb, it must returns this
                Class as a whole.
        """
        _ = DEBUG and log_debug(
            "MongodbService | get_db"
            + f"\n | self: {self}"
            + "\n | DB OK..."
        )
        return self._db

    def test_connection(self) -> str:
        """
        Test the database connection.

        Returns:
            str: The test result.
        """
        return dumps(self._db.list_collection_names())

    def collection_stats(self, collection_name: str = None) -> str:
        """
        Get the collection statistics.

        Args:
            collection_name (str): the collection name. None means
            get all collections stats. Defaults to None.

        Returns:
            str: the MongoDb 'collstats' for all or the given collection
        """
        return dumps(self._db.command("collstats", collection_name))

    def get_order_direction(self, direction: str):
        """
        Get the order direction.

        Args:
            direction (str): The direction to be returned.

        Returns:
            The order direction with the MongoDb constants.
        """
        import pymongo

        return pymongo.ASCENDING if direction == "asc" else pymongo.DESCENDING

    def get_table_class(self):
        """
        Returns the table class.

        Returns:
            The table class.
        """
        return self._db


class MongodbServiceBuilder(DbAbstract):
    """
    Builder class for MongoDb.
    """

    def __init__(self):
        self._instance = None

    def __call__(self, app_config, **_ignored):
        _ = DEBUG and log_debug(
            "MongodbServiceBuilder | __call__"
            + f"\n | app_config: {app_config}"
            + "\n | Starting..."
        )
        if not self._instance:
            self._instance = MongodbService(app_config)
        return self._instance
