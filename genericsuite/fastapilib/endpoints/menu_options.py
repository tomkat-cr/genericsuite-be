"""
Menu options access
"""
from typing import Optional

from fastapi import APIRouter, Depends, Body
from pydantic import BaseModel

from genericsuite.util.framework_abs_layer import Response
from genericsuite.fastapilib.util.dependencies import (
    get_current_user,
    # build_request,
    get_default_fa_request,
)
from genericsuite.models.menu_options.menu_options import (
    menu_options_get as menu_options_get_model,
    menu_options_element as menu_options_element_model,
)


class MenuElementRequest(BaseModel):
    """ Menu element request """
    element: str


router = APIRouter()


@router.get('/')
async def menu_options_get(
    current_user: str = Depends(get_current_user),
) -> Response:
    """ Get authorized menu options """
    request, other_params = get_default_fa_request(current_user)
    return menu_options_get_model(request, other_params)


@router.post(
    '/element',
    tags=['element'],
)
async def menu_options_element(
    current_user: str = Depends(get_current_user),
    json_body: MenuElementRequest = Body(...),
) -> Response:
    """ Get menu element configuration """
    request, other_params = get_default_fa_request(current_user,
        json_body=json_body.model_dump())
    return menu_options_element_model(request, other_params)
