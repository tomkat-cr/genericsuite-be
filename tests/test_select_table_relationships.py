"""
Tests for select_table 1-1 relationship resolution (GenericDbHelperSuper).
"""
import sys
from unittest.mock import MagicMock

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

from genericsuite.util.generic_db_helpers_super import (  # noqa: E402
    GenericDbHelperSuper
)


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
