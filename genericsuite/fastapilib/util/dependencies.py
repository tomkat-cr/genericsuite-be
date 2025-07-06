"""
FastAPI dependencies library
"""
from typing import Optional, Union

from fastapi import HTTPException,  Request as FaRequest
# from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from genericsuite.fastapilib.framework_abstraction import (
    Request,
)
from genericsuite.util.app_logger import log_debug
from genericsuite.util.jwt import (
    get_general_authorized_request,
    AuthorizedRequest,
    AuthTokenPayload,
)

DEBUG = False

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)


def build_request(
    method: Optional[str] = None,
    query_params: Optional[dict] = None,
    json_body: Optional[dict] = None,
    headers: Optional[dict] = None,
    preserve_nones: bool = False,
) -> Union[Request, AuthorizedRequest]:
    """
    Builds the request query parameters from query_received and cleans it,
    leaving only the ones that are not None

    Args:
        method (str): HTTP method.
        query_params (dict): URL query parameters.
        json_body (dict): Request JSON body.
        headers (dict): Request headers.

    Returns:
        dict: The cleaned request query parameters.
    """
    _ = DEBUG and log_debug(
        f">> BUILD_REQUEST"
        f"\n | method: {method}"
        f"\n | query_params: {query_params}"
        f"\n | json_body: {json_body}"
        f"\n | headers: {headers}"
        f"\n | preserve_nones: {preserve_nones}"
    )
    query_params_reduced = {}
    if query_params:
        # Reduce query_params leaving only the not None items
        query_params_reduced = {k: v for k, v in query_params.items()
                                if v is not None or preserve_nones}
    headers_reduced = headers if headers else {}
    if "token" in headers_reduced:
        headers_reduced["Authorization"] = f"Bearer {headers_reduced['token']}"
        del headers_reduced["token"]
    if "current_user" in headers_reduced:
        new_request = AuthorizedRequest(
            method=method if method else "get",
            query_params=query_params_reduced,
            json_body=json_body if json_body else {},
            headers=headers_reduced,
            user=headers_reduced["current_user"])
    else:
        new_request = Request(
            method=method if method else "get",
            query_params=query_params_reduced,
            json_body=json_body if json_body else {},
            headers=headers_reduced)
    return new_request


# async def get_current_user(
#     token: str = Depends(oauth2_scheme),
# ):
async def get_current_user(request: FaRequest):
    """
    Verifies the JWT token and returns the current user.
    """
    token = await oauth2_scheme(request)
    headers = dict(request.headers)
    headers["token"] = token
    _ = DEBUG and log_debug(
        f">> GET_CURRENT_USER"
        f"\n | token: {token}"
        f"\n | request: {request}"
        f"\n | headers: {headers}"
    )
    own_request = build_request(
        headers=headers,
        query_params=request.query_params,
        # JSON body must be processed in the endpoint,
        # with FastAPI + Pydantic style...
        # because none of the following worked:
        #   json_body=await request.json() if await request.body() else {},
        #   json_body=request.body(),
    )
    auth_request = get_general_authorized_request(own_request)
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not isinstance(auth_request, AuthorizedRequest):
        raise credentials_exception
    return auth_request.user


def get_default_fa_request(
    current_user: Optional[AuthTokenPayload] = None,
    json_body: Optional[dict] = None,
    headers: Optional[dict] = None,
    query_params: Optional[dict] = None,
    other_params: Optional[dict] = None,
    preserve_nones: bool = False,
):
    """
    Builds the default FA (FastAPI) Authentication request object.
    """
    params = {
        "json_body": json_body if json_body else {},
        "headers": headers if headers else {},
        "query_params": query_params if query_params else {},
        "preserve_nones": preserve_nones,
    }
    _ = DEBUG and log_debug(
        f">> GET_DEFAULT_FA_REQUEST"
        f"\n | current_user: {current_user}"
        f"\n | json_body: {json_body}"
        f"\n | headers: {headers}"
        f"\n | query_params: {query_params}"
        f"\n | preserve_nones: {preserve_nones}"
        f"\n | params: {params}"
    )
    if current_user:
        params["headers"]["current_user"] = current_user
    request = build_request(**params)
    other_params = other_params if other_params else {}
    return request, other_params


def get_fa_query_params(request: FaRequest):
    """
    Returns the query parameters from the request.
    The FastAPI request has a query_string attribute that a bytes object,
    so we need to decode it to a string and split it by "&" to get the
    query parameters.
    For example:
    'query_string': b'page=1&limit=30&like=1&comb=or&firstname=felipe&'
                    'lastname=felipe&creation_date=946684800'
    """
    query_params = {v.split("=")[0]: v.split("=")[1]
                    for v in request['query_string'].decode("utf-8").split("&")
                    if v.split("=") and len(v.split("=")) > 1}
    _ = DEBUG and log_debug(
        f">> GET_FA_QUERY_PARAMS from FastAPI Request"
        f"\n | request: {request}"
        f"\n | query_params: {query_params}"
    )
    return query_params
