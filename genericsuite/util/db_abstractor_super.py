"""
DbAbstractorSuper: Database abstraction layer super class
"""
from bson.json_util import dumps


# ----------------------- Factory Methods -----------------------


DEBUG = False


class ObjectFactory:
    """
    Factory class for creating the different database objects.
    """

    def __init__(self):
        self._builders = {}

    def register_builder(self, key, builder):
        """
        Register the object (builder) for the given key (database).

        Args:
            key (str): The key for the database object.
            builder (DbAbstract): The database object (builder).

        Returns:
            None
        """
        self._builders[key] = builder

    def create(self, key, **kwargs):
        """
        Returns the given builder (database object) for the given key.

        Args:
            key (str): The key for the database object.
            **kwargs (dict): The keyword arguments for the database object.

        Returns:
            DbAbstract: The database object (builder).
        """
        builder = self._builders.get(key)
        if not builder:
            raise ValueError(key)
        return builder(**kwargs)


# ----------------------- Db Abstract -----------------------


class DbAbstract:
    """
    Database abstract super class
    """

    def __init__(self, app_config, **_ignored):
        self._app_config = app_config
        self._db = self.get_db_connection()
        # self.create_tables()

    def get_db(self):
        """
        Returns the database object.

        Returns:
            Object: The database object.
        """
        return self._db

    def get_db_connection(self):
        """
        Returns the database connection object.

        Returns:
            Object: The database connection object.
        """
        return {}

    def test_connection(self) -> str:
        """
        Test the database connection.

        Returns:
            str: The test result.
        """
        return dumps({})

    def list_collections(self, collection_name: str = None) -> list:
        """
        List the collections in the database.

        Returns:
            list: The list of collections.
        """
        return []

    def collection_stats(self, collection_name: str = None):
        """
        Get the collection statistics.

        Args:
            collection_name (str): the collection name. None means
            get all collections stats. Defaults to None.

        Returns:
            str: The collection(s) statistics.
        """
        return dumps(self.list_collections(collection_name))

    def create_tables(self) -> bool:
        """
        Create the tables in the database.
        """
        return True

    def table_exists(self, table_name: str) -> bool:
        """
        Check if the table exists in the database.

        Args:
            table_name (str): The name of the table.

        Returns:
            bool: True if the table exists, False otherwise.
        """
        return True

    def get_order_direction(self, direction: str):
        """
        Get the order direction.

        Args:
            direction (str): The direction to be returned.

        Returns:
            The order direction with the MongoDb constants.
        """
        return direction
