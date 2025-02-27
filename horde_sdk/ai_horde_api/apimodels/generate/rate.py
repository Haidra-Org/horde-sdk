from pydantic import Field
from typing_extensions import override

from horde_sdk.ai_horde_api.apimodels.base import BaseAIHordeRequest
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_API_ENDPOINT_SUBPATH
from horde_sdk.consts import HTTPMethod
from horde_sdk.generic_api.apimodels import (
    HordeAPIObjectBaseModel,
    HordeResponseBaseModel,
)

"""AestheticsPayload{
best	string
example: 6038971e-f0b0-4fdd-a3bb-148f561f815e
minLength: 36
maxLength: 36
The UUID of the best image in this generation batch (only used when 2+ images generated). If 2+ aesthetic ratings are
also provided, then they take precedence if they're not tied.

ratings	[AestheticRating{
id*	string
example: 6038971e-f0b0-4fdd-a3bb-148f561f815e
minLength: 36
maxLength: 36
The UUID of image being rated.

rating*	integer
minimum: 1
maximum: 10
The aesthetic rating 1-10 for this image.

artifacts	integer
example: 1
minimum: 0
maximum: 5
The artifacts rating for this image.
0 for flawless generation that perfectly fits to the prompt.
1 for small, hardly recognizable flaws.
2 small flaws that can easily be spotted, but don not harm the aesthetic experience.
3 for flaws that look obviously wrong, but only mildly harm the aesthetic experience.
4 for flaws that look obviously wrong & significantly harm the aesthetic experience.
5 for flaws that make the image look like total garbage.

}]
}"""


class AestheticRating(HordeAPIObjectBaseModel):
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

    reward: float
    """The reward for the rating."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "GenerationSubmitted"


class RateRequest(AestheticsPayload, BaseAIHordeRequest):
    """Represents the data needed to make a request to the `/v2/rate` endpoint.

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
