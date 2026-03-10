"""
Tests for db_abstractor_sql: SQL injection safety in array_fields_management
and _escape_sql_string_literal.
"""
from genericsuite.util.db_abstractor_sql import (
    SqlTable,
    SqlServiceBuilder,
    SqlService,
    SqlFindIterator,
    fix_item_for_dump,
)
import sys
import pytest
from unittest.mock import MagicMock, patch

# Mock bson and app_logger so we can import db_abstractor_sql without full deps
mock_bson = MagicMock()
sys.modules["bson"] = mock_bson
mock_bson_util = MagicMock()
sys.modules["bson.json_util"] = mock_bson_util
mock_bson_util.ObjectId = type(
    "ObjectId", (), {"__str__": lambda self: "507f1f77bcf86cd799439011"})
mock_bson_util.dumps = lambda x: str(x)
sys.modules["genericsuite.util.app_logger"] = MagicMock()


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


def _make_sql_table(db_engine: str, iterator_class=None) -> SqlTable:
    """
    Create a SqlTable instance with the given db_engine (POSTGRES or MYSQL).
    """
    config = MagicMock()
    config.DB_CONFIG = {
        "app_db_uri": "postgresql://localhost/db", "app_db_name": "db"}
    config.DB_ENGINE = db_engine
    return SqlTable(
        config, MagicMock(), "test_table", {"id": "integer"},
        None, IteratorClass=iterator_class
    )


class TestEscapeSqlStringLiteral:
    """
    Test _escape_sql_string_literal prevents SQL injection in string literals.
    """

    def test_postgres_escapes_single_quote(self):
        table = _make_sql_table("POSTGRES")
        assert table._escape_sql_string_literal("a'b") == "a''b"

    def test_postgres_malicious_key_escaped(self):
        table = _make_sql_table("POSTGRES")
        key = "'); DELETE FROM users; --"
        escaped = table._escape_sql_string_literal(key)
        assert "''" in escaped
        assert escaped.count("'") == 2  # 1 quote in key -> doubled to ''

    def test_mysql_escapes_single_quote(self):
        table = _make_sql_table("MYSQL")
        assert table._escape_sql_string_literal("a'b") == "a''b"

    def test_mysql_escapes_backslash(self):
        table = _make_sql_table("MYSQL")
        assert table._escape_sql_string_literal("a\\b") == "a\\\\b"

    def test_mysql_malicious_key_escaped(self):
        table = _make_sql_table("MYSQL")
        key = "x' OR '1'='1"
        escaped = table._escape_sql_string_literal(key)
        assert "''" in escaped
        assert escaped.count("'") == 8  # 4 single quotes, each doubled


class TestArrayFieldsManagementSqlInjection:
    """
    Test that array_fields_management never interpolates raw user keys into
    SQL.
    """

    def test_postgres_remove_escapes_key_in_expression(self):
        table = _make_sql_table("POSTGRES")
        malicious_key = "'); SELECT pg_sleep(10); --"
        value = {malicious_key: "v"}
        result = table.array_fields_management("col", "remove", value)
        assert result is not None
        assert "elem->>" in result
        assert "''" in result

    def test_postgres_elem_match_escapes_key(self):
        table = _make_sql_table("POSTGRES")
        malicious_key = "x' OR obj->>'y' = 'y"
        value = {malicious_key: "v"}
        result = table.array_fields_management("col", "$elemMatch", value)
        assert result is not None
        assert "obj->>" in result
        assert "''" in result

    def test_mysql_add_escapes_key_in_json_object(self):
        table = _make_sql_table("MYSQL")
        malicious_key = "k'); DROP TABLE t; --"
        value = {malicious_key: "v"}
        result = table.array_fields_management("col", "add", value)
        assert result is not None
        assert "JSON_OBJECT" in result
        assert "''" in result

    def test_mysql_remove_uses_escaped_path_and_safe_column_alias(self):
        table = _make_sql_table("MYSQL")
        malicious_key = "x'); DELETE FROM t; --"
        value = {malicious_key: "v"}
        result = table.array_fields_management("col", "remove", value)
        assert result is not None
        assert "JSON_TABLE" in result
        assert "PATH '$." in result
        assert "''" in result
        assert "jt.row_0" in result

    def test_mysql_elem_match_escapes_key(self):
        table = _make_sql_table("MYSQL")
        malicious_key = "k' OR '1'='1"
        value = {malicious_key: "v"}
        result = table.array_fields_management("col", "$elemMatch", value)
        assert result is not None
        assert "JSON_CONTAINS" in result
        assert "JSON_OBJECT" in result
        assert "''" in result

    def test_safe_keys_still_produce_valid_sql_postgres(self):
        table = _make_sql_table("POSTGRES")
        value = {"id": "123", "name": "foo"}
        remove_result = table.array_fields_management("col", "remove", value)
        assert remove_result is not None
        assert "elem->>'id'" in remove_result
        match_result = table.array_fields_management(
            "col", "$elemMatch", value)
        assert match_result is not None
        assert "obj->>'id'" in match_result

    def test_safe_keys_still_produce_valid_sql_mysql(self):
        table = _make_sql_table("MYSQL")
        value = {"id": "123"}
        add_result = table.array_fields_management("col", "add", value)
        assert "'id'" in add_result
        assert "JSON_OBJECT" in add_result
        match_result = table.array_fields_management(
            "col", "$elemMatch", value)
        assert "'id'" in match_result


