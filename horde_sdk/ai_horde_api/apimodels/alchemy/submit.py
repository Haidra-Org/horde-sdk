from typing import override

from loguru import logger
from pydantic import model_validator

from horde_sdk.ai_horde_api.apimodels.base import BaseAIHordeRequest, JobRequestMixin
from horde_sdk.ai_horde_api.consts import GENERATION_STATE
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_API_ENDPOINT_SUBPATH
from horde_sdk.consts import HTTPMethod
from horde_sdk.generic_api.apimodels import APIKeyAllowedInRequestMixin, HordeResponseBaseModel


class AlchemyJobSubmitResponse(HordeResponseBaseModel):
    """Indicates that an alchemy job has been submitted successfully and the kudos gained.

    Represents the data returned from the following endpoints and http status codes:
        - /v2/interrogate/submit | AlchemyJobSubmitRequest [POST] -> 200

    v2 API Model: `GenerationSubmitted`
    """

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "GenerationSubmitted"

    reward: float
    """The kudos reward for this job."""


class AlchemyJobSubmitRequest(BaseAIHordeRequest, JobRequestMixin, APIKeyAllowedInRequestMixin):
    """Request to submit an alchemy job once a worker has completed it.

    Represents a POST request to the /v2/interrogate/submit endpoint.

    v2 API Model: `SubmitInputStable`
    """

    result: dict[str, object] | str
    """The results of the alchemy job, keyed by form name. The API requires this field even for
    faulted submissions, though it is ignored server-side in that case.

    The API swagger doc declares this field as a string, but the server actually requires a
    dictionary and will reject string submissions; the `str` arm exists only for swagger
    compatibility."""
    state: GENERATION_STATE
    """The state of this generation. See `GENERATION_STATE` for more information."""

    @model_validator(mode="after")
    def warn_on_string_result(self) -> "AlchemyJobSubmitRequest":
        """Warn that the server will reject a string `result` despite the swagger doc allowing it."""
        if isinstance(self.result, str):
            logger.warning(
                "AlchemyJobSubmitRequest.result was given a string, but the server requires a dictionary "
                "keyed by form name and will reject this submission.",
            )

        return self

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "SubmitInputStable"

    @override
    @classmethod
    def get_http_method(cls) -> HTTPMethod:
        return HTTPMethod.POST

    @override
    @classmethod
    def get_api_endpoint_subpath(cls) -> AI_HORDE_API_ENDPOINT_SUBPATH:
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_interrogate_submit

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[AlchemyJobSubmitResponse]:
        return AlchemyJobSubmitResponse
