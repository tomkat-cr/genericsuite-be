"""
Context manager to preserve data between GPT functions
"""
from typing import Any
import os

from genericsuite.constants.const_tables import get_constant
from genericsuite.util.current_user_data import (
    get_curr_user_data,
    get_curr_user_id,
    NON_AUTH_REQUEST_USER_ID,
)
from genericsuite.util.jwt import AuthorizedRequest
from genericsuite.util.utilities import get_default_resultset
from genericsuite.util.app_logger import log_debug


DEBUG = False


class AppContext:
    """
    Context manager class to preserve data between GPT functions
    """
    def __init__(self, request: AuthorizedRequest = None):
        # AuthorizedRequest object received from the endpoit handler
        self.request = request
        # Curret user's data
        self.user_data = None
        # Any error happened during the user's data or other retrievals
        self.error_message = None
        # "self.other" was created to make globally available some values that
        # should not be calculated each time a GPT function is called.
        self.other_data = {}
        # Environment variables loaded from the database
        self.env_data = {}

    def set_context(self, request):
        """ Set the request object """
        self.request = request
        self.user_data = self.get_user_data()

    def get_user_id(self):
        """ Get current user ID """
        return get_curr_user_id(self.request)

    def get_request(self):
        """ Get the request object """
        return self.request

    def get_user_data(self):
        """ Get current user data """
        if not self.user_data:
            user_response = get_curr_user_data(self.request)
            if user_response['error']:
                self.set_error(user_response['error_message'])
                return None
            self.user_data = user_response['resultset']
            if not self.user_data:
                if 'PYTEST_CURRENT_TEST' in os.environ:
                    self.user_data = {
                        "_id": self.get_user_id(),
                    }
                elif self.get_user_id() == NON_AUTH_REQUEST_USER_ID:
                    # It's a normal Request without Authorization headers
                    self.user_data = {}
                else:
                    # Inconsistency Error
                    self.set_error(get_constant("ERROR_MESSAGES",
                        "NO_USER_DATA", "System Error [AC-GUD-E010]" +
                        f" | id: {self.get_user_id()}"))
                    self.user_data = {}
            elif self.user_data.get('status', '1') == '0':
                self.set_error(get_constant("ERROR_MESSAGES",
                    "ACCOUNT_INACTIVE", "User account inactive [AC-GUD-E020]"))
        _ = DEBUG and log_debug("AppContext | GET_USER_DATA" + 
            f"\n | self.user_data: {self.user_data}" +
            f"\n | self.error_message: {self.error_message}")
        return self.user_data

    def get_other_data(
        self,
        element_name: str,
        generator_func: callable = None,
        generator_params: dict = None,
    ):
        """
        Get "other" data element value.
        If it doesn't exist try to call the generator_func
        with generator_params to assign the element's value.

        Args:
            element_name (str): name of the element to retrieve.
            generator_func (callable): function to generate the element value.
            The function should return a
            generator_params (dict): parameters for the generator fuction.

        Retuns:
            Any: the element's value or None if it's not present.
        """
        if element_name not in self.other_data:
            if generator_func is None:
                return None
            result = generator_func(**generator_params)
            if result.get("error", False):
                self.other_data[element_name] = result
            else:
                self.set_error(result.get(
                    "error_message", "ERROR calling generator_func [GPTC-010]"
                ))
        return self.other_data[element_name]

    def set_error(self, error_message: str) -> None:
        """
        Assign the internal error message
        """
        self.error_message = error_message

    def get_error(self) -> str:
        """
        Get the internal error message
        """
        return self.error_message

    def has_error(self) -> str:
        """
        Returns True if there's any error
        """
        return self.error_message is not None

    def get_error_resultset(self) -> dict:
        """
        Get the internal error message as a standard resultset
        """
        resultset = get_default_resultset()
        resultset["error"] = True
        resultset["error_message"] = self.error_message
        return resultset

    def set_other_data(
        self,
        element_name: str,
        value: Any,
    ) -> Any:
        """ Get "other" data element value. """
        self.other_data[element_name] = value
        return self.other_data[element_name]

    def get_env_var(self, var_name: str, def_value: Any = None) -> Any:
        """ Get environment variable value """
        return self.env_data.get(var_name, def_value)

    def set_env_var(
        self,
        var_name: str,
        value: Any,
    ) -> Any:
        """ Get "other" data element value. """
        self.env_data[var_name] = value
        return self.env_data[var_name]


class CommonAppContext():
    """
    Common context manager for the Langchain AI Chatbot API
    """
    def __init__(self):
        self.app_context = None

    def set(self, app_context: AppContext):
        """
        Set the common app context
        """
        self.app_context = app_context

    def get(self):
        """
        Get the common app context
        """
        return self.app_context
