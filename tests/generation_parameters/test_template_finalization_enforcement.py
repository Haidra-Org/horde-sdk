from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from importlib import import_module
from types import ModuleType
from typing import Protocol

import pytest


class TemplateConversionProbe(Protocol):
    def to_parameters(self, **kwargs: object) -> object:  # pragma: no cover - Protocol definition
        ...


@dataclass(frozen=True, slots=True)
class FinalizationEnforcementCase:
    module_path: str
    case_id: str
    template_factory: Callable[[ModuleType], TemplateConversionProbe]
    call_kwargs_factory: Callable[[ModuleType], dict[str, object]]


CASES: tuple[FinalizationEnforcementCase, ...] = (
    FinalizationEnforcementCase(
        module_path="horde_sdk.generation_parameters.image.object_models",
        case_id="image",
        template_factory=lambda module: module.ImageGenerationParametersTemplate(
            base_params=module.BasicImageGenerationParametersTemplate(
                model="example-image-model",
                prompt="prompt",
            ),
        ),
        call_kwargs_factory=lambda module: {"result_ids": ["img-1"]},
    ),
    FinalizationEnforcementCase(
        module_path="horde_sdk.generation_parameters.text.object_models",
        case_id="text",
        template_factory=lambda module: module.TextGenerationParametersTemplate(
            base_params=module.BasicTextGenerationParametersTemplate(
                model="example-text-model",
                prompt="prompt",
            ),
        ),
        call_kwargs_factory=lambda module: {"result_ids": ["txt-1"]},
    ),
    FinalizationEnforcementCase(
        module_path="horde_sdk.generation_parameters.alchemy.object_models",
        case_id="alchemy",
        template_factory=lambda module: module.UpscaleAlchemyParametersTemplate(
            form=module.KNOWN_ALCHEMY_FORMS.post_process,
            upscaler=module.KNOWN_UPSCALERS.RealESRGAN_x4plus,
        ),
        call_kwargs_factory=lambda module: {
            "result_id": "alchemy-1",
            "source_image": b"binary",
        },
    ),
)


@pytest.mark.parametrize("case", CASES, ids=[case.case_id for case in CASES])
def test_templates_call_finalize_template_for_parameters(
    case: FinalizationEnforcementCase,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = import_module(case.module_path)
    original = module.finalize_template_for_parameters
    finalize_called = False

    def _tracking_finalize(*args: object, **kwargs: object) -> object:
        nonlocal finalize_called
        finalize_called = True
        return original(*args, **kwargs)

    monkeypatch.setattr(module, "finalize_template_for_parameters", _tracking_finalize)

    template = case.template_factory(module)
    call_kwargs = case.call_kwargs_factory(module)
    template.to_parameters(**call_kwargs)

    assert finalize_called, (
        "Template.conversion must call finalize_template_for_parameters() to ensure deterministic result IDs."
    )
