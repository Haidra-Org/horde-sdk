from pydantic import Field
from typing_extensions import override

from horde_sdk.ai_horde_api.apimodels.base import BaseAIHordeRequest
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_API_ENDPOINT_SUBPATH
from horde_sdk.consts import HTTPMethod
from horde_sdk.generic_api.apimodels import (
    HordeAPIObjectBaseModel,
    HordeResponseBaseModel,
)
from horde_sdk.generic_api.decoration import Unequatable, Unhashable


class AestheticRating(HordeAPIObjectBaseModel):
    """Represents an aesthetic rating for an image.

    v2 API Model: `AestheticRating`
    """

    id_: str = Field(
        alias="id",
        description="The UUID of image being rated.",
    )
    """The UUID of image being rated."""

    rating: int
    """The aesthetic rating 1-10 for this image."""

    artifacts: int
    """The artifacts rating for this image.
    0 for flawless generation that perfectly fits to the prompt.
    1 for small, hardly recognizable flaws. 2 small flaws that can easily be spotted, but don not harm the aesthetic
    experience.
    3 for flaws that look obviously wrong, but only mildly harm the aesthetic experience.
    4 for flaws that look obviously wrong & significantly harm the aesthetic experience.
    5 for flaws that make the image look like total garbage."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "AestheticRating"


class AestheticsPayload(HordeAPIObjectBaseModel):
    """Represents the payload for rating images.

    v2 API Model: `AestheticsPayload`
    """

    best: str | None = None
    """The UUID of the best image in this generation batch (only used when 2+ images generated).
    If 2+ aesthetic ratings are also provided, then they take precedence if they're not tied."""

    ratings: list[AestheticRating]
    """The aesthetic ratings for each image in the batch."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "AestheticsPayload"


class RateResponse(HordeResponseBaseModel):
    """The response to a rating submission, including the reward amount.

    Represents the data returned from the /v2/generate/rate/{id} endpoint with http status code 200.

    v2 API Model: `GenerationSubmitted`
    """

    reward: float
    """The reward for the rating."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "GenerationSubmitted"


@Unhashable
@Unequatable
class RateRequest(AestheticsPayload, BaseAIHordeRequest):
    """Submit ratings for a batch of images.

    Represents a POST request to the /v2/generate/rate/{id} endpoint.

    v2 API Model: `AestheticsPayload`
    """

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "AestheticsPayload"

    @override
    @classmethod
    def get_http_method(cls) -> HTTPMethod:
        return HTTPMethod.POST

    @override
    @classmethod
    def get_api_endpoint_subpath(cls) -> AI_HORDE_API_ENDPOINT_SUBPATH:
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_generate_rate_id

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[RateResponse]:
        return RateResponse
