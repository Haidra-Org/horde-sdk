"""Retrieve the recorded parameters of an authenticated generation request."""

from __future__ import annotations

from typing import Literal, override

from horde_sdk.ai_horde_api.apimodels.base import BaseAIHordeRequest, ExtraSourceImageEntry, JobRequestMixin
from horde_sdk.ai_horde_api.apimodels.generate.async_ import ImageGenerationInputPayload
from horde_sdk.ai_horde_api.apimodels.generate.text.async_ import ContextFit, ModelGenerationInputKobold
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_API_ENDPOINT_SUBPATH
from horde_sdk.consts import HTTPMethod
from horde_sdk.generic_api.apimodels import APIKeyAllowedInRequestMixin, HordeResponseBaseModel
from horde_sdk.generic_api.decoration import Unequatable, Unhashable


@Unhashable
@Unequatable
class GenerationSubmittedStable(HordeResponseBaseModel):
    """Recorded submission before style expansion and moderation.

    Represents the data returned from the /v2/generate/request/{id} endpoint with http status code 200.

    v2 API Model: `GenerationSubmittedStable`
    """

    prompt: str | None = None
    """Original submitted prompt before styles/moderation; omitted when unavailable on legacy requests."""

    params: ImageGenerationInputPayload | None = None
    """The params reported by the API."""

    nsfw: bool | None = None
    """Set to true if this request is NSFW. This will skip workers which censor images."""

    trusted_workers: bool | None = None
    """When true, only trusted workers will serve this request. When False, Evaluating workers will also be used
    which can increase speed but adds more risk!"""

    validated_backends: bool | None = None
    """When true, only inference backends that are validated by the AI Horde devs will serve this request. When
    False, non-validated backends will also be used which can increase speed but you may end up with unexpected
    results."""

    slow_workers: bool | None = None
    """When True, allows slower workers to pick up this request. Disabling this incurs an extra kudos cost."""

    extra_slow_workers: bool | None = None
    """When True, allows very slower workers to pick up this request. Use this when you don't mind waiting a lot."""

    censor_nsfw: bool | None = None
    """If the request is SFW, and the worker accidentally generates NSFW, it will send back a censored image."""

    workers: list[str] | None = None
    """The workers reported by the API."""

    worker_blacklist: bool | None = None
    """If true, the worker list will be treated as a blacklist instead of a whitelist."""

    models: list[str] | None = None
    """The models reported by the API."""

    source_image: str | None = None
    """The object storage reference the source image was uploaded to on submission."""

    source_processing: Literal["img2img", "inpainting", "outpainting", "remix"] | None = None
    """If source_image is provided, specifies how to process it."""

    source_mask: str | None = None
    """The object storage reference the source mask was uploaded to on submission."""

    extra_source_images: list[ExtraSourceImageEntry] | None = None
    """The extra source images reported by the API."""

    r2: bool | None = None
    """If True, the image will be sent via cloudflare r2 download link."""

    shared: bool | None = None
    """If True, The image will be shared with LAION for improving their dataset. This will also reduce your kudos
    consumption by 2. For anonymous users, this is always True."""

    proxied_account: str | None = None
    """If using a service account as a proxy, provide this value to identify the actual account from which this
    request is coming from."""

    disable_batching: bool | None = None
    """When true, This request will not use batching. This will allow you to retrieve accurate seeds. Feature is
    restricted to Trusted users and Patreons."""

    webhook: str | None = None
    """Provide a URL where the AI Horde will send a POST call after each delivered generation. The request will
    include the details of the job as well as the request ID."""

    template_fields: dict[str, object] | None = None
    """Values for the placeholders the requested style's prompt accepts, as a flat object of strings keyed by field
    name. Only accepted together with 'style', and only for fields that style declares. Each value, and all of
    them together, are limited to the same length as a prompt (7500 words)."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return "GenerationSubmittedStable"


@Unhashable
@Unequatable
class GenerationSubmittedKobold(HordeResponseBaseModel):
    """Recorded submission before style expansion and moderation.

    Represents the data returned from the /v2/generate/text/request/{id} endpoint with http status code 200.

    v2 API Model: `GenerationSubmittedKobold`
    """

    prompt: str | None = None
    """Original submitted prompt before styles/moderation; omitted when unavailable on legacy requests."""

    params: ModelGenerationInputKobold | None = None
    """The params reported by the API."""

    softprompt: str | None = None
    """Specify which softpompt needs to be used to service this request."""

    trusted_workers: bool | None = None
    """When true, only trusted workers will serve this request. When False, Evaluating workers will also be used
    which can increase speed but adds more risk!"""

    validated_backends: bool | None = None
    """When true, only inference backends that are validated by the AI Horde devs will serve this request. When
    False, non-validated backends will also be used which can increase speed but you may end up with unexpected
    results."""

    slow_workers: bool | None = None
    """When True, allows slower workers to pick up this request. Disabling this incurs an extra kudos cost."""

    workers: list[str] | None = None
    """The workers reported by the API."""

    worker_blacklist: bool | None = None
    """If true, the worker list will be treated as a blacklist instead of a whitelist."""

    models: list[str] | None = None
    """The models reported by the API."""

    proxied_account: str | None = None
    """If using a service account as a proxy, provide this value to identify the actual account from which this
    request is coming from."""

    extra_source_images: list[ExtraSourceImageEntry] | None = None
    """The extra source images reported by the API."""

    disable_batching: bool | None = None
    """When true, This request will not use batching. This will allow you to retrieve accurate seeds. Feature is
    restricted to Trusted users and Patreons."""

    webhook: str | None = None
    """Provide a URL where the AI Horde will send a POST call after each delivered generation. The request will
    include the details of the job as well as the request ID."""

    template_fields: dict[str, object] | None = None
    """Values for the placeholders the requested style's prompt accepts, as a flat object of strings keyed by field
    name. Only accepted together with 'style', and only for fields that style declares. Each value, and all of
    them together, are limited to the same length as a prompt (7500 words)."""

    context_fit: ContextFit | None = None
    """What to do when the prompt does not fit the requested max_context_length. 'ignore' sends it anyway and the
    worker cuts the front of it away, 'reject' refuses the request, and 'grow' raises max_context_length until the
    prompt fits and charges for the larger context."""

    extra_slow_workers: bool | None = None
    """When True, allows very slower workers to pick up this request. Use this when you don't mind waiting a lot."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return "GenerationSubmittedKobold"


