"""
DbAbstractorSupabase: Database abstraction layer for Supabase
"""

from typing import Dict, List, Tuple, Union, Any, Callable
import re
from functools import lru_cache

from genericsuite.util.db_abstractor_sql import (
    SqlUtilities,
    SqlFindIterator,
    SqlTable,
    SqlService,
    SqlServiceBuilder,
)
from genericsuite.util.db_abstractor_elem_match import DbAbstractorElemMatch
from genericsuite.util.app_logger import log_debug, log_error

DEBUG = False
DETAILED_DEBUG = False


class SupabaseUtilities(SqlUtilities):
    """
    Supabase Utilities class
    """

    def get_cursor(self):
        """
        Return cursor object for the specific database connection.
        """
        _ = DEBUG and log_debug(">> SupabaseTable.get_cursor")
        import os
        from supabase import create_client, Client

        # url: str = Config().DB_CONFIG.get("app_db_uri")
        url: str = self.db_uri
        key: str = os.environ.get("SUPABASE_KEY")
        supabase: Client = create_client(url, key)
        return supabase

    def add_supabase_condition(
        self,
        cursor: Any,
        col_name: str,
        operator: str,
        value: Any
    ):
        """
        Add a condition to the cursor.

        Supabase filters reference:
        https://supabase.com/docs/reference/python/using-filters
        """
        if operator == "<>":
            cursor = cursor.neq(col_name, value)

        elif operator == ">":
            cursor = cursor.gt(col_name, value)

        elif operator == "<":
            cursor = cursor.lt(col_name, value)

        elif operator == ">=":
            cursor = cursor.gte(col_name, value)

        elif operator == "<=":
            cursor = cursor.lte(col_name, value)

        elif operator == "IN":
            cursor = cursor.in_(
                col_name,
                str(value).lstrip("[").rstrip("]").split(",")
            )

        elif operator == "NOT IN":
            cursor = cursor.not_.in_(
                col_name,
                str(value).lstrip("[").rstrip("]").split(",")
            )

        elif operator == "LIKE":
            cursor = cursor.ilike(
                str(col_name).lstrip("LOWER(").rstrip(")"),
                str(value).replace("*", "%")
            )

        elif operator == "NOT LIKE":
            cursor = cursor.not_.ilike(
                str(col_name).lstrip("LOWER(").rstrip(")"),
                str(value).replace("*", "%")
            )
        elif operator == "IS NULL":
            cursor = cursor.is_(col_name, "null")

        elif operator == "IS NOT NULL":
            cursor = cursor.not_.is_(col_name, "null")

        elif operator == "=":
            cursor = cursor.eq(col_name, value)
        else:
            cursor = cursor.eq(col_name, value)
        return cursor

    def supabase_where(
        self,
        cursor: Any,
        where: List[str],
        values: List[Any]
    ) -> Any:
        if isinstance(where, list):
            idx_val = 0
            for idx, col_name_op_val in enumerate(where):
                col_name, operator, placeholder = \
                    col_name_op_val.split(" ")

                # _ = DEBUG and
                log_debug(
                    f"SupabaseUtilities.supabase_where # 1"
                    f" | idx: {idx} | idx_val: {idx_val}"
                    f" | col_name_op_val: {col_name_op_val}"
                    f" | col_name: {col_name}"
                    f" | operator: {operator}"
                    f" | placeholder: {placeholder}")

                if 'IS NULL' in col_name_op_val:
                    operator = 'IS NULL'
                    value = None
                elif 'IS NOT NULL' in col_name_op_val:
                    operator = 'IS NOT NULL'
                    value = None
                else:
                    value = values[idx_val] if isinstance(
                        values, list) else placeholder
                    idx_val += 1
            # _ = DEBUG and
            log_debug(
                f"SupabaseUtilities.supabase_where # 2"
                f" | idx: {idx} | idx_val: {idx_val}"
                f" | col_name: {col_name}"
                f" | operator: {operator}"
                f" | placeholder: {placeholder}"
                f" | value: {value}")

            cursor = self.add_supabase_condition(
                cursor,
                col_name,
                operator,
                value)
        else:
            col_name, operator, placeholder = where.split(" ")
            value = values[0] if isinstance(
                values, list) else placeholder
            cursor = self.add_supabase_condition(
                cursor,
                col_name,
                operator,
                value)

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
        sql_dict = {
            "table_name": table_name,
            "fields": fields,
            "where": where,
            "values": values,
            "order_by": order_by,
            "limit": limit,
            "offset": offset,
        }

        _ = DEBUG and log_debug(
            "Supabase | SupabaseUtilities.run_query"
            + f"\n | sql: {sql_dict}"
            + f"\n | values: {values}")
        return self.cursor_execute(sql_dict, values)

    def cursor_execute(
        self,
        sql: dict,
        values: Union[List, Dict] = None,
    ):
        """
        Execute a raw SQL query statement and return the cursor object.
        """
        _ = DEBUG and log_debug(
            "Supabase | SupabaseUtilities.cursor_execute"
            + f"\n | sql: {sql}")

        table_name = sql.get("table_name")
        fields = sql.get("fields")
        where = sql.get("where")
        order_by = sql.get("order_by")
        limit = sql.get("limit")
        offset = sql.get("offset")

        supabase = self.get_cursor()
        if DEBUG:
            log_debug(
                f"SupabaseUtilities.cursor_execute:"
                f"\n| supabase.client: {supabase}"
                f"\n| table_name: {table_name}"
                f"\n| fields: {fields}"
                f"\n| where: {where}"
                f"\n| values: {values}"
                f"\n| order_by: {order_by}"
                f"\n| limit: {limit}"
                f"\n| offset: {offset}"
            )

        try:
            cursor = supabase

            schema_name = None
            if "." in table_name:
                schema_name = table_name.split(".")[0]
                table_name = table_name.split(".")[1]
                cursor = cursor.schema(schema_name)

            cursor = cursor.table(table_name)

            is_count = False
            if fields:
                if isinstance(fields, list):
                    fields = ",".join(fields)
                    _ = DEBUG and log_debug(
                        "SupabaseUtilities.cursor_execute"
                        f" | List fields: {fields}")
                    cursor = cursor.select(fields)
                elif fields.startswith("COUNT"):
                    match = re.search(r"COUNT\((.*?)\)", fields)
                    count_argument = match.group(1) if match else "*"
                    cursor = cursor.select(count_argument, count="exact")
                    is_count = True
                    _ = DEBUG and log_debug(
                        "SupabaseUtilities.cursor_execute"
                        f" | COUNT fields: {fields}"
                        f" | count_argument: {count_argument}")
                else:
                    _ = DEBUG and log_debug(
                        f"SupabaseUtilities.cursor_execute | fields: {fields}")
                    cursor = cursor.select(fields)

            if where:
                _ = DEBUG and log_debug(
                    f"SupabaseUtilities.cursor_execute | where: {where}")
                cursor = self.supabase_where(cursor, where, values)

            if order_by:
                _ = DEBUG and log_debug(
                    f"SupabaseUtilities.cursor_execute | order_by: {order_by}")
                cursor = cursor.order_by(order_by)

            if limit:
                _ = DEBUG and log_debug(
                    f"SupabaseUtilities.cursor_execute | limit: {limit}")
                cursor = cursor.limit(limit)

            if offset:
                _ = DEBUG and log_debug(
                    f"SupabaseUtilities.cursor_execute | offset: {offset}")
                cursor = cursor.offset(offset)

            if DEBUG:
                log_debug(f"SupabaseUtilities.cursor_execute.cursor: {cursor}")

            response = cursor.execute()
            if is_count:
                response.data = response.count

        except Exception as e:
            log_error(f"ERROR SupabaseUtilities.cursor_execute: {e}")
            raise e

        if DEBUG:
            log_debug(
                f"SupabaseUtilities.cursor_execute.data: {response}")
        if not response:
            raise Exception("SupabaseUtilities.cursor_execute: No response")
        return response

    def run_rpc(
        self,
        rpc_name: str,
        params: Union[List, Dict] = None,
    ):
        """
        Execute a raw SQL query and return the cursor object.
        """
        supabase = self.get_cursor()

        _ = DEBUG and log_debug(
            f"SupabaseUtilities.run_rpc | rpc_name: {rpc_name}"
            f" | params: {params}")

        if params:
            response = supabase.rpc(rpc_name, params).execute()
        else:
            response = supabase.rpc(rpc_name).execute()
        if not response:
            raise Exception("SupabaseUtilities.run_rpc: No response.data")
        if DETAILED_DEBUG:
            log_debug(f"SupabaseUtilities.run_rpc.response: {response}")
        return response.data


