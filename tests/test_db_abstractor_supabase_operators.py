from genericsuite.util.db_abstractor_supabase import (
    SupabaseTable,
    SupabaseService,
    SupabaseFindIterator,
    SupabaseServiceBuilder,
)
import sys
import pytest
from unittest.mock import MagicMock, patch

# Mock dependencies
mock_supabase = MagicMock()
sys.modules["supabase"] = mock_supabase

mock_logger = MagicMock()
sys.modules["genericsuite.util.app_logger"] = mock_logger

# Mock bson to avoid import error
mock_bson = MagicMock()
sys.modules["bson"] = mock_bson
mock_bson_util = MagicMock()
sys.modules["bson.json_util"] = mock_bson_util


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
def supabase_table():
    """Create SupabaseTable instance with mocked dependencies."""
    app_config = MagicMock()
    app_config.DB_CONFIG = {"app_db_uri": "http://localhost:5432"}
    connection = MagicMock()
    table_name = "test_table"
    table_structure = {
        "id": "integer",
        "name": "text",
        "value": "integer",
        "tags": "jsonb"
    }
    with patch(
        'genericsuite.util.db_abstractor_supabase'
        '.SupabaseService.get_db_config_data'
    ):
        table = SupabaseTable(
            app_config, connection,
            table_name, table_structure)

    # Mock get_cursor to return a mock supabase client
    mock_client = MagicMock()
    table.get_cursor = MagicMock(return_value=mock_client)

    # Mock find_one for state-requiring operators
    table.find_one = MagicMock()

    # Mock IteratorClass so find() with $elemMatch can return an iterator
    class SimpleIterator:
        def __init__(self, cursor, _table_structure):
            self._data = cursor.data if hasattr(cursor, "data") else []

        def __iter__(self):
            return iter(self._data)

    table.IteratorClass = SimpleIterator

    class Context:
        pass
    ctx = Context()
    ctx.table = table
    ctx.mock_client = mock_client
    return ctx


def test_update_one_set(supabase_table):
    query = {"id": 1}
    update = {"$set": {"name": "New Name"}}

    mock_response = MagicMock()
    mock_response.data = [{"id": 1, "name": "New Name"}]
    mock_response.count = 1

    supabase_table.mock_client.table().update.return_value = \
        supabase_table.mock_client
    supabase_table.mock_client.execute.return_value = mock_response

    with patch.object(
        supabase_table.table, 'supabase_where',
        return_value=supabase_table.mock_client
    ):
        supabase_table.table.update_one(query, update)

    supabase_table.mock_client.table.assert_called_with("test_table")
    supabase_table.mock_client.table.return_value.update.assert_called_with(
        {
            "name": "New Name"
        })


def test_update_one_inc(supabase_table):
    query = {"id": 1}
    update = {"$inc": {"value": 5}}

    supabase_table.table.find_one.return_value = {"value": 10}

    mock_response = MagicMock()
    mock_response.data = [{"id": 1, "value": 15}]
    mock_response.count = 1
    supabase_table.mock_client.table().update.return_value = \
        supabase_table.mock_client
    supabase_table.mock_client.execute.return_value = mock_response

    with patch.object(
        supabase_table.table, 'supabase_where',
        return_value=supabase_table.mock_client
    ):
        supabase_table.table.update_one(query, update)

    supabase_table.mock_client.table.return_value.update.assert_called_with(
        {
            "value": 15
        }
    )


def test_update_one_push(supabase_table):
    query = {"id": 1}
    update = {"$push": {"tags": "new_tag"}}

    supabase_table.table.find_one.return_value = {"tags": ["tag1"]}

    mock_response = MagicMock()
    mock_response.data = [{"id": 1, "tags": ["tag1", "new_tag"]}]
    mock_response.count = 1
    supabase_table.mock_client.table().update.return_value = \
        supabase_table.mock_client
    supabase_table.mock_client.execute.return_value = mock_response

    with patch.object(
        supabase_table.table, 'supabase_where',
        return_value=supabase_table.mock_client
    ):
        supabase_table.table.update_one(query, update)

    supabase_table.mock_client.table.return_value.update.assert_called_with(
        {"tags": ["tag1", "new_tag"]})


