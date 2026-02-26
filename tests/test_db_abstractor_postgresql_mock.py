from genericsuite.util.db_abstractor_postgresql import (
    PostgresqlService, PostgresqlTable)
import unittest
import sys
from unittest.mock import MagicMock, patch

# 1. Setup Mocks FIRST to avoid ModuleNotFoundError
mock_psycopg2 = MagicMock()
sys.modules["psycopg2"] = mock_psycopg2
mock_psycopg2_extras = MagicMock()
sys.modules["psycopg2.extras"] = mock_psycopg2_extras

mock_bson = MagicMock()
sys.modules["bson"] = mock_bson
mock_bson_util = MagicMock()
sys.modules["bson.json_util"] = mock_bson_util


class MockObjectId:
    def __init__(self, val=None):
        self.val = val or "507f1f77bcf86cd799439011"

    def __str__(self):
        return str(self.val)

    def __repr__(self):
        return f"ObjectId('{self.val}')"


mock_bson_util.ObjectId = MockObjectId
mock_bson_util.dumps = lambda x: str(x)

mock_logger = MagicMock()
sys.modules["genericsuite.util.app_logger"] = mock_logger

# 2. THEN import the project code


class TestPostgresqlAbstractor(unittest.TestCase):
    def setUp(self):
        self.mock_config = MagicMock()
        self.mock_config.DB_CONFIG = {
            "app_db_uri": "postgresql://user:pass@localhost:5432",
            "app_db_name": "db",
        }
        # Connection is mocked via mock_psycopg2
        self.service = PostgresqlService(self.mock_config)
        self.mock_conn = MagicMock()
        self.service._db = self.mock_conn

        # Create the table
        cursor = self.service.get_cursor()
        sql = "CREATE TABLE IF NOT EXISTS test_table " + \
            "(id SERIAL PRIMARY KEY, name TEXT, value INTEGER, _id TEXT)"
        try:
            cursor.execute(sql)
        except Exception as e:
            print(f"SqlTable.insert_one error: {e}")
            raise e

        # Manually register the table for the mock test
        table_name = "test_table"
        table_structure = {
            "id": "integer",
            "name": "text",
            "value": "integer",
            "_id": "text"
        }
        setattr(self.service, table_name, PostgresqlTable(
            self.mock_config,
            self.mock_conn,
            table_name,
            table_structure,
            self.service.get_iterator_class()
        ))

        self.service._db.commit()

    def tearDown(self):
        # Remove it when test finishes
        cursor = self.service.get_cursor()
        sql = "DROP TABLE IF EXISTS test_table"
        try:
            cursor.execute(sql)
        except Exception as e:
            print(f"SqlTable.insert_one error: {e}")
            raise e
        self.service._db.commit()

    @patch("psycopg2.connect")
    def test_connection(self, mock_connect):
        self.service.get_db_connection()
        mock_connect.assert_called_with(
            "postgresql://user:pass@localhost:5432/db")

    def test_insert_one_security(self):
        table = self.service["test_table"]
        mock_cursor = MagicMock()
        self.mock_conn.cursor.return_value = mock_cursor

        item = {"name'": "test", "value": 123}
        table.insert_one(item)

        self.assertTrue(mock_cursor.execute.called)
        args, _ = mock_cursor.execute.call_args
        sql = args[0]
        self.assertIn('"test_table"', sql)
        self.assertIn('"name\'"', sql)
        self.assertIn('"value"', sql)

    def test_find_complex_operators(self):
        table = self.service["test_table"]
        mock_cursor = MagicMock()
        self.mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []

        query = {
            "age": {"$gt": 18, "$lt": 30},
            "status": {"$in": ["active", "pending"]}
        }
        list(table.find(query))

        self.assertTrue(mock_cursor.execute.called)
        args, _ = mock_cursor.execute.call_args
        sql = args[0]
        self.assertIn('"age" > %s', sql)
        self.assertIn('"age" < %s', sql)
        self.assertIn('"status" IN (%s, %s)', sql)

    def test_sql_injection_protection(self):
        table = self.service["test_table"]
        mock_cursor = MagicMock()
        self.mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []

        query = {"email' OR 1=1 --": "test@example.com"}
        list(table.find(query))

        args, _ = mock_cursor.execute.call_args
        sql = args[0]
        self.assertIn('"email\' OR 1=1 --" = %s', sql)

    def test_update_one_security(self):
        table = self.service["test_table"]
        mock_cursor = MagicMock()
        self.mock_conn.cursor.return_value = mock_cursor
        mock_cursor.rowcount = 1

        query = {"_id": "123"}
        update = {"$set": {"name'": "updated"}}
        table.update_one(query, update)

        args, _ = mock_cursor.execute.call_args
        sql = args[0]
        self.assertIn('UPDATE "test_table" SET "name\'" = %s', sql)
        self.assertIn('WHERE "_id" = %s', sql)

    def test_delete_one_security(self):
        table = self.service["test_table"]
        mock_cursor = MagicMock()
        self.mock_conn.cursor.return_value = mock_cursor
        mock_cursor.rowcount = 1

        query = {"_id": "123"}
        table.delete_one(query)

        args, _ = mock_cursor.execute.call_args
        sql = args[0]
        self.assertIn('DELETE FROM "test_table" WHERE "_id" = %s', sql)


if __name__ == "__main__":
    unittest.main()
