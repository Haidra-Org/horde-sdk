import inspect
import sys

from .apimodels import BaseRequest


def get_all_request_types(module_name: str) -> list[type[BaseRequest]]:
    """Returns all non-abstract class types inheriting from `BaseRequest`.

    Args:
        moduleName (str): The target module name to reflect.

    Returns:
        list[type[BaseRequest]]: All types inheriting from `BaseRequest`.
    """
    list_of_types = []
    for value in sys.modules[module_name].__dict__.values():
        if isinstance(value, type) and issubclass(value, BaseRequest) and not inspect.isabstract(value):
            list_of_types.append(value)

    return list_of_types
