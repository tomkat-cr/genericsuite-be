from genericsuite.util.db_abstractor_dynamodb import (
    DynamoDbTableAbstract,
    DynamoDbFindIterator,
    DynamoDbUtilities,
    DynamodbService,
    DynamodbServiceBuilder,
)
import sys
import pytest
from unittest.mock import MagicMock, patch, PropertyMock

# Mock dependencies before importing db_abstractor_dynamodb (it imports bson)
mock_boto3 = MagicMock()
sys.modules["boto3"] = mock_boto3

mock_botocore = MagicMock()
sys.modules["botocore"] = mock_botocore
sys.modules["botocore.exceptions"] = mock_botocore.exceptions

mock_logger = MagicMock()
sys.modules["genericsuite.util.app_logger"] = mock_logger

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


@pytest.fixture
def dynamodb_table():
    """Create DynamoDbTableAbstract instance with mocked connection."""
    mock_db_connection = MagicMock()
    item_structure = {
        "TableName": "test_table",
        "prefix": "test_"
    }
    table = DynamoDbTableAbstract(
        item_structure, mock_db_connection)

    mock_table = MagicMock()
    mock_db_connection.Table.return_value = mock_table

    class Context:
        pass
    ctx = Context()
    ctx.table = table
    ctx.mock_db_connection = mock_db_connection
    ctx.mock_table = mock_table
    return ctx


# --- TestDynamoDbElemMatch ---

def test_extract_elem_match(dynamodb_table):
    query_params = {
        "name": "test",
        "tags": {"$elemMatch": {"id": "t1"}}
    }

    cleaned, elem_match = dynamodb_table.table._extract_elem_match(
        query_params)

    assert cleaned == {"name": "test"}
    assert elem_match == {"tags": {"id": "t1"}}


def test_filter_elem_match_single_condition(dynamodb_table):
    items = [
        {"id": 1, "tags": [{"id": "t1"}, {"id": "t2"}]},
        {"id": 2, "tags": [{"id": "t2"}, {"id": "t3"}]},
        {"id": 3, "tags": [{"id": "t1"}, {"id": "t3"}]}
    ]
    elem_match_conditions = {"tags": {"id": "t1"}}

    filtered = dynamodb_table.table._filter_elem_match(
        items, elem_match_conditions)

    assert len(filtered) == 2
    assert filtered[0]["id"] == 1
    assert filtered[1]["id"] == 3


def test_filter_elem_match_multiple_conditions(dynamodb_table):
    items = [
        {"id": 1, "tags": [{"id": "t1", "status": "active"}]},
        {"id": 2, "tags": [{"id": "t1", "status": "inactive"}]},
        {"id": 3, "tags": [{"id": "t2", "status": "active"}]}
    ]
    elem_match_conditions = {"tags": {"id": "t1", "status": "active"}}

    filtered = dynamodb_table.table._filter_elem_match(
        items, elem_match_conditions)

    assert len(filtered) == 1
    assert filtered[0]["id"] == 1


def test_filter_elem_match_no_match(dynamodb_table):
    items = [
        {"id": 1, "tags": [{"id": "t1"}, {"id": "t2"}]},
        {"id": 2, "tags": [{"id": "t2"}, {"id": "t3"}]}
    ]
    elem_match_conditions = {"tags": {"id": "nonexistent"}}

    filtered = dynamodb_table.table._filter_elem_match(
        items, elem_match_conditions)

    assert len(filtered) == 0


def test_filter_elem_match_single_item(dynamodb_table):
    item = {"id": 1, "tags": [{"id": "t1"}, {"id": "t2"}]}
    elem_match_conditions = {"tags": {"id": "t1"}}

    filtered = dynamodb_table.table._filter_elem_match(
        item, elem_match_conditions)

    assert filtered["id"] == 1


def test_filter_elem_match_single_item_no_match(dynamodb_table):
    item = {"id": 1, "tags": [{"id": "t2"}]}
    elem_match_conditions = {"tags": {"id": "t1"}}

    filtered = dynamodb_table.table._filter_elem_match(
        item, elem_match_conditions)

    assert filtered == {}


# Valid 24-char hex ObjectIds so id_addition works with real or mocked bson
_OID1 = "507f1f77bcf86cd799439011"
_OID2 = "507f1f77bcf86cd799439012"
_OID3 = "507f1f77bcf86cd799439013"


