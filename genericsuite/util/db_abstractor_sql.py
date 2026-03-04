"""
DbAbstractorSQL: Database abstraction layer for SQL databases
"""

from typing import List, Dict, Any, Tuple, Union, Callable
import json

from bson.json_util import dumps, ObjectId
from decimal import Decimal

from genericsuite.util.db_abstractor_super import DbAbstract
from genericsuite.util.app_logger import log_debug, log_error

DEBUG = False


def fix_item_for_dump(item: Dict):
    """
    Fix the item to be used in the application.
    """
    def fix_value(key: str, value: Any):
        if isinstance(value, ObjectId) or key == "_id":
            return str(value).strip()
        if isinstance(value, Decimal):
            return float(value)
        return value
    return {key: fix_value(key, value) for key, value in item.items()}


class SqlUtilities(DbAbstract):
    """
    SQL Utilities class
    """

    def new_id(self) -> str:
        """
        Generate mongodb styled "_id"
        """
        return str(ObjectId())

    def id_conversion(self, key_set: Dict) -> Dict:
        """
        To avoid error working internally with mongodb styled "_id"
        """
        if "_id" in key_set and not isinstance(key_set["_id"], str):
            key_set["_id"] = str(key_set["_id"])
        return key_set

    def null_comparison(self, operator: str, placeholder: str, value: Any
                        ) -> str:
        """
        Dynamically adjust the comparison operator to IS when the value is
        None.

        In SQL, comparing with NULL using = (i.e., column = NULL) evaluates to
        unknown, not true, so it's required to use IS NULL for NULL
        comparisons. The database driver will likely substitute Python's None
        with SQL NULL, leading to this issue.

        Args:
            operator (str): the comparison operator. It only can be "=" or "<>"
            placeholder (str): normally it should be "%s"
            value (Any): the value that will replace the placeholder.
                If it is None the IS NULL / NOT IS NULL will be returned

        Returns:
            (str): if value is None and operator is "=", "IS NULL"
                if value is None and operator is "<>", "IS NOT NULL"
                Otherwise "{operator} {placeholder}", e.g. "= %s" or "<> %s"
        """
        if value is None:
            return " IS NULL" if operator == "=" \
                else "IS NOT NULL"
        return f"{operator} {placeholder}"

    def _quote_identifier(self, identifier: str,
                          process_dot: bool = False) -> str:
        """
        Quote a SQL identifier (table name or column name)
        using double quotes to avoid SQL Injection.
        """
        # Escape double quotes within the identifier, so an attacker
        # cannot provide a malicious column name or table name (if
        # user-controlled) containing double quotes to break out of the
        # quoted string and inject arbitrary SQL commands. For example,
        # an identifier like col" = 1 OR "1" = "1 would result in
        # "col" = 1 OR "1" = "1", which alters the query logic.
        quote_char = "`" if self.db_engine == "MYSQL" else '"'
        identifier = identifier.replace('"', '\\"')
        if self.db_engine == "MYSQL":
            identifier = identifier.replace('`', '\\`')
        if process_dot:
            # Normally this is for table names
            identifier = identifier.replace(".", f"{quote_char}.{quote_char}")
        return f'{quote_char}{identifier}{quote_char}'

    def _get_sql_operator_mapping(self) -> dict:
        return {
            "$eq": "=",
            "$ne": "<>",
            "$gt": ">",
            "$gte": ">=",
            "$lt": "<",
            "$lte": "<=",
            "$in": "IN",
            "$nin": "NOT IN",
            "$and": "AND",
            "$or": "OR",
        }

    def _get_sql_operator(self, mongo_op: str) -> str:
        """
        Map MongoDB operators to SQL operators
        """
        return self._get_sql_operator_mapping().get(mongo_op, "=")

    def _normalize_objectid(self, value: Any) -> Any:
        """
        Normalize ObjectId to be used in SQL query
        by converting it to a string.
        """
        if isinstance(value, ObjectId):
            return str(value)
        elif isinstance(value, list):
            return [self._normalize_objectid(item) for item in value]
        elif isinstance(value, dict):
            return {k: self._normalize_objectid(v) for k, v in value.items()}
        return value

    def _prepare_value_for_sql(self, value: Any) -> Any:
        """
        Prepare one value for a SQL statement
        """
        return \
            json.dumps(value) if isinstance(value, (list, dict)) \
            else value

    def _prepare_values_for_sql(self, values: List[Any]) -> List[Any]:
        """
        Prepare values for a SQL statement
        """
        return [self._prepare_value_for_sql(value) for value in values]

    def _get_conditions_and_values(
        self,
        query_params: Dict
    ) -> Tuple[List[str], List[str], List[Any]]:
        """
        Build SQL WHERE clause from MongoDB-style query params
        """
        conditions = []
        columns = []
        values = []
        ops_mapping = self._get_sql_operator_mapping()

        def special_case_handling(col_name: str, op: str, op_val: Any):
            """
            Special case handling for $regex, $and, $or, $in, $nin
            """
            _ = DEBUG and log_debug(
                f"||| special_case_handling | op: {op} "
                f"| op_val: {op_val} | col_name: {col_name}")

            quoted_col = self._quote_identifier(col_name)

            if op == "$regex":
                # Simple regex mapping to LIKE or ~
                # Assuming simple contains for now as per DynamoDB
                # implementation
                conditions.append(f"{quoted_col} LIKE %s")
                # op_val will be a dictionary with $regex and $options
                # E.g. {'$regex': '.*1.*', '$options': 'si'}
                regex_value = op_val.get("$regex") if isinstance(
                    op_val, dict) else str(op_val)
                regex_value = regex_value.replace(".*", "")
                # Very basic regex support
                columns.append(col_name)
                values.append(f"%{regex_value}%")

            elif op == "$elemMatch":
                # op_val will be a dictionary with $elemMatch condition(s)
                # E.g. {'id': 'xyz'}
                array_cond = self.array_fields_management(
                    col_name, "$elemMatch", op_val)
                _ = DEBUG and log_debug(
                    f"||| special_case_handling [$elemMatch]"
                    f" | col_name: {col_name} "
                    f"| array_cond: {array_cond}"
                )
                conditions.append(array_cond)
                values.extend([one_val for one_val in op_val.values()])

            elif op in ["$and", "$or"]:
                # Handle $and and $or
                sub_conditions = []
                for sub_op, sub_op_val in op_val.items():
                    if sub_op == "$regex":
                        # In this case, the sub_op is regex:
                        # E.g. {'$regex': '.*1.*', '$options': 'si'}
                        # "op_val.items()"" will have 2 items. We need to
                        # extract the value from the first item.
                        special_case_handling(
                            col_name, sub_op, op_val)
                        # Break here because the next one is not needed.
                        # E.g. '$options': 'si'
                        return
                    sub_conditions.append(
                        f"{quoted_col} "
                        f"{self._get_sql_operator(sub_op)} %s")
                    columns.append(col_name)
                    values.append(sub_op_val)
                conditions.append(
                    f"({f' {self._get_sql_operator(op)} '.join(
                        sub_conditions)})")

            elif op in ["$in", "$nin"]:
                """
                For example:
                    For "op_val" = ['1', '22', '333'],
                       "placeholders" will be '%s, %s, %s'.
                    Then "conditions" will have:
                       ['"col_name" IN (%s, %s, %s)'].
                    Finally it needs 3 values that "values.extend(op_val)"
                    will add...
                """
                placeholders = ", ".join(["%s"] * len(op_val))
                sql_op = self._get_sql_operator(op)
                columns.append(col_name)
                conditions.append(
                    f"{quoted_col} {sql_op} ({placeholders})")
                values.extend(op_val)

            elif op in ops_mapping:
                sql_op = ops_mapping[op]
                columns.append(col_name)
                conditions.append(f"{quoted_col} {sql_op} %s")
                values.append(op_val)

            else:
                sql_op = self._get_sql_operator(op)
                columns.append(col_name)
                conditions.append(f"{quoted_col} {sql_op} %s")
                values.append(op_val)

        for key, value in query_params.items():
            # Handle _id mapping to id if necessary, or keep as _id if column
            # exists.
            # For now assuming column name is _id based on DynamoDB/Mongo usage
            col_name = key

            _ = DEBUG and log_debug(
                f"||| _get_conditions_and_values [1] | col_name: {col_name} "
                f"| value: {value}")

            if isinstance(value, list):
                for item in value:
                    for sub_col_name, sub_val in item.items():

                        if sub_col_name.startswith("$"):
                            special_case_handling(
                                col_name, sub_col_name, sub_val)

                        elif col_name.startswith("$"):
                            """
                            Example:

                            col_name: $or

                            value: [
                                {
                                    'firstname': {
                                        '$regex': '.*fyn.*',
                                        '$options': 'si'
                                    }
                                },
                                {
                                    'creation_date': {
                                        '$lte': 946771199.0,
                                        '$gte': 946684800.0
                                    }
                                }
                            ]
                            """

                            if isinstance(sub_val, dict):
                                if list(sub_val.keys())[0] == "$regex":
                                    special_case_handling(
                                        sub_col_name, "$regex", sub_val)
                                else:
                                    for cond_key, cond_val in sub_val.items():
                                        special_case_handling(
                                            sub_col_name, cond_key, cond_val)
                            else:
                                special_case_handling(
                                    sub_col_name, sub_val, sub_val)
                        else:
                            # Not an operator, treat as field-value pair
                            # Condition: "sub_col_name = %s"
                            value_normalized = self._normalize_objectid(
                                sub_val)
                            conditions.append(
                                f"{self._quote_identifier(sub_col_name)} " +
                                self.null_comparison("=", "%s",
                                                     value_normalized))
                            values.append(value_normalized)

            elif isinstance(value, dict):
                for op_key, op_val in value.items():
                    if op_key.startswith("$"):
                        special_case_handling(col_name, op_key, op_val)
                    else:
                        # Nested dict but not an operator?
                        # Handle as json or just equality
                        # Condition: "key = %s"
                        value_normalized = self._normalize_objectid(value)
                        conditions.append(
                            f"{self._quote_identifier(key)}" +
                            self.null_comparison("=", "%s", value_normalized)
                        )
                        values.append(value_normalized)
                        break
            else:
                # Condition: col_name = %s
                value_normalized = self._normalize_objectid(value)
                conditions.append(
                    f"{self._quote_identifier(col_name)} " +
                    self.null_comparison("=", "%s", value_normalized))
                values.append(value_normalized)

        _ = DEBUG and log_debug(
            "||| _get_conditions_and_values [2]" +
            f"\n| columns: {columns} " +
            f"\n| conditions: {conditions} " +
            f"\n| values: {values}")

        return conditions, columns, values

    def get_cursor(self):
        """
        Return cursor object for the specific database connection.

        For example:

        # PostgreSQL
        from psycopg2.extras import RealDictCursor
        return _conn.cursor(cursor_factory=RealDictCursor)

        # MySQL
        return _conn.cursor(dictionary=True)

        # Supabase
        from supabase import create_client, Client
        url: str = Config().DB_CONFIG.get("app_db_uri")
        key: str = os.environ.get("SUPABASE_KEY")
        supabase: Client = create_client(url, key)
        """
        self.not_implemented("get_cursor")

    def build_select_sql(
        self,
        table_name: str,
        fields: Union[str, List[str]],
        where: Union[str, List[str]] = None,
        values: Union[List, Dict] = None,
        order_by: Union[str, List[str]] = None,
        limit: int = None,
        offset: int = None
    ):
        """
        Build a raw SQL query and return the cursor object.
        """
        fields_str = fields if isinstance(fields, str) else ", ".join(
            [self._quote_identifier(f) for f in fields])
        quoted_table = self._quote_identifier(table_name, process_dot=True)
        sql = f"SELECT {fields_str} FROM {quoted_table}"
        if where:
            sql += f" WHERE {where}"
        if order_by:
            # Basic order_by quoting, assuming simple column names
            # or "col DESC"
            if isinstance(order_by, list):
                order_by_parts = []
                for ob in order_by:
                    parts = ob.split()
                    quoted_col = self._quote_identifier(parts[0])
                    if len(parts) > 1:
                        order_by_parts.append(f"{quoted_col} {parts[1]}")
                    else:
                        order_by_parts.append(quoted_col)
                sql += f" ORDER BY {', '.join(order_by_parts)}"
            else:
                sql += f" ORDER BY {order_by}"
        if limit:
            sql += f" LIMIT {limit}"
        if offset:
            sql += f" OFFSET {offset}"
        _ = DEBUG and log_debug(f"SqlUtilities.build_select_sql: {sql}")
        return sql

    def cursor_execute(
        self,
        sql: str,
        values: Union[List, Dict] = None,
    ):
        """
        Execute a raw SQL query statement and return the cursor object.
        """
        _ = DEBUG and log_debug(
            "SqlUtilities.cursor_execute"
            + f"\n | sql: {sql}")
        cursor = self.get_cursor()

        try:
            cursor.execute(sql, values)
        except Exception as e:
            _ = DEBUG and log_debug(
                "SqlUtilities.cursor_execute | error: " + str(e))
            raise e
        _ = DEBUG and log_debug(
            "SqlUtilities.cursor_execute | cursor.execute result:"
            + f"\n{cursor}")
        return cursor

    def run_query(
        self,
        table_name: str,
        fields: Union[str, List[str]],
        where: Union[str, List[str]] = None,
        values: Union[List, Dict] = None,
        order_by: Union[str, List[str]] = None,
        limit: int = None,
        offset: int = None,
    ):
        """
        Execute a raw SQL query and return the cursor object.
        """
        sql = self.build_select_sql(
            table_name,
            fields,
            where,
            values,
            order_by,
            limit,
            offset
        )
        _ = DEBUG and log_debug(
            "SqlUtilities.run_query"
            + f"\n | sql: {sql}"
            + f"\n | values: {values}")
        return self.cursor_execute(sql, values)

    def get_fields(self, projection: Dict = None):
        """
        Return fields of the table.
        """
        # Projection support (basic)
        fields_str = "*"
        if projection:
            # Filter fields with value 1
            included = [self._quote_identifier(
                k) for k, v in projection.items() if v == 1]
            if included:
                fields_str = ", ".join(included)
        if DEBUG:
            log_debug(f"SqlUtilities.get_fields: {fields_str}")
        return fields_str

    def info_schema_table_names(self):
        return {
            "tables": "information_schema.tables",
            "columns": "information_schema.columns",
        }


