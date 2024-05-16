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
)
from genericsuite.util.app_logger import log_debug, log_error
from genericsuite.util.generic_db_middleware import (
    fetch_all_from_db,
)
from genericsuite.util.jwt import AuthorizedRequest
from genericsuite.util.utilities import get_default_resultset

DEBUG = True
USE_DB_PARAMS_DEFAULT = os.environ.get('USE_DB_PARAMS_DEFAULT', "1")
# USE_DB_PARAMS_DEFAULT = "0"     # Usefull when local dev environment becomes slow


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


def app_context_and_set_env(request: AuthorizedRequest, blueprint: Any) -> AppContext:
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
    app_context.set_context_from_blueprint(blueprint=blueprint, request=request)
    pfc = ParamsFile(app_context.get_user_id())
    if app_context.has_error():
        log_error('GCFD-0) app_context_and_set_env ERROR:'
                  f' {app_context.get_error()}')
        return app_context
    if DEBUG:
        log_debug('GCFD-1) app_context_and_set_env')
    params = pfc.load_params_file()
    if params["found"] and params['resultset'].get('params'):
        if DEBUG:
            log_debug('GCFD-4) app_context_and_set_env |' +
                      f' Parameters loaded from file: {params["resultset"]}')
    else:
        params = get_config_from_db_raw(app_context)
        if params["error"]:
            log_debug('GCFD-3) ERROR: app_context_and_set_env |' +
                    f' params: {params}')
            app_context.set_error(params["error_message"])
            return app_context
        params = pfc.save_params_file(params['resultset'], app_context.get_user_data())
    for key, value in params['resultset']['params'].items():
        # Set the environmet variable in the app_context
        # Previously it was "os.environ[key] = value" but it
        # carries a lot of issues...
        app_context.set_env_var(var_name=key, value=value)
    if DEBUG:
        log_debug('GCFD-2) app_context_and_set_env |' +
                  f' Parameters set as os.environ(): {params["resultset"]}')
    return app_context


def set_init_custom_data(data: Optional[Union[dict, None]] = None):
    """
    Sets the custom data for the FastAPI/Flask/Chalice App.
    """
    data = data or {}
    result = data.copy()
    # Standard GenericDbHelper specific functions registry
    result['delete_params_file'] = delete_params_file
    if DEBUG:
        log_debug(f"Custom data: {result}")
    return result
