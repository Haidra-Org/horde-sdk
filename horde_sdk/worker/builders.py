from __future__ import annotations

import warnings
from collections.abc import Mapping, Sequence

from horde_sdk.consts import ID_TYPES
from horde_sdk.generation_parameters.alchemy.consts import KNOWN_ALCHEMY_FORMS
from horde_sdk.generation_parameters.alchemy.object_models import (
    SingleAlchemyParameters,
    SingleAlchemyParametersTemplate,
)
from horde_sdk.generation_parameters.image.object_models import (
    ImageGenerationParameters,
    ImageGenerationParametersTemplate,
)
from horde_sdk.generation_parameters.text.object_models import (
    TextGenerationParameters,
    TextGenerationParametersTemplate,
)
from horde_sdk.generation_parameters.utils import ResultIdAllocator

_DEPRECATION_MESSAGE = (
    "horde_sdk.worker.builders.* helpers are deprecated; call template.to_parameters() directly instead."
)


def _warn_deprecated(function_name: str) -> None:
    warnings.warn(
        f"{function_name} is deprecated: {_DEPRECATION_MESSAGE}",
        DeprecationWarning,
        stacklevel=2,
    )


def image_parameters_from_template(
    template: ImageGenerationParametersTemplate,
    *,
    base_param_updates: Mapping[str, object] | None = None,
    result_ids: Sequence[ID_TYPES] | None = None,
    allocator: ResultIdAllocator | None = None,
    seed: str = "image",
) -> ImageGenerationParameters:
    """Convert an image parameter template into concrete parameters."""
    _warn_deprecated("image_parameters_from_template")
    return template.to_parameters(
        base_param_updates=base_param_updates,
        result_ids=result_ids,
        allocator=allocator,
        seed=seed,
    )


def text_parameters_from_template(
    template: TextGenerationParametersTemplate,
    *,
    base_param_updates: Mapping[str, object] | None = None,
    result_ids: Sequence[ID_TYPES] | None = None,
    allocator: ResultIdAllocator | None = None,
    seed: str = "text",
) -> TextGenerationParameters:
    """Convert a text parameter template into concrete parameters."""
    _warn_deprecated("text_parameters_from_template")
    return template.to_parameters(
        base_param_updates=base_param_updates,
        result_ids=result_ids,
        allocator=allocator,
        seed=seed,
    )


def alchemy_parameters_from_template(
    template: SingleAlchemyParametersTemplate,
    *,
    result_id: ID_TYPES | None = None,
    source_image: bytes | str | None = None,
    default_form: KNOWN_ALCHEMY_FORMS | str | None = None,
    allocator: ResultIdAllocator | None = None,
    seed: str = "alchemy",
) -> SingleAlchemyParameters:
    """Convert an alchemy parameter template into concrete parameters."""
    _warn_deprecated("alchemy_parameters_from_template")
    return template.to_parameters(
        result_id=result_id,
        source_image=source_image,
        default_form=default_form,
        allocator=allocator,
        seed=seed,
    )