class SqlFindIterator:
    """
    SQL find iterator
    """

    def __init__(
        self,
        cursorOrSql: Any,
        table_structure: Dict = None,
        cursor_execute: Callable = None,
        cursor_values: Union[List, Dict] = None
    ):
        self._type = "sql" if isinstance(cursorOrSql, str) else "cursor"
        self._cursor = cursorOrSql if self._type == "cursor" else None
        self._sql: str = cursorOrSql if self._type == "sql" else None
        self._cursor_execute = cursor_execute
        self._cursor_values = cursor_values
        self._results = None
        self._idx = 0
        self._table_structure = table_structure
        self._defered_sort = None
        self._defered_skip = None
        self._defered_limit = None

    def _is_json_field(self, field: str) -> bool:
        return self._table_structure[field].lower() in [
            "json",
            "jsonb",
            "json_array",
            "json_object",
            "json_array_agg",
            "json_object_agg",
        ]

    def _row_types_convertion(self, row: Dict):
        for key, value in row.items():
            if key in self._table_structure:
                if self._is_json_field(key):
                    if isinstance(value, str):
                        row[key] = json.loads(
                            value) if value is not None else []
        return row

    def _load_cursor(self):
        if self._type == "sql":
            if self._defered_skip:
                self._sql += f" OFFSET {self._defered_skip}"
            if self._defered_limit:
                self._sql += f" LIMIT {self._defered_limit}"
            self._cursor = self._cursor_execute(self._sql, self._cursor_values)
        self._results = self._cursor.fetchall()
        if self._defered_sort:
            self._sort(self._defered_sort[0], self._defered_sort[1])
        self._idx = 0

        _ = DEBUG and log_debug(
            '\n\nSqlFindIterator | _load_cursor() |' +
            f'\nSQL: {self._sql}' +
            f'\nTable Structure: {self._table_structure}' +
            f'\nResults: {self._results}')

    def __iter__(self):
        if self._type == "cursor":
            self._results = self._cursor.fetchall()
            self._idx = 0
        return self

    def __next__(self):
        if self._type == "sql" and self._results is None:
            self._load_cursor()
        if self._results and self._idx < len(self._results):
            res = self._results[self._idx]
            self._idx += 1
            # Convert RealDictRow to dict
            row = dict(res)
            # Handle types if needed
            row = self._row_types_convertion(row)
            _ = DEBUG and log_debug(
                f"||| SqlFindIterator | __next__ | res: {row}")
            return fix_item_for_dump(row)
        raise StopIteration

    def _sort(self, key, direction):
        if self._results:
            self._results.sort(key=lambda x: x.get(
                key), reverse=(direction != "asc"))
        return self

    def sort(self, key, direction):
        # Sorting should ideally happen in the SQL query.
        # If we are here, we might need to sort in memory or this method
        # should have been called before executing the query.
        # For compatibility with the chainable API, we might just pass for now
        # or implement in-memory sort if results are already fetched.
        if self._type == "sql" and self._cursor is None:
            self._defered_sort = (key, direction)
            return self

        if self._results:
            self._results.sort(key=lambda x: x.get(
                key), reverse=(direction != "asc"))
        return self

    def skip(self, skip: int):
        # If the query has not been executed, defer the skip
        if self._type == "sql" and self._cursor is None:
            self._defered_skip = skip
            return self

        # If the query has been executed, skip in memory
        if self._results:
            self._results = self._results[skip:]
            self._idx = 0
        return self

    def limit(self, limit: int):
        # If the query has not been executed, defer the limit
        if self._type == "sql" and self._cursor is None:
            self._defered_limit = limit
            return self

        # If the query has been executed, limit in memory
        if self._results:
            self._results = self._results[:limit]
        return self


