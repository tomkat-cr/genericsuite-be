"""
Generic endpoint operations module
"""
from bson.json_util import dumps

# from chalice.app import Response
from genericsuite.util.framework_abs_layer import Response

from genericsuite.util.app_context import AppContext
from genericsuite.util.nav_helpers import get_navigation_params
from genericsuite.util.app_logger import log_debug
from genericsuite.util.utilities import (
    return_resultset_jsonified_or_exception,
    get_query_params,
    get_request_body,
    method_not_allowed,
    get_default_resultset,
    error_resultset,
)
from genericsuite.util.generic_db_helpers import GenericDbHelper

DEBUG = False


class GenericEndpointHelper:
    """
    Helper class for generic endpoint CRUD operations.
    """
    def __init__(
        self,
        app_context: AppContext,
        url_prefix: str,
        json_file: str,
        db_type: str = None,
    ):
        self.json_file = json_file
        self.app_context = app_context
        self.request = self.app_context.get_request()
        self.query_params = get_query_params(self.request)
        self.request_body = get_request_body(self.request)
        self.data = {}
        self.data["url_prefix"] = url_prefix
        self.dbo = GenericDbHelper(json_file=json_file,
                                   request=self.request,
                                   blueprint=app_context.get_blueprint(),
                                   db_type=db_type)
        if isinstance(self.dbo.cnf_db, list):
            self.data["title"] = f'{json_file}s'
            self.data["name"] = json_file
        else:
            self.data["title"] = self.dbo.cnf_db.get('title', f'{json_file}s')
            self.data["name"] = self.dbo.cnf_db.get('name', json_file)

    def get_comb_param(self):
        """
        Get the combinator parameter.
        """
        comb_param = self.query_params.get('comb', None)
        if comb_param:
            comb_param = "$or" if comb_param in ['o', 'or'] else "$and"
        return comb_param

    def get_like_param(self):
        """
        Get the like parameter.
        """
        like_param = self.query_params.get('like', '0')
        return like_param

    def get_like_query_params(self):
        """
        Get the like query parameters.
        """
        like_query_params = {
            k: v for k, v in self.query_params.items()
            if k not in ['page', 'limit', 'like', 'comb']
        }
        return like_query_params

    def generic_crud_main(self) -> Response:
        """
        Perform generic CRUD operations.
        """
        _ = DEBUG and \
            log_debug(f'ENTERING {self.data["url_prefix"]}_crud...' +
            f' | request.method: {self.request.method}' +
            f' | query_params: {self.query_params}'
            f' | request_body: {self.request_body}')

        if self.dbo.error_message:
            return error_resultset(self.dbo.error_message)

        row_id = self.query_params.get('id')
        like_param = self.get_like_param()
        comb_param = self.get_comb_param()

        additional_query_params = self.dbo.cnf_db.get('additional_query_params')

        (limit, skip, page) = get_navigation_params(self.request)

        _ = DEBUG and log_debug(f' | row_id: {row_id}' +
            f' | additional_query_params: {additional_query_params}' +
            f' | limit: {limit} | skip: {skip} | page: {page}' + 
            f' | like_param: {like_param} | comb_param: {comb_param}' + 
            f'\n | request_body: {self.request_body}')

        if self.request.method.upper() == 'POST':
            # Create
            _ = DEBUG and \
                log_debug(f'GCM-1.1) CREATE {self.data["name"]}...')
            result = self.dbo.create_row(self.request_body)
            _ = DEBUG and \
                log_debug(f'GCM-1.2) CREATE {self.data["name"]}' +
                f'\n | request_body: {self.request_body}' +
                f'\n | result: {result}')
        elif self.request.method.upper() == 'PUT':
            # Update
            _ = DEBUG and log_debug(f'GCM-2.1) UPDATE {self.data["name"]}...')
            options = {"update_item": self.query_params.get("update_item", "0")}
            result = self.dbo.update_row(record=self.request_body,
                                         options=options)
            _ = DEBUG and log_debug(f'GCM-2.2) UPDATE {self.data["name"]}' +
                f'\n | request_body: {self.request_body}' +
                f'\n | result: {result}')
        elif self.request.method.upper() == 'DELETE' and row_id is not None:
            # Delete
            _ = DEBUG and log_debug(f'GCM-3.1) DELETE {self.data["name"]}' +
                f' | row_id: {row_id}...')
            result = self.dbo.delete_row(row_id)
            _ = DEBUG and log_debug(f'GCM-3.2) DELETE {self.data["name"]}' +
                f' | row_id: {row_id}\n | result: {result}')
        elif row_id is not None:
            # Get one row by _id
            _ = DEBUG and log_debug(f'GCM-4.1) GET ROW {self.data["name"]}' +
                f' BY ID: {row_id}...')
            result = self.dbo.fetch_row(row_id)
            _ = DEBUG and log_debug(f'GCM-4.2) GET ROW {self.data["name"]}' +
                f' BY ID: {row_id}\n | result: {result}')
        elif like_param == "1":
            # Like Search
            _ = DEBUG and log_debug(f'GCM-5.1) LIKE SEARCH {self.data["name"]}' +
                f'\n | {like_query_params}...')
            like_query_params = self.get_like_query_params()
            result = self.dbo.fetch_list(
                skip=skip,
                limit=limit,
                like_query_params=like_query_params,
                combinator=comb_param
            )
            if not result['resultset']:
                result = error_resultset(
                    f'Error: {self.data["name"]} {like_query_params} ' + \
                    "doesn't exist", "GEM3")
            _ = DEBUG and log_debug(f'GCM-5.2) LIKE SEARCH {self.data["name"]}' +
                f'\n | {like_query_params}\n | result: {result}')
        elif additional_query_params is not None and \
             all(param in self.query_params
             for param in additional_query_params):
            # Get one row by additional_query_params
            _ = DEBUG and log_debug('GCM-6.1) SEARCH BY ATTRIBUTE' +
                f' {self.data["name"]} BY {param_name}: {param_value}' +
                '...')
            result = get_default_resultset()
            param_name = None
            param_value = None
            for key in additional_query_params:
                if not self.query_params.get(key):
                    continue
                param_name = key
                param_value = self.query_params[key]
                result = self.dbo.fetch_row_by_entryname_raw(
                    entry_name=param_name,
                    entry_value=param_value,
                )
                if not result['resultset']:
                    result = error_resultset(
                        f'ERROR: {self.data["name"]} {param_value} ' + \
                        "doesn't exist", "GEM1")
                else:
                    result['resultset'] = dumps(result['resultset'])
                break
            _ = DEBUG and log_debug('GCM-6.2) SEARCH BY ATTRIBUTE' +
                f' {self.data["name"]} BY {param_name}: {param_value}' +
                f'\n | result: {result}')
        else:
            # Fetch row list
            _ = DEBUG and log_debug(f'GCM-7.1) {self.data["name"]} list |' +
                f' skip: {skip}, limit: {limit}, page: {page}' +
                f'...')
            result = self.dbo.fetch_list(skip, limit, self.query_params)
            _ = DEBUG and log_debug(f'GCM-7.2) {self.data["name"]} list |' +
                f' skip: {skip}, limit: {limit}, page: {page}' +
                f'\n | result {result}')
        return return_resultset_jsonified_or_exception(result)

    def generic_raw_json(self) -> dict:
        """
        Get the raw JSON data.
        """
        result = get_default_resultset()
        _ = DEBUG and log_debug(f'GRJ-1) {self.json_file}')
        if self.dbo.error_message:
            result['error'] = True
            result['error_message'] = self.dbo.error_message
            return result
        result['resultset'] = self.dbo.cnf_db
        # _ = DEBUG and log_debug(f'GRJ-2) {self.json_file} | result: {result}')
        return result

    def generic_json_crud(self) -> Response:
        """
        Perform generic JSON CRUD operations.
        """
        result = self.generic_raw_json()
        return return_resultset_jsonified_or_exception(result)

    def generic_array_crud(self) -> Response:
        """
        Perform generic array CRUD operations.
        """
        array_parent_id_value = self.query_params.get(self.dbo.parent_key_field)
        (limit, skip, page) = get_navigation_params(self.request)
        array_child_id_value = self.query_params.get(self.dbo.array_field_key)
        filters = {}
        if array_child_id_value is not None:
            filters[self.dbo.array_field_key] = array_child_id_value
        like_param = self.get_like_param()
        comb_param = self.get_comb_param()
        result = None
        # Create
        if self.request.method.upper() == 'POST':
            _ = DEBUG and log_debug(f'>>> {self.data["name"]}_crud | ' +
                f'PUT request_body = {self.request_body}')
            result = self.dbo.add_array_item_to_row(self.request_body)
        # Delete
        elif self.request.method.upper() == 'DELETE':
            _ = DEBUG and log_debug(f'>>> {self.data["name"]}_crud | ' +
                f'DELETE request_body = {self.request_body}')
            result = self.dbo.remove_array_item_from_row(self.request_body)
        # Modify
        elif self.request.method.upper() == 'PUT':
            # When one element needs to be modified, first remove it,
            # then add it again
            _ = DEBUG and log_debug(f'>>> {self.data["name"]}_crud | ' +
                f'POST request_body = {self.request_body}')
            remove_operation_result = \
                self.dbo.remove_array_item_from_row(self.request_body)
            if remove_operation_result['error']:
                result = remove_operation_result
            else:
                result = self.dbo.add_array_item_to_row(self.request_body)
        # List
        elif self.request.method.upper() == 'GET':
            # Get the list (paginated) or one especific element
            like_query_params = (
                self.get_like_query_params() if like_param == "1" else {})
            _ = DEBUG and log_debug(f'>>> {self.data["name"]}_crud | GET' +
                f' array_parent_id_value: {array_parent_id_value}' +
                f'\n | filters: {filters}, skip: {skip}, limit: {limit}' +
                f', page: {page}, like_query_params: {like_query_params}' +
                f' comb_param: {comb_param}')
            result = self.dbo.fetch_array_rows(
                row_id=array_parent_id_value,
                filters=filters,
                skip=skip,
                limit=limit,
                like_query_params=like_query_params,
                combinator=comb_param
            )
        if not result:
            return method_not_allowed()
        return return_resultset_jsonified_or_exception(result)
