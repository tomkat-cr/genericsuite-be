"""
Configuration from the Database
"""
from typing import Any, Union, Optional
import os
import json

from genericsuite.util.app_context import (
    AppContext,
    ParamsFile,
    delete_params_file,
    PARAMS_FILE_ENABLED,
    PARAMS_FILE_GENERAL_FILENAME,
    NON_AUTH_REQUEST_USER_ID
)
from genericsuite.util.app_logger import log_debug, log_error
from genericsuite.util.generic_db_middleware import (
    fetch_all_from_db,
)
from genericsuite.util.jwt import AuthorizedRequest
from genericsuite.util.utilities import get_default_resultset


DEBUG = False
USE_DB_PARAMS_DEFAULT = os.environ.get('USE_DB_PARAMS_DEFAULT', "1")
# USE_DB_PARAMS_DEFAULT = "0"  # Usefull for slow local dev environments


def get_general_config(app_context: AppContext) -> dict:
    """
    Get all general parameters.
    """
    if DEBUG:
        log_debug('GGC-1) get_general_config')
    if os.environ.get("USE_DB_PARAMS", USE_DB_PARAMS_DEFAULT) != "1":
        return get_default_resultset()
    resultset = fetch_all_from_db(
        app_context=app_context,
        json_file='general_config',
        like_query_params={"active": "1"}
    )
    if not resultset["error"]:
        resultset["resultset"] = {
            r["config_name"]: r["config_value"]
            for r in json.loads(resultset["resultset"])
            if r["config_name"] not in
            # These variables cannot be loaded from database because
            # they are harmful if taken from source different
            # than enviroment variables.
            [
                "DB_CONFIG",
                "DB_ENGINE",
                "DEBUG",
                "APP_NAME",
                "APP_VERSION",
                "STAGE",
                "SECRET_KEY",
                "APP_SECRET_KEY",
                "APP_SUPERADMIN_EMAIL",
                "GIT_SUBMODULE_LOCAL_PATH",
                "CORS_ORIGIN",
                "HEADER_TOKEN_ENTRY_NAME",
                "USE_DB_PARAMS",
            ]
        }
    if DEBUG:
        log_debug('GGC-2) get_general_config |' +
                  f' resultset: {resultset}')
    return resultset


def get_users_config(app_context: AppContext) -> dict:
    """
    Get all user's parameters.
    """
    resultset = get_default_resultset()
    user_data = app_context.get_user_data()
    resultset["resultset"] = {r["config_name"]: r["config_value"]
                              for r in user_data.get("users_config", [])}
    if DEBUG:
        log_debug('GUC-2) get_users_config |' +
                  f' resultset: {resultset}')
    return resultset


def get_config_from_db_raw(app_context: AppContext) -> dict:
    """
    Get all dynamic parameters (general and user's).
    """
    if DEBUG:
        log_debug('GCFDR-1) get_config_from_db_raw')
    resultset = get_default_resultset()
    # Get general config from db
    config_from_db = get_general_config(app_context)
    if config_from_db["error"]:
        return config_from_db
    resultset['resultset'] = dict(config_from_db['resultset'].items())
    # Get user's config from db
    config_from_db = get_users_config(app_context)
    if config_from_db["error"]:
        return config_from_db
    resultset['resultset'].update(dict(config_from_db['resultset'].items()))
    if DEBUG:
        log_debug('GCFDR-2) get_config_from_db_raw |' +
                  f' resultset: {resultset}')
    return resultset


def get_all_params(app_context: AppContext):
    """
    Get all dynamic parameters (general and user's).
    First try from the json cache files, if not found get it from the
    database.
    """
    if PARAMS_FILE_ENABLED != '1':
        return get_config_from_db_raw(app_context)

    user_id = app_context.get_user_id()
    pfc = ParamsFile(user_id)

    # Try general params from the json file
    params = get_default_resultset()
    filename = pfc.get_params_file_path(PARAMS_FILE_GENERAL_FILENAME)
    load_result = pfc.load_params_file(filename)
    if load_result["found"]:  # and load_result['resultset']:
        params['resultset'].update(load_result['resultset'])
        _ = DEBUG and log_debug(
            'GCFD-4) app_context_and_set_env |' +
            ' General parameters loaded from file:' +
            f' {load_result["resultset"]}')
    else:
        # Get general params from json
        load_result = get_general_config(app_context)
        if load_result["error"]:
            return load_result
        params['resultset'].update(load_result['resultset'])
        # Save general params to json
        pfc.save_params_file(filename, load_result['resultset'])

    # Try user's config from json file
    if user_id != NON_AUTH_REQUEST_USER_ID:
        filename = pfc.get_params_filename()
        load_result = pfc.load_params_file(filename)
        if load_result["found"]:  # and load_result['resultset']:
            params['resultset'].update(
                {r["config_name"]: r["config_value"]
                    for r in load_result['resultset'].get("users_config", [])}
            )
            _ = DEBUG and log_debug(
                'GCFD-5) app_context_and_set_env |' +
                ' User\'s parameters loaded from file:' +
                f' {load_result["resultset"].get("users_config", [])}')
        else:
            # Get user's config from db
            load_result = get_users_config(app_context)
            if load_result["error"]:
                return load_result
            params['resultset'].update(dict(load_result['resultset'].items()))
            # Does not save the json file because it's a job for AppContex...
    return params


def app_context_and_set_env(request: AuthorizedRequest, blueprint: Any
                            ) -> AppContext:
    """
    Set the Appcontext and get all the parameters
    (general and user's) to dynamic set environment variables
    configured from the database.

    Args:
        request (AuthorizedRequest): the request object

    Returns:
        AppContext: the application context object, with
        the request object, user ID, user's data and the
        other object to expapnd the session dat.
    """
    app_context = AppContext()
    app_context.set_context_from_blueprint(blueprint=blueprint,
                                           request=request)
    if app_context.has_error():
        log_error('GCFD-0) app_context_and_set_env ERROR:'
                  f' {app_context.get_error()}')
        return app_context
    _ = DEBUG and \
        log_debug('GCFD-1) app_context_and_set_env')
    # Get all the parameters (general and user's) from dynamic set (database)
    params = get_all_params(app_context=app_context)
    if params["error"]:
        log_debug('GCFD-3) ERROR: app_context_and_set_env |' +
                  f' params: {params}')
        app_context.set_error(params["error_message"])
        return app_context
    for key, value in params['resultset'].items():
        # Set the environmet variable in the app_context
        # Previously it was "os.environ[key] = value" but it
        # carries a lot of issues...
        app_context.set_env_var(var_name=key, value=value)
    _ = DEBUG and \
        log_debug('GCFD-2) app_context_and_set_env |' +
                  f' Parameters set as os.environ(): {params["resultset"]}')
    return app_context


def set_init_custom_data(data: Optional[Union[dict, None]] = None):
    """
    Sets the custom data for the FastAPI/Flask/Chalice App.
    """
    result = dict(data.items()) if data else {}
    # Standard GenericDbHelper specific functions registry
    result['delete_params_file'] = delete_params_file
    _ = DEBUG and log_debug(f"//// Custom data: {result}")
    return result
