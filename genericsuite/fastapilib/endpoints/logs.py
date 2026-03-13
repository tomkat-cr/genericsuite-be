"""
Log server
"""
from fastapi import Depends, Body, Request as FaRequest

from genericsuite.util.framework_abs_layer import Response
from genericsuite.fastapilib.util.blueprint_one import BlueprintOne
from genericsuite.fastapilib.util.dependencies import (
    get_current_user,
    get_default_fa_request,
)
from genericsuite.models.logs.logs import (
    put_log,
    LogRequest,
)


router = BlueprintOne()


@router.post(
    '',
    tags=['logs'],
)
async def logs_creation(
    request: FaRequest,
    current_user: str = Depends(get_current_user),
    json_body: LogRequest = Body(...),
) -> Response:
    gs_request, other_params = get_default_fa_request(
        current_user,
        json_body=json_body.model_dump())
    router.set_current_request(request, gs_request)
    return put_log(
        request=gs_request, blueprint=router,
        other_params=other_params)