def test_generic_query_elemMatch_scan(dynamodb_table):
    query_params = {"tags": {"$elemMatch": {"id": "t1"}}}

    mock_response = {
        "Items": [
            {"_id": _OID1, "tags": [{"id": "t1"}, {"id": "t2"}]},
            {"_id": _OID2, "tags": [{"id": "t2"}, {"id": "t3"}]},
            {"_id": _OID3, "tags": [{"id": "t1"}, {"id": "t3"}]}
        ]
    }
    dynamodb_table.mock_table.scan.return_value = mock_response

    with patch.object(
            dynamodb_table.table, 'get_primary_keys',
            return_value=None):
        with patch.object(
            dynamodb_table.table,
            'get_global_secondary_indexes_keys',
                return_value=(None, None)):
            with patch.object(
                dynamodb_table.table,
                'get_condition_expresion_values',
                    return_value=({}, "", {})):
                results = dynamodb_table.table.generic_query(query_params)

    assert len(results) == 2


def test_generic_query_elemMatch_count(dynamodb_table):
    query_params = {"tags": {"$elemMatch": {"id": "t1"}}}

    mock_response = {
        "Items": [
            {"_id": _OID1, "tags": [{"id": "t1"}, {"id": "t2"}]},
            {"_id": _OID2, "tags": [{"id": "t2"}, {"id": "t3"}]},
            {"_id": _OID3, "tags": [{"id": "t1"}, {"id": "t3"}]}
        ]
    }
    dynamodb_table.mock_table.scan.return_value = mock_response

    with patch.object(
            dynamodb_table.table, 'get_primary_keys', return_value=None):
        with patch.object(
            dynamodb_table.table,
            'get_global_secondary_indexes_keys',
                return_value=(None, None)):
            with patch.object(dynamodb_table.table,
                              'get_condition_expresion_values',
                              return_value=({}, "", {})):
                count = dynamodb_table.table.generic_query(
                    query_params, select="COUNT")

    assert count == 2


# --- TestDynamoDbPull ---

def test_update_one_pull_single_key(dynamodb_table):
    keys = {"_id": "doc1"}
    dynamodb_table.mock_table.get_item.return_value = {
        "Item": {
            "_id": "doc1",
            "tags": [{"id": "t1"}, {"id": "t2"}],
        }
    }
    dynamodb_table.mock_table.update_item.return_value = {}

    with patch.object(dynamodb_table.table, "get_primary_keys",
                      return_value=keys):
        out = dynamodb_table.table.update_one(
            {"_id": "doc1"},
            {"$pull": {"tags": {"id": "t1"}}},
        )

    assert out  # update_one returns self (table) on success
    assert dynamodb_table.table.modified_count == 1
    dynamodb_table.mock_table.get_item.assert_called_once_with(Key=keys)
    call_kw = dynamodb_table.mock_table.update_item.call_args[1]
    assert "ExpressionAttributeValues" in call_kw
    vals = call_kw["ExpressionAttributeValues"]
    tag_vals = [v for k, v in vals.items() if isinstance(
        v, list) and v and isinstance(v[0], dict)]
    assert len(tag_vals) == 1
    assert tag_vals[0] == [{"id": "t2"}]


def test_update_one_pull_multi_key(dynamodb_table):
    keys = {"_id": "doc1"}
    dynamodb_table.mock_table.get_item.return_value = {
        "Item": {
            "_id": "doc1",
            "items": [
                {"id": "a", "scope": "x"},
                {"id": "a", "scope": "y"},
                {"id": "b", "scope": "x"},
            ],
        }
    }
    dynamodb_table.mock_table.update_item.return_value = {}

    with patch.object(dynamodb_table.table, "get_primary_keys",
                      return_value=keys):
        out = dynamodb_table.table.update_one(
            {"_id": "doc1"},
            {"$pull": {"items": {"id": "a", "scope": "y"}}},
        )

    assert out  # update_one returns self (table) on success
    assert dynamodb_table.table.modified_count == 1
    call_kw = dynamodb_table.mock_table.update_item.call_args[1]
    vals = call_kw["ExpressionAttributeValues"]
    list_vals = [v for v in vals.values() if isinstance(v, list)
                 and len(v) == 2]
    assert len(list_vals) == 1
    expected = [{"id": "a", "scope": "x"}, {"id": "b", "scope": "x"}]
    assert list_vals[0] == expected


