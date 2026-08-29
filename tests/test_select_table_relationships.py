"""
Tests for select_table 1-1 relationship resolution (GenericDbHelperSuper).
"""
import ast
import os
import sys
from unittest.mock import MagicMock, patch

_bson = MagicMock()
_bson.json_util = MagicMock()
_bson.json_util.dumps = lambda x: str(x)
_bson.json_util.ObjectId = str
sys.modules.setdefault("bson", _bson)
sys.modules.setdefault("bson.json_util", _bson.json_util)
sys.modules.setdefault("genericsuite.util.app_logger", MagicMock())
sys.modules.setdefault("genericsuite.util.framework_abs_layer", MagicMock())

_util_mock = MagicMock()
_util_mock.get_default_resultset.return_value = {
    "error": False, "error_message": None, "resultset": {}, "totalPages": None
}
sys.modules.setdefault("genericsuite.util.utilities", _util_mock)
sys.modules.setdefault("genericsuite.util.db_abstractor", MagicMock())
sys.modules.setdefault("genericsuite.util.db_abstractor_super", MagicMock())
sys.modules.setdefault("genericsuite.util.config_dbdef_helpers", MagicMock())
sys.modules.setdefault("genericsuite.util.datetime_utilities", MagicMock())
sys.modules.setdefault("genericsuite.util.passwords", MagicMock())

# Other test modules (e.g. test_util_jwt.py) install a MagicMock for
# generic_db_helpers_super when they are collected first. These tests need
# the REAL class, so drop any cached entry and import fresh — this keeps
# the file correct under ANY collection order, not just alphabetical.
sys.modules.pop("genericsuite.util.generic_db_helpers_super", None)
from genericsuite.util.generic_db_helpers_super import (  # noqa: E402
    GenericDbHelperSuper
)

# Some other test modules mock "genericsuite.util.generic_db_helpers"
# wholesale (via setdefault, or even direct assignment for "bson"/
# "bson.json_util") for their own isolation purposes. Since these tests
# below need the REAL GenericDbHelper class calling a *working* dumps(),
# force our own consistent bson mock back in and do a fresh import here,
# regardless of what any earlier-collected test file already put in
# sys.modules for these keys.
sys.modules["bson"] = _bson
sys.modules["bson.json_util"] = _bson.json_util
sys.modules.pop("genericsuite.util.generic_db_helpers", None)
from genericsuite.util.generic_db_helpers import GenericDbHelper  # noqa: E402
from bson.json_util import ObjectId  # noqa: E402


def make_helper(field_elements: list) -> GenericDbHelperSuper:
    """Build a helper without touching DB/config loading."""
    helper = GenericDbHelperSuper.__new__(GenericDbHelperSuper)
    helper.cnf_db = {'fieldElements': field_elements}
    helper.error_message = None
    helper.table_name = 'test_table'
    return helper


def test_get_select_table_relationships_defaults():
    helper = make_helper([
        {'name': 'user_id', 'type': 'select_table', 'related_table': 'users'},
        {'name': 'title', 'type': 'text'},
    ])
    rels = helper.get_select_table_relationships()
    assert rels == [{
        'local_field': 'user_id',
        'related_table': 'users',
        'related_key': '_id',
        'description_fields': ['name'],
        'description_separator': ' ',
        'related_filter': {},
    }]


def test_get_select_table_relationships_explicit_attrs():
    helper = make_helper([{
        'name': 'category_id', 'type': 'select_table',
        'related_table': 'categories', 'related_key': 'code',
        'description_fields': ['code', 'label'],
        'description_separator': ' - ',
        'related_filter': {'active': True},
    }])
    rels = helper.get_select_table_relationships()
    assert rels[0]['related_key'] == 'code'
    assert rels[0]['description_fields'] == ['code', 'label']
    assert rels[0]['description_separator'] == ' - '
    assert rels[0]['related_filter'] == {'active': True}


def test_get_select_table_relationships_skips_missing_related_table():
    helper = make_helper([
        {'name': 'user_id', 'type': 'select_table'},  # no related_table
    ])
    assert helper.get_select_table_relationships() == []


