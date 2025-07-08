"""
Context manager to preserve data between GPT functions
"""
from typing import Any, Union, Optional, Callable
import os
import json

from genericsuite.config.config_secrets import get_secrets_cache_filename
from genericsuite.constants.const_tables import get_constant
from genericsuite.util.current_user_data import (
    get_curr_user_data,
    get_curr_user_id,
    NON_AUTH_REQUEST_USER_ID,
)
from genericsuite.util.jwt import AuthorizedRequest
from genericsuite.util.utilities import get_default_resultset, get_id_as_string
from genericsuite.util.app_logger import log_debug, log_error
from genericsuite.util.generic_db_helpers import GenericDbHelper


DEBUG = False
TEMP_DIR = os.environ.get('TEMP_DIR', '/tmp')

PARAMS_FILE_ENABLED = os.environ.get('PARAMS_FILE_ENABLED', '1')
PARAMS_FILE_USER_FILENAME_TEMPLATE = os.environ.get(
    'PARAMS_FILE_USER_FILENAME_TEMPLATE', 'params_[user_id].json')
PARAMS_FILE_GENERAL_FILENAME = os.environ.get(
    'PARAMS_FILE_GENERAL_FILENAME', 'params_GENERAL.json')


class ParamsFile():
    """
    Class to manage the parameters file (/tmp/param_*.json)
    """
    def __init__(self, user_id: str):
        self.user_id = user_id

    def get_params_file_path(self, filename: str):
        """
        Get the path of the file.
        """
        return os.path.join(TEMP_DIR, filename)

    def get_params_filename(self, user_id: Optional[str] = None
                            ) -> Union[str, None]:
        """
        Get the filename where the parameters are stored.
        """
        if not user_id:
            user_id = self.user_id
        if user_id == NON_AUTH_REQUEST_USER_ID:
            # For the un-authenticated endpoint calls file
            filename = None
        else:
            filename = self.get_params_file_path(
                PARAMS_FILE_USER_FILENAME_TEMPLATE.replace(
                    '[user_id]', user_id))
        _ = DEBUG and \
            log_debug(
                'GET_FILENAME-1) get_params_filename |' +
                f' user_id: {user_id} | filename: {filename}')
        return filename

    def load_params_file(self, filename: str) -> dict:
        """
        Load the parameters from a file.
        """
        result = get_default_resultset()
        result['found'] = True
        if PARAMS_FILE_ENABLED != '1':
            result['error_message'] = "Params. file flag disabled"
            result['found'] = False
        elif not filename:
            result['error_message'] = "Filename is null"
            result['found'] = False
        elif not os.path.exists(filename):
            result['error_message'] = f"Filename does not exist: {filename}"
            result['found'] = False
        if result['found']:
            with open(filename, 'r', encoding='utf-8') as fhdlr:
                result['resultset'] = json.load(fhdlr)
        _ = DEBUG and \
            log_debug(f'LOAD_PF-1) load_params_file | File: {filename}' +
                      f' | {result["resultset"]}')
        return result

    def save_params_file(self, filename: str, data_to_save: dict) -> dict:
        """
        Store the parameters in a file.

        Example files:

        cat /tmp/params_{user_id}.json
        {
            "_id": "{user_id}",
            "firstname": "Exmaple name",
            "lastname": "Example lastname",
            "superuser": "0",
            "status": "1",
            "plan": "premium",
            "language": "en",
            "email": "example@email.com",
            "creation_date": 1731864902.365586,
            "update_date": 1731864902.365586,
            "birthday": -131760000,
            "gender": "m",
            "users_preferences": [
                {
                    "property_type": "house",
                    "property_for": "rent",
                    "min_price": 0,
                    "max_price": 0,
                    "preferred_location": "",
                    "id": "e1d24bc9-0b5b-4485-b257-47f5e93bfaab"
                }
            ],
            "users_config": [
                {
                    "config_name": "ExampleParamName",
                    "config_value": "ExampleParamValue",
                    "id": "00a72c28-58c9-499d-957a-f2cfad12670d"
                }
            ]
            "users_api_keys": [
                {
                    "access_token": "ExampleToken",
                    "id": "00a72c28-58c9-499d-957a-f2cfad12670d"
                }
            ]
        }

        cat /tmp/params_GENERAL.json
        {
            "AI_TECHNOLOGY": "xai"
        }

        """
        result = get_default_resultset()
        result['resultset'] = data_to_save
        if PARAMS_FILE_ENABLED != '1':
            return result
        if '_id' in data_to_save:
            data_to_save['_id'] = get_id_as_string(data_to_save)
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f)
        _ = DEBUG and log_debug('PF-2) save_params_file |' +
                                f' filename: {filename} |' +
                                f' content: {data_to_save}')
        return result