class SupabaseFindIterator(SqlFindIterator):
    """
    Supabase find iterator
    """

    def __init__(
        self,
        cursorOrSql: Any,
        table_structure: Dict = None,
        cursor_execute: Callable = None,
        cursor_values: Union[List, Dict] = None
    ):
        self._type = "sql" if isinstance(
            cursorOrSql, (dict, str)) else "cursor"
        self._cursor = cursorOrSql if self._type == "cursor" else None
        self._sql_dict = cursorOrSql if self._type == "sql" else None
        self._cursor_execute = cursor_execute
        self._cursor_values = cursor_values
        self._results = None
        self._idx = 0
        self._table_structure = table_structure
        self._defered_sort = None
        self._defered_skip = None
        self._defered_limit = None

    def _load_cursor(self):
        if self._type == "sql":
            self._cursor = self._cursor_execute(
                self._sql_dict, self._cursor_values)
        self._results = self._cursor.data
        if self._defered_sort:
            self._sort(self._defered_sort[0], self._defered_sort[1])
        self._idx = 0

        _ = DEBUG and log_debug(
            '\n\nSupabaseFindIterator | _load_cursor() |' +
            f'\nSQL: {self._sql_dict}' +
            f'\nValues: {self._cursor_values}' +
            f'\nTable Structure: {self._table_structure}' +
            f'\nCursor: {self._cursor}' +
            f'\nResults: {self._results}')

    def __iter__(self):
        if self._type == "cursor":

            _ = DEBUG and log_debug(
                '\n\nSupabaseFindIterator | __iter__() |' +
                f'\nSQL: {self._sql_dict}' +
                f'\nTable Structure: {self._table_structure}' +
                f'\nCursor: {self._cursor}')

            self._results = self._cursor.data
            self._idx = 0
        return self


