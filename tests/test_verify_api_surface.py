import pytest


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
        f" namespace: : {missing_imports}"
        f"\n\nMissing import names: {missing_import_names}"
    )


def test_all_ai_horde_api_data_objects_imported() -> None:
    import horde_sdk.ai_horde_api.apimodels
    import horde_sdk.meta

    unimported_classes, missing_imports = horde_sdk.meta.any_unimported_classes(
        horde_sdk.ai_horde_api.apimodels,
        horde_sdk.HordeAPIDataObject,
    )

    missing_import_names = {cls.__name__ for cls in missing_imports}

    assert not unimported_classes, (
        "The following HordeAPIDataObjects are not imported in the `__init__.py` of the apimodels "
        f" namespace: : {missing_imports}"
        f"\n\nMissing import names: {missing_import_names}"
    )


@pytest.mark.skip(reason="This test is not yet enforced.")
def test_all_ai_horde_api_models_defined() -> None:
    import horde_sdk.ai_horde_api.apimodels
    from horde_sdk.meta import all_undefined_classes

    undefined_classes = all_undefined_classes(horde_sdk.ai_horde_api.apimodels)

    assert (
        "GenerationInputStable" not in undefined_classes
    ), "A model which is known to be defined in the SDK was not found. Something critically bad has happened."

    # Pretty print the undefined classes sorted by dict values, NOT by keys
    import json

    undefined_classes_sorted = dict(sorted(undefined_classes.items(), key=lambda x: x[1]))
    print(json.dumps(undefined_classes_sorted, indent=4))

    assert not undefined_classes, (
        "The following models are defined in the API but not in the SDK: " f"{undefined_classes}"
    )


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
        f" namespace: : {missing_imports}"
        f"\n\nMissing import names: {missing_import_names}"
    )
