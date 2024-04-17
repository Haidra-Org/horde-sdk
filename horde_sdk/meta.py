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