def test_update_one_pull_scalar(dynamodb_table):
    keys = {"_id": "doc1"}
    dynamodb_table.mock_table.get_item.return_value = {
        "Item": {"_id": "doc1", "tags": ["tag1", "tag2", "tag3"]},
    }
    dynamodb_table.mock_table.update_item.return_value = {}

    with patch.object(dynamodb_table.table, "get_primary_keys",
                      return_value=keys):
        out = dynamodb_table.table.update_one(
            {"_id": "doc1"},
            {"$pull": {"tags": "tag2"}},
        )

    assert out  # update_one returns self (table) on success
    assert dynamodb_table.table.modified_count == 1
    call_kw = dynamodb_table.mock_table.update_item.call_args[1]
    vals = call_kw["ExpressionAttributeValues"]
    list_vals = [v for v in vals.values() if isinstance(v, list)
                 and v == ["tag1", "tag3"]]
    assert len(list_vals) == 1


def test_update_one_pull_not_found_returns_false(dynamodb_table):
    keys = {"_id": "doc1"}
    dynamodb_table.mock_table.get_item.return_value = {
        "Item": {"_id": "doc1", "tags": [{"id": "t1"}, {"id": "t2"}]},
    }

    with patch.object(dynamodb_table.table, "get_primary_keys",
                      return_value=keys):
        out = dynamodb_table.table.update_one(
            {"_id": "doc1"},
            {"$pull": {"tags": {"id": "t9"}}},
        )

    assert out is False
    dynamodb_table.mock_table.update_item.assert_not_called()


# --- DynamoDbUtilities: new_id, id_conversion, convert_floats, remove_decimal ---

def test_new_id_returns_24_char_string(dynamodb_table):
    uid = dynamodb_table.table.new_id()
    assert isinstance(uid, str)
    assert len(uid) == 24


def test_id_conversion_leaves_str_unchanged(dynamodb_table):
    key_set = {"_id": "507f1f77bcf86cd799439011"}
    dynamodb_table.table.id_conversion(key_set)
    assert key_set["_id"] == "507f1f77bcf86cd799439011"


def test_id_conversion_converts_non_str_to_str(dynamodb_table):
    key_set = {"_id": 123}
    dynamodb_table.table.id_conversion(key_set)
    assert key_set["_id"] == "123"


def test_convert_floats_to_decimal(dynamodb_table):
    data = {"a": 1.5, "b": [2.0, 3.5], "c": {"x": 4.25}}
    from decimal import Decimal
    out = dynamodb_table.table.convert_floats_to_decimal(data)
    assert out["a"] == Decimal("1.5")
    assert out["b"][0] == Decimal("2.0")
    assert out["c"]["x"] == Decimal("4.25")


def test_remove_decimal_types(dynamodb_table):
    item = {"_id": _OID1, "name": "x", "score": 10}
    with patch.object(dynamodb_table.table, "id_addition", side_effect=lambda r: r):
        out = dynamodb_table.table.remove_decimal_types(item)
    assert out["_id"] == _OID1
    assert out["name"] == "x"


# --- DynamoDbTableAbstract: get_table_name, get_primary_keys ---

def test_get_table_name(dynamodb_table):
    name = dynamodb_table.table.get_table_name()
    assert name == "test_test_table"


def test_get_primary_keys(dynamodb_table):
    with patch.object(dynamodb_table.table, "get_table_definitions"):
        dynamodb_table.table._key_schema = [
            {"AttributeName": "_id", "KeyType": "HASH"}
        ]
        keys = dynamodb_table.table.get_primary_keys({"_id": "doc1"})
        assert keys is not None


# --- DynamoDbFindIterator: skip, limit, sort ---

def test_dynamodb_find_iterator_skip_limit():
    data = [
        {"_id": _OID1, "name": "a"},
        {"_id": _OID2, "name": "b"},
        {"_id": _OID3, "name": "c"},
    ]
    it = DynamoDbFindIterator(data)
    it.skip(1).limit(1)
    results = list(it)
    assert len(results) == 1
    assert results[0]["name"] == "b"


def test_dynamodb_find_iterator_sort():
    data = [
        {"_id": _OID2, "order": 2},
        {"_id": _OID1, "order": 1},
        {"_id": _OID3, "order": 3},
    ]
    it = DynamoDbFindIterator(data)
    it.sort("order", "asc")
    results = list(it)
    assert [r["order"] for r in results] == [1, 2, 3]


# --- find_one, insert_one, delete_one, replace_one, count_documents ---

