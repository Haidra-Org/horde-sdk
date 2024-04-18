import importlib
import inspect
import pkgutil
import types
from functools import cache

import horde_sdk
import horde_sdk.ai_horde_api
import horde_sdk.ai_horde_api.apimodels
import horde_sdk.ai_horde_worker
import horde_sdk.ratings_api
import horde_sdk.ratings_api.apimodels
from horde_sdk import HordeAPIDataObject, HordeAPIObject
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_API_ENDPOINT_SUBPATH, get_ai_horde_swagger_url
from horde_sdk.generic_api.utils.swagger import SwaggerParser


@cache
def find_subclasses(module_or_package: types.ModuleType, super_type: type) -> list[type]:
    subclasses: list[type] = []

    if hasattr(module_or_package, "__package__") and module_or_package.__package__ is not None:
        module_or_package = importlib.import_module(module_or_package.__package__)

    for _importer, modname, _ispkg in pkgutil.walk_packages(
        path=module_or_package.__path__,
        prefix=module_or_package.__name__ + ".",
        onerror=lambda x: None,
    ):
        module = importlib.import_module(modname)
        for name in dir(module):
            obj = getattr(module, name)
            if (
                isinstance(obj, type)
                and issubclass(obj, super_type)
                and obj is not super_type
                and not inspect.isabstract(obj)
            ):
                subclasses.append(obj)
    return subclasses


module_found_classes: dict[types.ModuleType, dict[type, list[type]]] = {
    horde_sdk.ai_horde_api.apimodels: {
        HordeAPIObject: find_subclasses(horde_sdk.ai_horde_api.apimodels, HordeAPIObject),
        HordeAPIDataObject: find_subclasses(horde_sdk.ai_horde_api.apimodels, HordeAPIDataObject),
    },
}


def any_unimported_classes(module: types.ModuleType, super_type: type) -> tuple[bool, set[type]]:
    """Check if any classes in the module are not imported in the `__init__.py` of the apimodels namespace.

    Args:
        module (types.ModuleType): The module to check.
        super_type (type): The super type of the classes to check.

    Returns:
        tuple[bool, set[type]]: A tuple with a boolean indicating if there are any unimported classes and a set of the
        unimported classes.
    """
    if module not in module_found_classes:
        module_found_classes[module] = {
            super_type: find_subclasses(module, super_type),
        }

    if super_type not in module_found_classes[module]:
        module_found_classes[module][super_type] = find_subclasses(module, super_type)

    missing_classes = set()

    for class_type in module_found_classes[module][super_type]:
        if class_type.__name__ not in module.__all__:
            missing_classes.add(class_type)

    return bool(missing_classes), missing_classes


def all_undefined_classes(module: types.ModuleType) -> dict[str, str]:
    """Return all of the models defined on the API but not in the SDK."""
    if module not in module_found_classes:
        module_found_classes[module] = {
            HordeAPIObject: find_subclasses(module, HordeAPIObject),
            HordeAPIDataObject: find_subclasses(module, HordeAPIDataObject),
        }

    defined_api_object_names: set[str] = set()

    for class_type in module_found_classes[module][HordeAPIObject]:
        if not issubclass(class_type, HordeAPIObject):
            raise TypeError(f"Expected {class_type} to be a HordeAPIObject")

        api_model_name = class_type.get_api_model_name()
        if api_model_name is not None:
            defined_api_object_names.add(api_model_name)

    undefined_classes: dict[str, str] = {}

    parser = SwaggerParser(swagger_doc_url=get_ai_horde_swagger_url())
    swagger_doc = parser.get_swagger_doc()

    for path, swagger_endpoint in swagger_doc.paths.items():
        endpoint_request_models: list[str] = swagger_endpoint.get_all_request_models()
        endpoint_response_models: list[str] = swagger_endpoint.get_all_response_models()

        for model_name in endpoint_request_models + endpoint_response_models:
            if model_name not in defined_api_object_names:
                undefined_classes[model_name] = path

    return undefined_classes


def all_unknown_endpoints_ai_horde() -> set[str]:
    """Return all of the endpoints defined on the API but not in the SDK."""
    parser = SwaggerParser(swagger_doc_url=get_ai_horde_swagger_url())
    swagger_doc = parser.get_swagger_doc()

    known_paths = set(AI_HORDE_API_ENDPOINT_SUBPATH.__members__.values())
    unknown_paths = set()

    for path, _swagger_endpoint in swagger_doc.paths.items():
        if path not in known_paths:
            print(f"Unknown path: {path}")
            unknown_paths.add(path)

    return unknown_paths
