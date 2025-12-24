from __future__ import annotations

from horde_sdk.generation_parameters.image.object_models import (
    BasicImageGenerationParameters,
    BasicImageGenerationParametersTemplate,
    ImageGenerationParameters,
    ImageGenerationParametersTemplate,
)


def _create_basic_template(prompt: str) -> BasicImageGenerationParametersTemplate:
    return BasicImageGenerationParametersTemplate(
        prompt=prompt,
        model="example-model",
    )


def test_image_template_to_parameters_applies_base_updates() -> None:
    template = ImageGenerationParametersTemplate(
        base_params=_create_basic_template(prompt="starting"),
    )

    parameters = template.to_parameters(base_param_updates=BasicImageGenerationParametersTemplate(prompt="updated"))

    assert isinstance(parameters.base_params, BasicImageGenerationParameters)
    assert parameters.base_params.prompt == "updated"


def test_image_template_to_parameters_reuses_existing_result_ids() -> None:
    parameters = ImageGenerationParameters(
        base_params=BasicImageGenerationParameters(
            prompt="kept",
            model="example-model",
        ),
        result_ids=["existing-id"],
    )

    converted = parameters.to_parameters()

    assert converted.result_ids == ["existing-id"]


def test_image_parameters_accept_existing_instance_via_model_validate() -> None:
    template = ImageGenerationParametersTemplate(
        base_params=_create_basic_template(prompt="validate"),
    )

    parameters = template.to_parameters()
    clone = ImageGenerationParameters.model_validate(parameters, from_attributes=True)

    assert clone.model_dump() == parameters.model_dump()