def test_get_select_table_relationships_no_field_elements():
    helper = make_helper([])
    assert helper.get_select_table_relationships() == []


def test_build_relationship_description():
    helper = make_helper([])
    rel = {'description_fields': ['firstname', 'lastname'],
           'description_separator': ' '}
    assert helper.build_relationship_description(
        {'firstname': 'John', 'lastname': 'Doe'}, rel) == 'John Doe'


def test_build_relationship_description_skips_missing_fields():
    helper = make_helper([])
    rel = {'description_fields': ['firstname', 'lastname'],
           'description_separator': ' '}
    assert helper.build_relationship_description(
        {'firstname': 'John'}, rel) == 'John'


REL_USERS = {
    'local_field': 'user_id', 'related_table': 'users',
    'related_key': '_id', 'description_fields': ['name'],
    'description_separator': ' ', 'related_filter': {},
}


def test_resolve_relationships_merges_descriptions():
    helper = make_helper([])
    fake_users_table = MagicMock()
    fake_users_table.find.return_value = [
        {'_id': 'aaa', 'name': 'John Doe'},
        {'_id': 'bbb', 'name': 'Jane Roe'},
    ]
    fake_db = {'users': fake_users_table}
    rows = [{'user_id': 'aaa'}, {'user_id': 'bbb'}, {'user_id': 'zzz'}]
    with patch('genericsuite.util.generic_db_helpers_super.db', fake_db):
        result = helper.resolve_relationships(rows, [REL_USERS])
    assert result[0]['user_id_description'] == 'John Doe'
    assert result[1]['user_id_description'] == 'Jane Roe'
    assert result[2]['user_id_description'] is None  # no match
    # One single $in query for the whole page (no N+1)
    assert fake_users_table.find.call_count == 1
    query_arg = fake_users_table.find.call_args[0][0]
    assert '$in' in query_arg['_id']


def test_resolve_relationships_null_fk():
    helper = make_helper([])
    fake_db = {'users': MagicMock()}
    rows = [{'user_id': None}, {'title': 'no fk attr'}]
    with patch('genericsuite.util.generic_db_helpers_super.db', fake_db):
        result = helper.resolve_relationships(rows, [REL_USERS])
    assert result[0]['user_id_description'] is None
    assert result[1]['user_id_description'] is None
    fake_db['users'].find.assert_not_called()


def test_resolve_relationships_empty_inputs():
    helper = make_helper([])
    assert helper.resolve_relationships([], [REL_USERS]) == []
    rows = [{'user_id': 'aaa'}]
    assert helper.resolve_relationships(rows, []) == rows


def test_resolve_relationships_db_error_does_not_fail():
    helper = make_helper([])
    fake_users_table = MagicMock()
    fake_users_table.find.side_effect = Exception('boom')
    fake_db = {'users': fake_users_table}
    rows = [{'user_id': 'aaa'}]
    with patch('genericsuite.util.generic_db_helpers_super.db', fake_db):
        result = helper.resolve_relationships(rows, [REL_USERS])
    assert result[0]['user_id_description'] is None


def test_resolve_relationships_applies_related_filter_and_projection():
    helper = make_helper([])
    rel = dict(REL_USERS, related_filter={'active': True},
               description_fields=['firstname', 'lastname'])
    fake_users_table = MagicMock()
    fake_users_table.find.return_value = []
    fake_db = {'users': fake_users_table}
    with patch('genericsuite.util.generic_db_helpers_super.db', fake_db):
        helper.resolve_relationships([{'user_id': 'aaa'}], [rel])
    query_arg, projection_arg = fake_users_table.find.call_args[0]
    assert query_arg['active'] is True
    assert projection_arg == {'firstname': 1, 'lastname': 1, '_id': 1}


