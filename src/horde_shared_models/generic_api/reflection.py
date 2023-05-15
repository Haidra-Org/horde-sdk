import inspect
import sys

from .apimodels import BaseRequest


def getAllRequestTypes(moduleName: str) -> list[type[BaseRequest]]:
    """Returns all non-abstract classes inheriting from `BaseRequest`.

    Args:
        moduleName (str): The target module name to reflect.

    Returns:
        list[type[BaseRequest]]: All types inheriting from `BaseRequest`.
    """
    listOfTypes = []
    for value in sys.modules[moduleName].__dict__.values():
        if isinstance(value, type) and issubclass(value, BaseRequest) and not inspect.isabstract(value):
            listOfTypes.append(value)

    return listOfTypes
