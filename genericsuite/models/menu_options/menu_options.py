"""
Menu options access
"""
from typing import Optional

# from chalice.app import Response
from genericsuite.util.framework_abs_layer import Response

# from genericsuite.util.blueprint_one import BlueprintOne
# from genericsuite.util.jwt import (
#     request_authentication,
#     AuthorizedRequest
# )

from genericsuite.util.jwt import (
    AuthorizedRequest
)
from genericsuite.util.security import (
    get_authorized_menu_options,
    get_option_access,
)
from genericsuite.util.utilities import (
    get_request_body,
    return_resultset_jsonified_or_exception,
    get_default_resultset,
)
from genericsuite.config.config_from_db import app_context_and_set_env


# bp = BlueprintOne(__name__)


# @bp.route(
#     '/',
#     methods=['GET'],
#     authorizor=request_authentication(),
# )
def menu_options_get(
    request: AuthorizedRequest,
    other_params: Optional[dict] = None
) -> Response:
    """ Get authorized menu options """
    if other_params is None:
        other_params = {}
    # Set environment variables from the database configurations.
    app_context = app_context_and_set_env(request)
    if app_context.has_error():
        return return_resultset_jsonified_or_exception(
            app_context.get_error_resultset()
        )
    # Get authorized menu options
    menu_response, _, _ = get_authorized_menu_options(
        app_context=app_context, url_prefix=__name__
    )
    return return_resultset_jsonified_or_exception(
        menu_response
    )


# @bp.route(
#     '/element',
#     methods=['POST'],
#     authorizor=request_authentication(),
# )
def menu_options_element(
    request: AuthorizedRequest,
    other_params: Optional[dict] = None
) -> Response:
    """ Get menu element configuration """
    if other_params is None:
        other_params = {}
    # Set environment variables from the database configurations.
    app_context = app_context_and_set_env(request)
    if app_context.has_error():
        return return_resultset_jsonified_or_exception(
            app_context.get_error_resultset()
        )
    # Read parameters
    params = get_request_body(request)
    element = params.get('element')
    oa_response = get_default_resultset()
    if element is None:
        oa_response['error'] = True
        oa_response['error_message'] = "'element' parameter must" + \
            " be specified [MOEEP-010]"
        return return_resultset_jsonified_or_exception(
            oa_response, 403
        )
    # Get menu element configuration
    oa_response = get_option_access(app_context, element)
    if oa_response['error']:
        # Access denied
        return return_resultset_jsonified_or_exception(
            oa_response, 401
        )
    # Access granted
    oa_response['response'] = True
    return return_resultset_jsonified_or_exception(oa_response)
