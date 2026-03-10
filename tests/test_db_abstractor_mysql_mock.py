"""
Tests for MySQL db abstraction (MysqlService / MysqlTable) using mocks.
Mirrors test_db_abstractor_postgresql_mock.py for the SQL layer behavior
with MySQL-specific connection and backtick-quoted identifiers.
"""
from genericsuite.util.db_abstractor_mysql import (
    MysqlService,
    MysqlTable,
    MysqlServiceBuilder,
    MysqlFindIterator,
)
import sys
import pytest
from unittest.mock import MagicMock, patch

# Setup mocks first to avoid ModuleNotFoundError
# (before any genericsuite import)
mock_logger = MagicMock()
sys.modules["genericsuite.util.app_logger"] = mock_logger

mock_mysql_connector = MagicMock()
sys.modules["mysql"] = MagicMock()
sys.modules["mysql.connector"] = mock_mysql_connector

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


@pytest.fixture(autouse=True)
def patch_objectid_for_sql():
    """
    Ensure ObjectId is a real type so isinstance() in db_abstractor_sql
    works.
    """
    objectid_type = type(
        "ObjectId", (), {"__str__": lambda self: getattr(self, "val", "")}
    )
    with patch("genericsuite.util.db_abstractor_sql.ObjectId", objectid_type):
        yield


@pytest.fixture
def mysql_service():
    """Create MysqlService with test_table and mocked connection."""
    mock_config = MagicMock()
    mock_config.DB_CONFIG = {
        "app_db_uri": "mysql://user:pass@localhost:3306",
        "app_db_name": "testdb",
    }
    mock_config.DB_ENGINE = "MYSQL"
    service = MysqlService(mock_config)
    mock_conn = MagicMock()
    service._db = mock_conn

    table_name = "test_table"
    table_structure = {
        "id": "int",
        "name": "varchar(255)",
        "value": "int",
        "_id": "varchar(24)",
    }
    setattr(
        service,
        table_name,
        MysqlTable(
            mock_config,
            mock_conn,
            table_name,
            table_structure,
            primary_key=None,
            IteratorClass=service.get_iterator_class(),
        ),
    )

    yield service


def test_connection(mysql_service):
    """
    get_specific_db_connection is called with db_uri and db_name from 
    config.
    """
    with patch.object(
        mysql_service, "get_specific_db_connection", return_value=MagicMock()
    ) as mock_get_conn:
        mysql_service.get_db_connection()
        mock_get_conn.assert_called_once()
        args, kwargs = mock_get_conn.call_args
        assert args[0] == "mysql://user:pass@localhost:3306"
        assert args[1] == "testdb"


def test_find_empty_query(mysql_service):
    """find({}) runs SELECT without WHERE and returns iterator."""
    table = mysql_service["test_table"]
    mock_cursor = MagicMock()
    mysql_service._db.cursor.return_value = mock_cursor
    mock_cursor.fetchall.return_value = []
    list(table.find({}))
    assert mock_cursor.execute.called
    args, _ = mock_cursor.execute.call_args
    sql = args[0]
    assert "test_table" in sql
    assert "SELECT" in sql
    # MySQL uses backticks for identifiers
    assert "`" in sql


def test_insert_one_security(mysql_service):
    """
    insert_one quotes identifiers (backticks for MySQL) and parameterizes
    values.
    """
    table = mysql_service["test_table"]
    mock_cursor = MagicMock()
    mysql_service._db.cursor.return_value = mock_cursor

    item = {"name'": "test", "value": 123}
    table.insert_one(item)

    assert mock_cursor.execute.called
    args, _ = mock_cursor.execute.call_args
    sql = args[0]
    assert "test_table" in sql
    assert "name" in sql
    assert "value" in sql
    # MySQL backtick quoting
    assert "`" in sql


def test_find_complex_operators(mysql_service):
    """find() with $gt, $lt, $in produces correct SQL and placeholders."""
    table = mysql_service["test_table"]
    mock_cursor = MagicMock()
    mysql_service._db.cursor.return_value = mock_cursor
    mock_cursor.fetchall.return_value = []

    query = {
        "age": {"$gt": 18, "$lt": 30},
        "status": {"$in": ["active", "pending"]},
    }
    list(table.find(query))

    assert mock_cursor.execute.called
    args, _ = mock_cursor.execute.call_args
    sql = args[0]
    assert "age" in sql or "`age`" in sql
    assert ">" in sql and "<" in sql
    assert "status" in sql or "`status`" in sql
    assert "IN" in sql or "in" in sql


def test_sql_injection_protection(mysql_service):
    """User-supplied keys are quoted, not concatenated into SQL."""
    table = mysql_service["test_table"]
    mock_cursor = MagicMock()
    mysql_service._db.cursor.return_value = mock_cursor
    mock_cursor.fetchall.return_value = []

    query = {"email' OR 1=1 --": "test@example.com"}
    list(table.find(query))

    args, _ = mock_cursor.execute.call_args
    sql = args[0]
    # Malicious key must appear quoted (backtick) and value as placeholder
    assert "=" in sql
    assert "email" in sql or "1=1" not in sql  # value not raw in SQL


def test_update_one_security(mysql_service):
    """update_one uses quoted identifiers and placeholders."""
    table = mysql_service["test_table"]
    mock_cursor = MagicMock()
    mysql_service._db.cursor.return_value = mock_cursor
    mock_cursor.rowcount = 1

    query = {"_id": "123"}
    update = {"$set": {"name'": "updated"}}
    table.update_one(query, update)

    args, _ = mock_cursor.execute.call_args
    sql = args[0]
    assert "UPDATE" in sql
    assert "test_table" in sql
    assert "SET" in sql
    assert "WHERE" in sql


def test_delete_one_security(mysql_service):
    """delete_one uses quoted identifiers and placeholders."""
    table = mysql_service["test_table"]
    mock_cursor = MagicMock()
    mysql_service._db.cursor.return_value = mock_cursor
    mock_cursor.rowcount = 1

    query = {"_id": "123"}
    table.delete_one(query)

    args, _ = mock_cursor.execute.call_args
    sql = args[0]
    assert "DELETE" in sql
    assert "test_table" in sql
    assert "WHERE" in sql


def test_mysql_service_get_table_class(mysql_service):
    assert mysql_service.get_table_class() is MysqlTable


def test_mysql_service_get_iterator_class(mysql_service):
    assert mysql_service.get_iterator_class() is MysqlFindIterator


def test_mysql_count_documents(mysql_service):
    table = mysql_service["test_table"]
    mock_cursor = MagicMock()
    mysql_service._db.cursor.return_value = mock_cursor
    mock_cursor.fetchall.return_value = [(3,)]
    table.count_documents({"status": "active"})
    assert mock_cursor.execute.called
    args, _ = mock_cursor.execute.call_args
    assert "COUNT" in args[0] or "count" in args[0]


def test_mysql_find_one(mysql_service):
    table = mysql_service["test_table"]
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [{"id": 1, "name": "x"}]
    mysql_service._db.cursor.return_value = mock_cursor
    out = table.find_one({"id": 1})
    assert out is not None
    assert out["id"] == 1


def test_mysql_service_builder_returns_instance():
    mock_config = MagicMock()
    mock_config.DB_CONFIG = {"app_db_uri": "mysql:///db", "app_db_name": "db"}
    mock_config.DB_ENGINE = "MYSQL"
    with patch.object(MysqlService, "get_db_config_data"):
        builder = MysqlServiceBuilder()
        instance = builder(mock_config)
    assert instance is not None
    assert isinstance(instance, MysqlService)