class AppContext:
    """
    Context manager class to preserve data between GPT functions
    """
    def __init__(
        self,
        request: Optional[Union[AuthorizedRequest, None]] = None,
        blueprint: Optional[Any] = None
    ):
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
        user_response = get_curr_user_data(
            request=self.request,
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
                self.set_error(get_constant(
                    "ERROR_MESSAGES",
                    "NO_USER_DATA", "System Error [AC-GUD-E010]" +
                    f" | id: {self.get_user_id()}"))
                self.user_data = {}
        elif self.user_data.get('status', '1') == '0':
            self.set_error(get_constant(
                "ERROR_MESSAGES",
                "ACCOUNT_INACTIVE", "User account inactive [AC-GUD-E020]"))

    def get_user_data(self, check_params_file: Optional[bool] = True):
        """
        Get current user data verifying the params JSON cache file existence
        """
        if not self.user_data:
            if check_params_file and PARAMS_FILE_ENABLED == '1':
                pfc = ParamsFile(self.get_user_id())
                filename = pfc.get_params_filename()
                if not filename:
                    self.get_user_data_raw()
                else:
                    params_file_result = pfc.load_params_file(filename)
                    if params_file_result['found']:
                        # self.user_data = \
                        #   params_file_result['resultset']['user_data']
                        self.user_data = params_file_result['resultset']
                    else:
                        self.get_user_data_raw()
                        if '_id' in self.user_data:
                            pfc.save_params_file(filename, self.user_data)
            else:
                self.get_user_data_raw()
        _ = DEBUG and log_debug(
            "AppContext | GET_USER_DATA" +
            f"\n | self.user_data: {self.user_data}" +
            f"\n | self.error_message: {self.error_message}")
        return self.user_data

    def get_other_data(
        self,
        element_name: str,
        generator_func: Callable = None,
        generator_params: dict = None,
    ):
        """
        Get "other" data element value.
        If it doesn't exist, try to call the generator_func
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
        """ Set environment variable value """
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


def delete_params_file(
    app_context_or_blueprint: Any,
    action_data: Optional[Union[dict, None]]
) -> None:
    """
    GenericDbHelper specific function to delete the parameters file (e.g. when
    general_config or user's users_config array is changed).

    Args:
        app_context (AppContext): the application context object
        action_data (dict, optional): the action data. Defaults to None.
            If it's not None, it must have the following keys (attributes):
            "action": "list", "read", "create", "update" or "delete"
            "resultset": resultset for data to be stored, delete or
                retrieved with the keys: resultset, error, error_message.
            "cnf_db": the table configuration. E.g. tablename is
                cnf_db['tablename']
    """
    if PARAMS_FILE_ENABLED != '1':
        return action_data['resultset']

    app_context = get_app_context(app_context_or_blueprint)
    pfc = ParamsFile(app_context.get_user_id())
    action_data = action_data or {}
    tablename = action_data.get("cnf_db", {}).get("table_name")

    _ = DEBUG and log_debug("AppContext | DELETE_PARAMS_FILE" +
                            f"\n | action_data: {action_data}" +
                            f"\n | tablename: {tablename}")
    # Only delete the params file if the action is not read or list
    if action_data.get("action") in ["read", "list"]:
        return action_data['resultset']
    # Verify if any error
    if action_data['resultset']['error']:
        return action_data['resultset']
    if tablename:
        # Get the filename according to the table name
        if tablename == 'general_config':
            filenames = [
                pfc.get_params_file_path(PARAMS_FILE_GENERAL_FILENAME),
                get_secrets_cache_filename("secrets"),
                get_secrets_cache_filename("envs"),
            ]
        else:
            # Get the user ID if it's not the general table

            # Get the database item resultset
            db_item = action_data['resultset']['resultset']
            # Example db_item:
            # {"rows_affected": "1", "_id": "6771x9999999999999999999"}

            if isinstance(db_item, str):
                db_item = json.loads(db_item)
            _ = DEBUG and log_debug(
                'DB SPECIFIC FUNCTION:' +
                f" delete_params_file | db_item: {db_item}")

            # Inconsistency If _id not in resultset...
            if '_id' not in db_item:
                return action_data['resultset']

            # Get the user ID from the resultset
            user_id = get_id_as_string(db_item)
            _ = DEBUG and log_debug(
                'DB SPECIFIC FUNCTION:' +
                f" delete_params_file | user_id: {user_id}")

            filenames = [pfc.get_params_filename(user_id)]

        _ = DEBUG and log_debug("AppContext | DELETE_PARAMS_FILE" +
                                f"\n | filenames: {filenames}")

        if action_data.get("action") in ["create", "update"] and \
           tablename != 'general_config':
            # If it's a create or update, the params file must be created or
            # updated in order to make API Keys validation work...
            # Only if the params file is related to a user
            # Reference: get_api_key_auth() in jwt.py

            user_file_name = pfc.get_params_filename(user_id)
            if user_file_name in filenames:
                # Get user's data for id in db_item["_id"]
                dbo = GenericDbHelper(
                    json_file="users",
                    request=app_context_or_blueprint.get_current_request(),
                    blueprint=app_context_or_blueprint,
                )
                user_response = dbo.fetch_row_raw(user_id, {'passcode': 0})
                if user_response['error']:
                    log_error(
                        f"DELETE_PARAMS_FILE"
                        f" | action: {action_data['action']}"
                        f" | ERROR: {user_response['error_message']}")
                    return action_data['resultset']

            # Create or update usr's params file, delete others
            for filename in filenames:
                if filename == user_file_name:
                    pfc = ParamsFile(user_id)
                    pfc.save_params_file(filename, user_response['resultset'])
                elif os.path.exists(filename):
                    # Delete params file if it's not a user's params file
                    os.remove(filename)

        if action_data.get("action") in ["delete"] or \
           tablename == 'general_config':
            # Delete params file if exists
            for filename in filenames:
                if os.path.exists(filename):
                    os.remove(filename)
                    _ = DEBUG and log_debug("AppContext | DELETE_PARAMS_FILE" +
                                            f"\n | File deleted: {filename}")
                else:
                    _ = DEBUG and log_debug("AppContext | DELETE_PARAMS_FILE" +
                                            f"\n | File not found: {filename}")
    return action_data['resultset']


def save_user_param_file(user_id: str) -> dict:
    dbo = GenericDbHelper(json_file="users")
    user_response = dbo.fetch_row_raw(user_id, {'passcode': 0})
    if user_response['error']:
        return user_response
    pfc = ParamsFile(user_id)
    filename = pfc.get_params_filename(user_id)
    return pfc.save_params_file(filename, user_response['resultset'])


def save_all_users_params_files() -> dict:
    """
    Save all users params files, to enable use of API keys
    Check out "CAUJF: Create All User JSON Files" for more info
    """
    self_debug = DEBUG
    # self_debug = True
    response = get_default_resultset()
    dbo = GenericDbHelper(json_file="users")

    users_params_files = dbo.fetch_list(skip=0, limit=0)
    if users_params_files['error']:
        response['error'] = True
        response['error_message'] = \
            users_params_files['error_message']
        log_error(
            f"save_all_users_params_files"
            f" | ERROR: {users_params_files['error_message']}")
        return response

    errors = []
    _ = self_debug and log_debug(
        f"save_all_users_params_files"
        f" | users_params_files: {users_params_files}")
    for user in json.loads(users_params_files['resultset']):
        # Get user's data
        user_id = get_id_as_string(user)
        save_response = save_user_param_file(user_id)
        if save_response['error']:
            response['error'] = True
            errors.append(f"UserId: {user_id} | Error: "
                          f"{save_response['error_message']}")
            continue

    if response['error']:
        response['error_message'] = \
            f"Errors saving params files: {', '.join(errors)}"
        log_error(
            f"save_all_users_params_files"
            f" | ERROR: {response['error_message']}")
    else:
        _ = self_debug and log_debug(
            f"save_all_users_params_files"
            f" | All params files saved"
            f"\n | response: {response}")

    return response
