import importlib
import inspect
import pkgutil
import types
from functools import cache

import horde_sdk
import horde_sdk.ai_horde_api
import horde_sdk.ai_horde_api.apimodels
import horde_sdk.generic_api
import horde_sdk.generic_api.apimodels
import horde_sdk.ratings_api
import horde_sdk.ratings_api.apimodels
import horde_sdk.worker
from horde_sdk import HordeAPIObject, HordeRequest
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_API_ENDPOINT_SUBPATH, get_ai_horde_swagger_url
from horde_sdk.consts import _ANONYMOUS_MODEL, HTTPMethod, HTTPStatusCode
from horde_sdk.generic_api.apimodels import HordeAPIData, HordeResponse
from horde_sdk.generic_api.utils.swagger import SwaggerParser


@cache
def find_subclasses(module_or_package: types.ModuleType, super_type: type) -> list[type]:
    """Find all subclasses of a given type in a module or package.

    Args:
        module_or_package (types.ModuleType): The module or package to search in.
        super_type (type): The super type of the classes to search for.

    Returns:
        list[type]: A list of all the subclasses of the super type in the module or package.
    """
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


def any_unimported_classes(module: types.ModuleType, super_type: type) -> tuple[bool, set[type]]:
    """Check if any classes in the module are not imported in the `__init__.py` of the apimodels namespace.

    Args:
        module (types.ModuleType): The module to check.
        super_type (type): The super type of the classes to check.

    Returns:
        tuple[bool, set[type]]: A tuple with a boolean indicating if there are any unimported classes and a set of the
        unimported classes.
    """
    module_found_classes = find_subclasses(module, super_type)

    missing_classes = set()

    for class_type in module_found_classes:
        if class_type.__name__ not in module.__all__:
            missing_classes.add(class_type)

    return bool(missing_classes), missing_classes


def all_undefined_classes(module: types.ModuleType) -> list[str]:
    """Return all of the models defined on the API but not in the SDK."""
    module_found_classes = find_subclasses(module, HordeAPIObject)

    defined_api_object_names: set[str] = set()

    for class_type in module_found_classes:
        if not issubclass(class_type, HordeAPIObject):
            raise TypeError(f"Expected {class_type} to be a HordeAPIObject")

        api_model_name = class_type.get_api_model_name()
        if api_model_name is not None:
            defined_api_object_names.add(api_model_name)

    undefined_classes: list[str] = []

    parser = SwaggerParser(swagger_doc_url=get_ai_horde_swagger_url())
    swagger_doc = parser.get_swagger_doc()

    all_api_objects = set(swagger_doc.definitions.keys())
    missing_object_names = all_api_objects - defined_api_object_names

    for object_name in missing_object_names:
        undefined_classes.append(object_name)

    return undefined_classes


def all_undefined_classes_for_endpoints(module: types.ModuleType) -> dict[str, str]:
    """Return all of the models defined on the API but not in the SDK."""
    module_found_classes = find_subclasses(module, HordeAPIObject)

    defined_api_object_names: set[str] = set()

    for class_type in module_found_classes:
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
    """Return all of the endpoints defined on the API but not known by the SDK."""
    parser = SwaggerParser(swagger_doc_url=get_ai_horde_swagger_url())
    swagger_doc = parser.get_swagger_doc()

    known_paths = set(AI_HORDE_API_ENDPOINT_SUBPATH.__members__.values())
    unknown_paths = set()

    for path, _swagger_endpoint in swagger_doc.paths.items():
        if path not in known_paths:
            print(f"Unknown path: {path}")
            unknown_paths.add(path)

    return unknown_paths


def all_unaddressed_endpoints_ai_horde() -> set[AI_HORDE_API_ENDPOINT_SUBPATH]:
    """Return all of the endpoints known by the SDK but with no corresponding request."""
    known_paths = set(AI_HORDE_API_ENDPOINT_SUBPATH.__members__.values())
    known_paths.remove(AI_HORDE_API_ENDPOINT_SUBPATH.swagger)
    unaddressed_paths = set()

    all_classes = find_subclasses(horde_sdk.ai_horde_api.apimodels, HordeRequest)

    all_classes_paths = {cls.get_api_endpoint_subpath() for cls in all_classes if issubclass(cls, HordeRequest)}

    for path in known_paths:
        if path not in all_classes_paths:
            unaddressed_paths.add(path)

    return unaddressed_paths


