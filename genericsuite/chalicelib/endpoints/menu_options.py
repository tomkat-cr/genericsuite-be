"""
Menu options access
"""
from typing import Optional

# from chalice.app import Response
# from genericsuite.util.blueprint_one import BlueprintOne
from genericsuite.util.framework_abs_layer import Response, BlueprintOne

from genericsuite.util.jwt import (
    request_authentication,
    AuthorizedRequest
)

from genericsuite.models.menu_options.menu_options import (
    menu_options_get as menu_options_get_model,
    menu_options_element as menu_options_element_model,
)

bp = BlueprintOne(__name__)


@bp.route(
    '/',
    methods=['GET'],
    authorizor=request_authentication(),
)
def menu_options_get(
    request: AuthorizedRequest,
    other_params: Optional[dict] = None
) -> Response:
    """ Get authorized menu options """
    # return menu_options_get_model(request, other_params)
    return menu_options_get_model(request, bp, other_params)


@bp.route(
    '/element',
    methods=['POST'],
    authorizor=request_authentication(),
)
def menu_options_element(
    request: AuthorizedRequest,
    other_params: Optional[dict] = None
) -> Response:
    """ Get menu element configuration """
    # return menu_options_element_model(request, other_params)
    return menu_options_element_model(request, bp, other_params)