class ImageGenerateSubmittedRequest(BaseAIHordeRequest, JobRequestMixin, APIKeyAllowedInRequestMixin):
    """Retrieve recorded parameters using the API key that originally submitted the request.

    Represents a GET request to the /v2/generate/request/{id} endpoint.
    """

    @override
    @classmethod
    def get_api_model_name(cls) -> None:
        return None

    @override
    @classmethod
    def get_http_method(cls) -> HTTPMethod:
        return HTTPMethod.GET

    @override
    @classmethod
    def get_api_endpoint_subpath(cls) -> AI_HORDE_API_ENDPOINT_SUBPATH:
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_generate_request

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[GenerationSubmittedStable]:
        return GenerationSubmittedStable

    @override
    @classmethod
    def is_api_key_required(cls) -> bool:
        return True


class TextGenerateSubmittedRequest(BaseAIHordeRequest, JobRequestMixin, APIKeyAllowedInRequestMixin):
    """Retrieve recorded parameters using the API key that originally submitted the request.

    Represents a GET request to the /v2/generate/text/request/{id} endpoint.
    """

    @override
    @classmethod
    def get_api_model_name(cls) -> None:
        return None

    @override
    @classmethod
    def get_http_method(cls) -> HTTPMethod:
        return HTTPMethod.GET

    @override
    @classmethod
    def get_api_endpoint_subpath(cls) -> AI_HORDE_API_ENDPOINT_SUBPATH:
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_generate_text_request

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[GenerationSubmittedKobold]:
        return GenerationSubmittedKobold

    @override
    @classmethod
    def is_api_key_required(cls) -> bool:
        return True