def make_full_helper(field_elements, main_rows):
    """GenericDbHelper wired with a fake main table, bypassing __init__."""
    helper = GenericDbHelper.__new__(GenericDbHelper)
    helper.cnf_db = {'fieldElements': field_elements}
    helper.error_message = None
    helper.table_name = 'main_table'
    helper.name = 'Main'
    helper.title = 'Mains'
    helper.mandatory_filters = {}
    helper.query_params = {'only_listing_cols': '0'}
    helper.table_type = 'main_table'
    helper.sub_type = ''
    fake_cursor = MagicMock()
    fake_cursor.sort.return_value = fake_cursor
    fake_cursor.skip.return_value = fake_cursor
    fake_cursor.limit.return_value = fake_cursor
    fake_cursor.__iter__ = lambda self_: iter(main_rows)
    helper.table_obj = MagicMock()
    helper.table_obj.find.return_value = fake_cursor
    helper.table_obj.count_documents.return_value = len(main_rows)
    return helper


def test_fetch_list_resolves_select_table_descriptions():
    # Forces the default find()+resolve_relationships path (not the
    # MongoDB $lookup fast path, covered separately) by disabling the
    # MONGODB engine flag for the duration of this call.
    helper = make_full_helper(
        [{'name': 'user_id', 'type': 'select_table',
          'related_table': 'users', 'listing': True}],
        [{'_id': '1', 'user_id': 'aaa'}],
    )
    fake_users_table = MagicMock()
    fake_users_table.find.return_value = [{'_id': 'aaa', 'name': 'John Doe'}]
    with patch('genericsuite.util.generic_db_helpers_super.db',
               {'users': fake_users_table}), \
            patch.dict(os.environ, {'APP_DB_ENGINE': ''}):
        result = helper.fetch_list(skip=0, limit=10)
    assert result['error'] is False
    # NOTE: this test suite mocks bson.json_util.dumps as `str(x)` (Python
    # repr, not real JSON) for every test module that touches it, so we
    # decode with ast.literal_eval instead of bson.json_util.loads here.
    rows = ast.literal_eval(result['resultset'])
    assert rows[0]['user_id_description'] == 'John Doe'


def test_fetch_list_without_relationships_unchanged():
    helper = make_full_helper(
        [{'name': 'title', 'type': 'text', 'listing': True}],
        [{'_id': '1', 'title': 'Hello'}],
    )
    result = helper.fetch_list(skip=0, limit=10)
    assert result['error'] is False
    # NOTE: this test suite mocks bson.json_util.dumps as `str(x)` (Python
    # repr, not real JSON) for every test module that touches it, so we
    # decode with ast.literal_eval instead of bson.json_util.loads here.
    rows = ast.literal_eval(result['resultset'])
    assert rows == [{'_id': '1', 'title': 'Hello'}]


def test_fetch_row_resolves_select_table_descriptions():
    helper = make_full_helper(
        [{'name': 'user_id', 'type': 'select_table',
          'related_table': 'users'}],
        [],
    )
    helper.fetch_row_raw = MagicMock(return_value={
        'error': False, 'error_message': None,
        'resultset': {'_id': '1', 'user_id': 'aaa'},
    })
    fake_users_table = MagicMock()
    fake_users_table.find.return_value = [{'_id': 'aaa', 'name': 'John Doe'}]
    with patch('genericsuite.util.generic_db_helpers_super.db',
               {'users': fake_users_table}):
        result = helper.fetch_row('1')
    assert result['error'] is False
    # NOTE: this test suite mocks bson.json_util.dumps as `str(x)` (Python
    # repr, not real JSON) for every test module that touches it, so we
    # decode with ast.literal_eval instead of bson.json_util.loads here.
    row = ast.literal_eval(result['resultset'])
    assert row['user_id_description'] == 'John Doe'


def test_fetch_related_rows_dynamodb_uses_batch_get():
    helper = make_helper([])
    fake_users_table = MagicMock()
    fake_users_table.batch_get.return_value = [
        {'_id': 'aaa', 'name': 'John Doe'}]
    with patch('genericsuite.util.generic_db_helpers_super.db',
               {'users': fake_users_table}), \
            patch.dict(os.environ, {'APP_DB_ENGINE': 'DYNAMODB'}):
        rows = helper._fetch_related_rows(
            REL_USERS, ['aaa'], {'name': 1, '_id': 1})
    assert rows == [{'_id': 'aaa', 'name': 'John Doe'}]
    fake_users_table.find.assert_not_called()


