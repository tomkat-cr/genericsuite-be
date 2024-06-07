
"""
Flask abstraction layer
"""
import os
import importlib

# https://stackoverflow.com/questions/47277374/flask-get-current-blueprint-webroot
from flask import Blueprint as FlaskBlueprint


DEBUG = False
FRAMEWORK_LOADED = False
FRAMEWORK = os.environ.get('CURRENT_FRAMEWORK', '').lower()
if FRAMEWORK == 'flask':
    try:
        framework_module = importlib.import_module(FRAMEWORK)
        FRAMEWORK_LOADED = True
        if DEBUG:
            print(f'Flask abstraction | framework_module: {framework_module}')


        class FrameworkClass(framework_module.Flask):
            """
            Framkework class cloned from the selected framework super class.
            """


        class Request(framework_module.request):
            """
            Request class cloned from the selected Request framework super class.
            This class is the one to be imported by the project modules
            """


        class Response(framework_module.response):
            """
            Response class cloned from the selected Response framework super class.
            This class is the one to be imported by the project modules
            """


        # class Blueprint(framework_module.Blueprint):
        class Blueprint(FlaskBlueprint):
            """
            Blueprint class cloned from the selected Blueprint framework super class.
            This class is the one to be imported by the project modules
            """


        class BlueprintOne(Blueprint):
            """
            Class to register a new route with optional schema validation and authorization.
            """

    except ImportError as err:
        raise ImportError(f"Unable to import '{FRAMEWORK}': {err}") from None
