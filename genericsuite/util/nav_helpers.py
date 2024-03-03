"""
Navigation operation helpers
"""
import json
from genericsuite.util.app_logger import log_debug
from genericsuite.util.utilities import (
    get_query_params, get_standard_base_exception_msg
)

DEBUG = False


def get_total_pages(total_rows: int, limit: int) -> int:
    """
    Calculate the total number of pages based on the total number of rows
    and the limit per page.

    Args:
        total_rows (int): The total number of rows.
        limit (int): The limit of items per page.

    Returns:
        int: The total number of pages.
    """
    if limit == 0:
        return 1
    total_pages = int(total_rows / limit)
    if total_rows % limit > 0:
        total_pages += 1
    return total_pages


def get_navigation_params(request) -> (int, int, int):
    """
    Get navigation parameters from the request query parameters.

    Args:
        request: The request object.

    Returns:
        tuple: A tuple containing limit, skip, and page.
    """
    query_params = get_query_params(request)
    limit = query_params.get('limit')
    page = query_params.get('page')
    # skip = query_params.get('skip')
    limit = int((limit, 0)[limit is None])
    page = int((page, 1)[page is None])
    # skip = int((skip, 0)[skip is None])
    skip = (page * limit) - limit
    return (limit, skip, page)


def put_total_pages_from_resultset(
    limit: int,
    resultset: dict,
) -> dict:
    """
    Calculate total pages from resultset and limit.

    Args:
        limit (int): The limit of items per page.
        resultset (dict): The resultset containing the data.

    Returns:
        dict: The resultset with totalPages added.
    """
    if DEBUG:
        log_debug('>>--> *** put_total_pages_from_resultset ***' +
                  f'\nResultset: {resultset}' +
                  f'\nLimit: {limit}')

    if resultset['error']:
        return resultset
    resultset['totalPages'] = get_total_pages(
        len(json.loads(resultset['resultset'])), limit
    )
    if DEBUG:
        log_debug(f'NEW Resultset: {resultset}')
    return resultset


def put_total_pages_in_resultset(
    db_collection,
    listing_filter: dict,
    limit: int,
    resultset: dict,
    error_code: str,
):
    """
    Calculate total pages from resultset and limit.

    Args:
        db_collection: The collection from the database.
        listing_filter: The filter to apply to the collection.
        skip: The number of documents to skip.
        limit: The limit of items per page.
        resultset: The resultset containing the data.
        error_code: The error code to use in case of an exception.

    Returns:
        dict: The resultset with totalPages added.
    """
    if resultset['error']:
        return resultset
    count_docs = db_collection.count_documents(listing_filter)
    if DEBUG:
        log_debug('PUT_TOTAL_PAGES_IN_RESULTSET' +
                  f' | count_docs: {count_docs}')
    try:
        resultset['totalPages'] = get_total_pages(
            count_docs, limit
        )
    except BaseException as err:
        resultset['error_message'] = get_standard_base_exception_msg(
            err, error_code
        )
        resultset['error'] = True
    return resultset
