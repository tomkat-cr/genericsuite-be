"""
Security module
"""
from genericsuite.util.app_context import AppContext
from genericsuite.util.app_logger import log_debug
from genericsuite.util.generic_endpoint_helpers import GenericEndpointHelper
from genericsuite.util.utilities import (
    get_default_resultset, get_query_params, get_request_body
)

DEBUG = False


def get_user_groups(user_data: dict) -> list:
    """Get the user groups."""
    user_groups = []
    if "groups" in user_data:
        user_groups = user_data["groups"]
    if "superuser" in user_data and user_data["superuser"] == '1':
        user_groups.append('admin')
    user_groups.append('users')
    return user_groups


def get_user_authorized_menu(menu_data: list, user_data: dict) -> dict:
    """
    Get the authorized menu options.
    """
    menu_response = get_default_resultset()
    user_groups = get_user_groups(user_data)
    if DEBUG:
        log_debug(f'GAMO-1) user_data: {user_data}')
        log_debug(f'GAMO-2) user_groups: {user_groups}')
        # log_debug(f'GAMO-3) menu_data: {menu_data}')
    authorized_menu_options = authorize_menu_options(
        menu_data, user_groups
    )
    # if DEBUG:
    #     log_debug(f'GAMO-3) authorized_menu_options: {authorized_menu_options}')
    menu_response["resultset"] = authorized_menu_options
    return menu_response


def authorize_menu_options(menu_data: list, user_groups: list) -> list:
    """
    Authorize menu options based on user groups.

    Args:
        menu_data (list): The menu data to be authorized.
        user_groups (list): The groups of the current user.

    Returns:
        list: The authorized menu options.
    """
    authorized_menu_options = []
    for menu_option in menu_data:
        if "sub_menu_options" in menu_option:
            menu_option["sub_menu_options"] = \
                authorize_menu_options(
                    menu_option["sub_menu_options"], user_groups
                )
        if "sec_group" in menu_option:
            if menu_option["sec_group"] in user_groups:
                authorized_menu_options.append(menu_option)
        else:
            authorized_menu_options.append(menu_option)
    return authorized_menu_options


def get_authorized_menu_options(app_context: AppContext,
                                url_prefix: str = __name__
                                ) -> (dict, dict, list):
    """
    Get the authorized menu options.

    Args:
        app_context (AppContext): The application conntext
        url_prefix (str): The URL prefix.

    Returns:
        (dict, dict, list): A tuple containing the authorized menu options),
        the current user data, and the user groups list.
    """
    ep_helper = GenericEndpointHelper(
        app_context=app_context,
        json_file="app_main_menu",
        url_prefix=url_prefix,
        db_type="menu_options"
    )
    menu_response = get_default_resultset()
    user_groups = []
    user_data = app_context.get_user_data()
    if not user_data:
        menu_response = app_context.get_error_resultset()
        return menu_response, user_data, user_groups
    menu_data = ep_helper.generic_raw_json()
    if menu_data['error']:
        menu_response["error"] = True
        menu_response["error_message"] = menu_data['error_message']
        return menu_response, user_data, user_groups
    menu_response = get_user_authorized_menu(menu_data["resultset"],
                                             user_data)
    user_groups = get_user_groups(user_data)
    return menu_response, user_data, user_groups


def get_element_option(menu_data: list, element: str) -> dict:
    """
    Get the element option.
    """
    element_option = None
    for menu_option in menu_data:
        if "sub_menu_options" in menu_option:
            element_option = get_element_option(
                menu_option["sub_menu_options"], element
            )
            if element_option:
                if DEBUG:
                    log_debug(f'GEO-2) element: {element} Found!' +
                              f' -> {element_option}')
                return element_option
        if "element" in menu_option:
            if DEBUG:
                log_debug(f'GEO-1) element: {element} | ' +
                          f'menu_option.element: {menu_option["element"]}')
            if menu_option["element"] == element:
                element_option = menu_option
                if DEBUG:
                    log_debug(f'GEO-3) element: {element} Found!' +
                              f' -> {element_option}')
                return element_option
    return element_option


def get_option_access(app_context: AppContext, element: str) -> dict:
    """
    Get the user data from the app_context. Then, get the user groups from the
    user data, calling get_user_groups().
    Finally, call authorize_menu_options() with the menu data and user groups.
    Then verify in the authorized menu options if the option element
    is present.
    """
    oa_response = get_default_resultset()
    menu_response, _, user_groups = get_authorized_menu_options(app_context)
    if menu_response['error']:
        return menu_response
    menu_data = menu_response['resultset']
    element_option = get_element_option(menu_data, element)
    if not element_option:
        oa_response['error'] = True
        oa_response['error_message'] = \
            f'Element {element} not found [SOAV-010]'
    else:
        if 'sec_group' in element_option and \
           element_option['sec_group'] not in user_groups:
            oa_response['error'] = True
            oa_response['error_message'] = 'Access Denied [SOAV-020]'
    return oa_response


def verify_user_filter(app_context: AppContext) -> dict:
    """
    Verify the user filter in the endpoints that requires the user_id
    parameter.
    """
    request = app_context.get_request()
    vuf_response = get_default_resultset()
    if request.method.upper() in ['GET', 'DELETE']:
        query_params = get_query_params(request)
        user_id = query_params.get('user_id')
    else:  # request.method.upper() in ['POST', 'PUT']:
        form_data = get_request_body(request)
        user_id = form_data.get('user_id')
    if DEBUG:
        log_debug(f'VUF-1) VERIFY_USER_FILTER | user_id: {user_id}')
    if not user_id:
        vuf_response['error'] = True
        # Elements to build the Response()
        vuf_response['response'] = {
            "body": "user_id is required",
            "status_code": 400,
            "headers": {'Content-Type': 'text/plain'},
        }
    return vuf_response
