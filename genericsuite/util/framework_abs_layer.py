"""
Framework abstraction layer
"""
import os
import importlib

DEFAULT_FRAMEWORK = ''

def get_current_framework():
    """
    Get the current framework
    """
    return os.environ.get('CURRENT_FRAMEWORK', DEFAULT_FRAMEWORK)


framework = os.environ.get('CURRENT_FRAMEWORK', DEFAULT_FRAMEWORK).lower()
if framework not in ['chalice', 'fastapi', 'flask']:
    raise ValueError("Unsupported or undefined CURRENT_FRAMEWORK:" +
                     f" '{framework}'")

module_base_path = f"genericsuite.{framework}lib"
module_path = f"{module_base_path}.framework_abstraction"

try:
    framework_module = importlib.import_module(module_path)
    if not framework_module or not framework_module.FRAMEWORK_LOADED:
        raise ImportError(f"Framework '{module_path}' could no be loaded" +
            " [FAL-E010]" +
            f" | FRAMEWORK_LOADED={framework_module.FRAMEWORK_LOADED}")
except ImportError as err:
    raise ImportError(f"Unable to import module [1]: {err}") from None

try:
    create_app_path = f'{module_base_path}.util.create_app'
    module_create_app = importlib.import_module(create_app_path)
except ImportError as err:
    raise ImportError(f"Unable to import module [2]: {err}") from None


class FrameworkClass(framework_module.FrameworkClass):
    """
    Framkework class cloned from the selected framework super class.
    E.g. chalice, fastapi, flask:
        from flask import Flask
        from fastapi import FastAPI
        from chalice import Chalice
    Will be:
        from genericsuite.util.framework_abs_layer import FrameworkClass as Flask
        from genericsuite.util.framework_abs_layer import FrameworkClass as FastAPI
        from genericsuite.util.framework_abs_layer import FrameworkClass as Chalice
    This class is the one to be imported by the project modules.
    """


class Request(framework_module.Request):
    """
    Request class cloned from the selected Request framework super class.
    This class is the one to be imported by the project modules.
    """


class Response(framework_module.Response):
    """
    Response class cloned from the selected Response framework super class.
    This class is the one to be imported by the project modules.
    """


class Blueprint(framework_module.Blueprint):
    """
    Blueprint class cloned from the selected Blueprint framework super class.
    This class is the one to be imported by the project modules.
    """


class BlueprintOne(framework_module.BlueprintOne):
    """
    Blueprint wrapper to add authorization, other data and schema validation
    to requests.
    """
