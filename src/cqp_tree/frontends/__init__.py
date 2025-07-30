import importlib
import os

# All sub-directories in here are expected to be a module holding a frontend.
# As part of the frontend module, there should be a @translator decorated function.
# Its definition will also register the frontend for use elsewhere.


def load_submodules():
    directory = os.path.dirname(__file__)

    for frontend in os.listdir(directory):
        if os.path.isdir(os.path.join(directory, frontend)):
            importlib.import_module(f'.{frontend}', __package__)


load_submodules()