class SupabaseTable(SqlTable, SupabaseUtilities, DbAbstractorElemMatch):
    """
    Supabase Table abstraction
    """

    def _build_where_clause(
        self,
        query_params: Dict,
    ) -> Tuple[Union[str, List[Any], Dict[str, Any]], List[str], List[Any]]:
        """
        Build SQL WHERE clause from MongoDB-style query params
        """
        if not query_params:
            return [], [], []
        conditions, columns, values = self._get_conditions_and_values(
            query_params)
        return conditions, columns, values

    def find(self, query_params: Dict = None, projection: Dict = None):
        """
        Execute SELECT query with $elemMatch support
        """
        query_params = query_params or {}

        cleaned_params, elem_match_conditions = self._extract_elem_match(
            query_params)

        where_clause, columns, values = self._build_where_clause(
            cleaned_params)
        fields = self.get_fields(projection)

        if self.iterator_run_queries:
            sql_dict = {
                "table_name": self._table_name,
                "fields": fields,
                "where": where_clause,
            }
            _ = DEBUG and log_debug(
                f"SupabaseUtilities.find | sql_dict: {sql_dict}")

            if elem_match_conditions:
                cursor = self.cursor_execute(sql_dict, values)
                filtered_data = self._filter_elem_match(
                    cursor.data, elem_match_conditions)
                cursor.data = filtered_data
                return self.IteratorClass(cursor, self._table_structure)

            return self.IteratorClass(
                sql_dict,
                self._table_structure,
                cursor_execute=self.cursor_execute,
                cursor_values=values
            )

        cursor = self.run_query(
            table_name=self._table_name,
            fields=fields,
            where=where_clause,
            values=values,
        )

        if elem_match_conditions:
            filtered_data = self._filter_elem_match(
                cursor.data, elem_match_conditions)
            cursor.data = filtered_data

        _ = DEBUG and log_debug(
            f"SupabaseUtilities.find | cursor: {cursor}")
        return self.IteratorClass(cursor, self._table_structure)

    def insert_one(self, item: Dict):
        """
        Execute INSERT query using Supabase client.
        """
        if "_id" not in item:
            item["_id"] = self.new_id()

        supabase = self.get_cursor()

        _ = DEBUG and log_debug(
            f"SupabaseTable.insert_one | table: {self._table_name}"
            f" | item: {item}")

        # Fix value types
        columns = list(item.keys())
        values = self.fix_value_types(columns, list(item.values()))
        new_item = dict(zip(columns, values))

        try:
            _ = DEBUG and log_debug(
                f"SupabaseTable.insert_one | new_item: {new_item}")

            response = supabase \
                .table(self._table_name) \
                .insert(new_item) \
                .execute()

            if response.data is None or len(response.data) == 0:
                raise Exception(
                    f"SupabaseTable.insert_one: No data returned on insert."
                    f" Response: {response}")

            self.inserted_id = response.data[0]["_id"]
            self.inserted_count = response.count

            _ = DEBUG and log_debug(
                f"SupabaseTable.insert_one | inserted_id: {self.inserted_id}"
                f" | response.data: {response.data}")

        except Exception as e:
            log_error(f"ERROR SupabaseTable.insert_one: {e}")
            raise e
        return self

    def update_one(self, query_params: Dict, update_data: Dict):
        """
        Execute UPDATE query
        """
        where, columns, values = self._build_where_clause(query_params)

        # Safety check: don't update everything if query is empty
        if not where:
            log_error("SupabaseTable.update_one error: No WHERE clause")
            return self

        operators = ["$set", "$inc", "$push", "$addToSet", "$pull"]
        has_operators = any(op in update_data for op in operators)

        final_update_data = {}

        if not has_operators:
            final_update_data = update_data.copy()
        else:
            # Handle each operator
            if "$set" in update_data:
                final_update_data.update(update_data["$set"])

            # Operators that require the current state
            state_requiring_operators = ["$inc", "$push", "$addToSet", "$pull"]
            needs_current_state = any(
                op in update_data for op in state_requiring_operators)

            if needs_current_state:
                # Fetch existing record
                # We only need the fields that are being modified by these
                # operators
                fields_to_fetch = []
                for op in state_requiring_operators:
                    if op in update_data:
                        fields_to_fetch.extend(update_data[op].keys())

                # Deduplicate
                fields_to_fetch = list(set(fields_to_fetch))

                existing_record = self.find_one(
                    query_params,
                    projection={f: 1 for f in fields_to_fetch}
                )

                if not existing_record:
                    # If record doesn't exist, we might want to log or
                    # handle it.
                    # MongoDB update_one doesn't insert unless upsert=True
                    # is passed (which isn't here)
                    log_error(
                        "SupabaseTable.update_one: " +
                        "Record not found for state-requiring operators")
                    return self

                if "$inc" in update_data:
                    for k, v in update_data["$inc"].items():
                        current_val = existing_record.get(k, 0) or 0
                        final_update_data[k] = current_val + v

                if "$push" in update_data:
                    for k, v in update_data["$push"].items():
                        current_array = existing_record.get(k, []) or []
                        if not isinstance(current_array, list):
                            current_array = []
                        current_array.append(v)
                        final_update_data[k] = current_array

                if "$addToSet" in update_data:
                    for k, v in update_data["$addToSet"].items():
                        current_array = existing_record.get(k, []) or []
                        if not isinstance(current_array, list):
                            current_array = []
                        if v not in current_array:
                            current_array.append(v)
                        final_update_data[k] = current_array

                if "$pull" in update_data:
                    for k, v in update_data["$pull"].items():
                        # v can be a value or a dict (for field-based pull)
                        current_array = existing_record.get(k, []) or []
                        if not isinstance(current_array, list):
                            current_array = []

                        if isinstance(v, dict):
                            # Field-based pull (match by specific key)
                            match_key = list(v.keys())[0]
                            match_val = v[match_key]
                            final_update_data[k] = [
                                item for item in current_array
                                if not (isinstance(item, dict) and
                                        item.get(match_key) == match_val)
                                and not (item == v)  # fallback
                            ]
                        else:
                            # Direct value pull
                            final_update_data[k] = [
                                item for item in current_array if item != v
                            ]

            # Collect any other fields that are NOT operators but were passed
            # directly
            for k, v in update_data.items():
                if k not in operators:
                    final_update_data[k] = v

        supabase = self.get_cursor()

        _ = DEBUG and log_debug(
            f"SupabaseTable.update_one | table: {self._table_name}"
            f" | query_params: {query_params}"
            f" | where: {where}"
            f" | values: {values}"
            f" | update_data: {final_update_data}")

        try:
            # Add table name and UPDATE method (which must be called prior
            # to where)
            supabase = supabase.table(self._table_name).update(
                final_update_data)

            # Add WHERE clause condition
            supabase = self.supabase_where(supabase, where, values)

            # Execute UPDATE query
            response = supabase.execute()

            if response.data is None or len(response.data) == 0:
                raise Exception(
                    f"SupabaseTable.update_one: No data returned on update."
                    f" Response: {response}")

            self.modified_count = response.count

            _ = DEBUG and log_debug(
                "SupabaseTable.update_one"
                f" | modified_count: {self.modified_count}"
                f" | response.data: {response.data}"
                f" | response.count: {response.count}")

        except Exception as e:
            log_error(f"ERROR SupabaseTable.update_one: {e}")
            raise e
        return self

    def delete_one(self, query_params: Dict):
        """
        Execute DELETE query
        """
        where, columns, values = self._build_where_clause(query_params)

        # Safety check: don't delete everything if query is empty
        if not where:
            log_error("SupabaseTable.delete_one error: No WHERE clause")
            return self

        supabase = self.get_cursor()

        _ = DEBUG and log_debug(
            "SupabaseTable.delete_one"
            f" | where: {where}"
            f" | values: {values}")

        try:
            # Add table name and DELETE method (which must be called prior
            # to where)
            supabase = supabase.table(self._table_name).delete()

            # Add WHERE clause condition
            supabase = self.supabase_where(supabase, where, values)

            # Execute DELETE query
            response = supabase.execute()

            if response.data is None or len(response.data) == 0:
                raise Exception(
                    f"SupabaseTable.delete_one: No data returned on delete."
                    f" Response: {response}")

            self.deleted_count = response.count

            _ = DEBUG and log_debug(
                "SupabaseTable.delete_one"
                f" | deleted_count: {self.deleted_count}"
                f" | response.data: {response.data}"
                f" | response.count: {response.count}")

        except Exception as e:
            log_error(f"ERROR SupabaseTable.delete_one: {e}")
            raise e
        return self

    def count_documents(self, query_params: Dict) -> int:
        """
        Count documents matching query with $elemMatch support
        """
        cleaned_params, elem_match_conditions = self._extract_elem_match(
            query_params)

        if not elem_match_conditions:
            where, columns, values = self._build_where_clause(cleaned_params)
            fields = "COUNT(*)"
            cursor = self.run_query(
                table_name=self._table_name,
                fields=fields,
                where=where,
                values=values,
            )
            result = cursor.data
            if DEBUG:
                log_debug(f"SupabaseTable.count_documents: {result}")
            return result if result else 0

        where, columns, values = self._build_where_clause(cleaned_params)
        fields = "*"
        cursor = self.run_query(
            table_name=self._table_name,
            fields=fields,
            where=where,
            values=values,
        )

        filtered_data = self._filter_elem_match(
            cursor.data, elem_match_conditions)
        count = len(filtered_data) if isinstance(filtered_data, list) else \
            (1 if filtered_data else 0)

        if DEBUG:
            log_debug(
                f"SupabaseTable.count_documents (with $elemMatch): {count}")
        return count