def all_models_missing_docstrings() -> set[type]:
    """Return all of the models that do not have docstrings."""
    all_classes = find_subclasses(horde_sdk.ai_horde_api.apimodels, HordeAPIObject)
    all_classes += find_subclasses(horde_sdk.ai_horde_api.apimodels, HordeAPIData)

    all_classes = list(set(all_classes))

    missing_docstrings = set()

    for class_type in all_classes:
        if not class_type.__doc__:
            missing_docstrings.add(class_type)

    return missing_docstrings


def all_model_and_fields_missing_docstrings() -> dict[type, set[str]]:
    """Return all of the models' fields that do not have docstrings."""
    all_classes = find_subclasses(horde_sdk.generic_api.apimodels, HordeAPIObject)
    all_classes += find_subclasses(horde_sdk.generic_api.apimodels, HordeAPIData)
    all_classes += find_subclasses(horde_sdk.ai_horde_api.apimodels, HordeAPIObject)
    all_classes += find_subclasses(horde_sdk.ai_horde_api.apimodels, HordeAPIData)

    all_classes = list(set(all_classes))

    missing_docstrings: dict[type, set[str]] = {}

    from pydantic import BaseModel

    for class_type in all_classes:
        if not issubclass(class_type, BaseModel):
            continue

        missing_fields = set()
        for field_name, field_info in class_type.model_fields.items():
            if not field_info.description:
                missing_fields.add(field_name)

        if missing_fields:
            missing_docstrings[class_type] = missing_fields

    return missing_docstrings


class FoundResponseInfo:
    """A class to store information about a found response class (type)."""

    def __init__(
        self,
        *,
        response: type[HordeResponse],
        api_model_name: str | None,
        parent_request: type[HordeRequest],
        http_status_code: HTTPStatusCode,
        endpoint: str,
        http_method: HTTPMethod,
    ) -> None:
        self.response = response
        self.api_model_name = api_model_name
        self.parent_request = parent_request
        self.http_status_code = http_status_code
        self.endpoint = endpoint
        self.http_method = http_method

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FoundResponseInfo):
            return False

        return (
            self.response is other.response
            and self.api_model_name == other.api_model_name
            and self.parent_request is other.parent_request
            and self.http_status_code == other.http_status_code
            and self.endpoint == other.endpoint
            and self.http_method == other.http_method
        )

    def __hash__(self) -> int:
        return hash((self.response, self.parent_request, self.http_status_code, self.endpoint, self.http_method))


class FoundMixinInfo:
    """A class to store information about a found mixin class (type)."""

    def __init__(
        self,
        *,
        mixin: type,
        api_model_name: str | None,
    ) -> None:
        self.mixin = mixin
        self.api_model_name = api_model_name

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FoundMixinInfo):
            return False

        return self.mixin is other.mixin and self.api_model_name == other.api_model_name

    def __hash__(self) -> int:
        return hash((self.mixin, self.api_model_name))