def test_fetch_related_rows_dynamodb_dedupes_objectid_and_string_keys():
    # resolve_relationships() appends both the raw string FK and its
    # ObjectId() form to query_values when related_key == '_id' (see
    # resolve_relationships), so a real 24-hex FK arrives here twice:
    # once as str, once as ObjectId. The DynamoDb branch must dedupe
    # before calling batch_get, or DynamoDB raises ValidationException
    # on duplicate keys and the whole batch falls back to find() (silent
    # [FRR1] fallback), defeating the BatchGetItem fast path.
    helper = make_helper([])
    fake_users_table = MagicMock()
    fake_users_table.batch_get.return_value = [
        {'_id': '66aabbccddeeff0011223344', 'name': 'John Doe'}]
    hex_id = '66aabbccddeeff0011223344'
    query_values = [hex_id, ObjectId(hex_id)]
    with patch('genericsuite.util.generic_db_helpers_super.db',
               {'users': fake_users_table}), \
            patch.dict(os.environ, {'APP_DB_ENGINE': 'DYNAMODB'}):
        helper._fetch_related_rows(
            REL_USERS, query_values, {'name': 1, '_id': 1})
    fake_users_table.find.assert_not_called()
    fake_users_table.batch_get.assert_called_once()
    called_keys = fake_users_table.batch_get.call_args[0][0]
    assert called_keys.count(hex_id) == 1
    assert len(called_keys) == 1


def test_fetch_related_rows_dynamodb_falls_back_on_error():
    helper = make_helper([])
    fake_users_table = MagicMock()
    fake_users_table.batch_get.side_effect = Exception('boom')
    fake_users_table.find.return_value = [{'_id': 'aaa', 'name': 'John Doe'}]
    with patch('genericsuite.util.generic_db_helpers_super.db',
               {'users': fake_users_table}), \
            patch.dict(os.environ, {'APP_DB_ENGINE': 'DYNAMODB'}):
        rows = helper._fetch_related_rows(
            REL_USERS, ['aaa'], {'name': 1, '_id': 1})
    assert rows == [{'_id': 'aaa', 'name': 'John Doe'}]
    fake_users_table.find.assert_called_once()


def test_dynamodb_batch_get_chunks_and_retries_unprocessed():
    # Pop mocked modules to import the real DynamoDB class
    sys.modules.pop("genericsuite.util.db_abstractor_super", None)
    sys.modules.pop("genericsuite.util.db_abstractor_elem_match", None)
    sys.modules.pop("genericsuite.util.db_abstractor_dynamodb", None)
    from genericsuite.util.db_abstractor_dynamodb import (
        DynamoDbTableAbstract)
    table = DynamoDbTableAbstract.__new__(DynamoDbTableAbstract)
    table._prefix = ''
    table._table_name = 'users'
    table._key_schema = [{'AttributeName': '_id', 'KeyType': 'HASH'}]
    table._attribute_definitions = []
    table._global_secondary_indexes = []
    conn = MagicMock()
    # First call returns one item + unprocessed keys; retry returns rest.
    conn.batch_get_item.side_effect = [
        {'Responses': {'users': [{'_id': 'aaa', 'name': 'John'}]},
         'UnprocessedKeys': {'users': {'Keys': [{'_id': 'bbb'}]}}},
        {'Responses': {'users': [{'_id': 'bbb', 'name': 'Jane'}]},
         'UnprocessedKeys': {}},
    ]
    table._db_conection = conn
    result = table.batch_get(['aaa', 'bbb'])
    assert len(result) == 2
    assert conn.batch_get_item.call_count == 2
    # 150 keys -> chunked into 100 + 50 (2 more calls, no retries)
    conn.batch_get_item.side_effect = [
        {'Responses': {'users': []}, 'UnprocessedKeys': {}},
        {'Responses': {'users': []}, 'UnprocessedKeys': {}},
    ]
    conn.batch_get_item.reset_mock()
    table.batch_get([str(i) for i in range(150)])
    assert conn.batch_get_item.call_count == 2