class SupabaseService(SqlService, SupabaseUtilities):
    """
    Supabase Service class
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

        Returns:
            object: The database connection object.
        """
        _ = DEBUG and log_debug(
            ">> SupabaseService.get_specific_db_connection")
        supabase = self.get_cursor()
        return supabase

    def get_table_class(self):
        """
        Returns the table class.

        Returns:
            The table class.
        """
        return SupabaseTable

    def get_iterator_class(self):
        """
        Returns the iterator class.

        Returns:
            The iterator class.
        """
        return SupabaseFindIterator

    @lru_cache(maxsize=32)
    def set_tables_and_structures(self):
        """
        Sets the tables and structures in the database.
        """
        try:
            resultset = self.run_rpc(
                "get_columns",
                # params={"tablename": table_name},
            )
        except Exception as e:
            log_error(
                f"SupabaseService.table_structure.run_rpc error: {e}")
            raise e

        self.assign_tables_and_structures(resultset)

    @lru_cache(maxsize=32)
    def set_primary_keys(self):
        """
        Sets the tables and structures in the database.
        """
        try:
            resultset = self.run_rpc(
                "get_primary_keys",
                # params={"tablename": table_name},
            )
        except Exception as e:
            log_error(
                f"SupabaseService.set_primary_keys.run_rpc error: {e}")
            raise e

        self.assign_primary_keys(resultset)

    # def list_collection_names(self) -> list:
    #     """
    #     Returns a list of table names.
    #     In Supabase, it must be done calling a stored procedure because
    #     it's not possible to access the "information_schema" schema.
    #     For GenericSuite, it's "get_tables".
    #     """
    #     _ = DEBUG and log_debug(
    #         ">> SupabaseService.list_collection_names")
    #     if self.tables is None:
    #         self.set_tables_and_structures()
    #     return self.tables

    #     # try:
    #     #     table_names = self.run_rpc("get_tables")
    #     #     return table_names

    #     # except Exception as e:
    #     #     log_error("SupabaseService" +
    #     #         f".list_collection_names.run_rpc error: {e}")
    #     #     return []

    # def table_structure(self, table_name: str) -> dict:
    #     """
    #     Returns a dictionary with the table structure.
    #     In Supabase, it must be done calling a stored procedure because
    #     it's not possible to access the "information_schema" schema.
    #     For GenericSuite, it's "get_columns".
    #     """
    #     _ = DEBUG and log_debug(
    #         ">> SupabaseService.table_structure:"
    #         f" | table_name: {table_name}")
    #     if self.structures is None:
    #         self.set_tables_and_structures()
    #     return self.structures[table_name]


class SupabaseServiceBuilder(SqlServiceBuilder):
    """
    Builder class for Supabase.
    """

    def __init__(self):
        super().__init__(SupabaseService)
