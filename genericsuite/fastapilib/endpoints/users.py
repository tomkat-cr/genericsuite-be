"""
System users operations (CRUD, login, database test, super-admin creation)
"""
from fastapi import Request as FaRequest, Depends
# from fastapi.security import OAuth2PasswordRequestForm
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from genericsuite.util.framework_abs_layer import Response
from genericsuite.fastapilib.util.blueprint_one import BlueprintOne
from genericsuite.fastapilib.util.dependencies import (
    get_current_user,
    get_default_fa_request,
)
from genericsuite.models.users.users import (
    test_connection_handler as test_connection_handler_model,
    login_user as login_user_model,
    super_admin_create as super_admin_create_model,
    get_current_user_data,
)

# router = APIRouter()
router = BlueprintOne()

# Set up Basic Authentication
security = HTTPBasic()

HEADER_CREDS_ENTRY_NAME = 'Authorization'
DEBUG = False


@router.get('/test', tags='test')
async def test_connection_handler(
    request: FaRequest,
    current_user: str = Depends(get_current_user),
) -> Response:
    """Connection handler test"""
    gs_request, other_params = get_default_fa_request(current_user)
    router.set_current_request(request, gs_request)
    return test_connection_handler_model(gs_request, other_params)


@router.post('/login', tags='login')
async def login_user(
    request: FaRequest,
    # form_data: OAuth2PasswordRequestForm = Depends()
    credentials: HTTPBasicCredentials = Depends(security)
) -> Response:
    """User login"""
    gs_request, other_params = get_default_fa_request()
    router.set_current_request(request, gs_request)
    other_params['username'] = credentials.username
    other_params['password'] = credentials.password
    return login_user_model(
        request=gs_request, blueprint=router,
        other_params=other_params)


@router.post('/supad-create', tags='super-admin')
async def super_admin_create(
    request: FaRequest,
    # form_data: OAuth2PasswordRequestForm = Depends()
    credentials: HTTPBasicCredentials = Depends(security)
) -> Response:
    """Super admin user emergency creation"""
    gs_request, other_params = get_default_fa_request()
    router.set_current_request(request, gs_request)
    other_params['username'] = credentials.username
    other_params['password'] = credentials.password
    return super_admin_create_model(
        request=gs_request, blueprint=router,
        other_params=other_params)


@router.get('/current_user_d')
async def current_user_d(
    request: FaRequest,
    current_user: str = Depends(get_current_user),
) -> Response:
    """
    Current user data read
    """
    gs_request, other_params = get_default_fa_request(current_user)
    router.set_current_request(request, gs_request)
    return get_current_user_data(gs_request, router, other_params)