def all_models_non_conforming_docstrings() -> dict[type, tuple[str | None, str | None]]:
    """Return all of the models that do not have a v2 API model."""
    all_classes: list[type[HordeAPIObject] | type[HordeAPIData]]
    all_classes = find_subclasses(horde_sdk.ai_horde_api.apimodels, HordeAPIObject)

    request_docstring_template = "Represents a {http_method} request to the {endpoint} endpoint."
    response_docstring_template_single = (
        "Represents the data returned from the {endpoint} endpoint with http status code {http_status_code}."
    )
    endpoint_status_codes_pairs_template = (
        "        - {endpoint} | {request_type} [{http_method}] -> {http_status_code}\n"
    )
    response_docstring_template_multiple = (
        "Represents the data returned from the following endpoints and http "
        "status codes:\n{endpoint_status_codes_pairs}"
    )

    v2_api_model_template = "\n\n    v2 API Model: `{api_model}`"

    non_conforming_requests: dict[type, tuple[str | None, str | None]] = {}
    non_conforming_responses: dict[type, tuple[str | None, str | None]] = {}
    non_conforming_other: dict[type, tuple[str | None, str | None]] = {}

    request_response_map: dict[type[HordeRequest], list[FoundResponseInfo]] = {}
    response_request_map: dict[type[HordeResponse], list[FoundResponseInfo]] = {}

    def process_request(class_type: type[HordeRequest]) -> None:
        request_response_map[class_type] = []

        http_method = class_type.get_http_method()
        endpoint = class_type.get_api_endpoint_subpath()

        expected_request_docstring = request_docstring_template.format(
            http_method=http_method,
            endpoint=endpoint,
        )

        request_api_model_name = class_type.get_api_model_name()

        if request_api_model_name is not None:
            expected_request_docstring += v2_api_model_template.format(api_model=request_api_model_name)

        if not class_type.__doc__ or not class_type.__doc__.rstrip().endswith(expected_request_docstring):
            non_conforming_requests[class_type] = (class_type.__doc__, expected_request_docstring)

        for response_status_code, response_type in sorted(class_type.get_success_status_response_pairs().items()):
            if not issubclass(response_type, HordeResponse):
                raise TypeError(f"Expected {response_type} to be a HordeResponse")

            found_response_info = FoundResponseInfo(
                response=response_type,
                api_model_name=response_type.get_api_model_name(),
                parent_request=class_type,
                http_status_code=response_status_code,
                endpoint=endpoint,
                http_method=http_method,
            )

            request_response_map[class_type].append(found_response_info)

            if response_type not in response_request_map:
                response_request_map[response_type] = []

            response_request_map[response_type].append(found_response_info)

    def process_response(response_request_infos: list[FoundResponseInfo]) -> None:
        endpoint_status_codes_pairs = ""

        if len(response_request_infos) == 1:
            response_request_info = response_request_infos[0]

            endpoint_status_codes_pairs += endpoint_status_codes_pairs_template.format(
                endpoint=response_request_info.endpoint,
                request_type=response_request_info.parent_request.__name__,
                http_method=response_request_info.http_method,
                http_status_code=response_request_info.http_status_code,
            )

            expected_response_docstring = response_docstring_template_single.format(
                endpoint=response_request_info.endpoint,
                http_status_code=response_request_info.http_status_code,
            )

            if response_request_info.api_model_name:
                expected_response_docstring += v2_api_model_template.format(
                    api_model=response_request_info.api_model_name,
                )

            found_response_type = response_request_info.response

            if not found_response_type.__doc__ or not found_response_type.__doc__.rstrip().endswith(
                expected_response_docstring,
            ):
                non_conforming_responses[found_response_type] = (
                    found_response_type.__doc__,
                    expected_response_docstring,
                )

        else:
            last_response_request_info: FoundResponseInfo | None = None
            for response_request_info in response_request_infos:
                if (
                    last_response_request_info is not None
                    and last_response_request_info.endpoint == response_request_info.endpoint
                    and last_response_request_info.http_method == response_request_info.http_method
                    and last_response_request_info.http_status_code == response_request_info.http_status_code
                ):
                    continue

                last_response_request_info = response_request_info
                endpoint_status_codes_pairs += endpoint_status_codes_pairs_template.format(
                    endpoint=response_request_info.endpoint,
                    request_type=response_request_info.parent_request.__name__,
                    http_method=response_request_info.http_method,
                    http_status_code=response_request_info.http_status_code,
                )

            expected_response_docstring = response_docstring_template_multiple.format(
                endpoint_status_codes_pairs=endpoint_status_codes_pairs,
            )

            if response_request_info.api_model_name:
                expected_response_docstring = expected_response_docstring.rstrip()
                expected_response_docstring += v2_api_model_template.format(
                    api_model=response_request_info.api_model_name,
                )

            for response_request_info in response_request_infos:
                found_response_type = response_request_info.response

                if not found_response_type.__doc__ or not found_response_type.__doc__.rstrip().endswith(
                    expected_response_docstring,
                ):
                    non_conforming_responses[found_response_type] = (
                        found_response_type.__doc__,
                        expected_response_docstring,
                    )

    def process_other(class_type: type[HordeAPIObject]) -> None:
        api_model_name = class_type.get_api_model_name()

        expected_other_docstring = v2_api_model_template.format(api_model=api_model_name)

        if not class_type.__doc__:
            return

        if not class_type.__doc__.rstrip().endswith(expected_other_docstring):
            non_conforming_other[class_type] = (class_type.__doc__, expected_other_docstring)

    _sorted_all_classes = sorted(all_classes, key=lambda x: x.__name__)
    _sorted_all_classes.reverse()
    for class_type in _sorted_all_classes:
        if issubclass(class_type, HordeResponse):
            continue

        if issubclass(class_type, HordeRequest):
            process_request(class_type)
        elif issubclass(class_type, HordeAPIObject):
            process_other(class_type)

    for _, response_request_infos in sorted(response_request_map.items(), key=lambda x: x[0].__name__):
        process_response(response_request_infos)

    return {
        **non_conforming_requests,
        **non_conforming_responses,
        **non_conforming_other,
    }