def test_update_one_addToSet(supabase_table):
    query = {"id": 1}
    update = {"$addToSet": {"tags": "tag1"}}  # tag1 already exists

    supabase_table.table.find_one.return_value = {"tags": ["tag1"]}

    mock_response = MagicMock()
    mock_response.data = [{"id": 1, "tags": ["tag1"]}]
    mock_response.count = 1
    supabase_table.mock_client.table().update.return_value = \
        supabase_table.mock_client
    supabase_table.mock_client.execute.return_value = mock_response

    with patch.object(
        supabase_table.table, 'supabase_where',
        return_value=supabase_table.mock_client
    ):
        supabase_table.table.update_one(query, update)

    supabase_table.mock_client.table.return_value.update.assert_called_with(
        {
            "tags": ["tag1"]
        }
    )


def test_update_one_addToSet_new(supabase_table):
    query = {"id": 1}
    update = {"$addToSet": {"tags": "tag2"}}  # tag2 doesn't exist

    supabase_table.table.find_one.return_value = {"tags": ["tag1"]}

    mock_response = MagicMock()
    mock_response.data = [{"id": 1, "tags": ["tag1", "tag2"]}]
    mock_response.count = 1
    supabase_table.mock_client.table().update.return_value = \
        supabase_table.mock_client
    supabase_table.mock_client.execute.return_value = mock_response

    with patch.object(
        supabase_table.table, 'supabase_where',
        return_value=supabase_table.mock_client
    ):
        supabase_table.table.update_one(query, update)

    supabase_table.mock_client.table.return_value.update.assert_called_with(
        {"tags": ["tag1", "tag2"]})


def test_update_one_pull(supabase_table):
    query = {"id": 1}
    update = {"$pull": {"tags": "tag1"}}

    supabase_table.table.find_one.return_value = {"tags": ["tag1", "tag2"]}

    mock_response = MagicMock()
    mock_response.data = [{"id": 1, "tags": ["tag2"]}]
    mock_response.count = 1
    supabase_table.mock_client.table().update.return_value = \
        supabase_table.mock_client
    supabase_table.mock_client.execute.return_value = mock_response

    with patch.object(
        supabase_table.table, 'supabase_where',
        return_value=supabase_table.mock_client
    ):
        supabase_table.table.update_one(query, update)

    supabase_table.mock_client.table.return_value.update.assert_called_with(
        {
            "tags": ["tag2"]
        }
    )


def test_update_one_pull_dict(supabase_table):
    query = {"id": 1}
    update = {"$pull": {"tags": {"id": "t1"}}}

    supabase_table.table.find_one.return_value = {
        "tags": [{"id": "t1"}, {"id": "t2"}]}

    mock_response = MagicMock()
    mock_response.data = [{"id": 1, "tags": [{"id": "t2"}]}]
    mock_response.count = 1
    supabase_table.mock_client.table().update.return_value = \
        supabase_table.mock_client
    supabase_table.mock_client.execute.return_value = mock_response

    with patch.object(
        supabase_table.table, 'supabase_where',
        return_value=supabase_table.mock_client
    ):
        supabase_table.table.update_one(query, update)

    supabase_table.mock_client.table.return_value.update.assert_called_with(
        {"tags": [{"id": "t2"}]})


def test_find_elemMatch_simple(supabase_table):
    query = {"tags": {"$elemMatch": {"id": "t1"}}}

    mock_response = MagicMock()
    mock_response.data = [
        {"id": 1, "tags": [{"id": "t1"}, {"id": "t2"}]},
        {"id": 2, "tags": [{"id": "t2"}, {"id": "t3"}]},
        {"id": 3, "tags": [{"id": "t1"}, {"id": "t3"}]}
    ]

    supabase_table.mock_client.table().select.return_value = \
        supabase_table.mock_client
    supabase_table.mock_client.execute.return_value = mock_response

    with patch.object(
        supabase_table.table, 'supabase_where',
        return_value=supabase_table.mock_client
    ):
        result_iterator = supabase_table.table.find(query)
        results = list(result_iterator)

    assert len(results) == 2
    assert results[0]["id"] == 1
    assert results[1]["id"] == 3


def test_find_elemMatch_multiple_conditions(supabase_table):
    query = {"tags": {"$elemMatch": {"id": "t1", "status": "active"}}}

    mock_response = MagicMock()
    mock_response.data = [
        {"id": 1, "tags": [{"id": "t1", "status": "active"}]},
        {"id": 2, "tags": [{"id": "t1", "status": "inactive"}]},
        {"id": 3, "tags": [{"id": "t2", "status": "active"}]}
    ]

    supabase_table.mock_client.table().select.return_value = \
        supabase_table.mock_client
    supabase_table.mock_client.execute.return_value = mock_response

    with patch.object(
        supabase_table.table, 'supabase_where',
        return_value=supabase_table.mock_client
    ):
        result_iterator = supabase_table.table.find(query)
        results = list(result_iterator)

    assert len(results) == 1
    assert results[0]["id"] == 1


