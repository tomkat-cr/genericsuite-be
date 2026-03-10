from genericsuite.util.db_abstractor_postgresql import (
    PostgresqlService,
    PostgresqlTable,
    PostgresqlServiceBuilder,
    PostgresqlFindIterator,
)
import sys
import pytest
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


@pytest.fixture(autouse=True)
def patch_objectid_for_sql():
    """
    Ensure ObjectId is a real type so isinstance() in db_abstractor_sql
    works.
    """
    objectid_type = type(
        "ObjectId", (), {"__str__": lambda self: getattr(self, "val", "")})
    with patch("genericsuite.util.db_abstractor_sql.ObjectId", objectid_type):
        yield


@pytest.fixture
def postgresql_service():
    """Create PostgresqlService with test_table and cleanup after test."""
    mock_config = MagicMock()
    mock_config.DB_CONFIG = {
        "app_db_uri": "postgresql://user:pass@localhost:5432",
        "app_db_name": "db",
    }
    service = PostgresqlService(mock_config)
    mock_conn = MagicMock()
    service._db = mock_conn

    # Create the table
    cursor = service.get_cursor()
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
    setattr(service, table_name, PostgresqlTable(
        mock_config,
        mock_conn,
        table_name,
        table_structure,
        primary_key=None,
        IteratorClass=service.get_iterator_class(),
    ))

    service._db.commit()

    yield service

    # Teardown: remove table when test finishes
    cursor = service.get_cursor()
    sql = "DROP TABLE IF EXISTS test_table"
    try:
        cursor.execute(sql)
    except Exception as e:
        print(f"SqlTable.insert_one error: {e}")
        raise e
    service._db.commit()


def test_connection(postgresql_service):
    with patch("psycopg2.connect") as mock_connect:
        postgresql_service.get_db_connection()
        mock_connect.assert_called_with(
            "postgresql://user:pass@localhost:5432/db")


def test_find_empty_query(postgresql_service):
    """find({}) runs SELECT without WHERE and returns iterator."""
    table = postgresql_service["test_table"]
    mock_cursor = MagicMock()
    postgresql_service._db.cursor.return_value = mock_cursor
    mock_cursor.fetchall.return_value = []
    list(table.find({}))
    assert mock_cursor.execute.called
    args, _ = mock_cursor.execute.call_args
    sql = args[0]
    assert "test_table" in sql
    assert "SELECT" in sql


def test_insert_one_security(postgresql_service):
    table = postgresql_service["test_table"]
    mock_cursor = MagicMock()
    postgresql_service._db.cursor.return_value = mock_cursor

    item = {"name'": "test", "value": 123}
    table.insert_one(item)

    assert mock_cursor.execute.called
    args, _ = mock_cursor.execute.call_args
    sql = args[0]
    assert '"test_table"' in sql
    assert '"name\'"' in sql
    assert '"value"' in sql


def test_find_complex_operators(postgresql_service):
    table = postgresql_service["test_table"]
    mock_cursor = MagicMock()
    postgresql_service._db.cursor.return_value = mock_cursor
    mock_cursor.fetchall.return_value = []

    query = {
        "age": {"$gt": 18, "$lt": 30},
        "status": {"$in": ["active", "pending"]}
    }
    list(table.find(query))

    assert mock_cursor.execute.called
    args, _ = mock_cursor.execute.call_args
    sql = args[0]
    assert '"age" > %s' in sql
    assert '"age" < %s' in sql
    assert '"status" IN (%s, %s)' in sql


def test_sql_injection_protection(postgresql_service):
    table = postgresql_service["test_table"]
    mock_cursor = MagicMock()
    postgresql_service._db.cursor.return_value = mock_cursor
    mock_cursor.fetchall.return_value = []

    query = {"email' OR 1=1 --": "test@example.com"}
    list(table.find(query))

    args, _ = mock_cursor.execute.call_args
    sql = args[0]
    assert '"email\' OR 1=1 --" = %s' in sql


def test_update_one_security(postgresql_service):
    table = postgresql_service["test_table"]
    mock_cursor = MagicMock()
    postgresql_service._db.cursor.return_value = mock_cursor
    mock_cursor.rowcount = 1

    query = {"_id": "123"}
    update = {"$set": {"name'": "updated"}}
    table.update_one(query, update)

    args, _ = mock_cursor.execute.call_args
    sql = args[0]
    assert 'UPDATE "test_table" SET "name\'" = %s' in sql
    assert 'WHERE "_id" = %s' in sql


def test_delete_one_security(postgresql_service):
    table = postgresql_service["test_table"]
    mock_cursor = MagicMock()
    postgresql_service._db.cursor.return_value = mock_cursor
    mock_cursor.rowcount = 1

    query = {"_id": "123"}
    table.delete_one(query)

    args, _ = mock_cursor.execute.call_args
    sql = args[0]
    assert 'DELETE FROM "test_table" WHERE "_id" = %s' in sql


def test_postgresql_service_get_table_class(postgresql_service):
    assert postgresql_service.get_table_class() is PostgresqlTable


def test_postgresql_service_get_iterator_class(postgresql_service):
    assert postgresql_service.get_iterator_class() is PostgresqlFindIterator


def test_postgresql_count_documents(postgresql_service):
    table = postgresql_service["test_table"]
    mock_cursor = MagicMock()
    postgresql_service._db.cursor.return_value = mock_cursor
    # RealDictCursor returns dict; count_documents expects doc_count
    mock_cursor.fetchone.return_value = {"doc_count": 2}
    n = table.count_documents({"status": "active"})
    assert n == 2


def test_postgresql_find_one(postgresql_service):
    table = postgresql_service["test_table"]
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [{"id": 1, "name": "y"}]
    postgresql_service._db.cursor.return_value = mock_cursor
    out = table.find_one({"id": 1})
    assert out is not None
    assert out["id"] == 1


def test_postgresql_service_builder_returns_instance():
    mock_config = MagicMock()
    mock_config.DB_CONFIG = {
        "app_db_uri": "postgresql://user:pass@localhost:5432",
        "app_db_name": "db",
    }
    with patch("psycopg2.connect", return_value=MagicMock()):
        builder = PostgresqlServiceBuilder()
        instance = builder(mock_config)
    assert instance is not None
    assert isinstance(instance, PostgresqlService)
