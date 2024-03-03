"""
Constant tables (dict)
"""
from typing import Any
from genericsuite.util.config_dbdef_helpers import get_json_def_both


def get_all_constants() -> dict:
    """
    Get all constants from the json files: general_constants.json
    and app_constants.json

    Returns:
        dict: a dict with all constants attributes in the json files.
    """
    result = get_json_def_both("general_constants")
    result.update(get_json_def_both("app_constants"))
    return result


def get_constant(const_name: str, entry_name: str = None,
                 def_value: Any = None) -> Any:
    """
    Get a constant value from the constants attribute const_name.
    If the entry_name is not found in the constants attribute,
    returns the def_value.
    If the entry_name is None, returns all the constants attribute content.

    Args:
        const_name (str): Constant's attribute name
        entry_name (str): Entry name to be found in the constant's attribute
        name.
        def_value (Any): default value when the entry name is not found.
        Defaults to None.

    Returns:
        Any: the constant value from the constants attribute or the default
        value if it doesn't exist. If the entry_name is None, returns all
        the constants attribute content.
    """
    if not entry_name:
        return constants[const_name]
    return constants[const_name].get(entry_name, def_value)


constants = get_all_constants()
