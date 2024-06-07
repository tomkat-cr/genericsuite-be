"""
Generic Database middleware to facilitate calls to GenericDbHelper
"""
from typing import List, Union, Optional

from genericsuite.util.app_logger import log_debug, log_error
from genericsuite.util.generic_db_helpers import GenericDbHelper
from genericsuite.util.app_context import AppContext

DEBUG = False


# Database generic operations


def fetch_all_from_db(
    app_context: AppContext,
    json_file: str,
    like_query_params: Optional[dict] = None,
    combinator: Optional[str] = None,
    order_param: Optional[str] = None,
) -> dict:
    """
    Fetches all items from the database table using the GenericDbHelper class.

    Args:
        json_file (str): The JSON file containing the database.
        like_query_params (dict): The query parameters to filter
        the items as SQL LIKE.
        combinator (str): condiition combinator for the filter.
        It could be $and, $or, $not. Defaults to $and

    Returns:
        List[dict]: The fetched items resultset.
    """
    dbo = GenericDbHelper(
        json_file=json_file,
        request=app_context.get_request(),
        blueprint=app_context.get_blueprint(),
    )
    result = dbo.fetch_list(
        skip=0,
        limit=0,
        like_query_params=like_query_params,
        combinator=combinator,
        order_param=order_param,
    )
    if result['error']:
        log_error(
            f'AI_FAFD-E1) ERROR: Fetch all from {json_file}' +
            ' | result: {result}')
    elif DEBUG:
        log_debug(f'AI_FAFD-1) Fetch all from {json_file} | result: {result}')
    return result


def get_item_from_db(
    app_context: AppContext,
    json_file: str,
    entry_name: str,
    entry_value: Union[str, int, float],
    user_id: str = None,
) -> dict:
    """
    Fetches an item from the database by an entry name (field/column).

    Args:
        json_file (str): The JSON file containing the database.
        entry_name (str): The name of the entry to fetch.
        entry_value (Union[str, int]): The value of the entry to fetch.

    Returns:
        dict: The fetched item resultset.
    """
    dbo = GenericDbHelper(
        json_file=json_file,
        request=app_context.get_request(),
        blueprint=app_context.get_blueprint(),
    )
    filters = {}
    if user_id:
        filters = {"user_id": user_id}
    get_by_pk = entry_name in ["id", "_id"]
    if get_by_pk:
        result = dbo.fetch_row_raw(entry_value)
    else:
        result = dbo.fetch_row_by_entryname_raw(
            entry_name=entry_name,
            entry_value=entry_value,
            filters=filters
        )
    if result['error']:
        log_error(
            f'AG_IFD-E1) ERROR get_item_from_db {json_file} |' +
            f' get_by_pk: {get_by_pk} | result: {result}')
    elif DEBUG:
        log_debug(
            f'AG_IFD-1) get_item_from_db {json_file} |' +
            f' get_by_pk: {get_by_pk} | result: {result}')
    return result


def modify_item_in_db(
    app_context: AppContext,
    json_file: str,
    data: dict
) -> dict:
    """Modify an Item (row) in the database

    Args:
        json_file (str): json file name with the table definition.
        entry_name (str): The name of the entry to modify.
        entry_value (Union[str, int, float]): The value of the entry to modify.
        data (dict): data to be updated

    Returns:
        dict: operation result as a resultset. See: update_row()
    """
    dbo = GenericDbHelper(
        json_file=json_file,
        request=app_context.get_request(),
        blueprint=app_context.get_blueprint(),
    )
    result = dbo.update_row(data)
    if result['error']:
        log_error(
            'AI_MIFD-E1) ERROR modify_item_in_db {json_file}' +
            f' | result: {result}')
    elif DEBUG:
        log_debug(f'AI_MIFD-1) modify_item_in_db {json_file}' +
                  f' | result: {result}')
    return result


def add_item_to_db(
    app_context: AppContext,
    json_file: str,
    data: dict,
    filters: dict = None,
) -> dict:
    """Add an Item (row) to the database

    Args:
        json_file (str): json file name with the table definition.
        data (dict): data to be registered

    Returns:
        dict: operation result as a resultset. See: create_row()
    """
    filters = {} if not filters else filters
    dbo = GenericDbHelper(
        json_file=json_file,
        request=app_context.get_request(),
        blueprint=app_context.get_blueprint(),
    )
    result = dbo.create_row(data, filters)
    if result['error']:
        log_error(
            f'AI_AITD-E1) ERROR add_item_to_db {json_file} | result: {result}')
    elif DEBUG:
        log_debug(f'AI_AITD-1) add_item_to_db {json_file} | result: {result}')
    return result


def fetch_all_from_db_array(
    app_context: AppContext,
    json_file: str,
    row_id: str,
    like_query_params: Optional[dict] = None,
    combinator: Optional[str] = None,
    order_param: str = None,
# ) -> List[dict]:
) -> dict:
    """
    Fetches all items in a row's array from the database table
    using the GenericDbHelper class.

    Args:
        json_file (str): The JSON file containing the database.
        row_id (str): parent row ID.
        like_query_params (dict): The query parameters to filter
        the items as SQL LIKE.
        combinator (str): condiition combinator for the filter.
        It could be $and, $or, $not. Defaults to $and

    Returns:
        List[dict]: The fetched items resultset.
    """
    dbo = GenericDbHelper(
        json_file=json_file,
        request=app_context.get_request(),
        blueprint=app_context.get_blueprint(),
    )
    result = dbo.fetch_array_rows(
        row_id=row_id,
        skip=0,
        limit=0,
        like_query_params=like_query_params,
        combinator=combinator,
        order_param=order_param,
    )
    if result['error']:
        log_error(
            f'AI_FAFDA-E1) ERROR Fetch all (array) from {json_file} |' +
            f' result: {result}')
    elif DEBUG:
        log_debug(f'AI_FAFDA-1) Fetch all (array) from {json_file} |' +
                  f' result: {result}')
    return result
