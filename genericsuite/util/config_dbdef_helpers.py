# Desc: Helper functions for config_dbdef
from typing import Optional, Union
import json
import os

from genericsuite.config.config import Config
from genericsuite.util.utilities import log_debug

DEBUG = False
settings = Config()


def get_json_def(
    json_file_name: str,
    dir_name: str = '',
    default_value: Optional[Union[dict, list, None]] = None
# ) -> dict:
) -> Union[dict, list]:
    """
    Get JSON definition from file.

    Args:
        json_file_name (str): Name of the JSON file.
        dir_name (str, optional): Directory name. Defaults to ''.
        default_value (dict, optional): Default value. Defaults to None.

    Returns:
        dict: JSON definition.
    """
    if not default_value:
        default_value = {}

    app_path = os.getcwd()
    filename = f'{app_path}/{dir_name}/{json_file_name}.json'
    if not os.path.isfile(filename):
        if DEBUG:
            log_debug(f'File {filename} not found.')
        return default_value
    with open(filename, encoding="utf-8") as json_file:
        fe_db_def = json.load(json_file)
    return fe_db_def


def get_json_def_both(json_file_name: str) -> dict:
    """Get JSON definition from both frontend and backend.

    Args:
        json_file_name (str): Name of the JSON file.

    Returns:
        dict: JSON definition.
    """
    cnf_db_base_path = settings.GIT_SUBMODULE_LOCAL_PATH
    cnf_db = get_json_def(json_file_name, f'{cnf_db_base_path}/frontend', None)
    second_json = get_json_def(json_file_name, f'{cnf_db_base_path}/backend', None)
    if second_json:
        if not cnf_db:
            cnf_db = second_json.copy()
        elif isinstance(cnf_db, dict):
            cnf_db.update(second_json)
        else:
            cnf_db += second_json
    if not cnf_db:
        cnf_db = {}
    # log_debug(f'>>> CNF_DB\n| json_file_name: {json_file_name}\n| cnf_db: {cnf_db}')
    return cnf_db
