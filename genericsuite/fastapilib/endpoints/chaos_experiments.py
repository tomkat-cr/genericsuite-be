"""
Chaos experiments operations for FastAPI
"""
from fastapi import Request as FaRequest, Depends

from genericsuite.util.framework_abs_layer import Response
from genericsuite.fastapilib.util.blueprint_one import BlueprintOne
from genericsuite.fastapilib.util.dependencies import (
    get_current_user,
    get_default_fa_request,
)
from genericsuite.models.chaos.chaos_experiments import (
    list_chaos_experiments as list_chaos_experiments_model,
    start_chaos_experiment as start_chaos_experiment_model,
    stop_chaos_experiment as stop_chaos_experiment_model,
    get_chaos_experiment_status as get_chaos_experiment_status_model,
    chaos_test_endpoint as chaos_test_endpoint_model,
)

router = BlueprintOne()

DEBUG = False


@router.get('/list', tags=['chaos_experiments'])
async def list_chaos_experiments(
    request: FaRequest,
    current_user: str = Depends(get_current_user),
) -> Response:
    """List all available chaos experiments"""
    gs_request, other_params = get_default_fa_request(current_user)
    router.set_current_request(request, gs_request)
    return list_chaos_experiments_model(gs_request, router, other_params)


@router.post('/start', tags=['chaos_experiments'])
async def start_chaos_experiment(
    request: FaRequest,
    current_user: str = Depends(get_current_user),
) -> Response:
    """Start a chaos experiment"""
    gs_request, other_params = get_default_fa_request(current_user)
    router.set_current_request(request, gs_request)
    return start_chaos_experiment_model(gs_request, router, other_params)


@router.post('/stop', tags=['chaos_experiments'])
async def stop_chaos_experiment(
    request: FaRequest,
    current_user: str = Depends(get_current_user),
) -> Response:
    """Stop a chaos experiment"""
    gs_request, other_params = get_default_fa_request(current_user)
    router.set_current_request(request, gs_request)
    return stop_chaos_experiment_model(gs_request, router, other_params)


@router.get('/status', tags=['chaos_experiments'])
async def get_chaos_experiment_status(
    request: FaRequest,
    current_user: str = Depends(get_current_user),
) -> Response:
    """Get status of a chaos experiment"""
    gs_request, other_params = get_default_fa_request(current_user)
    router.set_current_request(request, gs_request)
    return get_chaos_experiment_status_model(gs_request, router, other_params)


@router.get('/test', tags=['chaos_experiments'])
@router.post('/test', tags=['chaos_experiments'])
async def chaos_test_endpoint(
    request: FaRequest,
) -> Response:
    """Test endpoint that applies active chaos experiments"""
    gs_request, other_params = get_default_fa_request()
    router.set_current_request(request, gs_request)
    return chaos_test_endpoint_model(gs_request, router, other_params)