def test_find_one(dynamodb_table):
    dynamodb_table.mock_table.get_item.return_value = {
        "Item": {"_id": _OID1, "name": "single"}
    }
    with patch.object(dynamodb_table.table, "get_primary_keys", return_value={"_id": _OID1}):
        with patch.object(dynamodb_table.table, "get_condition_expresion_values", return_value=({}, "", {})):
            out = dynamodb_table.table.find_one({"_id": _OID1})
    assert out is not None
    assert out["name"] == "single"


def test_insert_one(dynamodb_table):
    dynamodb_table.mock_table.put_item.return_value = {}
    item = {"name": "new", "value": 42}
    dynamodb_table.table.insert_one(item)
    assert dynamodb_table.table.inserted_id is not None
    dynamodb_table.mock_table.put_item.assert_called_once()
    call_item = dynamodb_table.mock_table.put_item.call_args[1]["Item"]
    assert "_id" in call_item
    assert call_item["name"] == "new"


def test_delete_one(dynamodb_table):
    dynamodb_table.mock_table.delete_item.return_value = {}
    with patch.object(dynamodb_table.table, "get_primary_keys", return_value={"_id": "doc1"}):
        dynamodb_table.table.delete_one({"_id": "doc1"})
    assert dynamodb_table.table.deleted_count == 1
    dynamodb_table.mock_table.delete_item.assert_called_once()


def test_replace_one(dynamodb_table):
    # replace_one delegates to update_one (update_item), not put_item
    dynamodb_table.mock_table.update_item.return_value = {}
    dynamodb_table.mock_table.get_item.return_value = {"Item": {"_id": "doc1", "name": "old"}}
    with patch.object(dynamodb_table.table, "get_primary_keys", return_value={"_id": "doc1"}):
        dynamodb_table.table.replace_one({"_id": "doc1"}, {"name": "replaced"})
    dynamodb_table.mock_table.update_item.assert_called_once()


def test_count_documents(dynamodb_table):
    dynamodb_table.mock_table.scan.return_value = {"Items": [], "Count": 0}
    with patch.object(dynamodb_table.table, "get_primary_keys", return_value=None):
        with patch.object(dynamodb_table.table, "get_global_secondary_indexes_keys", return_value=(None, None)):
            with patch.object(dynamodb_table.table, "get_condition_expresion_values", return_value=({}, "", {})):
                n = dynamodb_table.table.count_documents({})
    assert n == 0


# --- DynamodbService: __getitem__, get_table_class, get_iterator_class, table_exists ---

@pytest.fixture
def dynamodb_service():
    with patch.object(DynamodbService, "get_db_config_data"), patch.object(
        DynamodbService, "get_db_connection"
    ):
        app_config = MagicMock()
        app_config.DB_CONFIG = {"app_db_uri": "http://localhost:8000", "dynamdb_prefix": "test_"}
        service = DynamodbService(app_config)
        service._db = MagicMock()
        service._prefix = "test_"
        service.tables = ["test_users"]
        setattr(service, "test_users", DynamoDbTableAbstract({"TableName": "users", "prefix": "test_"}, service._db))
        return service


def test_dynamodb_service_getitem(dynamodb_service):
    table = dynamodb_service["users"]
    assert table is not None
    assert isinstance(table, DynamoDbTableAbstract)


def test_dynamodb_service_get_table_class(dynamodb_service):
    assert dynamodb_service.get_table_class() is DynamoDbTableAbstract


def test_dynamodb_service_get_iterator_class(dynamodb_service):
    assert dynamodb_service.get_iterator_class() is DynamoDbFindIterator


def test_table_exists_true(dynamodb_service):
    dynamodb_service._db.Table.return_value.table_status = "ACTIVE"
    assert dynamodb_service.table_exists("test_users") is True


def test_table_exists_false(dynamodb_service):
    ResourceNotFound = type("ResourceNotFoundException", (Exception,), {})
    dynamodb_service._db.meta.client.exceptions.ResourceNotFoundException = ResourceNotFound
    mock_table = MagicMock()
    type(mock_table).table_status = PropertyMock(side_effect=ResourceNotFound())
    dynamodb_service._db.Table.return_value = mock_table
    assert dynamodb_service.table_exists("nonexistent") is False


def test_dynamodb_service_builder_returns_instance():
    mock_config = MagicMock()
    mock_config.DB_CONFIG = {"app_db_uri": "http://localhost:8000", "dynamdb_prefix": "test_"}
    with patch.object(DynamodbService, "get_db_config_data"), patch.object(DynamodbService, "get_db_connection"):
        builder = DynamodbServiceBuilder()
        instance = builder(mock_config)
    assert instance is not None
    assert isinstance(instance, DynamodbService)