def test_count_documents_elemMatch(supabase_table):
    query = {"tags": {"$elemMatch": {"id": "t1"}}}

    mock_response = MagicMock()
    mock_response.data = [
        {"id": 1, "tags": [{"id": "t1"}, {"id": "t2"}]},
        {"id": 2, "tags": [{"id": "t2"}, {"id": "t3"}]},
        {"id": 3, "tags": [{"id": "t1"}, {"id": "t3"}]}
    ]

    supabase_table.mock_client.table().select.return_value = \
        supabase_table.mock_client
    supabase_table.mock_client.execute.return_value = mock_response

    with patch.object(
        supabase_table.table, 'supabase_where',
        return_value=supabase_table.mock_client
    ):
        count = supabase_table.table.count_documents(query)

    assert count == 2


def test_find_elemMatch_no_match(supabase_table):
    query = {"tags": {"$elemMatch": {"id": "nonexistent"}}}

    mock_response = MagicMock()
    mock_response.data = [
        {"id": 1, "tags": [{"id": "t1"}, {"id": "t2"}]},
        {"id": 2, "tags": [{"id": "t2"}, {"id": "t3"}]}
    ]

    supabase_table.mock_client.table().select.return_value = \
        supabase_table.mock_client
    supabase_table.mock_client.execute.return_value = mock_response

    with patch.object(
        supabase_table.table, 'supabase_where',
        return_value=supabase_table.mock_client
    ):
        result_iterator = supabase_table.table.find(query)
        results = list(result_iterator)

    assert len(results) == 0


def test_insert_one(supabase_table):
    item = {"name": "New Row", "value": 100}
    mock_response = MagicMock()
    mock_response.data = [{"id": 1, "_id": "gen-123", "name": "New Row", "value": 100}]
    mock_response.count = 1
    supabase_table.mock_client.table.return_value.insert.return_value.execute.return_value = mock_response

    supabase_table.table.insert_one(item)

    supabase_table.mock_client.table.assert_called_with("test_table")
    supabase_table.mock_client.table.return_value.insert.assert_called_once()
    assert supabase_table.table.inserted_id == "gen-123"


def test_delete_one(supabase_table):
    query = {"id": 1}
    mock_response = MagicMock()
    mock_response.data = [{"id": 1}]
    mock_response.count = 1
    # Chain: table().delete() returns client, .execute() returns response
    supabase_table.mock_client.table.return_value = supabase_table.mock_client
    supabase_table.mock_client.delete.return_value = supabase_table.mock_client
    supabase_table.mock_client.execute.return_value = mock_response

    with patch.object(
        supabase_table.table, 'supabase_where',
        return_value=supabase_table.mock_client
    ):
        supabase_table.table.delete_one(query)

    supabase_table.mock_client.table.assert_called_with("test_table")
    supabase_table.mock_client.delete.assert_called_once()
    assert supabase_table.table.deleted_count == 1


def test_supabase_service_get_table_class():
    with patch(
        'genericsuite.util.db_abstractor_supabase.SupabaseService.get_db_config_data'
    ), patch.object(SupabaseService, 'get_db_connection'):
        app_config = MagicMock()
        app_config.DB_CONFIG = {"app_db_uri": "http://localhost:5432"}
        service = SupabaseService(app_config)
        assert service.get_table_class() is SupabaseTable


def test_supabase_service_get_iterator_class():
    with patch(
        'genericsuite.util.db_abstractor_supabase.SupabaseService.get_db_config_data'
    ), patch.object(SupabaseService, 'get_db_connection'):
        app_config = MagicMock()
        app_config.DB_CONFIG = {"app_db_uri": "http://localhost:5432"}
        service = SupabaseService(app_config)
        assert service.get_iterator_class() is SupabaseFindIterator


def test_supabase_service_builder_returns_instance():
    mock_config = MagicMock()
    mock_config.DB_CONFIG = {"app_db_uri": "http://localhost:5432"}
    with patch(
        'genericsuite.util.db_abstractor_supabase.SupabaseService.get_db_config_data'
    ), patch.object(SupabaseService, 'get_db_connection'):
        builder = SupabaseServiceBuilder()
        instance = builder(mock_config)
    assert instance is not None
    assert isinstance(instance, SupabaseService)
