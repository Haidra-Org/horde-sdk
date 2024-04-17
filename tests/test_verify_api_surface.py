def test_all_ai_horde_api_models_imported() -> None:
    import horde_sdk.ai_horde_api.apimodels
    import horde_sdk.meta

    unimported_classes, missing_imports = horde_sdk.meta.any_unimported_classes(horde_sdk.ai_horde_api.apimodels)

    missing_import_names = {cls.__name__ for cls in missing_imports}
    assert not unimported_classes, (
        "The following classes are not imported in the `__init__.py` of the apimodels "
        f" namespace: : {missing_imports}"
        f"\n\nMissing import names: {missing_import_names}"
    )


def test_all_ratings_api_models_imported() -> None:
    import horde_sdk.ratings_api.apimodels  # noqa: I001
    import horde_sdk.meta

    unimported_classes, missing_imports = horde_sdk.meta.any_unimported_classes(horde_sdk.ratings_api.apimodels)

    missing_import_names = {cls.__name__ for cls in missing_imports}
    assert not unimported_classes, (
        "The following classes are not imported in the `__init__.py` of the apimodels "
        f" namespace: : {missing_imports}"
        f"\n\nMissing import names: {missing_import_names}"
    )
