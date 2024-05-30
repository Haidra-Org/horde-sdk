import pytest


@pytest.mark.object_verify
def test_all_ai_horde_api_models_imported() -> None:
    import horde_sdk.ai_horde_api.apimodels
    import horde_sdk.meta

    unimported_classes, missing_imports = horde_sdk.meta.any_unimported_classes(
        horde_sdk.ai_horde_api.apimodels,
        horde_sdk.HordeAPIObject,
    )

    missing_import_names = {cls.__name__ for cls in missing_imports}
    assert not unimported_classes, (
        "The following HordeAPIObjects are not imported in the `__init__.py` of the apimodels "
        f"namespace: : {missing_imports}"
        f"\n\nMissing import names: {missing_import_names}"
    )


@pytest.mark.object_verify
def test_all_ai_horde_api_data_objects_imported() -> None:
    import horde_sdk.ai_horde_api.apimodels
    import horde_sdk.generic_api.apimodels
    import horde_sdk.meta

    unimported_classes, missing_imports = horde_sdk.meta.any_unimported_classes(
        horde_sdk.ai_horde_api.apimodels,
        horde_sdk.generic_api.apimodels.HordeAPIDataObject,
    )

    missing_import_names = {cls.__name__ for cls in missing_imports}

    assert not unimported_classes, (
        "The following HordeAPIDataObjects are not imported in the `__init__.py` of the apimodels "
        f"namespace: : {missing_imports}"
        f"\n\nMissing import names: {missing_import_names}"
    )


@pytest.mark.skip(reason="This test is not yet enforced.")
@pytest.mark.object_verify
def test_all_ai_horde_api_models_defined() -> None:
    import horde_sdk.ai_horde_api.apimodels
    from horde_sdk.meta import all_undefined_classes

    undefined_classes = all_undefined_classes(horde_sdk.ai_horde_api.apimodels)

    assert (
        "GenerationInputStable" not in undefined_classes
    ), "A model which is known to be defined in the SDK was not found. Something critically bad has happened."

    # Pretty print the undefined classes sorted by dict values, NOT by keys
    import json

    error_responses = {
        "RequestError",
        "RequestValidationError",
    }

    for error_response in error_responses:
        if error_response in undefined_classes:
            print(f"Warning: {error_response} is an error response which may not be handled.")
            undefined_classes.pop(error_response)

    undefined_classes_sorted = dict(sorted(undefined_classes.items(), key=lambda x: x[1]))
    print(json.dumps(undefined_classes_sorted, indent=4))

    assert not undefined_classes, (
        "The following models are defined in the API but not in the SDK: " f"{undefined_classes}"
    )


@pytest.mark.object_verify
def test_all_ai_horde_endpoints_known() -> None:
    from horde_sdk.meta import all_unknown_endpoints_ai_horde

    unknown_endpoints = all_unknown_endpoints_ai_horde()

    assert not unknown_endpoints, (
        "The following endpoints are defined in the API but not in the SDK: " f"{unknown_endpoints}"
    )


@pytest.mark.skip(reason="This test is not yet enforced.")
@pytest.mark.object_verify
def test_all_ai_horde_endpoints_addressed() -> None:
    from horde_sdk.meta import all_unaddressed_endpoints_ai_horde

    unaddressed_endpoints = all_unaddressed_endpoints_ai_horde()

    assert not unaddressed_endpoints, (
        "The following endpoints are defined in the API but not in the SDK: " f"{unaddressed_endpoints}"
    )


@pytest.mark.object_verify
def test_all_ratings_api_models_imported() -> None:
    import horde_sdk.ratings_api.apimodels  # noqa: I001
    import horde_sdk.meta

    unimported_classes, missing_imports = horde_sdk.meta.any_unimported_classes(
        horde_sdk.ratings_api.apimodels,
        horde_sdk.HordeAPIObject,
    )

    missing_import_names = {cls.__name__ for cls in missing_imports}
    assert not unimported_classes, (
        "The following HordeAPIObjects are not imported in the `__init__.py` of the apimodels "
        f"namespace: : {missing_imports}"
        f"\n\nMissing import names: {missing_import_names}"
    )


@pytest.mark.object_verify
def test_all_models_have_docstrings() -> None:
    import horde_sdk.meta

    missing_docstrings = horde_sdk.meta.all_model_and_fields_missing_docstrings()

    import json

    stringified_missing_docstrings = {k.__name__: list(v) for k, v in missing_docstrings.items()}
    jsonified_missing_docstrings = json.dumps(stringified_missing_docstrings, indent=4)

    assert not missing_docstrings, "The following models are missing docstrings: " f"{jsonified_missing_docstrings}"