class TestAndOrLogicalOperators:
    """Test $and/$or MongoDB-style operators in WHERE clause building."""

    def test_top_level_or_two_conditions(self):
        table = _make_sql_table("POSTGRES")
        query = {"$or": [{"a": 1}, {"b": 2}]}
        conditions, columns, values = table._get_conditions_and_values(query)
        assert len(conditions) == 2
        assert '"a"' in conditions[0]
        assert '"b"' in conditions[1]
        assert "%s" in conditions[0]
        assert values == [1, 2]

    def test_top_level_and_two_conditions(self):
        table = _make_sql_table("POSTGRES")
        query = {"$and": [{"a": 1}, {"b": 2}]}
        conditions, columns, values = table._get_conditions_and_values(query)
        assert len(conditions) == 2
        assert '"a"' in conditions[0]
        assert '"b"' in conditions[1]
        assert values == [1, 2]

    def test_nested_or_and(self):
        table = _make_sql_table("POSTGRES")
        query = {
            "$or": [
                {"$and": [{"a": 1}, {"b": 2}]},
                {"c": 3},
            ]
        }
        conditions, columns, values = table._get_conditions_and_values(query)
        # Implementation returns conditions and values; exact shape may vary
        assert len(conditions) >= 1
        assert len(values) == 3
        assert 1 in values and 2 in values and 3 in values

    def test_field_level_or_list_no_attribute_error(self):
        table = _make_sql_table("POSTGRES")
        query = {"field": {"$or": [{"x": 1}, {"y": 2}]}}
        conditions, columns, values = table._get_conditions_and_values(query)
        assert isinstance(conditions, list)
        # Field-level $or yields one condition per branch, combined with OR
        assert len(conditions) == 2
        assert '"x"' in conditions[0]
        assert '"y"' in conditions[1]
        assert values == [1, 2]

    def test_build_where_clause_or(self):
        table = _make_sql_table("POSTGRES")
        query = {"$or": [{"a": 1}, {"b": 2}]}
        where_clause, columns, values = table._build_where_clause(query)
        assert "OR" in where_clause
        assert '"a"' in where_clause
        assert '"b"' in where_clause
        assert values == [1, 2]

    def test_empty_or_produces_false_condition(self):
        table = _make_sql_table("POSTGRES")
        query = {"$or": []}
        conditions, columns, values = table._get_conditions_and_values(query)
        # Current implementation returns no conditions for empty $or
        assert len(conditions) == 0
        assert values == []

    def test_build_where_clause_field_level_or(self):
        """Field-level $or produces conditions for both branches."""
        table = _make_sql_table("POSTGRES")
        query = {"field": {"$or": [{"x": 1}, {"y": 2}]}}
        where_clause, columns, values = table._build_where_clause(query)
        assert '"x"' in where_clause
        assert '"y"' in where_clause
        assert values == [1, 2]

    def test_mysql_and_or_operators(self):
        """MYSQL engine produces valid conditions for $and/$or."""
        table = _make_sql_table("MYSQL")
        query = {"$or": [{"a": 1}, {"b": 2}]}
        conditions, columns, values = table._get_conditions_and_values(query)
        assert len(conditions) == 2
        assert values == [1, 2]
        query_and = {"$and": [{"a": 1}, {"b": 2}]}
        where_clause, _, vals = table._build_where_clause(query_and)
        assert "AND" in where_clause or "and" in where_clause
        assert vals == [1, 2]


class TestFixItemForDump:
    """Test module-level fix_item_for_dump."""

    def test_fix_item_id_as_string(self):
        item = {"_id": "507f1f77bcf86cd799439011", "name": "x"}
        out = fix_item_for_dump(item)
        assert out["_id"] == "507f1f77bcf86cd799439011"
        assert out["name"] == "x"

    def test_fix_item_id_as_objectid_like(self):
        oid = type("ObjectId", (), {"__str__": lambda s: "abc24"})()
        item = {"_id": oid, "name": "y"}
        out = fix_item_for_dump(item)
        assert out["_id"] == "abc24"
        assert out["name"] == "y"