class SqlTable(SqlUtilities):
    """
    SQL Table abstraction
    """

    def __init__(self,
                 app_config,
                 connection,
                 table_name: str,
                 table_structure: Dict,
                 IteratorClass=None):
        self._app_config = app_config
        self._table_name = table_name
        self._db = connection
        self.db_uri = None
        self.db_name = None
        self.db_engine = None
        self.db_other_params = None
        self.inserted_id = None
        self.modified_count = 0
        self.deleted_count = 0
        self._table_structure = table_structure
        self.IteratorClass = IteratorClass
        self.get_db_config_data()

        # The $pull operation in update_one can be implemented by fetching the
        # row, filtering the array in Python, and then updating the entire
        # column. By the way this is not atomic and can lead to race conditions
        # where concurrent updates overwrite each other.
        # "self.atomic_pull = True" set to use database-native JSON functions
        # like jsonb_set or - in PostgreSQL, and JSON_REMOVE in MySQL.
        self.atomic_pull = True

        # When calling `self.run_query()` the SqlFindIterator fetches all
        # results into memory using cursor.fetchall(). For large tables, this
        # is highly inefficient and can lead to memory exhaustion.
        # "self.iterator_set_skip_limit = True" set the use of server-side
        # pagination (LIMIT/OFFSET) in the SQL query instead of in-memory
        # slicing in the iterator.
        self.iterator_set_skip_limit = True

    def fix_value_types(self, columns: List, values: List) -> List:
        """
        Fix value types
        """
        _ = DEBUG and log_debug(
            "SqlTable.fix_value_types:" +
            f"\ncolumns: {columns}" +
            f"\nvalues: {values}" +
            f"\ntable_structure: {self._table_structure}")
        for i, column in enumerate(columns):
            if column in self._table_structure:
                if self._table_structure[column] in [
                    "int",
                    "bigserial",
                    "integer",
                    "bigint",
                    "smallint",
                    "smallserial",
                    "serial",
                    "bigserial"
                ]:
                    if isinstance(values[i], list):
                        values[i] = [int(v) if v is not None and v !=
                                     "" else 0 for v in values[i]]
                    else:
                        if values[i] is None or values[i] == "":
                            values[i] = 0
                        values[i] = int(values[i])

                elif self._table_structure[column] in [
                    "float",
                    "numeric",
                    "real",
                    "double precision"
                ]:
                    if isinstance(values[i], list):
                        values[i] = [float(v) if v is not None and v !=
                                     "" else 0.0 for v in values[i]]
                    else:
                        if values[i] is None or values[i] == "":
                            values[i] = 0.0
                        values[i] = float(values[i])
                elif self._table_structure[column] in [
                    "bool",
                    "boolean"
                ]:
                    if isinstance(values[i], list):
                        values[i] = [bool(v) if v is not None and v !=
                                     "" else False for v in values[i]]
                    else:
                        if values[i] is None or values[i] == "":
                            values[i] = False
                        values[i] = bool(values[i])
        return values

    def _build_where_clause(
        self,
        query_params: Dict,
    ) -> Tuple[Union[str, List[Any], Dict[str, Any]], List[str], List[Any]]:
        """
        Build SQL WHERE clause from MongoDB-style query params
        """
        _ = DEBUG and log_debug(
            f"||| _build_where_clause | query_params: {query_params}")
        if not query_params:
            return "", [], []
        condition_glue = "OR" if "$or" in query_params else "AND"
        conditions, columns, values = \
            self._get_conditions_and_values(query_params)
        where_clause = \
            f" {condition_glue} ".join(conditions) if conditions else ""
        values = self.fix_value_types(columns, values)
        return where_clause, columns, values

    def find(self, query_params: Dict = None, projection: Dict = None):
        """
        Execute SELECT query
        """
        query_params = query_params or {}
        where_clause, columns, values = self._build_where_clause(query_params)
        fields = self.get_fields(projection)

        if self.iterator_set_skip_limit:
            sql = self.build_select_sql(
                table_name=self._table_name,
                fields=fields,
                where=where_clause,
                values=values,
            )
            return self.IteratorClass(
                sql, self._table_structure,
                cursor_execute=self.cursor_execute,
                cursor_values=values)

        cursor = self.run_query(
            table_name=self._table_name,
            fields=fields,
            where=where_clause,
            values=values,
        )
        return self.IteratorClass(cursor, self._table_structure)

    def find_one(self, query_params: Dict = None, projection: Dict = None):
        """
        Execute SELECT query and return first result
        """
        iterator = self.find(query_params, projection)
        # Execute query by starting iteration
        iterator.__iter__()
        try:
            return iterator.__next__()
        except StopIteration:
            return None

    def insert_one(self, item: Dict):
        """
        Execute INSERT query
        """
        _ = DEBUG and log_debug(f"SqlTable.insert_one: {item}")
        if "_id" not in item:
            item["_id"] = self.new_id()

        columns = list(item.keys())
        quoted_columns = [self._quote_identifier(c) for c in columns]
        values = self._prepare_values_for_sql(list(item.values()))
        values = self.fix_value_types(columns, values)
        placeholders = ["%s"] * len(values)

        quoted_table = self._quote_identifier(
            self._table_name, process_dot=True)
        sql = f"INSERT INTO {quoted_table} ({', '.join(quoted_columns)}) " + \
            f"VALUES ({', '.join(placeholders)})"

        cursor = self.get_cursor()
        _ = DEBUG and log_debug(
            f"SqlTable.insert_one: {sql} | values: {values}")

        try:
            cursor.execute(sql, values)
            self._db.commit()
            self.inserted_id = item["_id"]
        except Exception as e:
            self._db.rollback()
            log_error(f"SqlTable.insert_one error: {e}")
            raise e
        return self

    def array_fields_value(self, value: Any) -> str:
        """
        Prepare value for array fields
        """
        result = self._prepare_value_for_sql(value)
        _ = DEBUG and log_debug(f"SqlTable.array_fields_value: {result}")
        return result

    def array_fields_value_as_list(self, value: dict) -> list:
        """
        Prepare value for array fields
        """
        result = [value]
        if self.db_engine == "POSTGRES":
            result = [self._prepare_value_for_sql(value)]
        elif self.db_engine == "MYSQL":
            result = [v for v in value.values()]
        _ = DEBUG and log_debug(f"SqlTable.array_fields_value: {result}")
        return result

    def array_fields_management(self, col_name: str, operation: str,
                                value: Any):
        """
        Manage array type fields, for adding or removing elements operations
        """
        result = None

        if operation == "add":

            if self.db_engine == "POSTGRES":

                result = f"{self._quote_identifier(col_name)} = " + \
                    f"{self._quote_identifier(col_name)} || %s::jsonb"

            elif self.db_engine == "MYSQL":
                column_and_values = ", ".join([
                    f"'{key}', %s"
                    for key in value.keys()
                ])
                result = f"{self._quote_identifier(col_name)} = " + \
                    "JSON_ARRAY_APPEND(" + \
                    f"{self._quote_identifier(col_name)}, '$', " + \
                    f"JSON_OBJECT({column_and_values}))"

        elif operation == "remove":

            if self.db_engine == "POSTGRES":
                # Condition: (elem->>'{key}') <> %s
                where_contitions = " AND ".join([
                    (f"(elem->>'{key}') " +
                     self.null_comparison("<>", "%s", val))
                    for key, val in value.items()
                ])
                result = f"{self._quote_identifier(col_name)} = " + \
                    f"""COALESCE(
    (
        SELECT jsonb_agg(elem)
        FROM jsonb_array_elements({self._quote_identifier(col_name)}) AS elem
        WHERE {where_contitions}
    ),
    '[]'::jsonb  -- If all elements are filtered out, return an empty array
)
"""
            elif self.db_engine == "MYSQL":
                column_and_values = ",".join([
                    f"row_{key} VARCHAR(255) PATH '$.{key}'"
                    for key in value.keys()
                ])
                # Condition: jt.row_{key} = %s
                where_contitions = " AND ".join([
                    (f"jt.row_{key} " +
                     self.null_comparison("=", "%s", val))
                    for key, val in value.items()
                ])
                result = f"{self._quote_identifier(col_name)} = " + \
                    f"""JSON_REMOVE({self._quote_identifier(col_name)},
    (
        SELECT CONCAT('$[', jt.row_idx - 1, ']')
        FROM JSON_TABLE(
            {self._quote_identifier(col_name)},
            '$[*]' COLUMNS (
                {column_and_values},
                row_idx FOR ORDINALITY
            )
        ) AS jt
        WHERE {where_contitions}
        LIMIT 1
    )
)
"""
        elif operation == "$elemMatch":
            # Search an element in the array and returns True if
            # condition(s) are met

            if self.db_engine == "POSTGRES":
                # result = " AND ".join([
                #     f"{self._quote_identifier(col_name)} @> '[" + "{" +
                #     f'"{key}": %s' + "}]'"
                #     for key, val in value.items()
                # ])

                # Condition: obj->>'{key}' <> %s
                where_contitions = " AND ".join([
                    (f"obj->>'{key}' " +
                     self.null_comparison("=", "%s", val))
                    for key, val in value.items()
                ])
                result = "EXISTS (" + \
                    f"""SELECT 1
FROM jsonb_array_elements({self._quote_identifier(col_name)}) AS obj
WHERE {where_contitions}
)
"""

            elif self.db_engine == "MYSQL":
                result = "AND ".join([
                    f"JSON_CONTAINS({self._quote_identifier(col_name)}, "
                    + f"JSON_OBJECT('{key}', %s))"
                    for key, val in value.items()
                ])

        return result

    def update_one(self, query_params: Dict, update_data: Dict):
        """
        Execute UPDATE query
        """
        where, columns, where_values = self._build_where_clause(
            query_params)

        if not where:
            log_error("SqlTable.update_one error: No WHERE clause")
            return self

        set_clauses = []
        set_values = []

        # Handle $set
        if "$set" in update_data:
            for k, v in update_data["$set"].items():
                # Condition: k = %s
                val_prepared = self._prepare_value_for_sql(v)
                set_clauses.append(
                    f"{self._quote_identifier(k)} " +
                    self.null_comparison("=", "%s", val_prepared))
                set_values.append(val_prepared)
        else:
            # Direct update (replace) - might not be standard Mongo behavior
            # for update_one but handling generic case
            for k, v in update_data.items():
                if k not in [
                    "$set",
                    "$inc",
                    "$push",
                    "$addToSet",
                    "$pull",
                ]:
                    # Condition: k = %s
                    val_prepared = self._prepare_value_for_sql(v)
                    set_clauses.append(
                        f"{self._quote_identifier(k)} " +
                        self.null_comparison("=", "%s", val_prepared))
                    set_values.append(val_prepared)

                elif k == "$inc" or k == "$push" or k == "$addToSet":
                    # Add element(s) to array column
                    for k2, v2 in v.items():
                        set_clauses.append(
                            self.array_fields_management(k2, "add", v2))
                        set_values.extend(self.array_fields_value_as_list(v2))

                elif k == "$pull":
                    # Remove an element by its id from the array column
                    #
                    # For example:
                    #
                    # k = "$pull"
                    # v = {'array_name': {
                    #        'id_col_name_1': 'id_to_be_removed_1',
                    #                           .
                    #                           .
                    #        'id_col_name_N': 'id_to_be_removed_N'}}
                    #
                    if self.atomic_pull:

                        for k2, v2 in v.items():
                            # E.g.
                            # k2 = 'array_name'
                            # v2 = {'id_col_name_1': 'id_to_be_removed_1', ...}
                            set_clauses.append(
                                self.array_fields_management(k2, "remove", v2))
                            for val in v2.values():
                                set_values.append(self.array_fields_value(val))

                    else:
                        # Non-atomic pull operation...

                        # First retrieve the original content
                        fields = ", ".join([self._quote_identifier(k2)
                                            for k2 in v.keys()])
                        cursor = self.run_query(
                            table_name=self._table_name,
                            fields=fields,
                            where=where,
                            values=where_values,
                        )
                        iterator = self.IteratorClass(
                            cursor, self._table_structure)
                        _ = DEBUG and log_debug(
                            f"SqlTable.update_one: {iterator}")
                        array_column_values = list(iterator)[0]

                        for k2, v2 in v.items():
                            # Remove the element(s) by its id
                            filtered_array_elements = [
                                item for item in array_column_values[k2]
                                if item.get(list(v2.keys())[0]) !=
                                list(v2.values())[0]
                            ]
                            if not filtered_array_elements:
                                filtered_array_elements = []

                            # Finally add the array column update
                            # Condition: k = %s
                            val_prepared = self._prepare_value_for_sql(
                                filtered_array_elements)
                            set_clauses.append(
                                f"{self._quote_identifier(k2)} " +
                                self.null_comparison("=", "%s", val_prepared))
                            set_values.append(val_prepared)

        if not set_clauses:
            log_error("SqlTable.update_one error: No SET clauses")
            return self

        quoted_table = self._quote_identifier(
            self._table_name, process_dot=True)
        sql = f"UPDATE {quoted_table} SET {', '.join(set_clauses)}" \
            + f" WHERE {where}"
        values = set_values + where_values

        cursor = self.get_cursor()

        _ = DEBUG and log_debug(
            f"SqlTable.update_one: {sql} | values: {values}")

        try:
            cursor.execute(sql, values)
            self._db.commit()
            self.modified_count = cursor.rowcount
        except Exception as e:
            self._db.rollback()
            log_error(f"SqlTable.update_one error: {e}")
            raise e
        return self

    def replace_one(self, query_params: Dict, update_data: Dict):
        """
        Execute REPLACE query
        """
        return self.update_one(query_params, update_data)

    def delete_one(self, query_params: Dict):
        """
        Execute DELETE query
        """
        where_clause, columns, values = self._build_where_clause(query_params)

        # Safety check: don't delete everything if query is empty?
        # Mongo delete_one with empty query deletes first match.
        # SQL DELETE without WHERE deletes all.
        # We should probably enforce a limit or require WHERE.
        # For delete_one, we can use CTID or similar if we could find it
        # first, but standard SQL:
        #   DELETE FROM table WHERE ... AND ctid IN (SELECT ctid FROM table
        #   WHERE ... LIMIT 1)
        # For now, simple DELETE.

        if not where_clause:
            log_error("SqlTable.delete_one error: No WHERE clause")
            return self

        quoted_table = self._quote_identifier(
            self._table_name, process_dot=True)
        sql = f"DELETE FROM {quoted_table} WHERE {where_clause} LIMIT 1"

        cursor = self.get_cursor()
        if DEBUG:
            log_debug(f"SqlTable.delete_one: {sql} | values: {values}")

        try:
            cursor.execute(sql, values)
            self._db.commit()
            self.deleted_count = cursor.rowcount
        except Exception as e:
            self._db.rollback()
            log_error(f"SqlTable.delete_one error: {e}")
            raise e
        return self

    def count_documents(self, query_params: Dict) -> int:
        """
        Count documents matching query
        """
        where, columns, values = self._build_where_clause(query_params)
        fields = "COUNT(*) AS doc_count"
        cursor = self.run_query(
            table_name=self._table_name,
            fields=fields,
            where=where,
            values=values,
        )
        result = fix_item_for_dump(cursor.fetchone())
        _ = DEBUG and log_debug(
            f"SqlTable.count_documents: {result}")
        if isinstance(result, tuple):
            return result[0]
        if isinstance(result, dict):
            return result.get("doc_count", 0)
        return 0


