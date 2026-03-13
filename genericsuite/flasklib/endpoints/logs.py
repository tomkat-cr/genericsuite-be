"""
Log server
"""
from typing import Optional

from genericsuite.util.framework_abs_layer import Response

from genericsuite.util.jwt import (
    AuthorizedRequest
)
from genericsuite.config.config import Config
from genericsuite.flasklib.util.jwt import token_required
from genericsuite.flasklib.util.blueprint_one import BlueprintOne

from genericsuite.models.logs.logs import put_log


settings = Config()
bp = BlueprintOne("logs", __name__,
                  url_prefix=f'/{settings.API_VERSION}/logs')


@bp.route('', methods=['POST'])
@token_required
def logs_creation(
    request: AuthorizedRequest,
    other_params: Optional[dict] = None
) -> Response:
    return put_log(request, bp, other_params)
