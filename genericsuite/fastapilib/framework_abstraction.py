"""
FastAPI abstraction layer
"""
# from fastapi import Request as FastAPIRequest, Response as FastAPIResponse,
#     Blueprint as FastAPIBlueprint
import os
import importlib

DEBUG = False
FRAMEWORK_LOADED = False
FRAMEWORK = os.environ.get('CURRENT_FRAMEWORK', '').lower()
if FRAMEWORK == 'fastapi':
    try:
        framework_module = importlib.import_module(FRAMEWORK)
        FRAMEWORK_LOADED = True
        if DEBUG:
            print(f'FastAPI abstraction | framework_module: {framework_module}')


        class FrameworkClass(framework_module.FastAPI):
            """
            Framkework class cloned from the selected framework super class.
            """


        class Request():
            """
            Request class cloned from the selected Request framework super class.
            This class is the one to be imported by the project modules
            """


        class Response():
            """
            Response class cloned from the selected Response framework super class.
            This class is the one to be imported by the project modules
            """


        class Blueprint(framework_module.APIRouter):
            """
            Blueprint class cloned from the selected Blueprint framework super class.
            This class is the one to be imported by the project modules
            """

    except ImportError as err:
        raise ImportError(f"Unable to import '{FRAMEWORK}': {err}") from None
