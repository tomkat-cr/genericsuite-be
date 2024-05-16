"""
Context manager to preserve data between GPT functions
"""
from typing import Any, Union, Optional
import os
import json

from genericsuite.constants.const_tables import get_constant
from genericsuite.util.current_user_data import (
    get_curr_user_data,
    get_curr_user_id,
    NON_AUTH_REQUEST_USER_ID,
)
from genericsuite.util.jwt import AuthorizedRequest
from genericsuite.util.utilities import get_default_resultset, get_id_as_string
from genericsuite.util.app_logger import log_debug


DEBUG = False
TEMP_DIR = os.environ.get('TEMP_DIR', '/tmp')


class ParamsFile():
    """
    Class to manage the parameters file (/tmp/param_*.json)
    """
    def __init__(self, user_id: str):
        self.user_id = user_id

    def get_params_filename(self) -> str:
        """
        Get the filename where the parameters are stored.
        """
        filename = os.path.join(TEMP_DIR,
            f'params_{self.user_id}.json')
        if NON_AUTH_REQUEST_USER_ID in filename:
            # For the un-authenticated endpoint calls file
            filename = filename.replace(NON_AUTH_REQUEST_USER_ID, 'GENERAL')
        _ = DEBUG and \
            log_debug(f'PF-1) get_params_filename | filename: {filename}')
        return filename

    def load_params_file(self) -> Union[dict, None]:
        """
        Load the parameters from a file.
        """
        filename = self.get_params_filename()
        result = get_default_resultset()
        result['found'] = False
        if not os.path.exists(filename):
            return result
        with open(filename, 'r', encoding='utf-8') as f:
            result['found'] = True
            result['resultset'] = json.load(f)
        return result

    def save_params_file(self, params: dict, user_data: dict) -> dict:
        """
        Store the parameters in a file.
        """
        filename = self.get_params_filename()
        if '_id' in user_data:
            user_data['_id'] = get_id_as_string(user_data)
        data_to_save = {
            "user_data": user_data,
            "params": params,
        }
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f)
        result = get_default_resultset()
        result['resultset'] = data_to_save
        return result


class AppContext:
    """
    Context manager class to preserve data between GPT functions
    """
    def __init__(self, request: AuthorizedRequest = None, blueprint: Any = None):
        # AuthorizedRequest object received from the endpoit handler
        self.request = request
        # Blueprint object received from the endpoit handler
        self.blueprint = blueprint
        # Curret user's data
        self.user_data = None
        # Any error happened during the user's data or other retrievals
        self.error_message = None
        # "self.other" was created to make globally available some values that
        # should not be calculated each time a GPT function is called.
        self.other_data = {}
        # Environment variables loaded from the database
        self.env_data = {}

    def set_context_from_blueprint(self, blueprint: Any, request: Any = None):
        """ Set the request object """
        self.blueprint = blueprint
        if request:
            self.set_context(request)
        else:
            self.set_context(blueprint.get_current_request())

    def set_context(self, request: Any):
        """ Set the request object """
        self.request = request
        self.user_data = self.get_user_data()

    def get_user_id(self):
        """ Get current user ID """
        return get_curr_user_id(self.request)

    def get_request(self):
        """ Get the request object """
        return self.request

    def get_blueprint(self):
        """ Get the blueprint object """
        return self.blueprint

    def get_user_data_raw(self) -> None:
        """
        Get current user data
        """
        # user_response = get_curr_user_data(self.request)
        user_response = get_curr_user_data(request=self.request,
            blueprint=self.blueprint)
        if user_response['error']:
            self.set_error(user_response['error_message'])
            return
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

    def get_user_data(self, check_params_file: Optional[bool] = True):
        """
        Get current user data verifying the params file existence
        """
        if not self.user_data:
            if check_params_file:
                pfc = ParamsFile(self.get_user_id())
                params_file_result = pfc.load_params_file()
                if params_file_result['found']:
                    self.user_data = params_file_result['resultset']['user_data']
                else:
                    self.get_user_data_raw()
                    if '_id' in self.user_data:
                        pfc.save_params_file({}, self.user_data)
            else:
                self.get_user_data_raw()
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


def get_app_context(app_context_or_blueprint: Any):
    """
    Get the application context object
    """
    if isinstance(app_context_or_blueprint, AppContext):
        app_context = app_context_or_blueprint
    else:
        app_context = AppContext()
        app_context.set_context_from_blueprint(app_context_or_blueprint)
    return app_context


def delete_params_file(app_context_or_blueprint: Any,
    action_data: Optional[Union[dict, None]]) -> None:
    """
    GenericDbHelper specific function to delete the parameters file (e.g. when
    general_config or user's users_config array is changed).

    Args:
        app_context (AppContext): the application context object
        action_data (dict, optional): the action data. Defaults to None.
            If it's not None, it must have:
            "action" key: "create", "read", "update" or "delete"
            "resultset" key: resultset for data to be stored, delete or
                retrieved with the keys: resultset, error, error_message.
    """
    app_context = get_app_context(app_context_or_blueprint)
    pfc = ParamsFile(app_context.get_user_id())
    action_data = action_data or {}
    # if action_data.get("action") != "delete":
    #     return resultset
    filenames = [
        # For the current authenticated user file
        pfc.get_params_filename(),
        # For the un-authenticated endpoint calls file
        'params_GENERAL.json'
    ]
    for filename in filenames:
        if os.path.exists(filename):
            os.remove(filename)
    return action_data['resultset']
