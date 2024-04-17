import importlib
import inspect
import pkgutil
import types

import horde_sdk
import horde_sdk.ai_horde_api
import horde_sdk.ai_horde_api.apimodels
import horde_sdk.ai_horde_worker
import horde_sdk.ratings_api
import horde_sdk.ratings_api.apimodels


def find_subclasses(module_or_package: types.ModuleType, super_type: type) -> list[type]:
    subclasses: list[type] = []

    # If this is a module, we need to get the package name
    if hasattr(module_or_package, "__package__") and module_or_package.__package__ is not None:
        module_or_package = importlib.import_module(module_or_package.__package__)

    for _importer, modname, _ispkg in pkgutil.walk_packages(
        path=module_or_package.__path__,
        prefix=module_or_package.__name__ + ".",
        onerror=lambda x: None,
    ):
        module = importlib.import_module(modname)
        for _name, obj in inspect.getmembers(module):
            if (
                inspect.isclass(obj)
                and issubclass(obj, super_type)
                and obj != super_type
                and not inspect.isabstract(obj)
            ):
                subclasses.append(obj)
    return subclasses


all_found_classes: list[type] = find_subclasses(horde_sdk, horde_sdk.HordeAPIObject)

# Create a dict to map the class name to the class
found_class_name_to_class = {cls.__name__: cls for cls in all_found_classes}

api_models_modules = [
    horde_sdk.ai_horde_api.apimodels,
    # horde_sdk.ratings_api.apimodels,
]

# Create a dict for each module with a list of mapped classes
module_found_classes = {module: find_subclasses(module, horde_sdk.HordeAPIObject) for module in api_models_modules}


def any_unimported_classes(module: types.ModuleType) -> tuple[bool, set[type]]:
    """Check if any classes in the module have not been imported yet.

    Args:
        module (types.ModuleType): The module to check.

    Returns:
        tuple[bool, set[type]]: A tuple with a boolean indicating if there are any unimported classes and a set of the
        unimported classes.
    """
    if module not in module_found_classes:
        module_found_classes[module] = find_subclasses(module, horde_sdk.HordeAPIObject)

    missing_classes = set()

    for cls in module_found_classes[module]:
        if cls.__name__ not in module.__all__:
            missing_classes.add(cls)

    if len(missing_classes) > 0:
        return True, missing_classes

    return False, missing_classes
