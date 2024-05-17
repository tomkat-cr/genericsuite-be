"""
FastAPI dependencies library
"""
from typing import Optional, Union

from fastapi import HTTPException, Depends, Request as FaRequest
from fastapi.security import OAuth2PasswordBearer

from genericsuite.fastapilib.framework_abstraction import (
    Request,
)
from genericsuite.util.jwt import (
    get_general_authorized_request,
    AuthorizedRequest,
    AuthTokenPayload,
)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


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


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Verifies the JWT token and returns the current user.
    """
    request = build_request(headers={"token": token})
    auth_request = get_general_authorized_request(request)
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    # if auth_request.user is None:
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
    if current_user:
        params["headers"]["current_user"] = current_user
    request = build_request(**params)
    other_params = other_params if other_params else {}
    return request, other_params
