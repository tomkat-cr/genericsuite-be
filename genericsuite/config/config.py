"""
Configuration manager
"""
# C0103 | Disable "name doesn't conform to naming rules..." (snake_case)
# pylint: disable=C0103
# R0902 | Disable "too-many-instance-attributes"
# pylint: disable=R0902
# R0903 | Disable "too-few-public-methods"
# pylint: disable=R0903
# R0915 | Disable "too-many-statements "
# pylint: disable=R0915
# W0105 | Disable "pointless-string-statement" (for """ comments)
# pylint: disable=W0105
# C0301: | Disable "line-too-long"
# pylint: disable=C0301

from typing import Union, Any
import os
import json
import logging
import datetime


def formatted_log_message(message: str) -> str:
    """ Returns a formatted message with database name and date/time """
    return f"[{os.environ['APP_DB_NAME']}]" + \
        f" {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}" + \
        f" | {message}"


def log_config_error(message: str) -> None:
    """
    Log a message to the console.
    """
    logger = logging.getLogger(os.environ.get('APP_NAME'))
    logger.error("%s", formatted_log_message(message))


def text_to_dict(text: str) -> Union[dict, None]:
    """
    Convert a text string to a dictionary.
    """
    result = None
    try:
        result = json.loads(text)
    except json.JSONDecodeError as e:
        log_config_error(f'ERROR [C-E010] | converting text to dict: {e}')
    return result


class Config():
    """ Configuration class, to have the most used App variables """
    def __init__(self, app_context: Any = None) -> None:

        # Set the local app_context to eventually get values from
        # Database (any other place than the App initialization)
        self.app_context = app_context

        # ............................

        # IMPORTANT: these parameters values must be always retrieved
        # from environment variables

        # Database configuration

        self.DB_CONFIG = {
            'mongodb_uri': os.environ.get('APP_DB_URI'),
            'mongodb_db_name': os.environ.get('APP_DB_NAME'),
            'dynamdb_prefix': '_test_',
        }
        # DB_ENGINE = 'MONGO_DB'
        # DB_ENGINE = 'DYNAMO_DB'
        self.DB_ENGINE = os.environ.get('APP_DB_ENGINE')

        # App general configuration

        self.DEBUG = self.get_env('APP_DEBUG', '0') == '1'

        self.APP_NAME = os.environ.get('APP_NAME')
        self.APP_VERSION = os.environ.get('APP_VERSION', 'N/A')
        self.STAGE = os.environ.get('APP_STAGE')
        self.SECRET_KEY = os.environ.get('SECRET_KEY', str(os.urandom(16)))

        # App specific configuration

        self.APP_SECRET_KEY = os.environ.get('APP_SECRET_KEY')
        self.APP_SUPERADMIN_EMAIL = \
            os.environ.get('APP_SUPERADMIN_EMAIL')

        self.GIT_SUBMODULE_LOCAL_PATH = os.environ.get('GIT_SUBMODULE_LOCAL_PATH')

        # ............................

        # Auth parameters

        self.CORS_ORIGIN = self.get_env('APP_CORS_ORIGIN', '*')
        self.FRONTEND_AUDIENCE = self.get_env('APP_FRONTEND_AUDIENCE', '')
        self.HEADER_TOKEN_ENTRY_NAME = self.get_env(
            'HEADER_TOKEN_ENTRY_NAME',
            'Authorization'  # 'x-access-tokens'
        )

        # Languages

        self.DEFAULT_LANG = self.get_env('DEFAULT_LANG', 'en')


    def get_env(self, var_name: str, def_value: Any = None) -> Any:
        """
        Get value of a config variable. If it's in the app_context,
        get from there, if not, get from os.environ.
        """
        result = os.environ.get(var_name, def_value)
        if self.app_context:
            result = self.app_context.get_env_var(
                var_name=var_name,
                def_value=result,
            )
        return result
        # return getattr(self, var_name)

    def debug_vars(self) -> str:
        """
        Show all defined config variables.
        """
        return (
            'Config.debug_vars:\n\n' +
            f'DEBUG = {self.DEBUG}\n' +
            f'SECRET_KEY = {self.SECRET_KEY}\n' +
            f'DB_CONFIG = {self.DB_CONFIG}\n' +
            f'DB_ENGINE = {self.DB_ENGINE}\n' +
            f'APP_SECRET_KEY = {self.APP_SECRET_KEY}\n' +
            f'APP_SUPERADMIN_EMAIL = {self.APP_SUPERADMIN_EMAIL}\n' +
            f'CORS_ORIGIN = {self.CORS_ORIGIN}\n' +
            f'FRONTEND_AUDIENCE = {self.FRONTEND_AUDIENCE}\n' +
            f'HEADER_TOKEN_ENTRY_NAME = {self.HEADER_TOKEN_ENTRY_NAME}\n' +
            f'STAGE = {self.STAGE}\n' +
            '\n'
        )
