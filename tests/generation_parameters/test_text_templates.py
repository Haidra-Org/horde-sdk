from __future__ import annotations

from horde_sdk.generation_parameters.text.object_models import (
    BasicTextGenerationParameters,
    BasicTextGenerationParametersTemplate,
    TextGenerationParameters,
    TextGenerationParametersTemplate,
)


def _create_basic_template(prompt: str) -> BasicTextGenerationParametersTemplate:
    return BasicTextGenerationParametersTemplate(
        prompt=prompt,
        model="example-model",
    )


def test_text_template_to_parameters_applies_base_updates() -> None:
    template = TextGenerationParametersTemplate(
        base_params=_create_basic_template(prompt="initial"),
    )

    parameters = template.to_parameters(base_param_updates=BasicTextGenerationParametersTemplate(prompt="updated"))

    assert isinstance(parameters.base_params, BasicTextGenerationParameters)
    assert parameters.base_params.prompt == "updated"


def test_text_template_to_parameters_reuses_existing_result_ids() -> None:
    parameters = TextGenerationParameters(
        base_params=BasicTextGenerationParameters(
            prompt="kept",
            model="example-model",
        ),
        result_ids=["existing-id"],
    )

    converted = parameters.to_parameters()

    assert converted.result_ids == ["existing-id"]


def test_text_parameters_accept_existing_instance_via_model_validate() -> None:
    template = TextGenerationParametersTemplate(
        base_params=_create_basic_template(prompt="validate"),
    )

    parameters = template.to_parameters()
    clone = TextGenerationParameters.model_validate(parameters, from_attributes=True)

    assert clone.model_dump() == parameters.model_dump()
