"""
Blueprint wrapper to add authorization, other data and schema validation
to requests.
"""
from typing import Optional, Any

from fastapi import FastAPI
from fastapi import APIRouter, Request

# from genericsuite.util.app_logger import log_debug


class BlueprintOne(APIRouter):
    """
    Class to register a new route with optional schema validation and authorization.
    """
    name: str = "NoName"
    current_app: Optional[Any] = None
    current_request: Optional[Any] = None
    current_fa_request: Optional[Any] = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if len(args) > 0:
            self.name = args[0]

    def get_current_app(self) -> Any:
        """
        Get the current App object. It must be called inside a router function.
        """
        # self.current_request = Request(scope={"type": "http"})
        # self.current_app = self.app
        # log_debug(f">> BlueprintOne(APIRouter) | Current App: {self.current_app}")
        return self.current_app

    def set_current_app(self, app: FastAPI) -> Any:
        """
        Get the current App object. It must be called inside a router function.
        """
        self.current_app = app
        return self.current_app

    def get_current_fa_request(self) -> Any:
        """
        Get the current App object. It must be called inside a router function.
        """
        # self.current_request = Request(scope={"type": "http"})
        return self.current_fa_request

    def get_current_request(self) -> Any:
        """
        Get the current App object. It must be called inside a router function.
        """
        # self.current_request = Request(scope={"type": "http"})
        return self.current_request

    def set_current_request(self, fa_request: Request, gs_request: Any) -> Any:
        """
        Get the current App object. It must be called inside a router function.
        """
        self.current_request = gs_request
        self.current_fa_request = fa_request
        self.set_current_app(fa_request.app)
        return self.current_request
