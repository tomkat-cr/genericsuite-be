import unittest
import sys
from unittest.mock import MagicMock, patch

# Mock psycopg2 before importing the module that uses it
mock_psycopg2 = MagicMock()
sys.modules["psycopg2"] = mock_psycopg2
sys.modules["psycopg2.extras"] = MagicMock()

# Mock bson
mock_bson = MagicMock()
sys.modules["bson"] = mock_bson
sys.modules["bson.json_util"] = MagicMock()

# Mock app_logger to avoid Config initialization
mock_logger = MagicMock()
sys.modules["genericsuite.util.app_logger"] = mock_logger


from genericsuite.util.db_abstractor_postgresql import (
    PostgresqlService,
    PostgresqlTable,
)


class TestPostgresqlAbstractor(unittest.TestCase):
    def setUp(self):
        self.mock_config = MagicMock()
        self.mock_config.DB_CONFIG = {
            "app_db_uri": "postgresql://user:pass@localhost:5432",
            "app_db_name": "db",
        }
        self.service = PostgresqlService(self.mock_config)
        self.mock_conn = MagicMock()
        self.service._db = self.mock_conn

    @patch("psycopg2.connect")
    def test_connection(self, mock_connect):
        self.service.get_db_connection()
        mock_connect.assert_called_with("postgresql://user:pass@localhost:5432/db")

    def test_insert_one(self):
        table = self.service["test_table"]
        table._conn = self.mock_conn
        mock_cursor = MagicMock()
        self.mock_conn.cursor.return_value = mock_cursor

        item = {"name": "test", "value": 123}
        table.insert_one(item)

        self.assertTrue(mock_cursor.execute.called)
        args, _ = mock_cursor.execute.call_args
        sql = args[0]
        self.assertIn("INSERT INTO test_table", sql)
        self.assertIn("name", sql)
        self.assertIn("value", sql)
        self.assertIn("_id", sql)  # Should be auto-generated

    def test_find(self):
        table = self.service["test_table"]
        table._conn = self.mock_conn
        mock_cursor = MagicMock()
        self.mock_conn.cursor.return_value = mock_cursor

        # Mock fetchall result
        mock_cursor.fetchall.return_value = [{"name": "test", "value": 123}]

        query = {"name": "test"}
        iterator = table.find(query)
        results = list(iterator)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "test")

        args, _ = mock_cursor.execute.call_args
        sql = args[0]
        self.assertIn("SELECT * FROM test_table", sql)
        self.assertIn("WHERE name = %s", sql)

    def test_update_one(self):
        table = self.service["test_table"]
        table._conn = self.mock_conn
        mock_cursor = MagicMock()
        self.mock_conn.cursor.return_value = mock_cursor
        mock_cursor.rowcount = 1

        query = {"_id": "123"}
        update = {"$set": {"name": "updated"}}
        table.update_one(query, update)

        args, _ = mock_cursor.execute.call_args
        sql = args[0]
        self.assertIn("UPDATE test_table SET name = %s", sql)
        self.assertIn("WHERE _id = %s", sql)

    def test_delete_one(self):
        table = self.service["test_table"]
        table._conn = self.mock_conn
        mock_cursor = MagicMock()
        self.mock_conn.cursor.return_value = mock_cursor
        mock_cursor.rowcount = 1

        query = {"_id": "123"}
        table.delete_one(query)

        args, _ = mock_cursor.execute.call_args
        sql = args[0]
        self.assertIn("DELETE FROM test_table", sql)
        self.assertIn("WHERE _id = %s", sql)

    def test_query_translation(self):
        table = self.service["test_table"]
        table._conn = self.mock_conn
        mock_cursor = MagicMock()
        self.mock_conn.cursor.return_value = mock_cursor

        query = {"age": {"$gt": 18}, "status": {"$in": ["active", "pending"]}}
        list(table.find(query))

        args, _ = mock_cursor.execute.call_args
        sql = args[0]
        self.assertIn("age > %s", sql)
        self.assertIn("status IN (%s, %s)", sql)


if __name__ == "__main__":
    unittest.main()
