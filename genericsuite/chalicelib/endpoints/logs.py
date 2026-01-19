"""
Log server
"""
from typing import Optional

from genericsuite.util.framework_abs_layer import Response, BlueprintOne

from genericsuite.util.jwt import (
    request_authentication,
    AuthorizedRequest
)

from genericsuite.models.logs.logs import put_log


bp = BlueprintOne(__name__)


@bp.route(
    '/',
    methods=['POST'],
    authorizor=request_authentication(),
)
async def logs_creation(
    request: AuthorizedRequest,
    other_params: Optional[dict] = None
) -> Response:
    return put_log(request, bp, other_params)
