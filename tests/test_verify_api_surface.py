import pytest
from loguru import logger


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
        horde_sdk.generic_api.apimodels.HordeAPIData,
    )

    missing_import_names = {cls.__name__ for cls in missing_imports}

    assert not unimported_classes, (
        "The following HordeAPIDataObjects are not imported in the `__init__.py` of the apimodels "
        f"namespace: : {missing_imports}"
        f"\n\nMissing import names: {missing_import_names}"
    )


# @pytest.mark.skip(reason="This test is not yet enforced.")
@pytest.mark.object_verify
def test_all_ai_horde_api_models_defined() -> None:
    import horde_sdk.ai_horde_api.apimodels
    from horde_sdk.meta import all_undefined_classes, all_undefined_classes_for_endpoints

    undefined_classes = all_undefined_classes(horde_sdk.ai_horde_api.apimodels)

    # all_undefined_classes_for_endpoints handles the ones directly referenced by endpoints, so we remove them
    undefined_classes_for_endpoints = all_undefined_classes_for_endpoints(horde_sdk.ai_horde_api.apimodels)
    for key in undefined_classes_for_endpoints:
        if key in undefined_classes:
            undefined_classes.remove(key)

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
            undefined_classes.remove(error_response)

    undefined_classes_sorted = sorted(undefined_classes)
    print(json.dumps(undefined_classes_sorted, indent=4))

    skipped_classes = [  # FIXME
        "ModelPayloadStable",
        "WorkerDetailsLite",
        "ModelPayloadStyleKobold",
        "ModelStyleInputParamsStableNoDefaults",
        "SinglePeriodTxtModelStats",
        "ModelPayloadRootKobold",
        "ModelGenerationInputKobold",
        "SinglePeriodImgModelStats",
        "ModelSpecialPayloadStable",
        "ModelPayloadKobold",
        "InterrogationFormResult",
        "GenerationMetadataKobold",
        "InterrogationFormStatus",
        "SubmitInput",
        "UserActiveGenerations",
        "ModelInterrogationFormStable",
        "ModelPayloadStyleStable",
        "ResponseModelMessagePop",
    ]
    """Many of these classes are abstractions or mislabeled and their absence in the SDK is an implementation detail.
    While they may later be added, the intent of this test is to detect *new* unsupported classes.
    """

    logger.warning(f"Skipped classes: {skipped_classes}")  # TODO

    for skipped_class in skipped_classes:
        if skipped_class in undefined_classes:
            undefined_classes.remove(skipped_class)

    assert not undefined_classes, (
        "The following models are defined in the API but not in the SDK: " f"{undefined_classes}"
    )


@pytest.mark.object_verify
def test_all_ai_horde_api_models_defined_for_endpoints() -> None:
    import horde_sdk.ai_horde_api.apimodels
    from horde_sdk.meta import all_undefined_classes_for_endpoints

    undefined_classes = all_undefined_classes_for_endpoints(horde_sdk.ai_horde_api.apimodels)

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


# @pytest.mark.skip(reason="This test is not yet enforced.")
@pytest.mark.object_verify
def test_all_ai_horde_endpoints_addressed() -> None:
    from horde_sdk.ai_horde_api.endpoints import get_admin_only_endpoints, get_deprecated_endpoints
    from horde_sdk.meta import all_unaddressed_endpoints_ai_horde

    unaddressed_endpoints = all_unaddressed_endpoints_ai_horde()

    all_ignored_endpoints = get_admin_only_endpoints() | get_deprecated_endpoints()

    unaddressed_endpoints -= all_ignored_endpoints

    print()
    for unaddressed_endpoint in unaddressed_endpoints:
        print(f"Unaddressed path: {unaddressed_endpoint}.")

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


@pytest.mark.object_verify
def test_all_models_non_conforming_docstrings() -> None:
    import horde_sdk.meta

    non_conforming_docstrings = horde_sdk.meta.all_models_non_conforming_docstrings()

    import json

    stringified_non_conforming_docstrings = {k.__name__: v for k, v in non_conforming_docstrings.items()}
    jsonified_non_conforming_docstrings = json.dumps(stringified_non_conforming_docstrings, indent=4)

    map_to_dump: dict[str, dict[str, str]] = {}
    missing_original_docstrings: dict[str, dict[str, str]] = {}

    for model, docstrings in non_conforming_docstrings.items():
        original_docstring, new_docstring = docstrings

        if original_docstring is None:
            missing_original_docstrings[model.__name__] = {
                "new": new_docstring or "",
            }
            continue

        if original_docstring:
            map_to_dump[model.__name__] = {
                "original": original_docstring,
                "new": new_docstring or "",
            }
        else:
            map_to_dump[model.__name__] = {
                "new": new_docstring or "",
            }
    with open("docstrings.json", "w", encoding="utf-8") as f:
        json.dump(map_to_dump, f, indent=4)
        f.write("\n")

    with open("missing_original_docstrings.json", "w", encoding="utf-8") as f:
        json.dump(missing_original_docstrings, f, indent=4)
        f.write("\n")

    assert not non_conforming_docstrings, (
        "The following models have non-conforming docstrings: " f"{jsonified_non_conforming_docstrings}"
    )
