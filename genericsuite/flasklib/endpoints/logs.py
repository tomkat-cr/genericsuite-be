"""
Log server
"""
from genericsuite.util.framework_abs_layer import Response, Request

from genericsuite.config.config import Config
from genericsuite.flasklib.util.blueprint_one import BlueprintOne
from genericsuite.flasklib.util.limiter import get_flask_limiter

from genericsuite.models.logs.logs import (
    put_log,
    LogRequest,
)


settings = Config()
bp = BlueprintOne("logs", __name__,
                  url_prefix=f'/{settings.API_VERSION}/logs')
limiter = get_flask_limiter(bp)


@limiter.limit("10 per minute")
@bp.route('', methods=['POST'])
def logs_creation(
    request: Request,
) -> Response:
    return put_log(LogRequest(**request.get_json()))
