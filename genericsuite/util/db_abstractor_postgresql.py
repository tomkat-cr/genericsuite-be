"""
DbAbstractorPostgresql: Database abstraction layer for PostgreSQL
"""

from typing import List, Dict, Any, Tuple
import json

from bson.json_util import dumps, ObjectId

from genericsuite.util.db_abstractor_super import DbAbstract
from genericsuite.util.app_logger import log_debug, log_error

DEBUG = True


class PostgresqlUtilities:
    """
    PostgreSQL Utilities class
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

    def _get_sql_operator(self, mongo_op: str) -> str:
        """
        Map MongoDB operators to SQL operators
        """
        mapping = {
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
        return mapping.get(mongo_op, "=")

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
        return json.dumps(value) if isinstance(value, (list, dict)) else value

    def _prepare_values_for_sql(self, values: List[Any]) -> List[Any]:
        """
        Prepare values for a SQL statement
        """
        return [self._prepare_value_for_sql(value) for value in values]

    def _build_where_clause(self, query_params: Dict) -> Tuple[str, List[Any]]:
        """
        Build SQL WHERE clause from MongoDB-style query params
        """
        if not query_params:
            return "", []

        conditions = []
        values = []

        def special_case_handling(col_name: str, op: str, op_val: Any):
            """
            Special case handling for $regex, $and, $or, $in, $nin
            """
            _ = DEBUG and log_debug(
                f"||| special_case_handling | op: {op} "
                f"| op_val: {op_val} | col_name: {col_name}")
            if op == "$regex":
                # Simple regex mapping to LIKE or ~
                # Assuming simple contains for now as per DynamoDB impl
                conditions.append(f"{col_name} LIKE %s")
                # Very basic regex support
                values.append(f"%{op_val}%")
            elif op in ["$and", "$or"]:
                # Handle $and and $or
                sub_conditions = []
                for sub_op, sub_op_val in op_val.items():
                    sub_conditions.append(
                        f"{col_name} "
                        f"{self._get_sql_operator(sub_op)} %s")
                    values.append(sub_op_val)
                conditions.append(
                    f" {self._get_sql_operator(op)} ".join(
                        sub_conditions))
            elif op in ["$in", "$nin"]:
                placeholders = ", ".join(["%s"] * len(op_val))
                sql_op = self._get_sql_operator(op)
                conditions.append(
                    f"{col_name} {sql_op} ({placeholders})")
                values.extend(op_val)
            else:
                sql_op = self._get_sql_operator(op)
                conditions.append(f"{col_name} {sql_op} %s")
                values.append(op_val)

        for key, value in query_params.items():
            # Handle _id mapping to id if necessary, or keep as _id if column
            # exists.
            # For now assuming column name is _id based on DynamoDB/Mongo usage
            col_name = key

            _ = DEBUG and log_debug(
                f"||| _build_where_clause [1] | col_name: {col_name} "
                f"| value: {value}")

            if isinstance(value, list):
                for item in value:
                    op = col_name
                    for col_name, op_val in item.items():
                        special_case_handling(col_name, op, op_val)
            # elif isinstance(value, dict):
            #     for op, op_val in value.items():
            #         special_case_handling(col_name, op, op_val)
            else:
                conditions.append(f"{col_name} = %s")
                values.append(self._normalize_objectid(value))

        where_clause = " WHERE " + \
            " AND ".join(conditions) if conditions else ""
        return where_clause, values


class PostgresqlFindIterator:
    """
    PostgreSQL find iterator
    """

    def __init__(self, cursor):
        self._cursor = cursor
        self._results = None
        self._idx = 0

    def __iter__(self):
        self._results = self._cursor.fetchall()
        self._idx = 0
        return self

    def __next__(self):
        if self._results and self._idx < len(self._results):
            res = self._results[self._idx]
            self._idx += 1
            # Convert RealDictRow to dict and handle types if needed
            _ = DEBUG and log_debug(
                f"||| PostgresqlFindIterator | __next__ | res: {dict(res)}")
            return dict(res)
        raise StopIteration

    def sort(self, key, direction):
        # Sorting should ideally happen in the SQL query.
        # If we are here, we might need to sort in memory or this method
        # should have been called before executing the query.
        # For compatibility with the chainable API, we might just pass for now
        # or implement in-memory sort if results are already fetched.
        if self._results:
            self._results.sort(key=lambda x: x.get(
                key), reverse=(direction != "asc"))
        return self

    def skip(self, skip):
        # In-memory skip if query already executed
        if self._results:
            self._results = self._results[skip:]
            self._idx = 0
        return self

    def limit(self, limit):
        # In-memory limit
        if self._results:
            self._results = self._results[:limit]
        return self


class PostgresqlTable(PostgresqlUtilities):
    """
    PostgreSQL Table abstraction
    """

    def __init__(self, table_name: str, connection):
        self._table_name = table_name
        self._conn = connection
        self.inserted_id = None
        self.modified_count = 0
        self.deleted_count = 0

    def find(self, query_params: Dict = None, projection: Dict = None):
        """
        Execute SELECT query
        """
        from psycopg2.extras import RealDictCursor

        query_params = query_params or {}
        where_clause, values = self._build_where_clause(query_params)

        # Projection support (basic)
        fields = "*"
        if projection:
            # Filter fields with value 1
            included = [k for k, v in projection.items() if v == 1]
            if included:
                fields = ", ".join(included)

        sql = f"SELECT {fields} FROM {self._table_name}{where_clause}"

        if DEBUG:
            log_debug(f"PostgresqlTable.find: {sql} | values: {values}")

        cursor = self._conn.cursor(cursor_factory=RealDictCursor)
        # cursor = self._conn.cursor()
        if DEBUG:
            log_debug(f"PostgresqlTable.find | cursor: {cursor}")

        cursor.execute(sql, values)
        # cursor.execute(sql, tuple(values))
        if DEBUG:
            log_debug(
                "PostgresqlTable.find | return: "
                f"{PostgresqlFindIterator(cursor)}"
            )
        return PostgresqlFindIterator(cursor)

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
        if "_id" not in item:
            item["_id"] = self.new_id()

        columns = list(item.keys())
        values = self._prepare_values_for_sql(list(item.values()))
        placeholders = ["%s"] * len(values)

        sql = f"INSERT INTO {self._table_name} ({', '.join(columns)}) " + \
            f"VALUES ({', '.join(placeholders)})"

        cursor = self._conn.cursor()
        if DEBUG:
            log_debug(f"PostgresqlTable.insert_one: {sql} | values: {values}")

        try:
            cursor.execute(sql, values)
            self._conn.commit()
            self.inserted_id = item["_id"]
        except Exception as e:
            self._conn.rollback()
            log_error(f"PostgresqlTable.insert_one error: {e}")
            raise e
        return self

    def update_one(self, query_params: Dict, update_data: Dict):
        """
        Execute UPDATE query
        """
        where_clause, where_values = self._build_where_clause(query_params)

        set_clauses = []
        set_values = []

        # Handle $set
        if "$set" in update_data:
            for k, v in update_data["$set"].items():
                set_clauses.append(f"{k} = %s")
                set_values.append(self._prepare_value_for_sql(v))
        else:
            # Direct update (replace) - might not be standard Mongo behavior
            # for update_one but handling generic case
            for k, v in update_data.items():
                if k not in [
                    "$set",
                    "$inc",
                    "$push",
                    "$pull",
                ]:  # Ignore other operators for now
                    set_clauses.append(f"{k} = %s")
                    set_values.append(self._prepare_value_for_sql(v))

        if not set_clauses:
            return self

        sql = f"UPDATE {self._table_name} SET {', '.join(set_clauses)}" + \
            f"{where_clause}"
        values = set_values + where_values

        cursor = self._conn.cursor()
        if DEBUG:
            log_debug(f"PostgresqlTable.update_one: {sql} | values: {values}")

        try:
            cursor.execute(sql, values)
            self._conn.commit()
            self.modified_count = cursor.rowcount
        except Exception as e:
            self._conn.rollback()
            log_error(f"PostgresqlTable.update_one error: {e}")
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
        where_clause, values = self._build_where_clause(query_params)

        # Safety check: don't delete everything if query is empty?
        # Mongo delete_one with empty query deletes first match.
        # SQL DELETE without WHERE deletes all.
        # We should probably enforce a limit or require WHERE.
        # For delete_one, we can use CTID or similar if we could find it
        # first, but standard SQL:
        #   DELETE FROM table WHERE ... AND ctid IN (SELECT ctid FROM table
        #   WHERE ... LIMIT 1)
        # For now, simple DELETE.

        sql = f"DELETE FROM {self._table_name}{where_clause}"

        cursor = self._conn.cursor()
        if DEBUG:
            log_debug(f"PostgresqlTable.delete_one: {sql} | values: {values}")

        try:
            cursor.execute(sql, values)
            self._conn.commit()
            self.deleted_count = cursor.rowcount
        except Exception as e:
            self._conn.rollback()
            log_error(f"PostgresqlTable.delete_one error: {e}")
            raise e
        return self

    def count_documents(self, query_params: Dict) -> int:
        """
        Count documents matching query
        """
        where_clause, values = self._build_where_clause(query_params)
        sql = f"SELECT COUNT(*) FROM {self._table_name}{where_clause}"

        cursor = self._conn.cursor()
        cursor.execute(sql, values)
        result = cursor.fetchone()
        return result[0] if result else 0


class PostgresqlService(DbAbstract):
    """
    PostgreSQL Service class
    """

    def get_db_connection(self):
        """
        Returns the database connection object.
        """
        import psycopg2

        db_uri = self._app_config.DB_CONFIG.get("app_db_uri")
        db_name = self._app_config.DB_CONFIG.get("app_db_name")

        # Separate elements from URI
        # Format: postgresql://user:pass@localhost:5432
        # db_uri_raw = db_uri.replace("postgresql://", "")
        # db_user = db_uri_raw.split("@")[0].split(":")[0]
        # db_pass = db_uri_raw.split("@")[0].split(":")[1]
        # db_host = db_uri_raw.split("@")[1].split(":")[0]
        # db_port = db_uri_raw.split("@")[1].split(":")[1]

        if DEBUG:
            log_debug("PostgresqlService connecting to"
                      + f" {db_uri}/{db_name}")

        self._db = psycopg2.connect(f"{db_uri}/{db_name}")
        # self._db = psycopg2.connect(
        #     host=db_host,
        #     port=db_port,
        #     user=db_user,
        #     password=db_pass,
        #     database=db_name,
        # )

        if DEBUG:
            log_debug("PostgresqlService connected to"
                      + f" {db_uri}/{db_name}")

        self.create_table_name_propeties()
        return self

    def create_table_name_propeties(self):
        """
        Create table name class propeties so tables can be retrieved
        as a subscript (like MongoDB tables) using the __getitem__() method.
        """
        table_list = self.list_collection_names()
        for table_name in table_list:
            if DEBUG:
                log_debug(
                    "||| create_table_name_propeties"
                    + f"\n>>--> Setting property: {table_name}"
                )
            setattr(self, table_name, PostgresqlTable(table_name, self._db))

    def list_collection_names(self):
        """
        Returns a list with the Postgres table names
        """
        try:
            # table_names = map(
            #     lambda table_name: table_name[0],
            #     self._db.cursor()
            #         .execute(
            #             "SELECT table_name FROM information_schema.tables"
            #             " WHERE table_schema='public';"
            #     )
            #     .fetchall(),
            # )
            table_names = []
            cursor = self._db.cursor()
            cursor.execute(
                "SELECT table_name FROM information_schema.tables"
                " WHERE table_schema='public';"
            )
            table_names = cursor.fetchall()
            table_names = map(lambda table_name: table_name[0], table_names)
            return table_names
        except Exception as e:
            log_error(f"PostgresqlService list_collection_names error: {e}")
            return []

    def __getitem__(self, table_name):
        if DEBUG:
            log_debug(
                "PostgresqlService __getitem__ : "
                f"PostgresqlTable({table_name}, self._db)"
            )
        return getattr(self, table_name)

    def test_connection(self) -> str:
        try:
            cur = self._db.cursor()
            cur.execute("SELECT 1")
            return dumps({"status": "ok", "result": cur.fetchone()})
        except Exception as e:
            return dumps({"status": "error", "message": str(e)})


class PostgresqlServiceBuilder(DbAbstract):
    """
    Builder class for PostgreSQL.
    """

    def __init__(self):
        self._instance = None

    def __call__(self, app_config, **_ignored):
        if not self._instance:
            self._instance = PostgresqlService(app_config)
        return self._instance
