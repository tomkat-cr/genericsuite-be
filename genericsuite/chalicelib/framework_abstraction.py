"""
Chalice abstraction layer
"""
# from chalice import Request as ChaliceRequest, Response as ChaliceResponse
import os
import importlib

DEBUG = False
FRAMEWORK_LOADED = False
FRAMEWORK = os.environ.get('CURRENT_FRAMEWORK', '').lower()
if FRAMEWORK == 'chalice':
    try:
        framework_module = importlib.import_module(FRAMEWORK)
        FRAMEWORK_LOADED = True
        if DEBUG:
            print(f'Chalicelib abstraction | framework_module: {framework_module}')


        class FrameworkClass(framework_module.Chalice):
            """
            Framkework class cloned from the selected framework super class.
            """


        class Request(framework_module.app.Request):
            """
            Request class cloned from the selected Request framework super class.
            This class is the one to be imported by the project modules
            """


        class Response(framework_module.app.Response):
            """
            Response class cloned from the selected Response framework super class.
            This class is the one to be imported by the project modules
            """


        class Blueprint(framework_module.app.Blueprint):
            """
            Blueprint class cloned from the selected Blueprint framework super class.
            This class is the one to be imported by the project modules
            """

    except ImportError as err:
        raise ImportError(f"Unable to import '{FRAMEWORK}': {err}") from None