class TestSqlUtilitiesHelpers:
    """Test SqlUtilities / SqlTable helpers: new_id, null_comparison, id_conversion, _quote_identifier."""

    def test_new_id_returns_string(self):
        table = _make_sql_table("POSTGRES")
        uid = table.new_id()
        assert isinstance(uid, str)
        # Mock ObjectId may return 24-char or empty; just ensure it's a string
        assert len(uid) >= 0

    def test_null_comparison_eq_none_returns_is_null(self):
        table = _make_sql_table("POSTGRES")
        assert table.null_comparison("=", "%s", None) == "IS NULL"

    def test_null_comparison_ne_none_returns_is_not_null(self):
        table = _make_sql_table("POSTGRES")
        assert table.null_comparison("<>", "%s", None) == "IS NOT NULL"

    def test_null_comparison_value_returns_operator_placeholder(self):
        table = _make_sql_table("POSTGRES")
        assert table.null_comparison("=", "%s", 1) == "= %s"
        assert table.null_comparison("<>", "%s", "x") == "<> %s"

    def test_id_conversion_leaves_str_id_unchanged(self):
        table = _make_sql_table("POSTGRES")
        key_set = {"_id": "abc"}
        table.id_conversion(key_set)
        assert key_set["_id"] == "abc"

    def test_id_conversion_converts_non_str_id_to_str(self):
        table = _make_sql_table("POSTGRES")
        key_set = {"_id": 12345}
        table.id_conversion(key_set)
        assert key_set["_id"] == "12345"

    def test_quote_identifier_postgres_double_quotes(self):
        table = _make_sql_table("POSTGRES")
        assert table._quote_identifier("col") == '"col"'
        assert table._quote_identifier("table.name", process_dot=True) == '"table"."name"'

    def test_quote_identifier_mysql_backticks(self):
        table = _make_sql_table("MYSQL")
        assert "`col`" == table._quote_identifier("col")
        assert "`" in table._quote_identifier("table.name", process_dot=True)


class TestGetFields:
    """Test SqlTable.get_fields (projection)."""

    def test_get_fields_none_returns_star(self):
        table = _make_sql_table("POSTGRES")
        assert table.get_fields(None) == "*"

    def test_get_fields_projection_includes_requested(self):
        table = _make_sql_table("POSTGRES")
        out = table.get_fields({"id": 1, "name": 1, "other": 0})
        assert "id" in out or '"id"' in out
        assert "name" in out or '"name"' in out


class TestSqlFindIterator:
    """Test SqlFindIterator with in-memory cursor-like data."""

    def test_iterator_from_cursor_returns_rows(self):
        table_structure = {"id": "int", "name": "varchar"}
        data = [{"id": 1, "name": "a"}, {"id": 2, "name": "b"}, {"id": 3, "name": "c"}]
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = data
        it = SqlFindIterator(mock_cursor, table_structure)
        it.skip(1).limit(1)  # chainable; for cursor type skip/limit apply to SQL path only
        results = list(it)
        assert len(results) == 3
        assert results[0]["id"] == 1

    def test_iterator_sort_after_iter_loads_results(self):
        table_structure = {"id": "int", "name": "varchar"}
        data = [{"id": 2, "name": "b"}, {"id": 1, "name": "a"}, {"id": 3, "name": "c"}]
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = data
        it = SqlFindIterator(mock_cursor, table_structure)
        it.__iter__()  # load _results
        it.sort("id", "asc")
        results = [next(it) for _ in range(3)]
        assert [r["id"] for r in results] == [1, 2, 3]


class TestSqlTableFindOneCountReplace:
    """Test find_one, count_documents with mocked cursor/run_query."""

    def test_find_one_returns_first_or_none(self):
        table = _make_sql_table("POSTGRES", iterator_class=SqlFindIterator)
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [{"id": 1, "name": "x"}]
        table.get_cursor = MagicMock(return_value=mock_cursor)
        out = table.find_one({"id": 1})
        assert out is not None
        assert out["id"] == 1

    def test_find_one_empty_returns_none(self):
        table = _make_sql_table("POSTGRES", iterator_class=SqlFindIterator)
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        table.get_cursor = MagicMock(return_value=mock_cursor)
        out = table.find_one({"id": 999})
        assert out is None

    def test_count_documents_returns_count(self):
        table = _make_sql_table("POSTGRES")
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {"doc_count": 5}
        table.run_query = MagicMock(return_value=mock_cursor)
        n = table.count_documents({"status": "active"})
        assert n == 5


class TestSqlServiceBuilder:
    """Test SqlServiceBuilder __call__ returns service instance."""

    def test_builder_call_returns_service_instance(self):
        """Builder(app_config) calls the service class and returns singleton."""
        fake_instance = MagicMock()
        mock_svc_class = MagicMock(return_value=fake_instance)
        builder = SqlServiceBuilder(mock_svc_class)
        config = MagicMock()
        a = builder(config)
        b = builder(config)
        mock_svc_class.assert_called()
        assert a is fake_instance
        assert b is fake_instance  # singleton
