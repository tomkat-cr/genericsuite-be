"""
Chaos experiments operations for Chalice
"""
from typing import Optional

from genericsuite.util.framework_abs_layer import (
    Request,
    Response,
    BlueprintOne
)

from genericsuite.util.jwt import (
    request_authentication,
    AuthorizedRequest,
)

from genericsuite.models.chaos.chaos_experiments import (
    list_chaos_experiments as list_chaos_experiments_model,
    start_chaos_experiment as start_chaos_experiment_model,
    stop_chaos_experiment as stop_chaos_experiment_model,
    get_chaos_experiment_status as get_chaos_experiment_status_model,
    chaos_test_endpoint as chaos_test_endpoint_model,
)

bp = BlueprintOne(__name__)

DEBUG = False


@bp.route(
    '/list',
    methods=['GET'],
    authorizor=request_authentication(),
)
def list_chaos_experiments(
    request: AuthorizedRequest,
    other_params: Optional[dict] = None
) -> Response:
    """List all available chaos experiments"""
    return list_chaos_experiments_model(request, bp, other_params)


@bp.route(
    '/start',
    methods=['POST'],
    authorizor=request_authentication(),
)
def start_chaos_experiment(
    request: AuthorizedRequest,
    other_params: Optional[dict] = None
) -> Response:
    """Start a chaos experiment"""
    return start_chaos_experiment_model(request, bp, other_params)


@bp.route(
    '/stop',
    methods=['POST'],
    authorizor=request_authentication(),
)
def stop_chaos_experiment(
    request: AuthorizedRequest,
    other_params: Optional[dict] = None
) -> Response:
    """Stop a chaos experiment"""
    return stop_chaos_experiment_model(request, bp, other_params)


@bp.route(
    '/status',
    methods=['GET'],
    authorizor=request_authentication(),
)
def get_chaos_experiment_status(
    request: AuthorizedRequest,
    other_params: Optional[dict] = None
) -> Response:
    """Get status of a chaos experiment"""
    return get_chaos_experiment_status_model(request, bp, other_params)


@bp.route(
    '/test',
    methods=['GET', 'POST'],
)
def chaos_test_endpoint(
    request: Request,
    other_params: Optional[dict] = None
) -> Response:
    """Test endpoint that applies active chaos experiments"""
    return chaos_test_endpoint_model(request, bp, other_params)