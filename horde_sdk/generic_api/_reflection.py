import inspect
import sys

from horde_sdk.generic_api.apimodels import BaseRequest


def get_all_request_types(package_name: str) -> list[type[BaseRequest]]:
    """Return all non-abstract class types inheriting from `BaseRequest` by searching the package."""
    all_request_types: list[type[BaseRequest]] = []
    for _, obj in inspect.getmembers(sys.modules[package_name], inspect.isclass):
        if inspect.isabstract(obj):
            continue
        if not issubclass(obj, BaseRequest):
            continue
        all_request_types.append(obj)
    return all_request_types
