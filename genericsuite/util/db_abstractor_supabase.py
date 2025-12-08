"""
DbAbstractorSupabase: Database abstraction layer for Supabase
"""

from typing import Dict, List, Tuple, Union, Any
import re

# from genericsuite.config.config import Config
from genericsuite.util.db_abstractor_sql import (
    SqlUtilities,
    SqlFindIterator,
    SqlTable,
    SqlService,
    SqlServiceBuilder,
)
from genericsuite.util.app_logger import log_debug, log_error

DEBUG = False


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
            cursor = cursor.in_(col_name, value)
        elif operator == "NOT IN":
            cursor = cursor.not_in(col_name, value)
        elif operator == "LIKE":
            cursor = cursor.like(col_name, value)
        elif operator == "NOT LIKE":
            cursor = cursor.not_like(col_name, value)
        elif operator == "IS NULL":
            cursor = cursor.is_null(col_name)
        elif operator == "IS NOT NULL":
            cursor = cursor.is_not_null(col_name)
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
            for idx, col_name_op_val in enumerate(where):
                col_name, operator, placeholder = \
                    col_name_op_val.split(" ")
                value = values[idx] if isinstance(
                    values, list) else placeholder
            _ = DEBUG and log_debug(
                f"SupabaseUtilities.supabase_where | idx: {idx}"
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
        Execute a supabase query and return the cursor object.
        """
        supabase = self.get_cursor()
        if DEBUG:
            log_debug(
                f"SupabaseUtilities.run_query:"
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
                        f"SupabaseUtilities.run_query | List fields: {fields}")
                    cursor = cursor.select(fields)
                elif fields.startswith("COUNT"):
                    match = re.search(r"COUNT\((.*?)\)", fields)
                    count_argument = match.group(1) if match else "*"
                    cursor = cursor.select(count_argument, count="exact")
                    is_count = True
                    _ = DEBUG and log_debug(
                        "SupabaseUtilities.run_query"
                        f" | COUNT fields: {fields}"
                        f" | count_argument: {count_argument}")
                else:
                    _ = DEBUG and log_debug(
                        f"SupabaseUtilities.run_query | fields: {fields}")
                    cursor = cursor.select(fields)

            if where:
                _ = DEBUG and log_debug(
                    f"SupabaseUtilities.run_query | where: {where}")
                cursor = self.supabase_where(cursor, where, values)

            if order_by:
                _ = DEBUG and log_debug(
                    f"SupabaseUtilities.run_query | order_by: {order_by}")
                cursor = cursor.order_by(order_by)

            if limit:
                _ = DEBUG and log_debug(
                    f"SupabaseUtilities.run_query | limit: {limit}")
                cursor = cursor.limit(limit)

            if offset:
                _ = DEBUG and log_debug(
                    f"SupabaseUtilities.run_query | offset: {offset}")
                cursor = cursor.offset(offset)

            if DEBUG:
                log_debug(f"SupabaseUtilities.run_query.cursor: {cursor}")

            response = cursor.execute()
            if is_count:
                response.data = response.count

        except Exception as e:
            log_error(f"ERROR SupabaseUtilities.run_query: {e}")
            raise e

        if DEBUG:
            log_debug(
                f"SupabaseUtilities.run_query.data: {response}")
        if not response:
            raise Exception("SupabaseUtilities.run_query: No response")
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

        # func_to_call = rpc_name
        # if params:
        #     func_to_call += f" {', '.join(params)}"
        # _ = DEBUG and log_debug(
        #     f"SupabaseUtilities.run_rpc.func_to_call: {func_to_call}")
        # response = supabase.rpc(func_to_call).execute()
        _ = DEBUG and log_debug(
            f"SupabaseUtilities.run_rpc | rpc_name: {rpc_name}"
            f" | params: {params}")

        if params:
            response = supabase.rpc(rpc_name, params).execute()
        else:
            response = supabase.rpc(rpc_name).execute()
        if not response:
            raise Exception("SupabaseUtilities.run_rpc: No response.data")
        if DEBUG:
            log_debug(f"SupabaseUtilities.run_rpc.response: {response}")
        return response.data


class SupabaseFindIterator(SqlFindIterator):
    """
    Supabase find iterator
    """

    def __iter__(self):
        self._results = self._cursor.data
        self._idx = 0
        return self


class SupabaseTable(SqlTable, SupabaseUtilities):
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

        # Handle $set
        if "$set" in update_data:
            update_data = update_data["$set"].copy()

        supabase = self.get_cursor()

        _ = DEBUG and log_debug(
            f"SupabaseTable.update_one | table: {self._table_name}"
            f" | query_params: {query_params}"
            f" | where: {where}"
            f" | values: {values}"
            f" | update_data: {update_data}")

        try:
            # Add table name and UPDATE method (which must be called prior
            # to where)
            supabase = supabase.table(self._table_name).update(update_data)

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
        Count documents matching query
        """
        where, columns, values = self._build_where_clause(query_params)
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

    def list_collection_names(self) -> list:
        """
        Returns a list of table names.
        In Supabase, it must be done calling a stored procedure because
        it's not possible to access the "information_schema" schema.
        For GenericSuite, it's "get_tables".
        """
        _ = DEBUG and log_debug(
            ">> SupabaseService.list_collection_names")
        try:
            table_names = self.run_rpc("get_tables")
            return table_names

        except Exception as e:
            log_error(
                f"SupabaseService.list_collection_names.run_rpc error: {e}")
            return []

    def table_structure(self, table_name: str) -> dict:
        """
        Returns a dictionary with the table structure.
        In Supabase, it must be done calling a stored procedure because
        it's not possible to access the "information_schema" schema.
        For GenericSuite, it's "get_columns".
        """
        _ = DEBUG and log_debug(
            ">> SupabaseService.table_structure:"
            f" | table_name: {table_name}")
        try:
            return self.run_rpc(
                "get_columns",
                params={"tablename": table_name},
            )

        except Exception as e:
            log_error(f"SupabaseService.table_structure.run_rpc error: {e}")
            return {}


class SupabaseServiceBuilder(SqlServiceBuilder):
    """
    Builder class for Supabase.
    """

    def __init__(self):
        super().__init__(SupabaseService)
