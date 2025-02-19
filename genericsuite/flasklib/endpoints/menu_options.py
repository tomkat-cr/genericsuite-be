"""
Menu options access
"""
from typing import Optional

from genericsuite.util.framework_abs_layer import Response

from genericsuite.util.jwt import (
    AuthorizedRequest
)
from genericsuite.flasklib.util.jwt import token_required
from genericsuite.flasklib.util.blueprint_one import BlueprintOne

from genericsuite.models.menu_options.menu_options import (
    menu_options_get as menu_options_get_model,
    menu_options_element as menu_options_element_model,
)

bp = BlueprintOne("menu_options", __name__, url_prefix='/menu_options')


@bp.route('', methods=['GET'])
@token_required
def menu_options_get(
    request: AuthorizedRequest,
    other_params: Optional[dict] = None
) -> Response:
    """ Get authorized menu options """
    return menu_options_get_model(request, bp, other_params)


@bp.route('/element', methods=['POST'])
@token_required
def menu_options_element(
    request: AuthorizedRequest,
    other_params: Optional[dict] = None
) -> Response:
    """ Get menu element configuration """
    return menu_options_element_model(request, bp, other_params)
