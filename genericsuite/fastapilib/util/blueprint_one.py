"""
Blueprint wrapper to add authorization, other data and schema validation
to requests.
"""
from typing import Optional, Any, Union, Dict

from fastapi import FastAPI
from fastapi import APIRouter, Request

# from genericsuite.util.app_logger import log_debug


class BlueprintOne(APIRouter):
    """
    Class to register a new route with optional schema validation and
    authorization.
    """
    name: str = "NoName"
    current_app: Optional[Any] = None
    current_request: Optional[Any] = None
    current_fa_request: Optional[Any] = None
    context: Optional[dict] = {}
    event_dict: Optional[dict] = {}

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
        # log_debug(
        #    f">> BlueprintOne(APIRouter) | Current App: {self.current_app}")
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
        # https://stackoverflow.com/questions/62147474/how-to-print-complete-http-request-using-chalice
        self.context = {
            "resourcePath": fa_request.url.path.split('/')[-1],
            "Path": str(fa_request.url.path),
            "requestId": fa_request.headers.get('X-Amzn-Trace-Id'),
            "apiId": fa_request.headers.get('X-Api-Id'),
            "resourceId": fa_request.headers.get('X-Amz-Api-Id'),
        }
        return self.current_request

    def to_dict(self):
        """
        Returns the request data as a dictionary.
        """
        return {
            "method": self.method,
            "query_params": self.query_params,
            "json_body": self.json_body,
            "headers": self.headers,
            "context": self.context,
        }

    def to_original_event(self) -> Union[Dict[str, Any], None]:
        """
        Returns the original event dictionary.
        """
        return self.event_dict
