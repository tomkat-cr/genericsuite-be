"""
Blueprint wrapper to add authorization, other data and schema validation
to requests.
"""
from typing import Optional, Any
from fastapi import APIRouter, Request
# from fastapi import Depends


class BlueprintOne(APIRouter):
    """
    Class to register a new route with optional schema validation and authorization.
    """
    name: str = "NoName"
    current_app: Optional[Any] = Request(scope={}).app
    current_request: Optional[Any] = Request(scope={})

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if len(args) > 0:
            self.name = args[0]

    def get_current_app(self) -> Any:
        """
        Get the current App object. It must be called inside a router function.
        """
        return self.current_app

    def get_current_request(self) -> Any:
        """
        Get the current App object. It must be called inside a router function.
        """
        return self.current_request