class SqlService(SqlUtilities):
    """
    SQL Service class
    """

    def get_specific_db_connection(self, db_uri: str, db_name: str,
                                   other_params: Dict = None):
        """
        Returns the specific database connection object.

        Args:
            db_uri (str): The database URI.
            db_name (str): The database name.
            other_params (Dict, optional): Other parameters for the database
                connection.

        For example:
            import psycopg2
            return psycopg2.connect(f"{db_uri}/{db_name}", **other_params)

        Returns:
            object: The database connection object.
        """
        self.not_implemented("get_specific_db_connection")

    def get_db_connection(self):
        """
        Returns the database connection object.
        Sets the _db property and returns this class instance.
        """
        _ = DEBUG and log_debug(
            "SqlService connecting to"
            + f" {self.db_uri}/{self.db_name}")

        # For this database service self._db must be set before executing
        # create_table_name_propeties()
        self._db = self.get_specific_db_connection(
            self.db_uri, self.db_name, self.db_other_params)

        _ = DEBUG and log_debug(
            "SqlService connected to"
            + f" {self.db_uri}/{self.db_name}"
            + f"\n | self._db: {self._db}"
            + "\n | DB Connector OK...")

        self.create_table_name_propeties()
        return

    def create_table_name_propeties(self):
        """
        Create table name class propeties so tables can be retrieved
        as a subscript (like MongoDB tables) using the __getitem__() method.
        """
        self.TableClass = self.get_table_class()
        self.IteratorClass = self.get_iterator_class()
        table_list = self.list_collection_names()
        for table_name in table_list:
            _ = DEBUG and log_debug(
                "||| create_table_name_propeties"
                + f"\n>>--> Setting property: {table_name}")
            table_structure = self.table_structure(table_name)
            setattr(self, table_name, self.TableClass(
                self._app_config,
                self._db,
                table_name,
                table_structure,
                self.IteratorClass))

    def set_tables_and_structures(self):
        """
        Sets the tables and structures in the database.
        """
        try:
            cursor = self.run_query(
                table_name=self.info_schema_table_names()["columns"],
                fields="table_name, column_name, data_type",
            )
            resultset = cursor.fetchall()
            cursor.close()
        except Exception as e:
            log_error(
                f"SqlService.set_tables_and_structures error: {e}")
            raise e
        self.assign_tables_and_structures(resultset)

    # def list_collection_names(self) -> list:
    #     """
    #     Returns a list of table names
    #     """
    #     try:
    #         cursor = self.run_query(
    #             table_name=self.info_schema_table_names()["tables"],
    #             fields="table_name",
    #             where="table_schema = 'public'"
    #         )
    #         table_names = cursor.fetchall()
    #         cursor.close()
    #         _ = DEBUG and log_debug(
    #             "SqlService list_collection_names"
    #             + f"\n | table_names fetched: {table_names}")
    #     except Exception as e:
    #         log_error(
    #             f"SqlService list_collection_names.run_query error: {e}")
    #         raise e
    #     try:
    #         table_names = map(
    #             lambda table_name: table_name["table_name"], table_names)
    #         return table_names
    #     except Exception as e:
    #         log_error(f"SqlService list_collection_names.map error: {e}")
    #         raise e

    # def table_structure(self, table_name: str) -> dict:
    #     """
    #     Returns a dictionary with the table structure
    #     """
    #     try:
    #         cursor = self.run_query(
    #             table_name=self.info_schema_table_names()["columns"],
    #             fields="column_name, data_type",
    #             where=f"table_name = '{table_name}'",
    #         )
    #         table_structure = cursor.fetchall()
    #         cursor.close()
    #         # _ = DEBUG and log_debug(
    #         #     f"SqlService table_structure [1] | Table: {table_name}"
    #         #     + f"\n | table_structure fetched: {table_structure}")
    #     except Exception as e:
    #         log_error(f"SqlService table_structure error: {e}")
    #         raise e
    #     try:
    #         table_structure = {
    #             column["column_name"]: column["data_type"]
    #             for column in table_structure
    #         }
    #         # _ = DEBUG and log_debug(
    #         #     f"SqlService table_structure [2] | Table: {table_name}"
    #         #     + f"\n | table_structure fetched: {table_structure}")
    #         return table_structure
    #     except Exception as e:
    #         log_error(f"SqlService table_structure.map error: {e}")
    #         raise e

    def __getitem__(self, table_name):
        _ = DEBUG and log_debug(
            "SqlService __getitem__ : "
            f"SqlTable({table_name}, self._db)"
        )
        return getattr(self, table_name)

    def test_connection(self) -> str:
        try:
            # cur = self._db.cursor()
            # cur.execute("SELECT 1")
            # return dumps({"status": "ok", "result": cur.fetchone()})

            return dumps({"status": "ok", "result": self.run_query(
                table_name=self.info_schema_table_names()["tables"],
                fields="table_name",
                where=["table_schema = 'public'"],
            )})

        except Exception as e:
            return dumps({"status": "error", "message": str(e)})


class SqlServiceBuilder(DbAbstract):
    """
    Builder class for PostgreSQL.
    """

    def __init__(self, SqlServiceClass: SqlService):
        self._instance = None
        self._SqlServiceClass = SqlServiceClass

    def __call__(self, app_config, **_ignored):
        if not self._instance:
            self._instance = self._SqlServiceClass(app_config)
        return self._instance