def test_dynamodb_batch_get_raises_after_max_retries():
    # Pop mocked modules to import the real DynamoDB class
    sys.modules.pop("genericsuite.util.db_abstractor_super", None)
    sys.modules.pop("genericsuite.util.db_abstractor_elem_match", None)
    sys.modules.pop("genericsuite.util.db_abstractor_dynamodb", None)
    from genericsuite.util.db_abstractor_dynamodb import (
        DynamoDbTableAbstract)
    table = DynamoDbTableAbstract.__new__(DynamoDbTableAbstract)
    table._prefix = ''
    table._table_name = 'users'
    table._key_schema = [{'AttributeName': '_id', 'KeyType': 'HASH'}]
    table._attribute_definitions = []
    table._global_secondary_indexes = []
    conn = MagicMock()
    # ALWAYS returns non-empty UnprocessedKeys -> must raise, not hang.
    conn.batch_get_item.return_value = {
        'Responses': {'users': []},
        'UnprocessedKeys': {'users': {'Keys': [{'_id': 'aaa'}]}},
    }
    table._db_conection = conn
    with patch('genericsuite.util.db_abstractor_dynamodb.time.sleep'):
        try:
            table.batch_get(['aaa'])
            assert False, "batch_get should raise after max retries"
        except RuntimeError as err:
            assert '[BGUK1]' in str(err)
    assert conn.batch_get_item.call_count == 5  # capped at max attempts


def test_fetch_list_mongodb_uses_lookup_pipeline():
    helper = make_full_helper(
        [{'name': 'user_id', 'type': 'select_table',
          'related_table': 'users', 'listing': True}],
        [],
    )
    helper.table_obj.aggregate.return_value = [
        {'_id': '1', 'user_id': 'aaa',
         '_rel_user_id': [{'_id': 'aaa', 'name': 'John Doe'}]},
        {'_id': '2', 'user_id': 'zzz', '_rel_user_id': []},
    ]
    with patch.dict(os.environ, {'APP_DB_ENGINE': 'MONGODB'}):
        result = helper.fetch_list(skip=0, limit=10)
    assert result['error'] is False
    rows = ast.literal_eval(result['resultset'])
    assert rows[0]['user_id_description'] == 'John Doe'
    assert rows[1]['user_id_description'] is None
    assert '_rel_user_id' not in rows[0]
    pipeline = helper.table_obj.aggregate.call_args[0][0]
    stages = [list(stage.keys())[0] for stage in pipeline]
    assert '$lookup' in stages
    assert stages.index('$skip' if '$skip' in stages else '$sort') \
        < stages.index('$lookup')  # join happens after pagination
    helper.table_obj.find.assert_not_called()


def test_fetch_list_mongodb_lookup_falls_back_on_error():
    helper = make_full_helper(
        [{'name': 'user_id', 'type': 'select_table',
          'related_table': 'users', 'listing': True}],
        [{'_id': '1', 'user_id': 'aaa'}],
    )
    helper.table_obj.aggregate.side_effect = Exception('no aggregate')
    fake_users_table = MagicMock()
    fake_users_table.find.return_value = [{'_id': 'aaa', 'name': 'John Doe'}]
    with patch('genericsuite.util.generic_db_helpers_super.db',
               {'users': fake_users_table}), \
            patch.dict(os.environ, {'APP_DB_ENGINE': 'MONGODB'}):
        result = helper.fetch_list(skip=0, limit=10)
    assert result['error'] is False
    rows = ast.literal_eval(result['resultset'])
    assert rows[0]['user_id_description'] == 'John Doe'


def test_fetch_related_rows_falls_back_when_batch_get_exhausts_retries():
    helper = make_helper([])
    fake_users_table = MagicMock()
    fake_users_table.batch_get.side_effect = RuntimeError(
        'batch_get: unprocessed keys remain after max retries [BGUK1]')
    fake_users_table.find.return_value = [{'_id': 'aaa', 'name': 'John Doe'}]
    with patch('genericsuite.util.generic_db_helpers_super.db',
               {'users': fake_users_table}), \
            patch.dict(os.environ, {'APP_DB_ENGINE': 'DYNAMODB'}):
        rows = helper._fetch_related_rows(
            REL_USERS, ['aaa'], {'name': 1, '_id': 1})
    assert rows == [{'_id': 'aaa', 'name': 'John Doe'}]
    fake_users_table.find.assert_called_once()
