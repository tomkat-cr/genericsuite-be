"""
DbAbstractorSuper: Database abstraction layer super class
"""
from bson.json_util import dumps
from genericsuite.util.app_logger import log_debug


# ----------------------- Factory Methods -----------------------


DEBUG = False

PYMONGO_ASCENDING = 1
PYMONGO_DESCENDING = -1


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
        self.db_uri = None
        self.db_name = None
        self.db_other_params = None
        self._db = None
        self.TableClass = self.get_table_class()
        self.structures = None
        self.tables = None
        self.primary_keys = None

        self.get_db_config_data()
        self.get_db_connection()

    def not_implemented(self, method_name: str = None):
        """
        Raises a Exception.
        """
        raise Exception(f"Not implemented: {method_name}")

    def get_db(self):
        """
        Returns the database object.

        Returns:
            Object: The database object.
        """
        _ = DEBUG and log_debug(
            "DB_ABSTRACTOR | DbAbstract | get_db"
            + f"\n | self: {self}"
            + "\n | DB OK..."
        )
        return self

    def get_db_config_data(self):
        """
        Returns the database configuration data.

        Returns:
            dict: The database configuration data.
        """
        self.db_uri = self._app_config.DB_CONFIG.get("app_db_uri")
        self.db_name = self._app_config.DB_CONFIG.get("app_db_name")
        self.db_other_params = self._app_config.DB_CONFIG.get(
            "app_db_other_params")
        self.db_engine = self._app_config.DB_ENGINE
        return

    def get_db_connection(self):
        """
        Sets the database connection object.
        """
        self.not_implemented("get_db_connection")

    def test_connection(self) -> str:
        """
        Test the database connection.

        Returns:
            str: The test result.
        """
        self.not_implemented("test_connection")

    def assign_tables_and_structures(self, resultset: list):
        """
        Assigns the tables and structures class properties from the resultset.

        Args:
            resultset (list): The resultset from the database. It must
                contain the following fields:
                    - table_name (str): The name of the table.
                    - column_name (str): The name of the column.
                    - data_type (str): The data type of the column.
        """
        self.structures = {}
        self.tables = []
        table_name = ""
        for table_item in resultset:
            if table_item["table_name"] != table_name:
                self.structures[table_item["table_name"]] = {}
                table_name = table_item["table_name"]
                if table_name not in self.tables:
                    self.tables.append(table_name)
            self.structures[table_name][
                table_item["column_name"]] = table_item["data_type"]

    def assign_primary_keys(self, resultset: list):
        """
        Assigns the primary keys class property from the resultset.

        Args:
            resultset (list): The resultset from the database. It must
                contain the following fields:
                    - table_name (str): The name of the table.
                    - primary_key (str): The name of the primary key.
                    - sort_key (str): The name of the sort key
                      (optional. e.g. for DynamoDB). Defaults to None.
        """
        self.primary_keys = {
            item["table_name"]: {
                "pk": item["primary_key"],
                "sk": item.get("sort_key")
            }
            for item in resultset
        }

    def set_tables_and_structures(self):
        """
        Sets the tables and structures in the database.
        """
        self.not_implemented("set_tables_and_structures")

    def set_primary_keys(self):
        """
        Sets the primary keys in the database.
        """
        self.not_implemented("set_primary_keys")

    def list_collections(self, collection_name: str = None) -> list:
        """
        List the collections in the database.

        Returns:
            list: The list of collections.
        """
        self.not_implemented("list_collections")

    def list_collection_names(self) -> list:
        """
        Returns the list of collection names in the database.

        Returns:
            list: The list of collection names.
        """
        if self.tables is None:
            self.set_tables_and_structures()
        if self.primary_keys is None:
            self.set_primary_keys()
        return self.tables

    def table_structure(self, table_name: str) -> dict:
        """
        Returns a dictionary with the table structure.
        In Supabase, it must be done calling a stored procedure because
        it's not possible to access the "information_schema" schema.
        For GenericSuite, it's "get_columns".
        """
        if self.structures is None:
            self.set_tables_and_structures()
        return self.structures[table_name]

    def primary_key(self, table_name: str) -> dict:
        """
        Returns the primary key of the table.
        """
        if self.primary_keys is None:
            self.set_primary_keys()
        return self.primary_keys[table_name]

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
        self.not_implemented("create_tables")

    def table_exists(self, table_name: str) -> bool:
        """
        Check if the table exists in the database.

        Args:
            table_name (str): The name of the table.

        Returns:
            bool: True if the table exists, False otherwise.
        """
        self.not_implemented("table_exists")

    def get_order_direction(self, direction: str):
        """
        Get the order direction.

        Args:
            direction (str): The direction to be returned.

        Returns:
            The order direction with the MongoDb constants.
        """
        return PYMONGO_ASCENDING if direction == "asc" else PYMONGO_DESCENDING

    def get_table_class(self):
        """
        Returns the table class.

        Returns:
            The table class.
        """
        self.not_implemented("get_table_class")

    def get_iterator_class(self):
        """
        Returns the iterator class.

        Returns:
            The iterator class.
        """
        self.not_implemented("get_iterator_class")
