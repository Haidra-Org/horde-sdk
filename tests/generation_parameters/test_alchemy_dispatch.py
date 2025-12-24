from __future__ import annotations

import pytest

from horde_sdk.generation_parameters.alchemy.consts import (
    KNOWN_ALCHEMY_FORMS,
    KNOWN_CAPTION_MODELS,
    KNOWN_FACEFIXERS,
    KNOWN_INTERROGATORS,
    KNOWN_UPSCALERS,
)
from horde_sdk.generation_parameters.alchemy.object_models import (
    CaptionAlchemyParameters,
    CaptionAlchemyParametersTemplate,
    FacefixAlchemyParameters,
    FacefixAlchemyParametersTemplate,
    InterrogateAlchemyParameters,
    InterrogateAlchemyParametersTemplate,
    NSFWAlchemyParameters,
    NSFWAlchemyParametersTemplate,
    ResolverRule,
    SingleAlchemyParameters,
    SingleAlchemyParametersTemplate,
    UpscaleAlchemyParameters,
    UpscaleAlchemyParametersTemplate,
    instantiate_alchemy_parameters,
    register_alchemy_parameter_rule,
    unregister_alchemy_parameter_rule,
)


@pytest.mark.parametrize(
    "template, expected_type",
    [
        (
            UpscaleAlchemyParametersTemplate(
                form=KNOWN_ALCHEMY_FORMS.post_process,
                upscaler=KNOWN_UPSCALERS.RealESRGAN_x4plus,
            ),
            UpscaleAlchemyParameters,
        ),
        (
            FacefixAlchemyParametersTemplate(
                form=KNOWN_ALCHEMY_FORMS.post_process,
                facefixer=KNOWN_FACEFIXERS.GFPGAN,
            ),
            FacefixAlchemyParameters,
        ),
        (
            InterrogateAlchemyParametersTemplate(
                form=KNOWN_ALCHEMY_FORMS.interrogation,
                interrogator=KNOWN_INTERROGATORS.BACKEND_DEFAULT,
            ),
            InterrogateAlchemyParameters,
        ),
        (
            CaptionAlchemyParametersTemplate(
                form=KNOWN_ALCHEMY_FORMS.caption,
                caption_model=KNOWN_CAPTION_MODELS.BLIP_BASE_SALESFORCE,
            ),
            CaptionAlchemyParameters,
        ),
        (
            NSFWAlchemyParametersTemplate(
                form=KNOWN_ALCHEMY_FORMS.nsfw,
                nsfw_detector="demo",
            ),
            NSFWAlchemyParameters,
        ),
    ],
)
def test_template_dispatches_to_specialised_model(
    template: SingleAlchemyParametersTemplate,
    expected_type: type[SingleAlchemyParameters],
) -> None:
    parameters = template.to_parameters(result_id="example-id")
    assert isinstance(parameters, expected_type)


def test_template_without_specialised_fields_uses_base_model() -> None:
    template = SingleAlchemyParametersTemplate(form="custom-form")
    parameters = template.to_parameters(result_id="example-id")
    assert isinstance(parameters, SingleAlchemyParameters)


class CustomAlchemyParameters(SingleAlchemyParameters):
    custom_value: str


class CustomAlchemyParametersTemplate(SingleAlchemyParametersTemplate):
    custom_value: str | None = None


def test_custom_resolver_can_be_registered() -> None:
    template = CustomAlchemyParametersTemplate(custom_value="demo", form="custom")

    rule = ResolverRule(
        predicate=lambda payload: payload.get("custom_value") == "demo",
        model=CustomAlchemyParameters,
    )

    register_alchemy_parameter_rule(rule)
    try:
        parameters = template.to_parameters(result_id="example-id")
        assert isinstance(parameters, CustomAlchemyParameters)
    finally:
        unregister_alchemy_parameter_rule(rule)


def test_instantiate_accepts_template_payload() -> None:
    template = UpscaleAlchemyParametersTemplate(
        form=KNOWN_ALCHEMY_FORMS.post_process,
        upscaler=KNOWN_UPSCALERS.RealESRGAN_x4plus,
        result_id="template-id",
    )

    parameters = instantiate_alchemy_parameters(template)

    assert isinstance(parameters, UpscaleAlchemyParameters)
    assert parameters.result_id == "template-id"
