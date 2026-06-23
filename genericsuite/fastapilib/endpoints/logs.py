"""
Log server
"""
from fastapi import Body, Request

from genericsuite.util.framework_abs_layer import Response
from genericsuite.fastapilib.util.blueprint_one import BlueprintOne
from genericsuite.models.logs.logs import (
    put_log,
    LogRequest,
)
from genericsuite.util.limiter import limiter


router = BlueprintOne()


@limiter.limit("5/10minutes")
@router.post(
    '',
    tags=['logs'],
)
async def logs_creation(
    request: Request,
    data: LogRequest = Body(...),
) -> Response:
    return put_log(data)
