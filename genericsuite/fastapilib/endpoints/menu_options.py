"""
Menu options access
"""
# from fastapi import APIRouter, Depends, Body
from fastapi import Depends, Body, Request as FaRequest
from pydantic import BaseModel

from genericsuite.util.framework_abs_layer import Response
from genericsuite.fastapilib.util.blueprint_one import BlueprintOne
from genericsuite.fastapilib.util.dependencies import (
    get_current_user,
    get_default_fa_request,
)
from genericsuite.models.menu_options.menu_options import (
    menu_options_get as menu_options_get_model,
    menu_options_element as menu_options_element_model,
)


class MenuElementRequest(BaseModel):
    """ Menu element request """
    element: str


# router = APIRouter()
router = BlueprintOne()


@router.get('')
async def menu_options_get(
    request: FaRequest,
    current_user: str = Depends(get_current_user),
) -> Response:
    """ Get authorized menu options """
    gs_request, other_params = get_default_fa_request(current_user)
    router.set_current_request(request, gs_request)
    return menu_options_get_model(request=gs_request, blueprint=router,
        other_params=other_params)


@router.post(
    '/element',
    tags=['element'],
)
async def menu_options_element(
    request: FaRequest,
    current_user: str = Depends(get_current_user),
    json_body: MenuElementRequest = Body(...),
) -> Response:
    """ Get menu element configuration """
    gs_request, other_params = get_default_fa_request(current_user,
        json_body=json_body.model_dump())
    router.set_current_request(request, gs_request)
    return menu_options_element_model(request=gs_request, blueprint=router,
        other_params=other_params)
